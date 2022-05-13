
import requests
import urllib.request
import threading
import random
import json


def thingspeak_post():                                    # Pubblica ogni 15 secondi un valore random nel primo grafico di thingspeak 
    threading.Timer(15,thingspeak_post).start()           # se avete piu di un grafico basta modificare l'header
    val=random.randint(1,30)
    URL="https://api.thingspeak.com/update?api_key="
    KEY="170QQ2K8DG7ZZ5RN"      # chiave di scrittura presa da thingspeak 
    HEADER='&field1={}'.format(val) #essendoci solo un grafico con cui ho provato c'è solo un field1 se se ne vogliono aggiungere altri 
                                    # basta fare ex. '&field1={}&filed2={}&field3={}.....'
    NEW_URL=URL+KEY+HEADER         # unisco per creare il nuovo url 
    print(NEW_URL)
    data=urllib.request.urlopen(NEW_URL) # apro l'url per modificare il grafico
    print(data)     

def thingspeak_get(): # Riceve i dati che sono stati pubblicati nei grafici 
    data=urllib.request.urlopen('https://api.thingspeak.com/channels/1722561/feeds.json?results=2') # modificate solo il nuero del canale (ovvere 1722561) con il vostro
    prova=json.loads(data.read())
    print(json.dumps(prova,indent=4))

if __name__=='__main__':
   # thingspeak_get()
    thingspeak_post()