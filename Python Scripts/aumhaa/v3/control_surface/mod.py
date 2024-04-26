# by amounra 0216 : http://www.aumhaa.com
# written against Live 10.0.5 on 120418


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
from aumhaa.v3.control_surface.mod_devices import *
from aumhaa.v3.control_surface.mod_device import *


INITIAL_SCROLLING_DELAY = 5
INTERVAL_SCROLLING_DELAY = 1

CS_LIST_KEY = 'control_surfaces'

LOCAL_DEBUG = False
debug = initialize_debug(local_debug = LOCAL_DEBUG)


def hascontrol(handler, control):
	return control in list(handler._controls.keys())


def enumerate_track_device(track):
	devices = []
	if hasattr(track, 'devices'):
		for device in track.devices:
			devices.append(device)
			if device.can_have_chains:
				for chain in device.chains:
					for chain_device in enumerate_track_device(chain):
						devices.append(chain_device)
	return devices


def get_monomodular(host):
		if isinstance(__builtins__, dict):
			if not 'monomodular' in list(__builtins__.keys()) or not isinstance(__builtins__['monomodular'], ModRouter):
				__builtins__['monomodular'] = ModRouter()
		else:
			if not hasattr(__builtins__, 'monomodular') or not isinstance(__builtins__['monomodular'], ModRouter):
				setattr(__builtins__, 'monomodular', ModRouter())
		monomodular = __builtins__['monomodular']
		if not monomodular.has_host():
			monomodular.set_host(host)
		return monomodular


def get_control_surfaces():
	if isinstance(__builtins__, dict):
		if CS_LIST_KEY not in list(__builtins__.keys()):
			__builtins__[CS_LIST_KEY] = []
		return __builtins__[CS_LIST_KEY]
	else:
		if not hasattr(__builtins__, CS_LIST_KEY):
			setattr(__builtins__, CS_LIST_KEY, [])
		return getattr(__builtins__, CS_LIST_KEY)


def return_empty():
	return []


def appointed_device():
	return Live.song().appointed_device


def drumrack_devices(song):
	found_drumrack_devices = []
	for track in song.tracks:
		if liveobj_valid(track) and track.has_midi_input:
			for device in track.devices:
				#if liveobj_valid(device):
					#debug(device.type, device)
				if liveobj_valid(device) and isinstance(device, Live.RackDevice.RackDevice):  # and device.has_drum_pads:
					found_drumrack_devices.append(device)
	#debug('found_drumrack_devices:', found_drumrack_devices)
	return found_drumrack_devices


def device_to_appoint(device):
	appointed_device = device
	if liveobj_valid(device) and device.can_have_drum_pads and not device.has_macro_mappings and len(device.chains) > 0 and liveobj_valid(device.view.selected_chain) and len(device.view.selected_chain.devices) > 0:
		appointed_device = device_to_appoint(device.view.selected_chain.devices[0])
	return appointed_device


def select_and_appoint_device(song, device_to_select, ignore_unmapped_macros = False):
	appointed_device = device_to_select
	if ignore_unmapped_macros:
		appointed_device = device_to_appoint(device_to_select)
	song.view.select_device(device_to_select, False)
	song.appointed_device = appointed_device


def get_modrouter():
	modrouter = None
	if hasattr(__builtins__, 'monomodular') or 'monomodular' in list(__builtins__.keys()):
		modrouter = __builtins__['monomodular']
	return modrouter


def livedevice(device):
	return device._mod_device if hasattr(device, '_mod_device') else device


class ElementTranslation(object):


	def __init__(self, name, script):
		self._script = script
		self._name = name
		self._targets = {}
		self._last_received = None


	def set_enabled(self, name, enabled):
		try:
			self._targets[name]['Enabled'] = enabled > 0
			if enabled and not self._last_received is None:
				target = self._targets[name]
				value_list = [i for i in target['Arguments']] + [j for j in self._last_received]
				try:
					getattr(target['Target'], method)(*value_list)
				except:
					pass
		except:
			pass


	def is_enabled(self, name):
		try:
			return self._targets[name]['Enabled']
		except:
			return False


	def target(self, name):
		try:
			return self._targets[name]['Target']
		except:
			return None


	def add_target(self, name, target, *args, **k):
		self._targets[name] = {'Target':target, 'Arguments':args, 'Enabled':True}


	def receive(self, method, *values):
		#debug(str(self._name) + ' receive: ' + str(method) + ' ' + str(values))
		for entry in list(self._targets.keys()):
			target = self._targets[entry]
			if target['Enabled'] == True:
				value_list = [i for i in target['Arguments']] + [j for j in values]
				try:
					getattr(target['Target'], method)(*value_list)
				except:
					pass
		self._last_received = values


class StoredElement(object):

	_name = ""

	def __init__(self, active_handlers = return_empty, *a, **attributes):
		self._active_handlers = active_handlers
		self._value = 0
		for name, attribute in attributes.items():
			setattr(self, name, attribute)


	def value(self, value):
		self._value = value
		self.update_element()


	def update_element(self):
		for handler in self._active_handlers():
			handler.receive_address(self._name, value=self._value)


	def restore(self):
		self.update_element()


