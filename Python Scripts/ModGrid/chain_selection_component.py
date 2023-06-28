from __future__ import absolute_import, print_function, unicode_literals
from itertools import count
from ableton.v2.base import listens, listens_group, liveobj_valid
from ableton.v2.control_surface.components import ItemProvider
from Push2.colors import DISPLAY_BUTTON_SHADE_LEVEL, IndexedColor
from Push2.item_lister import ItemListerComponent

class ChainProvider(ItemProvider):

	def __init__(self, *a, **k):
		(super(ChainProvider, self).__init__)(*a, **k)
		self._rack = None

	def set_rack(self, rack):
		if rack != self._rack:
			rack_view = rack.view if rack else None
			self._rack = rack
			self._ChainProvider__on_chains_changed.subject = rack
			self._ChainProvider__on_selected_chain_changed.subject = rack_view
			self.notify_items()
			self.notify_selected_item()

	@property
	def items(self):
		chains = self._rack.chains if liveobj_valid(self._rack) else []
		return [(chain, 0) for chain in chains]

	@property
	def chains(self):
		if liveobj_valid(self._rack):
			return self._rack.chains
		return []

	@property
	def selected_item(self):
		if liveobj_valid(self._rack):
			return self._rack.view.selected_chain

	def select_chain(self, chain):
		self._rack.view.selected_chain = chain

	@listens('chains')
	def __on_chains_changed(self):
		self.notify_items()

	@listens('selected_chain')
	def __on_selected_chain_changed(self):
		self.notify_selected_item()


class ChainSelectionComponent(ItemListerComponent):
	text_data_sources = [DisplayDataSource('') for index in range(8)]

	def __init__(self, *a, **k):
		self._chain_parent = ChainProvider()
		(super(ChainSelectionComponent, self).__init__)(a, item_provider=self._chain_parent, **k)
		# (super(ChainSelectionComponent, self).__init__)(a, **k)
		self.register_disconnectable(self._chain_parent)
		self._ChainSelectionComponent__on_items_changed.subject = self
		self._ChainSelectionComponent__on_items_changed()
		self._on_item_names_changed.subject = self

	def _on_select_button_pressed(self, button):
		self._chain_parent.select_chain(self.items[button.index].item)

	def _color_for_button(self, button_index, is_selected):
		if is_selected:
			return self.color_class_name + '.ItemSelected'
		chain_color = self._chain_parent.chains[button_index].color_index
		return IndexedColor.from_live_index(chain_color, DISPLAY_BUTTON_SHADE_LEVEL)

	def set_parent(self, parent):
		self._chain_parent.set_rack(parent)

	@listens('items')
	def __on_items_changed(self):
		self._ChainSelectionComponent__on_chain_color_index_changed.replace_subjects((self._chain_parent.chains),
		  identifiers=(count()))

	@listens_group('color_index')
	def __on_chain_color_index_changed(self, chain_index):
		self.select_buttons[chain_index].color = self._color_for_button(chain_index, self._items_equal(self.items[chain_index], self._item_provider.selected_item))

	def set_select_buttons(self, buttons):
		if not buttons is None:
			self.select_buttons.set_control_element(buttons)
			for index, button in enumerate(buttons):
				if hasattr(button, "_display"):
					button._display.set_data_sources([self.text_data_sources[index]])
		else:
			self.select_buttons.set_control_element(None)

	@listens('items')
	def _on_item_names_changed(self, *a):
		items = [x.item for x in self.items]
		new_items = [str(item.name) if hasattr(item, 'name') else '' for item in items]
		items[:len(new_items)] = new_items
		debug('CHAIN._on_items_changed:', items)
		for source, item in zip_longest(self.text_data_sources, items):
			if source:
				source.set_display_string(item if not item is None else '')

	def set_select_button_displays(self, displays):
		debug('set_select_button_displays', displays)
		# super(ModGridDeviceNavigationComponent, self).set_select_buttons(buttons)
		for source, display in zip_longest(self.text_data_sources, displays or []):
			if hasattr(display, "set_data_sources"):
				display.set_data_sources([source])
