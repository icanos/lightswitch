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
			devices += "<tr><td style=\"padding-left: 10px;\">" + device.getName() + "</td><td>" + device.getStatus() + "</td></tr>"

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

	# =========================================================================================
	#
	#  Service routes
	#
	# =========================================================================================

	@route('/service/stop')
	def service_stop():
		# Stopping the service and exiting the application
		Web.instance.engine.running = False
		Web.instance.statusMessage = '<div class="success">Successfully shutdown the system.</div>'

		redirect('/index')

	@route('/service/reload')
	def service_reload():
		Web.instance.engine.load()
		Web.instance.statusMessage = '<div class="information">Reloaded system configuration.</div>'

		redirect('/index')

	@route('/service/log')
	def service_log():
		content = open(Settings.loggingPath, 'r').read()
		return '<pre>' + content + '</pre>'

	# =========================================================================================
	#
	#  Device routes
	#
	# =========================================================================================

	@route('/devices')
	def devices():
		content = open(Web.instance.webdir + '/devices.html', 'r').read()

		devices = ''
		for device in Web.instance.engine.devices:
			devices += '<tr><td style="padding-left: 10px; width: 20px;"><input type="checkbox" name="device_' + str(device.getId()) + '" value="' + str(device.getId()) + '" /></td><td><a href="/devices/edit/' + str(device.getId()) + '">'\
					+ device.getName() + '</a></td><td>' + device.getStatus() + '</td><td>' + device.getType() + '</td>\
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

	@route('/devices/edit/:id')
	def device_edit(id):
		content = open(Web.instance.webdir + '/device_edit.html', 'r').read()

		device = Web.instance.engine.deviceParser.findDevice(int(id))

		if device is None:
			Web.instance.statusMessage = '<div class="error">Unable to find a device with id ' + id + '.</div>'
			redirect('/devices')
			return

		content = content.replace("#ID#", str(device.getId()))
		content = content.replace('#NAME#', str(device.getName()))
		content = content.replace('#REMOTECONTROL#', device.getHouse())
		content = content.replace('#UNIT#', device.getUnit())

		if device.getSunrise() == True:
			content = content.replace("#CHECKEDSUNRISE#", 'checked="checked"')
		else:
			content = content.replace("#CHECKEDSUNRISE#", "")

		if device.getSunset() == True:
			content = content.replace("#CHECKEDSUNSET#", 'checked="checked"')
		else:
			content = content.replace("#CHECKEDSUNSET#", "")

		deviceModel = Web.instance.engine.deviceParser.getDeviceManufacturerByModel(str(device.getModel()))
		content = content.replace("#MODEL#", deviceModel)

		deviceType = Web.instance.engine.deviceParser.getDeviceTypeByModel(str(device.getModel()))
		if deviceType == 'SelfLearningOnOff':
			deviceTypeNiceName = 'Self Learning On/Off'
		elif deviceType == 'SelfLearningDimmer':
			deviceTypeNiceName = 'Self Learning Dimmer'
		elif deviceType == 'CodeSwitch':
			deviceTypeNiceName = 'Code Switch'
		elif deviceType == 'Bell':
			deviceTypeNiceName = 'Bell'

		content = content.replace("#TYPE#", deviceType)
		content = content.replace("#TYPENICENAME#", deviceTypeNiceName)

		return Web.instance.header() + content + Web.instance.footer()

	@route('/devices/save', method = 'POST')
	def device_save():
		if request.forms.action_type == 'add':
			Web.instance.engine.deviceParser.addDevice(request.forms.name, request.forms.model, request.forms.type, request.forms.remote_control_code, request.forms.unit_code, request.forms.sunrise, request.forms.sunset)
		else:
			# update the information
			Web.instance.engine.deviceParser.editDevice(request.forms.id, request.forms.name, request.forms.model, request.forms.type, request.forms.remote_control_code, request.forms.unit_code, request.forms.sunrise, request.forms.sunset)

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

	# =========================================================================================
	#
	#  Schema routes
	#
	# =========================================================================================

	@route('/schemas')
	def schemas():
		content = open(Web.instance.webdir + '/schemas.html', 'r').read()

		# Status messages
		content = content.replace('#STATUSMESSAGE#', Web.instance.statusMessage)
		Web.instance.statusMessage = ''

		schemas = ''
		for schema in Web.instance.engine.schemas:
			devices = '<tr><td colspan="7" style="background-color: #f9f9f9;"><small><strong>DEVICES</strong></small></td></tr>'

			if schema.getPower() == 'on':
				powerType = 'Turn on'
			else:
				powerType = 'Turn off'

			deviceList = schema.getDevices().split(',')
			nod = len(deviceList)

			for d in deviceList:
				device = Web.instance.engine.deviceParser.findDevice(int(d))

				if device is None:
					continue

				devices += '<tr><td colspan="7" style="background-color: #f9f9f9; padding-left: 30px;"><small><div style="float: left;"><a href="/devices/edit/' + str(device.getId()) + '">' + device.getName() + '</a></div><div style="float: left; margin-left: 40px;">' + device.getType() + '</div></small></td>'

			devices += '<tr><td colspan="7">&nbsp;</td></tr>'

			schemas += '<tr><td><input type="checkbox" name="schema_' + str(schema.getId()) + '" value="' + str(schema.getId()) + '" /></td><td><a href="/schemas/edit/' + str(schema.getId()) + '">' + schema.getName() + '</a></td><td>' + powerType + '</td><td style="text-align: center;">' + str(nod) + '</td><td>' + schema.getTime() + '</td><td>' + schema.getDaysString() + '</td><td>' + schema.getCondition() + '</td></tr>'
			schemas += devices

		content = content.replace('#SCHEMAS#', schemas)

		return Web.instance.header() + content + Web.instance.footer()

	# =========================================================================================
	#
	#  Misc routes
	#
	# =========================================================================================

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

	# =========================================================================================
	#
	#  Helper functions
	#
	# =========================================================================================

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
    <script type="text/javascript" src="/web/jquery-1.8.3.min.js"></script>\
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