class Grid(object):


	def __init__(self, name, width, height, active_handlers = return_empty, *a, **k):
		self._active_handlers = active_handlers
		self._name = name
		self._width = width
		self._height = height
		self._cell = [[StoredElement(active_handlers, _name = self._name + '_' + str(x) + '_' + str(y), _x = x, _y = y , *a, **k) for y in range(height)] for x in range(width)]


	def restore(self):
		for column in self._cell:
			for element in column:
				self.update_element(element)


	def update_element(self, element):
		for handler in self._active_handlers():
			handler.receive_address(self._name, element._x, element._y, value = element._value)


	def value(self, x, y, value, *a):
		element = self._cell[x][y]
		element._value = value
		self.update_element(element)


	def row(self, row, value, *a):
		for column in range(len(self._cell)):
			self.value(column, row, value)


	def column(self, column, value, *a):
		for row in range(len(self._cell[column])):
			self.value(column, row, value)


	def clear(self, value, *a):
		self.all(0)


	def all(self, value, *a):
		for column in range(len(self._cell)):
			for row in range(len(self._cell[column])):
				self.value(column, row, value)


	def batch_row(self, row, *values):
		width = len(self._cell)
		for index in range(len(values)):
			self.value(index%width, row + int(index/width), values[index])


	def batch_column(self, column, *values):
		for row in range(len(self._cell[column])):
			if values[row]:
				self.value(column, row, values[row])


	def batch_all(self, *values):
		for column in range(len(self._cell)):
			for row in range(len(self._cell[column])):
				if values[column + (row*self._width)]:
					self.value(column, row, values[column + (row*len(self._cell))])


	def mask(self, x, y, value, *a):
		element = self._cell[x][y]
		if value > -1:
			for handler in self._active_handlers():
				handler.receive_address(self._name, element._x, element._y, value = value)
		else:
			self.update_element(element)


	def mask_row(self, row, value, *a):
		for column in range(len(self._cell[row])):
			self.mask(column, row, value)


	def mask_column(self, column, value, *a):
		for row in range(len(self._cell)):
			self.mask(column, row, value)


	def mask_all(self, value, *a):
		for column in range(len(self._cell)):
			for row in range(len(self._cell[column])):
				self.mask(column, row, value)


	def batch_mask_row(self, row, *values):
		width = len(self._cell)
		for index in range(len(values)):
			self.mask(index%width, row + int(index/width), values[index])


	def batch_mask_column(self, column, *values):
		for row in range(len(self._cell[column])):
			if values[row]:
				self.mask(column, row, values[row])


	def batch_mask_all(self, *values):
		for column in range(len(self._cell)):
			for row in range(len(self._cell[column])):
				if values[column + (row*len(self._cell))]:
					self.mask(column, row, values[column + (row*self._width)])


	def batch_row_fold(self, row, end, *values):
		width = min(len(self._cell), end)
		for index in range(len(values)):
			self.value(index%width, row + int(index/width), values[index])


	def batch_column_fold(self, column, end, *values):
		height = min(len(self._cell[0] if hasattr(self._cell, len) else 0, end))
		for index in range(len(values)):
			self.value(column + int(index/height), index%height, values[index])


	def map(self, x_offset, y_offset, *values):
		if len(values) is 8:
			if x_offset % 8 is 0 and y_offset % 8 is 0:
				for row in range(8):
					for column in range(8):
						self.value(x_offset+column, y_offset+row, (values[row]>>column)&1)


	def monome_row(self, x_offset, y, value = 0, *a):
		if x_offset % 8 is 0:
			for column in range(8):
				self.value(x_offset+column, y, (value>>column)&1)


	def monome_col(self, y_offset, x, value = 0, *a):
		if y_offset % 8 is 0:
			for row in range(8):
				self.value(x, y_offset+row, (value>>row)&1)


	def mask_next_empty_x(self, x, y, value, *a):
		#debug('mask_next_empty_x', x, y, value)
		for handler in self._active_handlers():
			x_off = handler.x_offset
			y_off = handler.y_offset
			next_empty_x = None
			for column in range(x_off, x_off+8):
				#debug('column:', column, 'sum:', sum([self._cell[column][y_off+row]._value for row in range(8)]))
				if not sum([self._cell[column][y_off+row]._value for row in range(8)]):
					next_empty_x = column
					break
			if next_empty_x:
				if value:
					#debug('sending:', self._name, next_empty_x + x + x_off, y + y_off, value)
					handler.receive_address(self._name, next_empty_x + x + x_off, y + y_off, value = value)
				else:
					element = self._cell[next_empty_x + x + x_off][y + y_off]
					handler.receive_address(self._name, element._x, element._y, value = element._value)


	def mask_next_empty_y(self, x, y, value, *a):
		for handler in self._active_handlers():
			x_off = handler.x_offset
			y_off = handler.y_offset
			next_empty_y = None
			for row in range(y_off, y_off+8):
				if not sum([self._cell[x_off+column][y_off+row]._value for column in range(8)]):
					next_empty_y = row
					break
			if next_empty_y:
				if value:
					handler.receive_address(self._name, x + x_off, next_empty_y + y + y_off, value = value)
				else:
					element = self._cell[x + x_off][next_empty_y + y + y_off]
					handler.receive_address(self._name, element._x, element._y, value = element._value)


class ButtonGrid(Grid):


	def __init__(self, name, width, height, active_handlers = return_empty, *a, **k):
		self._active_handlers = active_handlers
		self._name = name
		self._cell = [[StoredElement(active_handlers, _name = self._name + '_' + str(x) + '_' + str(y), _x = x, _y = y, _identifier = -1, _channel = -1 ) for y in range(height)] for x in range(width)]


	def identifier(self, x, y, identifier = -1, *a):
		element = self._cell[x][y]
		element._identifier = min(127, max(-1, identifier))
		self.update_element(element)


	def channel(self, x, y, channel = -1, *a):
		element = self._cell[x][y]
		element._channel = min(15, max(-1, channel))
		self.update_element(element)


	def update_element(self, element):
		for handler in self._active_handlers():
			handler.receive_address(self._name, element._x, element._y, value = element._value, identifier = element._identifier, channel = element._channel)


class Array(object):


	def __init__(self, name, size, active_handlers = return_empty, *a, **k):
		self._active_handlers = active_handlers
		self._name = name
		self._cell = [StoredElement(self._name + '_' + str(num), _num = num, *a, **k) for num in range(size)]


	def restore(self):
		for element in self._cell:
			self.update_element(element)


	def update_element(self, element):
		for handler in self._active_handlers():
			handler.receive_address(self._name, element._num, value = element._value)


	def value(self, num, value):
		element = self._cell[num]
		element._value = value
		self.update_element(element)


	def all(self, value):
		for num in range(len(self._cell)):
			self.value(num, value)


	def mask(self, num, value):
		control = self._cell[num]
		if value > 0:
			for handler in self._active_handlers():
				handler.receive_address(self._name, control._num, value)
		else:
			self.update_element(control)


	def mask_all(self, value):
		for num in range(len(self._cell)):
			self.mask(num, value)


class RadioArray(Array):


	def value(self, num):
		for element in self._cell:
			element._value = int(element is self._cell[num])
			self.update_element(element)


class RingedStoredElement(StoredElement):


	def __init__(self, active_handlers = return_empty, *a, **attributes):
		self._green = 0
		self._mode = 0
		self._custom = [0, 0, 0, 0, 0, 0, 0, 0, 0]
		super(RingedStoredElement, self).__init__(active_handlers, *a, **attributes)


	def mode(self, value):
		self._mode = value
		self.update_element()


	def green(self, value):
		self._green = value
		self.update_element()


	def custom(self, *values):
		self._custom = values
		self.update_element()


	def update_element(self):
		for handler in self._active_handlers():
			handler.receive_address(self._name, value = self._value)
			handler.receive_address(self._name, green = self._green)
			handler.receive_address(self._name, mode = self._mode)
			handler.receive_address(self._name, custom = self._custom)


