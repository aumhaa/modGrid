# by amounra 0524 : http://www.aumhaa.com
# written against Live 12.0.5b3 on 052524
# version b7.0

import Live
from math import *
from itertools import chain, starmap
from functools import partial
from ableton.v2.control_surface import Component, ClipCreator, Layer
from ableton.v2.control_surface.components import SessionRingComponent, SessionComponent, ViewControlComponent, PlayableComponent, DrumGroupComponent
from ableton.v2.base import listens, listens_group, forward_property, find_if, first, in_range, product, clamp, listenable_property, liveobj_changed
from ableton.v2.control_surface.elements import ButtonElement, ButtonMatrixElement, DisplayDataSource
from ableton.v2.control_surface.mode import ModesComponent, AddLayerMode, LayerMode, ModeButtonBehaviour
from ableton.v2.base.task import *
from ableton.v2.control_surface.components.session_recording import *
from ableton.v2.base import task
from ableton.v2.control_surface.control import control_list, ButtonControl, StepEncoderControl, ToggleButtonControl, control_color, PlayableControl, control_matrix
from ableton.v2.control_surface.percussion_instrument_finder import PercussionInstrumentFinder as DrumGroupFinderComponent, find_drum_group_device
from ableton.v2.control_surface.elements.proxy_element import ProxyElement


from pushbase.step_seq_component import StepSeqComponent
#from pushbase.percussion_instrument_finder import PercussionInstrumentFinder as DrumGroupFinderComponent, find_drum_group_device
from pushbase.note_editor_component import NoteEditorComponent
from pushbase.loop_selector_component import LoopSelectorComponent
from pushbase.playhead_component import PlayheadComponent
from pushbase.grid_resolution import GridResolution
from pushbase.pad_control import PadControl
# from Push2.colors import IndexedColor
from pushbase.colors import LIVE_COLORS_TO_MIDI_VALUES, RGB_COLOR_TABLE


from aumhaa.v3.control_surface.mono_modes import CancellableBehaviour, CancellableBehaviourWithRelease
from aumhaa.v3.control_surface.components.channelized_settings import ChannelizedSettingsBase, ScrollingChannelizedSettingsComponent, ToggledChannelizedSettingsComponent, TaggedSettingsComponent
from aumhaa.v3.control_surface.components.mono_keygroup import MonoKeyGroupComponent
from aumhaa.v3.control_surface.components.mono_drumgroup import MonoDrumGroupComponent
from aumhaa.v3.control_surface.instrument_consts import *
from aumhaa.v3.base import initialize_debug
from .Map import *

LOCAL_DEBUG = False
debug = initialize_debug(local_debug=LOCAL_DEBUG)


def is_triplet_quantization(triplet_factor):
	return triplet_factor == 0.75


def song():
	return Live.Application.get_application().get_document()


def get_instrument_type(track, scale, settings):
	instrument_type = 'keypad'
	if scale is 'Auto':
		for device in track.devices:
			if isinstance(device, Live.Device.Device):
				if device.class_name == 'DrumGroupDevice':
					instrument_type = 'drumpad'
					break
	elif scale is 'DrumPad' or settings['DefaultAutoScale'] is 'DrumPad':
		instrument_type = 'drumpad'
	return instrument_type


def find_nearest_color(rgb_table, src_hex_color):

	def hex_to_channels(color_in_hex):
		return (
		 (color_in_hex & 16711680) >> 16,
		 (color_in_hex & 65280) >> 8,
		 color_in_hex & 255)

	def squared_distance(color):
		return sum([(a - b) ** 2 for a, b in zip(hex_to_channels(src_hex_color), hex_to_channels(color[1]))])

	return min(rgb_table, key=squared_distance)[0]


class ShiftCancellableBehaviourWithRelease(CancellableBehaviour):


	def release_delayed(self, component, mode):
		component.pop_mode(mode)


	def update_button(self, component, mode, selected_mode):
		pass


class OffsetTaggedSetting(TaggedSettingsComponent, ScrollingChannelizedSettingsComponent):


	_set_attribute_tag_model = lambda self, a: int(a)


class ScaleTaggedSetting(TaggedSettingsComponent, ScrollingChannelizedSettingsComponent):


	_set_attribute_tag_model = lambda self, a: str(a)


class ToggledTaggedSetting(TaggedSettingsComponent, ChannelizedSettingsBase):


	_set_attribute_tag_model = lambda self, a: str(a)

	split_toggle = ToggleButtonControl(toggled_color = 'MonoInstrument.SplitModeOnValue', untoggled_color = 'DefaultButton.Off')
	seq_toggle = ToggleButtonControl(toggled_color = 'MonoInstrument.SequencerModeOnValue', untoggled_color = 'DefaultButton.Off')

	def __init__(self, *a, **k):
		super(ToggledTaggedSetting, self).__init__(value_dict = ['none', 'seq', 'split',], *a, **k)


	@split_toggle.toggled
	def split_toggle(self, toggled, button):
		self.value = 'none' if self.value == 'split' else 'split'
		self.update()


	@seq_toggle.toggled
	def seq_toggle(self, toggled, button):
		self.value = 'none' if self.value == 'seq' else 'seq'
		self.update()


	def _update_controls(self):
		self.split_toggle.is_toggled = bool(self.value is 'split')
		self.seq_toggle.is_toggled = bool(self.value is 'seq')


