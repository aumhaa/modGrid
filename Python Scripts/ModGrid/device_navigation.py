
from contextlib import contextmanager
from itertools import chain
from functools import partial,  update_wrapper, singledispatch

from future.moves.itertools import zip_longest

import Live
from ableton.v2.base import PY3, find_if, first, index_if, listenable_property, listens, listens_group, liveobj_changed, liveobj_valid, EventObject, SlotGroup, task
from ableton.v2.control_surface import DecoratorFactory, device_to_appoint
from ableton.v2.control_surface.components import DeviceNavigationComponent as DeviceNavigationComponentBase, FlattenedDeviceChain, ItemSlot, ItemProvider, is_empty_rack, nested_device_parent
from ableton.v2.control_surface.control import control_list, StepEncoderControl
from ableton.v2.control_surface.mode import Component, ModesComponent, NullModes, DelayMode, AddLayerMode, Layer
from ableton.v2.control_surface.control import ButtonControl
from ableton.v2.control_surface.elements import DisplayDataSource

from pushbase.device_chain_utils import is_first_device_on_pad
from Push2.bank_selection_component import BankSelectionComponent, BankProvider
from Push2.chain_selection_component import ChainSelectionComponent
from Push2.colors import DISPLAY_BUTTON_SHADE_LEVEL, IndexedColor
from Push2.device_util import is_drum_pad, find_chain_or_track
from Push2.item_lister import IconItemSlot, ItemListerComponent

# from Push2.device_navigation import singledispatchmethod

# from aumhaa.v3.base.debug import log_flattened_arguments
from aumhaa.v3.base import initialize_debug

# if PY3:
# 	from functools import singledispatch
# else:
# 	from singledispatch import singledispatch

# def singledispatchmethod(func):
# 	dispatcher = singledispatch(func)

# 	def wrapper(*args, **kw):
# 		return (dispatcher.dispatch(args[1].__class__))(*args, **kw)

# 	wrapper.register = dispatcher.register
# 	update_wrapper(wrapper, func)
# 	return wrapper

def nop(self, *a, **k):
	pass


LOCAL_DEBUG = False
debug = initialize_debug(local_debug=LOCAL_DEBUG)


def singledispatchmethod(func):
	"""
	TODO(lsp) Replace with builtin decorator when we update to python 3.8+
	this method didn't include a catch for calls without arguments, so it is added in the wrapper
	"""
	dispatcher = singledispatch(func)

	def wrapper(*args, **kw):
		return dispatcher.dispatch(args[0].__class__)(*args, **kw)
		# debug('args:', args)
		# if len(args) > 1:
		# 	return dispatcher.dispatch(args[0].__class__)(*args, **kw)
		# else:
		# 	return nop

	wrapper.register = dispatcher.register
	update_wrapper(wrapper, func)
	return wrapper


def find_drum_pad(items):
	elements = map(lambda i: i.item, items)
	return find_if(lambda e: is_drum_pad(e), elements)


@singledispatchmethod
def is_active_element(drum_pad):
	# debug('drumpad is_active')
	return not drum_pad.mute and drum_pad.canonical_parent.is_active


@singledispatchmethod
def is_active_element(device):
	return device.is_active
	# active = is_on(device)
	# debug('active:', active)
	# return active

@is_active_element.register(Live.DrumPad.DrumPad)
def _(drum_pad):
	return not drum_pad.mute and drum_pad.canonical_parent.is_active

def set_enabled(device, is_on):
	device.parameters[0].value = int(is_on)


def is_on(device):
	return bool(device.parameters[0].value)


def collect_devices(track_or_chain, nesting_level = 0):
	chain_devices = track_or_chain.devices if liveobj_valid(track_or_chain) else []
	devices = []
	for device in chain_devices:
		devices.append((device, nesting_level))
		if device.can_have_drum_pads and device.view.selected_drum_pad:
			devices.append((device.view.selected_drum_pad, nesting_level + 1))
		devices.extend(collect_devices(nested_device_parent(device), nesting_level=nesting_level + 1))

	return devices


def delete_device(device):
	device_parent = device.canonical_parent
	device_index = list(device_parent.devices).index(device)
	device_parent.delete_device(device_index)


def drum_rack_for_pad(drum_pad):
	return drum_pad.canonical_parent