class RingedGrid(Grid):


	def __init__(self, name, width, height, active_handlers = return_empty, *a, **k):
		self._active_handlers = active_handlers
		self._name = name
		self._width = width
		self._height = height
		self._relative = False
		self._local = True
		self._cell = [[RingedStoredElement(active_handlers, _name = self._name + '_' + str(x) + '_' + str(y), _x = x, _y = y , *a, **k) for y in range(height)] for x in range(width)]


	def green(self, x, y, value):
		element = self._cell[x][y]
		element._green = value
		self.update_element(element)


	def led(self, x, y, value):
		element = self._cell[x][y]
		element._led = value
		self.update_element(element)


	def mode(self, x, y, value):
		element = self._cell[x][y]
		element._mode = value
		self.update_element(element)


	def custom(self, x, y, *values):
		element = self._cell[x][y]
		element._custom = values
		self.update_element(element)


	def relative(self, value):
		#if not self._relative == value:
		self._relative = bool(value)
		self.restore()


	def local(self, value):
		#if not self._local == bool(value):
		#debug(self._name, 'internal receive local', value)
		self._local = bool(value)
		self.restore()


	def restore(self):
		for handler in self._active_handlers():
			#handler.receive_address(str(self._name+'_relative'), self._relative)
			#handler.receive_address(str(self._name+'_local'), self._local)
			handler.receive_address(self._name, 0, 0, relative = self._relative)
			handler.receive_address(self._name, 0, 0, local = self._local)
		super(RingedGrid, self).restore()


	def update_element(self, element):
		for handler in self._active_handlers():
			handler.receive_address(self._name, element._x, element._y, value = element._value, green = element._green, mode = element._mode, custom = element._custom)


class ModHandler(Component):


	_name = 'DefaultModHandler'

	@depends(device_provider = None)
	def __init__(self, script, addresses=None, device_selector=None, device_provider=None, *a, **k):
		super(ModHandler, self).__init__(*a, **k)
		self._script = script
		self._device_selector = device_selector or DeviceSelectorComponent(script)
		self._device_provider = device_provider
		self._color_type = 'RGB'
		self.modrouter = script.monomodular
		self._active_mod = None
		self._colors = list(range(128))
		self._is_enabled = False
		self._is_connected = False
		self._is_locked = False
		self._is_alted = False
		self._is_shifted = False
		self._is_shiftlocked = False
		self._receive_methods = {}
		self._addresses = {'grid': {'obj':ButtonGrid('grid', 16, 16), 'method':self._receive_grid},
							'key': {'obj':Array('key', 8), 'method':self._receive_key},
							'shift': {'obj':StoredElement(_name = 'shift'), 'method':self._receive_shift},
							'alt': {'obj':StoredElement(_name = 'alt'), 'method':self._receive_alt},
							'channel': {'obj':RadioArray('channel', 16), 'method':self._receive_channel}}
		self._addresses.update(addresses or {})
		self._grid = None
		self._mod_nav_buttons = None
		self.x_offset = 0
		self.y_offset = 0
		self.navbox_selected = 3
		self.navbox_unselected = 5
		self._initialize_receive_methods()
		self.modrouter.register_handler(self)
		self._on_device_changed.subject = self._device_provider
		self.modrouter._task_group.add(sequence(delay(5), self.select_appointed_device))


	def disconnect(self, *a, **k):
		self._active_mod = None
		super(ModHandler, self).disconnect(*a, **k)


	def _initialize_receive_methods(self):
		addresses = self._addresses
		for address, Dict in addresses.items():
			if not address in list(self._receive_methods.keys()):
				self._receive_methods[address] = Dict['method']


	def _register_addresses(self, client):
		addresses = self._addresses
		for address, Dict in addresses.items():
			if not address in list(client._addresses.keys()):
				client._addresses[address] = copy.deepcopy(Dict['obj'])
				client._addresses[address]._active_handlers = client.active_handlers


	def receive_address(self, address_name, *a, **k):
		#debug('receive_address ' + str(address_name) + str(a))
		if address_name in list(self._receive_methods.keys()):
			self._receive_methods[address_name](*a, **k)


	def update(self, *a, **k):
		if self._active_mod:
			self._active_mod.restore()
		self.update_buttons()


	def select_mod(self, mod = None):
		self._active_mod = mod
		self._colors = list(range(128))
		# debug('select_mod(), new mod is:--------------------------------', mod)
		for mod in self.modrouter._mods:
			if self in mod._active_handlers:
				mod._active_handlers.remove(self)
				mod.report_active_handlers()
		if not self._active_mod is None:
			self._active_mod._active_handlers.append(self)
			# if self._color_type in list(self._active_mod._color_maps.keys()):
			# 	self._colors = self._active_mod._color_maps[self._color_type]
			self._active_mod.report_active_handlers()
			self._active_mod.restore()
		self.update()


	def active_mod(self, *a, **k):
		return self._active_mod


	@listens('device')
	def _on_device_changed(self):
		#debug('modhandler on_device_changed')
		if not self.is_locked() or self.active_mod() is None:
			#debug('ModHandler _on_device_changed()')
			self.select_appointed_device()


	def on_selected_track_changed(self):
		#debug('modhandler on_selected_track_changed()')
		if not self.is_locked() or self.active_mod() is None:
			self.select_appointed_device()


	def select_appointed_device(self, *a):
		#debug('select_appointed_device' + str(a))
		self.select_mod(self.modrouter.is_mod(self._device_provider.device))


	def update_buttons(self):
		self._shift_value.subject and self._shift_value.subject.send_value(7 + self.is_shifted()*7)
		self._on_shiftlock_value.subject and self._on_shiftlock_value.subject.send_value(3 + self.is_shiftlocked()*7)
		self._on_lock_value.subject and self._on_lock_value.subject.send_value(1 + self.is_locked()*7)
		self._alt_value.subject and self._alt_value.subject.send_value(2 + self.is_alted()*7)


	def set_mod_nav_buttons(self, buttons):
		self._mod_nav_buttons = buttons
		self._on_mod_nav_button_value.replace_subjects(buttons)
		self._update_mod_nav_buttons()


	@listens_group('value')
	def _on_mod_nav_button_value(self, value, sender):
		if value and not self._mod_nav_buttons is None:
			direction = self._mod_nav_buttons.index(sender)
			if direction:
				self.nav_mod_up()
			else:
				self.nav_mod_down()


	def _update_mod_nav_buttons(self):
		if not self._mod_nav_buttons is None:
			for button in self._mod_nav_buttons:
				if not button is None:
					button.turn_on()


	def nav_mod_down(self):
		new_mod = self.modrouter.get_previous_mod(self.active_mod())
		#debug('new_mod: ' + str(new_mod))
		if isinstance(new_mod, ModClient):
			device = new_mod.linked_device
			#debug('device: ' + str(device))
			if isinstance(device, Live.Device.Device):
				self.song.view.select_device(device)
				#debug('selected: ' + str(device))
				self.select_mod(new_mod)


	def nav_mod_up(self):
		new_mod = self.modrouter.get_next_mod(self.active_mod())
		#debug('new_mod: ' + str(new_mod))
		if isinstance(new_mod, ModClient):
			device = new_mod.linked_device
			if isinstance(device, Live.Device.Device):
				self.song.view.select_device(device)
				self.select_mod(new_mod)


	def select_mod_by_name(self, name, view = False, *a, **k):
		debug('select_mod_by_name', name, view)
		new_mod = self.modrouter.get_mod_by_name(name)
		debug('new_mod:', new_mod);
		if isinstance(new_mod, ModClient):
			device = new_mod.linked_device
			if isinstance(device, Live.Device.Device):
				if view:
					self.song.view.select_device(device)
				self.select_mod(new_mod)


	def show_mod_in_live(self):
		if isinstance(self.active_mod(), Live.Device.Device):
			self.song.view.select_device(self.active_mod().linked_device)


	def set_grid(self, grid):
		#debug('set grid:' + str(grid))
		self._grid = grid
		self._grid_value.subject = grid
		if not self._grid is None:
			for button, _ in grid.iterbuttons():
				if not button == None:
					button.use_default_message()
					if hasattr(button, 'set_enabled'):
						button.set_enabled(True)
					elif hasattr(button, 'suppress_script_forwarding'):
						button.suppress_script_forwarding = False
		self.update()


	def _receive_grid(self, *a, **k):
		debug('receive grid:  this should be overridden')


	@listens('value')
	def _grid_value(self, value, x, y, *a, **k):
		#debug('_grid_value ' + str(x) + str(y) + str(value))
		if self.active_mod():
			if self.active_mod().legacy:
				x += self.x_offset
				y += self.y_offset
			self._active_mod.send('grid', x, y, value)


	def set_key_buttons(self, keys):
		self._keys_value.subject = keys
		if self.active_mod():
			self.active_mod()._addresses['key'].restore()


	def _receive_key(self, x, value):
		#debug('_receive_key: %s %s' % (x, value))
		if not self._keys_value.subject is None:
			self._keys_value.subject.send_value(x, 0, self._colors[value], True)


	@listens('value')
	def _keys_value(self, value, x, y, *a, **k):
		if self._active_mod:
			self._active_mod.send('key', x, value)



	def set_channel_buttons(self, buttons):
		self._channel_value.subject = buttons
		if self.active_mod():
			self.active_mod()._addresses['channel'].restore()


	def _receive_channel(self, x, value):
		#debug('_receive_channel:', x, value)
		if not self._channel_value.subject is None and x < self._channel_value.subject.width():
			self._channel_value.subject.send_value(x, 0, self._colors[value], True)


	@listens('value')
	def _channel_value(self, value, x, y, *a, **k):
		#debug('_channel_value: %s %s' % (x, value))
		if value and self._active_mod:
			self._active_mod.send('channel', x)



	def set_shift_button(self, button):
		self._shift_value.subject = button
		if button:
			button.send_value(self.is_shifted())


	def is_shifted(self):
		return self._is_shifted


	def _receive_shift(self, value):
		if not self._shift_value.subject is None:
			self._shift_value.subject.send_value(value)


	@listens('value')
	def _shift_value(self, value, *a, **k):
		self._is_shifted = not value is 0
		if self.active_mod():
			self._active_mod.send('shift', value)
		self.update()


	def set_alt_button(self, button):
		self._alt_value.subject = button
		if button:
			button.send_value(self.is_alted())


	def is_alted(self):
		return self._is_alted


	def _receive_alt(self, value):
		if not self._alt_value.subject is None:
			self._alt_value.subject.send_value(value)


	@listens('value')
	def _alt_value(self, value, *a, **k):
		self._is_alted = not value is 0
		mod = self.active_mod()
		if mod:
			mod.send('alt', value)
			mod._device_proxy._alted = bool(value)
			mod._device_proxy.update_parameters()
			#mod._param_component._is_alted = bool(value)
			#mod._param_component.update()
			#self.update_device()
		self.update()


	def set_lock_button(self, button):
		self._on_lock_value.subject = button
		self.update()


	def is_locked(self):
		return self._is_locked


	def set_lock(self, value):
		self._is_locked = value > 0
		self.select_appointed_device()


	@listens('value')
	def _on_lock_value(self, value):
		if value>0:
			self.set_lock(not self.is_locked())
		self.update()



	def set_shiftlock_button(self, button):
		self._on_shiftlock_value.subject = button


	def is_shiftlocked(self):
		return self._is_shiftlocked


	@listens('value')
	def _on_shiftlock_value(self, value):
		#debug('shiftlock value ' + str(value))
		if value>0:
			self._is_shiftlocked = not self.is_shiftlocked()
			self.update()



	def set_offset(self, x, y):
		#debug('setting offset:' + str(x) + str(y))
		self.x_offset = max(0, min(x, 12))
		self.y_offset = max(0, min(y, 12))
		if self._active_mod and self._active_mod.legacy:
			self._active_mod.send('offset', self.x_offset, self.y_offset)
			self.update()


	def _display_nav_box(self):
		pass


	def set_device_selector_matrix(self, matrix):
		self._device_selector and self._device_selector.set_matrix(matrix)


	def set_nav_matrix(self, matrix):
		self.nav_box and self.nav_box.set_matrix(matrix)


	def set_nav_buttons(self, buttons):
		assert buttons is None or len(buttons)==4
		if buttons is None:
			buttons = [None for index in range(4)]
		self.set_nav_up_button(buttons[0])
		self.set_nav_down_button(buttons[1])
		self.set_nav_left_button(buttons[2])
		self.set_nav_right_button(buttons[3])


	def set_nav_up_button(self, button):
		if not self.nav_box is None:
			self.nav_box.set_nav_up_button(button)


	def set_nav_down_button(self, button):
		if not self.nav_box is None:
			self.nav_box.set_nav_down_button(button)


	def set_nav_left_button(self, button):
		if not self.nav_box is None:
			self.nav_box.set_nav_left_button(button)


	def set_nav_right_button(self, button):
		if not self.nav_box is None:
			self.nav_box.set_nav_right_button(button)


	def on_enabled_changed(self):
		super(ModHandler, self).on_enabled_changed()
		#if not self.is_enabled():
		#    self._instrument and self._instrument.set_enabled(False)


