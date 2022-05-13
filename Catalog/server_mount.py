import json
import requests
import cherrypy
import re
from catalog_manager import catalog
from location_service import location_service

class FrontEnd(object):
    exposed=True

    def __init__(self,base):
        self.basePath = base 
    
    def GET(self,*uri,**params):
        # Essendo l'uri corrispondente al nome del file html posso fare direttamente:
        with open(self.basePath+'/'+uri[0],'r') as f:
            view=f.read()
        return view
            
        # if uri[0] == "home.html":

        #     # Carica l'html della home
        #     f=open(self.basePath+'/'+uri[0],'r')
        #     view=f.read()
        #     f.close()
        #     return view

        # elif uri[0] == "patient-rec.html":
            
        #     # Carica l'html del form
        #     f=open(self.basePath+'/'+uri[0],'r')
        #     view=f.read()
        #     f.close()
        #     return view
            
        # elif uri[0] == "clinician-rec.html":
            
        #     # Carica l'html del form
        #     f=open(self.basePath+'/'+uri[0],'r')
        #     view=f.read()
        #     f.close()
        #     return view

        # elif uri[0] == "clinics-rec.html":
            
        #     # Carica l'html del form
        #     f=open(self.basePath+'/'+uri[0],'r')
        #     view=f.read()
        #     f.close()
        #     return view

class Root(object):

    @cherrypy.expose
    def GET(self):
        print('benvenuto al servizio')

if __name__ == '__main__':

    catalog_file = './catalog.json'

    # Estrae dal catalog host e port in modo che in caso sia 
    # necessario cambiarli è possibile cambiarli direttamente da lì una volta per tutte
    with open(catalog_file,'r') as f:
        cat = json.load(f)

    host = cat["base_host"]
    port = cat["base_port"]

    # Corregge i 'baseUrl' in tutti i file html che fanno richieste di GET/POST al catalog_manager
    htmlFiles=[
        'front/patient-rec.html',
        'front/clinician-rec.html',
        'front/clinics-rec.html'
    ]

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
    
    # Definisce l'url del catalog manager
    catalog_address = "http://"+host+":"+port+"/catalog_manager"

    conf = {
        '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tool.session.on': True
                #cambiare la porta
        }
    }

    cherrypy.tree.mount(location_service(catalog_address), '/location_service', conf)
    cherrypy.tree.mount(catalog(catalog_file), '/catalog_manager', conf)
    cherrypy.tree.mount(FrontEnd("./front"), '/', conf)
    # MONTARE IN MAIN DIVERSI
       
    cherrypy.config.update({'server.socket_host':host,
                            'server.socket_port':int(port)})
    # this is needed if you want to have the custom error page
    # cherrypy.config.update({'error_page.400': error_page_400}) # potremmo metterla anche noi questa pagina
    cherrypy.engine.start()
    cherrypy.engine.block()