class DisplayingButtonControl(ButtonControl):

	class State(ButtonControl.State):
		text = ''

		def __init__(self, text=None, *a, **k):
			(super(DisplayingButtonControl.State, self).__init__)(*a, **k)
			if text is not None:
				self.text = text

		def set_control_element(self, control_element):
			super(DisplayingButtonControl.State, self).set_control_element(control_element)
			if hasattr(control_element, "_display"):
				control_element._display.display_message(self.text)


# class DisplayingButtonControl(ButtonControl):
#
# 	class State(ButtonControl.State):
#
# 		def __init__(self, text=None, *a, **k):
# 			self._text_data_source = DisplayDataSource(text)
# 			(super(DisplayingButtonControl.State, self).__init__)(*a, **k)
#
# 		def set_control_element(self, control_element):
# 			super(DisplayingButtonControl.State, self).set_control_element(control_element)
# 			if hasattr(control_element, "_display"):
# 				control_element._display.set_data_sources([self._text_data_source])


class SpecialBankSelectionComponent(BankSelectionComponent):

	color_class_name = 'BankSelection'
	next_bank_button = DisplayingButtonControl(text="Bank->")
	previous_bank_button = DisplayingButtonControl(text="<-Bank")
	text_data_sources = [DisplayDataSource('') for index in range(8)]

	def __init__(self, *a, **k):
		super(SpecialBankSelectionComponent, self).__init__(*a, **k)
		self._on_item_names_changed.subject = self
		self._on_item_names_changed()


	def _create_slot(self, index, item, nesting_level):
		items = self._item_provider.items[self.item_offset:]
		num_slots = min(self._num_visible_items, len(items))
		slot = None
		if index == 0 and self.can_scroll_left():
			slot = IconItemSlot(name='<--', icon='page_left.svg')
			slot.is_scrolling_indicator = True
		elif index == num_slots - 1 and self.can_scroll_right():
			slot = IconItemSlot(name='-->', icon='page_right.svg')
			slot.is_scrolling_indicator = True
		else:
			slot = ItemSlot(item=item, nesting_level=nesting_level)
			slot.is_scrolling_indicator = False
		return slot

	@listens('items')
	def _on_item_names_changed(self, *a):
		debug('BANK._on_item_names_changed:')
		items = [x.item for x in self.items]
		new_items = [str(item.name) if hasattr(item, 'name') else '-B-' for item in items]
		items[:len(new_items)] = new_items
		debug('BANK._on_items_changed:', items)
		for source, item in zip_longest(self.text_data_sources, items):
			if source:
				source.set_display_string(item if not item is None else '')

	def set_select_buttons(self, buttons):
		if not buttons is None:
			self.select_buttons.set_control_element(buttons)
			for index, button in enumerate(buttons):
				if hasattr(button, "_display"):
					button._display.set_data_sources([self.text_data_sources[index]])
		else:
			self.select_buttons.set_control_element(None)

	def set_select_button_displays(self, displays):
		debug('set_select_button_displays', displays)
		# super(ModGridDeviceNavigationComponent, self).set_select_buttons(buttons)
		for source, display in zip_longest(self.text_data_sources, displays or []):
			if hasattr(display, "set_data_sources"):
				display.set_data_sources([source])


	def update(self, *a, **k):
		super(SpecialBankSelectionComponent, self).update(*a, **k)
		if self.is_enabled():
			self._update_button_colors()

	def _color_for_button(self, button_index, is_selected):
		# debug('color_for_button:', button_index, is_selected)
		if is_selected:
			return self.color_class_name + '.ItemSelected'
		return self.color_class_name + '.ItemNotSelected'

	def set_previous_bank_button(self, button):
		self.previous_bank_button.set_control_element(button)

	def set_next_bank_button(self, button):
		self.next_bank_button.set_control_element(button)

	@next_bank_button.pressed
	def next_bank_button(self, button):
		debug('BankSelection._on_next_bank_button_pressed')
		self._bank_provider._bank_registry.set_device_bank(self._bank_provider._device, min(len(self._bank_provider.items), self._bank_provider._bank_registry.get_device_bank(self._bank_provider._device) + 1))


	@previous_bank_button.pressed
	def previous_bank_button(self, button):
		debug('BankSelection._on_previous_bank_button_pressed')
		self._bank_provider._bank_registry.set_device_bank(self._bank_provider._device, max(0, self._bank_provider._bank_registry.get_device_bank(self._bank_provider._device) - 1))