class SpecialNullPlayhead(object):
	notes = []
	start_time = 0.0
	step_length = 1.0
	velocity = 127.0
	wrap_around = False
	track = None
	clip = None
	set_feedback_channels = nop
	set_buttons = nop
	_last_step_index = 0


class Playhead(Component):

	def __init__(self, *a, **k):
		super(Playhead, self).__init__(*a, **k)
		self._notes = []
		self._start_time = 0.0
		self._step_length = 1.0
		self._velocity = 127.0
		self._wrap_around = False
		self._track = None
		self._clip = None
		self.set_feedback_channels = nop
		self._last_step_index = -1
		self._buttons = None
		self._used_buttons = []

	@property
	def notes(self):
		return self._notes

	@notes.setter
	def notes(self, val):
		self._notes = val
		# debug('playhead notes are now:', self._notes)
		self.update_used_buttons()

	def update_used_buttons(self):
		# if not self._used_buttons is None:
		# 	for button in self._used_buttons:
		# 		button.unflash_playhead()
		if not self._buttons is None and not self._notes is None:
			self._used_buttons = sorted(filter(lambda button: button._msg_identifier in self._notes, self._buttons), key=lambda button: self._notes.index(button._msg_identifier))
		else:
			self._used_buttons = None



	@property
	def clip(self):
		return self._clip

	@clip.setter
	def clip(self, clip):
		self._clip = clip
		self._on_clip_playing_position_changed.subject = clip
		debug('playhead clip is now:', self._clip)


	# @listens('playing_position')
	# def _on_clip_playing_position_changed(self):
	# 	if not self._buttons is None:
	# 		position = liveobj_valid(self._clip) and self._clip.playing_position
	# 		step_index = floor((position-self._start_time)/self._step_length)
	# 		buttons_length = len(self._buttons)
	# 		# debug('buttons_length:', buttons_length, 'step_index:', step_index)
	# 		# if (step_index != self._last_step_index) and (step_index < buttons_length) and (step_index > 0):
	# 		if (step_index != self._last_step_index):
	# 			if (step_index < buttons_length):
	# 				# debug('start_time:', self._start_time)
	# 				last_button = self._buttons[self._last_step_index] if len(self._buttons) >self._last_step_index else None
	# 				# debug('last_step_index:', self._last_step_index, 'last_button', last_button)
	# 				last_button != None and last_button.unflash_playhead()
	# 				button = None
	# 				if step_index < len(self._buttons):
	# 					button = self._buttons[step_index]
	# 				# button = self._buttons[step_index] if step_index < len(self._buttons) else None
	# 				# debug('step_index:', step_index, 'button', button)
	# 				# button != None and button.flash_playhead(self.velocity)
	# 				button != None and button.flash_playhead(color=5)
	# 				self._last_step_index = step_index
	# 			elif self._last_step_index > -1:
	# 				last_button = self._buttons[self._last_step_index] if len(self._buttons) >self._last_step_index else None
	# 				last_button != None and last_button.unflash_playhead()
	# 				self._last_step_index = -1

	@listens('playing_position')
	def _on_clip_playing_position_changed(self):
		if not self._used_buttons is None:
			position = liveobj_valid(self._clip) and self._clip.playing_position
			step_index = floor((position-self._start_time)/self._step_length)
			buttons_length = len(self._used_buttons)
			# debug('buttons_length:', buttons_length, 'step_index:', step_index)
			# if (step_index != self._last_step_index) and (step_index < buttons_length) and (step_index > 0):
			if (step_index != self._last_step_index):
				if (step_index < buttons_length):
					# debug('start_time:', self._start_time)
					last_button = self._used_buttons[self._last_step_index] if len(self._used_buttons) >self._last_step_index else None
					# debug('last_step_index:', self._last_step_index, 'last_button', last_button)
					last_button != None and last_button.unflash_playhead()
					button = None
					if step_index < len(self._used_buttons):
						button = self._used_buttons[step_index]
					# button = self._buttons[step_index] if step_index < len(self._buttons) else None
					# debug('step_index:', step_index, 'button', button)
					# button != None and button.flash_playhead(self.velocity)
					button != None and button.flash_playhead(color=5)
					self._last_step_index = step_index
				elif self._last_step_index > -1:
					last_button = self._used_buttons[self._last_step_index] if len(self._used_buttons) >self._last_step_index else None
					last_button != None and last_button.unflash_playhead()
					self._last_step_index = -1

			# debug('playing position is:', position, step_index)

	@property
	def track(self):
		return self._track

	@track.setter
	def track(self, track):
		self._track = track
		# debug('playhead track is now:', self._track)

	@property
	def start_time(self):
		return self._start_time

	@start_time.setter
	def start_time(self, start_time):
		self._start_time = start_time
		# debug('playhead start_time is now:', self._start_time)

	@property
	def step_length(self):
		return self._step_length

	@step_length.setter
	def step_length(self, step_length):
		self._step_length = step_length
		# debug('playhead step_length is now:', self._step_length)

	@property
	def velocity(self):
		return self._velocity

	@velocity.setter
	def velocity(self, velocity):
		self._velocity = velocity
		# debug('playhead velocity is now:', self._velocity)

	@property
	def wrap_around(self):
		return self._wrap_around

	@wrap_around.setter
	def wrap_around(self, wrap_around):
		self._wrap_around = wrap_around
		# debug('playhead wrap_around is now:', self._wrap_around)

	def set_buttons(self, buttons):
		#debug('set buttons:', buttons)
		# if self._buttons:
		# 	self._buttons.reset()
		# debug('set_buttons:', buttons)
		if not buttons is None:
			# debug('not none')
			self._buttons = [button for row in buttons._orig_buttons for button in row]
		else:
			self._buttons = None
		self.update_used_buttons()

