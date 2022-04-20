import cherrypy
from catalog_manager import catalog
from location_service import location_service

class Root(object):

    @cherrypy.expose
    def GET(self):
        print('benvenuto al servizio')

if __name__ == '__main__':

    catalog_address = 'http://127.0.0.1:8080/catalog_manager' 
    catalog_file = 'catalog.json'

    conf = {
        '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tool.session.on': True
                #cambiare la porta
        }
    }

    cherrypy.tree.mount(location_service(catalog_address), '/location_service', conf)
    cherrypy.tree.mount(catalog(catalog_file), '/catalog_manager', conf)
    # this is needed if you want to have the custom error page
    # cherrypy.config.update({'error_page.400': error_page_400}) # potremmo metterla anche noi questa pagina
    cherrypy.engine.start()
    cherrypy.engine.block()
