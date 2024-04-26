import sys
import os
import copy
import Live
import contextlib
from re import *
from itertools import chain

from ableton.v2.base import nop, clamp, flatten, depends, listenable_property, listens, listens_group, liveobj_changed, liveobj_valid, EventObject
from ableton.v2.control_surface import ControlSurface, Component, ControlElement, NotifyingControlElement, InputSignal
from ableton.v2.control_surface.device_provider import DeviceProvider
from ableton.v2.control_surface.elements import ButtonElement, ButtonMatrixElement, SysexElement, DisplayDataSource, DisplayElement
from ableton.v2.control_surface.control import ControlManager
from ableton.v2.base.task import *
from ableton.v2.base import Event, listens, listens_group, Signal, in_range, Disconnectable, listenable_property
from ableton.v2.control_surface.internal_parameter import InternalParameter
from ableton.v2.control_surface.input_control_element import MIDI_NOTE_TYPE

from aumhaa.v3.control_surface.components import DeviceSelectorComponent, MonoParamComponent, MonoDeviceComponent
from aumhaa.v3.control_surface.mod_devices import *
from aumhaa.v3.base.debug import initialize_debug
from aumhaa.v3.control_surface.elements import generate_strip_string

INITIAL_SCROLLING_DELAY = 5
INTERVAL_SCROLLING_DELAY = 1

CS_LIST_KEY = 'control_surfaces'

LOCAL_DEBUG = True
debug = initialize_debug(local_debug = LOCAL_DEBUG)


class DisplayParameter(InternalParameter):

	def __init__(self, *a, **k):
		super(DisplayParameter, self).__init__(*a, **k)

	def set_name(self, name):
		#debug(self._name, 'set_name:', name)
		self._name = name

	def set_value(self, value):
		#debug(self._name, 'set_value:', value)
		self._value = value

	def _get_value(self):
		return self._value

	def _set_value(self, new_value):
		self._value = new_value

	value = property(_get_value, _set_value)


class ParamHolder(ControlManager, EventObject):

# class ParamHolder(Component):
	__subject_events__ = (Event(name='value', signal=InputSignal, override=True),)
	_input_signal_listener_count = 0

	__doc__ = ' Simple class to hold the owner of a Device.parameter and forward its value when receiving updates from Live, or update its value from a mod '
	_parameter = None
	_feedback = True
	_report = True

	def __init__(self, parent, index, control_prefix = 'Encoder', send_via_pipe = True, *a, **k):
		self._index = index
		self._control_name = control_prefix+'_'+str(index)
		self._parent = parent
		self._send_via_pipe = send_via_pipe
		super(ParamHolder, self).__init__(*a, **k)


	def set_control_prefix(self, control_prefix):
		self._control_name = str(control_prefix)+'_'+str(self._index)


	@listenable_property
	def parameter(self):
		return self._parameter

	@listenable_property
	def display_value(self):
		return ' ' if not liveobj_valid(self._parameter) else self._parameter.str_for_value(self._parameter.value)
	
	@listenable_property
	def display_name(self):
		return ' ' if not liveobj_valid(self._parameter) else self._parameter.name

	@listenable_property
	def normalized_value(self):
		return 0 if not liveobj_valid(self._parameter) else ((self._parameter.value - self._parameter.min) / (self._parameter.max - self._parameter.min))

	@parameter.setter
	def parameter(self, parameter, *a):
		self._parameter = parameter
		self._value_change.subject = parameter
		self.notify_display_name(self.display_name, self)
		self.notify_display_value(self.display_value, self)
		self.notify_normalized_value(self.normalized_value, self)
	

	@listens('value')
	def _value_change(self, *a):
		self.notify_display_value(self.display_value, self)
		self.notify_normalized_value(self.normalized_value, self)


	def _change_value(self, value):
		if(self._parameter != None):
			if(self._parameter.is_enabled):
				self._feedback = False
				newval = float(float(float(value)) * float(self._parameter.max - self._parameter.min)) + self._parameter.min
				#debug('newval:', newval)
				self._parameter.value = newval


class NoDevice(object):
	__doc__ = 'Dummy Device with no parameters and custom class_name that is used when no device is selected, but parameter assignment is still necessary'


	def __init__(self):
		self.class_name = 'NoDevice'
		self.parameters = []
		self.canonical_parent = None
		self.can_have_chains = False
		self.name = 'NoDevice'


	def add_name_listener(self, callback=None):
		pass


	def remove_name_listener(self, callback=None):
		pass


	def name_has_listener(self, callback=None):
		return False


	def add_parameters_listener(self, callback=None):
		pass


	def remove_parameters_listener(self, callback=None):
		pass


	def parameters_has_listener(self, callback=None):
		return False


	def store_chosen_bank(self, callback=None):
		pass


class ModParameterProxy(ControlManager, EventObject):


	_name = 'ModParameterProxy'
	_value = 0

	def __init__(self, parameter = None, *a, **k):
		super(ModParameterProxy, self).__init__(*a, **k)


