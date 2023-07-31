# by amounra 0623 : http://www.aumhaa.com
# written against Live 11.310b1 release on 062723

from aumhaa.v2.base.debug import *

LOCAL_DEBUG = False
debug = initialize_debug(local_debug = LOCAL_DEBUG)


#  SYSEX_HEADER + MODGRID_SYSEX_HEADER + tuple( (10, self._original_channel, self._original_identifier, int(enabled), 247,)))
# SYSEX_HEADER = (240, 0, 1, 97)
# MODGRID_SYSEX_HEADER = (93, 93)

class PRODUCTS:
	MODGRID = 93



CALLS = {'set_piano_view':50,
	 	'set_mira_id': 42,
		'set_mira_address':41,
		'set_mira_view':40,
		'set_skin_view':30,
	 	'set_full_grid_view':20,
	 	'enable_button_mpe':10,
		'text_to_button':0,
		'name_text_to_dial':1,
		'value_text_to_dial':2,}

def fallback_send_midi(message = None, *a, **k):
	debug('control surface not assigned to the sysex call:', message)


def get_call_type(call_type):
	#debug('call type is:', call_type)
	if call_type in CALLS:
		return [CALLS[call_type]]
	else:
		return False



class AumhaaSettings(object):


	def __init__(self, prefix = [240, 0, 1, 97], model = [93, 93], control_surface = None, *a, **k):
		super(AumhaaSettings, self).__init__()
		self._prefix = prefix
		self._model = model
		self._send_midi = control_surface._send_midi if control_surface else fallback_send_midi
		for keyword, value in k.items():
			setattr(self, keyword, value)
	

	def query_surface(self):
		self._send_midi(QUERYSURFACE)
	

	def set_model(self, model):
		self._model = model
	

	def send(self, call = None, message = [], *a, **k):
		call = get_call_type(call)
		if call:
			message = self._prefix + self._model + call + message + [247]
			debug('sending:', message)
			self._send_midi(tuple(message))
		else:
			debug(call, 'is not a valid aumhaa_settings call')



class DescriptorBank(object):

	def __init__(self, name = None, *a, **k):
		super(DescriptorBank, self).__init__()
	









