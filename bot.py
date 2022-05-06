import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import requests
import time
from MyMQTT import *


class TeleBot:
    def __init__(self, token, broker, port, topic, catalog):
        # Local token
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        self.client = MyMQTT("TelegramBotIot", broker, port, self)
        self.catalog = catalog
        self.client.start()
        self.topic = topic
        self.client.mySubscribe(topic)
        
        #self.__message = {'bn': "telegramBot",
        #                  'e':
         #                 [
          #                    {'n': 'switch', 'v': '', 't': '', 'u': 'bool'},
           #               ]
            #              }
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
            doctors = json.loads(requests.get(catalog + '/avail-docs').text)
            for doctor in doctors:
                if doctor['chat_ID'] == chat_ID:
                    doctor_id = doctor['docID']

            # a partire dal doctor id scorro la lista dei pazienti e tengo solamente coloro che hanno quel dottore 
            patients = json.loads(requests.get(catalog + '/get_patients',params= {'doctor_ID':doctor_id}).text)
            print(patients)
            
            #question = 'This is the list of your patients, select the one that you are interest about'
            #self.bot.sendMessage(chat_ID, text=question,
            #    reply_markup=InlineKeyboardMarkup(
            #        inline_keyboard=[
            #            list(map(lambda c: InlineKeyboardButton(text=str(c), callback_data=str(c)), patients))
            #        ]
            #    )
            #)
        
        else:
            # se nessun messaggio e' riconosciuto rimando la lista dei possibili comandi
            self.bot.sendMessage(chat_ID, text="Command not supported. The available command are:\n\
    /start: if you want to know your ChatID\n\
    /report: if you want the report of a patient\n\
    /quit: exit?\n")
            


    ### Routine per rispondere alle inline Keyboard
    def on_callback_query(self,msg):
        query_ID , chat_ID , query_data = telepot.glance(msg,flavor='callback_query') 
        # estraggo lista pazienti a partire dal chatID come fatto in precedenza 
        patients = ['mf', 'hd']
        # possibili periodi temporali di cui il medico vuole il resocont
        TimeLapse = ['day', 'week', 'month']
        for patient in patients:
            if query_data == patient:           
                # ho trovato il paziente selezionato dal medico tramite inline Keyboard e restituisco una nuova inline keyboard
                # con i 3 periodi temporali tra cui il medico deve scegliere (rimandare all'URL di thingspeak)
                question = 'Select the time lapse you are interest about'
                self.bot.sendMessage(chat_ID, text=question,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        list(map(lambda c: InlineKeyboardButton(text=str(c), callback_data=str(c)), TimeLapse))
                    ]
                )
            )



    ### Routine per messaggi di alert derivanti da Alert service tramite protocollo MQTT ###
    def notify(self,topic,message):
        # leggo il messaggio ed estraggo il chat_ID del medico a cui deve essere mandata la notifica 
        msg=json.loads(message)        
        alert=msg["alert"]
        chat_ID = msg["chat_ID"]

        if topic == "telebot/personal_alert":    
            action=msg["action"]
            personal_alert=f"ATTENTION!!!\n{alert}, you should {action}"
            self.bot.sendMessage(chat_ID, text=personal_alert)

        elif topic == "telebot/critical_alert":
            patient_ID = msg["alert"]
            critical_alert=f"ATTENTION!!!\n{patient_ID} is having a {alert}"
            self.bot.sendMessage(chat_ID, text=critical_alert)


if __name__ == "__main__":

    ####       CODICE DI "DEBUG"                                                        # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("./catalog.json",'r') as f:                                               # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                              # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
    port = cat['base_port']
    catalog = "http://"+host+":"+port+cat["services"]["catalog_manager"]["address"]
    ####

    # Ottiene dal catalog l'indirizzo del servizio di telegram bot e di comunicazione MQTT
    s = requests.session()
    token = s.get(catalog+"/service-address?name=telegram_bot")["token"]
    MQTT_info = s.get(catalog+"/service-address?name=MQTT")
    broker = MQTT_info["broker"]
    port = MQTT_info["port"]
    alert_topic = s.get(catalog+"/service-address?name=alert_service")["topic"]
    

    bot=TeleBot(token,broker,port,alert_topic, catalog)

    print("Bot started ...")
    while True:
        time.sleep(3)
