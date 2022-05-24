from MyMQTT import MyMQTT
import json
import time
import requests as r

class Clinica1(object):					#Subscriber Clinica Alert
	def __init__(self, clientID, topic,broker,port,catalog_address):
		self.clinican=MyMQTT(clientID,broker,port,self)
		self.topic=topic

	def start (self):
		self.clinican.start()
		self.clinican.mySubscribe(self.topic)



	def notify(self,topic, msg):
		#Messaggio ricevuto dall'Alert Service
		msg=json.loads(msg)
		patientID=msg['p_ID']
		latitudine=msg['patient_location']['latitude']
		longitudine=msg['patient_location']['longitude']
		problema=msg['patient_problem']
		doctor=msg['doctor_name']
		chat_id=msg['chat_ID']
		print(f'ATTENTION!\n The patient {patientID} needs an ambulance at the coordinates lat:{latitudine} long:{longitudine}!\n Suffers from {problema} , contact his Doctor {doctor} chat ID number:{chat_id}')
		#stampo a video l'indirizzo del bot che conduce alla mappa
		#print(f'\n https://www.latlong.net/c/?lat=&long=')
		url_maps= (json.loads(r.get(catalog_address+"/get_service_info",params={'service_ID':'Clinics_client'}).text)['url_maps']).split('&')
		print (f'{url_maps[0]}{latitudine}&{url_maps[1]}{longitudine}')



if __name__=='__main__':
	
	with open('config.json','r') as f:                                               
		cat = json.load(f)    

	host = cat["base_host"]                                                        
	port = cat["base_port"]
	catalog_address = "http://"+host+":"+port+cat["address"]
####
  
    # Ottiene dal catalog l'indirizzo del servizio di location
    # s = requests.session() # session non dovrebbe servire a noi: https://realpython.com/python-requests/#the-session-object
	MQTT_info = json.loads(r.get(catalog_address+"/get_service_info",params={'service_ID':'MQTT'}).text)
	info_clinics=json.loads(r.get(catalog_address +"/get_clinics").text)

	while True:
		k=0
		name_clinics=input('Welcome!\n Write the name of clinics:')
		for p in info_clinics:
			if p['name']==name_clinics:
				k=1
				print('Your clinics is subscriber!')
				# carica i dati relativi al client MQTT e agli indirizzi del location service e del catalog manager
				topic = p["clinic_topic"]
				broker=MQTT_info["broker"]
				port = MQTT_info['port']
				service_ID = p["clinic_ID"]

				c=Clinica1(service_ID,topic,broker,port,catalog_address)
				c.start()

				done=False
				while not done:
					time.sleep(1)
		if k==0:
			print('The clinics is not subscriber!')
			


 