class NavigationBox(Component):


	def __init__(self, parent, width, height, window_x, window_y, callback = None, *a, **k):
		super(NavigationBox, self).__init__(*a, **k)
		self._parent = parent
		self._width = width
		self._height = height
		self._window_x = window_x
		self._window_y = window_y
		self._callback = callback
		self._scroll_up_ticks_delay = -1
		self._scroll_down_ticks_delay = -1
		self._scroll_right_ticks_delay = -1
		self._scroll_left_ticks_delay = -1
		self._x_inc = 0
		self._y_inc = 0
		self.on_value = 5
		self.off_value = 1
		self.x_offset = 0
		self.y_offset = 0
		#debug('timer is callable:', callable(self._on_timer))
		self._task_group = TaskGroup(auto_kill=False)
		self._task_group.add(totask(self._on_timer))
		#self._register_timer_callback(self._on_timer)


	def width(self):
		return self._width


	def height(self):
		return self._height


	def set_matrix(self, matrix):
		#if matrix:
		#    for button, _ in matrix.iterbuttons():
		#        button and button.set_on_off_values('Mod.Nav.OnValue', 'Mod.Nav.OffValue')
		self._on_navigation_value.subject = matrix
		if not matrix is None:
			self._x_inc = int(self.width()/matrix.width())
			self._y_inc = int(self.height()/matrix.height())
		else:
			self._x_inc = 0
			self._y_inc = 0
		#debug('incs: ' + str(self._x_inc) + ' ' + str(self._y_inc))
		self.update()


	def set_nav_buttons(self, buttons):
		assert buttons is None or len(buttons)==4
		if buttons is None:
			buttons = [None for index in range(4)]
		self.set_nav_up_button(buttons[0])
		self.set_nav_down_button(buttons[1])
		self.set_nav_left_button(buttons[2])
		self.set_nav_right_button(buttons[3])


	def set_nav_up_button(self, button):
		#button and button.set_on_off_values('Mod.Nav.OnValue', 'Mod.Nav.OffValue')
		self._on_nav_up_value.subject = button


	def set_nav_down_button(self, button):
		#button and button.set_on_off_values('Mod.Nav.OnValue', 'Mod.Nav.OffValue')
		self._on_nav_down_value.subject = button


	def set_nav_left_button(self, button):
		#button and button.set_on_off_values('Mod.Nav.OnValue', 'Mod.Nav.OffValue')
		self._on_nav_left_value.subject = button


	def set_nav_right_button(self, button):
		#button and button.set_on_off_values('Mod.Nav.OnValue', 'Mod.Nav.OffValue')
		self._on_nav_right_value.subject = button


	@listens('value')
	def _on_navigation_value(self, value, x, y, *a, **k):
		nav_grid = self._on_navigation_value.subject
		if value>0 and nav_grid:
			new_x = self.x_offset
			new_y = self.y_offset
			xinc = self._x_inc
			yinc = self._y_inc
			newx = x*xinc
			newy = y*yinc
			xoff = self.x_offset
			yoff = self.y_offset
			xmax = xoff+self._window_x
			ymax = yoff+self._window_y
			if newx < xoff:
				new_x = newx
			elif newx >= xmax:
				new_x = (newx+xinc)-self._window_x
			if newy < yoff:
				new_y = newy
			elif newy >= ymax:
				new_y = (newy+yinc)-self._window_y
			#new_x = x * self._x_inc
			#new_y = y * self._y_inc
			# debug('new offsets:', new_x, new_y)
			self.set_offset(new_x, new_y)


	@listens('value')
	def _on_nav_up_value(self, value):
		if value:
			self._scroll_up_ticks_delay = INITIAL_SCROLLING_DELAY
			if (not self._is_scrolling()):
				self.set_offset(self.x_offset, self.y_offset - 1)
				#self.update()
		else:
			self._scroll_up_ticks_delay = -1


	@listens('value')
	def _on_nav_down_value(self, value):
		if value:
			self._scroll_down_ticks_delay = INITIAL_SCROLLING_DELAY
			if (not self._is_scrolling()):
				self.set_offset(self.x_offset, self.y_offset + 1)
				#self.update()
		else:
			self._scroll_down_ticks_delay = -1


	@listens('value')
	def _on_nav_left_value(self, value):
		if value:
			self._scroll_left_ticks_delay = INITIAL_SCROLLING_DELAY
			if (not self._is_scrolling()):
				self.set_offset(self.x_offset - 1, self.y_offset)
				#self.update()
		else:
			self._scroll_left_ticks_delay = -1


	@listens('value')
	def _on_nav_right_value(self, value):
		if value:
			self._scroll_right_ticks_delay = INITIAL_SCROLLING_DELAY
			if (not self._is_scrolling()):
				self.set_offset(self.x_offset + 1, self.y_offset)
				#self.update()
		else:
			self._scroll_right_ticks_delay = -1


	def update(self):
		nav_grid = self._on_navigation_value.subject
		left_button = self._on_nav_left_value.subject
		right_button = self._on_nav_right_value.subject
		up_button = self._on_nav_up_value.subject
		down_button = self._on_nav_down_value.subject
		xinc = self._x_inc
		yinc = self._y_inc
		xoff = self.x_offset
		yoff = self.y_offset
		xmax = xoff+self._window_x
		ymax = yoff+self._window_y
		if nav_grid:
			for button, coord in nav_grid.iterbuttons():
				x = coord[0]
				y = coord[1]
				button and button.set_light('Mod.Nav.OnValue' if ((x*xinc) in range(xoff, xmax)) and ((y*yinc) in range(yoff, ymax)) else 'Mod.Nav.OffValue')
		left_button and left_button.set_light('Mod.Nav.OnValue' if xoff>0 else 'Mod.Nav.OffValue')
		right_button and right_button.set_light(xoff<(self.width()-self._window_x))
		up_button and up_button.set_light('Mod.Nav.OnValue' if yoff>0 else 'Mod.Nav.OffValue')
		down_button and down_button.set_light(yoff<(self.height()-self._window_y))


	def set_offset(self, x, y):
		self.x_offset = min(x, self.width() - self._window_x)
		self.y_offset = min(y, self.height() - self._window_y)
		self.update()
		if self._callback:
			self._callback(x, y)


	def _is_scrolling(self):
		return (0 in (self._scroll_up_ticks_delay, self._scroll_down_ticks_delay, self._scroll_right_ticks_delay, self._scroll_left_ticks_delay))


	def _on_timer(self):
		if self.is_enabled():
			scroll_delays = [self._scroll_up_ticks_delay,
							 self._scroll_down_ticks_delay,
							 self._scroll_right_ticks_delay,
							 self._scroll_left_ticks_delay]
			if (scroll_delays.count(-1) < 4):
				x_increment = 0
				y_increment = 0
				if (self._scroll_right_ticks_delay > -1):
					if self._is_scrolling():
						x_increment += 1
						self._scroll_right_ticks_delay = INTERVAL_SCROLLING_DELAY
					self._scroll_right_ticks_delay -= 1
				if (self._scroll_left_ticks_delay > -1):
					if self._is_scrolling():
						x_increment -= 1
						self._scroll_left_ticks_delay = INTERVAL_SCROLLING_DELAY
					self._scroll_left_ticks_delay -= 1
				if (self._scroll_down_ticks_delay > -1):
					if self._is_scrolling():
						y_increment += 1
						self._scroll_down_ticks_delay = INTERVAL_SCROLLING_DELAY
					self._scroll_down_ticks_delay -= 1
				if (self._scroll_up_ticks_delay > -1):
					if self._is_scrolling():
						y_increment -= 1
						self._scroll_up_ticks_delay = INTERVAL_SCROLLING_DELAY
					self._scroll_up_ticks_delay -= 1
				new_x_offset = max(0, (self.x_offset + x_increment))
				new_y_offset = max(0, (self.y_offset + y_increment))
				if ((new_x_offset != self.x_offset) or (new_y_offset != self.y_offset)):
					self.set_offset(new_x_offset, new_y_offset)
					self.update()


