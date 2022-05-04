import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
import requests
import time
from MyMQTT import *
import random

class TeleBot:
    def __init__(self, token, broker, port, topic):
        # Local token
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        self.client = MyMQTT("TelegramBotIot", broker, port, self)
        self.client.start()
        self.topic = topic
        #self.__message = {'bn': "telegramBot",
        #                  'e':
         #                 [
          #                    {'n': 'switch', 'v': '', 't': '', 'u': 'bool'},
           #               ]
            #              }
        MessageLoop(self.bot, {'chat': self.on_chat_message,
                               'callback_query': self.on_callback_query}).run_as_thread()


    def on_chat_message(self, msg):
        content_type, chat_type, chat_ID = telepot.glance(msg)
        message = msg['text']
        user = msg['from']['first_name']
        
        if message=="/start":
            start_message = f"Welcome {user} to IoT_IHealthBOT. To complete the registration you have to add this chatID to the web page:\n {chat_ID}!!!"
            self.bot.sendMessage(chat_ID, text=start_message)

        elif message == '/report':
            patients = ['mf', 'hd']
            question = 'This is the list of your patients, select the one that you are interest about'
            self.bot.sendMessage(chat_ID, text=question,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        list(map(lambda c: InlineKeyboardButton(text=str(c), callback_data=str(c)), patients))
                    ]
                )
            )
        
        else:
            self.bot.sendMessage(chat_ID, text="Command not supported. The available command are:\n\
    /start: if you want to know your ChatID\n\
    /report: if you want the report of a patient\n\
    /quit: exit?\n")
            

    def on_callback_query(self,msg):
        query_ID , chat_ID , query_data = telepot.glance(msg,flavor='callback_query')  
        patients = ['mf', 'hd']
        TimeLapse = ['day', 'week', 'month']
        for patient in patients:
            if query_data == patient:           
                question = 'Select the time lapse you are interest about'
                self.bot.sendMessage(chat_ID, text=question,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        list(map(lambda c: InlineKeyboardButton(text=str(c), callback_data=str(c)), TimeLapse))
                    ]
                )
            )


    def notify(self,topic,message):
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

    conf = json.load(open("settings.json"))
    token = conf["telegramToken"]
    broker = conf["broker"]
    port = conf["port"]
    topic = "telebot/critical_alert"
    bot=TeleBot(token,broker,port,topic)

    print("Bot started ...")
    while True:
        time.sleep(3)