#we only override this because we need to inject the SpecialNullPlayhead as the proxied interface
class SpecialPlayheadElement(ProxyElement, Component):

	def __init__(self, playhead = None, *a, **k):
		super(SpecialPlayheadElement, self).__init__(proxied_object=playhead, proxied_interface = SpecialNullPlayhead())

	def reset(self):
		self.track = None





# """We need to add an extra mode to the instrument to deal with session shifting, thus the _matrix_modes and extra functions."""
# """We also set up the id's for the note_editor here"""
# """We also make use of a shift_mode instead of the original shift mode included in the MonoInstrument so that we can add a custom behaviour locking behaviour to it"""
#
# class ModGridMonoInstrumentComponent(MonoInstrumentComponent):
#
#
# 	def __init__(self, *a, **k):
# 		self._matrix_modes = ModesComponent(name = 'MatrixModes')
# 		super(ModGridMonoInstrumentComponent, self).__init__(*a, **k)
# 		self._playhead_component = SpecialPlayheadComponent(parent=self, grid_resolution=self._grid_resolution, paginator=self.paginator, follower=self._loop_selector, notes=chain(*starmap(range, ((4, 8),
# 		 (12, 16),
# 		 (20, 24),
# 		 (28, 32)))), triplet_notes=chain(*starmap(range, ((4, 7),
# 		 (12, 15),
# 		 (20, 23),
# 		 (28, 31)))), feedback_channels=[15])
# 		self._playhead_component.set_follower(self._loop_selector)
# 		self._loop_selector.follow_detail_clip = True
# 		self._loop_selector._on_detail_clip_changed.subject = self.song.view
# 		self._update_delay_task = self._tasks.add(task.sequence(task.wait(.1), task.run(self._update_delayed)))
# 		self._update_delay_task.kill()
		# self._keypad._note_sequencer._playhead_component._notes=tuple(range(0, 32))
		# self._keypad._note_sequencer._playhead_component._triplet_notes=tuple(range(0, 28))
		# self._keypad._note_sequencer._note_editor._visible_steps_model = lambda indices: [k for k in indices if k % 16 not in (13, 14, 15, 16, 29, 30, 31, 32)]
		# self._drumpad._step_sequencer._playhead_component._notes=tuple(range(0, 32))
		# self._drumpad._step_sequencer._playhead_component._triplet_notes=tuple(range(0, 28))
		# self._drumpad._step_sequencer._note_editor._visible_steps_model = lambda indices: [k for k in indices if k % 16 not in (13, 14, 15, 16, 29, 30, 31, 32)]
		# self._matrix_modes.add_mode('disabled', [DelayMode(self.update, delay = .1, parent_task_group = self._parent_task_group)])
		# self._matrix_modes.add_mode('enabled', [DelayMode(self.update, delay = .1, parent_task_group = self._parent_task_group)], behaviour = DefaultedBehaviour())
		# self._matrix_modes._last_selected_mode = 'enabled'
		# self._matrix_modes.selected_mode = 'disabled'
		#
		# self.set_session_mode_button = self._matrix_modes.enabled_button.set_control_element



	# def _setup_shift_mode(self):
	# 	self._shifted = False
	# 	self._shift_mode = ModesComponent()
	# 	self._shift_mode.add_mode('shift', tuple([lambda: self._on_shift_value(True), lambda: self._on_shift_value(False)]), behaviour = ColoredCancellableBehaviourWithRelease(color = 'MonoInstrument.ShiftOn', off_color = 'MonoInstrument.ShiftOff') if SHIFT_LOCK else BicoloredMomentaryBehaviour(color = 'MonoInstrument.ShiftOn', off_color = 'MonoInstrument.ShiftOff'))
	# 	self._shift_mode.add_mode('disabled', None)
	# 	self._shift_mode.selected_mode = 'disabled'


# 	def update(self):
# 		super(MonoInstrumentComponent, self).update()
# 		self._main_modes.selected_mode = 'disabled'
# 		if self.is_enabled():
# 			new_mode = 'disabled'
# 			drum_device = find_drum_group_device(self.song.view.selected_track)
# 			self._drumpad._drumgroup.set_drum_group_device(drum_device)
# 			cur_track = self.song.view.selected_track
# 			if cur_track.has_audio_input and cur_track in self.song.visible_tracks:
# 				new_mode = 'audioloop'
# 				if self._shifted:
# 					new_mode += '_shifted'
# 			elif cur_track.has_midi_input:
# 				scale, mode = self._scale_offset_component.value, self._mode_component.value
# 				new_mode = get_instrument_type(cur_track, scale, self._settings)
# 				if mode is 'split':
# 					new_mode += '_split'
# 				elif mode is 'seq':
# 					new_mode +=  '_sequencer'
# 				if self._shifted:
# 					new_mode += '_shifted'
# 				if self._matrix_modes.selected_mode is 'enabled':
# 					new_mode += '_session'
# 				self._script.set_feedback_channels([self._scale_offset_component.channel])
# 				self._script.set_controlled_track(self.song.view.selected_track)
# 			if new_mode in self._main_modes._mode_map or new_mode is None:
# 				self._main_modes.selected_mode = new_mode
# 				self._script.set_controlled_track(self.song.view.selected_track)
# 			else:
# 				self._main_modes.selected_mode = 'disabled'
# 				self._script.set_controlled_track(None)
# 			debug('monoInstrument mode is:', self._main_modes.selected_mode, '  inst:', self.is_enabled(), '  modes:', self._main_modes.is_enabled(), '   key:', self._keypad.is_enabled(), '   drum:', self._drumpad.is_enabled())
#
#
#
# """We need to override the update notification call in AutoArmComponent"""