class ModClient(NotifyingControlElement):


	__subject_events__ = (Event(name='value', signal=InputSignal, override=True),)
	_input_signal_listener_count = 0

	def __init__(self, parent, device, name, *a, **k):
		super(ModClient, self).__init__(*a, **k)
		self.name = name
		self._device = device  #the m4l device
		self._device_parent = device.canonical_parent  #used to listen for when the m4l device is removed
		self._parent = parent  #parent is modRouter
		self._active_handlers = []
		self._addresses = {}
		self._translations = {}
		self._translation_groups = {}
		self._mira_address = None
		self._view = 'Full'
		self._report_parameter_data = False
		self._device_proxy = ModGridDeviceProxy(parent = self, mod_device = device)
		self._proxied_devices = [self._device_proxy]
		self.register_addresses()
		if self._device_parent.devices_has_listener(self._device_listener):
			self._device_parent.remove_devices_listener(self._device_listener)
		self._device_parent.add_devices_listener(self._device_listener)
		self._on_parameters_changed.subject = self._device_proxy
		self._on_parameters_changed()

	@listenable_property
	def legacy(self):
		return False

	@property
	def report_parameter_data(self):
		return self._report_parameter_data

	@report_parameter_data.setter
	def report_parameter_data(self, report = True):
		self._report_parameter_data = report
		self._on_parameters_changed()

	def set_report_parameter_data(self, report = True, *a):
		debug('set_report_parameter_data:', report)
		self.report_parameter_data = bool(report)

	@property
	def proxied_devices(self):
		return self._proxied_devices


	@property
	def device(self):
		return self._device

	@listens('parameters')
	def _on_parameters_changed(self):
		self._on_parameters_display_value_changed.replace_subjects(self._device_proxy._params)
		self._on_parameters_normalized_value_changed.replace_subjects(self._device_proxy._params)
		self._on_parameters_name_changed.replace_subjects(self._device_proxy._params)
		if self.report_parameter_data:
			for param in self._device_proxy._params:
				self.send('display_name', param._index, param.display_name)
				self.send('display_value', param._index, param.display_value)
				self.send('normalized_value', param._index, param.normalized_value)

	##none of these listeners will stay connected to js.  they drop out when too much data is sent at once, apparently, however they can be sent on the 
	#normal .send channel fine.  makes absolutely no sense. We're sending exactly the same thing :/  it has nothing to do with the argument length or format,
	#  as it happens even when sending a single 'test' string through.  
	@listens_group('display_name')
	def _on_parameters_name_changed(self, name, param, *a):
		if self.report_parameter_data:
			self.send('display_name', param._index, name)


	@listens_group('display_value')
	def _on_parameters_display_value_changed(self, value, param, *a):
		if self.report_parameter_data:
			self.send('display_value', param._index, value)


	@listens_group('normalized_value')
	def _on_parameters_normalized_value_changed(self, value, param, *a):
		if self.report_parameter_data:
			self.send('normalized_value', param._index, value)


	@property
	def parameter_data(self):
		device = self._device_proxy
		params = device._params
		displays = ([param.display_name, param.display_value, param.normalized_value] for param in params)
		return displays
	

	@listenable_property
	def view(self):
		return self._view


	@listenable_property
	def mira_address(self):
		return self._mira_address


	def register_addresses(self):
		for handler in self._parent._handlers:
			handler._register_addresses(self)
			self.send('register_handler', handler.name)


	def addresses(self):
		return self._addresses


	def translations(self):
		return self._translations


	def active_handlers(self):
		return self._active_handlers


	def report_active_handlers(self):
		args = ['active_handlers'] + [handler._name for handler in self.active_handlers()]
		self.send(*args)


	def Receive(self, address_name, method = 'value', *value_list):
		if address_name in list(self._addresses.keys()):
			address = self._addresses[address_name]
			#debug('address: ' + str(address) + ' value_list: ' + str(value_list))
			try:
				getattr(address, method)(*value_list)
			except:
				debug('Receive method exception', address_name, method, value_list)


	def Distribute(self, function_name, *value_list):
		if hasattr(self, function_name):
			debug('distribute: ' + str(function_name) + str(value_list))
			try:
				getattr(self, function_name)(*value_list)
			except:
				debug('Distribute method exception', function_name, value_list)


	def send(self, control_name, *a):
		#with self._parent._host.component_guard():
		self.notify_value(control_name, *a)


	def is_active(self):
		return (len(self._active_host) > 0)


	def set_enabled(self, val):
		self._enabled = bool(val)


	def reset(self):
		pass


	def restore(self):
		for address_name, address in self._addresses.items():
			address.restore()
		#self._param_component.update()

	#this listens to see when the m4l device disconnets and then dissolves the containing client
	#@listens('devices')
	def _device_listener(self, *a, **k):
		#debug('devices listener....', liveobj_valid(self.device))
		liveobj_valid(self.device) or self._disconnect_client()


	def _disconnect_client(self, reconnect = False):
		#self._device_listener.subject = None
		self._device = None
		self.send('disconnect')
		for handler in self.active_handlers():
			handler.select_mod(None)
		self._parent.remove_mod(self)
		self.disconnect()


	def disconnect(self):
		self._active_handlers = []
		if self._device_parent.devices_has_listener(self._device_listener):
			self._device_parent.remove_devices_listener(self._device_listener)
		self._on_parameters_changed.subject = None
		self._on_parameters_display_value_changed.replace_subjects([None])
		self._on_parameters_normalized_value_changed.replace_subjects([None])
		self._on_parameters_name_changed.replace_subjects([None])
		#self._device_listener.subject = None
		super(ModClient, self).disconnect()


	@property
	def linked_device(self):
		return self.device


	def script_wants_forwarding(self):
		return True


	def receive_device(self, command, *args):
		#debug('receive_device_proxy', 'command:', command, 'args:', args)
		try:
			getattr(self._device_proxy, command)(*args)
		except:
			debug('receive_device exception: %(c)s %(a)s' % {'c':command, 'a':args})


	def update_device(self):
		for handler in self.active_handlers():
			handler.update_device()


	def set_legacy(self, value):
		# debug('set_legacy: ' + str(value))
		self._legacy = value > 0
		# self.notify_legacy(self.legacy)
		# for handler in self.active_handlers():
		# 	handler.update()

	
	def set_mira_address(self, address, *a, **k):
		debug('set_mira_address: ' + str(address))
		self._mira_address = str(address)
		self.notify_mira_address(self.mira_address)


	def set_view(self, view, *a, **k):
		debug('mod.set_view:', view)
		self._view = str(view)
		self.notify_view(self.view)


	def set_name(self, name):
		# debug('set_name:', name)
		self.name = name


	def select_device_from_key(self, key):
		key = str(key)
		preset = None
		for track in self._parent.song.tracks:
			for device in enumerate_track_device(track):
				if(match(key, str(device.name)) != None):
					preset = device
					break
		for return_track in self._parent.song.return_tracks:
			for device in enumerate_track_device(return_track):
				if(match(key, str(device.name)) != None):
					preset = device
					break
		for device in enumerate_track_device(self._parent.song.master_track):
			if(match(key, str(device.name)) != None):
				preset = device
				break
		if preset != None:
			self._parent.song.view.select_device(preset)


	@property
	def parameters(self):
		return self._device_proxy.parameters

	@property
	def parameter_holders(self):
		return self._device_proxy._params


	def Forward(self, method = None, *value_list):
		if not method is None:
			for handler in self.active_handlers():
				try:
					getattr(handler, method)(*value_list)
				except:
					debug('Forward method exception', method, value_list)


	def add_translation(self, name, target, group=None, *args, **k):
		debug('name: ' + str(name) + ' target: ' + str(target) + ' args: ' + str(args))
		if target in list(self._addresses.keys()):
			if not name in list(self._translations.keys()):
				self._translations[name] = ElementTranslation(name, self)
			#debug('adding new target')
			self._translations[name].add_target(target, self._addresses[target], *args)
			if not group is None:
				if not group in list(self._translation_groups.keys()):
					self._translation_groups[group] = []
				self._translation_groups[group].append([name, target])
				#debug('added to group ' + str(group) + ' : ' + str(self._translation_groups[group]))


	def enable_translation(self, name, target, enabled = True):
		if name in list(self._translations.keys()):
			self._translations[name].set_enabled(target, enabled)


	def enable_translation_group(self, group, enabled = True):
		if group in list(self._translation_groups.keys()):
			for pair in self._translation_groups[group]:
				#debug('enabling for ' + str(pair))
				self.enable_translation(pair[0], pair[1], enabled)


	def receive_translation(self, translation_name, method = 'value', *values):
		#value_list = unpack_items(values)
		#debug('receive_translation: ' + str(translation_name) + ' ' + str(method) + ' ' + str(values))
		try:
			self._translations[translation_name].receive(method, *values)
		except:
			debug('receive_translation method exception', translation_name, method, values)


