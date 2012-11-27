# Configure paths etc
import platform

class Settings:
	loggingPath 		= ""
	webPort 			= 8080

	# Stockholm
	# this is used to calculate sunrise/sunset
	latitude 			= 60.48
	longitude			= 15.45

	# EXPERIMENTAL FEATURES
	enableExperimenal	= True

# Specify the logging path
if platform.system() in ['Darwin', 'Linux']:
	Settings.loggingPath = '/var/log/lightswitch.log'
else:
	Settings.loggingPath = 'C:\Temp\lightswitch.log'