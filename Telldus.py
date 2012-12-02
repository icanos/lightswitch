import logging
import platform
from Settings import Settings
from ctypes import c_int, c_ubyte, c_void_p, c_char_p, POINTER, string_at

#Device methods
TELLSTICK_TURNON =         1
TELLSTICK_TURNOFF =        2
TELLSTICK_BELL =           4
TELLSTICK_TOGGLE =         8
TELLSTICK_DIM =           16
TELLSTICK_LEARN =         32
TELLSTICK_EXECUTE =       64
TELLSTICK_UP =           128
TELLSTICK_DOWN =         256
TELLSTICK_STOP =         512

methodsReadable = {1: 'ON',
                   2: 'OFF',
                   4: 'BELL',
                   8: 'TOGGLE',
                   16: 'DIM',
                   32: 'LEARN',
                   64: 'EXECUTE',
                   128: 'UP',
                   256: 'DOWN',
                   512: 'STOP'}

#Sensor value types
TELLSTICK_TEMPERATURE =    1
TELLSTICK_HUMIDITY =       2

sensorValueTypeReadable = {TELLSTICK_TEMPERATURE: 'Temperature',
                           TELLSTICK_HUMIDITY: 'Humidity'}

#Error codes
TELLSTICK_SUCCESS =                       0
TELLSTICK_ERROR_NOT_FOUND =              -1
TELLSTICK_ERROR_PERMISSION_DENIED =      -2
TELLSTICK_ERROR_DEVICE_NOT_FOUND =       -3
TELLSTICK_ERROR_METHOD_NOT_SUPPORTED =   -4
TELLSTICK_ERROR_COMMUNICATION =          -5
TELLSTICK_ERROR_CONNECTING_SERVICE =     -6
TELLSTICK_ERROR_UNKNOWN_RESPONSE =       -7
TELLSTICK_ERROR_SYNTAX =                 -8
TELLSTICK_ERROR_BROKEN_PIPE =            -9
TELLSTICK_ERROR_COMMUNICATING_SERVICE = -10
TELLSTICK_ERROR_CONFIG_SYNTAX =         -11
TELLSTICK_ERROR_UNKNOWN =               -99

#Controller typedef
TELLSTICK_CONTROLLER_TELLSTICK =          1
TELLSTICK_CONTROLLER_TELLSTICK_DUO =      2
TELLSTICK_CONTROLLER_TELLSTICK_NET =      3

#Device changes
TELLSTICK_DEVICE_ADDED =                  1
TELLSTICK_DEVICE_CHANGED =                2
TELLSTICK_DEVICE_REMOVED =                3
TELLSTICK_DEVICE_STATE_CHANGED =          4

#Change types
TELLSTICK_CHANGE_NAME =                   1
TELLSTICK_CHANGE_PROTOCOL =               2
TELLSTICK_CHANGE_MODEL =                  3
TELLSTICK_CHANGE_METHOD =                 4
TELLSTICK_CHANGE_AVAILABLE =              5
TELLSTICK_CHANGE_FIRMWARE =               6


methodsSupportedDefault = 0