class MonoStepSeqComponent(StepSeqComponent):


	def __init__(self, *a, **k):
		super(MonoStepSeqComponent, self).__init__(*a, **k)
		self._playhead_component = PlayheadComponent(parent=self, grid_resolution=self._grid_resolution, paginator=self.paginator, follower=self._loop_selector, notes=chain(*starmap(range, ((0, 8),
		 (8, 16),
		 (16, 24),
		 (24, 32)))), triplet_notes=chain(*starmap(range, ((0, 6),
		 (8, 12),
		 (16, 22),
		 (24, 30)))), feedback_channels=[15])
		self._loop_selector.follow_detail_clip = True
		self._loop_selector._on_detail_clip_changed.subject = self.song.view
		self._update_delay_task = self._tasks.add(task.sequence(task.wait(.1), task.run(self._update_delayed)))
		self._update_delay_task.kill()


	def update(self):
		"""We need to delay the update task, as on_detail_clip_changed (triggering set_detail_clip() in loopselector) causes all stored sequencer states to zero out while modes are switching"""
		super(StepSeqComponent, self).update()
		self._update_delay_task.restart()


	def _update_delayed(self):
		self._on_detail_clip_changed()
		self._update_playhead_color()
		self._update_delay_task.kill()


	def set_follow_button(self, button):
		#self._loop_selector.set_follow_button(button)
		pass


	def set_solo_button(self, button):
		debug('set_solo_button:', button, hasattr(self._instrument, 'set_solo_button'))
		hasattr(self._instrument, 'set_solo_button') and self._instrument.set_solo_button(button)


class MonoNoteEditorComponent(NoteEditorComponent):


	"""Custom function for displaying triplets for different grid sizes, called by _visible steps"""
	_visible_steps_model = lambda self, indices: [k for k in indices if k % 8 not in (7, 8)]
	#_matrix = None
	matrix = control_matrix(PadControl, channel=1, sensitivity_profile='loop', mode=PlayableControl.Mode.listenable)

	@matrix.pressed
	def matrix(self, button):
		super(MonoNoteEditorComponent, self)._on_pad_pressed(button.coordinate)

	@matrix.released
	def matrix(self, button):
		super(MonoNoteEditorComponent, self)._on_pad_released(button.coordinate)

	def _on_pad_pressed(self, coordinate):
		y, x = coordinate
		debug('MonoNoteEditorComponent._on_pad_pressed:', y, x)
		super(MonoNoteEditorComponent, self)._on_pad_pressed(coordinate)

	def _visible_steps(self):
		first_time = self.page_length * self._page_index
		steps_per_page = self._get_step_count()
		step_length = self._get_step_length()
		indices = list(range(steps_per_page))
		if is_triplet_quantization(self._triplet_factor):
			indices = self._visible_steps_model(indices)
		return [ (self._time_step(first_time + k * step_length), index) for k, index in enumerate(indices) ]


class ScaleSessionComponent(SessionComponent):


	_clip_launch_buttons = None

	def __init__(self, *a, **k):
		super(ScaleSessionComponent, self).__init__(*a, **k)
		self._session_ring._update_highlight = lambda : None


	def set_clip_launch_buttons(self, matrix):
		self._clip_launch_buttons = matrix
		if matrix:
			for button, (x,y) in matrix.iterbuttons():
				debug('session button is:', button)
				if button:
					button.display_press = False
					# button.set_off_value('DefaultButton.Off')
					button.reset()
					index = x + (y*matrix.width())
					scene = self.scene(index)
					slot = scene.clip_slot(0)
					slot.set_launch_button(button)
			#self._session_ring.update_highlight(ring.tracks_to_use(), ring.song.return_tracks)
		else:
			for x, y in product(range(self._session_ring.num_tracks), range(self._session_ring.num_scenes)):
				scene = self.scene(y)
				slot = scene.clip_slot(x)
				slot.set_launch_button(None)
		self._reassign_tracks()
		self._reassign_scenes()
		self.update()


	def update_current_track(self):
		#for some reason Live returns our tracks in reversed order....
		if self.is_enabled():
			track = self.song.view.selected_track
			track_list = [track for track in reversed(self._session_ring._tracks_to_use())]
			if track in track_list:
				self._session_ring.track_offset = abs(track_list.index(self.song.view.selected_track)-(len(track_list)-1))
			self.update()


	def update(self):
		super(ScaleSessionComponent, self).update()



class MPEPlayableControl(PlayableControl):

	class State(PlayableControl.State):

		def set_control_element(self, control_element):
			super(MPEPlayableControl.State, self).set_control_element(control_element)
			if hasattr(control_element, 'set_mpe_enabled'):
				control_element.set_mpe_enabled(True)