class ModDeviceProxy(ControlManager, EventObject):

	class_name = 'ModDeviceProxy'
	_name = 'ModDeviceProxy'
	_parameters = []
	_alted = False

	def __init__(self, parent = None, mod_device = None, *a, **k):
		self._parent = parent
		self._mod_device = mod_device
		self._bank_dict = {}
		super(ModDeviceProxy, self).__init__(*a, **k)
		self.fill_parameters_from_device(mod_device)


	def fill_parameters_from_device(self, device):
		self._parameters = []
		if device:
			#self._parameters = [ModParameterProxy(parameter = parameter) for parameter in device.parameters]
			self._parameters = [parameter for parameter in device.parameters]


	def set_bank_dict_entry(self, bank_type, bank_num, *a):
		#debug('set bank dict_entry for proxy:', self._name, 'type:', bank_type, 'num:', bank_num, 'contents:', *a)
		if not bank_type in list(self._bank_dict.keys()):
			self._bank_dict[bank_type] = []
		self._bank_dict[bank_type].insert(bank_num, [item for item in a])
		#debug('new banks:', self._bank_dict)


	def update_parameters(self):
		self.notify_parameters()


	@property
	def bank_dict(self):
		return self._bank_dict


	@listenable_property
	def parameters(self):
		#debug('notifying parameters:', self._parameters if not self._alted else [self._parameters[0]] + self._parameters[8:])
		return self._parameters if (not self._alted or len(self._parameters) < 9) else [self._parameters[0]] + self._parameters[9:]


	def current_parameters(self):
		return self._parameters


	@parameters.setter
	def parameters(self, parameters):
		self._parameters = parameters
		#debug('parameters are now:', [parameter.name if hasattr(parameter, 'name') else None for parameter in self._parameters])
		self.notify_parameters()


	@listenable_property
	def name(self):
		return self._name


	def store_chosen_bank(self, callback=None):
		pass


	@property
	def canonical_parent(self):
		return self._mod_device.canonical_parent


	@property
	def can_have_chains(self):
		return self._mod_device.can_have_chains


