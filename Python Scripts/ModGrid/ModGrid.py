# by amounra 0123 : http://www.aumhaa.com
# written against Live 11.2.10b3 on 011823


import Live
import time
import math
import sys
from re import *
from itertools import chain, starmap
import inspect


import logging
logger = logging.getLogger(__name__)

from future.moves.itertools import zip_longest
from past.builtins import long

from ableton.v2.base import inject, listens, listens_group, liveobj_valid, is_iterable, nop
from ableton.v2.control_surface import ControlSurface, ControlElement, Layer, Skin, PrioritizedResource, Component, ClipCreator, DeviceBankRegistry, midi, BANK_MAIN_KEY, BANK_PARAMETERS_KEY, use
from ableton.v2.control_surface.elements import ButtonMatrixElement, DoublePressElement, MultiElement, DisplayDataSource, SysexElement, EventElement
from ableton.v2.control_surface.components import MixerComponent, BackgroundComponent, ViewControlComponent, PlayableComponent, ClipSlotComponent, SessionComponent, ViewControlComponent, SessionRingComponent, SessionNavigationComponent, MixerComponent, ChannelStripComponent, UndoRedoComponent, TransportComponent, DeviceNavigationComponent, DisplayingDeviceParameterComponent, DeviceComponent, ScrollComponent
from ableton.v2.control_surface.components.mixer import SimpleTrackAssigner, TrackAssigner, RightAlignTracksTrackAssigner
from ableton.v2.control_surface.mode import AddLayerMode, ModesComponent, DelayMode, CompoundMode
from ableton.v2.control_surface.elements.physical_display import PhysicalDisplayElement, DisplayElement
from ableton.v2.control_surface.elements.display_data_source import adjust_string
from ableton.v2.control_surface.components.session_recording import *
from ableton.v2.control_surface.percussion_instrument_finder import PercussionInstrumentFinder, find_drum_group_device
from ableton.v2.control_surface.control import PlayableControl, ButtonControl, control_matrix, ControlList, MappedSensitivitySettingControl, ToggleButtonControl
from ableton.v2.control_surface.device_decorator_factory import DeviceDecoratorFactory
from ableton.v2.control_surface.default_bank_definitions import BANK_DEFINITIONS
from ableton.v2.control_surface.elements import ButtonElement, ComboElement, WrapperElement, EncoderElement, DisplayDataSource, PlayheadElement
from ableton.v2.control_surface.components.auto_arm import AutoArmComponent
from ableton.v2.control_surface.input_control_element import InputControlElement, MIDI_CC_TYPE, MIDI_NOTE_TYPE, MIDI_PB_TYPE, MIDI_SYSEX_TYPE, ScriptForwarding
from ableton.v2.control_surface import ParameterInfo
from ableton.v2.control_surface.device_parameter_bank import *
from ableton.v2.control_surface.banking_util import *
from ableton.v2.control_surface.device_parameter_bank import DeviceParameterBank
from ableton.v2.control_surface.control import control_list
from ableton.v2.control_surface.components.toggle import ToggleComponent
from ableton.v2.control_surface.mode import *
from ableton.v2.control_surface.components.scroll import *
from ableton.v2.control_surface import CompoundElement
from ableton.v2.control_surface.control import MatrixControl
from ableton.v2.control_surface import midi
# from ableton.v2.control_surface.elements.proxy_element import ProxyElement

# from Push2.device_navigation import DeviceNavigationComponent
# from Push2.track_list import TrackListComponent
from Push2.track_selection import *
from Push2.device_parameter_bank_with_options import DescribedDeviceParameterBankWithOptions
# from Push2.master_track import MasterTrackComponent
from pushbase.actions import DeleteComponent
from pushbase.grid_resolution import GridResolution
# from pushbase.colors import LIVE_COLORS_TO_MIDI_VALUES, RGB_COLOR_TABLE
from pushbase.colors import RGB_COLOR_TABLE
LIVE_COLORS_TO_MIDI_VALUES = {0:0}

from aumhaa.v3.base import initialize_debug
from aumhaa.v3.control_surface import MomentaryBehaviour, ExcludingMomentaryBehaviour, DelayedExcludingMomentaryBehaviour, ShiftedBehaviour, LatchingShiftedBehaviour, FlashingBehaviour
from aumhaa.v3.control_surface.mod_devices import *
from aumhaa.v3.control_surface.mod import *
from aumhaa.v3.control_surface.elements import generate_strip_string, MonoButtonElement, MonoEncoderElement, MonoBridgeElement, generate_strip_string, CodecEncoderElement
from aumhaa.v3.control_surface.elements.mono_button import *
from aumhaa.v3.control_surface.components import MonoDeviceComponent, DeviceNavigator, TranslationComponent, DeviceSelectorComponent
from aumhaa.v3.control_surface.components.m4l_interface import M4LInterfaceComponent
from aumhaa.v3.control_surface.components.mono_mixer import MonoMixerComponent, MonoChannelStripComponent
from aumhaa.v3.control_surface.elements.mono_encoder import *
from aumhaa.v3.control_surface.mono_modes import SendLividSysexMode, SendSysexMode, CancellableBehaviourWithRelease, ColoredCancellableBehaviourWithRelease, MomentaryBehaviour, BicoloredMomentaryBehaviour, DefaultedBehaviour
from aumhaa.v3.control_surface.components.fixed_length_recorder import FixedLengthSessionRecordingComponent

# from aumhaa.v3.control_surface.components.mono_instrument import *


from .loop_selector_component import LoopSelectorComponent
from .parameter_mapping_sensitivities import parameter_mapping_sensitivity, fine_grain_parameter_mapping_sensitivity
from .track_list import TrackListComponent
from .device_navigation import DeviceNavigationComponent as UtilDeviceNavigationComponent
from .device_provider import DeviceProvider as SpecialDeviceProvider
from .mono_instrument import *
from .utilities import *


from pushbase.auto_arm_component import AutoArmComponent

from ableton.v2.control_surface.elements.color import Color
from aumhaa.v3.livid.colors import *

from Launchpad_MK2 import Launchpad_MK2
from .launchpad_mk2_mod import _Launchpad_MK2_setup_mod

from Launchpad_Pro import Launchpad_Pro
from .launchpad_pro_mod import _Launchpad_Pro_setup_mod

from Launchpad import Launchpad
from .launchpad_mod import _Launchpad_setup_mod

"""Custom files, overrides, and files from other scripts"""
from _Generic.Devices import *
from .Map import *

LOCAL_DEBUG = False

debug = initialize_debug(local_debug=LOCAL_DEBUG)

DEVICE_COMPONENTS = ['device_0', 'device_1']
LENGTH_VALUES = [2, 3, 4]
SYSEX_HEADER = (240, 0, 1, 97)
MODGRID_SYSEX_HEADER = (93, 93)
MIDI_NOTE_TYPE = 0
MIDI_CC_TYPE = 1
MIDI_PB_TYPE = 2
MIDI_MSG_TYPES = (MIDI_NOTE_TYPE, MIDI_CC_TYPE, MIDI_PB_TYPE)
MIDI_NOTE_ON_STATUS = 144
MIDI_NOTE_OFF_STATUS = 128
MIDI_CC_STATUS = 176
MIDI_PB_STATUS = 224

MOD_VIEWS = {'Full': 0, 
	    	'Half':1, 
			'Quarter':2,
			'Piano':3,
			'SplitPiano':4,
			'Skin':5,
			'Mira':6,
			'Tall':7,
			'Wide':8,
			'Dial':9,
			'Mixer':10,
			'Sequencer':11
			}
DEFAULT_MOD_VIEW = 0

#COLOR_MAP = [2, 64, 4, 8, 16, 127, 32]
#COLOR_MAP = [1,2,3,4,5,6,7]
COLOR_MAP = range(1, 128)
# LIVID_SYSEX_HEADER = (0, 1, 97)

def checkpad(button):
	return nameIs(button, 'Pad_112') or nameIs(button, 'Pad_48')


def nameIs(obj, name):
	return hasattr(obj, 'name') and obj.name == name

#should be called from inspected method like: caller_info(inspect.currentframe())
def caller_info(frame):
	caller_frame = frame.f_back
	try:
		caller_name = inspect.getframeinfo(caller_frame).function
		caller_context = inspect.getframeinfo(caller_frame).filename
		debug('caller:', caller_name)
		debug('filename:', caller_context)
	finally:
		del caller_frame


def xstr(s):
	if s is None:
		return ''
	else:
		return str(s)


def create_device_bank(device, banking_info):
	bank = None
	if liveobj_valid(device):
		if banking_info.has_bank_count(device):
			bank_class = MaxDeviceParameterBank
		elif banking_info.device_bank_definition(device) is not None:
			# bank_class = DescribedDeviceParameterBank
			bank_class = LargeDescribedDeviceParameterBank
		else:
			bank_class = DeviceParameterBank
		bank = bank_class(device=device, size=16, banking_info=banking_info)
	return bank


class SpecialBackgroundComponent(BackgroundComponent):
	text_data_source = DisplayDataSource(' ')

	def _reset_control(self, control):
		super(SpecialBackgroundComponent, self)._reset_control(control)
		if hasattr(control, "_display"):
			control._display.set_data_sources([self.text_data_source])


class EventMode(Mode, NotifyingControlElement):
	_send_current_color = nop
	send_value = nop
	set_light = nop


	def __init__(self, text = "", *a, **k):
		self._is_pressed = False
		super(EventMode, self).__init__(resource_type=PrioritizedResource, *a, **k)

	def reset(self):
		pass

	def is_pressed(self):
		return self._is_pressed

	def enter_mode(self):
		self._is_pressed = True
		self.notify_value(127)

	def leave_mode(self):
		self._is_pressed = False
		self.notify_value(0)

	def is_momentary(self):
		return False


class DisplayingButtonWrapper(WrapperElement):

	def __init__(self, control, text):
		self._text_data_source = DisplayDataSource(text)
		# debug("TEXT is", text)
		super(DisplayingButtonWrapper, self).__init__(wrapped_control = control)
		self.register_control_element(self.wrapped_control)

	# def set_control_element(self, control, grabbed):
	# 	super(DisplayingButtonWrapper, self).set_control_element(control, grabbed = True)
	# 	# debug('DisplayingButtonWrapper.set_control_element()', control, control.name if hasattr(control, 'name') else "NoName")
	# 	if hasattr(control, '_display'):
	# 		if(control is self.wrapped_control):
	# 			control._display.set_data_sources([self._text_data_source]) # if grabbed else None)

	def on_nested_control_element_received(self, control):
		super(DisplayingButtonWrapper, self).on_nested_control_element_received(control)
		# debug('DisplayingButtonWrapper.set_control_element()', control, control.name if hasattr(control, 'name') else "NoName")
		if hasattr(control, '_display'):
			if(control is self.wrapped_control):
				control._display.set_data_sources([self._text_data_source]) # if else None)

	# def on_nested_control_element_lost(self, control):


class MasterTrackComponent(Component):
    toggle_button = ToggleButtonControl(toggled_color = 'MasterTrack.On', untoggled_color = 'MasterTrack.Off')

    def __init__(self, tracks_provider=None, *a, **k):
        (super(MasterTrackComponent, self).__init__)(*a, **k)
        self._tracks_provider = tracks_provider
        self._MasterTrackComponent__on_selected_item_changed.subject = self._tracks_provider
        self._previous_selection = self._tracks_provider.selected_item
        self._update_button_state()

    @listens('selected_item')
    def __on_selected_item_changed(self, *a):
        self._update_button_state()
        if not self._is_on_master():
            self._previous_selection = self._tracks_provider.selected_item

    def _update_button_state(self):
        self.toggle_button.is_toggled = self._is_on_master()

    @toggle_button.toggled
    def toggle_button(self, toggled, button):
        if toggled:
            self._previous_selection = self._tracks_provider.selected_item
            self._tracks_provider.selected_item = self.song.master_track
        else:
            self._tracks_provider.selected_item = self._previous_selection
        self._update_button_state()

    def _is_on_master(self):
        return self._tracks_provider.selected_item == self.song.master_track


class DisplayingComboElement(ComboElement):

	def __init__(self, control, text, modifier):
		self._text_data_source = DisplayDataSource(text)
		super(DisplayingComboElement, self).__init__(control, modifier)

	# def set_control_element(self, control, grabbed):
	# 	super(DisplayingComboElement, self).set_control_element(control, grabbed)
	# 	if(grabbed):
	# 		if hasattr(control, '_display'):
	# 			if(control is self.wrapped_control):
	# 				control._display.set_data_sources([self._text_data_source] if grabbed else None)
	
	def on_nested_control_element_received(self, control):
		super(DisplayingComboElement, self).on_nested_control_element_received(control)
		if hasattr(control, '_display'):
			if(control is self.wrapped_control):
				control._display.set_data_sources([self._text_data_source])

	def on_nested_control_element_lost(self, control):
		super(DisplayingComboElement, self).on_nested_control_element_lost(control)
		if hasattr(control, '_display'):
			if(control is self.wrapped_control):
				control._display.set_data_sources(None)


class DisplayingButtonControl(ButtonControl):

	class State(ButtonControl.State):

		def __init__(self, text=None, *a, **k):
			self._text_data_source = DisplayDataSource(text)
			(super(DisplayingButtonControl.State, self).__init__)(*a, **k)

		def set_control_element(self, control_element):
			super(DisplayingButtonControl.State, self).set_control_element(control_element)
			if hasattr(control_element, "_display"):
				control_element._display.set_data_sources([self._text_data_source])


class DisplayingToggleButtonControl(ToggleButtonControl):

	class State(ToggleButtonControl.State):

		def __init__(self, text=None, *a, **k):
			self._text_data_source = DisplayDataSource(text)
			(super(DisplayingToggleButtonControl.State, self).__init__)(*a, **k)

		def set_control_element(self, control_element):
			super(DisplayingToggleButtonControl.State, self).set_control_element(control_element)
			if hasattr(control_element, "_display"):
				control_element._display.set_data_sources([self._text_data_source])


class ModGridFixedLengthSessionRecordingComponent(FixedLengthSessionRecordingComponent):
	# apparently toggle doesn't work with display
	automation_button = DisplayingToggleButtonControl(toggled_color='Automation.On',
	  untoggled_color='Automation.Off', text="Auto")
	re_enable_automation_button = DisplayingButtonControl(text="ReAuto", color='Automation.On')
	delete_automation_button = DisplayingButtonControl(text="DelAuto", color='Automation.Off')
	record_button = DisplayingButtonControl(text="O", color='Recording.Off')

	@record_button.pressed
	def record_button(self, button):
		self._on_record_button_pressed()

	@record_button.released
	def record_button(self, button):
		self._on_record_button_released()

	def set_scene_list_new_button(self, button):
		super(ModGridFixedLengthSessionRecordingComponent, self).set_scene_list_new_button(button)
		if hasattr(button, "_display"):
			button._display.display_message("ScnLst+")

	# def set_new_button(self, button):
	# 	super(ModGridFixedLengthSessionRecordingComponent, self).set_new_button(button)
	# 	if hasattr(button, "_display"):
	# 		button._display.display_message("New")

	def set_new_scene_button(self, button):
		super(ModGridFixedLengthSessionRecordingComponent, self).set_new_scene_button(button)
		if hasattr(button, "_display"):
			button._display.display_message("NewScn")

	@automation_button.toggled
	def automation_button(self, is_toggled, button):
		self.song.session_automation_record = is_toggled

	def _jump_to_next_slot(self, track, start_index):
		super(ModGridFixedLengthSessionRecordingComponent, self)._jump_to_next_slot(track, start_index)
		self._start_recording()


class ModGridUndoRedoComponent(UndoRedoComponent):
	undo_button = DisplayingButtonControl(text="Undo")
	redo_button = DisplayingButtonControl(text="Redo")

	@undo_button.pressed
	def undo_button(self, button):
		# debug('undo')
		self._undo()

	@redo_button.pressed
	def redo_button(self, button):
		self._redo()


class ModGridTransportComponent(TransportComponent):

	play_button = DisplayingToggleButtonControl(toggled_color='Transport.PlayOn', untoggled_color='Transport.PlayOff', text="Play", )
	stop_button = DisplayingButtonControl(text="Stop")
	continue_playing_button = DisplayingButtonControl(text="Continue")
	tap_tempo_button = DisplayingButtonControl(text="Tap", color='DefaultButton.On', pressed_color='DefaultButton.Off')

	_metro_display = DisplayDataSource('Metro')
	_overdub_display = DisplayDataSource('Overdub')
	_record_display = DisplayDataSource('Record')
	_loop_display = DisplayDataSource('Loop')

	def __init__(self, *a, **k):
		super(TransportComponent, self).__init__(*a, **k)
		# self._metronome_toggle = ToggleComponent('metronome', song, parent=self, view_transform = (lambda val :  "Transport.MetroOn" if val else "Transport.MetroOff"))

		self._ffwd_button = None
		self._rwd_button = None
		self._tap_tempo_button = None
		self._tempo_control = None
		self._tempo_fine_control = None
		self._rwd_task = task.Task()
		self._ffwd_task = task.Task()
		self._fine_tempo_needs_pickup = True
		self._prior_fine_tempo_value = -1
		self._end_undo_step_task = self._tasks.add(task.sequence(task.wait(1.5), task.run(self.song.end_undo_step)))
		self._end_undo_step_task.kill()
		song = self.song
		self._loop_toggle = ToggleComponent('loop', song, parent=self)
		self._punch_in_toggle = ToggleComponent('punch_in',
		  song, is_momentary=True, parent=self)
		self._punch_out_toggle = ToggleComponent('punch_out',
		  song, is_momentary=True, parent=self)
		self._record_toggle = ToggleComponent('record_mode', song, parent=self, view_transform = (lambda val : 'Transport.RecordOn' if val > 0 else 'Transport.RecordOff'))
		self._nudge_down_toggle = ToggleComponent('nudge_down',
		  song, is_momentary=True, parent=self)
		self._nudge_up_toggle = ToggleComponent('nudge_up',
		  song, is_momentary=True, parent=self)
		self._metronome_toggle = ToggleComponent('metronome', song, parent=self, view_transform = (lambda val : 'Transport.MetroOn' if val > 0 else 'Transport.MetroOff'))
		self._arrangement_overdub_toggle = ToggleComponent('arrangement_overdub',
		  song, parent=self)
		self._overdub_toggle = ToggleComponent('overdub', song, parent=self, view_transform = (lambda val : 'Transport.OverdubOn' if val > 0 else 'Transport.OverdubOff'))
		self._TransportComponent__on_is_playing_changed.subject = song
		self._TransportComponent__on_is_playing_changed()


	def set_metronome_button(self, button):
		super(ModGridTransportComponent, self).set_metronome_button(button)
		if hasattr(button, "_display"):
			# button._display.display_message('Metro')
			button._display.set_data_sources([self._metro_display])

	def set_overdub_button(self, button):
		super(ModGridTransportComponent, self).set_overdub_button(button)
		if hasattr(button, "_display"):
			# button._display.display_message('OvrDb')
			button._display.set_data_sources([self._overdub_display])

	def set_record_button(self, button):
		super(ModGridTransportComponent, self).set_record_button(button)
		if hasattr(button, "_display"):
			# button._display.display_message('OvrDb')
			button._display.set_data_sources([self._record_display])

	def set_loop_button(self, button):
		super(ModGridTransportComponent, self).set_loop_button(button)
		if hasattr(button, "_display"):
			# button._display.display_message('OvrDb')
			button._display.set_data_sources([self._loop_display])

	@stop_button.released
	def _on_stop_button_released(self, button):
		self.song.is_playing = False

	@play_button.toggled
	def _on_play_button_toggled(self, is_toggled, button):
		self.song.is_playing = is_toggled


class ModGridDeviceNavigationComponent(UtilDeviceNavigationComponent):

	def __init__(self, *a, **k):
		self.text_data_sources = [DisplayDataSource('') for index in range(8)]
		super(ModGridDeviceNavigationComponent, self).__init__(*a, **k)
		self._on_item_names_changed.subject = self
		self._on_item_names_changed()

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


