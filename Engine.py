import logging
import time
import platform, sys
from Schema import Schemas
from Device import Devices, Device
from DataSource import DataSources, DataSource
from Telldus import Telldus
from datetime import datetime

class Engine:
	def __init__(self, logLevel, overwriteTelldus):
		self.schemas = []
		self.devices = []
		self.executedDates = {}
		self.executedDates['start'] = []
		self.executedDates['end'] = []
		self.logLevel = logLevel
		self.overwriteTelldus = overwriteTelldus

		self.telldus = Telldus(logLevel)
		self.deviceParser = Devices(logLevel)
		self.schemaParser = Schemas(logLevel)
		self.dataSourceParser = DataSources(logLevel)

		# logging
		logging.basicConfig(level=logLevel)
		self.logger = logging.getLogger('engine')

	def run(self):
		self.logger.info('running on %s platform', platform.system())

		# load schemas
		self.logger.info('loading schemas')
		self.schemas = self.schemaParser.load()

		# load devices
		self.logger.info('loading devices')
		self.devices = self.deviceParser.load(self.telldus)

		# load datasources
		self.logger.info('loading datasources')
		self.datasources = self.dataSourceParser.load()

		if len(self.devices) != self.telldus.getNumberOfDevices():
			if not overwriteTelldus:
				self.logger.info('number of devices in lightswitch differs from telldus. run with -o to overwrite telldus.')
				self.telldus.close()
				exit(1)
			else:
				self.logger.info('replacing devices in telldus with devices from lightswitch.')
				self.updateTelldusWithDevices()

		self.logger.info('running application')
		# lightswitch main loop
		while True:
			for schema in self.schemas:
				startDate = self.schemaParser.getStartDate(schema)
				now = datetime.today().replace(second=0, microsecond=0)
				weekday = datetime.today().weekday()

				# check if its a start of a schedule
				if (startDate is not None and\
						now == startDate and\
						weekday in schema.getDays() and\
						now not in self.executedDates['start'] and\
						self.schemaParser.tryCondition(self.dataSourceParser, schema)\
					) or (\
						startDate is None and self.schemaParser.tryCondition(self.dataSourceParser, schema) and\
						now not in self.executedDates['start']):

					self.logger.info('executing schema %s', schema.getName())
					self.execute(schema)

					if 'start' in self.executedDates.keys():
						self.executedDates['start'].append(now)
					else:
						self.executedDates['start'] = [now]

			time.sleep(1)

		self.telldus.close()

	def execute(self, schema):
		for id in schema.getDevices().split(','):
			self.logger.debug('looking for device with id %d', int(id))
			device = self.deviceParser.findDevice(int(id))

			if device is None:
				return

			self.logger.debug('device found')
			if schema.getPower() == 'on':
				self.logger.info('turning on device')
				self.telldus.turnOn(device.getTelldusId())
				time.sleep(1)
				self.telldus.turnOn(device.getTelldusId())
			elif schema.getPower() == 'dim':
				self.logger.info('dimming device to level %d', schema.getProcentualLevel())
				self.telldus.dim(device.getTelldusId(), schema.getLevel())
			else:
				self.logger.info('turning off device')
				self.telldus.turnOff(device.getTelldusId())

			time.sleep(1)

	def updateTelldusWithDevices(self):
		self.logger.debug('removing devices from telldus')
		for i in range(self.telldus.getNumberOfDevices()):
			self.telldus.removeDevice(self.telldus.getDeviceId(i))

		for device in self.devices:
			self.logger.debug('adding device %s to telldus', device.getName())

			tdevice = self.telldus.addDevice(len(self.devices))
			tdevice.setName(device.getName())
			tdevice.setProtocol(device.getProtocol())
			tdevice.setModel(device.getModel())
			tdevice.setParameter('house', device.getHouse())
			tdevice.setParameter('unit', device.getUnit())


logLevel = logging.DEBUG

overwriteTelldus = False

for arg in sys.argv:
	if arg == '-o':
		overwriteTelldus = True

engine = Engine(logLevel, overwriteTelldus)
engine.run()