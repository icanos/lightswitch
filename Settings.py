# Configure paths etc
import platform

class Settings:
	loggingPath = ""

# Specify the logging path
if platform.system() in ['Darwin', 'Linux']:
	Settings.loggingPath = '/var/log/lightswitch.log'
else:
	Settings.loggingPath = 'C:\Temp\lightswitch.log'