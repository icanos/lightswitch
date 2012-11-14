import inspect, os
from bottle import route, run, static_file
from Settings import Settings

class Web:
	# Singleton
	instance = None

	def __init__(self):
		self.service = None
		self.webdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '/web'
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
		content = 'hej'
		return Web.instance.header() + content + Web.instance.footer()

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
    <div id="wrapper"><div id="header"></div><div id="menu"><ul><li>Devices</li><li>Schemas</li><li>Data Sources</li><li>Power</li></ul></div><div id="content">'

		return content

	def footer(self):
		content = '\
		</div></div>\
	</body>\
</html>'

		return content