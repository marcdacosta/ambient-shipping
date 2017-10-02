# Ambient Shipping

This repo contains utilities for capturing AIS messages broadcast by passing ships and then joining them with public data sets that reveal what the ships are carrying.

### Overview:
Ambient Shipping enables you to look inside cargo ships. It has two main components:

  - `ship-utils.py`: A simple set of functions that enables (1) the translation between an MMSI and a Vessel's Name and (2) wrappers around the [Enigma Public API](https://public.enigma.com) to query Bill of Lading Import Records for that Vessel to reveal what is inside it.
 
  - `ais-server.py`: A data relay server for relaying decoded AIS transmissions to a remote database server. It is intended to be run on a small linux machine with a SDR (e.g. a raspberry pi) and in proximity to waterways frequented by cargo ships. 

![NY Harbor](https://s3.amazonaws.com/marcdacosta.com/storage/nyharbor.jpg)


### Context:

The [Automatic Identification System (AIS)](https://en.wikipedia.org/wiki/Automatic_identification_system) is a broadcast radio signal that reports a ship's position, speed, heading and other metadata about its movements. It is primarily used for safety and for ships to have situational awareness. The signals are broadcast on two VHF channels (161.975 MHz, 162.025 MHz) and generally have a range of 10-20 miles at sea, although, on land, buildings interfere with the signal and it can be difficult to receive without a clear line of sight for the antenna. 

![AIS Transceiver](https://s3.amazonaws.com/marcdacosta.com/storage/Matsutec-boat-GPS-navigation-equipment-5-6-Color-LCD-Marine-GPS-SBAS-Navigator-w-High-Sensitivity.jpg_640x640.jpg)


There are many different types of AIS messages that are broadcast ([detailed here](https://en.wikipedia.org/wiki/Automatic_identification_system#AIS_messages)) but, most commonly, an AIS transceiver sends basic positional data every 2 to 10 seconds depending on a vessel's speed while underway, and every 3 minutes while a vessel is at anchor.

Using a [RTL-SDR](https://www.amazon.com/NooElec-NESDR-Mini-Compatible-Packages/dp/B009U7WZCA) dongle, these transmissions can be picked up and decoded. The [RTL-AIS](https://github.com/dgiardini/rtl-ais) project is quite useful as a local server which will receive AIS messages and output them on a local host port. It must be run as a background process for `ais-server.py` to function properly.

Example AIS data:

`!AIVDM,1,1,,B,15MwDp0P0hJe>pLGBUq;q?wN2@KI,0*27`

`!AIVDM,1,1,,B,15N85>PP00re>T8GBVmf4?v:2<4R,0*6E`


The [spec](http://catb.org/gpsd/AIVDM.html#_aivdm_aivdo_sentence_layer) for AIS encoding is quite complicated, but convenient tools like Python's [libais](https://pypi.python.org/pypi/libais) make it straightforward to decode. Using this in conjunction with the `ais-server.py` script will enable received messages to be uploaded to a remote database for later analysis.

For instance, a decoded AIS message will look something like this:

`print ais.decode('15PIIv7P00D5i9HNn2Q3G?wB0t0I')` (nb the last portion of the message is the payload to be decoded. see the AIS spec for a fuller explanation.)

```
{  
   u'slot_timeout':7,
   u'sync_state':1,
   u'received_stations':25,
   u'true_heading':511,
   u'sog':0.0,
   u'rot':-731.386474609375,
   u'nav_status':7,
   u'repeat_indicator':0,
   u'raim':False,
   u'id':1,
   u'spare':0,
   u'cog':86.0,
   u'timestamp':41,
   u'y':53.90443420410156,
   u'x':-166.5121307373047,
   u'position_accuracy':0,
   u'rot_over_range':True,
   u'mmsi':369515000,
   u'special_manoeuvre':0
}
```

The MMSI field contains the ship's Maritime Mobile Service Identity number. The MMSI is a unique identifier for the ship's radio that can be used to communicate directly with the ship. MMSIs are regulated and managed internationally by the International Telecommunications Union in Geneva, Switzerland, just as radio call signs are regulated. 


![Bill of Lading](https://s3.amazonaws.com/marcdacosta.com/storage/bill+of+lading.jpg)

The `ship-utils.py` contains a function for looking up the MMSI with the ITU in order to find out the Vessel Name (you can also get the Vessel's satellite phone number if you're interested in giving them a call). If the ship is transporting containers or other commodities, the Vessel Name can be used to query the [Enigma Public API](https://public.enigma.com) to discover what the ship contains. 

The script relies upon data published in the Automated Manifest System by the US Customs and Border Protection. It contains structured copies of the bills of lading of everything that is imported into the United States. A bill of lading is a document that describes a shipment: who sent it, where its going, what it contains, &c. 

### Origin:

Ambient Shipping grew out of a residency of The ![More&More Unlimited](http://www.moreandmore.world/) collective on ![Governor's Island](https://www.google.com/maps/place/Governors+Island/@40.6885841,-74.0281299,15z/data=!3m1!4b1!4m5!3m4!1s0x89c25a7ada7d834f:0x78c2917911c7f535!8m2!3d40.6894501!4d-74.016792) in collaboration with ![Surya Mattu](http://www.suryamattu.com/), ![Sarah Rothberg](http://sarahrothberg.com/) and ![Marina Zurkow](http://www.o-matic.com/) and it was made possible with support from the ![Lower Manhattan Cultural Council](http://lmcc.net/). More&More Unlimited produces critical and artistic work engaging with the impact of maritime shipping on deep oceans and the logistics of global trade.