class SpecialMonoDrumGroupComponent(MonoDrumGroupComponent):
	TRANSLATION_CHANNEL = 15
	_clip_palette = LIVE_COLORS_TO_MIDI_VALUES
	_clip_rgb_table = RGB_COLOR_TABLE

	def _color_for_pad(self, pad):
		color = super(SpecialMonoDrumGroupComponent, self)._color_for_pad(pad)
		color = self._chain_color_for_pad(pad, color)
		return color

	def _chain_color_for_pad(self, pad, color):
		if color == 'DrumGroup.PadFilled' or color == 'DrumGroup.PadFilledAlt':
			color = self._color_value(pad.chains[0].color)
		# elif color == 'DrumGroup.PadMuted':
		# 	color = IndexedColor.from_live_index((pad.chains[0].color_index), shade_level=1)
		return color

	def _color_value(self, color):
		# debug('color_index:', color)
		try:
			return self._clip_palette[color]
		except (KeyError, IndexError):
			if self._clip_rgb_table is not None:
				return find_nearest_color(self._clip_rgb_table, color)
			else:
				return 'DrumGroup.PadFilled'


class SpecialMonoKeyGroupComponent(MonoKeyGroupComponent):
	#we use this to tell the special MPE elements that we want to set forwarding to none and translate everything on MPE channels spanning above original_channel of button
	TRANSLATION_CHANNEL = 15
	matrix = control_matrix(MPEPlayableControl)

	def _get_current_channel(self):
		# cur_track = self.song.view.selected_track
		# cur_chan = cur_track.current_input_sub_routing
		# if len(cur_chan) == 0:
		# 	cur_chan = 'All Channels'
		# if cur_chan == 'All Channels':
		# 	cur_chan = 1
		# if cur_chan in self._channel_list:
		# 	cur_chan = (self._channel_list.index(cur_chan)%15)+1
		# else:
		# 	cur_chan = 14
		# return cur_chan
		return self.TRANSLATION_CHANNEL

	def _note_translation_for_button(self, button):
		y, x = button.coordinate
		scale_len = len(self._scales[self._scale])
		note_pos = x + (abs((self.height-1)-y)*self._vertoffset)
		note = self._offset + self._scales[self._scale][note_pos%scale_len] + (12*int(note_pos/scale_len))
		channel = self.TRANSLATION_CHANNEL
		#we are shifting the channel forward so that this button won't interfere with other buttons that aren't being translated
		if button._control_element:
			channel = button._control_element._original_channel+1
		#translation channel should be completely overhauled in existing aumhaa framework, its only half implemented 
		return (note, channel)

	#need to remove a bunch of stuff, and make sure that reset_state resets MPE to off. Need to turn set forwarding to exclusive when mpe is enabled.
	def _set_matrix_special_attributes(self, enabled):
		#debug('set_matrix_special_attributes')
		# for button in self.matrix:
		# 	if button._control_element:
		# 		# button._control_element.display_press = enabled
		# 		# button._control_element._last_flash = 0
				
		# 		# if not enabled:
		# 		# 	button._control_element.reset_state()
		# 		# else:
		# 		try:
		# 			button._control_element.set_mpe_enabled(True)
		# 		except:
		# 			debug('button is not mpeElement')
		pass


class MonoScaleComponent(Component):


	_offset_settings_component_class = OffsetTaggedSetting

	def __init__(self, parent, control_surface, skin, grid_resolution, parent_task_group, settings = DEFAULT_INSTRUMENT_SETTINGS, *a, **k):
		super(MonoScaleComponent, self).__init__(*a, **k)
		debug('grid resolution is:', grid_resolution)
		self._settings = settings
		self._parent = parent
		self._control_surface = control_surface
		self._skin = skin
		self._grid_resolution = grid_resolution

		#self._vertical_offset_component = self.register_component(self._offset_settings_component_class(name = 'VerticalOffset', attribute_tag = 'vert_offset', parent_task_group = parent_task_group, value_dict = range(24), default_value_index = self._settings['DefaultVertOffset'], default_channel = 0, on_color = 'MonoInstrument.VerticalOffsetOnValue', off_color = 'MonoInstrument.VerticalOffsetOffValue'))
		self._vertical_offset_component = self._offset_settings_component_class(parent = self, name = 'VerticalOffset', attribute_tag = 'vert_offset', parent_task_group = parent_task_group, value_dict = list(range(24)), default_value_index = self._settings['DefaultVertOffset'], default_channel = 0, on_color = 'MonoInstrument.VerticalOffsetOnValue', off_color = 'MonoInstrument.VerticalOffsetOffValue')
		self._vertical_offset_value.subject = self._vertical_offset_component

		#self._offset_component = self.register_component(self._offset_settings_component_class(name = 'NoteOffset', attribute_tag = 'drum_offset', parent_task_group = parent_task_group, value_dict = range(112), default_value_index = self._settings['DefaultOffset'], default_channel = 0, bank_increment = 12, on_color = 'MonoInstrument.OffsetOnValue', off_color = 'MonoInstrument.OffsetOffValue'))
		self._offset_component = self._offset_settings_component_class(parent = self, name = 'NoteOffset', attribute_tag = 'drum_offset', parent_task_group = parent_task_group, value_dict = list(range(112)), default_value_index = self._settings['DefaultOffset'], default_channel = 0, bank_increment = 12, on_color = 'MonoInstrument.OffsetOnValue', off_color = 'MonoInstrument.OffsetOffValue')
		self._offset_value.subject = self._offset_component
		self.set_offset_shift_toggle = self._offset_component.shift_toggle.set_control_element

		self._keygroup = SpecialMonoKeyGroupComponent(settings = self._settings, channel_list = self._settings['Channels'])
		self.set_keypad_matrix = self._keygroup.set_matrix
		self.set_keypad_select_matrix = self._keygroup.set_select_matrix

		scale_clip_creator = ClipCreator()
		scale_note_editor = MonoNoteEditorComponent(clip_creator=scale_clip_creator, grid_resolution=grid_resolution)
		self._note_sequencer = MonoStepSeqComponent(parent = self, clip_creator=scale_clip_creator, skin=skin, grid_resolution=self._grid_resolution, name='Note_Sequencer', note_editor_component=scale_note_editor, instrument_component=self._keygroup )
		#self._note_sequencer._playhead_component._follower = self._note_sequencer._loop_selector  ##########pull this if everything works, it was a test
		self._note_sequencer._playhead_component._notes=tuple(chain(*starmap(range, ((0, 8), (16, 24), (32, 40), (48, 56)))))
		self._note_sequencer._playhead_component._triplet_notes=tuple(chain(*starmap(range, ((0, 6), (16, 22), (32, 38), (48, 54)))))
		# self._note_sequencer._playhead_component._feedback_channels = [15]
		self._note_sequencer._note_editor._visible_steps_model = lambda indices: [k for k in indices if k % 8 not in (6, 7)]
		self.set_playhead = self._note_sequencer.set_playhead
		self.set_loop_selector_matrix = self._note_sequencer.set_loop_selector_matrix
		self.set_quantization_buttons = self._note_sequencer.set_quantization_buttons
		self.set_follow_button = self._note_sequencer.set_follow_button
		self.set_sequencer_matrix = self._note_sequencer.set_button_matrix
		self.set_delete_button = self._note_sequencer.set_delete_button
		#self.register_component(self._note_sequencer)

		self.set_split_matrix = self._parent._selected_session.set_clip_launch_buttons


	@listens('value')
	def _vertical_offset_value(self, value):
		#debug('_vertical_offset_value', value)
		self._keygroup.vertical_offset = value
		#self._set_device_attribute(self._top_device(), 'vertoffset', value)
		self._vertical_offset_component.buttons_are_pressed() and self._control_surface.show_message('New vertical offset is ' + str(value))


	@listens('value')
	def _offset_value(self, value):
		#debug('offset_value', value)
		self._keygroup.offset = value
		#self._set_device_attribute(self._top_device(), 'offset', offset)
		self._offset_component.buttons_are_pressed() and self._control_surface.show_message('New root is Note# ' + str(value) + ', ' + str(NOTENAMES[value]))


	def update(self):
		super(MonoScaleComponent, self).update()
		#debug('monoscale enabled:', self.is_enabled())