class ModGridPhysicalDisplayElement(PhysicalDisplayElement):

	def __init__(self, *a, **k):
		super(ModGridPhysicalDisplayElement, self).__init__(*a, **k)
		self._last_sent_messages = []
		self._last_sent_message = None

	def display_message(self, message):
		if not self._block_messages:
			message = adjust_string(message, self._width)
			self._message_to_send = self._message_header + tuple(self._translate_string(message)) + self._message_tail
			self._request_send_message()

	def _send_message(self):
		if not self._block_messages:
			if self._message_to_send is None:
				self._message_to_send = self._build_message(list(map(first, self._central_resource.owners)))
			if self._message_to_send!=self._last_sent_message:
				self.send_midi(self._message_to_send)
				self._last_sent_message = self._message_to_send
				# debug('_send_message', self._last_sent_message)


class SpecialMonoButtonElement(ButtonElement):

	# def __init__(self, name='button', script=None, monobridge=None, *a, **k):
	def __init__(self, name = 'MonoButton', script = None, color_map = COLOR_MAP, monobridge = None, animation_handler = None, *a, **k):
		self._text = ''
		self._display = None
		self._script = script
		self._color_map = color_map
		self._monobridge = monobridge
		self._color = 0
		self._on_value = 127
		self._off_value = 0
		self._animation_handler = animation_handler
		super(SpecialMonoButtonElement, self).__init__(name = name, *a, **k)
		self._setup_display()

	def set_light(self, value, *a, **k):
		try:
			self._animation_handler.remove_interface(self)
		except:
			pass
		if old_hasattr(value, 'draw'):
			value.draw(self)
		elif type(value) in (int, long) and in_range(value, 0, 128):
			self.send_value(value)
		elif isinstance(value, bool):
			self._set_skin_light('DefaultButton.On' if value else 'DefaultButton.Off')
		else:
			self._set_skin_light(value)

	@listenable_property
	def text(self):
		return str(self._text)

	def set_text(self, text = ''):
		# debug('button.set_text:', text)
		# self._text = text.encode('utf-8', 'ignore')
		self._text = str(text)
		if not self._display is None:
			self._display.display_message(self._text)
		self.notify_text(self._text)

	def reset(self):
		super(SpecialMonoButtonElement, self).reset()
		# debug('resetting...')
		# self._darkened = 0
		self.force_next_send()
		self.set_light('DefaultButton.Disabled')
		self.use_default_message()
		self.script_forwarding = ScriptForwarding.exclusive
		self.reset_state()
		self._text = ''
		self.notify_text(self._text)
		self._display.display_message('')

	def _setup_display(self):
		self._display = ModGridPhysicalDisplayElement(width_in_chars = 12)
		self._display.name = self.name + 'Display'
		self._display.set_message_parts( SYSEX_HEADER + MODGRID_SYSEX_HEADER + (0, self._original_channel, self._original_identifier), (247,))
		# self._display.set_clear_all_message((176, 34, 127, 176, 35, 127))
		# self._display.set_translation_table(_base_translations)

	def flash_playhead(self, color):
		data_byte1 = self._original_identifier
		data_byte2 = color
		status_byte = self._original_channel
		status_byte += MIDI_NOTE_ON_STATUS
		self.send_midi((status_byte,
		 data_byte1,
		 data_byte2))

	def unflash_playhead(self):
		self._do_send_value(self._last_sent_message[0], self._last_sent_message[1])
		# pass

	def set_enabled(self, enabled):
		self._is_enabled = enabled
		# self.suppress_script_forwarding = not self._is_enabled
		# self.suppress_script_forwarding = self._is_enabled
		# # self.script_forwarding = ScriptForwarding(2)
		# self._request_rebuild()

	def flash(self, value, *a):
		# debug('flash:', value)
		# self._set_skin_light(value)
		if type(value) in (int, long) and in_range(value, 0, 128):
			self.send_value(value)
		elif isinstance(value, bool):
			self._set_skin_light('DefaultButton.On' if value else 'DefaultButton.Off')
		else:
			self._set_skin_light(value)

	# def unflash(self, color, *a):
	# 	# debug('unflash:', color)
	# 	self._set_skin_light(color)


class SpecialMPEMonoButtonElement(SpecialMonoButtonElement):

	MPE_CHANNEL_SPAN = 5

	def __init__(self, *a, **k):
		self._mpe_enabled = False
		self._mpe_channel_enabled = False
		super(SpecialMPEMonoButtonElement, self).__init__(*a, **k)
		self._tasks.add(task.run(self.update_mpe_enabled))

	# def set_identifier(self, identifier):
	# 	if checkpad(self):
	# 		debug('set_identifier:', self.name, identifier)
	# 		# caller_info(inspect.currentframe())
	# 	super(SpecialMPEMonoButtonElement, self).set_identifier(identifier)

	# def set_channel(self, channel):
	# 	if checkpad(self):
	# 		debug('set_channel:', self.name, channel)
	# 		caller_info(inspect.currentframe())
	# 	super(SpecialMPEMonoButtonElement, self).set_channel(channel)

	# def reset_state(self):
	# 	if checkpad(self):
	# 		debug('reset_state')
	# 	super(SpecialMPEMonoButtonElement, self).reset_state()

	def use_default_message(self):
		super(SpecialMPEMonoButtonElement, self).use_default_message()
		self.set_mpe_enabled(False)
		# self._request_rebuild()
		# if checkpad(self):
		# 	debug('use_default_message', self.name)

	def set_mpe_enabled(self, value = False):
		# if checkpad(self): 
		# 	debug('set_mpe_enabled:', value, self.name)
		if value != self._mpe_enabled:
			self._mpe_enabled = value
			self.update_mpe_enabled()
	
	def update_mpe_enabled(self):
		# if checkpad(self): 
		# 	debug('sending mpe enabled:', self._mpe_enabled, self.name)
		enabled = 1 if self._mpe_enabled else 0
		self.send_midi( SYSEX_HEADER + MODGRID_SYSEX_HEADER + tuple( (10, self._original_channel, self._original_identifier, int(enabled), 247,)))

	# def use_default_message(self, *a, **k):
	# 	debug('use_default_message', self.name)
	# 	super(SpecialMPEMonoButtonElement, self).use_default_message(*a, **k)


	def install_connections(self, install_translation, install_mapping, install_forwarding):
			# if checkpad(self):
			# 	debug('install connections:', self.name, self._msg_type, self._original_identifier, self._original_channel, self._msg_identifier, self._msg_channel)
			self._send_delayed_messages_task.kill()
			self._is_mapped = False
			self._is_being_forwarded = False

			if self._mpe_enabled is True:
				# if checkpad(self):
				# 	debug('mpe translating span:', self.name, self._msg_type, self._original_identifier, self._original_channel, self._msg_identifier, self._msg_channel)
				install_translation(self._msg_type, self._original_identifier, self._original_channel, self._msg_identifier, self._msg_channel)
				'''
				for mpe buttons, we're translating via the playable (mono-key/drumgroup) to one higher channel.
				when mpe is enabled, each button is sending two notes, one for the regular buttonn and one for the mpe voice
				this must be done so it doesn't interfere with mpe buttons that aren't being translated 
				(don't understand why, and I think its a bug, but when a button is forwarded and has also a translation, and there is another button
				with the same id, it causes that button to double-input.  If its not forwarded, of course it bleeds through to the channel)
				'''
				for channel in range(self._original_channel+2, min(15, int(self._original_channel+self.MPE_CHANNEL_SPAN)+2)):
					install_translation(self._msg_type, self._original_identifier, channel, self._msg_identifier, channel)
			elif self._msg_channel != self._original_channel or (self._msg_identifier != self._original_identifier):
				install_translation(self._msg_type, self._original_identifier, self._original_channel, self._msg_identifier, self._msg_channel)

			if liveobj_valid(self._parameter_to_map_to):
				self._is_mapped = install_mapping(self, self._parameter_to_map_to, self._mapping_feedback_delay, self._mapping_feedback_values())

			#we're overriding here, just to make sure nothing has accidentally turned off exclusive elsewhere (playable).
			#this should be fixed in the client class and removed at some point.
			if self._mpe_enabled is True:

				# if checkpad(self):
				# 	 debug('mpe enabled, forwarding exclusive:', self._original_channel, self._original_identifier, self._msg_channel, self._msg_identifier, self.name if hasattr(self, 'name') else self)
				self._is_being_forwarded = install_forwarding(self, ScriptForwarding.exclusive)
				if self.send_depends_on_forwarding:
					self._send_delayed_messages_task.restart()
				# if checkpad(self):
				# 	debug('is_being_forwarded:', self._is_being_forwarded)
			else: 
				if self.script_wants_forwarding():
					self._is_being_forwarded = install_forwarding(self, self.script_forwarding)
					if self._is_being_forwarded:
						# if checkpad(self):
						# 	debug('forwarding:', self.script_forwarding, 'name:', self.name if hasattr(self, 'name') else self)
						if self.send_depends_on_forwarding:
							self._send_delayed_messages_task.restart()
			
			#send out sysex to update the controllers mpe button on/off state
			self._tasks.add(task.run(self.update_mpe_enabled))


class SpecialMultiElement(MultiElement):

	_identifier = 0
	_enabled = True
	# _original_identifier = 0
	_name = 'specMulti'
	_channel = 0

	def __init__(self, *controls, **k):
		self._original_identifier = controls[0].original_identifier()
		(super(SpecialMultiElement, self).__init__)(*controls, **k)

	@property
	def channel(self):
		return self._channel

	@channel.setter
	def channel(self, value):
		pass

	def set_channel(self, channel):
		pass

	def original_identifier(self):
		return self._original_identifier

	@property
	def identifier(self):
		return self._identifier

	@identifier.setter
	def identifier(self, value):
		self._identifier = value
		self.update_identifier()

	def update_identifier(self):
		#this is enumerating button_elements, which do not actually contain the identifier etc....I need their linked control (button_control)
		# debug('sending id:', self._name, self._identifier)
		if len(self.owned_control_elements()):
			control = self.owned_control_elements()[0]
			# debug('control type:', type(control))
		for control in self.owned_control_elements():
			# debug('control:', control, 'original identifier:', self.identifier, 'type:', type(control))
			# control.identifier = self._identifier
			control.set_identifier(self._identifier)

	def set_identifier(self, identifier):
		# debug('set_identifier:', identifier)
		self.identifier = identifier

	@property
	def enabled(self):
		return self._enabled

	@enabled.setter
	def enabled(self, value):
		self._enabled = value
		self.update_enabled()

	def update_enabled(self):
		# debug('sending enabled:', self.enabled)
		for control in self.owned_control_elements():
			# control.enabled = self._enabled
			control.script_forwarding = ScriptForwarding.non_consuming if self._enabled else ScriptForwarding.none

	def on_nested_control_element_value(self, value, control):
		super(SpecialMultiElement, self).on_nested_control_element_value(value, control)
		#this recieves the button_element
		# debug('on_nested_control_element_value', 'type:', type(control))
		# if hasattr(control, '_control_element'):
		# debug('on_nested_control_element_value:', value, control.script_forwarding, control.message_channel(), control.message_identifier())


class SpecialEncoderElement(EncoderElement):
	"""this component is currently in a flux state.  some of the logic is for use in Commander and probably needs to be removed now 
	(_text should be replaced wholly by _internal_data_source)
	ideally this provides a way to automatically forward name/value data to its displays based on what its currently connected to. 
	should be able to be overrided explicitly by setting a different data source to its displays, but not much testing done thus far"""
	def __init__(self, *a, **k):
		self._name_text = ''
		self._value_text = ''
		self._name_display = None
		self._value_display = None
		self._internal_name_data_source = DisplayDataSource('Internal name')
		self._internal_value_data_source = DisplayDataSource('Internal value')
		super(SpecialEncoderElement, self).__init__(*a, **k)
		self._setup_displays()

	@listenable_property
	def name_text(self):
		return str(self._name_text)

	@listenable_property
	def value_text(self):
		return str(self._value_text)

	def use_internal_name_data(self, enabled=True):
		if enabled:
			self._name_display.set_data_sources([self._internal_name_data_source])
		else:
			self._name_display.set_data_sources(None)

	def use_internal_value_data(self, enabled=True):
		if enabled:
			self._value_display.set_data_sources([self._internal_value_data_source])
		else:
			self._value_display.set_data_sources(None)

	def _setup_displays(self):
		self._name_display = ModGridPhysicalDisplayElement(width_in_chars = 20)
		self._name_display.name = self.name + 'Name_Display'
		self._name_display.set_message_parts( SYSEX_HEADER + MODGRID_SYSEX_HEADER + (1, self._original_channel, self._original_identifier), (247,))
		self._value_display = ModGridPhysicalDisplayElement(width_in_chars = 20)
		self._value_display.name = self.name + 'Value_Display'
		self._value_display.set_message_parts( SYSEX_HEADER + MODGRID_SYSEX_HEADER + (2, self._original_channel, self._original_identifier), (247,))

	def reset(self):
		# super(SpecialEncoderElement, self).reset()
		# if not liveobj_valid(self._parameter_to_map_to):
			# if checkpad(self):
			# 	debug(self.name, 'reset invalid parameter', self._parameter_to_map_to)
		self.send_value(0, True)
		# else:
		# 	debug(self.name, 'is valid', self._parameter_to_map_to.name)
		self._name_text = ''
		self._value_text = ''
		self.notify_name_text(self._name_text)
		self.notify_value_text(self._value_text)
		self._internal_name_data_source.set_display_string('')
		self._internal_value_data_source.set_display_string('')

	# def reset_state(self):
	# 	super(SpecialEncoderElement, self).reset_state()
	# 	self.use_internal_name_data()
	# 	self.use_internal_value_data()

	# def install_connections(self, install_translation, install_mapping, install_forwarding):
	# 	super(SpecialEncoderElement, self).install_connections(install_translation, install_mapping, install_forwarding)


	def connect_to(self, parameter):
		if checkpad(self):
			debug('connect to', parameter, self.name, parameter.name if liveobj_valid(parameter) else 'None')
		self.remove_parameter_listener()
		self.use_internal_name_data()
		self.use_internal_value_data()
		super(SpecialEncoderElement, self).connect_to(parameter)
		self.add_parameter_listener()
		self._on_parameter_value_changed()
		self.notify_parameter_name()
		self._internal_name_data_source.set_display_string(self.parameter_name)

	#this keeps everything from hanging onto the last value when getting a non valid or None parameter
	def release_parameter(self):
		super(SpecialEncoderElement, self).release_parameter()
		self.reset()

	def add_parameter_listener(self, *a):
		# debug('add_parameter_listener', self.name)
		if liveobj_valid(self._parameter_to_map_to) and not self._parameter_to_map_to.value_has_listener(self._on_parameter_value_changed):
			self._parameter_to_map_to.add_value_listener(self._on_parameter_value_changed)
		# else:
		# 	debug('liveobj_valid:', liveobj_valid(self._parameter_to_map_to), 'has_listener:', self._parameter_to_map_to.value_has_listener(self._on_parameter_value_changed))

	def remove_parameter_listener(self, *a):
		if liveobj_valid(self._parameter_to_map_to) and self._parameter_to_map_to.value_has_listener(self._on_parameter_value_changed):
			self._parameter_to_map_to.remove_value_listener(self._on_parameter_value_changed)

	def _on_parameter_value_changed(self, *a):
		self.notify_parameter_value(self.parameter_value)
		self.notify_normalized_parameter_value(self.normalized_parameter_value)
		self._internal_value_data_source.set_display_string(self.parameter_value)

	def send_value(self, value, force=False, channel=None):
		super(SpecialEncoderElement, self).send_value(value, force, channel)
		if checkpad(self):
			debug('send_value:', value, force, channel)

	@listenable_property
	def parameter_name(self):
		parameter = self._parameter_to_map_to
		if liveobj_valid(parameter):
			try:
				name = str(parameter.name)
				return name
			except:
				return ''
		return ''

	@listenable_property
	def parameter_value(self):
		parameter = self._parameter_to_map_to
		if liveobj_valid(parameter):
			try:
				value = str(parameter.str_for_value(parameter.value))
				return value
			except:
				return ''
		return ''

	@listenable_property
	def normalized_parameter_value(self):
		parameter = self._parameter_to_map_to
		if liveobj_valid(parameter):
			value = int(((parameter.value - parameter.min) / (parameter.max - parameter.min))  * 127)
			return value
		return ''

	def set_normalized_value(self, value):
		parameter = self._parameter_to_map_to
		if liveobj_valid(parameter):
			newval = float(float(float(value)/127) * float(parameter.max - parameter.min)) + parameter.min
			parameter.value = newval
		else:
			self.receive_value(value)

	def set_value(self, value):
		parameter = self._parameter_to_map_to
		if liveobj_valid(parameter):
			newval = float(value * (parameter.max - parameter.min)) + parameter.min
			parameter.value = newval
		else:
			self.receive_value(int(value*127))


class LargeDescribedDeviceParameterBank(DescribedDeviceParameterBankWithOptions):

	def _current_parameter_slots(self):
		if self.bank_count() > self.index+1:
			return self._definition.value_by_index(self.index).get(BANK_PARAMETERS_KEY)+self._definition.value_by_index(self.index+1).get(BANK_PARAMETERS_KEY) or tuple()
		else:
			return self._definition.value_by_index(self.index).get(BANK_PARAMETERS_KEY) or tuple()


class MaxParameterProxy(Component):

	def __init__(self, *a, **k):
		self._parameter = None
		super(MaxParameterProxy, self).__init__(*a, **k)

	def set_parameter(self, parameter):
		if parameter != self._parameter:
			if not self._parameter == None and self._parameter.value_has_listener(self._on_parameter_value_changed):
				self._parameter.remove_value_listener(self._on_parameter_value_changed)
			self._parameter = parameter
			if not self._parameter == None:
				self._parameter.add_value_listener(self._on_parameter_value_changed)
			self._on_parameter_value_changed()

	def _on_parameter_value_changed(self, *a):
		parameter = self._parameter
		# debug('parameter_value_changed:', parameter)
		if liveobj_valid(parameter):
			# value = int(parameter.value * 127)
			value = int(self.normalized_value)
			self.notify_parameter_value(parameter)
			self.notify_normalized_value(value)

	def set_value(self, value):
		parameter = self._parameter
		if liveobj_valid(parameter):
			parameter.value = float(float(float(value)/127) * float(parameter.max - parameter.min)) + parameter.min

	@listenable_property
	def parameter_value(self):
		parameter = self._parameter
		if liveobj_valid(parameter):
			value = parameter
			return value

	@listenable_property
	def normalized_value(self):
		parameter = self._parameter
		if liveobj_valid(parameter):
			value = ((parameter.value - parameter.min) / (parameter.max - parameter.min))  * 127
			return value


class UtilDeviceParameterComponent(DisplayingDeviceParameterComponent):
	controls = ControlList(MappedSensitivitySettingControl, 16)

	def __init__(self, *a, **k):
		self.parameter_proxies = [MaxParameterProxy(name = 'ParameterProxy_'+str(index)) for index in range(16)]
		super(UtilDeviceParameterComponent, self).__init__(*a, **k)
		self._parameter_name_data_sources = list(map(DisplayDataSource, ('', '', '', '', '', '', '', '','', '', '', '', '', '', '', '')))
		self._parameter_value_data_sources = list(map(DisplayDataSource, ('', '', '', '', '', '', '', '','', '', '', '', '', '', '', '')))

	def get_parameter_proxy(self, index):
		return self.parameter_proxies[index] if index < len(self.parameter_proxies) else None

	@listenable_property
	def current_parameters(self):
		return [p and hasattr(p.parameter, 'str_for_value') and str(p.parameter.str_for_value(p.parameter.value)).replace(' ', '_') or '---' for p in self._parameter_provider.parameters]

	@listenable_property
	def current_parameter_names(self):
		return [p and p.name.replace(' ', '_') or '---' for p in self.parameters]

	def _update_parameter_names(self):
		#debug('_update_parameter_names')
		super(UtilDeviceParameterComponent, self)._update_parameter_names()
		if self.is_enabled():
			names = self.current_parameter_names
			self.notify_current_parameter_names(*names)

	def _update_parameter_values(self):
		#debug('_update_parameter_values')
		super(UtilDeviceParameterComponent, self)._update_parameter_values()
		if self.is_enabled():
			values = self.current_parameters
			self.notify_current_parameters(*values)

	def _connect_parameters(self):
		super(UtilDeviceParameterComponent, self)._connect_parameters()
		parameters = self._parameter_provider.parameters[:16]
		# debug('parameters are:', parameters)
		for proxy, parameter_info in zip(self.parameter_proxies, parameters):
			# debug('here')
			parameter = parameter_info.parameter if parameter_info else None
			# debug('proxy:', proxy, 'parameter:', parameter)
			if proxy:
				proxy.set_parameter(parameter)


