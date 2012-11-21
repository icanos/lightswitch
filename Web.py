import inspect, os
from bottle import route, run, static_file, redirect
from Settings import Settings
from Schema import *
from Device import *
from DataSource import *
from datetime import datetime

class Web:
	# Singleton
	instance = None

	def __init__(self, telldus, schemas, devices, datasources):
		self.webdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '/web'

		self.schemas = schemas
		self.devices = devices
		self.datasources = datasources
		self.telldus = telldus

		self.statusMessage = "Test"

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
		for device in Web.instance.devices:
			devices += "<tr><td style=\"padding-left: 10px;\">" + device.getName() + "</td><td>" + "Unknown" + "</td></tr>"

		content = content.replace('#DEVICES#', devices)

		schemas = ''
		for schema in Web.instance.schemas:
			schemas += '<tr><td style="padding-left: 10px;">' + schema.getName() + '</td><td>' + str(len(schema.getDevices().split(','))) + '</td><td>' + str(schema.getTime()) + '</td></tr>'

		content = content.replace('#SCHEMAS#', schemas)

		datasources = ''
		for ds in Web.instance.datasources:
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
		for device in Web.instance.devices:
			devices += '<tr><td style="padding-left: 10px; width: 20px;"><input type="checkbox" name="device[]" value="true" /></td><td>'\
					+ device.getName() + '</td><td>' + device.getStatus() + '</td><td>' + device.getType() + '</td>\
						<td><a href="/power/on/' + str(device.getTelldusId()) + '">Turn on</a> | <a href="/power/off/' + str(device.getTelldusId()) + '">Turn off</a></td></tr>'

		content = content.replace('#DEVICES#', devices)

		# Status messages
		content = content.replace('#STATUSMESSAGE#', Web.instance.statusMessage)
		Web.instance.statusMessage = ''

		return Web.instance.header() + content + Web.instance.footer()

	@route('/power/on/:id')
	def powerOn(id):
		Web.instance.telldus.turnOn(id)

		device = None
		for dev in Web.instance.devices:
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
		Web.instance.telldus.turnOff(id)

		device = None
		for dev in Web.instance.devices:
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
    <link rel="stylesheet" href="web/style.css" type="text/css" />\
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