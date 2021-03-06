# TODO: Create a schema class and populate (like Devices and DataSources)

import ConfigParser, os, sys
import logging, platform
from Settings import Settings
from datetime import datetime, timedelta
from pyparsing import Word, nums, alphanums, alphas, oneOf, Group, Combine, Optional
import re

class Schemas:
	def __init__(self, logLevel):
		self.schemas = []
		self.schemaPath = ''
		self.configParser = None

		logging.basicConfig(level=logLevel)
		fileLog = logging.FileHandler(Settings.loggingPath)
		self.logger = logging.getLogger('schemas')
		self.logger.addHandler(fileLog)

		# define lexing conditions
		self.defineConditionSyntax()

	def load(self):
		if platform.system() == 'Linux':
			self.schemaPath = os.path.dirname(sys.argv[0]) + "/config/schemas.cfg"
		else:
			self.schemaPath = os.path.dirname(sys.argv[0]) + "\config\schemas.cfg"

		self.schemas = []

		self.configParser = ConfigParser.ConfigParser()
		self.configParser.readfp(open(self.schemaPath))

		nos = len(self.configParser.sections())
		
		if nos > 0:
			for i in range(1, nos + 1):
				schema = {}
				for item in self.configParser.items('schema_' + str(i)):
					schema[item[0]] = item[1]

				sobj = Schema(i)
				sobj.parse(schema)

				# if there is no schedule (days) add a standard one
				if 'days' not in schema.keys():
					sobj.days = [0, 1, 2, 3, 4, 5 ,6]

				self.schemas += [sobj]
				self.logger.debug('loaded schema %s', schema['name'])

		return self.schemas

	def getStartDate(self, schema):
		if len(schema.getTime()) == 0:
			return None

		timePart = schema.getTime().split(':')
		if len(timePart) > 1:
			return datetime.today().replace(hour=int(timePart[0]), minute=int(timePart[1]), second=0, microsecond=0)
		else:
			return datetime.today().replace(year=1970, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

	def defineConditionSyntax(self):
		num = Combine(Optional(oneOf("+ -")) + Word(nums) + "." +
               Optional(Word(nums)) +
               Optional(oneOf("e E")+Optional(oneOf("+ -")) +Word(nums)))
		op = oneOf("< == > >= <= !=")
		expr = Word(alphanums) + op + num

		return expr

	def tryCondition(self, datasources, schema):
		evalStr = ""
		condition = schema.getCondition()
		parser = self.defineConditionSyntax()

		if len(condition) == 0:
			return True

		p = re.compile(r'( and | or )')
		ands = p.split(condition)

		for i in range(len(ands)):
			if i % 2 == 1:
				continue

			literals = parser.parseString(ands[i].strip().replace('(', '').replace(')', ''))
			ds = datasources.findSource(literals[0])

			if ds is None:
				evalStr += "False "
			else:
				if ands[i].strip()[0:1] == '(':
					evalStr += '('

				evalStr += str(ds.execute()) + " " + literals[1] + " " + literals[2]

				if ands[i].strip()[-1:] == ')':
					evalStr += ')'

			if i < (len(ands) - 1):
				evalStr += ands[i + 1]
			else:
				evalStr += "and "
		
		evalStr = evalStr[0:-4]
		result = eval(evalStr)

		#if result:
		#	self.logger.debug('condition of schema %s was fulfilled', schema.getName())

		return result

	def findSchema(self, id):
		for schema in self.schemas:
			if schema.getId() == id:
				return schema

		return None

	def addSchema(self, name, devices, power, executionTime, days):
		config = self.configParser

		sectionName = 'schema_' + str(len(self.schemas) + 1)
		config.add_section(sectionName)
		config.set(sectionName, 'name', name)
		config.set(sectionName, 'devices', devices)
		config.set(sectionName, 'power', power)
		config.set(sectionName, 'time', executionTime)
		config.set(sectionName, 'days', days)

		with open(self.schemaPath, 'wb') as configfile:
			config.write(configfile)

	def editSchema(self, id, name, devices, power, executionTime, days):
		config = self.configParser

		sectionName = 'schema_' + str(id)
		config.set(sectionName, 'name', name)
		config.set(sectionName, 'devices', devices)
		config.set(sectionName, 'power', power)
		config.set(sectionName, 'time', executionTime)
		config.set(sectionName, 'days', days)

		with open(self.schemaPath, 'wb') as configfile:
			config.write(configfile)

	def removeSchema(self, id):
		config = self.configParser

		sectionName = 'schema_' + str(id)
		config.remove_section(sectionName)

		with open(self.schemaPath, 'wb') as configfile:
			config.write(configfile)

class Schema:
	def __init__(self, id):
		self.id = id
		self.name = ""
		self.power = ""
		self.time = ""
		self.days = []
		self.condition = ""
		self.devices = ""
		self.level = 0

	def getId(self):
		return self.id

	def getName(self):
		return self.name

	def getPower(self):
		return self.power

	def getTime(self):
		return self.time

	def getDays(self):
		return self.days

	def getDaysString(self):
		dayStr = { 0: 'mo', 1: 'tu', 2: 'we', 3: 'th', 4: 'fr', 5: 'sa', 6: 'su' }
		days = ''

		for d in self.days:
			days += dayStr[d] + ", "

		return days[0:len(days) - 2]

	def getCondition(self):
		return self.condition

	def getDevices(self):
		return self.devices

	def getLevel(self):
		return int((float(self.level) / float(100)) * float(254))

	def getProcentualLevel(self):
		return self.level

	def parse(self, schema):
		if 'name' in schema.keys():
			self.name = schema['name']
		else:
			raise Exception('no name was specified with the schema with id %d', int(self.id))

		if 'power' in schema.keys():
			self.power = schema['power']
		else:
			power = "on"

		if 'time' in schema.keys():
			self.time = schema['time']

		if 'days' in schema.keys():
			days = schema['days'].split(',')

			for day in days:
				self.days += [int(day.strip())]

			days.sort()

		if 'condition' in schema.keys():
			self.condition = schema['condition']

		if 'devices' in schema.keys():
			self.devices = schema['devices']

		if 'level' in schema.keys():
			self.level = int(schema['level'])
