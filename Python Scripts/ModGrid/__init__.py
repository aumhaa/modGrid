

from ableton.v2.control_surface import capabilities as caps
from .ModGrid import ModGrid

def get_capabilities():
    return {caps.CONTROLLER_ID_KEY: caps.controller_id(vendor_id=10996, product_ids=[2304], model_name=['ModGrid', 'MODGRID']),
     caps.PORTS_KEY: [caps.inport(props=[caps.NOTES_CC, caps.SCRIPT]), caps.outport(props=[caps.NOTES_CC, caps.SCRIPT])],
     caps.TYPE_KEY: 'ModGrid'}


def create_instance(c_instance):
    return ModGrid(c_instance=c_instance)
