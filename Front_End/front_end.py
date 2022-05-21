import json
import cherrypy
import requests

class FrontEnd:
    exposed=True

    def __init__(self, catalog_address):
        self.catalog_address = catalog_address
    
    def GET(self, *uri, **params):
                
        # Essendo l'uri corrispondente al nome del file html posso fare direttamente:
        with open(f"./{uri[0]}",'r') as f:
            view=f.read()
        return view

    def POST(self, *uri, **params):

        body = json.loads(cherrypy.request.body.read())
        requests.post(f"{catalog_address}/{uri[0]}", json=body)

    def PUT(self, *uri, **params):

        body = json.loads(cherrypy.request.body.read())
        requests.put(f"{catalog_address}/{uri[0]}", json=body)

#####################################################################################


if __name__ == '__main__':

    ####       CODICE DI "DEBUG"                        # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("config.json",'r') as f:               # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat  = json.load(f)                        # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                             # tutti i codici si adattano al cambio
    port = cat["base_port"]
    catalog_address = f"http://{host}:{port}{cat['address']}"

    # Corregge i 'baseUrl' in tutti i file html che fanno richieste di GET al catalog_manager
    # Per i post viene adottata la strategia indicata dal prof. Orlando, ma per i get di riempimento 
    # dei menù a tendina abbiamo scelto di conservare la richesta diretta al catalog manager
    htmlFiles=[
        'patient-rec.html',
        'clinician-page.html'
    ]

    import re
    for fileName in htmlFiles:
        with open(fileName, 'r') as file:
            lines = file.readlines()

        l = -1;i = -1
        for line in lines:
            l+=1
            if line.find("const baseUrl") != -1:
                break

        i = lines[l].find("//")
        toSub = lines[l][i:]
        new = "//"+host+":"+port+"/catalog_manager'\n"
        lines[l] = re.sub(toSub,new,lines[l])

        with open(fileName, 'w') as file:
            file.writelines(lines)
    ####
    
    # with open("./config.json",'r') as f:
    #   catalog_address = json.load(f)["catalog_address"]

    service_info = json.loads(requests.get(f"{catalog_address}/get_service_info?service_ID=front_end").text)
    
    conf = {
        '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tool.session.on': True
        }
    }

    cherrypy.tree.mount(FrontEnd('./'), '/', conf)

    cherrypy.config.update({'server.socket_host': service_info['host'],
                            'server.socket_port': int(service_info['port'])})
    
    cherrypy.engine.start()
    cherrypy.engine.block()