class UtilDeviceComponent(DeviceComponent):

	bank_up_button = DisplayingButtonControl(text='BankUp')
	bank_down_button = DisplayingButtonControl(text='BankDn')

	@bank_up_button.pressed
	def bank_up_button(self, button):
		self._on_bank_up_button_pressed(button)

	def _on_bank_up_button_pressed(self, button):
		self.bank_up()

	def bank_up(self):
		#debug('bank_up')
		self._device_bank_registry.set_device_bank(self._bank._device, min(self._bank.index + 1, self._bank.bank_count()))

	@bank_down_button.pressed
	def bank_down_button(self, button):
		self._on_bank_down_button_pressed(button)

	def _on_bank_down_button_pressed(self, button):
		self.bank_down()

	def bank_down(self):
		#debug('bank_down')
		self._device_bank_registry.set_device_bank(self._bank._device, max(0, self._bank.index - 1))

	def _create_parameter_info(self, parameter, name):
		device_class_name = self.device().class_name
		return ParameterInfo(parameter=parameter, name=name, default_encoder_sensitivity=parameter_mapping_sensitivity(parameter, device_class_name), fine_grain_encoder_sensitivity=fine_grain_parameter_mapping_sensitivity(parameter, device_class_name))

	def _setup_bank(self, device, bank_factory = create_device_bank):
		if self._bank is not None:
			self.disconnect_disconnectable(self._bank)
			self._bank = None
		if liveobj_valid(device):
			self._bank = self.register_disconnectable(bank_factory(device, self._banking_info))

	@listenable_property
	def options(self):
		return getattr(self._bank, 'options', [None] * 7)

	@property
	def bank_view_description(self):
		return getattr(self._bank, 'bank_view_description', '')

	@listenable_property
	def device_name(self):
		device = self.device()
		name = str(device.name).replace(' ', '_') if liveobj_valid(device) and hasattr(device, 'name') else '-'
		return name

	def _on_device_changed(self, device):
		super(UtilDeviceComponent, self)._on_device_changed(device)
		self.notify_device_name(self.device_name)


class TrackCreatorComponent(Component):

	create_audio_track_button = DisplayingButtonControl(text = 'Create Audio')
	create_midi_track_button = DisplayingButtonControl(text = 'Create MIDI')

	def __init__(self, *a, **k):
		super(TrackCreatorComponent, self).__init__(*a, **k)

	@create_audio_track_button.pressed
	def create_audio_track_button(self, button):
		self._on_create_audio_track_button_pressed(button)

	def _on_create_audio_track_button_pressed(self, button):
		self.create_audio_track()

	def create_audio_track(self):
		self.song.create_audio_track()

	@create_midi_track_button.pressed
	def create_midi_track_button(self, button):
		self._on_create_midi_track_button_pressed(button)

	def _on_create_midi_track_button_pressed(self, button):
		self.create_midi_track()

	def create_midi_track(self):
		self.song.create_midi_track()


class UtilAutoArmComponent(AutoArmComponent):

	util_autoarm_toggle_button = DisplayingButtonControl(text='AutoArm')
	__autoarm_enabled = True

	def __init__(self, *a, **k):
		# self._keysplitter_disable_autoarm = False
		super(UtilAutoArmComponent, self).__init__(*a, **k)
		self._update_autoarm_toggle_button.subject = self
		self._update_autoarm_toggle_button()

	def set_util_autoarm_toggle_button(self, button):
		self.util_autoarm_toggle_button.set_control_element(button)
		# if hasattr(button, "_display"):
		# 	button._display.display_message('Autoarm+/-')

	@util_autoarm_toggle_button.pressed
	def util_autoarm_toggle_button(self, button):
		self._on_util_autoarm_toggle_button_pressed(button)

	def _on_util_autoarm_toggle_button_pressed(self, button):
		self.toggle_autoarm()

	def toggle_autoarm(self):
		self.__autoarm_enabled = not self.__autoarm_enabled
		#debug('toggle_autoarm')
		self.notify_autoarm_enabled()
		self.update()

	@listenable_property
	def autoarm_enabled(self):
		return self.__autoarm_enabled

	def can_auto_arm_track(self, track):
		# if self._keysplitter_disable_autoarm:
		# 	return False
		# else:
		return self.track_can_be_armed(track) and self.autoarm_enabled

	@listens('autoarm_enabled')
	def _update_autoarm_toggle_button(self, *a):
		#debug('_update_autoarm_toggle_button')
		self.util_autoarm_toggle_button.color = 'Auto_Arm.Enabled' if self.autoarm_enabled else 'Auto_Arm.Disabled'

	# def update(self):
	# 	if not self._keysplitter_disable_autoarm:
	# 		super(UtilAutoArmComponent, self).update()
	# 	else:
	# 		debug('autoarm.update(), keysplitter disabled')


class UtilChannelStripComponent(MonoChannelStripComponent):

	util_mute_exclusive_button = DisplayingButtonControl(text='Mute*')
	util_solo_exclusive_button = DisplayingButtonControl(text='Solo*')
	util_arm_exclusive_button = DisplayingButtonControl(text='Arm*')

	def __init__(self, *a, **k):
		self._volume_name_data_source = DisplayDataSource('Volume')
		self._pan_name_data_source = DisplayDataSource('Pan')
		self._send_name_data_source = DisplayDataSource('Send*')

		super(UtilChannelStripComponent, self).__init__(*a, **k)


	def get_tracks(self):
		tracks = [track for track in self.song.tracks]
		for track in self.song.return_tracks:
			tracks.append(track)
		return tracks

	def set_track(self, track):
		# assert(isinstance(track, (type(None), Live.Track.Track)))
		self._on_devices_changed.subject = track
		self.__on_playing_slot_index_changed.subject = track
		self._update_device_selection()
		self._detect_eq(track)
		self._update_playing_clip()
		super(MonoChannelStripComponent,self).set_track(track)

	@listens('playing_slot_index')
	def __on_playing_slot_index_changed(self):
		# debug('channelstrip.__on_playing_slot_index_changed')
		self._update_playing_clip()

	def set_mute_button(self, button):
		super(UtilChannelStripComponent, self).set_mute_button(button)
		if hasattr(button, "_display"):
			button._display.display_message('Mute')

	def set_solo_button(self, button):
		super(UtilChannelStripComponent, self).set_solo_button(button)
		if hasattr(button, "_display"):
			button._display.display_message('Solo')

	def set_arm_button(self, button):
		super(UtilChannelStripComponent, self).set_arm_button(button)
		if hasattr(button, "_display"):
			button._display.display_message('Arm')

	def set_util_mute_exclusive_button(self, button):
		self.util_mute_exclusive_button.set_control_element(button)
		# button._display.display_message('MuteExcl')

	@util_mute_exclusive_button.pressed
	def util_mute_exclusive_button(self, button):
		self._on_util_mute_exclusive_button_pressed(button)

	def _on_util_mute_exclusive_button_pressed(self, button):
		self.mute_exclusive()

	def mute_exclusive(self):
		if(self._track.mute is True):
			self._track.mute = False
		else:
			self._track.mute = True
			for t in self.get_tracks():
				if not t == self._track:
					t.mute = False


	def set_util_solo_exclusive_button(self, button):
		self.util_solo_exclusive_button.set_control_element(button)
		# button._display.display_message('SoloExcl')

	@util_solo_exclusive_button.pressed
	def util_solo_exclusive_button(self, button):
		self._on_util_solo_exclusive_button_pressed(button)

	def _on_util_solo_exclusive_button_pressed(self, button):
		self.solo_exclusive()

	def solo_exclusive(self):
		if(self._track.solo is True):
			self._track.solo = False
		else:
			self._track.solo = True
			for t in self.get_tracks():
				if not t == self._track:
					t.solo = False


	def set_util_arm_exclusive_button(self, button):
		self.util_arm_exclusive_button.set_control_element(button)
		# button._display.display_message('ArmExcl')

	@util_arm_exclusive_button.pressed
	def util_arm_exclusive_button(self, button):
		self._on_util_arm_exclusive_button_pressed(button)

	def _on_util_arm_exclusive_button_pressed(self, button):
		self.arm_exclusive()

	def arm_exclusive(self):
		if liveobj_valid(self._track) and self._track.can_be_armed:
			if(self._track.arm is True):
				self._track.arm = False
			else:
				self._track.arm = True
				for t in self.get_tracks():
					if not t == self._track:
						if liveobj_valid(t) and t.can_be_armed:
							t.arm = False


class SendScrollComponent(ScrollComponent):

	def __init__(self, mixer = None, *a, **k):
		assert not mixer is None
		self._mixer = mixer
		super(SendScrollComponent, self).__init__(*a, **k)

	def can_scroll_up(self):
		return self._mixer.send_index < (self._mixer.num_sends-1)
	
	def can_scroll_down(self):
		return self._mixer.send_index > 0
	
	def scroll_up(self):
		self._mixer.send_index = self._mixer.send_index + 1

	def scroll_down(self):
		self._mixer.send_index = self._mixer.send_index - 1


class UtilRightAlignTracksTrackAssigner(TrackAssigner):

	def __init__(self, song=None, include_master_track=False, *a, **k):
		(super(UtilRightAlignTracksTrackAssigner, self).__init__)(*a, **k)
		self._song = song
		self._include_master_track = include_master_track

	def tracks(self, tracks_provider):
		offset = tracks_provider.track_offset
		tracks = tracks_provider.tracks_to_use()
		tracks_to_right_align = list(self._song.return_tracks) + ([self._song.master_track] if self._include_master_track else [])
		size = tracks_provider.num_tracks
		right_size = len(tracks_to_right_align)
		num_empty_tracks = max(0, size + offset - len(tracks))
		track_list = size * [None]
		for i in range(size):
			track_index = i + offset
			if len(tracks) > track_index:
				track = tracks[track_index]
				empty_offset = 0 if tracks[track_index] not in tracks_to_right_align else num_empty_tracks
				track_list[i + empty_offset] = track

		return track_list


class UtilSimpleTrackAssigner(TrackAssigner):

	def tracks(self, tracks_provider):
		debug('_________________________________________________________assigning tracks')
		tracks = list(tracks_provider.controlled_tracks())
		if len(tracks) < tracks_provider.num_tracks:
			num_empty_track_slots = tracks_provider.num_tracks - len(tracks)
			tracks += [None] * num_empty_track_slots
		return tracks


class UtilMixerComponent(MonoMixerComponent):

	util_mute_kill_button = DisplayingButtonControl(text='MuteX')
	util_solo_kill_button = DisplayingButtonControl(text='SoloX')
	util_arm_kill_button = DisplayingButtonControl(text='ArmX')
	util_mute_flip_button = DisplayingButtonControl(text='Mute@')
	util_select_first_armed_track_button = DisplayingButtonControl(text='Sel1st*')
	util_lower_all_track_volumes_button = DisplayingButtonControl(text='VolsX')

	def __init__(self, *a, **k):
		self._send_control_name_dipslays = None
		self._send_control_value_displays = None
		super(UtilMixerComponent, self).__init__(*a, **k)
		self.send_navigation = SendScrollComponent(mixer=self)

	def set_send_controls(self, controls):
		debug('set_send_controls', controls)
		MixerComponent.set_send_controls(self, controls)

	def _reassign_tracks(self):
		super(UtilMixerComponent, self)._reassign_tracks()
		names = self.track_names
		self.notify_track_names(*names)

	def set_volume_control_name_displays(self, displays):
		for strip, display in zip_longest(self._channel_strips, displays or []):
			strip.set_volume_control_name_display(display)

	def set_volume_control_name_displays(self, displays):
		for strip, display in zip_longest(self._channel_strips, displays or []):
			strip.set_volume_control_name_display(display)

	def set_pan_control_name_displays(self, displays):
		for strip, display in zip_longest(self._channel_strips, displays or []):
			strip.set_pan_control_name_display(display)

	def set_pan_control_value_displays(self, displays):
		for strip, display in zip_longest(self._channel_strips, displays or []):
			strip.set_pan_control_value_display(display)

	# def set_send_control_name_displays(self, displays):
	# 	self._send_control_name_displays = displays
	# 	for strip, display in zip_longest(self._channel_strips, displays or []):
	# 		if self._send_index is None:
	# 			strip.set_send_control_name_display(None)
	# 		else:
	# 			strip.set_send_control_name_display(None, ) * self._send_index + (display,))

	# def set_send_control_value_displays(self, displays):
	# 	self._send_control_value_displays = displays
	# 	for strip, display in zip_longest(self._channel_strips, displays or []):
	# 		if self._send_index is None:
	# 			strip.set_send_control_value_display(None)
	# 		else:
	# 			strip.set_send_control_value_display(None, ) * self._send_index + (display,))

	# def set_arm_buttons(self, buttons):
	# 	for strip, button in zip_longest(self._channel_strips, buttons or []):
	# 		strip.set_arm_button(button)

	# def set_solo_buttons(self, buttons):
	# 	for strip, button in zip_longest(self._channel_strips, buttons or []):
	# 		strip.set_solo_button(button)

	# def set_mute_buttons(self, buttons):
	# 	for strip, button in zip_longest(self._channel_strips, buttons or []):
	# 		strip.set_mute_button(button)

	# def set_track_select_buttons(self, buttons):
	# 	for strip, button in zip_longest(self._channel_strips, buttons or []):
	# 		strip.set_select_button(button)


	@listenable_property
	def track_names(self):
		names = []
		for strip in self._channel_strips:
			if liveobj_valid(strip._track) and hasattr(strip._track, 'name'):
				try:
					names.append(str(strip._track.name).replace(' ', '_'))
				except:
					names.append('-')
			else:
				names.append('-')
		return names

	def get_tracks(self):
		tracks = [track for track in self.song.tracks]
		for track in self.song.return_tracks:
			tracks.append(track)
		return tracks

	def armed_tracks(self):
		tracks = []
		for t in self.get_tracks():
			if liveobj_valid(t) and t.can_be_armed:
				if t.arm:
					tracks.append(t)
		return tracks

	def set_arming_track_select_buttons(self, buttons):
		super(UtilMixerComponent, self).set_arming_track_select_buttons(buttons)
		# for button in buttons:
		# 	if hasattr(button, '_display'):
		# 		button._display.set_data_source(self.track_names)
		for strip, button in zip_longest(self._channel_strips, buttons or []):
			if hasattr(button, "_display"):
				button._display.set_data_sources([strip.track_name_data_source()])

	def set_util_select_first_armed_track_button(self, button):
		self.util_select_first_armed_track_button.set_control_element(button)

	@util_select_first_armed_track_button.pressed
	def util_select_first_armed_track_button(self, button):
		self._on_util_select_first_armed_track_button_pressed(button)

	def _on_util_select_first_armed_track_button_pressed(self, button):
		self.select_first_armed_track()

	def select_first_armed_track(self):
		# debug('select_first_armed_track')
		armed_tracks = self.armed_tracks()
		if len(armed_tracks):
			self.song.view.selected_track = armed_tracks[0]


	def set_util_mute_kill_button(self, button):
		# debug('set_util_mute_kill_button', button)
		self.util_mute_kill_button.set_control_element(button)
		# button._display.display_message('MuteX')


	@util_mute_kill_button.pressed
	def util_mute_kill_button(self, button):
		self._on_util_mute_kill_button_pressed(button)

	def _on_util_mute_kill_button_pressed(self, button):
		self.mute_kill()

	def mute_kill(self):
		for t in self.get_tracks():
			t.mute = False


	def set_util_mute_flip_button(self, button):
		self.util_mute_flip_button.set_control_element(button)
		# button._display.display_message('MuteFlip')

	@util_mute_flip_button.pressed
	def util_mute_flip_button(self, button):
		self._on_util_mute_flip_button_pressed(button)

	@util_mute_flip_button.pressed
	def util_mute_flip_button(self, button):
		self._on_util_mute_flip_button_pressed(button)

	def _on_util_mute_flip_button_pressed(self, button):
		self.mute_flip()

	def mute_flip(self):
		for t in self.get_tracks():
			t.mute = not t.mute


	def set_util_solo_kill_button(self, button):
		self.util_solo_kill_button.set_control_element(button)
		# button._display.display_message('SoloX')

	@util_solo_kill_button.pressed
	def util_solo_kill_button(self, button):
		self._on_util_solo_kill_button_pressed(button)

	def _on_util_solo_kill_button_pressed(self, button):
		self.solo_kill()

	def solo_kill(self):
		for t in self.get_tracks():
			t.solo = False


	def set_util_arm_kill_button(self, button):
		self.util_arm_kill_button.set_control_element(button)
		# button._display.display_message('ArmX')

	@util_arm_kill_button.pressed
	def util_arm_kill_button(self, button):
		self._on_util_arm_kill_button_pressed(button)

	def _on_util_arm_kill_button_pressed(self, button):
		self.arm_kill()

	def arm_kill(self):
		for t in self.get_tracks():
			if liveobj_valid(t) and t.can_be_armed:
				t.arm = False

	def set_util_lower_all_track_volumes_button(self, button):
		self.util_lower_all_track_volumes_button.set_control_element(button)
		# button._display.display_message('LowerAll')

	@util_lower_all_track_volumes_button.pressed
	def util_lower_all_track_volumes_button(self, button):
		self._on_util_lower_all_track_volumes_button_pressed(button)

	def _on_util_lower_all_track_volumes_button_pressed(self, button):
		self.lower_all_track_volumes()

	def lower_all_track_volumes(self):
		# debug('lower_all_track_volumes')
		for t in self.get_tracks():
			if liveobj_valid(t) and t.has_audio_output:
				t.mixer_device.volume.value = t.mixer_device.volume.value*.95


