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
		patientID=msg['patient_ID']
		name=msg['full_name']
		latitudine=msg['patient_location']['latitude']
		longitudine=msg['patient_location']['longitude']
		problema=msg['message']
		doctor=f"{msg['doctor_name']} {msg['doctor_surname']}"
		chat_id=msg['chat_ID']
		print(f'{problema}\nSend an ambulance at the coordinates lat:{latitudine:.4f} long:{longitudine:.4f} and contact the personal doctor: {doctor}')
		url_maps= (json.loads(r.get(catalog_address+"/get_service_info",params={'service_ID':'Clinics_client'}).text)['url_maps']).split('&')
		print (f'\nLink pointing at the position: \n\n\t{url_maps[0]}{latitudine}&{url_maps[1]}{longitudine}')



if __name__=='__main__':
	
	with open('config.json','r') as f:                                               
		cat = json.load(f)    

	host = cat["base_host"]                                                        
	port = cat["base_port"]
	catalog_address = "http://"+host+":"+port+cat["address"]
  
    # Ottiene dal catalog l'indirizzo del servizio di location
    # s = requests.session() # session non dovrebbe servire a noi: https://realpython.com/python-requests/#the-session-object
	MQTT_info = json.loads(r.get(catalog_address+"/get_service_info",params={'service_ID':'MQTT'}).text)
	info_clinics=json.loads(r.get(catalog_address +"/get_clinics").text)
	basetopic = MQTT_info['baseTopic']

	while True:
		k=0
		clinics=input('Welcome!\n Write the clinic ID:')
		for p in info_clinics:
			if p['clinic_ID']==clinics:
				k=1
				name_clinics=p['name']
				print(f'Your clinics {name_clinics} is subscriber!')
				# carica i dati relativi al client MQTT e agli indirizzi del location service e del catalog manager
				topic = basetopic+'/'+p["clinic_topic"]
				broker=MQTT_info["broker"]
				port = MQTT_info['port']
				service_ID = p["clinic_ID"]

				c=Clinica1(service_ID,topic,broker,port,catalog_address)
				c.start()

				done=False
				while not done:
					time.sleep(2)
		if k==0:
			print('The clinics is not subscriber!')
			


 