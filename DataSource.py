import xml.etree.ElementTree as ET
import ConfigParser, os, sys
import logging, json, platform, time
from Settings import Settings
from urllib import urlopen
from datetime import datetime

class DataSources:
	def __init__(self, logLevel):
		self.sources = []

		logging.basicConfig(level=logLevel)
		fileLog = logging.FileHandler(Settings.loggingPath)
		self.logger = logging.getLogger('devices')
		self.logger.addHandler(fileLog)
		self.logLevel = logLevel

	def load(self):
		if platform.system() == 'Linux':
			datasourcepath = os.path.dirname(sys.argv[0]) + "/config/datasources.cfg"
		else:
			datasourcepath = os.path.dirname(sys.argv[0]) + "\config\datasources.cfg"

		config = ConfigParser.ConfigParser()
		config.readfp(open(datasourcepath))

		nos = len(config.sections())
		
		if nos > 0:
			source = {}
			for i in range(1, nos + 1):
				for item in config.items('datasource_' + str(i)):
					source[item[0]] = item[1]

				dobj = DataSource(self.logLevel, source['id'])
				dobj.parse(source)
				self.sources += [dobj]
				self.logger.debug('loaded datasource %s', source['name'].decode('utf8'))

		return self.sources

	def findSource(self, name):
		for source in self.sources:
			if source.getName() == name.decode('utf8'):
				return source

		return None

class DataSource:
	def __init__(self, logLevel, id):
		self.name = ""
		self.url = ""
		self.id = int(id)
		self.parse_start = 0
		self.parse_end = 0
		self.parse_all = "off"
		self.parse_xpath = ""
		self.parse_json = ""
		self.parse_type = "text"
		self.interval = 5
		self.bad_response_use_previous = "on"

		self.seconds_elapsed = 0
		self.first_run = True
		self.current_value = -10000.0
		self.previous_value = -10000.0
		self.last_updated = None

		logging.basicConfig(level=logLevel)
		fileLog = logging.FileHandler(Settings.loggingPath)
		self.logger = logging.getLogger('device')
		self.logger.addHandler(fileLog)

	def execute(self):
		self.seconds_elapsed += 1
		
		if (self.seconds_elapsed >= (self.interval * 60)) or self.first_run:
			self.logger.debug('getting content from data source %s', self.name)

			# execute the fetching stuff
			content = urlopen(self.url).read()
			self.first_run = False
			
			self.previous_value = self.current_value

			if 'xml' == self.parse_type:
				self.current_value = self.parseXmlValue(content)
			elif 'json' == self.parse_type:
				self.current_value = self.parseJsonValue(content)
			elif 'text' == self.parse_type:
				self.current_value = self.parseTextValue(content)
				
			if self.previous_value != self.current_value:
				self.logger.debug('new value retrieved %s (old: %s)', self.current_value, self.previous_value)

			self.last_updated = datetime.today().replace(second=0, microsecond=0)

			# todo: implement bad value handling

			# reset the seconds counter
			self.seconds_elapsed = 0

			return self.current_value

		return self.current_value

	def parseXmlValue(self, content):
		root = ET.fromstring(content)
		node = root.findall(self.parse_xpath)

		if len(node) > 0:
			return node[0]

		return 0.0

	def parseJsonValue(self, content):
		data = json.load(content)
		raise Exception('json parsing is not yet implemented')

	def parseTextValue(self, content):
		if 'on' == self.parse_all:
			return content.strip()

		return content[self.parse_start:self.parse_end].strip()

	def getName(self):
		return self.name

	def getId(self):
		return self.id

	def getLastUpdated(self):
		if self.last_updated is None:
			return ''

		return str(self.last_updated)

	def getUrl(self):
		return self.url

	def getParseStart(self):
		return self.parse_start

	def getParseEnd(self):
		return self.parse_end

	def getParseAll(self):
		return self.parse_all

	def getParseXpath(self):
		return self.parse_xpath

	def getParseJson(self):
		return self.parse_json

	def getParseType(self):
		return self.parse_type

	def getInterval(self):
		return self.interval

	def getBadResponseUsePrevious(self):
		return self.bad_response_use_previous

	def parse(self, source):
		if 'name' in source.keys():
			self.name = source['name']
		else:
			raise Exception('No name was provided to the source with id %d', self.id)

		if 'url' in source.keys():
			self.url = source['url']
		else:
			raise Exception('No url was provided with the data source, url is needed. data source %d', self.id)

		if 'parse_start' in source.keys():
			self.parse_start = int(source['parse_start'])

		if 'parse_end' in source.keys():
			self.parse_end = int(source['parse_end'])

		if 'parse_all' in source.keys():
			self.parse_all = source['parse_all']

		if 'parse_type' in source.keys():
			self.parse_type = source['parse_type']

		if 'parse_xpath' in source.keys():
			self.parse_xpath = source['parse_xpath']

		if 'parse_json' in source.keys():
			self.parse_json = source['parse_json']

		if 'interval' in source.keys():
			self.interval = int(source['interval'])
		else:
			raise Exception('interval is needed in order to enable a data source. data source %s', self.id)

		if 'bad_response_use_previous' in source.keys():
			self.bad_response_use_previous = source['bad_response_use_previous']

		if self.parse_type != 'text' and self.parse_type != 'xml' and self.parse_type != 'json':
			raise Exception('supported parse types is: text, xml or json. data source %s', self.id)