class ModRouter(Component):


	def __init__(self, *a, **k):
		super(ModRouter, self).__init__(*a, **k)
		self._host = None
		self._task_group = TaskGroup(auto_kill=False)
		self._handlers = []
		self._mods = []
		self._is_connected = True
		self.log_message = self._log_message
		return None


	def set_host(self, host):
		assert isinstance(host, ControlSurface)
		self._host = host
		#self._task_group = host._task_group
		self._host.log_message('host registered: ' + str(host))
		self.log_message = host.log_message


	def has_host(self):
		return not self._host is None


	def _log_message(self, *a, **k):
		pass


	def register_handler(self, handler):
		if handler not in self._handlers:
			self._handlers.append(handler)
		for mod in self._mods:
			mod.register_addresses()
			mod.send('disconnect')


	def unregister_handler(self, cs, handler):
		debug('unregistering handler ' + str(cs) + ' ' + str(handler))
		for mod in self._mods:
			mod.send('disconnect')
		for index in range(len(self._handlers)):
			if self._handlers[index] is handler:
				self._host = None
				self._task_group = None
				debug('deleting from handlers: ' + str(self._handlers[index]))
				del self._handlers[index]
				for surface in get_control_surfaces():
					if not surface is cs:
						if hasattr(surface, 'monomodular'):
							debug('reconnecting router to ' + str(surface))
							self.set_host(surface)
							break
				self._log_message = self._log_message
				break


	@listenable_property
	def connected(self):
		return self._is_connected

	@connected.setter
	def connected(self, is_connected):
		self._is_connected = is_connected
		self.notify_connected()

	@listenable_property
	def mods(self):
		return self._mods


	@mods.setter
	def mods(self, mods):
		self._mods = mods
		self.notify_mods()


	def update_handlers(self, *a, **k):
		self.notify_mods()
		for handler in self._handlers:
			handler._on_device_changed()


	@property
	def devices(self):
		return [mod.device for mod in self.mods]


	def get_mod(self, device):
		#debug('getting mod...')
		mod_client = None
		for mod in self.mods:
			if mod.device == device:
				mod_client = mod
		return mod_client


	def get_next_mod(self, active_mod):
		if not active_mod is None:
			return self._mods[(self._mods.index(active_mod) +1) % len(self._mods)]
		elif not len(self._mods) is 0:
			return self._mods[0]
		else:
			return None


	def get_previous_mod(self, active_mod):
		if not active_mod is None:
			return self._mods[(self._mods.index(active_mod) + len(self._mods) -1) % len(self._mods)]
		elif not len(self._mods) is 0:
			return self._mods[-1]
		else:
			return active_mod


	def get_mod_by_name(self, name):
		# debug('getting mod by name...', name)
		mod_client = None
		for mod in self.mods:
			if mod.name == name:
				mod_client = mod
		return mod_client


	def add_mod(self, device):
		try:
			mod_client = self.get_mod(device)
			debug('add_mod', device)
			if not mod_client is None:
				mod_client._disconnect_client()
			with self._host.component_guard():
				#this needs a unique naming convention, this doesn't actually do anything
				mod_client = ModClient(parent = self, device = device, name = 'modClient'+str(len(self.mods)))
				self._mods.append( mod_client )
			debug('add mod device:', device.name, mod_client)
			# self._host.schedule_message(1, self.update_handlers)
			self.notify_mods()
			return mod_client
		except Exception as e:
			debug('add_mod EXCEPTION:', e)

	# def add_mod(self, device):
	# 	mod_client = self.get_mod(device)
	# 	debug('add_mod', device)
	# 	#debug('devices:', self.devices)
	# 	if mod_client is None:
	# 		#debug('device not in self.mods')
	# 		with self._host.component_guard():
	# 			mod_client = ModClient(parent = self, device = device, name = 'modClient'+str(len(self.mods)))
	# 			self._mods.append( mod_client )
	# 	debug('add mod device:', device.name, mod_client)
	# 	self._host.schedule_message(1, self.update_handlers)
	# 	return mod_client

	def remove_mod(self, mod):
		if mod in self._mods:
			debug('removing mod:', mod)
			self._mods.remove(mod)


	def timer(self, *a, **k):
		pass


	def update(self):
		pass


	def disconnect(self):
		for mod in self._mods:
			mod._disconnect_client()
		self._mods = []
		# for surface in get_control_surfaces():
			# if hasattr(surface, 'monomodular'):
			# 	debug('deleting monomodular for ' + str(surface))
			# 	del surface.monomodular
		old_host = self._host
		self._host = None
		self._handlers = []
		if hasattr(__builtins__, 'monomodular') or 'monomodular' in list(__builtins__.keys()):
			debug('deleting monomodular from builtins')
			del __builtins__['monomodular']
		for surface in get_control_surfaces():
			if not surface is old_host:
				if hasattr(surface, 'restart_monomodular'):
					surface.schedule_message(2, surface.restart_monomodular)
		self.connected = False
		debug('monomodular is disconnecting....')
		super(ModRouter, self).disconnect()


	def is_mod(self, device):
		#debug('is mod(', device, ')')
		mod_device = None
		if isinstance(device, Live.Device.Device):
			try:
				if device.can_have_chains and not device.can_have_drum_pads and len(device.view.selected_chain.devices)>0:
					device = device.view.selected_chain.devices[0]
			except:
				pass
			debug('device name is:', device.name)
			#debug('---------------device startswith @modAlias:', device.name.startswith('@modAlias'))
			if device.name.startswith('@modAlias:'):
				alias_name = device.name.split('@modAlias:')[1]
				#debug('---------------modAlias name is:', alias_name)
				for mod in self._mods:
					name = mod.device.name if mod.device else None
					#debug('mod device name is:', name)
					#debug('name == alias_name:', str(name) == str(alias_name))
					if str(name) == str(alias_name):
						device = mod.device
						break
		if not device is None:
			for mod in self._mods:
				#debug('mod in mods: ' + str(mod.device))
				if mod.device == device or device in mod.proxied_devices:
					mod_device = mod
					break
		#debug('modrouter is_mod() returned device: ' + str(mod_device))
		return mod_device


