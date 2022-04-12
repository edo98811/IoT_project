import cherrypy
from catalog_manager import catalog
from location_service import location_service

if __name__ == '__main__':
    conf = {
        '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tool.session.on': True
        }
    }
    cherrypy.tree.mount(location_service(), '/location service', conf)
    cherrypy.tree.mount(catalog(), '/catalog_manager', conf)
    # this is needed if you want to have the custom error page
    # cherrypy.config.update({'error_page.400': error_page_400})
    cherrypy.engine.start()
    cherrypy.engine.block()