class UtilSessionComponent(SessionComponent):
	# managed_select_button = DisplayingButtonControl(text="Se", color='Session.Select',
	#   pressed_color='Session.SelectPressed')
	managed_duplicate_button = DisplayingButtonControl(text="Duplicate", color='Session.Duplicate', pressed_color='Session.DuplicatePressed')
	managed_delete_button = DisplayingButtonControl(text="Delete", color='Session.Delete', pressed_color='Session.DeletePressed')

	clip_stop_buttons = control_list(DisplayingButtonControl)

	util_capture_new_scene_button = DisplayingButtonControl(text='ScnCapture')
	util_fire_next_button = DisplayingButtonControl(text='FireNext')
	util_fire_prev_button = DisplayingButtonControl(text='FirePrev')
	util_fire_next_absolute_button = DisplayingButtonControl(text='FireNEXT')
	util_fire_prev_absolute_button = DisplayingButtonControl(text='FirePREV')
	util_fire_next_on_single_armed_button = DisplayingButtonControl(text='FireNxtSngl', color = "Session.FireNextArm")

	util_fire_next_on_all_armed_button = DisplayingButtonControl(text='FireNxtAll*')
	util_select_playing_clipslot_button = DisplayingButtonControl(text='Slct>Slot')
	util_stop_clip_button = DisplayingButtonControl(text='ClipX')
	util_new_scene_button = DisplayingButtonControl(text='Scene+')
	util_select_playing_on_single_armed_button = DisplayingButtonControl(text='Slct>Armed')


	def __init__(self, *a, **k):
		super(UtilSessionComponent, self).__init__(*a, **k)

	def get_tracks(self):
		return [track for track in self.song.tracks]

	def set_stop_all_clips_button(self, button):
		super(UtilSessionComponent, self).set_stop_all_clips_button(button)
		if hasattr(button, "_display"):
			button._display.display_message('StopAll')

	def set_util_capture_new_scene_button(self, button):
		self.util_capture_new_scene_button.set_control_element(button)
		# button._display.display_message('Capture')

	@util_capture_new_scene_button.pressed
	def util_capture_new_scene_button(self, button):
		self._on_util_capture_new_scene_button_pressed(button)

	def _on_util_capture_new_scene_button_pressed(self, button=None):
		if self.is_enabled() and self._prepare_new_action():
			song = self.song
			view = song.view
			try:
				if liveobj_valid(view.highlighted_clip_slot.clip):
					song.capture_and_insert_scene(Live.Song.CaptureMode.all)
			except Live.Base.LimitationError:
				pass

	def _prepare_new_action(self):
		song = self.song
		selected_track = song.view.selected_track
		if selected_track.can_be_armed:
			song.overdub = False
			return True


	def set_util_stop_clip_button(self, button):
		self.util_stop_clip_button.set_control_element(button)
		# button._display.display_message('StopClip')

	@util_stop_clip_button.pressed
	def util_stop_clip_button(self, button):
		self._on_util_stop_clip_button_pressed(button)

	def _on_util_stop_clip_button_pressed(self, button):
		self.stop_selected_track()

	def stop_selected_track(self):
		# debug('stop_selected_track')
		self.song.view.selected_track.stop_all_clips()


	def set_util_fire_next_button(self, button):
		self.util_fire_next_button.set_control_element(button)
		# button._display.display_message('FireNext')

	@util_fire_next_button.pressed
	def util_fire_next_button(self, button):
		self._on_util_fire_next_button_pressed(button)

	def _on_util_fire_next_button_pressed(self, button):
		self.fire_next_available_clip_slot()


	def set_util_fire_prev_button(self, button):
		self.util_fire_prev_button.set_control_element(button)
		# button._display.display_message('FirePrev')

	@util_fire_prev_button.pressed
	def util_fire_prev_button(self, button):
		self._on_util_fire_prev_button_pressed(button)

	def _on_util_fire_prev_button_pressed(self, button):
		self.fire_previous_available_clip_slot()


	def set_util_fire_next_absolute_button(self, button):
		self.util_fire_next_absolute_button.set_control_element(button)
		# button._display.display_message('FireNext*')

	@util_fire_next_absolute_button.pressed
	def util_fire_next_absolute_button(self, button):
		self._on_util_fire_next_absolute_button_pressed(button)

	def _on_util_fire_next_absolute_button_pressed(self, button):
		self.fire_next_clip_slot()


	def set_util_fire_prev_absolute_button(self, button):
		self.util_fire_prev_absolute_button.set_control_element(button)
		# button._display.display_message('FirePrev*')

	@util_fire_prev_absolute_button.pressed
	def util_fire_prev_absolute_button(self, button):
		self._on_util_fire_prev_absolute_button_pressed(button)

	def _on_util_fire_prev_absolute_button_pressed(self, button):
		self.fire_previous_clip_slot()


	def set_util_fire_next_on_single_armed_button(self, button):
		self.util_fire_next_on_single_armed_button.set_control_element(button)
		# button._display.display_message('NextSingle')


	@util_fire_next_on_single_armed_button.pressed
	def util_fire_next_on_single_armed_button(self, button):
		self._on_util_fire_next_on_single_armed_button_pressed(button)

	def _on_util_fire_next_on_single_armed_button_pressed(self, button):
		self.fire_next_available_clip_slot_on_single_armed_track()


	def set_util_select_playing_on_single_armed_button(self, button):
		self.util_select_playing_on_single_armed_button.set_control_element(button)
		# button._display.display_message('SelectSingle')

	@util_select_playing_on_single_armed_button.pressed
	def util_select_playing_on_single_armed_button(self, button):
		self._on_util_select_playing_on_single_armed_button_pressed(button)

	def _on_util_select_playing_on_single_armed_button_pressed(self, button):
		self.select_playing_clip_slot_on_single_armed_track()


	def set_util_fire_next_on_all_armed_button(self, button):
		self.util_fire_next_on_all_armed_button.set_control_element(button)
		# button._display.display_message('FireAllArmed')

	@util_fire_next_on_all_armed_button.pressed
	def util_fire_next_on_all_armed_button(self, button):
		self._on_util_fire_next_on_all_armed_button_pressed(button)

	def _on_util_fire_next_on_all_armed_button_pressed(self, button):
		self.fire_next_available_clip_slot_on_all_armed_tracks()


	def get_first_available_clip(self, track):
		clip_slots = track.clip_slots
		for slot in clip_slots:
			if slot.has_clip:
				return slot
		return None


	def get_first_empty_clipslot(self, track):
		clip_slots = track.clip_slots
		for slot in clip_slots:
			if not slot.has_clip:
				return slot
		return None


	def get_clip_slot_by_delta_bool(self, current_clip_slot, track, d_value, bool_callable):
		clip_slots = track.clip_slots
		max_clip_slots = len(clip_slots)

		found = False
		if d_value > 0:
			the_range = list(range(max_clip_slots))
		else:
			the_range = list(range(max_clip_slots-1, -1, -1))

		for i in the_range:
			clip_slot = clip_slots[i]
			if found and bool_callable(clip_slot):
				return clip_slot

			if clip_slot == current_clip_slot:
				found = True


	def fire_clip_slot_by_delta(self, d_value, available=False, create=False):
		current_clip_slot = self.song.view.highlighted_clip_slot
		track = self.song.view.selected_track
		if d_value is 1 and create is True:
			clip_slots = track.clip_slots
			if clip_slots[-1] == current_clip_slot:
				# self._on_util_capture_new_scene_button_pressed()
				# debug('creating new scene...')
				self.song.create_scene(-1)

		if available:
			if track.arm:
				clip_slot = self.get_clip_slot_by_delta_bool(current_clip_slot, track, d_value, lambda x: x.has_stop_button and not x.has_clip)
			else:
				clip_slot = self.get_clip_slot_by_delta_bool(current_clip_slot, track, d_value, lambda x: x.has_clip)
		else:
			clip_slot = self.get_clip_slot_by_delta_bool(current_clip_slot, track, d_value, lambda x: True)

		if clip_slot:
			clip_slot.fire()
			self.song.view.highlighted_clip_slot = clip_slot


	def fire_clip_slot_by_delta_with_explicit_track(self, d_value, track, available=False, create=False, select=False):
		current_scene = self.song.view.selected_scene
		scenes = list(self.song.scenes)
		current_scene_index = scenes.index(current_scene)
		current_clip_slot = track.clip_slots[current_scene_index]
		if d_value is 1 and create is True:
			clip_slots = track.clip_slots
			if clip_slots[-1] == current_clip_slot:
				self.song.create_scene(-1)

		if available:
			if track.arm:
				clip_slot = self.get_clip_slot_by_delta_bool(current_clip_slot, track, d_value, lambda x: x.has_stop_button and not x.has_clip)
			else:
				clip_slot = self.get_clip_slot_by_delta_bool(current_clip_slot, track, d_value, lambda x: x.has_clip)
		else:
			clip_slot = self.get_clip_slot_by_delta_bool(current_clip_slot, track, d_value, lambda x: True)

		if clip_slot:
			clip_slot.fire()
			if select:
				self.song.view.highlighted_clip_slot = clip_slot


	def fire_next_clip_slot(self):
		# debug('fire_next_clip_slot')
		self.fire_clip_slot_by_delta(1, available=False)


	def fire_next_available_clip_slot(self):
		# debug('fire_next_available_clip_slot')
		self.fire_clip_slot_by_delta(1, available=True, create=True)


	def fire_previous_clip_slot(self):
		# debug('fire_previous_clip_slot')
		self.fire_clip_slot_by_delta(-1, available=False)


	def fire_previous_available_clip_slot(self):
		# debug('fire_previous_available_clip_slot')
		self.fire_clip_slot_by_delta(-1, available=True)


	def _fire_next_available_clip_slot_on_single_armed_track(self):
		# debug('fire_next_available_clip_slot_on_single_armed_track')
		tracks = self.get_tracks()
		armed_tracks = self.armed_tracks()
		selected_track = self.song.view.selected_track
		if selected_track in armed_tracks:
			self.fire_clip_slot_by_delta(1, available=True, create=True)
		else:
			selected_index = tracks.index(selected_track) if selected_track in tracks else 0
			# debug('selected_index:', selected_index)
			if len(tracks) > selected_index:
				for track in tracks[selected_index:]:
					if track.can_be_armed and track.arm is True:
						self.fire_clip_slot_by_delta_with_explicit_track(d_value=1, track=track, available=True, create=True, select=True)
						break

		#fire_first_available_clip_slot_on_single_armed_track


	def fire_next_available_clip_slot_on_single_armed_track(self):
		tracks = self.get_tracks()
		armed_tracks = self.armed_tracks()
		selected_track = self.song.view.selected_track
		if selected_track in armed_tracks:
			clip_slot = self.get_first_empty_clipslot(selected_track)
			if clip_slot:
				clip_slot.fire()
				self.song.view.highlighted_clip_slot = clip_slot
			else:
				self.fire_next_available_clip_slot()

		else:
			selected_index = tracks.index(selected_track) if selected_track in tracks else 0
			if len(tracks) > selected_index:
				for track in tracks[selected_index:]:
					if track.can_be_armed and track.arm is True:
						clip_slot = self.get_first_empty_clipslot(track)
						if clip_slot:
							clip_slot.fire()
							self.song.view.highlighted_clip_slot = clip_slot
						else:
							self.fire_clip_slot_by_delta_with_explicit_track(d_value=1, track=track, available=True, create=True, select=True)
						break


	def fire_next_available_clip_slot_on_all_armed_tracks(self):
		# debug('fire_next_available_clip_slot_on_all_armed_tracks')
		armed_tracks = self.armed_tracks()
		# debug('armed_tracks:', len(armed_tracks))
		for track in armed_tracks:
			clip_slot = self.get_first_empty_clipslot(track)
			if clip_slot:
				clip_slot.fire()
				#self.song.view.highlighted_clip_slot = clip_slot
			else:
				self.fire_clip_slot_by_delta_with_explicit_track(d_value=1, track=track, available=True, create=False)


	def select_playing_clip_slot_on_single_armed_track(self):
		# debug('select_playing_clip_slot_on_single_armed_track')

		tracks = list(self.get_tracks())
		armed_tracks = list(self.armed_tracks())
		selected_track = self.song.view.selected_track
		track =  None
		if selected_track in armed_tracks:
			# debug('selected_track in armed_tracks')
			track = selected_track
		elif len(armed_tracks) > 0:
			# debug('len(armed_tracks)>0')
			track = armed_tracks[0]
		else:
			# debug('no armed tracks')
			track = selected_track
		if liveobj_valid(track):
			last_clip = None
			for clip_slot in track.clip_slots:
				if clip_slot.has_clip:
					if clip_slot.clip.is_playing:
						last_clip = None
						self.song.view.highlighted_clip_slot = clip_slot
						break
					else:
						# debug('adding last clip:', clip_slot.has_clip)
						last_clip = clip_slot
			if liveobj_valid(last_clip):
				self.song.view.highlighted_clip_slot = last_clip


	def set_util_select_playing_clipslot_button(self, button):
		self.util_select_playing_clipslot_button.set_control_element(button)
		# button._display.display_message('SelPlaying')


	@util_select_playing_clipslot_button.pressed
	def util_select_playing_clipslot_button(self, button):
		self._on_util_select_playing_clipslot_button_pressed(button)


	def _on_util_select_playing_clipslot_button_pressed(self, button):
		self.select_playing_clip()


	def select_playing_clip(self):
		# debug('select_playing_clip')
		for clip_slot in self.song.view.selected_track.clip_slots:
			if clip_slot.has_clip and clip_slot.clip.is_playing:
				self.song.view.highlighted_clip_slot = clip_slot


	def armed_tracks(self):
		tracks = []
		for t in self.get_tracks():
			if liveobj_valid(t) and t.can_be_armed:
				if t.arm is True:
					tracks.append(t)
		return tracks


	@clip_stop_buttons.pressed
	def clip_stop_buttons(self, button):
		debug('clip_stop_buttons.pressed', button)
		self._on_stop_track_value(button)


	def _on_stop_track_value(self, button):
		if self.is_enabled():
			button = button._control_element
			tracks = self._session_ring.tracks_to_use()
			track_index = list(self.clip_stop_buttons.control_elements).index(button) + self._session_ring.track_offset
			debug('track_index:', track_index)
			if in_range(track_index, 0, len(tracks)):
				debug('in range', tracks[track_index])
				if liveobj_valid(tracks[track_index]):
					debug('in tracks')
					tracks[track_index].stop_all_clips()

	# def set_new_managed_select_button(self, button):
	#     self.new_managed_select_button.set_control_element(button)
	#     self.set_modifier_button(button, 'select')
	#
	# def set_new_managed_delete_button(self, button):
	#     self.new_managed_delete_button.set_control_element(button)
	#     self.set_modifier_button(button, 'delete')
	#
	# def set_new_managed_duplicate_button(self, button):
	#     self.new_managed_duplicate_button.set_control_element(button)
	#     self.set_modifier_button(button, 'duplicate')


#mixer offset problem is here somehow
class UtilSessionRingComponent(SessionRingTrackProvider):

	def __init__(self, *a, **k):
		super(UtilSessionRingComponent, self).__init__(*a, **k)
		#self._track_assigner = UtilRightAlignTracksTrackAssigner(song=(self.song))
		#self._track_assigner = UtilSimpleTrackAssigner()
		self._on_offsets_changed.subject = self

	@listens('offset')
	def _on_offsets_changed(self, track_offset, scene_offset):
		self.notify_offsets(self.track_offset, self.scene_offset)

	@listenable_property
	def offsets(self):
		return (self.track_offset, self.scene_offset)


class ModGridSessionNavigationComponent(SessionNavigationComponent):

	def set_up_button(self, button):
		super(ModGridSessionNavigationComponent, self).set_up_button(button)
		if hasattr(button, "_display"):
			button._display.display_message('^')

	def set_down_button(self, button):
		super(ModGridSessionNavigationComponent, self).set_down_button(button)
		if hasattr(button, "_display"):
			button._display.display_message('v')

	def set_left_button(self, button):
		super(ModGridSessionNavigationComponent, self).set_left_button(button)
		if hasattr(button, "_display"):
			button._display.display_message('<')

	def set_right_button(self, button):
		super(ModGridSessionNavigationComponent, self).set_right_button(button)
		if hasattr(button, "_display"):
			button._display.display_message('>')

	def set_page_up_button(self, page_up_button):
		super(ModGridSessionNavigationComponent, self).set_page_up_button(page_up_button)
		if hasattr(button, "_display"):
			button._display.display_message('PgUp')

	def set_page_down_button(self, page_down_button):
		super(ModGridSessionNavigationComponent, self).set_page_down_button(page_down_button)
		if hasattr(button, "_display"):
			button._display.display_message('PgDn')

	def set_page_left_button(self, page_left_button):
		super(ModGridSessionNavigationComponent, self).set_page_left_button(page_left_button)
		if hasattr(button, "_display"):
			button._display.display_message('PgLt')

	def set_page_right_button(self, page_right_button):
		super(ModGridSessionNavigationComponent, self).set_page_right_button(page_right_button)
		if hasattr(button, "_display"):
			button._display.display_message('PgRt')


class UtilViewControlComponent(ViewControlComponent):

	toggle_clip_detail_button = DisplayingButtonControl(text='ClipDetail')
	toggle_detail_clip_loop_button = DisplayingButtonControl(text='LoopDetail')

	def __init__(self, *a, **k):
		super(UtilViewControlComponent, self).__init__(*a, **k)

	def set_toggle_clip_detail_button(self, button):
		self.toggle_clip_detail_button.set_control_element(button)
		if hasattr(button, "_display"):
			button._display.display_message('Detail')

	@toggle_clip_detail_button.pressed
	def toggle_clip_detail_button(self, button):
		self._on_toggle_clip_detail_button_pressed(button)

	def _on_toggle_clip_detail_button_pressed(self, button):
		self.toggle_clip_detail()

	def toggle_clip_detail(self):
		app_view = self.application.view
		if app_view.is_view_visible('Detail/Clip') and app_view.is_view_visible('Detail'):
			app_view.hide_view('Detail/Clip')
			app_view.hide_view('Detail')
		else:
			self.show_view('Detail/Clip')

	def set_toggle_detail_clip_loop_button(self, button):
		self.toggle_detail_clip_loop_button.set_control_element(button)
		if hasattr(button, "_display"):
			button._display.display_message('LoopDetail')

	@toggle_detail_clip_loop_button.pressed
	def toggle_detail_clip_loop_button(self, button):
		self._on_toggle_detail_clip_loop_button_pressed(button)

	def _on_toggle_detail_clip_loop_button_pressed(self, button):
		self.toggle_detail_clip_loop()

	def toggle_detail_clip_loop(self):
		detail_clip = self.song.view.detail_clip
		if liveobj_valid(detail_clip) and hasattr(detail_clip, 'looping'):
			detail_clip.looping = not detail_clip.looping

	def set_prev_track_button(self, button):
		super(UtilViewControlComponent, self).set_prev_track_button(button)
		if hasattr(button, "_display"):
			button._display.display_message('<-')

	def set_next_track_button(self, button):
		super(UtilViewControlComponent, self).set_next_track_button(button)
		if hasattr(button, "_display"):
			button._display.display_message('->')


class PresetTaggerSelectorComponent(Component):


	PT_button = DisplayingButtonControl(text='PT')
	def __init__(self, modhandler, *a, **k):
		self._modhandler = modhandler
		self._PT_locked = False
		super(PresetTaggerSelectorComponent, self).__init__(*a, **k)

	@PT_button.pressed
	def PT_button(self, button):
		if not self._PT_locked:
			self._PT_locked = True
			self._modhandler.select_mod_by_name('PT')
			self._modhandler.set_lock(True)
			self.PT_button.color = 'DefaultButton.On'
		else:
			self._PT_locked = False
			self._modhandler.set_lock(False)
			self._modhandler._on_device_changed()
			self.PT_button.color = 'DefaultButton.Off'
			self.select_first_armed_track()

	def get_tracks(self):
		tracks = [track for track in self.song.tracks]
		for track in self.song.return_tracks:
			tracks.append(track)
		return tracks

	def armed_tracks(self):
		tracks = []
		for t in self.get_tracks():
			if liveobj_valid(t) and t.can_be_armed:
				if t.arm:
					tracks.append(t)
		return tracks

	def select_first_armed_track(self):
		debug('select_first_armed_track')
		armed_tracks = self.armed_tracks()
		if len(armed_tracks):
			self.song.view.selected_track = armed_tracks[0]


class DeviceDeleteComponent(Component):


	delete_button = DisplayingButtonControl(text='DeviceDel')

	def __init__(self, device_provider, *a, **k):
		self.device_provider = device_provider
		super(DeviceDeleteComponent, self).__init__(*a, **k)

	@delete_button.pressed
	def delete_button(self, button):
		device = self.device_provider.device
		if liveobj_valid(device):
			device_parent = device.canonical_parent
			device_index = list(device_parent.devices).index(device)
			device_parent.delete_device(device_index)


class HotswapComponent(Component):

	hotswap_button = DisplayingButtonControl(text='Hotswap')

	def __init__(self, device_provider = None, *a, **k):
		self._drum_group_device = None
		self._selected_drum_pad = None
		super(HotswapComponent, self).__init__(*a, **k)
		self.device_provider = device_provider or SpecialDeviceProvider(song = self.song)
		self._browser = Live.Application.get_application().browser
		self.__on_device_changed.subject = self.device_provider
		# self._on_track_changed.subject = self.__on_selected_device_changed.subject = self.song.view.selected_track.view

	@hotswap_button.pressed
	def hotswap_button(self, button):
		debug('hotswap button pressed')
		device = self.device_provider.device
		browser = self._browser
		selected_track_device = self.song.view.selected_track.view.selected_device
		debug('selected_track.view.selected_device:', selected_track_device)
		if not browser.hotswap_target == None:
			browser.hotswap_target = None
		elif liveobj_valid(self._selected_drum_pad):
			browser.hotswap_target = self._selected_drum_pad
		elif liveobj_valid(self._drum_group_device):
			browser.hotswap_target = self._drum_group_device
		elif liveobj_valid(device):
			browser.hotswap_target = device
		elif liveobj_valid(selected_track_device):
			browser.hotswap_target = selected_track_device

	def set_drum_group_device(self, drum_group_device):
		debug('set_drum_group_device', drum_group_device)
		if drum_group_device and not drum_group_device.can_have_drum_pads:
			drum_group_device = None
		if drum_group_device != self._drum_group_device:
			drum_group_view = drum_group_device.view if drum_group_device else None
			self.__on_selected_drum_pad_changed.subject = drum_group_view
			# self.__on_chains_changed.subject = drum_group_device
			self._drum_group_device = drum_group_device
			# self._update_drum_pad_listeners()
			self._update_selected_drum_pad()

	@listens('device')
	def __on_device_changed(self):
		device = self.device_provider.device
		debug('_on_device_changed', device)
		# if liveobj_valid(device) and not self.browser.hotswap_target == None:
		# 	self.browser.hotswap_target = device
		self.set_drum_group_device(device)

	@listens('selected_drum_pad')
	def __on_selected_drum_pad_changed(self):
		self._update_selected_drum_pad()

	def _update_selected_drum_pad(self):
		debug('_update_selected_drum_pad')
		selected_drum_pad = self._drum_group_device.view.selected_drum_pad if liveobj_valid(self._drum_group_device) else None
		if liveobj_changed(self._selected_drum_pad, selected_drum_pad):
			self._selected_drum_pad = selected_drum_pad
			self._on_selected_drum_pad_changed()

	def _on_selected_drum_pad_changed(self):
		debug('_on_selected_drum_pad_changed', self._selected_drum_pad)

	# @listens(u'selected_track')
	# def __on_selected_track_changed(self):
	#     self.__on_selected_device_changed.subject = self.song.view.selected_track.view
	#     if self.device_selection_follows_track_selection:
	#         self.update_device_selection()
	#
	# @listens(u'selected_device')
	# def __on_selected_device_changed(self):
	#     self._update_appointed_device()