# class SpecialMonoDrumGroupComponent(MonoDrumGroupComponent):



class MonoDrumpadComponent(Component):

	_offset_settings_component_class = OffsetTaggedSetting

	def __init__(self, parent, control_surface, skin, grid_resolution, parent_task_group, settings = DEFAULT_INSTRUMENT_SETTINGS, *a, **k):
		super(MonoDrumpadComponent, self).__init__(*a, **k)
		self._settings = settings
		self._parent = parent
		self._control_surface = control_surface
		self._skin = skin
		self._grid_resolution = grid_resolution

		#self._drum_offset_component = self.register_component(self._offset_settings_component_class(attribute_tag = 'drum_offset', name = 'DrumPadOffset', parent_task_group = parent_task_group, value_dict = range(28), default_value_index = self._settings['DefaultDrumOffset'], default_channel = 0, bank_increment = 4, on_color = 'MonoInstrument.OffsetOnValue', off_color = 'MonoInstrument.OffsetOffValue'))
		self._drum_offset_component = self._offset_settings_component_class(parent = self, attribute_tag = 'drum_offset', name = 'DrumPadOffset', parent_task_group = parent_task_group, value_dict = list(range(28)), default_value_index = self._settings['DefaultDrumOffset'], default_channel = 0, bank_increment = 4, on_color = 'MonoInstrument.OffsetOnValue', off_color = 'MonoInstrument.OffsetOffValue')
		self._drum_offset_value.subject = self._drum_offset_component
		self.set_offset_shift_toggle = self._drum_offset_component.shift_toggle.set_control_element

		self._drumgroup = SpecialMonoDrumGroupComponent(translation_channel = 15, set_pad_translations = self._control_surface.set_pad_translations, channel_list = self._settings['Channels'], settings = self._settings)
		self._drumpad_position_value.subject = self._drumgroup
		self.set_drumpad_matrix = self._drumgroup.set_matrix
		self.set_drumpad_select_matrix = self._drumgroup.set_select_matrix

		drum_clip_creator = ClipCreator()
		drum_note_editor = MonoNoteEditorComponent(clip_creator=drum_clip_creator, grid_resolution=grid_resolution)
		self._step_sequencer = MonoStepSeqComponent(parent = self, clip_creator=drum_clip_creator, skin=skin, grid_resolution=grid_resolution, name='Drum_Sequencer', note_editor_component=drum_note_editor, instrument_component=self._drumgroup)
		self._step_sequencer._playhead_component._notes=tuple(chain(*starmap(range, ((0, 8), (16, 24), (32, 40), (48, 56)))))
		self._step_sequencer._playhead_component._triplet_notes=tuple(chain(*starmap(range, ((0, 6), (16, 22), (32, 38), (48, 54)))))
		# self._step_sequencer._playhead_component._feedback_channels = [15]
		# self._step_sequencer._note_editor._visible_steps_model = lambda indices: [k for k in indices if k % 4 != 3]
		self._step_sequencer._note_editor._visible_steps_model = lambda indices: [k for k in indices if k % 8 not in (6, 7)]
		self.set_sequencer_matrix = self._step_sequencer.set_button_matrix
		self.set_playhead = self._step_sequencer.set_playhead
		self.set_loop_selector_matrix = self._step_sequencer.set_loop_selector_matrix
		self.set_quantization_buttons = self._step_sequencer.set_quantization_buttons
		# self.set_follow_button = self._step_sequencer.set_follow_button
		# self.set_follow_button = self._step_sequencer.set_follow_button
		self.set_mute_button = self._step_sequencer.set_mute_button
		self.set_solo_button = self._step_sequencer.set_solo_button
		self.set_delete_button = self._step_sequencer.set_delete_button
		#self.register_component(self._step_sequencer)

		self.set_split_matrix = self._parent._selected_session.set_clip_launch_buttons


	@listens('value')
	def _drum_offset_value(self, value):
		self._drumgroup.position = value
		self._drum_offset_component.buttons_are_pressed() and self._control_surface.show_message('New drum root is ' + str(value))
		#debug('_drum_offset_value', value)


	@listens('position')
	def _drumpad_position_value(self):
		self._drum_offset_component.set_index(self._drumgroup.position)


	def update(self):
		self._drumgroup._update_assigned_drum_pads()
		self._drumgroup._create_and_set_pad_translations()
		super(MonoDrumpadComponent, self).update()
		#debug('monodrum is enabled:', self.is_enabled())