class LegacyModDeviceProxy(ModDeviceProxy):

	class_name = 'LegacyModDeviceProxy'
	_name = 'LegacyModDeviceProxy'
	_device_parent = None
	_chain = 0
	_device_chain = 0
	_params = []
	_bank_index = 0
	_assigned_device = None
	_nodevice = NoDevice()
	_custom_parameter = []
	_control_prefix = 'Encoder'
	_type = None

	def __init__(self, *a, **k):
		super(LegacyModDeviceProxy, self).__init__(*a, **k)
		self._params = [ParamHolder(self, index, self._control_prefix, send_via_pipe = True) for index in range(16)]
		def plain_display_conversion(value):
			return str(value)
		#, display_value_conversion = plain_display_conversion
		self._display_parameters = [DisplayParameter(name = 'DisplayParameter{i}'.format(i=index)) for index in range(8)]
		for dp in self._display_parameters:
			dp.set_display_value_conversion(plain_display_conversion)


	def fill_parameters_from_device(self, *a):
		self.set_mod_device(self._mod_device)


	def _set_device_parent(self, mod_device_parent, single = None):
		# debug('_set_device_parent', mod_device_parent, single, mod_device_parent.name if hasattr(mod_device_parent, 'name') else 'No name attr')

		self._parent_device_changed.subject = None
		if isinstance(mod_device_parent, Live.Device.Device):
			if mod_device_parent.can_have_chains and single is None:
				self._device_parent = mod_device_parent
				if self._device_parent.canonical_parent != None:
					self._parent_device_changed.subject = self._device_parent.canonical_parent
				self._select_parent_chain(self._device_chain)
			else:
				self._device_parent = mod_device_parent
				self._assign_parameters(self._device_parent, True)
		elif 'NoDevice' in list(self._bank_dict.keys()):
			# debug('_set_device_parent is NoDevice')
			self._device_parent = self._nodevice
			self._device_chain = 0
			self._assign_parameters(None, True)
		else:
			# debug('_set_device_parent is None')
			self._device_parent = None
			self._device_chain = 0
			self._assign_parameters(None, True)


	def _select_parent_chain(self, chain, force = False):
		# debug('_select_parent_chain ', str(chain))
		self._device_chain = chain
		if self._device_parent != None:
			if isinstance(self._device_parent, Live.Device.Device):
				if self._device_parent.can_have_chains:
					if len(self._device_parent.chains) > chain:
						if len(self._device_parent.chains[chain].devices) > 0:
							self._assign_parameters(self._device_parent.chains[chain].devices[0], force)
					elif 'NoDevice' in list(self._bank_dict.keys()):
						self._assign_parameters(self._nodevice, True)
					else:
						self._assign_parameters(None)


	def _select_drum_pad(self, pad, force = False):
		# debug('_select_drum_pad', pad, force, 'parent:', self._device_parent)
		if self._device_parent != None:
			if isinstance(self._device_parent, Live.Device.Device):
				#debug('is device')
				if self._device_parent.can_have_drum_pads and self._device_parent.has_drum_pads:
					#debug('can and has drum_pads')
					pad = self._device_parent.drum_pads[pad]
					#debug('pad is: ', str(pad))
					if pad.chains and pad.chains[0] and pad.chains[0].devices and isinstance(pad.chains[0].devices[0], Live.Device.Device):
						self._assign_parameters(pad.chains[0].devices[0], force)
					elif 'NoDevice' in list(self._bank_dict.keys()):
						self._assign_parameters(self._nodevice, True)
					else:
						self._assign_parameters(None)


	@listens('devices')
	def _parent_device_changed(self):
		#debug('parent_device_changed')
		self._set_device_parent(None)
		self._parent.send('lcd', 'parent', 'check')


	@listens('devices')
	def _device_changed(self):
		#debug('device_changed')
		self._assign_parameters(None)
		self._parent.send('lcd', 'device', 'check')


	def _assign_parameters(self, device, force = False, *a):
		# debug('_assign_parameters:', device, device.class_name if device and hasattr(device, 'class_name') else 'no name')
		self._assigned_device = device
		new_parameters = [self._mod_device.parameters[0]]
		for param in self._params:
			param.parameter = None
		if device is None:
			class_name = 'NoDevice'
		elif (device and device.class_name in list(self._bank_dict.keys())):
			class_name = device.class_name
		else:
			class_name = 'Other'
		#debug('class name is:', class_name, 'keys:', self._bank_dict.keys());
		if (class_name in list(self._bank_dict.keys())):
			#debug('class name in keys...')
			bank_index = clamp(self._bank_index, 0, len(self._bank_dict[class_name]))
			#debug('bank index is:', bank_index)
			bank = [name for name in self._bank_dict[class_name][bank_index]]
			#debug('bank is:', bank)
			for parameter_name in bank:
				new_parameters.append(self.get_parameter_by_name(device, parameter_name))
		elif device is self._mod_device:
			new_parameters = [parameter for parameter in self._mod_device.parameters]
		for param, parameter in zip(self._params, new_parameters[1:]):
			param.parameter = parameter
		self.parameters = new_parameters
		self._parent.send('lcd', 'device_name', 'lcd_name', generate_strip_string(str(device.name)) if hasattr(device, 'name') else ' ')
		#debug('params are now:', [param.parameter.name if hasattr(param.parameter, 'name') else None for param in self._params])


	def get_parameter_by_name(self, device, name):
		#debug('get parameter: device-', device, 'name-', name)
		result = None
		if device:
			for i in device.parameters:
				if (i.original_name == name):
					result = i
					break
			if result == None:
				if name == 'Mod_Chain_Pan':
					if device.canonical_parent.mixer_device != None:
						if device.canonical_parent.mixer_device.panning != None:
							result = device.canonical_parent.mixer_device.panning
				elif name == 'Mod_Chain_Vol':
					if device.canonical_parent.mixer_device !=None:
						if device.canonical_parent.mixer_device.panning != None:
							result = device.canonical_parent.mixer_device.volume
				elif(match('Mod_Chain_Send_', name)):
					#debug('match Mod_Chain_Send_')
					send_index = int(name.replace('Mod_Chain_Send_', ''))
					if device.canonical_parent != None:
						if device.canonical_parent.mixer_device != None:
							if device.canonical_parent.mixer_device.sends != None:
								if len(device.canonical_parent.mixer_device.sends)>send_index:
									result = device.canonical_parent.mixer_device.sends[send_index]
		if result == None:
			#debug('checking for ModDevice...')
			if match('ModDevice_', name) and self._mod_device != None:
				name = name.replace('ModDevice_', '')
				#debug('modDevice with name:', name)
				for i in self._mod_device.parameters:
					if (i.name == name):
						result = i
						break
			elif match('CustomParameter_', name):
				index = int(name.replace('CustomParameter_', ''))
				if len(self._custom_parameter)>index:
					if isinstance(self._custom_parameter[index], Live.DeviceParameter.DeviceParameter):
						result = self._custom_parameter[index]
			elif match('ModDisplayParameter_', name):
				index = int(name.replace('ModDisplayParameter_', ''))
				if len(self._display_parameters)>index:
					result = self._display_parameters[index]
					#debug('passing ModDisplayParameter:', result)
		return result


	def rebuild_parameters(self):
		self._assign_parameters(device = self._assigned_device, force = True)


	def set_params_report_change(self, value):
		for param in self._params:
			param._report = bool(value)


	def set_params_control_prefix(self, prefix):
		self._control_prefix = prefix
		for param in self._params:
			param.set_control_prefix(prefix)


	def set_number_params(self, number, *a):
		#debug('set number params', number)
		for param in self._params:
			param.parameter = None
		self._params = [ParamHolder(parent=self, index=index, control_prefix=self._control_prefix, send_via_pipe = True) for index in range(number)]
		self._name_data_sources = [DisplayDataSource('') for index in range(number)]
		self._value_data_sources = [DisplayDataSource('') for index in range(number)]
		#self._assign_parameters(self._assigned_device)


	def set_mod_device_type(self, mod_device_type, *a):
		#debug('set type ' + str(mod_device_type))
		self._type = mod_device_type


	def set_mod_device(self, mod_device, *a):
		#debug('set_mod_device:', mod_device)
		self._assign_parameters(mod_device)


	def set_mod_device_parent(self, mod_device_parent, single=None, *a):
		#debug('set_mod_device_parent:', mod_device_parent, single)
		self._set_device_parent(mod_device_parent, single)


	def set_mod_device_chain(self, chain, *a):
		#debug('set_mod_device_chain:', chain)
		self._select_parent_chain(chain, True)


	def set_mod_drum_pad(self, pad, *a):
		#debug('set_mod_drum_pad:', pad)
		self._select_drum_pad(pad, True)


	def set_mod_device_bank(self, bank_index, *a):
		#debug('set_mod_device_bank:', bank_index)
		if bank_index != self._bank_index:
			self._bank_index = bank_index
			self.rebuild_parameters()


	def set_mod_display_parameter_name(self, num = 0, val = 'default', *a):
		#debug('set_mod_display_parameter_name:', num, val)
		if num < self._display_parameters:
			self._display_parameters[num].set_name(val)


	def set_mod_display_parameter_value(self, num = 0, val = 0, *a):
		#debug('set_mod_display_parameter_name:', num, val)
		if num < self._display_parameters:
			self._display_parameters[num].set_value(val)


	def set_mod_parameter_value(self, num, val, *a):
		num < len(self._params) and self._params[num]._change_value(val)


	def _params_value_change(self, sender, control_name, feedback = True):
		# debug('params change', sender, control_name)
		pn = ' '
		pv = ' '
		val = 0
		if(sender != None):
			pn = str(generate_strip_string(str(sender.name)))
			if sender.is_enabled:
				try:
					value = str(sender)
				except:
					value = ' '
				pv = str(generate_strip_string(value))
			else:
				pv = '-bound-'
			val = ((sender.value - sender.min) / (sender.max - sender.min))  * 127
		self._parent.send('lcd', control_name, 'lcd_name', pn)
		self._parent.send('lcd', control_name, 'lcd_value', pv)
		if feedback == True:
			self._parent.send('lcd', control_name, 'encoder_value', val)


	def set_number_custom(self, number, *a):
		self._custom_parameter = [None for index in range(number)]


	def set_custom_parameter(self, number, parameter, rebuild = True, *a):
		if number < len(self._custom_parameter):
			#debug('custom=', parameter)
			if isinstance(parameter, Live.DeviceParameter.DeviceParameter) or parameter is None:
				#debug('custom is device:', parameter)
				self._custom_parameter[number] = parameter
				rebuild and self.rebuild_parameters()


	def set_custom_parameter_value(self, num, value, *a):
		if num < len(self._custom_parameter):
			parameter = self._custom_parameter[num]
			if parameter != None:
				newval = float(float(float(value)/127) * float(parameter.max - parameter.min)) + parameter.min
				parameter.value = newval


	def set_all_params_to_defaults(self):
		#debug('set all params to default')
		for param in self._parameters:
			if param:
				name = param.name
				#debug('param name:', name)
				if name:
					for item in name.split(' '):
						if len(str(item)) and str(item)[0]=='@':
							vals = item[1:].split(':')
							if vals[0] in ['rst', 'def', 'defaults']:
								self.set_param_to_default(param, vals[1])
							else:
								#debug('no def value...')
								pass


	def set_param_to_default(self, param, val):
		rst_val = float(val)/100
		newval = float(rst_val * (param.max - param.min)) + param.min
		param.value = newval


	def toggle_param(self, param):
		if param.value == param.min:
			param.value = param.max
		else:
			param.value = param.min


