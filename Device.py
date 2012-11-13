import ConfigParser, os, sys
import logging

class Devices:
	def __init__(self, logLevel):
		self.devices = []

		logging.basicConfig(level=logLevel)
		self.logger = logging.getLogger('devices')

	def load(self, telldus):
		from Telldus import Telldus

		devicepath = os.path.dirname(sys.argv[0]) + "\config\devices.cfg"

		config = ConfigParser.ConfigParser()
		config.readfp(open(devicepath))

		nos = len(config.sections())
		
		if nos > 0:
			device = {}
			for i in range(1, nos + 1):
				for item in config.items('device_' + str(i)):
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

		self.telldus = telldus

	def getTelldusId(self):
		return self.tid

	def getId(self):
		return self.id

	def getName(self):
		return self.name

	def getProtocol(self):
		return self.protocol

	def getModel(self):
		return self.model

	def getHouse(self):
		return self.house

	def getUnit(self):
		return self.unit

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