class SpecialChainSelectionComponent(ChainSelectionComponent):

	color_class_name = 'ChainNavigation'
	# select_buttons = control_list(DisplayingButtonControl,
	#   unavailable_color=(color_class_name + '.NoItem'))
	text_data_sources = [DisplayDataSource('') for index in range(8)]

	def __init__(self, *a, **k):
		super(SpecialChainSelectionComponent, self).__init__(*a, **k)
		self._on_item_names_changed.subject = self
		self._on_item_names_changed()

	def _on_select_button_pressed(self, button):
		super(SpecialChainSelectionComponent, self)._on_select_button_pressed(button)
		self._parent._exit_chain_selection()

	def set_select_buttons(self, buttons):
		if not buttons is None:
			self.select_buttons.set_control_element(buttons)
			for index, button in enumerate(buttons):
				if hasattr(button, "_display"):
					button._display.set_data_sources([self.text_data_sources[index]])
		else:
			self.select_buttons.set_control_element(None)

	def _create_slot(self, index, item, nesting_level):
		#debug('ChainSelector._create_slot')
		items = self._item_provider.items[self.item_offset:]
		num_slots = min(self._num_visible_items, len(items))
		slot = None
		if index == 0 and self.can_scroll_left():
			slot = IconItemSlot(icon='page_left.svg')
			slot.is_scrolling_indicator = True
		elif index == num_slots - 1 and self.can_scroll_right():
			slot = IconItemSlot(icon='page_right.svg')
			slot.is_scrolling_indicator = True
		else:
			slot = ItemSlot(item=item, nesting_level=nesting_level)
			slot.is_scrolling_indicator = False
		return slot

	@listens('items')
	def _on_item_names_changed(self, *a):
		debug('CHAINS._on_item_names_changed:')
		items = [x.item for x in self.items]
		debug('items:', items)
		new_items = [str(item.name) if hasattr(item, 'name') else '-C-' for item in items]
		items[:len(new_items)] = new_items
		debug('CHAINS._on_items_changed:', items)
		for source, item in zip_longest(self.text_data_sources, items):
			if source:
				source.set_display_string(item if not item is None else '')

	def update(self, *a, **k):
		super(SpecialChainSelectionComponent, self).update(*a, **k)
		if self.is_enabled():
			self._update_button_colors()

	def _color_for_button(self, button_index, is_selected):
		if is_selected:
			return self.color_class_name + '.ItemSelected'
		return self.color_class_name + '.ItemNotSelected'

	# def _scroll_left(self):
	# 	debug('scroll_left')
	# 	super(SpecialChainSelectionComponent, self)._scroll_left()
	# 	debug('scroll_left finished')


class DeviceChainStateWatcher(EventObject):
	"""
	Listens to the device navigations items and notifies whenever the items state
	changes and the color of the buttons might be affected.
	"""
	__events__ = ('state',)

	def __init__(self, device_navigation = None, *a, **k):
		assert device_navigation is not None
		super(DeviceChainStateWatcher, self).__init__(*a, **k)
		self._device_navigation = device_navigation
		self.__on_items_changed.subject = device_navigation
		self._update_listeners_and_notify()

	@listens('items')
	def __on_items_changed(self, *a):
		self._update_listeners_and_notify()

	@listens_group('is_active')
	def __on_is_active_changed(self, device):
		self.notify_state()

	@listens_group('color_index')
	def __on_chain_color_index_changed(self, chain):
		self.notify_state()

	@listens('mute')
	def __on_mute_changed(self):
		self.notify_state()

	def _navigation_items(self):
		return filter(lambda i: not i.is_scrolling_indicator, self._device_navigation.items)

	def _devices(self):
		device_items = filter(lambda i: not is_drum_pad(i.item), self._navigation_items())
		return [i.item for i in device_items]

	def _update_listeners_and_notify(self):
		debug('............................_update_listeners_and_notify')
		items = list(self._navigation_items())
		chains = set(filter(liveobj_valid, map(lambda i: find_chain_or_track(i.item), items)))
		self.__on_is_active_changed.replace_subjects(self._devices())
		self.__on_mute_changed.subject = find_drum_pad(items)
		self.__on_chain_color_index_changed.replace_subjects(chains)
		self.notify_state()


