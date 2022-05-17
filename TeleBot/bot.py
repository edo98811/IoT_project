from operator import imod
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import requests
import time
from MyMQTT import *


class TeleBot:
    def __init__(self, token, broker, port, topics, catalog_address):
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        self.catalog_address = catalog_address
        self.client = MyMQTT("TelegramBotIot", broker, port, self)
        self.client.start()
        self.topics = topics
        for topic in topics:
            self.client.mySubscribe(topic)
        MessageLoop(self.bot, {'chat': self.on_chat_message,
                               'callback_query': self.on_callback_query}).run_as_thread()



    ### Routine di risposta ai messaggi di telegram ###
    def on_chat_message(self, msg):                                 
        # estrazione del chat_ID da cui è arrivato il messaggio
        content_type, chat_type, chat_ID = telepot.glance(msg)
        # estrazione del testo del messaggio e dello user da cui è stato mandato
        message = msg['text']
        user = msg['from']['first_name']
        
        if message=="/start":
            # restituisco un messaggio di benvenuto in caso l'utente mi dia come input /start, gli restituisco 
            start_message = f"Welcome {user} to IoT_IHealthBOT. To complete the registration you have to add this chatID to the web page:\n {chat_ID}!!!"
            self.bot.sendMessage(chat_ID, text=start_message)

        elif message == '/report':
            # in caso il medico scelga questa key bisogna resituirgli la lista di tutti i suoi pazienti
            # dal chat_id risalgo al nome del medico
            doctors = json.loads(requests.get(self.catalog_address + '/avail_docs').text)
            doctor_id = doctors["docID"][doctors["chatID"].index(str(chat_ID))]
            # a partire dal doctor id scorro la lista dei pazienti e tengo solamente coloro che hanno quel dottore 
            patients = json.loads(requests.get(self.catalog_address + '/get_patients').text)
            patFullNames = [f"{pat['personal_info']['name']} {pat['personal_info']['surname']}" for pat in patients if pat['doctor_ID']==doctor_id]
            
            patIndex = [patients.index(pat) for pat in patients if pat['doctor_ID']==doctor_id]
            
            question = 'This is the list of your patients, select the one that you are interest about'
            self.bot.sendMessage(chat_ID, text=question,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        list(map(lambda c,p: InlineKeyboardButton(text=str(c), callback_data=str(p)), patFullNames, patIndex))
                    ]
                )
            )
        
        else:
            # se nessun messaggio e' riconosciuto rimando la lista dei possibili comandi
            self.bot.sendMessage(chat_ID, text="Command not supported. The available command are:\n\
    /start: if you want to know your ChatID\n\
    /report: if you want the report of a patient\n\
    /quit: exit?\n")
            


    ### Routine per rispondere alle inline Keyboard ###
    def on_callback_query(self,msg):
        # estraggo chat_id del medico ed il paziente selezionato (da query data so la posizione che il paziente occupa nel catalog, parto da 0)
        query_ID , chat_ID , query_data = telepot.glance(msg,flavor='callback_query') 
        patients = json.loads(requests.get(self.catalog_address + '/get_patients').text)
        pat = patients[int(query_data)]
        # estraggo i possibili sensori (in sensoro ho i devID e i fullNames)
        sensors = json.loads(requests.get(self.catalog_address + '/avail_devs').text)
        chID = pat['TS_chID']
        # per trovare i nomi dei sensori che possiede quel paziente devo fare un controllo tra i sensori in sensors e i sensori di patients
        sensNames = [sensors['fullName'][i] for i in range(len(sensors['fullName'])) if sensors['devID'][i] in [d['type_ID'] for d in pat['sensors']]] 
           
        # ho trovato il paziente selezionato dal medico tramite inline Keyboard e restituisco una nuova inline keyboard
        # con i possibili sensori tra cui il medico deve scegliere (rimandare all'URL di thingspeak)
        question = 'Select the sensor you are interest about'
        
        self.bot.sendMessage(chat_ID, text=question,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                list(map(lambda c,i: InlineKeyboardButton(text=str(c), url=f"https://thingspeak.com/channels/{chID}/charts/{i}?bgcolor=%23ffffff&color=%23d62020&dynamic=true&results=60&type=line&update=15"), sensNames,range(1,len(sensNames)+1)))
            ]
            )
        )



    ### Routine per messaggi di alert derivanti da Alert service tramite protocollo MQTT ###
    def notify(self,topic,message):
        
        # leggo il messaggio ed estraggo il chat_ID del medico a cui deve essere mandata la notifica 
        msg=json.loads(message) 
        
        print(json.dumps(msg))
        #if topic == topic_alert:       
        alert=msg["message"]
        chat_ID = msg["chat_ID"]
        patient_ID = msg["patient_ID"]
        topic_spit = topic.split("/")[-1]

        if topic_spit == "personal_alert":   
            personal_alert=f"ATTENTION!!!\n{alert}"
            self.bot.sendMessage(chat_ID, text=personal_alert)

        elif topic_spit == "critical_alert":
            patient_ID = msg["patient_ID"]
            critical_alert=f"ATTENTION {patient_ID}!!!\n{alert}"
            self.bot.sendMessage(chat_ID, text=critical_alert)

        #elif topic_spit == "weekly_report":
            


if __name__ == "__main__":

    ####       CODICE DI "DEBUG"                                                        # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("../Catalog/catalog.json",'r') as f:                                              # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                              # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
    port = cat['base_port']
    catalog_address = "http://"+host+":"+port+cat["services"]["catalog_manager"]["address"]
    ####

    with open("./config.json",'r') as f:
        catalog_address = json.load(f)["catalog_address"]

    # Ottiene dal catalog l'indirizzo del servizio di telegram bot e di comunicazione MQTT
    token = json.loads(requests.get(catalog_address+"/get_service_info",params =  {'service_ID':'telegram_bot'}).text)["token"]
    MQTT_info = json.loads(requests.get(catalog_address+"/get_service_info",params =  {'service_ID':'MQTT'}).text)
    broker = MQTT_info["broker"]
    port = MQTT_info["port"]
    base_Topic= MQTT_info["baseTopic"]

    # creo lista di topic a cui il telebot fa da subscriber
    ts =  ['personal_alert_topic','critical_alert_topic','weekly_report_topic']
    topics =  [base_Topic +'/'+ json.loads(requests.get(catalog_address+"/get_service_info", params = {'service_ID':'telegram_bot'}).text)[t] for t in ts]

    bot=TeleBot(token,broker,port, topics, catalog_address)

    print("Bot started ...")
    while True:
        time.sleep(3)
