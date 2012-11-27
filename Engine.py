import logging
import time
import platform, sys
import threading
from Settings import Settings
from Schema import Schemas
from Device import Devices, Device
from DataSource import DataSources, DataSource
from Telldus import Telldus
from Web import Web
from Sun import Sun
from datetime import datetime

class Engine:
	VERSION = '0.0.5'
	running = True

	def __init__(self, logLevel, overwriteTelldus):
		self.schemas = []
		self.devices = []
		self.executedDates = {}
		self.executedDates['start'] = []
		self.executedDates['end'] = []
		self.sunDates = []
		self.logLevel = logLevel
		self.overwriteTelldus = overwriteTelldus

		self.telldus = Telldus(logLevel)
		self.deviceParser = Devices(logLevel)
		self.schemaParser = Schemas(logLevel)
		self.dataSourceParser = DataSources(logLevel)
		self.sun = Sun()
		self.webServer = None
		self.webThread = None

		# logging
		logging.basicConfig(level=logLevel)
		fileLog = logging.FileHandler(Settings.loggingPath)
		self.logger = logging.getLogger('engine')
		self.logger.addHandler(fileLog)

	def load(self):
		# load schemas
		self.logger.info('loading schemas')
		self.schemas = self.schemaParser.load()

		# load devices
		self.logger.info('loading devices')
		self.devices = self.deviceParser.load(self.telldus)

		# load datasources
		self.logger.info('loading datasources')
		self.datasources = self.dataSourceParser.load()

		# starting web service
		self.logger.info('starting web service on port 8080')
		self.webThread = threading.Thread(target = self.startWebService)
		self.webThread.start()

		if len(self.devices) != self.telldus.getNumberOfDevices():
			if not overwriteTelldus:
				self.logger.info('number of devices in lightswitch differs from telldus. run with -o to overwrite telldus.')
				#self.telldus.close()
				#exit(1)
			else:
				self.logger.info('replacing devices in telldus with devices from lightswitch.')
				self.updateTelldusWithDevices()

		if Settings.enableExperimenal:
			self.logger.info(' ')
			self.logger.info(' ')
			self.logger.info('         RUNNING EXPERIMENTAL FEATURES')
			self.logger.info(' ')
			self.logger.info(' ')

		self.startUp()

	def run(self):
		self.logger.info('running on %s platform', platform.system())

		self.logger.info('running application version ' + self.VERSION)

		# lightswitch main loop
		try:
			while self.running:
				now = datetime.today().replace(second=0, microsecond=0)
				weekday = datetime.today().weekday()

				if Settings.enableExperimenal:
					for device in self.devices:
						if device.getSunrise() == 'on' and now not in self.sunDates and now == self.sun.sunrise():
							self.logger.info('turning off device %s because of sunrise', device.getName())
							self.telldus.turnOff(device.getTelldusId())
							device.setStatus('Off')

							self.sunDates.append(now)
						elif device.getSunset() == 'on' and now not in self.sunDates and now == self.sun.sunset():
							self.logger.info('turning on device %s because of sunset', device.getName())
							self.telldus.turnOn(device.getTelldusId())
							device.setStatus('On')

							self.sunDates.append(now)

				for schema in self.schemas:
					startDate = self.schemaParser.getStartDate(schema)

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

				if len(self.executedDates) > 100:
					self.executedDates = {}

				if len(self.sunDates) > 100:
					self.sunDates = []

				time.sleep(1)
		except KeyboardInterrupt:
			pass
		
		#self.webThread.join()
		self.webThread._Thread__stop()
		self.telldus.close()
		sys.exit(3)

	def startWebService(self):
		self.webServer = Web(self, self.deviceParser, self.schemaParser)

	def startUp(self):
		power = {}
		self.logger.debug('synchronizing devices')

		for schema in self.schemas:
			startDate = self.schemaParser.getStartDate(schema)
			now = datetime.today().replace(second=0, microsecond=0)
			weekday = datetime.today().weekday()

			if startDate is not None and\
					startDate < now and\
					weekday in schema.getDays() and\
					self.schemaParser.tryCondition(self.dataSourceParser, schema):

				self.logger.info('adding schema %s to execution', schema.getName())
				
				for device in schema.getDevices().split(','):
					if schema.getPower() == 'dim':
						power[int(device)] = schema.getPower() + ":" + str(schema.getLevel())
					else:
						power[int(device)] = schema.getPower()

		for device in power.keys():
			dev = self.deviceParser.findDevice(device)

			if dev is None:
				self.logger.info('no device with id %d was found', device)
				continue

			if power[device] == 'on':
				self.logger.info('turning on device')
				self.telldus.turnOn(dev.getTelldusId())
				self.telldus.turnOn(dev.getTelldusId())
				dev.setStatus('On')
			elif power[device] == 'off':
				self.logger.info('turning off device')
				self.telldus.turnOff(dev.getTelldusId())
				dev.setStatus('Off')
			elif power[device][0:3] == 'dim':
				self.logger.info('dimming device to level %d', int(power[device][4:]))
				self.telldus.dim(dev.getTelldusId(), int(power[device][4:]))
				dev.setStatus('Dimmed')
				#dev.setStatus('On')
				#self.telldus.dim(dev.getTelldusId(), int((float(power[device][4:]) / float(100)) * float(254)))

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
				device.setStatus('On')
			elif schema.getPower() == 'dim':
				self.logger.info('dimming device to level %d', schema.getProcentualLevel())
				self.telldus.dim(device.getTelldusId(), schema.getLevel())
				device.setStatus('Dimmed ' + schema.getProcentualLevel() + '%')
			else:
				self.logger.info('turning off device')
				self.telldus.turnOff(device.getTelldusId())
				self.telldus.turnOff(device.getTelldusId())
				device.setStatus('Off')

			#time.sleep(1)

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
engine.load()
engine.run()