class MoveDeviceComponent(Component):
	MOVE_DELAY = 0.1
	move_encoders = control_list(StepEncoderControl)

	def __init__(self, *a, **k):
		super(MoveDeviceComponent, self).__init__(*a, **k)
		self._device = None

	def set_device(self, device):
		self._device = device

	@move_encoders.value
	def move_encoders(self, value, encoder):
		if liveobj_valid(self._device):
			with self._disabled_encoders():
				if value > 0:
					self._move_right()
				else:
					self._move_left()

	@contextmanager
	def _disabled_encoders(self):
		self._disable_all_encoders()
		yield
		self._tasks.add(task.sequence(task.wait(self.MOVE_DELAY), task.run(self._enable_all_encoders)))

	def _disable_all_encoders(self):
		for encoder in self.move_encoders:
			encoder.enabled = False

	def _enable_all_encoders(self):
		for encoder in self.move_encoders:
			encoder.enabled = True

	def _move_right(self):
		parent = self._device.canonical_parent
		device_index = list(parent.devices).index(self._device)
		if device_index == len(parent.devices) - 1 and isinstance(parent, Live.Chain.Chain):
			self._move_out(parent.canonical_parent, move_behind=True)
		elif device_index < len(parent.devices) - 1:
			right_device = parent.devices[device_index + 1]
			if right_device.can_have_chains and right_device.view.is_showing_chain_devices and right_device.view.selected_chain:
				self._move_in(right_device)
			else:
				self.song.move_device(self._device, parent, device_index + 2)

	def _move_left(self):
		parent = self._device.canonical_parent
		device_index = list(parent.devices).index(self._device)
		if device_index > 0:
			left_device = parent.devices[device_index - 1]
			if left_device.can_have_chains and left_device.view.is_showing_chain_devices and left_device.view.selected_chain:
				self._move_in(left_device, move_to_end=True)
			else:
				self.song.move_device(self._device, parent, device_index - 1)
		elif isinstance(parent, Live.Chain.Chain):
			self._move_out(parent.canonical_parent)

	def _move_out(self, rack, move_behind = False):
		parent = rack.canonical_parent
		rack_index = list(parent.devices).index(rack)
		self.song.move_device(self._device, parent, rack_index + 1 if move_behind else rack_index)

	def _move_in(self, rack, move_to_end = False):
		chain = rack.view.selected_chain
		if chain:
			self.song.move_device(self._device, chain, len(chain.devices) if move_to_end else 0)


