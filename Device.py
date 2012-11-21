import ConfigParser, os, sys
import logging, platform
from Settings import Settings

class Devices:
	def __init__(self, logLevel):
		self.devices = []
		self.configParser = None
		self.telldus = None
		self.devicePath = ""

		self.protocols = { 'Nexa': 'arctech', 'GAO': 'risingsun', 'Waveman': 'waveman', 'Elro': 'sartano', 'HomeEasy': 'arctech', 'Intertechno': 'arctech', 'Kjell och Company': 'risingsun', 'KlikAndKlikUit': 'arctech', 'Chacon': 'arctech', 'Proove': 'arctech', 'Sartano': 'sartano', 'CoCo': 'arctech', 'Roxcore': 'brateck', 'Ikea': 'ikea', 'HQ': 'fuhaote', 'Conrad': 'risingsun', 'Kappa': 'arctech', 'UPM': 'upm', 'X10': 'x10', 'Otio': 'risingsun', 'Ecosavers': 'silvanchip', 'Brennenstuhl': 'sartano', 'Hasta': 'hasta' }
		self.types = { 'SelfLearningOnOff': 'selflearning-switch', 'SelfLearningDimmer': 'selflearning-dimmer', 'CodeSwitch': 'codeswitch', 'Bell': 'bell' }

		logging.basicConfig(level=logLevel)
		fileLog = logging.FileHandler(Settings.loggingPath)
		self.logger = logging.getLogger('devices')
		self.logger.addHandler(fileLog)

	def load(self, telldus):
		from Telldus import Telldus

		self.telldus = telldus
		self.devices = []

		if platform.system() == 'Linux':
			self.devicePath = os.path.dirname(sys.argv[0]) + "/config/devices.cfg"
		else:
			self.devicePath = os.path.dirname(sys.argv[0]) + "\config\devices.cfg"

		self.configParser = ConfigParser.ConfigParser()
		self.configParser.readfp(open(self.devicePath))

		nos = len(self.configParser.sections())
		
		if nos > 0:
			device = {}
			for i in range(1, nos + 1):
				for item in self.configParser.items('device_' + str(i)):
					device[item[0]] = item[1]

				# try to find the device in Telldus Core based on device name
				devid = telldus.findDeviceByName(device['name'])

				dobj = Device(i, devid, telldus)
				dobj.parse(device)
				self.devices += [dobj]
				self.logger.debug('loaded device %s', device['name'])

		return self.devices

	def findDevice(self, id):
		for device in self.devices:
			if device.getId() == id:
				return device

		return None

	def findDeviceByTelldusId(self, id):
		for device in self.devices:
			if device.getTelldusId() == id:
				return device

		return None

	def addDevice(self, name, model, type, house, unit, sunrise, sunset):
		config = self.configParser

		if sunrise is None or len(sunrise) == 0:
			sunrise = "off"

		if sunset is None or len(sunset) == 0:
			sunset = "off"

		protocol = self.protocols[model]
		unitModel = self.types[type] + ':'

		# TODO: Ugly! Fix this later on
		if type == 'Kjell och Company':
			unitModel += 'kjelloco'
		else:
			unitModel += model.lower()

		sectionName = 'device_' + str(len(self.devices) + 1)
		config.add_section(sectionName)
		config.set(sectionName, 'name', name)
		config.set(sectionName, 'protocol', protocol)
		config.set(sectionName, 'model', unitModel)
		config.set(sectionName, 'house', house)
		config.set(sectionName, 'unit', unit)
		config.set(sectionName, 'sunrise', sunrise)
		config.set(sectionName, 'sunset', sunset)

		with open(self.devicePath, 'wb') as configfile:
			config.write(configfile)

		device = self.telldus.addDevice()
		device.setName(str(name))
		device.setProtocol(protocol)
		device.setModel(model)

	def removeDevice(self, id):
		config = self.configParser

		sectionName = 'device_' + id
		config.remove_section(sectionName)

		with open(self.devicePath, 'wb') as configfile:
			config.write(configfile)

		device = self.findDevice(int(id))

		#if device is not None:
		self.telldus.removeDevice(device.getTelldusId())

class Device:
	def __init__(self, id, tid, telldus):
		self.id = int(id)
		self.tid = int(tid)
		self.name = ""
		self.protocol = ""
		self.model = ""
		self.house = ""
		self.unit = ""
		self.sunrise = False
		self.sunset = False
		self.status = "Unknown"

		self.telldus = telldus

	def getTelldusId(self):
		return self.tid

	def getId(self):
		return self.id

	def getName(self):
		return str(self.name)

	def getProtocol(self):
		return self.protocol

	def getModel(self):
		return self.model

	def getHouse(self):
		return self.house

	def getUnit(self):
		return self.unit

	def getType(self):
		if self.model == 'selflearning-switch:nexa':
			return "Self-Learning Nexa Switch"

		# TODO: Add more devices

		return "Unknown"

	def getStatus(self):
		return self.status

	def setStatus(self, status):
		self.status = status

	def setName(self, name):		
		self.name = name
		return self.telldus.setName(self.tid, name)

	def setProtocol(self, protocol):
		self.protocol = protocol
		return self.telldus.setProtocol(self.tid, protocol)

	def setModel(self, model):
		self.model = model
		return self.telldus.setModel(self.tid, model)

	def setParameter(self, param, value):
		return self.telldus.setParameter(self.tid, param, value)

	def parse(self, device):
		if 'name' in device.keys():
			self.name = device['name'].decode('utf8')
		else:
			raise Exception('No name was provided to the device with id %d', self.tid)

		if 'protocol' in device.keys():
			self.protocol = device['protocol']
		else:
			raise Exception('No protocol was provided to the device with id %d', self.tid)

		if 'model' in device.keys():
			self.model = device['model']
		else:
			raise Exception('No model was provided to the device with id %d', self.tid)

		if 'house' in device.keys():
			self.house = device['house']
		else:
			raise Exception('No house was provided to the device with id %d', self.tid)

		if 'unit' in device.keys():
			self.unit = device['unit']
		else:
			raise Exception('No unit was provided to the device with id %d', self.tid)

		if 'sunrise' in device.keys():
			if device['sunrise'] == 'on':
				self.sunrise = True

		if 'sunset' in device.keys():
			if device['sunset'] == 'on':
				self.sunset = True

		if self.telldus.getProtocol(self.tid) != self.protocol:
			self.telldus.setProtocol(self.tid, self.protocol)

		if self.telldus.getModel(self.tid) != self.model:
			self.telldus.setModel(self.tid, self.model)
