
import Live
from ableton.v2.base import listenable_property, listens, liveobj_changed, liveobj_valid, EventObject

from aumhaa.v3.base.debug import initialize_debug

LOCAL_DEBUG=False
debug = initialize_debug(local_debug=LOCAL_DEBUG)


def device_to_appoint(device):
	appointed_device = device
	if liveobj_valid(device) and device.can_have_drum_pads and not device.has_macro_mappings and len(device.chains) > 0 and liveobj_valid(device.view.selected_chain) and len(device.view.selected_chain.devices) > 0:
		appointed_device = device_to_appoint(device.view.selected_chain.devices[0])
	return appointed_device


def select_and_appoint_device(song, device_to_select, ignore_unmapped_macros = False):
	"""
	Convenience function for selecting a device for a control surface to control.

	This takes care of selecting the device and appointing it for remote control, which
	is important, because these are two concepts, that are not exactly the same.

	The device component always controls the appointed device. It's possible to select
	another device, but not appoint it for control. The behaviour in this function
	appoints a drum rack's selected chain's first device if none of the macros are mapped
	for the drum rack. Though, it's still possible to select the drum rack, we just do
	not display its controls in this scenario.
	"""
	appointed_device = device_to_select
	if ignore_unmapped_macros:
		appointed_device = device_to_appoint(device_to_select)
	song.view.select_device(device_to_select, False)
	song.appointed_device = appointed_device


class DeviceProvider(EventObject):
	"""
	Provide "controlled device" to device component

	This class abstracts the logic required to provide a controlled device to be used
	by the device component. In most cases, this is the same as the appointed device, but
	not always, e.g. when a surface is locked to a device (there is only one global
	appointed device per Song).

	This class also takes care of appointing the right device when switching between
	tracks etc.
	"""
	device_selection_follows_track_selection = True

	def __init__(self, song = None, *a, **k):
		super(DeviceProvider, self).__init__(*a, **k)
		self._device = None
		self._locked_to_device = False
		self._selected_drum_pad = None
		self.song = song
		self.__on_appointed_device_changed.subject = song
		self.__on_selected_track_changed.subject = song.view
		self.__on_selected_device_changed.subject = song.view.selected_track.view

	@listenable_property
	def device(self):
		return self._device

	@listenable_property
	def selected_drum_pad(self):
		return self._selected_drum_pad

	@device.setter
	def device(self, device):
		if liveobj_changed(self._device, device) and not self.is_locked_to_device:
			self._device = device
			self.notify_device()

	@listenable_property
	def is_locked_to_device(self):
		"""
		Indicates whether the provider is currently locked to a device.
		"""
		return self._locked_to_device

	def lock_to_device(self, device):
		self.device = device
		self._locked_to_device = True
		self.notify_is_locked_to_device()

	def unlock_from_device(self):
		self._locked_to_device = False
		self.notify_is_locked_to_device()
		self.update_device_selection()

	def update_device_selection(self):
		view = self.song.view
		track_or_chain = view.selected_chain if view.selected_chain else view.selected_track
		device_to_select = None
		if isinstance(track_or_chain, Live.Track.Track):
			device_to_select = track_or_chain.view.selected_device
		if device_to_select == None and len(track_or_chain.devices) > 0:
			device_to_select = track_or_chain.devices[0]
		if liveobj_valid(device_to_select):
			appointed_device = device_to_appoint(device_to_select)
			#self.song.view.select_device(device_to_select, False)
			#self.song.appointed_device = appointed_device
			self.device = appointed_device
		else:
			#self.song.appointed_device = None
			self.device = None

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

	def _update_appointed_device(self):
		song = self.song
		device = song.view.selected_track.view.selected_device
		# if liveobj_valid(device):
		# 	self.song.appointed_device = device_to_appoint(device)
		if liveobj_valid(device):
			self.song.appointed_device = device_to_appoint(device)
			debug('Device_to_appoint:', device.name if hasattr(device, 'name') else "None")
		rack_device = device if isinstance(device, Live.RackDevice.RackDevice) else None
		self.__on_has_macro_mappings_changed.subject = rack_device
		self.__on_chains_changed.subject = rack_device