class DeviceNavigationComponent(DeviceNavigationComponentBase):
	__events__ = ('drum_pad_selection', 'mute_solo_stop_cancel_action_performed')
	color_class_name = 'DeviceNavigation'
	# disable_button = DisplayingButtonControl(text="Disable")
	disable_button = ButtonControl()
	text_data_sources = [DisplayDataSource('') for index in range(8)]

	def __init__(self, device_bank_registry = None, banking_info = None, delete_handler = None, track_list_component = None, *a, **k):
		assert banking_info is not None
		assert device_bank_registry is not None
		assert track_list_component is not None
		self._flattened_chain = FlattenedDeviceChain(collect_devices)
		self._track_decorator = DecoratorFactory()
		self._modes = NullModes()
		self.move_device = None
		super(DeviceNavigationComponent, self).__init__(item_provider=self._flattened_chain, *a, **k)
		self._delete_handler = delete_handler
		self.chain_selection = SpecialChainSelectionComponent(parent=self, is_enabled=False)
		# self.chain_selection.select_button_layer = AddLayerMode(self.chain_selection, Layer([]))
		self.bank_selection = SpecialBankSelectionComponent(bank_registry=device_bank_registry, banking_info=banking_info, device_options_provider=self._device_component, is_enabled=False, parent=self)
		# self.bank_selection.select_button_layer = AddLayerMode(self.bank_selection, Layer([]))
		self.move_device = MoveDeviceComponent(parent=self, is_enabled=False)
		self._last_pressed_button_index = -1
		self._selected_on_previous_press = None
		self._was_in_chain_mode = False
		self._was_in_bank_mode = False
		self._modes = ModesComponent(parent=self)
		self._modes.add_mode('default', [partial(self.chain_selection.set_parent, None), partial(self.bank_selection.set_device, None), self.update_item_name_listeners, DelayMode(self.update, delay = .05, parent_task_group = self._tasks)])
		self._modes.add_mode('chain_selection', [self.chain_selection, self.update_item_name_listeners, DelayMode(self.update, delay = .05, parent_task_group = self._tasks)])
		self._modes.add_mode('bank_selection', [self.bank_selection, self.update_item_name_listeners, DelayMode(self.update, delay = .05, parent_task_group = self._tasks)])
		self._modes.selected_mode = 'default'
		self.register_disconnectable(self._flattened_chain)
		self.__on_items_changed.subject = self
		self.__on_bank_selection_closed.subject = self.bank_selection
		self.__on_bank_items_changed.subject = self.bank_selection
		self.__on_chain_items_changed.subject = self.chain_selection
		# self.__on_chain_selection_closed.subject = self.chain_selection
		self._update_selected_track()
		self._track_list = track_list_component
		watcher = self.register_disconnectable(DeviceChainStateWatcher(device_navigation=self))
		self.__on_device_item_state_changed.subject = watcher
		self._on_mode_changed.subject = self._modes
		self._update_device()
		self._update_button_colors()
		self._on_item_names_changed.subject = self
		self._on_item_names_changed()

	# def set_bank_and_chain_select_buttons(self, buttons):
	# 	self._bank_and_chain_select_buttons = buttons
	# 	self.chain_selection.select_button_layer = AddLayerMode(self.chain_selection, Layer())


	@listens('items')
	def _on_item_names_changed(self, *a):
		items = [x.item for x in self.items]
		new_items = [str(item.name) if hasattr(item, 'name') else '' for item in items]
		items[:len(new_items)] = new_items
		# debug('_on_items_changed:', items)
		for source, item in zip_longest(self.text_data_sources, items):
			if source:
				source.set_display_string(item if not item is None else '')
		#self.bank_selection._on_item_names_changed()
		# self.chain_selection._on_item_names_changed()

	# def set_select_buttons(self, buttons):

	def set_select_button_displays(self, displays):
		debug('set_select_button_displays', displays)
		# super(ModGridDeviceNavigationComponent, self).set_select_buttons(buttons)
		for source, display in zip_longest(self.text_data_sources, displays or []):
			if hasattr(display, "set_data_sources"):
				display.set_data_sources([source])

	def _update_button_colors(self, *a, **k):
		super(DeviceNavigationComponent, self)._update_button_colors()

	def update(self, *a, **k):
		super(DeviceNavigationComponent, self).update(*a, **k)
		if self.is_enabled():
			self._update_button_colors()
			self.chain_selection._update_button_colors()
			self.bank_selection._update_button_colors()

	def set_select_buttons(self, buttons):
		if not buttons is None:
			self.select_buttons.set_control_element(buttons)
			for index, button in enumerate(buttons):
				if hasattr(button, "_display"):
					button._display.set_data_sources([self.text_data_sources[index]])
		else:
			self.select_buttons.set_control_element(None)


	@property
	def modes(self):
		return self._modes

	@listens('selected_mode')
	def _on_mode_changed(self, *a, **k):
		self._update_button_colors()
		self.chain_selection._update_button_colors()
		self.bank_selection._update_button_colors()

	#use select button + device instead
	# @disable_button.pressed
	# def disable_button(self, button):
	# 	debug('disable_button pressed', button)
	#     self._toggle_device

	def _in_device_enabling_mode(self):
		#return self.disable_button.is_pressed()
		# debug('disable_button:', self.disable_button)
		# debug('disable_button._is_pressed:', self.disable_button._is_pressed)
		return self.disable_button._is_pressed
		# return False

	def _on_select_button_pressed(self, button):
		debug('on_select_button_pressed')
		device_or_pad = self.items[button.index].item
		if self._in_device_enabling_mode():
			self._toggle_device(device_or_pad)
			self.notify_mute_solo_stop_cancel_action_performed()
		else:
			self._last_pressed_button_index = button.index
			if not self._delete_handler or not self._delete_handler.is_deleting:
				self._selected_on_previous_press = device_or_pad if self.selected_object != device_or_pad else None
				self._was_in_chain_mode = self._modes.selected_mode == 'chain_selection'
				self._was_in_bank_mode = self._modes.selected_mode == 'bank_selection'
				# debug('was_in_chain_mode:', self._was_in_chain_mode, self._was_in_bank_mode)
				self._select_item(device_or_pad)

	def _on_select_button_released_immediately(self, button):
		debug('_on_select_button_released_immediately')
		if not self._in_device_enabling_mode():
			self._last_pressed_button_index = -1
			device_or_pad = self.items[button.index].item
			if self._delete_handler and self._delete_handler.is_deleting:
				self._delete_item(device_or_pad)
			elif self.selected_object == device_or_pad and device_or_pad != self._selected_on_previous_press:
				self._on_reselecting_object(device_or_pad)
			self._selected_on_previous_press = None

	def _on_select_button_pressed_delayed(self, button):
		debug('_on_select_button_pressed_delayed')
		if not self._in_device_enabling_mode():
			self._on_pressed_delayed(self.items[button.index].item)

	def _on_select_button_released(self, button):
		debug('_on_select_button_released')
		if button.index == self._last_pressed_button_index:
			self._modes.selected_mode = 'default'
			self._last_pressed_button_index = -1
			self._end_move_device()

	# @select_buttons.double_clicked
	# def select_buttons(self, button):
	# 	self._on_select_button_double_clicked(button)
	#
	# def _on_select_button_double_clicked(self, button):
	# 	debug('_on_select_button_double_clicked', button)

	@singledispatchmethod
	def _toggle_device(self, drum_pad):
		if liveobj_valid(drum_pad):
			drum_pad.mute = not drum_pad.mute

	@singledispatchmethod
	def _toggle_device(self, device):
		if liveobj_valid(device) and device.parameters[0].is_enabled:
			set_enabled(device, not is_on(device))

	@listens('state')
	def __on_device_item_state_changed(self):
		self._update_button_colors()
		# debug('___________________________________________________________________adding task...')
		self._tasks.add(self._update_button_colors)

	@listenable_property
	def item_names(self):
		items = ['-' for index in range(16)]
		if self._modes.selected_mode == 'default' or self._modes.selected_mode == 'chain_selection':
			new_items = [str(item.name).replace(' ', '_') if hasattr(item, 'name') else '-' for item in self.items]
			items[:len(new_items)] = new_items
		if self._modes.selected_mode == 'chain_selection':
			items[8:] = [str(item.name).replace(' ', '_') if hasattr(item, 'name') else  '-' for item in self.chain_selection.items]
		elif self._modes.selected_mode == 'bank_selection':
			items[8:] = [str(item.name).replace(' ', '_') if hasattr(item, 'name') else '-' for item in self.bank_selection.items]
		return tuple(items)

	@listens('items')
	def __on_bank_items_changed(self):
		# new_items = map(lambda x: x.item, self.bank_selection.items)
		# names = self.item_names
		# self.notify_item_names()
		# debug('BANK CHANGED')
		self.update_item_name_listeners()

	@listens('items')
	def __on_chain_items_changed(self):
		# names = self.item_names
		# self.notify_item_names()
		# new_items = map(lambda x: x.item, self.chain_selection.items)
		self.update_item_name_listeners()

	@listens('items')
	def __on_items_changed(self):
		new_items = [x.item for x in self.items]
		lost_selection_on_empty_pad = new_items and is_drum_pad(new_items[-1]) and self._flattened_chain.selected_item not in new_items
		if self._should_select_drum_pad() or lost_selection_on_empty_pad:
			self._select_item(self._current_drum_pad())
		if self.moving:
			self._show_selected_item()
		self.notify_drum_pad_selection()
		self.update_item_name_listeners()
		# new_items = [str(item.name) if hasattr(item, 'name') else ('*' if item.is_scrolling_indicator else 'x') for item in self.items]


	def update_item_name_listeners(self):
		names = self.item_names
		self.notify_item_names(*names)

	def _create_slot(self, index, item, nesting_level):
		items = self._item_provider.items[self.item_offset:]
		num_slots = min(self._num_visible_items, len(items))
		slot = None
		if index == 0 and self.can_scroll_left():
			slot = IconItemSlot(name='<-', icon='page_left.svg')
			slot.is_scrolling_indicator = True
		elif index == num_slots - 1 and self.can_scroll_right():
			slot = IconItemSlot(name='->', icon='page_right.svg')
			slot.is_scrolling_indicator = True
		else:
			slot = ItemSlot(item=item, nesting_level=nesting_level)
			slot.is_scrolling_indicator = False
		return slot

	@listenable_property
	def moving(self):
		return self.move_device.is_enabled()

	@property
	def device_selection_update_allowed(self):
		return not self._should_select_drum_pad()

	def _color_for_button(self, button_index, is_selected):
		item = self.items[button_index]
		device_or_pad = item.item
		is_active = liveobj_valid(device_or_pad) and is_active_element(device_or_pad)
		chain = find_chain_or_track(device_or_pad)
		# debug('is active:', button_index, is_active, liveobj_valid(device_or_pad),is_active_element(device_or_pad) )
		if not is_active:
			return 'ItemNavigation.ItemSelectedOff' if is_selected else 'ItemNavigation.ItemNotSelectedOff'
		elif is_selected:
			return 'ItemNavigation.ItemSelected'
		elif liveobj_valid(chain):
			return IndexedColor.from_live_index(chain.color_index, DISPLAY_BUTTON_SHADE_LEVEL)
			# return 'ItemNavigation.ItemNotSelected'
		else:
			return 'ItemNavigation.ItemNotSelected'

	def _begin_move_device(self, device):
		if not self.move_device.is_enabled() and device.type != Live.Device.DeviceType.instrument:
			self.move_device.set_device(device)
			self.move_device.set_enabled(True)
			self._scroll_overlay.set_enabled(False)
			self.notify_moving()

	def _end_move_device(self):
		if self.move_device and self.move_device.is_enabled():
			self.move_device.set_device(None)
			self.move_device.set_enabled(False)
			self._scroll_overlay.set_enabled(True)
			self.notify_moving()

	def request_drum_pad_selection(self):
		self._current_track().drum_pad_selected = True

	def unfold_current_drum_pad(self):
		self._current_track().drum_pad_selected = False
		self._current_drum_pad().canonical_parent.view.is_showing_chain_devices = True

	def sync_selection_to_selected_device(self):
		self._update_item_provider(self.song.view.selected_track.view.selected_device)

	@property
	def is_drum_pad_selected(self):
		return is_drum_pad(self._flattened_chain.selected_item)

	@property
	def is_drum_pad_unfolded(self):
		selection = self._flattened_chain.selected_item
		assert is_drum_pad(selection)
		return drum_rack_for_pad(selection).view.is_showing_chain_devices

	def _current_track(self):
		return self._track_decorator.decorate(self.song.view.selected_track, additional_properties={'drum_pad_selected': False})

	def _should_select_drum_pad(self):
		return self._current_track().drum_pad_selected

	def _current_drum_pad(self):
		return find_drum_pad(self.items)

	def _update_selected_track(self):
		self._selected_track = self.song.view.selected_track
		selected_track = self._current_track()
		self.reset_offset()
		self._flattened_chain.set_device_parent(selected_track)
		self._device_selection_in_track_changed.subject = selected_track.view
		self._modes.selected_mode = 'default'
		self._end_move_device()
		self._restore_selection(selected_track)

	def _restore_selection(self, selected_track):
		to_select = None
		if self._should_select_drum_pad():
			to_select = self._current_drum_pad()
		if to_select == None:
			to_select = selected_track.view.selected_device
		self._select_item(to_select)

	def back_to_top(self):
		pass

	@property
	def selected_object(self):
		selected_item = self.item_provider.selected_item
		return getattr(selected_item, 'proxied_object', selected_item)

	@singledispatchmethod
	def _do_select_item(self, pad):
		self._current_track().drum_pad_selected = True
		device = self._first_device_on_pad(pad)
		self._appoint_device(device)

	def _first_device_on_pad(self, drum_pad):
		chain = drum_rack_for_pad(drum_pad).view.selected_chain
		if chain and chain.devices:
			return first(chain.devices)

	def _appoint_device(self, device):
		if self._device_component._device_changed(device):
			self._device_component.set_device(device)

	def _select_item(self, device_or_pad):
		debug('_select_item:', self._modes.selected_mode)
		super(DeviceNavigationComponent, self)._select_item(device_or_pad)
	# 	if self._modes.selected_mode == u'chain_selection':
	# 		self._modes.selected_mode = u'default'
	# 	else:
	# 		super(DeviceNavigationComponent, self)._select_item(device_or_pad)

	@singledispatchmethod
	def _do_select_item(self, device):
		self._current_track().drum_pad_selected = False
		if hasattr(device, 'can_have_drum_pads'):
			appointed_device = device_to_appoint(device)
			self._appoint_device(appointed_device)
			self.song.view.select_device(device, False)
			self.song.appointed_device = appointed_device


	@singledispatchmethod
	def _on_reselecting_object(self, drum_pad):
		# debug('_on_reselecting_object drumpad')
		# if self._modes.selected_mode is u'chain_selection':
		# 	self._modes.selected_mode = u'default'
		# else:
		rack = drum_rack_for_pad(drum_pad)
		self._toggle(rack)
		if rack.view.is_showing_chain_devices:
			first_device = self._first_device_on_pad(drum_pad)
			if first_device:
				self._select_item(first_device)
		self.notify_drum_pad_selection()

	@singledispatchmethod
	def _on_reselecting_object(self, device):
		debug('_on_reselecting_object object',  self._modes.selected_mode)
		# if self._modes.selected_mode == 'chain_selection':
		# 	debug('just set mode to default...')
		# 	self._modes.selected_mode = 'default'
		# elif self._modes.selected_mode == 'bank_selection':
		# 	debug('just set mode to default...')
		# 	self._modes.selected_mode = 'default'
		if liveobj_valid(device) and hasattr(device, 'can_have_chains') and device.can_have_chains:
			if not device.can_have_drum_pads:
				self._toggle(device)
			else:
				if self._was_in_chain_mode:
					debug('was in chain mode')
					self._modes.selected_mode = 'default'
					self._was_in_chain_mode = False
				else:
					self._show_chains(device)

		else:
			if self._was_in_bank_mode:
				self._modes.selected_mode = 'default'
				self._was_in_bank_mode = False
			else:
				self.bank_selection.set_device(device)
				self._modes.selected_mode = 'bank_selection'

	@singledispatchmethod
	def _on_pressed_delayed(self, _):
		pass

	@singledispatchmethod
	def _on_pressed_delayed(self, device):
		# self._show_chains(device)
		# self._begin_move_device(device)
		self._toggle_device(device)

	@singledispatchmethod
	def _delete_item(self, pad):
		pass

	@singledispatchmethod
	def _delete_item(self, device):
		delete_device(device)

	def _show_chains(self, device):
		if device.can_have_chains:
			self.chain_selection.set_parent(device)
			self._modes.selected_mode = 'chain_selection'

	@listens('back')
	def __on_bank_selection_closed(self):
		self._modes.selected_mode = 'default'

	@listens('back')
	def __on_chain_selection_closed(self):
		self._modes.selected_mode = 'default'

	def _exit_chain_selection(self):
		debug('last_pressed_button:', self._last_pressed_button_index)

	def _update_device(self):
		if not self._should_select_drum_pad() and not self._is_drum_rack_selected():
			self._modes.selected_mode = 'default'
			self._update_item_provider(self._device_component.device())

	def _is_drum_rack_selected(self):
		selected_item = self._flattened_chain.selected_item
		instrument = self._find_top_level_instrument()
		return liveobj_valid(selected_item) and isinstance(selected_item, Live.RackDevice.RackDevice) and selected_item.can_have_drum_pads and not liveobj_changed(selected_item, instrument)

	def _find_top_level_instrument(self):
		return find_if(lambda device: device.type == Live.Device.DeviceType.instrument, self._current_track().devices)

	@listens('selected_device')
	def _device_selection_in_track_changed(self):
		new_selection = self.song.view.selected_track.view.selected_device
		if self._can_update_device_selection(new_selection):
			self._modes.selected_mode = 'default'
			self._update_item_provider(new_selection)

	def _toggle(self, item):
		view = item.view
		if view.is_collapsed:
			view.is_collapsed = False
			view.is_showing_chain_devices = True
		else:
			view.is_showing_chain_devices = not view.is_showing_chain_devices

	def _can_update_device_selection(self, new_selection):
		can_update = liveobj_valid(new_selection)
		drum_pad_selected_or_requested = self.is_drum_pad_selected or self._should_select_drum_pad()
		if can_update and drum_pad_selected_or_requested:
			if is_empty_rack(new_selection):
				can_update = False
			if can_update and self.is_drum_pad_selected:
				can_update = not is_first_device_on_pad(new_selection, self._flattened_chain.selected_item)
		elif not can_update and not drum_pad_selected_or_requested:
			can_update = True
		return can_update

	def _update_item_provider(self, selection):
		self._flattened_chain.selected_item = selection
		if not is_drum_pad(selection):
			self._current_track().drum_pad_selected = False
		self.notify_drum_pad_selection()