class Telldus:
	def __init__(self, logLevel):
		if platform.system() is 'Windows':
			from ctypes import windll, WINFUNCTYPE

			try:
				self.tdlib = windll.LoadLibrary('TelldusCore.dll')
			except WindowsError:
				raise Exception('Telldus Core was not found, are you sure it is installed?')
		else:
			from ctypes import cdll

			try:
				self.tdlib = cdll.LoadLibrary('/usr/local/lib/libtelldus-core.so')
			except OSError:
				try:
					self.tdlib = cdll.LoadLibrary('/usr/lib/libtelldus-core.so')
				except OSError:
					raise Exception('Telldus Core was not found, are you sure it is installed?')

		if self.tdlib is None:
			raise Exception('No Telldus Core library was found')

		self.tdlib.tdInit()

		logging.basicConfig(level=logLevel)
		fileLog = logging.FileHandler(Settings.loggingPath)
		self.logger = logging.getLogger('telldus')
		self.logger.addHandler(fileLog)

	def getNumberOfDevices(self):
		return self.tdlib.tdGetNumberOfDevices()

	def getDeviceId(self, idx):
		return self.tdlib.tdGetDeviceId(int(idx))

	def getDeviceIdFromStr(self, s):
		try:
			id = int(s)
			deviceid = getDeviceId(id)
			return deviceid, getName(deviceid)
		except:
			pass

		for i in range(getNumberOfDevices()):
			if s == getName(getDeviceId(i)):
				return getDeviceId(i), s

		return -1, 'UNKNOWN'

	def getName(self, id):
		getNameFunc = self.tdlib.tdGetName
		getNameFunc.restype = c_void_p

		vp = getNameFunc(id)
		cp = c_char_p(vp)
		s = cp.value

		self.tdlib.tdReleaseString(vp)

		return s

	def turnOn(self, id):
		self.logger.debug('sending turnOn() to device %d', int(id))
		retval = self.tdlib.tdTurnOn(id)

		if retval is not 0:
			getErrorStringFunc = self.tdlib.tdGetErrorString
			getErrorStringFunc.restype = c_void_p

			vp = getErrorStringFunc(retval)
			cp = c_char_p(vp)
			s = cp.value

			self.logger.error('error while trying to turn on device: %s', s)
			self.tdlib.tdReleaseString(vp)

		return retval

	def turnOff(self, id):
		self.logger.debug('sending turnOff() to device %d', id)
		retval = self.tdlib.tdTurnOff(id)

		if retval is not 0:
			getErrorStringFunc = self.tdlib.tdGetErrorString
			getErrorStringFunc.restype = c_void_p

			vp = getErrorStringFunc(retval)
			cp = c_char_p(vp)
			s = cp.value

			self.logger.error('error while trying to turn off device: %s', s)
			self.tdlib.tdReleaseString(vp)

		return retval

	def dim(self, id, level):
		self.logger.debug('sending dim(...) to device %d', id)
		retval = self.tdlib.tdDim(id, level)

		if retval is not 0:
			getErrorStringFunc = self.tdlib.tdGetErrorString
			getErrorStringFunc.restype = c_void_p

			vp = getErrorStringFunc(retval)
			cp = c_char_p(vp)
			s = cp.value

			self.logger.error('error while trying to dim device: %s', s)
			self.tdlib.tdReleaseString(vp)

		return retval

	def learn(self, id):
		self.logger.debug('sending learn(...) to device %d', id)
		retval = self.tdlib.tdLearn(id)

		if retval is not 0:
			getErrorStringFunc = self.tdlib.tdGetErrorString
			getErrorStringFunc.restype = c_void_p

			vp = getErrorStringFunc(retval)
			cp = c_char_p(vp)
			s = cp.value

			self.logger.error('error while trying to learn device: %s', s)
			self.tdlib.tdReleaseString(vp)

		return int(retval)

	def getStatus(self, id):
		state = self.tdlib.tdLastSentCommand(id)
		self.logger.debug('state retrieved from device %s (id: %d)', state, id)

		return state

	def addDevice(self):
		self.logger.debug('creating new device')
		from Device import Device
		return Device(0, self.tdlib.tdAddDevice(), self)

	def removeDevice(self, id):
		self.logger.debug('removing device %d', id)
		return self.tdlib.tdRemoveDevice(id)

	def setName(self, id, name):
		if not isinstance(name, str):
			raise ValueError('name needs to be str')
		if not isinstance(id, int):
			raise ValueError('id needs to be int')

		self.logger.debug('setting name to device %d, new name %s', id, name)
		return self.tdlib.tdSetName(id, name)

	def setProtocol(self, id, protocol):
		return self.tdlib.tdSetProtocol(id, protocol)

	def setModel(self, id, model):
		return self.tdlib.tdSetModel(id, model)

	def setParameter(self, id, param, value):
		return self.tdlib.tdSetDeviceParameter(id, param, value)

	def getProtocol(self, id):
		getProtocolFunc = self.tdlib.tdGetProtocol
		getProtocolFunc.restype = c_void_p

		vp = getProtocolFunc(id)
		cp = c_char_p(vp)
		s = cp.value

		self.tdlib.tdReleaseString(vp)

		return s

	def getModel(self, id):
		getModelFunc = self.tdlib.tdGetModel
		getModelFunc.restype = c_void_p

		vp = getModelFunc(id)
		cp = c_char_p(vp)
		s = cp.value

		self.tdlib.tdReleaseString(vp)

		return s

	def getParameter(self, id, param):
		getParameterFunc = self.tdlib.tdGetDeviceParameter
		getParameterFunc.restype = c_void_p

		vp = getParameterFunc(id, param, None)
		cp = c_char_p(vp)
		s = cp.value

		self.tdlib.tdReleaseString(vp)

		return s

	def findDeviceByName(self, name):
		nrDevices = self.tdlib.tdGetNumberOfDevices()

		for i in range(nrDevices):
			devid = self.tdlib.tdGetDeviceId(i)

			devname = self.getName(devid)
			if devname == name:
				self.logger.debug('setting device id %i to device with name %s', devid, devname)
				return devid

		self.logger.debug('no device id was found for device with name %s', name)
		return -1

	def close(self):
		self.tdlib.tdClose()
