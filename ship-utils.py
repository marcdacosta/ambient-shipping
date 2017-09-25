import requests
import dateutil.parser
from lxml import html
import math


# ABOUT THIS SCRIPT
# These functions will enable you to go from an `MMSI` to a `Vessel Name`. 
# Query that `Vessel Name` to find its most recent `Port of Call`. 
# And then to discover the contents of the `Containers` it unloaded at that `Port of Call`.

#Configuration variables
billoflading_summary_2017_datasetid = "0293cd20-8580-4d30-b173-2ac27952b74b"
billoflading_cargo_2017_datasetid = "d416ba07-6be9-4f13-9793-370fe715b9c1"
row_limit = 200

#Testing variables
mmsi = "211776000"
vessel_name = "MAERSK IDAHO"
shipment_id = "2017011045018"
container_number = "TEMU6379303"


def find_most_recent_snapshotid(dataset_id):
	# for a particular enigma dataset, find the most recent update of the table.
	url = "https://public.enigma.com/api/datasets/" + dataset_id
	r = requests.get(url)
	most_recent_snapshot_payload = r.json()
	most_recent_snapshot = most_recent_snapshot_payload['current_snapshot']['id'] #most recent Enigma data snapshot for given dataset_id
	return most_recent_snapshot


def find_most_recent_arrival(vessel_name):
	# find most recent lading summary table snapshot id
	billoflading_summary_snapshotid = find_most_recent_snapshotid(billoflading_summary_2017_datasetid)

	# for that id, find most recent arrival
	url = "https://public.enigma.com/api/snapshots/" + billoflading_summary_snapshotid + "??&query_mode=advanced&query=(vessel_name%3A(" + vessel_name + "))&stats=true&row_limit=200&row_offset=0"
	r = requests.get(url)	
	most_recent_arrival = r.json()
	most_recent_arrival_date = most_recent_arrival['stats']['actual_arrival_date']['max_as_string'].split("T")[0] #most recent date of a bill of lading for that vessel

	most_recent_shipments(vessel_name,most_recent_arrival_date)


def most_recent_shipments(vessel_name,most_recent_arrival,page=1):
	# generate list of shipments for a specific vessel arriving at a specific date

	# gather variables
	billoflading_summary_snapshotid = find_most_recent_snapshotid(billoflading_summary_2017_datasetid)
	row_offset = (page * row_limit) - row_limit

	url = "https://public.enigma.com/api/snapshots/" + billoflading_summary_snapshotid + "??&query_mode=advanced&query=(vessel_name%3A(" + vessel_name + "))%26%26(actual_arrival_date:[" + most_recent_arrival + " TO " + most_recent_arrival + "])&row_limit=" + str(row_limit) + "&row_offset=" + str(row_offset)
	
	r = requests.get(url)
	shipments_array = r.json()

	total_pages = int(math.ceil(shipments_array['table_rows']['count']/float(row_limit)))

	for row in shipments_array['table_rows']['rows']:
		print row[6]
		shipment_id = row[0]
		container_number = row[23]
		consignee_name = row[13]
		shipper_name = row[18]
		tarrif_code = row[27]
		cargo_desc = row[26]
		foreign_port_of_lading = row[6]
		final_destination = row[10]

		print "id: " + shipment_id + " CONTAINER: " + str(container_number) + " ORIGIN: " + foreign_port_of_lading + " TO: " +  str(consignee_name) + " SHIPPER: " + str(shipper_name) + " CONTENTS: " + str(cargo_desc) + " -- tariff code: " + str(tarrif_code)

	if page != total_pages:
		page += 1
		most_recent_shipments(vessel_name,most_recent_arrival,page)


def things_in_container(container_number, shipment_id = ""):
	# if shipment_id is blank then will return everything in that container this year; otherwise, it will return shipment contents for specific arrival date
	billoflading_cargo_snapshotid = find_most_recent_snapshotid(billoflading_cargo_2017_datasetid)

	if (shipment_id != ""):
		url = "https://public.enigma.com/api/snapshots/" + billoflading_cargo_snapshotid + "??&query_mode=advanced&query=(identifier%3A(" + shipment_id + "))%26%26(container_number%3A(" + container_number + "))&row_limit=200&row_offset=0"
		r = requests.get(url)
		container_cargo_array = r.json()
		return container_cargo_array

	else:
		url = "https://public.enigma.com/api/snapshots/" + billoflading_cargo_snapshotid + "??&query_mode=advanced&query=(container_number%3A(" + container_number + "))&row_limit=200&row_offset=0"
		r = requests.get(url)
		container_cargo_array = r.json()
		return container_cargo_array


def get_vessel_details(mmsi):
	# look up vessel name from the vessel's Mobile Maritime Subscriber Identifier (mmsi)
	data= {
	    'lang':'en',
		'lgg':7,
		'p':1,
		'sh_name':'',
		'sh_callsign':'',
		'sh_mmsi': mmsi,
		'cgaid':0,
		'sh_epirb_id':'',
		'sh_epirb_hex':'',
		'sh_imo_nbr':''
	    }
	r = requests.post('http://www.itu.int/online/mms/mars/ship_search.sh', data=data)

	page = r.text.split("\n")
	for x in page:
		if "<A HREF=ship_detail.sh" in x:
			link = "http://www.itu.int/online/mms/mars/" + x.split("<A HREF=")[1].split(">")[0]
			print link
			vessel_name = link.split("&")[2].replace("+"," ")
			return vessel_name

		
# These functions will enable you to go from an MMSI to a Vessel Name. 
# Query that vessel name to find its most recent port of call. 
# And then to discover the contents of the containers it unloaded at that port.
vessel_name = get_vessel_details(mmsi)
find_most_recent_arrival(vessel_name)
print things_in_container(container_number, shipment_id) #should be applied for each in the results of `find_most_recent_arrival`