class SpecialBicoloredMomentaryBehaviour(BicoloredMomentaryBehaviour):

	def press_immediate(self, *a, **k):
		pass

	def press_delayed(self, *a, **k):
		super(SpecialBicoloredMomentaryBehaviour, self).press_immediate(*a, **k)


class ModGridKeysGroup(PlayableComponent, ScrollComponent, Scrollable):

	_position = 5
	_channel_offset = 0
	_hi_limit = 9
	TRANSLATION_CHANNEL = 15
	matrix = control_matrix(MPEPlayableControl)


	def __init__(self, translation_channel = 0, *a, **k):
		self._translation_channel = translation_channel
		super(ModGridKeysGroup, self).__init__(*a, **k)


	@listenable_property
	def view_is_enabled(self):
		return self.is_enabled()


	@listenable_property
	def position(self):
		return self._position


	@position.setter
	def position(self, index):
		assert(0 <= index <= 28)
		self._position = index
		#self.notify_position()


	def can_scroll_up(self):
		return self._position < self._hi_limit


	def can_scroll_down(self):
		return self._position > 1


	def scroll_up(self):
		self.position = self.position + 1
		self._update_note_translations()


	def scroll_down(self):
		self.position = self.position - 1
		self._update_note_translations()


	def _get_current_channel(self):
		return self.TRANSLATION_CHANNEL


	def _note_translation_for_button(self, button):
		note = button.identifier
		channel = self.TRANSLATION_CHANNEL
		#we are shifting the channel forward so that this button won't interfere with other buttons that aren't being translated
		if button._control_element:
			note = button._control_element.original_identifier() + (self.position * 12)
			channel = button._control_element._original_channel+1
			# debug('channel is:', channel)
		return ( note, channel)

	def _update_button_color(self, button):
		if not button._control_element is None and hasattr(button._control_element, 'original_identifier'):
			note = button._control_element.original_identifier()
			button.color = 1 if note%12 in WHITEKEYS else 0
			if button._control_element:
				button._control_element.scale_color = button.color

	def update(self, *a, **k):
		super(ModGridKeysGroup, self).update(*a, **k)
		self.notify_view_is_enabled()


class SpecialDeviceSelectorComponent(DeviceSelectorComponent):
	_name_data_sources = list(map(DisplayDataSource, ('', '', '', '', '', '', '', '')))
	
	def set_buttons(self, buttons):
		super(SpecialDeviceSelectorComponent, self).set_buttons(buttons)

		if self.is_enabled():
			if len(self._device_registry) != len(self._buttons):
				self.scan_all()
			name = 'None'
			dev = self.song.appointed_device
			offset = self._offset
			if self._buttons:
				for index in range(len(self._buttons)):
					preset = self._device_registry[index]
					button = self._buttons[index]
					if isinstance(button, ButtonElement):
						if isinstance(preset, Live.Device.Device) and hasattr(preset, 'name'):
							name = preset.name
							dev_type = preset.type
							dev_class = preset.class_name
							val = (dev_class in self._device_colors and self._device_colors[dev_class]) or (dev_type in self._device_colors and self._device_colors[dev_type]) or 7
							selected_shift = (dev == preset)*self._selected_colorshift
							button.send_value(val + selected_shift)
							button.set_text(preset.name)
						else:
							button.send_value(self._off_value)
							button.set_text(' ')
		

class AnimationComponent(Component):

	def __init__(self, task_server = None, *a, **k):
		self._flashing_elements = {}
		self._strobing_elements = {}
		super(AnimationComponent, self).__init__(*a, **k)
		self._tasks.add(task.repeat(task.sequence(task.delay(3), self.flash, task.delay(3), self.unflash)))

	def remove_interface(self, element):
		self._flashing_elements.pop(element, None)
		self._strobing_elements.pop(element, None)

	def add_interface(self, element, colors):
		# debug('add_interface:', element, colors)
		if not element in self._flashing_elements:
			self._flashing_elements[element] = colors

	def flash(self, *a):
		# debug('flash...', arg)
		# elements = self._flashing_elements.copy()
		elements = self._flashing_elements
		for element in elements:
			element.flash(elements[element][0])
	
	def unflash(self, *a):
		# debug('unflash...', arg)
		# elements = self._flashing_elements.copy()
		elements = self._flashing_elements
		for element in elements:
			element.flash(elements[element][1])


class SpecialModControl(ModControl):


	def refresh_state(self, *a, **k):
		# super(Util, self).refresh_state(*a, **k)
		self.modscript.refresh_state(*a, **k)
		self.modscript.modhandler.update()


	def modhandler_select_mod_by_name(self, name):
		if not self.modscript.modhandler is None:
			self.modscript.modhandler.select_mod_by_name(name)


	def modhandler_set_lock(self, val):
		if not self.modscript.modhandler is None:
			self.modscript.modhandler.set_lock(val)


	def hotswap_enable(self, value):
		browser = Live.Application.get_application().browser
		if value:
			device = self.modscript._device_provider.device
			if liveobj_valid(device):
				browser.hotswap_target = device
		else:
			browser.hotswap_target = None


	def change_device_bank(self, value, m4l_device = None, *a, **k):
		device = self.modscript._parameter_provider
		# debug('special_device is:', liveobj_valid(device.device()), device.device().name if liveobj_valid(device.device()) else device.device())
		if device.is_enabled() and liveobj_valid(device.device()) and (m4l_device == device.device()):
			if value != device._bank.index:
				device._device_bank_registry.set_device_bank(device._bank._device, min(device._bank.bank_count(), max(0, value)))


	def load_preset(self, target = None, folder = None, directory = 'defaultPresets'):
		debug('load_preset()', 'target:', target, 'folder:', folder, 'directory:', directory)
		if not target is None:
			browser = Live.Application.get_application().browser ##if not self.application.view.browse_mode else self.application.browser.hotswap_target
			user_folders = browser.user_folders
			for item in user_folders:
				if item.name == directory:
					if not folder is None:
						folder_target = None
						item_iterator = item.iter_children
						inneritems = [inneritem for inneritem in item_iterator]
						for inneritem in inneritems:
							if inneritem.name == folder:
								folder_target = inneritem
								break
						if folder_target:
							item_iterator = folder_target.iter_children
							inneritems = [inneritem for inneritem in item_iterator]
							for inneritem in inneritems:
								if isinstance(target, int):
									if target < len(inneritems):
										if inneritems[target].is_loadable:
											browser.load_item(inneritems[target])
											break
										elif inneritems[target].is_folder:
											debug(inneritems[target], '.is_folder')
											innertarget = inneritems[target]
											innertarget_iterator = innertarget.iter_children
											innertargetitems = [innertargetitem for innertargetitem in innertarget_iterator]
											debug('innertargetitems:', innertargetitems)
											if len(innertargetitems)>0 and innertargetitems[0].is_loadable:
												browser.load_item(innertargetitems[0])
												break
											else:
												debug(innertargetitems[0], 'item isnt loadable 0')
												break
										else:
											debug(inneritems[target], 'item isnt loadable 1')
											break
								else:
									if inneritem.name == target:
										if inneritem.is_loadable:
											browser.load_item(inneritem)
										else:
											debug(inneritem, 'item isnt loadable 2')
										break
					else:
							item_iterator = item.iter_children
							inneritems = [inneritem for inneritem in item_iterator]
							for inneritem in inneritems:
								if isinstance(target, int):
									if target < len(inneritems):
										if inneritems[target].is_loadable:
											browser.load_item(inneritems[target])
											break
										else:
											debug(inneritems[target], 'item isnt loadable 3')
											break
								else:
									if inneritem.name == target:
										if inneritem.is_loadable:
											browser.load_item(inneritem)
											break
										else:
											debug(inneritem, 'item isnt loadable 4')
											break


class TextGrid(Grid):

	def __init__(self, name, width, height, active_handlers = return_empty, *a, **k):
		super(TextGrid, self).__init__(name, width, height, active_handlers, *a, **k)
		self._cell = [[StoredElement(active_handlers, _name = self._name + '_' + str(x) + '_' + str(y), _x = x, _y = y , _value = '', *a, **k) for y in range(height)] for x in range(width)]


class TextArray(Array):

	def __init__(self, name, size, active_handlers = return_empty, *a, **k):
		super(TextArray, self).__init__(name, size, active_handlers, *a, **k)
		self._cell = [StoredElement(self._name + '_' + str(num), _num = num, _value = '', *a, **k) for num in range(size)]


class ModGridNavigationBox(NavigationBox):


	def update(self):
		# debug('nav_box.update()')
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
		left_button and left_button.set_light('DefaultButton.On' if (xoff>0) else 'DefaultButton.Off')
		right_button and right_button.set_light('DefaultButton.On' if (xoff<(self.width()-self._window_x)) else 'DefaultButton.Off')
		up_button and up_button.set_light('DefaultButton.On' if (yoff>0) else 'DefaultButton.Off')
		down_button and down_button.set_light('DefaultButton.On' if (yoff<(self.height()-self._window_y)) else 'DefaultButton.Off')


class ModGridModHandler(ModHandler):


	Shift_button = DisplayingButtonControl(text='Shift', color='DefaultButton.Off', pressed_color=7)
	Alt_button = DisplayingButtonControl(text='Alt', color='DefaultButton.Off', pressed_color=7)
	_name = 'ModGridModHandler'

	def __init__(self, *a, **k):
		self._color_type = 'Push'
		self._grid = None
		addresses = {'key_text': {'obj':TextArray('key_text', 8), 'method':self._receive_key_text},
					'grid_text': {'obj':TextGrid('grid_text', 16, 16), 'method':self._receive_grid_text}}
		self._special_mode_index = 0
		super(ModGridModHandler, self).__init__(addresses = addresses, *a, **k)
		self.nav_box = ModGridNavigationBox(self, 16, 16, 16, 16, self.set_offset,)
		self._shifted = False


	@listenable_property
	def view(self):
		return self.active_mod().view if not self.active_mod() is None else 'Full'


	@listenable_property
	def mira_address(self):
		return self.active_mod().mira_address if not self.active_mod() is None else None


	@listens('view')
	def _on_view_changed(self, *a, **k):
		debug('handler._on_view_changed', self.view)
		self.notify_view(self.view)


	@listens('mira_address')
	def _on_mira_address_changed(self, *a, **k):
		# debug('_on_mira_address_changed()')
		self.notify_mira_address(self.mira_address)


	def select_mod(self, mod):
		super(ModGridModHandler, self).select_mod(mod)
		#self._script._select_note_mode()
		self._on_view_changed.subject = mod
		self._on_mira_address_changed.subject = mod
		self.update()
		#debug('modhandler select mod: ' + str(mod))


	def set_shift_mode(self, shift_mode = None):
		pass


	def set_alt_mode(self, alt_mode = None):
		pass


	# @listens('selected_mode')
	# def set_grid(self, grid):
	# 	#debug('set grid:' + str(grid))
	# 	self._grid = grid
	# 	self._grid_value.subject = grid
	# 	if not self._grid is None:
	# 		for button, _ in grid.iterbuttons():
	# 			if not button == None:
	# 				button.use_default_message()
	# 				if hasattr(button, 'set_enabled'):
	# 					button.set_enabled(True)
	# 				elif hasattr(button, 'suppress_script_forwarding'):
	# 					button.suppress_script_forwarding = False
	# 	self.update()

	def _receive_grid(self, x, y, value = -1, identifier = -1, channel = -1, *a, **k):
		#debug('_receive_ blocks_grid:', x, y, value, identifier, channel)
		mod = self.active_mod()
		if mod and self._grid_value.subject:
			if mod.legacy:
				x = x-self.x_offset
				y = y-self.y_offset
			if x in range(16) and y in range(16):
				# value > -1 and self._grid_value.subject.send_value(x, y, self._push_colors[self._colors[value]], True)
				try:
					value > -1 and self._grid_value.subject.send_value(x, y, value, True)
				except:
					pass
				button = self._grid_value.subject.get_button(y, x)
				if button:
					new_identifier = identifier if identifier > -1 else button._original_identifier
					new_channel = channel if channel > -1 else button._original_channel
					button._msg_identifier != new_identifier and button.set_identifier(new_identifier)
					button._msg_channel != new_channel and button.set_channel(new_channel)
					button._report_input = True
					# button.set_enabled((channel, identifier) == (-1, -1))
					button.script_forwarding = ScriptForwarding.exclusive if (channel, identifier) == (-1, -1) else ScriptForwarding.non_consuming


	def _receive_grid_text(self, x, y, value = '', *a, **k):
		# debug('_receive_grid_text:', x, y, value)
		mod = self.active_mod()
		if mod and self._grid_value.subject:
			if mod.legacy:
				x = x-self.x_offset
				y = y-self.y_offset
			if x in range(16) and y in range(16):
				button = self._grid_value.subject.get_button(y, x)
				if button:
					# debug('setting button')
					button.set_text(value)


	def _receive_key(self, x, value):
		#debug('_receive_key:', x, value)
		if not self._keys_value.subject is None:
			# self._keys_value.subject.send_value(x, 0, self._push_colors[self._colors[value]], True)
			self._keys_value.subject.send_value(x, 0, value, True)


	def _receive_key_text(self, x, value = '', *a, **k):
		# debug('_receive_key_text:', x, value)
		if not self._keys_value.subject is None:
			button = self._keys_value.subject.get_button(0, x)
			if button:
				button.set_text(value)


	def nav_update(self):
		self.nav_box and self.nav_box.update()


	def set_modifier_colors(self):
		shiftbutton = self._shift_value.subject
		# shiftbutton and shiftbutton.set_on_off_values('Mod.ShiftOn', 'Mod.ShiftOff')
		altbutton = self._alt_value.subject
		# altbutton and altbutton.set_on_off_values('Mod.AltOn', 'Mod.AltOff')


	@Shift_button.pressed
	def Shift_button(self, button):
		debug('shift_button.pressed')
		self._is_shifted = True
		mod = self.active_mod()
		if mod:
			mod.send('shift', 1)
		self.shift_layer and self.shift_layer.enter_mode()
		if mod and mod.legacy:
			self.legacy_shift_layer and self.legacy_shift_layer.enter_mode()
		self.update()


	@Shift_button.released
	def Shift_button(self, button):
		self._is_shifted = False
		mod = self.active_mod()
		if mod:
			mod.send('shift', 0)
		self.legacy_shift_layer and self.legacy_shift_layer.leave_mode()
		self.shift_layer and self.shift_layer.leave_mode()
		self.update()


	@Alt_button.pressed
	def Alt_button(self, button):
		debug('alt_button.pressed')
		self._is_alted = True
		mod = self.active_mod()
		if mod:
			mod.send('alt', 1)
			mod._device_proxy._alted = True
			mod._device_proxy.update_parameters()
		self.alt_layer and self.alt_layer.enter_mode()
		self.update()


	@Alt_button.released
	def Alt_button(self, button):
		self._is_alted = False
		mod = self.active_mod()
		if mod:
			mod.send('alt', 0)
			mod._device_proxy._alted = False
			mod._device_proxy.update_parameters()
		self.alt_layer and self.alt_layer.leave_mode()
		self.update()


	def update(self, *a, **k):
		mod = self.active_mod()
		if not mod is None:
			mod.restore()
			if not self._grid_value.subject is None:
				for button in self._grid_value.subject:
					button.suppress_script_forwarding = False
		else:
			if not self._grid_value.subject is None:
				self._grid_value.subject.reset()
				for button in self._grid_value.subject:
					button.suppress_script_forwarding = False  #should be false to conform with original, but that really makes no sense. 
			if not self._keys_value.subject is None:
				self._keys_value.subject.reset()


	def update(self, *a, **k):
		super(ModGridModHandler, self).update()
		# mod = self.active_mod()
		# if self._is_alted:
		# 	self.alt_layer and self.alt_layer.enter_mode()
		# elif self._is_shifted:
		# 	self.legacy_shift_layer and self.legacy_shift_layer.leave_mode()
		# 	self.shift_layer and self.shift_layer.leave_mode()
		self.notify_view()
		self.notify_mira_address()


	@listens('value')
	def _shift_value(self, value, *a, **k):
		super(ModGridModHandler, self)._shift_value(value)
		debug('shift value:', value)
		if value:
			self.legacy_shift_layer and self.legacy_shift_layer.enter_mode()
			self.shift_layer and self.shift_layer.enter_mode()
		else:
			self.legacy_shift_layer and self.legacy_shift_layer.leave_mode()
			self.shift_layer and self.shift_layer.leave_mode()


	@listens('value')
	def _alt_value(self, value, *a, **k):
		debug('alt_value:', value)
		super(ModGridModHandler, self)._alt_value(value)
		if value:
			self.alt_layer and self.alt_layer.enter_mode()
		else:
			self.alt_layer and self.alt_layer.leave_mode()


	def update_buttons(self):
		# self._shift_value.subject and self._shift_value.subject.send_value(7 + self.is_shifted()*7)
		# self._on_shiftlock_value.subject and self._on_shiftlock_value.subject.send_value(3 + self.is_shiftlocked()*7)
		self._on_lock_value.subject and self._on_lock_value.subject.send_value(1 + self.is_locked()*7)
		# self._alt_value.subject and self._alt_value.subject.send_value(2 + self.is_alted()*7)


	def set_device_selector_assign_button(self, button):
		self._device_selector.set_assign_button(button)