class MonoInstrumentComponent(Component):


	_keypad_class = MonoScaleComponent
	_drumpad_class = MonoDrumpadComponent

	_scale_settings_component_class = ScaleTaggedSetting
	_toggle_settings_component_class = ToggledTaggedSetting

	_shifted = False

	def __init__(self, script, skin, grid_resolution, drum_group_finder, device_provider, parent_task_group, settings = DEFAULT_INSTRUMENT_SETTINGS, *a, **k):
		super(MonoInstrumentComponent, self).__init__(*a, **k)
		self._settings = settings
		self._parent_task_group = parent_task_group
		self._scalenames = settings['ScaleNames']
		self._device_provider = device_provider
		self._script = script
		self._skin = skin
		self._grid_resolution = grid_resolution
		self._drum_group_finder = drum_group_finder

		self._setup_selected_session_control()

		self._setup_shift_mode()

		#self._scale_offset_component = self.register_component(self._scale_settings_component_class(name = 'VerticalOffset', attribute_tag = 'scale', parent_task_group = parent_task_group, value_dict = self._scalenames, default_value_index = self._scalenames.index(DEFAULT_SCALE), default_channel = 0, on_color = 'MonoInstrument.ScaleOffsetOnValue', off_color = 'MonoInstrument.ScaleOffsetOffValue'))
		self._scale_offset_component = self._scale_settings_component_class(parent = self, name = 'VerticalOffset', attribute_tag = 'scale', parent_task_group = parent_task_group, value_dict = self._scalenames, default_value_index = self._scalenames.index(DEFAULT_SCALE), default_channel = 0, on_color = 'MonoInstrument.ScaleOffsetOnValue', off_color = 'MonoInstrument.ScaleOffsetOffValue')
		self._scale_offset_value.subject = self._scale_offset_component
		self.set_scale_up_button = self._scale_offset_component.up_button.set_control_element
		self.set_scale_down_button = self._scale_offset_component.down_button.set_control_element

		#self._mode_component = self.register_component(self._toggle_settings_component_class(name = 'SplitModeOffset', attribute_tag = 'mode', parent_task_group = parent_task_group,))
		self._mode_component = self._toggle_settings_component_class(parent = self, name = 'SplitModeOffset', attribute_tag = 'mode', parent_task_group = parent_task_group,)
		self._mode_value.subject = self._mode_component
		self.set_split_button = self._mode_component.split_toggle.set_control_element
		self.set_sequencer_button = self._mode_component.seq_toggle.set_control_element

		#self._keypad = self.register_component(self._keypad_class(parent = self, control_surface = script, skin = skin, grid_resolution = grid_resolution, parent_task_group = parent_task_group, settings = self._settings))
		self._keypad = self._keypad_class(parent = self, control_surface = script, skin = skin, grid_resolution = grid_resolution, parent_task_group = parent_task_group, settings = self._settings)
		self.set_vertical_offset_up_button = self._keypad._vertical_offset_component.up_button.set_control_element
		self.set_vertical_offset_down_button = self._keypad._vertical_offset_component.down_button.set_control_element
		self.set_offset_up_button = self._keypad._offset_component.up_button.set_control_element
		self.set_offset_down_button = self._keypad._offset_component.down_button.set_control_element
		self.set_octave_up_button = self._keypad._offset_component.bank_up_button.set_control_element
		self.set_octave_down_button = self._keypad._offset_component.bank_down_button.set_control_element

		#self._drumpad = self.register_component(self._drumpad_class(parent = self, control_surface = script, skin = skin, grid_resolution = grid_resolution, parent_task_group = parent_task_group, settings = self._settings))
		self._drumpad = self._drumpad_class(parent = self, control_surface = script, skin = skin, grid_resolution = grid_resolution, parent_task_group = parent_task_group, settings = self._settings)
		self.set_drum_offset_up_button = self._drumpad._drum_offset_component.up_button.set_control_element
		self.set_drum_offset_down_button = self._drumpad._drum_offset_component.down_button.set_control_element
		self.set_drum_octave_up_button = self._drumpad._drum_offset_component.bank_up_button.set_control_element
		self.set_drum_octave_down_button = self._drumpad._drum_offset_component.bank_down_button.set_control_element
		self.set_drumpad_mute_button = self._drumpad._drumgroup.mute_button.set_control_element
		self.set_drumpad_solo_button = self._drumpad._drumgroup.solo_button.set_control_element

		self._audio_loop = LoopSelectorComponent(follow_detail_clip=True, measure_length=1.0, name='Loop_Selector', default_size = 8)
		self.set_loop_selector_matrix = self._audio_loop.set_loop_selector_matrix

		#self._main_modes = self.register_component(ModesComponent())
		self._main_modes = ModesComponent()  #parent = self)
		self._main_modes.add_mode('disabled', [])
		self._main_modes.add_mode('audioloop', [self._audio_loop])
		self._main_modes.set_enabled(True)

		self._on_device_changed.subject = self._device_provider

		self.on_selected_track_changed.subject = self.song.view
		self.on_selected_track_changed()


	def set_delete_button(self, button):
		self._keypad.set_delete_button(button)
		self._drumpad.set_delete_button(button)

	def _setup_selected_session_control(self):
		self._session_ring = SessionRingComponent(num_tracks=1, num_scenes=32)
		self._selected_session = ScaleSessionComponent(name = "SelectedSession", session_ring = self._session_ring, auto_name = True, is_enabled = False)
		self._selected_session.set_enabled(False)


	def _setup_shift_mode(self):
		self._shifted = False
		#self._shift_mode = self.register_component(ModesComponent())
		self._shift_mode = ModesComponent()  #parent = self)
		self._shift_mode.add_mode('disabled', [])
		self._shift_mode.add_mode('shift', tuple([lambda a: self._on_shift_value(True), lambda a: self._on_shift_value(False)]), behaviour = ShiftCancellableBehaviourWithRelease())


	def set_shift_button(self, button):
		debug('shift_button:', button)
		self._on_shift_value.subject = button
		self._shifted = 0


	def set_shift_mode_button(self, button):
		self._on_shift_value.subject = None
		self._shifted = 0
		self._shift_mode.shift_button.set_control_element(button)


	@listens('value')
	def _on_shift_value(self, value):
		#debug('on shift value:', value)
		self._shifted = bool(value)
		self.update()



	def set_octave_enable_button(self, button):
		self._keypad._offset_component.shift_button.set_control_element(button)
		self._drumpad._drum_offset_component.shift_button.set_control_element(button)


	@listens('value')
	def _on_octave_enable_value(self, value):
		value and self._keypad._offset_component.shift_button._press_button() or self._keypad._offset_component.shift_button._release_button()
		value and self._drumpad._drum_offset_component.shift_button._press_button() or self._drumpad._drum_offset_component.shift_button._release_button()


	@listens('value')
	def _mode_value(self, value):
		self.update()


	@listens('value')
	def _scale_offset_value(self, value):
		#debug('_scale_offset_value', value)
		value = self._settings['DefaultAutoScale'] if value is 'Auto' else value
		self._keypad._keygroup.scale = value
		self._scale_offset_component.buttons_are_pressed() and self._script.show_message('New scale is ' + str(value))
		self.update()


	@listens('instrument')
	def _on_drum_group_changed(self):
		drum_device = self._drum_group_finder.drum_group
		#debug('monoinstrument _on_drum_group_changed', drum_device)
		self._drumpad._step_sequencer.set_drum_group_device(drum_device)


	@listens('device')
	def _on_device_changed(self):
		#debug('monoinstrument _on_device_changed')
		self._script.schedule_message(1, self.update)
		#self.update()


	@listens('selected_track')
	def on_selected_track_changed(self):
		self._selected_session.update_current_track()
		self.update()


	def update(self):
		super(MonoInstrumentComponent, self).update()
		# self._main_modes.selected_mode = 'disabled'
		#if self.is_enabled():
		new_mode = 'disabled'
		drum_device = find_drum_group_device(self.song.view.selected_track)
		#debug('instrument update, drum device:', drum_device.name if drum_device else None)
		self._drumpad._drumgroup.set_drum_group_device(drum_device)
		cur_track = self.song.view.selected_track
		if cur_track.has_audio_input and cur_track in self.song.visible_tracks:
			new_mode = 'audioloop'
		elif cur_track.has_midi_input:
			scale, mode = self._scale_offset_component.value, self._mode_component.value
			new_mode = get_instrument_type(cur_track, scale, self._settings)
			if mode is 'split':
				new_mode += '_split'
			elif mode is 'seq':
				new_mode +=  '_sequencer'
			if self._shifted:
				new_mode += '_shifted'
			self._script.set_feedback_channels([self._scale_offset_component.channel])
			self._script.set_controlled_track(self.song.view.selected_track)
		debug('trying to set mode:', new_mode)
		if new_mode in self._main_modes._mode_map or new_mode is None:
			if self._main_modes.selected_mode != new_mode:
				self._main_modes.selected_mode = new_mode
			self._script.set_controlled_track(self.song.view.selected_track)
		else:
			self._main_modes.selected_mode = 'disabled'
			self._script.set_controlled_track(self.song.view.selected_track)
		#debug('monoInstrument mode is:', self._main_modes.selected_mode, '  inst:', self.is_enabled(), '  modes:', self._main_modes.is_enabled(), '   key:', self._keypad.is_enabled(), '   drum:', self._drumpad.is_enabled())



#a
