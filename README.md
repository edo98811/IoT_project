
# MonIoTor
MonIoTor is an IoT platform designed as final project of the Programming for IoT Application exam at Politecnico di Torino. </br>
The main goal of the platform is to *guarantee 24/7 monitoring and support* for patients with assessed medical issues. </br>
MonIoTor is based on a *user registry system* for patients, clinicians and clinics, and the availability of *device connectors*, one per patient, able to link traditional wearable devices to the IoT system. </br>

The platform allows to:</br>
* prevent **critical events** and/or guarantee an immediate response (such as stroke in cardiovascular patients);
* simplify **personal therapies** (such as insulin self-injection for diabetic people);
* automate **signal acquisition** for easier quantification of disease evolution (such as sensorized orthesis for postural disease patients)  
</br></br>

## Catalog
The catalog holds all the useful information about the system such as:</br>

* **Broker** IP and Port
* **Patients registered** as a list where each item is a profile containing:
    * ID (```patient_ID```) and personal info (name and contacts)
    * List of personal devices safety specifics (thresholds and emergency level)
    * Personal doctor ID
    * Device connector info (```service_ID``` and publishing ```topic```)
* **Clinicians registered** as a list where each item is a profile containing: 
    * ID (```doctor_ID```) and personal info (name and contacts)
* **Supported sensor types** as a list where each item is a profile containing:
    * ID (```type_ID```) and specifics (feasible range and unit)
* **Clinics registered** as a list where each item is a profile containing:
    * ID (```clinic_ID```) and position
* Services provided and specific addresses</br>

### Catalog HTTP requests

Replace ```xxx.xxx.xxx.xxx``` with the catalog Ip and Port present in the related config file.</br>
#### GET Requests

Request | Response
--------|----------
```xxx.xxx.xxx.xxx/broker_ip```| broker ip
```xxx.xxx.xxx.xxx/broker_port```|broker port
```xxx.xxx.xxx.xxx/active_arduino```| list of arduino boards running
```xxx.xxx.xxx.xxx/breadCategories```| unique types of bread that are leavening in the system.
```xxx.xxx.xxx.xxx/broker_ip_outside```|broker_ip_outside
```xxx.xxx.xxx.xxx/cases```| return the list of cases that are connected
```xxx.xxx.xxx.xxx/category?caseID=case_name```| returns the bread type stored in the case specified with *case_name* ID
```xxx.xxx.xxx.xxx/db```|database informations (host, database name, password and username).
```xxx.xxx.xxx.xxx/InfluxDB```|InfluxDB parameters (bucket, token and url)
```xxx.xxx.xxx.xxx/telegramBot```|telegram informations (port and token)
```xxx.xxx.xxx.xxx/freeboard```|freeboard host and port
```xxx.xxx.xxx.xxx/thingspeak```|thingspeak upload information
```xxx.xxx.xxx.xxx/thresholds```|list of thresholds where the number of items in the list is refered to a different type of bread
```xxx.xxx.xxx.xxx/topics```|topics on which the system publish/subscribes.



#### POST Requests

Request URI | Body | Response
--------|----------|----------
```xxx.xxx.xxx.xxx/addSensor```|```{'ip': catalog_ip, 'port': catalog_port, 'name': sensorID,  'last_seen': last_seen}```| called sensors to register themselves in the catalog under the raspberry. used also by the ESP to connect the arduino. 
```xxx.xxx.xxx.xxx/addBot```|```{self.catalogPort}/addBot", json={'ip': catalogIP, 'chat_ID': chatID, 'last_seen': time.time()}```| telegram bot is added to the catalog and updates it
```xxx.xxx.xxx.xxx/removeSensor```|.|remove device
```xxx.xxx.xxx.xxx/removeBot```| |when exiting from bot, remove it
```xxx.xxx.xxx.xxx/setThresholds```|```{"type": type,"min_temperature_th": min_T_th,"min_humidity_th": min_hum_th,"min_co2_th": min_co2_th,"max_temperature_th": max_T_th,"max_humidity_th": max_hum_th,"max_co2_th": max_co2_th}```| et thresolds of breadtype defined by *type*
```xxx.xxx.xxx.xxx/setBreadType```|```{'breadtype':breadtype, 'caseID': caseID}```| set the type of bread stored in a specific case.

#### PUT
Request URI | Body | Response
--------|----------|----------
```xxx.xxx.xxx.xxx/setThresholds```|```{"type": type,"min_temperature_th": min_T_th,"min_humidity_th": min_hum_th,"min_co2_th": min_co2_th,"max_temperature_th": max_T_th,"max_humidity_th": max_hum_th,"max_co2_th": max_co2_th}```| set thresolds of breadtype defined by *type*. used by telegramBOT


## Software Usage
1. ___Catalog___
Run ```$ python catalog/catalog.py``` first. The ip and port of the catalog are present in a config file. 

2.  ___Sensors and Devices___
    * Run ```$ pub.py``` Temperature and Humidity sensors
    * Run ```$ co2sensor.py``` Co2 sensors
    * Connect the Arduino board. It will automatically try and form an MQTT connection through the ESP. Must be always up and running. To restart: rest button on esp.
    
Now everything is running!</br>
Pressing a button on the Arduino already shows how the bread type, of the case to which said board is attached, changes between the available options. </br>

To control and analyze: </br>

3. ___Control System___
Looks for the cases present in the system and creates instances of each an everyone of them. Control the behaviour inside them and turns on and off the lamps and the fans of those who exceed the imposed thresholds
To Run it: ```$ python ControlSystem.py``` 

4. ___Freeboard___
To access the Freeboard web page run ```$ python server.py```, which implement the freeboard web service.
Open `http:/127.0.0.1:8080` in your favorite browser.

5. ___Telegram bot___
Run ```$ python telegramBot_InfluxDB.py``` to turn the bot on.

6. ___Telegram bot___
Run ```$ python thingspeak_mqtt.py```

## 
(c) 2021, Brendan David Polidori, Eleonora Gastaldi, Laura Lavezza, Andrea Minardi

