# TODO: Create a schema class and populate (like Devices and DataSources)

import ConfigParser, os, sys
import logging
from datetime import datetime, timedelta
from pyparsing import Word, nums, alphanums, alphas, oneOf, Group, Combine, Optional
import re

class Schemas:
	def __init__(self, logLevel):
		self.schemas = []

		logging.basicConfig(level=logLevel)
		self.logger = logging.getLogger('schemas')

		# define lexing conditions
		self.defineConditionSyntax()

	def load(self):
		schemapath = os.path.dirname(sys.argv[0]) + "\config\schemas.cfg"

		config = ConfigParser.ConfigParser()
		config.readfp(open(schemapath))

		nos = len(config.sections())
		
		if nos > 0:
			for i in range(1, nos + 1):
				schema = {}
				for item in config.items('schema_' + str(i)):
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



class Schema:
	def __init__(self, id):
		self.id = id
		self.name = ""
		self.power = ""
		self.time = ""
		self.days = []
		self.condition = ""
		self.devices = ""

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

	def getCondition(self):
		return self.condition

	def getDevices(self):
		return self.devices

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

		if 'condition' in schema.keys():
			self.condition = schema['condition']

		if 'devices' in schema.keys():
			self.devices = schema['devices']