class ModDeviceProvider(EventObject):


	device_selection_follows_track_selection = True

	def __init__(self, song = None, *a, **k):
		super(ModDeviceProvider, self).__init__(*a, **k)
		self._device = None
		self._locked_to_device = False
		self.song = song
		self.__on_appointed_device_changed.subject = song
		self.__on_selected_track_changed.subject = song.view
		self.__on_selected_device_changed.subject = song.view.selected_track.view
		#self.__on_mod_device_added.subject = get_modrouter()


	@listenable_property
	def device(self):
		#debug('delivering device:', self._device)
		return self._device


	@device.setter
	def device(self, device):
		device = self.mod_device_from_device(device)
		if liveobj_changed(self._device, device) and not self.is_locked_to_device:
			#self._device = device
			self._device = device
			#debug('setting device:', self._device)
			self.notify_device()


	@listenable_property
	def is_locked_to_device(self):
		return self._locked_to_device


	def lock_to_device(self, device):
		self.device = device
		self._locked_to_device = True
		self.notify_is_locked_to_device()


	def unlock_from_device(self):
		self._locked_to_device = False
		self.notify_is_locked_to_device()
		self.update_device_selection()


	@listens('appointed_device')
	def __on_appointed_device_changed(self):
		self.device = device_to_appoint(self.song.appointed_device)


	@listens('has_macro_mappings')
	def __on_has_macro_mappings_changed(self):
		self.song.appointed_device = device_to_appoint(self.song.view.selected_track.view.selected_device)


	@listens('selected_track')
	def __on_selected_track_changed(self):
		self.__on_selected_device_changed.subject = self.song.view.selected_track.view
		if self.device_selection_follows_track_selection:
			self.update_device_selection()


	@listens('selected_device')
	def __on_selected_device_changed(self):
		self._update_appointed_device()


	@listens('chains')
	def __on_chains_changed(self):
		self._update_appointed_device()


	@listens('mods')
	def __on_mod_device_added(self):
		debug('__on_mod_device_added')
		self.update_device_selection()


	def restart_mod(self):
		self.__on_mod_device_added.subject = get_modrouter()


	def _update_appointed_device(self):
		song = self.song
		device = song.view.selected_track.view.selected_device
		if liveobj_valid(device):
			self.song.appointed_device = device_to_appoint(device)
		rack_device = device if isinstance(device, Live.RackDevice.RackDevice) else None
		self.__on_has_macro_mappings_changed.subject = rack_device
		self.__on_chains_changed.subject = rack_device


	def mod_device_from_device(self, device):
		modrouter = get_modrouter()
		if modrouter:
			mod_device = modrouter.is_mod(device)
			if mod_device and isinstance(mod_device, ModClient):
				device = mod_device._device_proxy
		return device


	def update_device_selection(self):
		debug('--------------update_device_selection')
		view = self.song.view
		track_or_chain = view.selected_chain if view.selected_chain else view.selected_track
		device_to_select = None
		if isinstance(track_or_chain, Live.Track.Track):
			device_to_select = track_or_chain.view.selected_device
		if device_to_select is None and len(track_or_chain.devices) > 0:
			device_to_select = track_or_chain.devices[0]
		if liveobj_valid(device_to_select):
			appointed_device = device_to_appoint(device_to_select)
			self.song.view.select_device(device_to_select, False)
			self.song.appointed_device = appointed_device
			#appointed_device = self.mod_device_from_device(appointed_device)
			self.device = appointed_device
		else:
			self.song.appointed_device = None
			self.device = None


	def reevaluate_device(self):
		debug('reevaluate_device')
		if isinstance(self.device, ModDeviceProxy):
			self.notify_device()
		else:
			device = self.mod_device_from_device(self.device)
			self._device = device
			self.notify_device()