class ModGridDeviceProxy(ModDeviceProxy):

	class_name = 'ModGridDeviceProxy'
	_name = 'ModGridDeviceProxy'
	_device_parent = None
	_chain = 0
	_device_chain = 0
	_params = []
	_bank_index = 0
	_assigned_device = None
	_nodevice = NoDevice()
	_custom_parameter = []
	_control_prefix = 'parameter'
	_type = None
	_explicit_parameters = []
	_use_explicit_parameters = False

	def __init__(self, *a, **k):
		super(ModGridDeviceProxy, self).__init__(*a, **k)
		self._params = [ParamHolder(self, index, self._control_prefix, send_via_pipe = False) for index in range(16)]
		# def plain_display_conversion(value):
		# 	return str(value)
		#, display_value_conversion = plain_display_conversion
		# self._display_parameters = [DisplayParameter(name = 'DisplayParameter{i}'.format(i=index)) for index in range(8)]
		# for dp in self._display_parameters:
		# 	dp.set_display_value_conversion(plain_display_conversion)



	def set_use_explicit_parameters(self, value = True):
		debug('set_use_explicit_parameters', value>0)
		self._use_explicit_parameters = value > 0


	def set_explicit_parameter(self, index, param, *a):
		# debug('set_explicit_parameter', index, param)
		if index < len(self._params):
			param = param if liveobj_valid(param) else None
			self._explicit_parameters[index] = param
			self._assign_parameters()


	def set_explicit_parameters(self, *parameters):
		debug('set_explicit_parameters', len(parameters))
		new_parameters = []
		for index in range(len(self._explicit_parameters)):
			self._explicit_parameters[index] = parameters[index] if (len(parameters) > index and liveobj_valid(parameters[index])) else None
		self._assign_parameters()


	def _assign_explicit_parameters(self):
		self._assigned_device = self._mod_device
		used_parameters = [self._mod_device.parameters[0]] + self._explicit_parameters
		debug('_assign_explicit_parameters:', used_parameters[0], used_parameters[1], self._use_explicit_parameters)
		for param, parameter in zip(self._params, used_parameters):
			param.parameter = parameter
		self.parameters = used_parameters
		# self._parent.send('lcd', 'device_name', 'lcd_name', generate_strip_string(str(device.name)) if hasattr(device, 'name') else ' ')
		self.notify_parameters() 


	def fill_parameters_from_device(self, *a):
		debug('fill_parameters_from_device')
		self.set_mod_device(self._mod_device)


	def _set_device_parent(self, mod_device_parent, single = None):
		# debug('_set_device_parent', mod_device_parent, single, mod_device_parent.name if hasattr(mod_device_parent, 'name') else 'No name attr')

		self._parent_device_changed.subject = None
		if isinstance(mod_device_parent, Live.Device.Device):
			if mod_device_parent.can_have_chains and single is None:
				self._device_parent = mod_device_parent
				if self._device_parent.canonical_parent != None:
					self._parent_device_changed.subject = self._device_parent.canonical_parent
				self._select_parent_chain(self._device_chain)
			else:
				self._device_parent = mod_device_parent
				self._assign_parameters(self._device_parent, True)
		elif 'NoDevice' in list(self._bank_dict.keys()):
			# debug('_set_device_parent is NoDevice')
			self._device_parent = self._nodevice
			self._device_chain = 0
			self._assign_parameters(None, True)
		else:
			# debug('_set_device_parent is None')
			self._device_parent = None
			self._device_chain = 0
			self._assign_parameters(None, True)


	def _select_parent_chain(self, chain, force = False):
		# debug('_select_parent_chain ', str(chain))
		self._device_chain = chain
		if self._device_parent != None:
			if isinstance(self._device_parent, Live.Device.Device):
				if self._device_parent.can_have_chains:
					if len(self._device_parent.chains) > chain:
						if len(self._device_parent.chains[chain].devices) > 0:
							self._assign_parameters(self._device_parent.chains[chain].devices[0], force)
					elif 'NoDevice' in list(self._bank_dict.keys()):
						self._assign_parameters(self._nodevice, True)
					else:
						self._assign_parameters(None)


	def _select_drum_pad(self, pad, force = False):
		# debug('_select_drum_pad', pad, force, 'parent:', self._device_parent)
		if self._device_parent != None:
			if isinstance(self._device_parent, Live.Device.Device):
				#debug('is device')
				if self._device_parent.can_have_drum_pads and self._device_parent.has_drum_pads:
					#debug('can and has drum_pads')
					pad = self._device_parent.drum_pads[pad]
					#debug('pad is: ', str(pad))
					if pad.chains and pad.chains[0] and pad.chains[0].devices and isinstance(pad.chains[0].devices[0], Live.Device.Device):
						self._assign_parameters(pad.chains[0].devices[0], force)
					elif 'NoDevice' in list(self._bank_dict.keys()):
						self._assign_parameters(self._nodevice, True)
					else:
						self._assign_parameters(None)


	@listens('devices')
	def _parent_device_changed(self):
		#debug('parent_device_changed')
		self._set_device_parent(None)
		# self._parent.send('lcd', 'parent', 'check')


	@listens('devices')
	def _device_changed(self):
		#debug('device_changed')
		self._assign_parameters(None)
		# self._parent.send('lcd', 'device', 'check')


	def _assign_parameters(self, device = None, force = False, *a):
		# debug('_assign_parameters:', device, device.class_name if device and hasattr(device, 'class_name') else 'no name')
		if self._use_explicit_parameters:
			debug('assigning explicit...')
			self._assign_explicit_parameters()
		else:
			self._assigned_device = device
			new_parameters = [self._mod_device.parameters[0]]
			for param in self._params:
				param.parameter = None
			if device is None:
				class_name = 'NoDevice'
			elif (device and device.class_name in list(self._bank_dict.keys())):
				class_name = device.class_name
			else:
				class_name = 'Other'
			#debug('class name is:', class_name, 'keys:', self._bank_dict.keys());
			if (class_name in list(self._bank_dict.keys())):
				#debug('class name in keys...')
				bank_index = clamp(self._bank_index, 0, len(self._bank_dict[class_name]))
				#debug('bank index is:', bank_index)
				bank = [name for name in self._bank_dict[class_name][bank_index]]
				#debug('bank is:', bank)
				for parameter_name in bank:
					new_parameters.append(self.get_parameter_by_name(device, parameter_name))
			elif device is self._mod_device:
				new_parameters = [parameter for parameter in self._mod_device.parameters]
			for param, parameter in zip(self._params, new_parameters[1:]):
				param.parameter = parameter
			self.parameters = new_parameters
			self._parent.send('lcd', 'device_name', 'lcd_name', generate_strip_string(str(device.name)) if hasattr(device, 'name') else ' ')
			#debug('params are now:', [param.parameter.name if hasattr(param.parameter, 'name') else None for param in self._params])
			self.notify_parameters()   


	def get_parameter_by_name(self, device, name):
		#debug('get parameter: device-', device, 'name-', name)
		result = None
		if device:
			for i in device.parameters:
				if (i.original_name == name):
					result = i
					break
			if result == None:
				if name == 'Mod_Chain_Pan':
					if device.canonical_parent.mixer_device != None:
						if device.canonical_parent.mixer_device.panning != None:
							result = device.canonical_parent.mixer_device.panning
				elif name == 'Mod_Chain_Vol':
					if device.canonical_parent.mixer_device !=None:
						if device.canonical_parent.mixer_device.panning != None:
							result = device.canonical_parent.mixer_device.volume
				elif(match('Mod_Chain_Send_', name)):
					#debug('match Mod_Chain_Send_')
					send_index = int(name.replace('Mod_Chain_Send_', ''))
					if device.canonical_parent != None:
						if device.canonical_parent.mixer_device != None:
							if device.canonical_parent.mixer_device.sends != None:
								if len(device.canonical_parent.mixer_device.sends)>send_index:
									result = device.canonical_parent.mixer_device.sends[send_index]
		if result == None:
			#debug('checking for ModDevice...')
			if match('ModDevice_', name) and self._mod_device != None:
				name = name.replace('ModDevice_', '')
				#debug('modDevice with name:', name)
				for i in self._mod_device.parameters:
					if (i.name == name):
						result = i
						break
			elif match('CustomParameter_', name):
				index = int(name.replace('CustomParameter_', ''))
				if len(self._custom_parameter)>index:
					if isinstance(self._custom_parameter[index], Live.DeviceParameter.DeviceParameter):
						result = self._custom_parameter[index]
			elif match('ModDisplayParameter_', name):
				index = int(name.replace('ModDisplayParameter_', ''))
				if len(self._display_parameters)>index:
					result = self._display_parameters[index]
					#debug('passing ModDisplayParameter:', result)
		return result


	def rebuild_parameters(self):
		self._assign_parameters(device = self._assigned_device, force = True)


	def set_params_report_change(self, value):
		for param in self._params:
			param._report = bool(value)


	def set_params_control_prefix(self, prefix):
		self._control_prefix = prefix
		for param in self._params:
			param.set_control_prefix(prefix)


	def set_number_params(self, number, *a):
		debug('set number params', number)
		try:
			for param in self._params:
				param.parameter = None
			self._params = [ParamHolder(parent=self, index=index, control_prefix=self._control_prefix, send_via_pipe = False) for index in range(number)]
			self._explicit_parameters = [None for index in range(number)]
		except Exception as e:
			debug('EXCEPTION:', e)
		#self._assign_parameters(self._assigned_device)


	def set_mod_device_type(self, mod_device_type, *a):
		#debug('set type ' + str(mod_device_type))
		self._type = mod_device_type


	def set_mod_device(self, mod_device, *a):
		#debug('set_mod_device:', mod_device)
		self._assign_parameters(mod_device)


	def set_mod_device_parent(self, mod_device_parent, single=None, *a):
		#debug('set_mod_device_parent:', mod_device_parent, single)
		self._set_device_parent(mod_device_parent, single)


	def set_mod_device_chain(self, chain, *a):
		#debug('set_mod_device_chain:', chain)
		self._select_parent_chain(chain, True)


	def set_mod_drum_pad(self, pad, *a):
		#debug('set_mod_drum_pad:', pad)
		self._select_drum_pad(pad, True)


	def set_mod_device_bank(self, bank_index, *a):
		#debug('set_mod_device_bank:', bank_index)
		if bank_index != self._bank_index:
			self._bank_index = bank_index
			self.rebuild_parameters()


	def set_mod_display_parameter_name(self, num = 0, val = 'default', *a):
		#debug('set_mod_display_parameter_name:', num, val)
		if num < self._display_parameters:
			self._display_parameters[num].set_name(val)


	def set_mod_display_parameter_value(self, num = 0, val = 0, *a):
		#debug('set_mod_display_parameter_name:', num, val)
		if num < self._display_parameters:
			self._display_parameters[num].set_value(val)


	def set_mod_parameter_value(self, num, val, *a):
		num < len(self._params) and self._params[num]._change_value(val)


	def _params_value_change(self, sender, control_name, feedback = True):
		# debug('params change', sender, control_name)
		pn = ' '
		pv = ' '
		val = 0
		if(sender != None):
			pn = str(generate_strip_string(str(sender.name)))
			if sender.is_enabled:
				try:
					value = str(sender)
				except:
					value = ' '
				pv = str(generate_strip_string(value))
			else:
				pv = '-bound-'
			val = ((sender.value - sender.min) / (sender.max - sender.min))  * 127
		self._parent.send('lcd', control_name, 'lcd_name', pn)
		self._parent.send('lcd', control_name, 'lcd_value', pv)
		if feedback == True:
			self._parent.send('lcd', control_name, 'encoder_value', val)


	def set_number_custom(self, number, *a):
		self._custom_parameter = [None for index in range(number)]


	def set_custom_parameter(self, number, parameter, rebuild = True, *a):
		if number < len(self._custom_parameter):
			#debug('custom=', parameter)
			if isinstance(parameter, Live.DeviceParameter.DeviceParameter) or parameter is None:
				#debug('custom is device:', parameter)
				self._custom_parameter[number] = parameter
				rebuild and self.rebuild_parameters()


	def set_custom_parameter_value(self, num, value, *a):
		if num < len(self._custom_parameter):
			parameter = self._custom_parameter[num]
			if parameter != None:
				newval = float(float(float(value)/127) * float(parameter.max - parameter.min)) + parameter.min
				parameter.value = newval


	def set_all_params_to_defaults(self):
		#debug('set all params to default')
		for param in self._parameters:
			if param:
				name = param.name
				#debug('param name:', name)
				if name:
					for item in name.split(' '):
						if len(str(item)) and str(item)[0]=='@':
							vals = item[1:].split(':')
							if vals[0] in ['rst', 'def', 'defaults']:
								self.set_param_to_default(param, vals[1])
							else:
								#debug('no def value...')
								pass


	def set_param_to_default(self, param, val):
		rst_val = float(val)/100
		newval = float(rst_val * (param.max - param.min)) + param.min
		param.value = newval


	def toggle_param(self, param):
		if param.value == param.min:
			param.value = param.max
		else:
			param.value = param.min


