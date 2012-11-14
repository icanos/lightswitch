lightswitch
==================================================================

PLEASE READ THE LICENSE.md FOR MORE INFORMATION ABOUT LICENSING

Home automation solution with Telldus Tellstick written in Python

System Requirements:
 - Python 2.7+ (not tested with Python 3.0, most likely will not work)
 - ctypes python library

Tested on:
 - Windows 7 with Python 2.7.3
 - Raspberry Pi (Raspbian) with Python 2.7.3

Installation:
 Extract to a folder on your system, execute with the following command:

 	python /path/to/Engine.py

 If lightswitch complains about a mismatch between devices in lightswitch and telldus core,
 start the engine with -o to overwrite the devices in telldus core.

 	python /path/to/Engine.py -o

 Configuration:
  Please refer to the examples in devices.cfg, schemas.cfg and datasources.cfg
  in the config/ directory.


 PLEASE REPORT ANY BUGS OR FEATURE REQUESTS TO THE 'ISSUES' PAGE, THANK YOU!