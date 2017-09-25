#consider logging each raw NMEA message to a seperate pg table or local file

import socket
import ais.stream
import logging
import json
import psycopg2
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#logging.basicConfig(filename='ais-server.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

try:
	from db_conf import *
	# db_conf file schema:
	# dbname = ""
	# user = ""
	# host = ""
	# pwd = ""
except ImportError:
   logging.critical("could not load db conf file")
   sys.exit()

try:
	conn = psycopg2.connect("dbname='" + dbname + "' user='" + user + "' host='" + host + "' password='" + pwd + "'")
except:
	logging.critical("could not establish connection to db")

cur = conn.cursor()

UDP_IP_ADDRESS = "127.0.0.1"
UDP_PORT_NO = 10110

serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverSock.bind((UDP_IP_ADDRESS, UDP_PORT_NO))
logging.debug("successful server intiation")


def insertdata(data):
	pgpayload = ({"table":dbtable, "data":json.dumps(data)})
	
	try:
		cur.execute("""INSERT into """ + pgpayload['table'] + """ VALUES (%(data)s)""",pgpayload)
		conn.commit()
	except psycopg2.Error as e:
		print e
		logging.warning("could not insert pgpayload into db")


while True:
	try:
	    data, addr = serverSock.recvfrom(1024)
	    payload=data.split(",")

	    messagecontainer = ""

	    pad = int(payload[-1].split('*')[0][-1])
	    msglength = int(payload[1])
	    msgpart = int(payload[2])

	    if msglength == 1:
		    rawmessage = payload[5]
		    decodedmessage = ais.decode(rawmessage,pad)

		    logging.info("SUCCESS: decoded message -> %s", str(decodedmessage))
		    print json.dumps(decodedmessage)
		    insertdata(decodedmessage)

		    messagecontainer = ""
	    
	    else: 
	    	msgcomplete = 0
	    	messagecontainer += payload[5]
	    	
	    	while (msgcomplete == 0): 
				data, addr = serverSock.recvfrom(1024)
				payload=data.split(",")
				rawmessage = payload[5]
				msglength = int(payload[1])
				msgpart = int(payload[2])

				messagecontainer += rawmessage

				logging.debug("incoming data -> %s", str(data))
				logging.debug("message part -> %s", str(msgpart))
				logging.debug("message length -> %s", str(msglength))
				logging.debug("pad ->  %s", str(pad))
				logging.debug("raw message -> %s", str(rawmessage))
				logging.debug("messagecontainer -> %s", str(messagecontainer))

				
				if (msglength == msgpart):
					pad = int(payload[-1].split('*')[0][-1])
					
					#remove escape from test udp
					messagecontainer = messagecontainer.replace("\\","")

					logging.debug("final pad ->  %s", str(pad))
					logging.debug("final messagecontainer -> %s", str(messagecontainer))

					decodedmessage = ais.decode(messagecontainer,pad)
					
					logging.info("SUCCESS: decoded multipart message -> %s", str(decodedmessage))
					print json.dumps(decodedmessage)
					insertdata(decodedmessage)

					messagecontainer = ""
					msgcomplete = 1

	except:
		logging.warning("failed to process message")
    	

# Note code above implemented a strip of "\" from incoming messages given need to add escape when socat-ing on terminal; should be removed in prod
# Example 2 part message
# echo "\!AIVDM,2,1,9,B,53nFBv01SJ<thHp6220H4heHTf2222222222221?50\:454o<\`9QSlUDp,0*09" | socat - UDP4-DATAGRAM:127.0.0.1:10110 && echo "\!AIVDM,2,2,9,B,888888888888880,2\*2E" | socat - UDP4-DATAGRAM:127.0.0.1:10110
# Example 2 part + 1 part message
#echo "\!AIVDM,2,1,9,B,53nFBv01SJ<thHp6220H4heHTf2222222222221?50\:454o<\`9QSlUDp,0*09" | socat - UDP4-DATAGRAM:127.0.0.1:10110 && echo "\!AIVDM,2,2,9,B,888888888888880,2*2E" | socat - UDP4-DATAGRAM:127.0.0.1:10110 && echo "\!AIVDM,1,1,,B,15MnnEPP0qJe?6dGBV1=2wvF2D4h,0*2AthHp6220H4heHTf2222222222221?50\:454o<\`9QSlUDp,0*09" | socat - UDP4-DATAGRAM:127.0.0.1:10110

#example simple execution of ais.decode
# print ais.decode("53nFBv01SJ<thHp6220H4heHTf2222222222221?50:454o<`9QSlUDp888888888888880",2)

# Note: may need to trim "L" from IMO and MMSI in decoded messages