class ModControl(SysexElement):

	def __init__(self, modscript, monomodular, *a, **k):
		self._monomodular = monomodular
		self.modscript = modscript
		super(ModControl, self).__init__(*a, **k)
		self.modscript._do_send_midi = self._monkeypatch__do_send_midi(modscript)


	def _monkeypatch__do_send_midi(self, modscript):
		cls = type(modscript)
		debug('class is:', cls)
		def _do_send_midi(midi_event_bytes):
			super(cls, modscript)._do_send_midi(midi_event_bytes)
			bytes = list(midi_event_bytes)
			self.notify_pipe('midi', *bytes)
		return _do_send_midi

	@listenable_property
	def pipe(self):
		return None

	def _send(self, **a):
		notify_pipe(a)

	@property
	def monomodular(self):
		return self._monomodular

	@property
	def components(self):
		# comps = list(component.__name__ for component in self.modscript._components)
		# debug('components:', comps)
		# for component in comps:
		# 	debug('component name:', component, component.__name__)
		return tuple(component for component in self.modscript.components)

	@property
	def controls(self):
		# return tuple(self.modscript._controls)
		return tuple(control for control in self.modscript.controls)

	@property
	def functions(self):
		return tuple(item for item in dir(self.modscript) if not item.startswith('_'))

	# def get_script_component(self, name):
	# 	if hasattr(self.modscript, name):
	# 		return getattr(self.modscript, name)
	# 	else:
	# 		return None

	def get_control(self, name):
		debug('get control:', name)
		return self._get_cs_control(self.modscript, name)

	def _get_cs_control(self, cs, name):
		for control in cs.controls:
			if hasattr(control, u'name') and control.name == name:
				return control

	def call_script_function(self, func, *a, **k):
		debug('call_script_function:', func, a, k)
		# if hasattr(self.script, func) and callable(getattr(self.script, func)):
		try:
			debug('trying func:', func, *a, **k)
			getattr(self.modscript, func)(*a, **k)
		except:
			pass

	def receive_note(self, num, val, chan=0):
		# debug('receive_note', num, val)
		self.modscript.receive_midi(tuple([144+chan, num, val]))

	def receive_cc(self, num, val, chan=0):
		# debug('receive_cc', num, val)
		self.modscript.receive_midi(tuple([176+chan, num, val]))





#a
