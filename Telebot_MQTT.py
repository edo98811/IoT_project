import json
import time
import requests
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup

from MyMQTT import *


class BotMQTT:
    exposed=True
    def __init__(self,token,broker,port,topic):
        # Local token
        self.tokenBot = token
        self.bot = telepot.Bot(self.tokenBot)
        self.client = MyMQTT("TelegramBotIot", broker, port, self)
        self.client.start()
        self.topic = topic
        self.client.mySubscribe(topic)
        MessageLoop(self.bot, {'chat': self.on_chat_message}).run_as_thread()

    def on_chat_message(self, msg):
        content_type, chat_type, chat_ID = telepot.glance(msg)
        message = msg['text']
        user = msg['from']['first_name']
        msg_tosend=f"Welcome {user} to IoT_IHealthBOT. To complete the registration you have to add this chatID to the web page:\n {chat_ID}!!!"
        if message=="/start":
            self.bot.sendMessage(chat_ID, text=msg_tosend)    
        else:
            self.bot.sendMessage(chat_ID, text="Command not supported")

    def notify(self,topic,message):
        
        msg=json.loads(message)
                
        alert=msg["alert"]
        action=msg["action"]
        chat_ID = msg["ID"]
        alert_tosend=f"ATTENTION!!!\n{alert}, you should {action}"
    
        self.bot.sendMessage(chat_ID, text=alert_tosend)

if __name__ == "__main__":
    conf = json.load(open("settings.json"))
    token = conf["telegramToken"]

    # SimpleSwitchBot
    broker = conf["broker"]
    port = conf["port"]
    topic = "telebot/alert/message"
    sb=BotMQTT(token,broker,port,topic)

    input("press a key to start")
    test=MyMQTT("testIoTBot",broker,port,None)
    test.start()
    for i in range(5):
        message={"alert":i,"action":i*2, "ID":1022322332}
        test.myPublish(topic,message)
        time.sleep(3)
