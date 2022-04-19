
from math import dist
import requests


class location_service():
    def __init__(self,catalog,):
        self.catalog = catalog
        self.clinics_pos = requests.get(catalog)
        self.patient_list = requests.get(catalog)

        self.nearest = []

        for patient in self.patient_list 

            self.nearest.append({
                'patient_ID' :'patient_id',
                'clinic_pos':'',
                'patient_pos':'',
                'nearest':'',
            })
            
    

    def GET(self,msg):
        pat_id = msg['patient_id']

        #trova la clinic più vicina

        return nearest_clinic



    def POST(self,msg): #vedere come si fanno e richieste in rest e se si usa il topic cosi 
        pat_pos = msg['pos']

        for clinic,i in enumerate(self.clinics_pos):
            cl_pos = clinic['clinic_pos']

            #calcolo della piu vicina
            if dist < dist_temp:
                dist_temp = dist
                nearest_id = i

        #p_index = filter(lambda patient: self.patient_list['patient_ID'] == msg['pat_id'], people) #come posso ricavare il pateinteindex?
        self.nearest[p_index]['nearest'] == self.clinics_pos[nearest_id]['clinic_id']
        self.nearest[p_index]['patient_pos'] == msg['pos']
        self.nearest[p_index]['clinic_pos'] == self.clinics_pos[nearest_id]['clinic_pos']

    #def update_pos(self): forse non serve


