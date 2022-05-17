
from math import dist
import json
import time
import requests as r
import cherrypy

from MyMQTT import *


class location_service():
    exposed=True
    def __init__(self,broker, port, service_ID, topic, catalog_address):
        self.catalog_address = catalog_address
        self.clinics = []
        self.patient_list = []
        self.loc_service = MyMQTT(service_ID, broker, int(port), self)
        self.loc_service.start()
        self.loc_service.mySubscribe(topic)
        self.catalog_address = catalog_address # tutti gli indirizzi si potrebbero salvare nel catalog e prenderli all'inizio con una richiwsta e poi aggiungere un controllo negli errori nel caso 

        print(topic)

    def notify(self,topic, msg):
        print('funzionaaaa')

if __name__=="__main__":
    
    with open("catalog.json",'r') as f:                                                 # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat = json.load(f)                                                              # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                                                             # tutti i codici si adattano al cambio
    port = cat["base_port"]
    catalog_address = "http://"+host+":"+port+cat["services"]["catalog_manager"]["address"]

    conf = {
        '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tool.s ession.on': True
        }
    }
    
    cherrypy.tree.mount(location_service('test.mosquitto.org', 1883, 'funzionaa?', 'Iot_Healthcare/service/#', catalog_address), '/', conf)
      
    cherrypy.config.update({'server.socket_host': "127.0.0.1",
                            'server.socket_port': int(8086)})
    # this is needed if you want to have the custom error page
    # cherrypy.config.update({'error_page.400': error_page_400}) # potremmo metterla anche noi questa pagina
    cherrypy.engine.start()
    cherrypy.engine.block()