class ModGrid(ControlSurface):



	_rgb = 0
	_color_type = 'Push'
	_timer = 0
	_touched = 0
	flash_status = False
	_model_name = 'ModGrid'
	_host_name = 'ModGrid'
	_version_check = 'b996'
	monomodular = None
	device_provider_class = ModDeviceProvider
	bank_definitions = BANK_DEFINITIONS
	_translation_table = ascii_translations

	def __init__(self, *a, **k):
		super(ModGrid, self).__init__(*a, **k)
		self.log_message = logger.info
		# self._skin = Skin(ModGridColors)
		self._skin = Skin(UtilColors)
		self._disable_autoarm = False
		with self.component_guard():
			self._setup_monobridge()
			self._setup_sysex()
			self._setup_animations()
			self._setup_controls()
			self._setup_background()
			self._setup_delete()
			self._setup_autoarm()
			self._setup_session_control()
			self._setup_mixer_control()
			self._setup_track_creator()
			self._setup_undo_redo()
			self._setup_view_control()
			self._setup_transport()
			self._setup_session_recording_component()
			self._setup_device_controls()
			self._setup_device_deleter()
			self._setup_hotswap()
			self._setup_device_selector()
			self._setup_mod()
			# self._setup_preset_tagger()
			self._setup_audiolooper()
			self._setup_instrument()
			self._setup_piano()
			self._setup_main_modes()
			self._initialize_script()
		self._on_device_changed.subject = self._device_provider
		self._update_view.subject = self.modhandler
		self._update_mira_address.subject = self.modhandler
		self.schedule_message(1, self._open_log)


	def _initialize_script(self):
		# self._main_modes.set_enabled(True)
		# self._main_modes.selected_mode = 'Main'
		self._global_modes.set_enabled(True)
		self._global_modes.selected_mode = "Full"
		self._on_device_changed()
		

	def turn_on_full_grid(self):
		# debug('sending full on')
		self._sysex.send('set_full_grid_view', [1, 1, 1])


	def turn_off_full_grid(self):
		# debug('sending full off')
		self._sysex.send('set_full_grid_view', [0, 0, 0])


	def _open_log(self):
		#self.log_message("<<<<<<<<<<<<<<<<<<<<= " + str(self._model_name) + " " + str(self._version_check) + " log opened =>>>>>>>>>>>>>>>>>>>")
		self.show_message(str(self._model_name) + ' Control Surface Loaded')


	def _close_log(self):
		#self.log_message("<<<<<<<<<<<<<<<<<<<<= " + str(self._model_name) + " " + str(self._version_check) + " log closed =>>>>>>>>>>>>>>>>>>>")
		pass


	@listenable_property
	def pipe(self):
		return None


	def _send(self, **a):
		notify_pipe(a)


	def _setup_sysex(self):
		self._sysex = AumhaaSettings(model = [93, 93], control_surface = self)


	def _setup_animations(self):
		self._animation_handler = AnimationComponent()


	def _setup_controls(self):
		main_chan = MAIN_CONTROL_CHANNEL
		is_momentary = True
		optimized = True
		resource = PrioritizedResource
		color_map = COLOR_MAP
		#self._pads_raw = [ ButtonElement(True, MIDI_NOTE_TYPE, 0, identifier, name=u'Pad_{}'.format(identifier), skin=skin) for identifier in xrange(100) ]

		# self._pad_raw = [None for index in range(128)]
		# for chan in range(14):
		# 	self._pad_raw[chan] = [[ButtonElement(is_momentary = is_momentary, msg_type = MIDI_NOTE_TYPE, channel = chan, identifier = MORPH_PADS[row][column], name = 'Pad_' + str(column) + '_' + str(row) + '_' + str(chan), skin = self._skin, resource_type = resource) for column in range(4)] for row in range(4)]
		# 	for row in self._pad_raw[chan]:
		# 		for pad in row:
		# 			pad.enabled = False
		# for proxy in range(256):
		# 	buttons = []
		# 	# debug('making pad ...', chan, proxy%4, math.floor(proxy/4))
		# 	for chan in range(7):
		# 		button = self._pad_raw[chan][int(proxy%4)][int(math.floor(proxy/4))]
		# 		buttons.append(button)
		# 	self._pad[int(proxy%4)][int(math.floor(proxy/4))] = SpecialMultiElement(buttons[0], buttons[1], buttons[2], buttons[3], buttons[4], buttons[5], buttons[6], buttons[7], buttons[8], buttons[9], buttons[10], buttons[11], buttons[12], buttons[13], buttons[14], buttons[15])
		# 	self._pad[int(proxy%4)][int(math.floor(proxy/4))]._name = 'PadCombo_'+str(proxy)

		self._pad = [SpecialMPEMonoButtonElement(is_momentary = is_momentary, 
				msg_type = MIDI_NOTE_TYPE,
				channel = 1 if index < 128 else 8, 
				identifier = index%128, 
				name = 'Pad_' + str(index), 
				script = self, 
				monobridge = self._monobridge, 
				skin = self._skin, 
				color_map = COLOR_MAP, 
				animation_handler = self._animation_handler, 
				optimized_send_midi = optimized, 
				resource_type = resource) 
			for index in range(256)]
		self._matrix = ButtonMatrixElement(name = 'Matrix', rows = [self._pad[(index*16):(index*16)+16] for index in range(16)])
		self._8x8_matrix = ButtonMatrixElement(name = "8x8Matrix", rows = [self._pad[(index*16):(index*16)+8] for index in range(8)])
		self._piano_matrix = ButtonMatrixElement(name = "PianoMatrix", rows = [self._pad[0:25]])

		self._key = [SpecialMonoButtonElement(is_momentary = is_momentary, msg_type = MIDI_NOTE_TYPE, channel = main_chan, identifier = index, name = 'Key_' + str(index), script = self, monobridge = self._monobridge, skin = self._skin, color_map = COLOR_MAP, optimized_send_midi = optimized, resource_type = resource) for index in range(8)]
		self._key_matrix = ButtonMatrixElement(name = 'KeyMatrix', rows = [self._key])

		self._shift = SpecialMonoButtonElement(is_momentary = is_momentary, msg_type = MIDI_NOTE_TYPE, channel = main_chan, identifier = 8, name = 'Shift', script = self, monobridge = self._monobridge, skin = self._skin, color_map = COLOR_MAP, optimized_send_midi = optimized, resource_type = resource)
		self._alt = SpecialMonoButtonElement(is_momentary = is_momentary, msg_type = MIDI_NOTE_TYPE, channel = main_chan, identifier = 9, name = 'Alt', script = self, monobridge = self._monobridge, skin = self._skin, color_map = COLOR_MAP, optimized_send_midi = optimized, resource_type = resource)
		self._lock = SpecialMonoButtonElement(is_momentary = is_momentary, msg_type = MIDI_NOTE_TYPE, channel = main_chan, identifier = 10, name = 'Lock', script = self, monobridge = self._monobridge, skin = self._skin, color_map = COLOR_MAP, optimized_send_midi = optimized, resource_type = resource)
		self._delete_button = SpecialMonoButtonElement(is_momentary = is_momentary, msg_type = MIDI_NOTE_TYPE, channel = main_chan, identifier = 11, name = 'Delete', script = self, monobridge = self._monobridge, skin = self._skin, color_map = COLOR_MAP, optimized_send_midi = optimized, resource_type = resource)

		self._fader = SpecialEncoderElement(msg_type = MIDI_CC_TYPE, channel = main_chan, identifier = 16, map_mode = Live.MidiMap.MapMode.absolute, name = 'Fader', resource_type = resource)
		self._master_dial = SpecialEncoderElement(msg_type = MIDI_CC_TYPE, channel = main_chan, identifier = 17, map_mode = Live.MidiMap.MapMode.absolute, name = 'MasterDial', resource_type = resource)
		self._crossfader = SpecialEncoderElement(msg_type = MIDI_CC_TYPE, channel = main_chan, identifier = 18, map_mode = Live.MidiMap.MapMode.absolute, name = 'Crossfader', resource_type = resource)

		self._button = [SpecialMonoButtonElement(color_map = color_map, script = self, monobridge = self._monobridge, is_momentary = is_momentary, msg_type = MIDI_NOTE_TYPE, channel = main_chan, identifier = index+12, name = 'Button_' + str(index), optimized_send_midi = optimized, resource_type = resource, skin = self._skin) for index in range(0,116)]
		self._button_matrix = ButtonMatrixElement(name = 'ButtonMatrix', rows = [self._button + [self._shift, self._alt, self._lock, self._delete_button]])
		self._track_select_matrix = ButtonMatrixElement(name = 'TrackSelectMatrix', rows = [self._button[80:88]])
		self._device_select_matrix = ButtonMatrixElement(name = 'DeviceSelectMatrix', rows = [self._button[88:96]])
		self._chain_select_matrix = ButtonMatrixElement(name = 'ChainSelectMatrix', rows = [self._button[96:104]])

		# self._device_select_display_matrix = ButtonMatrixElement(name = 'DeviceSelectDisplayMatrix', rows = [[self._button[index]._display for index in range(88,104)]])

		self._encoder = [SpecialEncoderElement(name = 'Encoder_'+str(index),  msg_type = MIDI_CC_TYPE, channel = main_chan, identifier = index, map_mode = Live.MidiMap.MapMode.absolute,) for index in range(0,16)]

		self._encoder_matrix = ButtonMatrixElement(name = 'Dial_Matrix', rows = [self._encoder]) # + [self._fader, self._master_dial, self._crossfader]]) #, self._encoder[8:]])
		self._encoder_name_displays = ButtonMatrixElement(name = 'Dial_Name_Displays', rows = [[self._encoder[index]._name_display for index in range(16)]])
		self._encoder_value_displays = ButtonMatrixElement(name = 'Dial_Value_Displays', rows = [[self._encoder[index]._value_display for index in range(16)]])

		self._keys = self._key_matrix

		# self.on_button_text_changed.replace_subjects(self._pad + self._key + [self._shift, self._alt])

		self._shiftMode = EventMode()
		self._altMode = EventMode()
		self._sendMode = EventMode()
		self._deviceMode = EventMode()

		self._shiftModes = ModesComponent(name = 'ShiftModes')
		self._shiftModes.add_mode('disabled', [])
		self._shiftModes.add_mode('shift', [self._shiftMode], behaviour = CancellableBehaviourWithRelease())
		self._shiftModes.layer = Layer(priority = 6, shift_button = self._shift)
		self._shiftModes.selected_mode = 'disabled'
		self._shiftModes.set_enabled(True)
		self._shift._display.set_data_sources([DisplayDataSource("Shift")])

		self._altModes = ModesComponent(name = 'AltModes')
		self._altModes.add_mode('disabled', [])
		self._altModes.add_mode('alt', [self._altMode], behaviour = CancellableBehaviourWithRelease())
		self._altModes.layer = Layer(priority = 6, alt_button = self._alt)
		self._altModes.selected_mode = 'disabled'
		self._altModes.set_enabled(True)
		self._alt._display.set_data_sources([DisplayDataSource("Alt")])

		self._sendModes = ModesComponent(name = 'SendModes')
		self._sendModes.add_mode('disabled', [])
		self._sendModes.add_mode('send', [self._sendMode], behaviour = SpecialBicoloredMomentaryBehaviour(color = 5, off_color = 10))
		self._sendModes.layer = Layer(priority = 6, send_button = self._button[23])
		self._sendModes.selected_mode = 'disabled'
		self._sendModes.set_enabled(True)
		# self._shift._display.set_data_sources([DisplayDataSource("Shift")])
	
		self._deviceModes = ModesComponent(name = 'DeviceModes')
		self._deviceModes.add_mode('disabled', [])
		self._deviceModes.add_mode('device', [self._deviceMode], behaviour = SpecialBicoloredMomentaryBehaviour(color = 5, off_color = 10))
		self._deviceModes.layer = Layer(priority = 6, device_button = self._button[21])
		self._deviceModes.selected_mode = 'disabled'
		self._deviceModes.set_enabled(True)

		self._shifted_chain_select_matrix = ButtonMatrixElement(rows = [[DisplayingComboElement(button, "Stop", modifier = self._shiftMode) for button in self._button[96:104]]])
		self._shifted_left_matrix = ButtonMatrixElement(rows = [[DisplayingComboElement(self._pad[(index*16)+7], "Scene", modifier = self._shiftMode)]for index in range(8)])


	def _setup_background(self):
		self._background = SpecialBackgroundComponent(name = 'Background', add_nop_listeners=True)
		self._background.layer = Layer(priority = 1, 
			matrix = self._matrix,
			keys = self._key_matrix,
			buttons = self._button_matrix, 
			encoders = self._encoder_matrix, 
			device_matrix = self._device_select_matrix, 
			chain_matrix = self._chain_select_matrix,
			fader = self._fader,
			master_dial = self._master_dial,
			crossfader = self._crossfader)
		self._background.set_enabled(False)


	def _setup_delete(self):
		# self._delete_default_component = DeleteAndReturnToDefaultComponent(name='DeleteAndDefault')
        # self._delete_default_component.layer = Layer(delete_button='delete_button')
        # self._delete_clip = DeleteSelectedClipComponent(name='Selected_Clip_Deleter')
        # self._delete_clip.layer = Layer(action_button='delete_button')
        # self._delete_scene = DeleteSelectedSceneComponent(name='Selected_Scene_Deleter')
        # self._delete_scene.layer = Layer(action_button=(self._with_shift('delete_button')))
		self._delete_component = DeleteComponent(name='Deleter')
		self._delete_component.layer = Layer(priority=6, delete_button=self._delete_button)


	def _setup_autoarm(self):
		self._autoarm = UtilAutoArmComponent(name='Auto_Arm')
		# self._autoarm.layer = Layer(priority = 6, util_autoarm_toggle_button = self._pad[16])
		self._autoarm.layer = Layer(priority = 6, util_autoarm_toggle_button = self._with_alt_latch(control=self._button[88], text='AutoArm'))
		self._autoarm.set_enabled(False)
		#self._auto_arm._can_auto_arm_track = self._can_auto_arm_track


	def _setup_session_control(self):
		self._session_ring = UtilSessionRingComponent(num_tracks = 8, num_scenes = 8)
		self._session_ring.set_enabled(False)

		self._session_navigation = ModGridSessionNavigationComponent(name = 'SessionNavigation', session_ring = self._session_ring)
		self._session_navigation.layer = Layer(priority = 6, left_button = self._with_shift_latch(self._button[59]), right_button = self._with_shift_latch(self._button[60]), up_button = self._with_shift_latch(self._button[58]), down_button = self._with_shift_latch(self._button[61]))
		self._session_navigation.set_enabled(False)

		# self._session_recording = SessionRecordingComponent(name = 'SessionRecording')
		# self._session_recording.layer = Layer(scene_list_new_button = self._button[8])
		# self._session_recording.set_enabled(False)

		self._session = UtilSessionComponent(session_ring = self._session_ring, auto_name = True)
		self._session.set_rgb_mode(LIVE_COLORS_TO_MIDI_VALUES, RGB_COLOR_TABLE, clip_slots_only=True)
		self._session.launch_layer = AddLayerMode(self._session, Layer(priority = 6, 
			clip_launch_buttons = self._8x8_matrix, 
			clip_stop_buttons = self._shifted_chain_select_matrix))
		self._session.delete_layer = AddLayerMode(self._session, Layer(priority = 6,
			managed_delete_button = self._delete_button,
			managed_duplicate_button = self._with_shift_latch(self._with_text(self._button[6], 'Duplicate'))))
		self._session.scene_layer = AddLayerMode(self._session, Layer(priority = 6,
			scene_launch_buttons = self._shifted_left_matrix))
		# self._session.layer = Layer(util_fire_next_button = self._button[3],
		# 	util_fire_prev_button = self._button[4],
		# 	util_stop_clip_button = self._button[5],
		# 	stop_all_clips_button = self._button[6],
		# 	util_select_playing_clipslot_button = self._button[7],
		# 	util_capture_new_scene_button = self._button[8],
		# 	util_fire_next_absolute_button = self._button[24],
		# 	util_fire_prev_absolute_button = self._button[25],
		# 	util_fire_next_on_single_armed_button = self._button[26],
		# 	util_fire_next_on_all_armed_button = self._button[27],
		# 	util_select_playing_on_single_armed_button = self._button[35])

		self._session.set_enabled(False)


	def _setup_mixer_control(self):
		self._mixer = UtilMixerComponent(name = 'Mixer', tracks_provider = self._session_ring, track_assigner = SimpleTrackAssigner(), auto_name = True, channel_strip_component_type = UtilChannelStripComponent)
		#self._mixer = UtilMixerComponent(name = 'Mixer', tracks_provider = self._session_ring, track_assigner = RightAlignTracksTrackAssigner(include_master_track = True), auto_name = True, channel_strip_component_type = UtilChannelStripComponent)

		self._mixer.layer = Layer(priority = 6,
			util_arm_kill_button = self._with_alt_latch(control = self._button[0], text = "ArmKill"),
			util_mute_kill_button = self._with_alt_latch(control = self._button[1], text = "MuteKill"),
			util_solo_kill_button = self._with_alt_latch(control = self._button[2], text = "SoloKill"),
			arming_track_select_buttons = self._track_select_matrix,)
		self._mixer.prehear_layer = AddLayerMode(self._mixer, Layer(priority = 6, 
			prehear_volume_control = self._with_shift_latch(control = self._master_dial, text = "Prehear")))
			# util_mute_flip_button = self._button[12],
			# util_select_first_armed_track_button = self._button[23],

			# util_lower_all_track_volumes_button = self._button[36],
		self._mixer._selected_strip.layer = Layer(priority = 6,
			arm_button = self._button[0],
			mute_button = self._button[1],
			solo_button = self._button[2],
			util_arm_exclusive_button = self._with_shift_latch(control=self._button[0], text="ArmExcl"),
			util_mute_exclusive_button = self._with_shift_latch(control=self._button[1], text="MuteExcl"),
			util_solo_exclusive_button = self._with_shift_latch(control=self._button[2], text="SoloExcl"),
			volume_control = self._fader,)
		self._mixer._selected_strip.all_sends_layer = AddLayerMode(self._mixer._selected_strip, Layer(priority = 6,
			send_controls = self._encoder_matrix.submatrix[:8, :]))

		# self._mixer.device_layer = AddLayerMode(self._mixer, Layer(priority = 6,
		# 	))
		self._mixer.sends_layer = AddLayerMode(self._mixer, Layer(priority = 6,
			send_controls = self._encoder_matrix.submatrix[:8, :]))
		self._mixer.send_navigation.scroll_layer = AddLayerMode(self._mixer.send_navigation, Layer(priority = 8, 
			scroll_up_button = self._with_sends_latch(control=self._button[95], text="Send Up"),
			scroll_down_button = self._with_sends_latch(control=self._button[94], text="Send Down")))
		self._mixer.volume_layer = AddLayerMode(self._mixer, Layer(priority = 6,
			volume_controls = self._encoder_matrix.submatrix[:8, :]))
		self._mixer.pan_layer = AddLayerMode(self._mixer, Layer(priority = 6,
			pan_controls = self._encoder_matrix.submatrix[8:, :]))
		self._mixer.hybrid_send_layer = AddLayerMode(self._mixer.selected_strip, Layer(priority = 6,
			send_controls = self._encoder_matrix.submatrix[:4, :]))
		self._mixer.hybrid_return_layer = AddLayerMode(self._mixer, Layer(priority = 6,
			return_controls = self._encoder_matrix.submatrix[4:8, :]))

		self._mixer.mute_layer = AddLayerMode(self._mixer, Layer(priority=6, 
			mute_buttons = self._device_select_matrix))

		self._mixer._master_strip.layer = Layer(priority = 6,
			volume_control = self._master_dial)
		self._master_select = MasterTrackComponent(tracks_provider = self._session_ring)
		self._master_select.layer = Layer(priority = 6,
			toggle_button = self._with_text(self._button[3], "Master"))
		self._master_select.set_enabled(False)
		self._mixer._assign_skin_colors()
		self._mixer.set_enabled(False)


	def _setup_track_creator(self):
		self._track_creator = TrackCreatorComponent()
		# self._track_creator.layer = Layer(priority = 6, create_audio_track_button = self._button[18], create_midi_track_button = self._with_shift_latch(self._button[18], "Create MIDI"))
		self._track_creator.layer = Layer(priority = 6, 
			create_audio_track_button=self._with_alt_latch(control=self._button[89], text='Create Audio'), 
			create_midi_track_button = self._with_alt_latch(control=self._button[90], text="Create MIDI"))


	def _setup_undo_redo(self):
		self._undo_redo = ModGridUndoRedoComponent()
		self._undo_redo.layer = Layer(priority = 6, undo_button = self._button[20], redo_button = self._with_shift_latch(self._button[20], "Redo"))


	def _setup_view_control(self):
		self._view_control = UtilViewControlComponent()
		self._view_control.layer = Layer(priority = 6, prev_track_button = self._button[59], next_track_button = self._button[60], prev_scene_button = self._button[58], next_scene_button = self._button[61])
		# toggle_clip_detail_button = self._button[17], toggle_detail_clip_loop_button = self._button[22],


	def _setup_transport(self):
		self._transport = ModGridTransportComponent()
		self._transport.layer = Layer(priority = 6, play_button = self._button[4],
				stop_button = self._with_shift_latch(control=self._button[4],  text="Stop"),
				metronome_button = self._with_shift_latch(control=self._button[3],  text="Metro"),
				overdub_button = self._with_shift_latch(self._button[7], text="Overdub"),
				record_button = self._button[5])
		# stop_button = self._button[31],


	def _setup_session_recording_component(self):
		self._clip_creator = ClipCreator()
		self._clip_creator.name = 'ClipCreator'
		self._recorder = ModGridFixedLengthSessionRecordingComponent(length_values = LENGTH_VALUES, clip_creator = self._clip_creator, view_controller = ViewControlComponent())
		self._recorder.layer = Layer(priority = 6, 
			record_button = self._button[7], 
			# new_button = self._with_shift_latch(control=self._button[7], text="New"),
			new_button = self._with_text(self._button[6], 'New'),
			automation_button = self._with_shift_latch(control=self._button[5], text="Automation"))

		# record_button = self._button[6],
		# , scene_list_new_button = self._button[38]
		#self._recorder.alt_layer = LayerMode(self._recorder, Layer(priority = 6, new_button = self._button[5], record_button = self._button[6]))
		# self._recorder.alt_layer = LayerMode(self._recorder, Layer(priority = 6, length_buttons = self._nav_buttons.submatrix[1:4,:]))
		self._recorder.set_enabled(False)


	def _setup_device_controls(self):
		self._device_bank_registry = DeviceBankRegistry()
		self._device_decorator = DeviceDecoratorFactory()
		self._banking_info = BankingInfo(self.bank_definitions)
		self._parameter_provider  = UtilDeviceComponent(device_provider = self._device_provider,
													device_decorator_factory = self._device_decorator,
													device_bank_registry = self._device_bank_registry,
													banking_info = self._banking_info,
													name = "DeviceComponent")
		self._parameter_provider.layer = Layer(priority = 6, bank_down_button = self._button[44], bank_up_button = self._button[45])
		self._device = UtilDeviceParameterComponent(parameter_provider = self._parameter_provider,)
		self._device.main_layer = AddLayerMode(self._device, Layer(priority = 6, parameter_controls = self._encoder_matrix,
									parameter_name_displays = self._encoder_name_displays,
									parameter_value_displays = self._encoder_value_displays,))
		self._device.half_layer = AddLayerMode(self._device, Layer(priority = 6, parameter_controls = self._encoder_matrix.submatrix[8:, :],
									parameter_name_displays = self._encoder_name_displays.submatrix[8:, :],
									parameter_value_displays = self._encoder_value_displays.submatrix[8:, :],))
		self._device.set_enabled(False)

		self._track_list_component = TrackListComponent(tracks_provider = self._session_ring)
		self._device_navigation = UtilDeviceNavigationComponent(device_bank_registry = self._device_bank_registry,
																banking_info = self._banking_info,
																device_component = self._parameter_provider,
																track_list_component = self._track_list_component,
																delete_handler = self._delete_component)
		self._device_navigation.layer = Layer(priority = 6, 
			select_buttons = self._device_select_matrix,)
		self._device_navigation.scroll_left_layer = Layer(button = self._with_text(self._button[88], '<-'), priority = 8)
		self._device_navigation.scroll_right_layer = Layer(button = self._with_text(self._button[95], '->'), priority = 8)
		self._device_navigation.chain_selection.layer = Layer(select_buttons = self._chain_select_matrix, priority = 6)
		self._device_navigation.chain_selection.scroll_left_layer = Layer(button = self._with_text(self._button[96], '<-'), priority = 8)
		self._device_navigation.chain_selection.scroll_right_layer = Layer(button = self._with_text(self._button[103], '->'), priority = 8)
		self._device_navigation.bank_selection.layer = Layer(select_buttons = self._chain_select_matrix, priority = 6) #option_buttons = self._device_select_matrix,
		self._device_navigation.bank_selection.scroll_left_layer = Layer(button = self._with_text(self._button[96], '<-'), priority = 8)
		self._device_navigation.bank_selection.scroll_right_layer = Layer(button = self._with_text(self._button[103], '->'), priority = 8)
		# self._device_navigation.bank_inc_dec_layer = AddLayerMode(self._device_navigation.bank_selection, Layer(next_bank_button = self._button[44], priority = 6))
		self._device_navigation.set_enabled(False)

		# self._device_bank_incdec = BankIncDecComponent(device_bank_registry = self._device_bank_registry, banking_info = self._banking_info)
		# self._device_bank_incdec.layer = Layer(next_bank_button = self._button[44])
		# self._device_bank_incdec.set_enabled(False)


	def _setup_device_deleter(self):
		self._device_deleter = DeviceDeleteComponent(device_provider = self._device_provider)
		# self._device_deleter.layer = Layer(priority = 6, delete_button = self._button[39])


	def _setup_hotswap(self):
		# self._hotswap = HotswapComponent(self._device_provider)
		self._hotswap = HotswapComponent()
		self._hotswap.layer = Layer(priority = 6, hotswap_button = self._button[34])
		self._hotswap.set_enabled(False)


	def _setup_preset_tagger(self):
		self._preset_tagger_selector = PresetTaggerSelectorComponent(self.modhandler)
		self._preset_tagger_selector.layer = Layer(priority = 6, PT_button = self._button[119])
		self._preset_tagger_selector.set_enabled(False)


	def _setup_audiolooper(self):
		self._audiolooper = LoopSelectorComponent(follow_detail_clip=True, measure_length=4.0, name='Loop_Selector', default_size = 32)
		self._audiolooper.layer = Layer(priority = 6, loop_selector_matrix=self._matrix,
														shift_loop_left_button=self._key[0],
														shift_loop_right_button=self._key[1],
														latest_loop_button=self._key[2],
														toggle_recording_on_all_clips_and_loop_button=self._key[3],
														prev_page_button=self._key[6],
														next_page_button=self._key[7],
														shift_loop_right_keycommand_button=self._button[46],
														play_selected_clip_button=self._button[47],
														latest_loop_keycommand_button=self._button[48],
														loop_length_1_button=self._button[49],
														loop_length_2_button=self._button[50],
														loop_length_4_button=self._button[51],
														loop_length_8_button=self._button[52],
														loop_length_16_button=self._button[53],
														fix_grid_button=self._button[54],
														favorite_clip_color_button=self._button[55],
														shift_loop_left_keycommand_button=self._button[56],)

		self._audiolooper.set_enabled(False)


	def _setup_instrument(self):
		self._grid_resolution = GridResolution()

		# self._c_instance.playhead.enabled = True
		# self._playhead_element = PlayheadElement(self._c_instance.playhead)
		self._playhead_element = SpecialPlayheadElement(playhead = Playhead())
		#self._playhead_element.reset()

		quantgrid = ButtonMatrixElement([self._matrix._orig_buttons[2][4:8], self._matrix._orig_buttons[3][4:7]])

		self._drum_group_finder = PercussionInstrumentFinder(device_parent=self.song.view.selected_track)

		self._instrument = MonoInstrumentComponent(name = 'InstrumentModes', script = self, skin = self._skin, drum_group_finder = self._drum_group_finder, grid_resolution = self._grid_resolution, settings = DEFAULT_INSTRUMENT_SETTINGS, device_provider = self._device_provider, parent_task_group = self._task_group)
		self._instrument.layer = Layer(priority = 6, delete_button = self._with_text(self._delete_button, 'Delete'), shift_button = self._shiftMode)
		self._instrument.audioloop_layer = LayerMode(self._instrument, Layer(priority = 6, loop_selector_matrix = self._matrix))

		self._instrument.keypad_options_layer = AddLayerMode(self._instrument, Layer(priority = 5,
									scale_up_button = self._with_text(self._button[103], 'Scale->'),
									scale_down_button = self._with_text(self._button[102], '<-Scale'),
									offset_up_button = self._with_text(self._button[99], 'Offset->'),
									offset_down_button = self._with_text(self._button[98], '<-Offset'),
									vertical_offset_up_button = self._with_text(self._button[101], 'Vert->'),
									vertical_offset_down_button = self._with_text(self._button[100], '<-Vert'),
									#split_button = self._with_text(self._button[96], 'Split'),
									sequencer_button = self._with_text(self._button[96], 'Seq')))
		self._instrument.drumpad_options_layer = AddLayerMode(self._instrument, Layer(priority = 5,
									scale_up_button = self._with_text(self._button[103], 'Scale->'),
									scale_down_button = self._with_text(self._button[102], '<-Scale'),
									drum_offset_up_button = self._with_text(self._button[99], 'Offset->'),
									drum_offset_down_button = self._with_text(self._button[98], '<-Offset'),
									drumpad_mute_button = self._with_text(self._button[101], 'PadMute'),
									drumpad_solo_button = self._with_text(self._button[100], 'PadSolo'),
									#split_button = self._with_text(self._button[96], 'Split'),
									sequencer_button = self._with_text(self._button[96], 'Seq')))

		self._instrument._keypad.octave_toggle_layer = AddLayerMode(self._instrument._keypad, Layer(priority = 5, offset_shift_toggle = self._with_text(self._button[97], 'Octave')))
		self._instrument._drumpad.octave_toggle_layer = AddLayerMode(self._instrument._drumpad, Layer(priority = 5, offset_shift_toggle = self._with_text(self._button[97], 'Octave')))

		self._instrument._keypad.main_layer = LayerMode(self._instrument._keypad, Layer(priority = 5, keypad_matrix = self._8x8_matrix.submatrix[:,:]))
		self._instrument._keypad.select_layer = LayerMode(self._instrument._keypad, Layer(priority = 5, keypad_matrix = self._8x8_matrix.submatrix[:, 4:]))
		self._instrument._keypad.split_layer = LayerMode(self._instrument._keypad, Layer(priority = 5, keypad_matrix = self._8x8_matrix.submatrix[:, 4:]))
		self._instrument._keypad.split_select_layer = LayerMode(self._instrument._keypad, Layer(priority = 5, keypad_select_matrix = self._8x8_matrix.submatrix[:, 4:]))

		# self._instrument._keypad.sequencer_layer = AddLayerMode(self._instrument._keypad, Layer(priority = 5, playhead = self._playhead_element, sequencer_matrix = self._8x8_matrix.submatrix[:, :4], quantization_buttons = self._8x8_matrix.submatrix[4:8, 6:8],))
		self._instrument._keypad.sequencer_layer = AddLayerMode(self._instrument._keypad, Layer(priority = 5, playhead = self._playhead_element, keypad_matrix = self._8x8_matrix.submatrix[:,4:], sequencer_matrix = self._8x8_matrix.submatrix[:, :4], keypad_select_matrix = self._8x8_matrix.submatrix[:,4:]))
		self._playhead_element.keypad_layer = AddLayerMode(self._playhead_element, Layer(priority = 5, buttons = self._8x8_matrix.submatrix[:, :4]))
		self._instrument._keypad.sequencer_shift_layer = AddLayerMode(self._instrument._keypad, Layer(priority = 5, loop_selector_matrix = self._8x8_matrix.submatrix[:, :3], quantization_buttons = self._8x8_matrix.submatrix[:, 3:4],))

		self._instrument._drumpad.main_layer = LayerMode(self._instrument._drumpad, Layer(priority = 5, drumpad_matrix = self._8x8_matrix.submatrix[:,:],))
		self._instrument._drumpad.select_layer = LayerMode(self._instrument._drumpad, Layer(priority = 5, drumpad_select_matrix = self._8x8_matrix.submatrix[:,:]))
		self._instrument._drumpad.split_layer = LayerMode(self._instrument._drumpad, Layer(priority = 5, drumpad_matrix = self._8x8_matrix.submatrix[:4, 4:],))
		self._instrument._drumpad.split_select_layer = LayerMode(self._instrument._drumpad, Layer(priority = 5, drumpad_select_matrix = self._8x8_matrix.submatrix[:4, 4:]))

		self._instrument._drumpad.sequencer_layer = AddLayerMode(self._instrument._drumpad, Layer(priority = 5, playhead = self._playhead_element, sequencer_matrix = self._8x8_matrix.submatrix[:, :4], loop_selector_matrix = self._8x8_matrix.submatrix[4:8, 4:6], quantization_buttons = self._8x8_matrix.submatrix[4:8, 6:8],))
		self._playhead_element.drumpad_layer = AddLayerMode(self._playhead_element, Layer(priority = 5, buttons = self._8x8_matrix.submatrix[:, :4]))
		self._instrument._drumpad.sequencer_shift_layer = AddLayerMode(self._instrument._drumpad, Layer(priority = 5, sequencer_matrix = self._8x8_matrix.submatrix[:, :4], loop_selector_matrix = self._8x8_matrix.submatrix[4:8, 4:6], quantization_buttons = self._8x8_matrix.submatrix[4:8, 6:8]))

		self._instrument._selected_session._keys_layer = LayerMode(self._instrument._selected_session, Layer(priority = 5, clip_launch_buttons = self._8x8_matrix.submatrix[:, :2]))
		self._instrument._selected_session._drum_layer = LayerMode(self._instrument._selected_session, Layer(priority = 5, clip_launch_buttons = self._8x8_matrix.submatrix[:, :2]))

		self._instrument._main_modes = ModesComponent(parent = self._instrument, name = 'InstrumentModes')
		self._instrument._main_modes.add_mode('disabled', [])
		self._instrument._main_modes.add_mode('drumpad', [self._instrument._drumpad, self._instrument._drumpad.main_layer, self._instrument.drumpad_options_layer, self._instrument._drumpad.octave_toggle_layer])
		self._instrument._main_modes.add_mode('drumpad_split', [self._instrument._drumpad, self._instrument._drumpad.split_layer, self._instrument._selected_session, self._instrument._selected_session._drum_layer, self._instrument.drumpad_options_layer, self._instrument._drumpad.octave_toggle_layer])
		self._instrument._main_modes.add_mode('drumpad_sequencer', [self._instrument._drumpad, self._instrument._drumpad.sequencer_layer, self._playhead_element, self._playhead_element.drumpad_layer, self._instrument._drumpad.split_layer, self._instrument.drumpad_options_layer, self._instrument._drumpad.octave_toggle_layer])
		self._instrument._main_modes.add_mode('drumpad_shifted', [self._instrument._drumpad, self._instrument._drumpad.select_layer, self._instrument.drumpad_options_layer, self._instrument._drumpad.octave_toggle_layer])
		# self._instrument._main_modes.add_mode('drumpad_split_shifted', [ self._instrument._drumpad, self._instrument._drumpad.split_select_layer, self._instrument.drumpad_options_layer, self._instrument._drumpad.octave_toggle_layer, self._instrument._selected_session, self._instrument._selected_session._drum_layer])
		self._instrument._main_modes.add_mode('drumpad_sequencer_shifted', [self._instrument._drumpad, self._instrument._drumpad.split_select_layer, self._instrument._drumpad.sequencer_shift_layer, self._instrument.drumpad_options_layer, self._instrument._drumpad.octave_toggle_layer])
		self._instrument._main_modes.add_mode('keypad', [self._instrument._keypad, self._instrument._keypad.main_layer, self._instrument.keypad_options_layer, self._instrument._keypad.octave_toggle_layer])
		self._instrument._main_modes.add_mode('keypad_split', [self._instrument._keypad, self._instrument._keypad.split_layer, self._instrument._selected_session, self._instrument._selected_session._keys_layer, self._instrument.keypad_options_layer, self._instrument._keypad.octave_toggle_layer])
		self._instrument._main_modes.add_mode('keypad_sequencer', [self._instrument._keypad, self._instrument._keypad.sequencer_layer, self._playhead_element, self._playhead_element.keypad_layer, self._instrument._keypad.split_layer, self._instrument.keypad_options_layer, self._instrument._keypad.octave_toggle_layer])
		self._instrument._main_modes.add_mode('keypad_shifted', [self._instrument._keypad, self._instrument._keypad.main_layer, self._instrument.keypad_options_layer, self._instrument._keypad.octave_toggle_layer])
		# self._instrument._main_modes.add_mode('keypad_split_shifted', [self._instrument._keypad, self._instrument._keypad.split_select_layer, self._instrument.keypad_options_layer, self._instrument._keypad.octave_toggle_layer, self._instrument._selected_session, self._instrument._selected_session._keys_layer])
		self._instrument._main_modes.add_mode('keypad_sequencer_shifted', [self._instrument._keypad, self._instrument._keypad.split_select_layer, self._instrument._keypad.sequencer_shift_layer, self._instrument.keypad_options_layer, self._instrument._keypad.octave_toggle_layer])
		self._instrument._main_modes.add_mode('audioloop', [self._instrument.audioloop_layer])
		self._instrument.set_enabled(False)


	def _setup_piano(self):
		self._piano_group = ModGridKeysGroup()
		self._piano_group._hi_limit = 8
		self._piano_group.layer = Layer(priority = 6,
			matrix = self._piano_matrix, 
			scroll_up_button = self._with_text(self._button[99], 'Octave->'), 
			scroll_down_button = self._with_text(self._button[98], '<-Octave'))
		#self._piano_group.shift_layer = AddLayerMode(self._piano_group, Layer(matrix = self._piano_shift_matrix, scroll_up_button = self._pian0[12], scroll_down_button = self._key[11]))
		self._piano_group.set_enabled(False)


	def _setup_device_selector(self):
		self._device_selector = SpecialDeviceSelectorComponent(self)
		self._device_selector.main_layer = LayerMode(self._device_selector, Layer(priority = 7, 
			matrix = self._track_select_matrix, 
			assign_button = self._with_text(self._button[3], 'Assign'),
		))


	def _setup_mod(self):

		def get_monomodular(host):
				if isinstance(__builtins__, dict):
					if not 'monomodular' in list(__builtins__.keys()) or not isinstance(__builtins__['monomodular'], ModRouter):
						__builtins__['monomodular'] = ModRouter(song = self.song, register_component = self._register_component)
				else:
					if not hasattr(__builtins__, 'monomodular') or not isinstance(__builtins__['monomodular'], ModRouter):
						setattr(__builtins__, 'monomodular', ModRouter(song = self.song, register_component = self._register_component))
				monomodular = __builtins__['monomodular']
				if not monomodular.has_host():
					monomodular.set_host(host)
				return monomodular


		self.monomodular = get_monomodular(self)
		self.monomodular.name = 'monomodular_switcher'
		# with inject(register_component = const(self._register_component), song = const(self.song)).everywhere():
		self.modhandler = ModGridModHandler(self, song = self.song, register_component = self._register_component)
		self.modhandler.name = 'ModHandler'
		self.modhandler.layer = Layer( priority = 6, grid = self._matrix,
																			# shift_mode = self._shiftMode,
																			# alt_mode = self._altMode,
																			# Shift_button = self._shiftMode,
																			# Alt_button = self._altMode,
																			shift_button = self._shiftMode,
																			alt_button = self._altMode,
																			key_buttons = self._chain_select_matrix,)
																			# key_buttons = self._key_matrix)
		self.modhandler.alt_shift_layer = AddLayerMode( self.modhandler, Layer())
		self.modhandler.legacy_shift_layer = AddLayerMode( self.modhandler, Layer(priority = 6,
																			lock_button = self._with_text(self._button[28], "Mod Lock"),
																			# device_selector_matrix = self._matrix.submatrix[:, :1],
																			# device_selector_matrix = self._track_select_matrix,
																			#channel_buttons = self._matrix.submatrix[:, 1:2],
																			# lock_button = self._button[3],
																			))
																			#nav_matrix = self._matrix.submatrix[4:8, 2:6],
																			#))
		self.modhandler.shift_layer = AddLayerMode( self.modhandler, Layer( priority = 7,
																			# device_selector_matrix = self._matrix.submatrix[:, :1],
																			# device_selector_matrix = self._track_select_matrix,
																			# device_selector_assign_button = self._button[21],
																			# device_selector_assign_button = self._with_text(self._button[21], "Assign"),  //doesn't update text when giving back control
																			lock_button = self._with_text(self._button[28], "Mod Lock"),
																			))
																			#lock_button = self.elements.master_select_button,
																			#))
		self.modhandler.alt_layer = AddLayerMode( self.modhandler, Layer( priority = 7,
																			))
																			#key_buttons = self.elements.select_buttons))
																			#key_buttons = self.elements.track_state_buttons))
		self._device_provider.restart_mod()
		self._modHandle = SpecialModControl(modscript = self, monomodular = self.monomodular, name = 'ModHandle')
		self._update_modswitcher.subject = self.monomodular


	def _setup_main_modes(self):

		self._view_modes = ModesComponent(name = 'ViewModes')
		self._view_modes.add_mode('Full', [self.send_view_mode])
		self._view_modes.add_mode('Half', [self.send_view_mode])
		self._view_modes.add_mode('Quarter', [self.send_view_mode])
		self._view_modes.add_mode('Piano', [self.send_view_mode])
		self._view_modes.add_mode('SplitPiano', [self.send_view_mode])
		self._view_modes.add_mode('Skin', [self.send_view_mode])
		self._view_modes.add_mode('Mira', [self.send_view_mode])
		self._view_modes.add_mode('Tall', [self.send_view_mode])
		self._view_modes.add_mode('Wide', [self.send_view_mode])
		self._view_modes.add_mode('Dial', [self.send_view_mode])
		self._view_modes.add_mode('Mixer', [self.send_view_mode])
		self._view_modes.add_mode('Sequencer', [self.send_view_mode])
		self._view_modes.selected_mode = 'Half'
		self._view_modes.set_enabled(True)

		self._modswitcher = ModesComponent(name = 'ModSwitcher')
		self._modswitcher.add_mode('disabled', [])
		self._modswitcher.add_mode('mod', [self.modhandler, ])
		# self._modswitcher.add_mode('audiolooper', [self._audiolooper])
		self._modswitcher.add_mode('instrument', [self._instrument])
		self._modswitcher.add_mode('piano', [self._piano_group])
		self._modswitcher.selected_mode = 'disabled'
		self._modswitcher.set_enabled(False)

		#sends sysex to change grid view in app, keeps track of grid assignments
		self._modgrid_view_modes = ModesComponent(name = 'GridModes')
		self._modgrid_view_modes.add_mode('Compact', [self.turn_off_full_grid])
		self._modgrid_view_modes.add_mode('Full', [self.turn_on_full_grid],)
		self._modgrid_view_modes.layer = Layer(priority=6, cycle_mode_button=self._with_alt_latch(control=self._button[3], text='GridMode'))
		self._modgrid_view_modes.selected_mode = 'Compact'
		self._modgrid_view_modes.set_enabled(True)

		self._device_selector_modes = ModesComponent(name = 'DeviceSelectorModes')
		self._device_selector_modes.add_mode('disabled', [])
		self._device_selector_modes.add_mode('DeviceSelector', [self._device_selector.main_layer])
		self._device_selector_modes.layer = Layer(priority=6, cycle_mode_button=self._deviceMode)
		self._device_selector_modes.selected_mode = 'disabled'
		self._device_selector_modes.set_enabled(True)

		#16x16 view, not used atm
		self._main_modes = ModesComponent(name = 'MainModes')
		self._main_modes.add_mode('disabled', [])

		self._main_modes.add_mode('Main', [self._modswitcher,
											self._recorder,
											self._device,
											self._device_navigation,
											self._parameter_provider,
											self._master_select])
		# self._main_modes.add_mode('Main', [self._modswitcher])
		# self._main_modes.add_mode('Mod', [self.modhandler, self._device, self._device_navigation, self._session_ring, self._transport, self._view_control, self._undo_redo, self._track_creator, self._mixer, self._mixer._selected_strip, self._session, self._session_navigation, self._autoarm])
		# self._main_modes.selected_mode = 'disabled'
		# self._main_modes.layer = Layer(Main_button = self._button[44], Mod_button = self._button[45])
		self._main_modes.set_enabled(False)

		#changes encoders and corresponding button assignments
		self._encoder_modes = ModesComponent(name = 'EncoderModes')
		self._encoder_modes.add_mode('Device', [self._device, self._device.main_layer, self._mixer])
		self._encoder_modes.add_mode('Mixer', [self._device, self._mixer, self._mixer.volume_layer, self._mixer.pan_layer, self._mixer.mute_layer])
		self._encoder_modes.add_mode('Sends', [self._device, self._device.half_layer, self._mixer, self._mixer.sends_layer, self._mixer.send_navigation.scroll_layer])
		self._encoder_modes.add_mode('Track', [self._device, self._device.half_layer, self._mixer, self._mixer._selected_strip.all_sends_layer])
		self._encoder_modes.add_mode('Hybrid', [self._device, self._device.half_layer, self._mixer, self._mixer.hybrid_send_layer, self._mixer.hybrid_return_layer])
		self._encoder_modes.selected_mode = 'Device'
		self._encoder_modes.layer = Layer(priority = 6,
			Device_button = self._button[21], 
			Mixer_button = self._button[22], 
			Sends_button = self._button[23], 
			Track_button = self._button[24], 
			Hybrid_button = self._button[25])
		self._button[21]._display.set_data_sources([DisplayDataSource("Device")])
		self._button[22]._display.set_data_sources([DisplayDataSource("Mixer")])
		self._button[23]._display.set_data_sources([DisplayDataSource("Sends")])
		self._button[24]._display.set_data_sources([DisplayDataSource("Track")])
		self._button[25]._display.set_data_sources([DisplayDataSource("Track/Return")])
		self._encoder_modes.set_enabled(False)

		#manages different modes that grid can be used for
		self._grid_modes = ModesComponent(name = 'GridModes')
		self._grid_modes.add_mode('Piano', [self._piano_group, self._session, self._session.delete_layer, self._update_view])
		self._grid_modes.add_mode('Instrument', [self._modswitcher, self._session, self._session.delete_layer, self._update_view])
		self._grid_modes.add_mode('Session', [self._session, 
			self._session.launch_layer,
			 self._session.delete_layer, 
			 self._session.scene_layer, 
			 self._update_view])
		self._grid_modes.selected_mode = 'Instrument'
		self._grid_modes.layer = Layer(priority = 6, 
			Instrument_button = self._with_text(self._button[28], 'Instrument'),
			Session_button = self._with_text(self._button[29], 'Session'), 
			Piano_button = self._with_alt_latch(control=self._button[28], text='Piano'))
		self._button[28]._display.set_data_sources([DisplayDataSource("Instrument")])
		self._button[29]._display.set_data_sources([DisplayDataSource("Session")])
		self._grid_modes.set_enabled(False)

		#mixer hybrid view
		self._full_modes = ModesComponent(name = 'FullModes')
		self._full_modes.add_mode('disabled', [])
		self._full_modes.add_mode('Main', [self._background,
											self._master_select,
											self._mixer,
											self._mixer._selected_strip,
											self._mixer._master_strip,
											self._mixer.prehear_layer,
											self._grid_modes,
											self._encoder_modes,
											self._recorder,
											self._device_navigation,
											self._parameter_provider,
											self._session_ring,
											self._transport,
											self._view_control,
											self._undo_redo,
											self._track_creator,
											self._session_navigation,
											self._autoarm,
											self._device_deleter,
											self._device_selector_modes,
											self._hotswap,
											self._modgrid_view_modes],
											behaviour = LatchingShiftedBehaviour(color = 'MainModes.Full'))

		# self._full_modes.layer = Layer(priority = 7, Main_button=self._shift)
		self._full_modes.selected_mode = "Main"
		self._full_modes.set_enabled(False)

		self._global_modes = ModesComponent(name = "GlobalModes")
		# self._global_modes.add_mode("Main", [self._main_modes])
		self._global_modes.add_mode("Full", [self._full_modes])
		self._global_modes.selected_mode = "Full"
		self._global_modes.set_enabled(False)


	def _with_shift(self, control = None, text = ""):
		return DisplayingComboElement(control, text, modifier=self._shift)

	def _with_shift_latch(self, control = None, text = ""):
		# if is_iterable(control):
		# 	return ButtonMatrixElement(rows = [[DisplayingComboElement(item, text, modifier = self._shiftMode) for item in control._orig_buttons]])
		# else:
		return DisplayingComboElement(control, text, modifier=self._shiftMode)


	def _with_alt(self, control = None, text = ""):
		return DisplayingComboElement(control, text, modifier=self._alt)

	def _with_alt_latch(self, control = None, text = ""):
		return DisplayingComboElement(control, text, modifier=self._altMode)

	def _with_text(self, control, text):
		return DisplayingButtonWrapper(control, text)

	def _with_sends_latch(self, control = None, text = ""):
		return DisplayingComboElement(control, text, modifier=self._sendMode)

	def _with_device_text_latch(self, control = None, text = ""):
		return DisplayingComboElement(control, text, modifier=self._deviceMode)

	def _with_device_latch(self, control = None):
		return ComboElement(control, modifier=self._deviceMode)




	def _can_auto_arm_track(self, track):
		routing = track.current_input_routing
		return routing == 'Ext: All Ins' or routing == 'All Ins'
		# return False


	def _setup_monobridge(self):
		# self._monobridge = MonoBridgeElement(self)
		# self._monobridge.name = 'MonoBridge'
		self._monobridge = None


	@listens('device')
	def _on_device_changed(self):
		self.schedule_message(1, self._update_modswitcher)
		debug('ModGrid on_device_changed')
		self._update_modswitcher()


	def _on_selected_track_changed(self):
		super(ModGrid, self)._on_selected_track_changed()
		if not len(self.song.view.selected_track.devices):
			self._update_modswitcher()
		#self.schedule_message(1, self._update_modswitcher)


	def disconnect(self):
		# for script in self._connected_scripts:
		# 	if hasattr(script, '_disconnect_mod'):
		# 		script._disconnect_mod()
		super(ModGrid, self).disconnect()
		self._close_log()


	def restart_monomodular(self):
		#self.log_message('restart monomodular')
		self.modhandler.disconnect()
		with self.component_guard():
			self._setup_mod()


	def refresh_state(self):
		super(ModGrid, self).refresh_state()
		debug('_update_view')
		self.send_view_mode()


	def process_midi_bytes(self, midi_bytes, midi_processor):
		"""
		Finds the right recipient for the MIDI message and translates it into the
		expected format. The result is forwarded to the midi_processor.
		"""
		# debug('message:', midi.pretty_print_bytes(midi_bytes))
		if midi.is_sysex(midi_bytes):
			debug('sysex in:', midi_bytes)
			if midi_bytes == (240, 0, 1, 97, 93, 93, 9, 247):
				debug('asking for update...')
				self.refresh_state()
			# elif midi_bytes == (240, 0, 1, 97, 93, 93, 10, 247):
			# 	debug('asking for update...')
			# 	self._main_modes.selected_mode = "Full"
			# elif midi_bytes == (240, 0, 1, 97, 93, 93, 11, 247):
			# 	debug('asking for update...')
			# 	self._main_modes.selected_mode = "Main"
			else:
				debug('nope', type(bytes))

		if midi.is_sysex(midi_bytes):
			result = self.get_registry_entry_for_sysex_midi_message(midi_bytes)
			if result is not None:
				identifier, recipient = result
				midi_processor(recipient, midi_bytes[len(identifier):-1])
			#elif self.received_midi_listener_count() == 0:
			#	logger.warning(u'Got unknown sysex message: ' + midi.pretty_print_bytes(midi_bytes))
		else:
			recipient = self.get_recipient_for_nonsysex_midi_message(midi_bytes)
			if recipient is not None:
				# debug('recipient:', recipient.name if hasattr(recipient, 'name') else '', midi.pretty_print_bytes(midi_bytes) )
				# debug('recipient data', recipient._msg_channel, recipient._msg_identifier)
				midi_processor(recipient, midi.extract_value(midi_bytes))
			#elif self.received_midi_listener_count() == 0:
			#	logger.warning(u'Got unknown message: ' + midi.pretty_print_bytes(midi_bytes))


	@listens('mods')
	def _update_modswitcher(self):
		debug('update modswitcher, mod is:', self.modhandler.active_mod())
		if self.modhandler.active_mod():
			if not self._modswitcher.selected_mode == 'mod':
				self._modswitcher.selected_mode = 'mod'
		else:
			# self._modswitcher.selected_mode = 'audiolooper'
			if not self._modswitcher.selected_mode == 'instrument':
				self._modswitcher.selected_mode = 'instrument'
		# self._update_mod_special_mode(mode = self.modhandler.special_mode_index)


	# @listens('special_mode_index')
	# def _update_mod_special_mode(self, mode=0, force=False, *a):
	# 	# mode = self.modhandler.special_mode_index
	# 	# if force or self._grid_modes.selected_mode is 'Instrument':
	# 	# 	self._sysex.send('set_skin_view', [mode, mode, mode])
	# 	# debug('update_mod_special_mode', mode)
	# 	pass


	def _view_to_sysex(self, value):
		if value in MOD_VIEWS:
			return  MOD_VIEWS[value]
		return DEFAULT_MOD_VIEW


	@listens('view')
	def _update_view(self, *a, **k):
		view = 'Half'
		if self._grid_modes.selected_mode is 'Piano':
			view = 'Piano'
		elif self._grid_modes.selected_mode is 'Session':
			view = 'Half'
		elif self._modswitcher.selected_mode is 'mod':
			view = self.modhandler.view if self.modhandler.view in MOD_VIEWS else 'Full'
		# self._sysex.send('set_view', [self._view_to_sysex(view)])
		self._view_modes.selected_mode = view


	def send_view_mode(self):
		view = self._view_modes.selected_mode
		self._sysex.send('set_view', [self._view_to_sysex(view)])


	def _translate_char(self, char_to_translate):
		result = 63
		if char_to_translate in self._translation_table.keys():
			result = self._translation_table[char_to_translate]
		else:
			result = self._translation_table['?']
		return result


	def _translate_string(self, string):
		return list(map(self._translate_char, string))


	@listens('mira_address')
	def _update_mira_address(self, *a, **k):
		address = self.modhandler.mira_address
		debug('ModGrid._update_mira_address:', address)
		if not address is None:
			self._sysex.send('set_mira_address', self._translate_string(address))


	# @listens('mira_view')
	# def _update_mira_view(self, *a, **k):
	# 	value = self.modhandler.mira_view if (self._modswitcher.selected_mode == 'mod' and self._grid_modes.selected_mode == 'Instrument') else False
	# 	# debug('ModGrid._update_mira_view:', value)
	# 	val = 1 if value else 0
	# 	self._sysex.send('set_mira_view', [val, val, val])



	# def _send_instrument_shifted(self):
	# 	# self._instrument.is_enabled() and self._instrument._on_shift_value(1)
	# 	# self.modhandler.is_enabled() and self.modhandler._shift_value(1)
	# 	pass
	#
	#
	# def _send_instrument_unshifted(self):
	# 	# self._instrument.is_enabled() and self._instrument._on_shift_value(0)
	# 	# self.modhandler.is_enabled() and self.modhandler._shift_value(0)
	# 	pass

	#this is an override of the original element to deal with MPE channel spanning.  
	# def _install_forwarding(self, midi_map_handle, control, forwarding_type=ScriptForwarding.exclusive):
	# 	success = False
	# 	should_consume_event = forwarding_type == ScriptForwarding.exclusive
	# 	if control.message_type() == MIDI_NOTE_TYPE:
	# 		#we are mapping mulitple channels of the same id to forward to the script in case of an mpe control element
	# 		if hasattr(control, "IS_MPE") and control.IS_MPE:
	# 			success = True
	# 			local_success = False
	# 			span = control.MPE_CHANNEL_SPAN
	# 			for channel in range(control.message_channel(), min(15, control.message_channel()+int(span))):
	# 				try:
	# 					# local_success = Live.MidiMap.forward_midi_note(self._c_instance.handle(), midi_map_handle, int(channel), control.message_identifier(), False)
	# 					local_success = Live.MidiMap.forward_midi_note(self._c_instance.handle(), midi_map_handle, int(channel), control.message_identifier(), should_consume_event)
	# 				except:
	# 					debug('local_success failed:', channel, control.message_identifier())
	# 				if not local_success:
	# 					debug('local_success failed:', channel, control.message_identifier())
	# 					success = False
	# 		else:
	# 			success = Live.MidiMap.forward_midi_note(self._c_instance.handle(), midi_map_handle, control.message_channel(), control.message_identifier(), should_consume_event)
	# 			if not success:
	# 				debug('success failed:', control.message_channel(), control.message_identifier())
	# 	elif control.message_type() == MIDI_CC_TYPE:
	# 		success = Live.MidiMap.forward_midi_cc(self._c_instance.handle(), midi_map_handle, control.message_channel(), control.message_identifier(), should_consume_event)
	# 	elif control.message_type() == MIDI_PB_TYPE:
	# 		success = Live.MidiMap.forward_midi_pitchbend(self._c_instance.handle(), midi_map_handle, control.message_channel())
	# 	else:
	# 		success = True
	# 	if success:
	# 		#we are assigning mutliple channels of the same id to a single control in the registry in case of an mpe control element
	# 		if hasattr(control, "IS_MPE") and control.IS_MPE:
	# 			forwarding_keys = control.mpe_identifier_bytes()
	# 		else:
	# 			forwarding_keys = control.identifier_bytes()
	# 		for key in forwarding_keys:
	# 			registry = self._forwarding_registry if control.message_type() != MIDI_SYSEX_TYPE else self._forwarding_long_identifier_registry
	# 			registry[key] = control

	# 	return success

	# def _install_forwarding(self, midi_map_handle, control, forwarding_type=ScriptForwarding.exclusive, channel=None):
	# 	success = False
	# 	should_consume_event = forwarding_type == ScriptForwarding.exclusive
	# 	actual_channel = channel if not channel is None else control.message_channel()
	# 	if control.message_type() == MIDI_NOTE_TYPE:
	# 		# debug('FORWARD:', actual_channel, control.name if hasattr(control, 'name') else control)
	# 		success = Live.MidiMap.forward_midi_note(self._c_instance.handle(), midi_map_handle, actual_channel, control.message_identifier(), should_consume_event)
	# 	elif control.message_type() == MIDI_CC_TYPE:
	# 		success = Live.MidiMap.forward_midi_cc(self._c_instance.handle(), midi_map_handle, actual_channel, control.message_identifier(), should_consume_event)
	# 	elif control.message_type() == MIDI_PB_TYPE:
	# 		success = Live.MidiMap.forward_midi_pitchbend(self._c_instance.handle(), midi_map_handle, actual_channel)
	# 	else:
	# 		success = True
	# 	if success:
	# 		forwarding_keys = control.identifier_bytes()
	# 		for key in forwarding_keys:
	# 			registry = self._forwarding_registry if control.message_type() != MIDI_SYSEX_TYPE else self._forwarding_long_identifier_registry
	# 			registry[key] = control

	# 	return success

	# def connect_script_instances(self, instanciated_scripts):
	# 	debug('connect_script_instances', instanciated_scripts)
	# 	self._connected_scripts = []
	# 	for script in instanciated_scripts:
	# 		# debug(script)
	# 		if  isinstance (script, Launchpad_MK2):
	# 			self._connected_scripts.append(script)
	# 			self._on_lp2_mode_changed.subject = script._modes
	# 			if not hasattr(script, '_modified') or (hasattr(script, '_modified') and not script._modified):
	# 				script.setup_mod = _Launchpad_MK2_setup_mod
	# 				script.schedule_message(1, script.setup_mod, [script, self])
	# 		elif  isinstance (script, Launchpad_Pro):
	# 			self._connected_scripts.append(script)
	# 			self._on_lppro_mode_changed.subject = script._note_modes
	# 			if not hasattr(script, '_modified') or (hasattr(script, '_modified') and not script._modified):
	# 				script.setup_mod = _Launchpad_Pro_setup_mod
	# 				script.schedule_message(1, script.setup_mod, [script, self])
	# 		elif  isinstance (script, Launchpad):
	# 			self._connected_scripts.append(script)
	# 			# self._on_lppro_mode_changed.subject = script._note_modes
	# 			if not hasattr(script, '_modified') or (hasattr(script, '_modified') and not script._modified):
	# 				script.setup_mod = _Launchpad_setup_mod
	# 				script.schedule_message(1, script.setup_mod, [script, self])
	# 	debug('connected_scripts:', self._connected_scripts)


	# @listens('selected_mode')
	# def _on_lp2_mode_changed(self, mode):
	# 	debug('_on_lp2_mode_changed', mode)

	# @listens('selected_mode')
	# def _on_lppro_mode_changed(self, mode):
	# 	debug('_on_lppro_mode_changed', mode)

	# @listens_group("text")
	# def on_button_text_changed(self, *a, **k):
	# 	#debug('text changed:', a, k)
	# 	pass


	# def _do_send_midi(self, midi_event_bytes):
	# 	super(ModGrid, self)._do_send_midi(midi_event_bytes)
	# 	bytes = list(midi_event_bytes)
	# 	self.notify_pipe('midi', *bytes)


	# def receive_note(self, num, val, chan=0):
	# 	# debug('receive_note', num, val)
	# 	self.receive_midi(tuple([144+chan, num, val]))


	# def receive_cc(self, num, val, chan=0):
	# 	# debug('receive_cc', num, val)
	# 	self.receive_midi(tuple([176+chan, num, val]))


	# def _setup_modswitcher(self):
	# 	self._modswitcher = ModesComponent(name = 'ModSwitcher')
	# 	self._modswitcher.add_mode('mod', [self.modhandler])
	# 	self._modswitcher.selected_mode = 'mod'
	# 	self._modswitcher.set_enabled(True)


	# def flash(self):
	# 	if(self.flash_status > 0):
	# 		for control in self.controls:
	# 			if isinstance(control, MonoButtonElement):
	# 				control.flash(self._timer)


	# def update_display(self):
	# 	super(ControlSurface, self).update_display()
	# 	self._timer = (self._timer + 1) % 256
	# 	self.flash()


	# def touched(self):
	# 	if self._touched is 0:
	# 		self._monobridge._send('touch', 'on')
	# 		self.schedule_message(2, self.check_touch)
	# 	self._touched +=1


	# def check_touch(self):
	# 	if self._touched > 5:
	# 		self._touched = 5
	# 	elif self._touched > 0:
	# 		self._touched -= 1
	# 	if self._touched is 0:
	# 		self._monobridge._send('touch', 'off')
	# 	else:
	# 		self.schedule_message(2, self.check_touch)