class ModGridDirectDeviceProxy(ModDeviceProxy):

	class_name = 'ModGridDirectDeviceProxy'
	_name = 'ModGridDirectDeviceProxy'
	_device_parent = None
	_chain = 0
	_device_chain = 0
	_params = []
	_bank_index = 0
	_assigned_device = None
	_nodevice = NoDevice()
	_custom_parameter = []
	_control_prefix = 'parameter'
	_type = None
	_explicit_parameters = []

	def __init__(self, *a, **k):
		super(ModGridDeviceProxy, self).__init__(*a, **k)
		self._params = [ParamHolder(self, index, self._control_prefix, send_via_pipe = False) for index in range(16)]
		# def plain_display_conversion(value):
		# 	return str(value)
		#, display_value_conversion = plain_display_conversion
		# self._display_parameters = [DisplayParameter(name = 'DisplayParameter{i}'.format(i=index)) for index in range(8)]
		# for dp in self._display_parameters:
		# 	dp.set_display_value_conversion(plain_display_conversion)



	def fill_parameters_from_device(self, *a):
		debug('fill_parameters_from_device')
		self.set_mod_device(self._mod_device)


	def set_explicit_parameter(self, index, param, *a):
		debug('_set_explicit_parameter', index, param)
		# param = param if liveobj_valid(param) else None
		# if index > 0:
		# 	self._explicit_parameters[index] = param


	def _set_device_parent(self, mod_device_parent, single = None):
		# debug('_set_device_parent', mod_device_parent, single, mod_device_parent.name if hasattr(mod_device_parent, 'name') else 'No name attr')

		self._parent_device_changed.subject = None
		if isinstance(mod_device_parent, Live.Device.Device):
			if mod_device_parent.can_have_chains and single is None:
				self._device_parent = mod_device_parent
				if self._device_parent.canonical_parent != None:
					self._parent_device_changed.subject = self._device_parent.canonical_parent
				self._select_parent_chain(self._device_chain)
			else:
				self._device_parent = mod_device_parent
				self._assign_parameters(self._device_parent, True)
		elif 'NoDevice' in list(self._bank_dict.keys()):
			# debug('_set_device_parent is NoDevice')
			self._device_parent = self._nodevice
			self._device_chain = 0
			self._assign_parameters(None, True)
		else:
			# debug('_set_device_parent is None')
			self._device_parent = None
			self._device_chain = 0
			self._assign_parameters(None, True)


	def _select_parent_chain(self, chain, force = False):
		# debug('_select_parent_chain ', str(chain))
		self._device_chain = chain
		if self._device_parent != None:
			if isinstance(self._device_parent, Live.Device.Device):
				if self._device_parent.can_have_chains:
					if len(self._device_parent.chains) > chain:
						if len(self._device_parent.chains[chain].devices) > 0:
							self._assign_parameters(self._device_parent.chains[chain].devices[0], force)
					elif 'NoDevice' in list(self._bank_dict.keys()):
						self._assign_parameters(self._nodevice, True)
					else:
						self._assign_parameters(None)


	def _select_drum_pad(self, pad, force = False):
		# debug('_select_drum_pad', pad, force, 'parent:', self._device_parent)
		if self._device_parent != None:
			if isinstance(self._device_parent, Live.Device.Device):
				#debug('is device')
				if self._device_parent.can_have_drum_pads and self._device_parent.has_drum_pads:
					#debug('can and has drum_pads')
					pad = self._device_parent.drum_pads[pad]
					#debug('pad is: ', str(pad))
					if pad.chains and pad.chains[0] and pad.chains[0].devices and isinstance(pad.chains[0].devices[0], Live.Device.Device):
						self._assign_parameters(pad.chains[0].devices[0], force)
					elif 'NoDevice' in list(self._bank_dict.keys()):
						self._assign_parameters(self._nodevice, True)
					else:
						self._assign_parameters(None)


	@listens('devices')
	def _parent_device_changed(self):
		#debug('parent_device_changed')
		self._set_device_parent(None)
		# self._parent.send('lcd', 'parent', 'check')


	@listens('devices')
	def _device_changed(self):
		#debug('device_changed')
		self._assign_parameters(None)
		# self._parent.send('lcd', 'device', 'check')


	def _assign_parameters(self, device, force = False, *a):
		# debug('_assign_parameters:', device, device.class_name if device and hasattr(device, 'class_name') else 'no name')
		self._assigned_device = device
		new_parameters = [self._mod_device.parameters[0]]
		for param in self._params:
			param.parameter = None
		if device is None:
			class_name = 'NoDevice'
		elif (device and device.class_name in list(self._bank_dict.keys())):
			class_name = device.class_name
		else:
			class_name = 'Other'
		#debug('class name is:', class_name, 'keys:', self._bank_dict.keys());
		if (class_name in list(self._bank_dict.keys())):
			#debug('class name in keys...')
			bank_index = clamp(self._bank_index, 0, len(self._bank_dict[class_name]))
			#debug('bank index is:', bank_index)
			bank = [name for name in self._bank_dict[class_name][bank_index]]
			#debug('bank is:', bank)
			for parameter_name in bank:
				new_parameters.append(self.get_parameter_by_name(device, parameter_name))
		elif device is self._mod_device:
			new_parameters = [parameter for parameter in self._mod_device.parameters]
		for param, parameter in zip(self._params, new_parameters[1:]):
			param.parameter = parameter
		self.parameters = new_parameters
		self._parent.send('lcd', 'device_name', 'lcd_name', generate_strip_string(str(device.name)) if hasattr(device, 'name') else ' ')
		#debug('params are now:', [param.parameter.name if hasattr(param.parameter, 'name') else None for param in self._params])
		self.notify_parameters()   


	def get_parameter_by_name(self, device, name):
		#debug('get parameter: device-', device, 'name-', name)
		result = None
		if device:
			for i in device.parameters:
				if (i.original_name == name):
					result = i
					break
			if result == None:
				if name == 'Mod_Chain_Pan':
					if device.canonical_parent.mixer_device != None:
						if device.canonical_parent.mixer_device.panning != None:
							result = device.canonical_parent.mixer_device.panning
				elif name == 'Mod_Chain_Vol':
					if device.canonical_parent.mixer_device !=None:
						if device.canonical_parent.mixer_device.panning != None:
							result = device.canonical_parent.mixer_device.volume
				elif(match('Mod_Chain_Send_', name)):
					#debug('match Mod_Chain_Send_')
					send_index = int(name.replace('Mod_Chain_Send_', ''))
					if device.canonical_parent != None:
						if device.canonical_parent.mixer_device != None:
							if device.canonical_parent.mixer_device.sends != None:
								if len(device.canonical_parent.mixer_device.sends)>send_index:
									result = device.canonical_parent.mixer_device.sends[send_index]
		if result == None:
			#debug('checking for ModDevice...')
			if match('ModDevice_', name) and self._mod_device != None:
				name = name.replace('ModDevice_', '')
				#debug('modDevice with name:', name)
				for i in self._mod_device.parameters:
					if (i.name == name):
						result = i
						break
			elif match('CustomParameter_', name):
				index = int(name.replace('CustomParameter_', ''))
				if len(self._custom_parameter)>index:
					if isinstance(self._custom_parameter[index], Live.DeviceParameter.DeviceParameter):
						result = self._custom_parameter[index]
			elif match('ModDisplayParameter_', name):
				index = int(name.replace('ModDisplayParameter_', ''))
				if len(self._display_parameters)>index:
					result = self._display_parameters[index]
					#debug('passing ModDisplayParameter:', result)
		return result


	def rebuild_parameters(self):
		self._assign_parameters(device = self._assigned_device, force = True)


	def set_params_report_change(self, value):
		for param in self._params:
			param._report = bool(value)


	def set_params_control_prefix(self, prefix):
		self._control_prefix = prefix
		for param in self._params:
			param.set_control_prefix(prefix)


	def set_number_params(self, number, *a):
		debug('set number params', number)
		try:
			for param in self._params:
				param.parameter = None
			self._params = [ParamHolder(parent=self, index=index, control_prefix=self._control_prefix, send_via_pipe = False) for index in range(number)]
		except Exception as e:
			debug('EXCEPTION:', e)
		#self._assign_parameters(self._assigned_device)


	def set_mod_device_type(self, mod_device_type, *a):
		#debug('set type ' + str(mod_device_type))
		self._type = mod_device_type


	def set_mod_device(self, mod_device, *a):
		#debug('set_mod_device:', mod_device)
		self._assign_parameters(mod_device)


	def set_mod_device_parent(self, mod_device_parent, single=None, *a):
		#debug('set_mod_device_parent:', mod_device_parent, single)
		self._set_device_parent(mod_device_parent, single)


	def set_mod_device_chain(self, chain, *a):
		#debug('set_mod_device_chain:', chain)
		self._select_parent_chain(chain, True)


	def set_mod_drum_pad(self, pad, *a):
		#debug('set_mod_drum_pad:', pad)
		self._select_drum_pad(pad, True)


	def set_mod_device_bank(self, bank_index, *a):
		#debug('set_mod_device_bank:', bank_index)
		if bank_index != self._bank_index:
			self._bank_index = bank_index
			self.rebuild_parameters()


	def set_mod_display_parameter_name(self, num = 0, val = 'default', *a):
		#debug('set_mod_display_parameter_name:', num, val)
		if num < self._display_parameters:
			self._display_parameters[num].set_name(val)


	def set_mod_display_parameter_value(self, num = 0, val = 0, *a):
		#debug('set_mod_display_parameter_name:', num, val)
		if num < self._display_parameters:
			self._display_parameters[num].set_value(val)


	def set_mod_parameter_value(self, num, val, *a):
		num < len(self._params) and self._params[num]._change_value(val)


	def _params_value_change(self, sender, control_name, feedback = True):
		# debug('params change', sender, control_name)
		pn = ' '
		pv = ' '
		val = 0
		if(sender != None):
			pn = str(generate_strip_string(str(sender.name)))
			if sender.is_enabled:
				try:
					value = str(sender)
				except:
					value = ' '
				pv = str(generate_strip_string(value))
			else:
				pv = '-bound-'
			val = ((sender.value - sender.min) / (sender.max - sender.min))  * 127
		self._parent.send('lcd', control_name, 'lcd_name', pn)
		self._parent.send('lcd', control_name, 'lcd_value', pv)
		if feedback == True:
			self._parent.send('lcd', control_name, 'encoder_value', val)


	def set_number_custom(self, number, *a):
		self._custom_parameter = [None for index in range(number)]


	def set_custom_parameter(self, number, parameter, rebuild = True, *a):
		if number < len(self._custom_parameter):
			#debug('custom=', parameter)
			if isinstance(parameter, Live.DeviceParameter.DeviceParameter) or parameter is None:
				#debug('custom is device:', parameter)
				self._custom_parameter[number] = parameter
				rebuild and self.rebuild_parameters()


	def set_custom_parameter_value(self, num, value, *a):
		if num < len(self._custom_parameter):
			parameter = self._custom_parameter[num]
			if parameter != None:
				newval = float(float(float(value)/127) * float(parameter.max - parameter.min)) + parameter.min
				parameter.value = newval


	def set_all_params_to_defaults(self):
		#debug('set all params to default')
		for param in self._parameters:
			if param:
				name = param.name
				#debug('param name:', name)
				if name:
					for item in name.split(' '):
						if len(str(item)) and str(item)[0]=='@':
							vals = item[1:].split(':')
							if vals[0] in ['rst', 'def', 'defaults']:
								self.set_param_to_default(param, vals[1])
							else:
								#debug('no def value...')
								pass


	def set_param_to_default(self, param, val):
		rst_val = float(val)/100
		newval = float(rst_val * (param.max - param.min)) + param.min
		param.value = newval


	def toggle_param(self, param):
		if param.value == param.min:
			param.value = param.max
		else:
			param.value = param.min
