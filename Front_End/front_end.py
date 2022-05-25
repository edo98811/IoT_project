import json
import cherrypy
import requests

class FrontEnd:
    exposed=True

    def __init__(self, catalog_address):
        self.catalog_address = catalog_address
    
    def GET(self, *uri, **params):

        if not uri:
            with open(f"./home.html",'r') as f:
                view = f.read()
            return view

        elif uri[0] in ['avail_devs','avail_docs']:
            resp = requests.get(f"{self.catalog_address}/{uri[0]}")
            return resp
        
        else:
            with open(f"./{uri[0]}.html",'r') as f:
                view=f.read()
            return view

    def POST(self, *uri, **params):

        body = json.loads(cherrypy.request.body.read())
        resp = requests.post(f"{self.catalog_address}/{uri[0]}", json=body)
        return resp
        
    def PUT(self, *uri, **params):

        body = json.loads(cherrypy.request.body.read())
        resp = requests.put(f"{self.catalog_address}/{uri[0]}", json=body)
        return resp

# In javascript devo dire ad ajax di aspettarsi un json (dataType = json) in risposta,
# quindi il metodo nel server dovrà ritornare la risposta di cat_man (la quale deve essere un json),
# e all'interno di tale dizionario potrò muovermi utilizzando la notazione [obj].[key] 

#####################################################################################


if __name__ == '__main__':

    ####       CODICE DI "DEBUG"                        # Per motivi di comodità di progettazione e debug, preleva l'indirizzo del 
    with open("config.json",'r') as f:               # catalog manager dal catalog stesso, in modo da poter avere le informazioni 
        cat  = json.load(f)                        # centralizzate, e in caso di necessità cambiando tale indirizzo nel catalog,
    host = cat["base_host"]                             # tutti i codici si adattano al cambio
    port = cat["base_port"]
    catalog_address = f"http://{host}:{port}{cat['address']}"

    service_info = json.loads(requests.get(f"{catalog_address}/get_service_info?service_ID=front_end").text)
    
    conf = {
        '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tool.session.on': True
        }
    }

    cherrypy.tree.mount(FrontEnd(catalog_address), '/', conf)

    cherrypy.config.update({'server.socket_host': service_info['host'],
                            'server.socket_port': int(service_info['port'])})
    
    cherrypy.engine.start()
    cherrypy.engine.block()