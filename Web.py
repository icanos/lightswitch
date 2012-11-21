import inspect, os
from bottle import route, run, static_file, redirect, request
from Settings import Settings
from Schema import *
from Device import *
from DataSource import *
from datetime import datetime

class Web:
	# Singleton
	instance = None

	def __init__(self, engine, deviceParser, schemaParser):
		self.webdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '/web'

		self.engine = engine
		#self.schemas = schemas
		#self.devices = devices
		#self.datasources = datasources
		#self.telldus = telldus
		self.deviceParser = deviceParser
		self.schemaParser = schemaParser

		self.statusMessage = ''

		# set singleton instance
		Web.instance = self

		run(host='localhost', port=Settings.webPort)

	@route('/hello/:name')
	def hello(name):
		return '<h1>Hello %s!</h1>' % name.title()

	@route('/web/:file')
	def web(file):
		return static_file(file, root=Web.instance.webdir)

	@route('/index')
	def index():
		content = open(Web.instance.webdir + '/index.html', 'r').read()

		devices = ''
		for device in Web.instance.engine.devices:
			devices += "<tr><td style=\"padding-left: 10px;\">" + device.getName() + "</td><td>" + "Unknown" + "</td></tr>"

		content = content.replace('#DEVICES#', devices)

		schemas = ''
		for schema in Web.instance.engine.schemas:
			schemas += '<tr><td style="padding-left: 10px;">' + schema.getName() + '</td><td>' + str(len(schema.getDevices().split(','))) + '</td><td>' + str(schema.getTime()) + '</td></tr>'

		content = content.replace('#SCHEMAS#', schemas)

		datasources = ''
		for ds in Web.instance.engine.datasources:
			datasources += '<tr><td style="padding-left: 10px;">' + ds.getName() + '</td><td>' + ds.execute() + '</td><td>' + ds.getLastUpdated() + '</td></tr>'

		content = content.replace('#DATASOURCES#', datasources)

		# Status messages
		content = content.replace('#STATUSMESSAGE#', Web.instance.statusMessage)
		Web.instance.statusMessage = ''

		return Web.instance.header() + content + Web.instance.footer()

	@route('/devices')
	def devices():
		content = open(Web.instance.webdir + '/devices.html', 'r').read()

		devices = ''
		for device in Web.instance.engine.devices:
			devices += '<tr><td style="padding-left: 10px; width: 20px;"><input type="checkbox" name="device_' + str(device.getId()) + '" value="' + str(device.getId()) + '" /></td><td>'\
					+ device.getName() + '</td><td>' + device.getStatus() + '</td><td>' + device.getType() + '</td>\
						<td><a href="/power/on/' + str(device.getTelldusId()) + '">Turn on</a> | <a href="/power/off/' + str(device.getTelldusId()) + '">Turn off</a></td></tr>'

		content = content.replace('#DEVICES#', devices)

		# Status messages
		content = content.replace('#STATUSMESSAGE#', Web.instance.statusMessage)
		Web.instance.statusMessage = ''

		return Web.instance.header() + content + Web.instance.footer()

	@route('/devices/add')
	def device_add():
		content = open(Web.instance.webdir + '/device_add.html', 'r').read()

		return Web.instance.header() + content + Web.instance.footer()

	@route('/devices/save', method = 'POST')
	def device_save():
		Web.instance.engine.deviceParser.addDevice(request.forms.name, request.forms.model, request.forms.type, request.forms.remote_control_code, request.forms.unit_code, request.forms.sunrise, request.forms.sunset)
		Web.instance.statusMessage = '<div class="success">Successfully added a device with name ' + request.forms.name + '.</div>'

		# reload all configuration
		Web.instance.engine.load()

		redirect('/devices')

	@route('/devices/remove', method = 'POST')
	def device_remove():
		for elem in request.forms.keys():
			if elem[0:7] == 'device_':
				Web.instance.engine.deviceParser.removeDevice(request.forms[elem])

		Web.instance.statusMessage = '<div class="success">Successfully removed selected devices.</div>'

		# reload all configuration
		Web.instance.engine.load()

		redirect('/devices')

	@route('/power/on/:id')
	def powerOn(id):
		Web.instance.engine.telldus.turnOn(id)

		device = None
		for dev in Web.instance.engine.devices:
			if dev.getTelldusId() == id:
				device = dev
				break

		if device is not None:
			device.setStatus('On')
			Web.instance.statusMessage = '<div class="information">' + device.getName() + ' was turned on.</div>'
		else:
			Web.instance.statusMessage = '<div class="error">No device with id ' + str(id) + ' was found in Telldus.</div>'

		redirect('/devices')

	@route('/power/off/:id')
	def powerOff(id):
		Web.instance.engine.telldus.turnOff(id)

		device = None
		for dev in Web.instance.engine.devices:
			if dev.getTelldusId() == id:
				device = dev
				break

		if device is not None:
			device.setStatus('Off')
			Web.instance.statusMessage = '<div class="information">' + device.getName() + ' was turned off.</div>'
		else:
			Web.instance.statusMessage = '<div class="error">No device with id ' + str(id) + ' was found in Telldus.</div>'

		redirect('/devices')

	def header(self):
		content = '\
<!DOCTYPE html>\
<html>\
	<head>\
    <meta charset="utf-8">\
    <meta http-equiv="X-UA-Compatible" content="IE=edge">\
    <title>lightswitch</title>\
    <link rel="stylesheet" href="/web/style.css" type="text/css" />\
    <link rel="stylesheet" type="text/css" href="http://fonts.googleapis.com/css?family=Open%20Sans" />\
    </head>\
    <body>\
    <div id="wrapper"><div id="header"></div><div id="menu"><ul><li><a href="/index">Home</a></li><li><a href="/devices">Devices</a></li><li><a href="/schemas">Schemas</a></li><li><a href="/datasources">Data Sources</a></li><li><a href="/power">Power</a></li></ul></div><div id="content">'

		return content

	def footer(self):
		content = '\
		</div></div>\
	</body>\
</html>'

		return content