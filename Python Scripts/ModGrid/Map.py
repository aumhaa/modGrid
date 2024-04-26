# by amounra 0524 : http://www.aumhaa.com
# written against Live 12.0.5b3 on 052524
# version b7.0

from ableton.v2.control_surface.elements.color import Color
from aumhaa.v3.livid.colors import *

MAIN_CONTROL_CHANNEL = 0
# CHANNEL = 3
# SECONDARY_CHANNEL = 4

UTIL_BUTTONS = list(range(128))
SECONDARY_CHANNEL_UTIL_BUTTONS = list(range(128))

FAVORITE_CLIP_COLOR = 14

# COLOR_MAP = [1,2,3,4,5,6,7]
COLOR_MAP = range(1, 128)

WHITEKEYS = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24]

LENGTH_VALUES = [2, 3, 4]

CHANNELS = ['Ch. 2', 'Ch. 3', 'Ch. 4', 'Ch. 5', 'Ch. 6', 'Ch. 7', 'Ch. 8', 'Ch. 9', 'Ch. 10', 'Ch. 11', 'Ch. 12', 'Ch. 13', 'Ch. 14']

ascii_translations = {'0':48, 
	 '1':49, 
	 '2':50, 
	 '3':51, 
	 '4':52, 
	 '5':53, 
	 '6':54, 
	 '7':55, 
	 '8':56, 
	 '9':57, 
	 'A':65, 
	 'B':66, 
	 'C':67, 
	 'D':68, 
	 'E':69, 
	 'F':70, 
	 'G':71, 
	 'H':72, 
	 'I':73, 
	 'J':74, 
	 'K':75, 
	 'L':76, 
	 'M':77, 
	 'N':78, 
	 'O':79, 
	 'P':80, 
	 'Q':81, 
	 'R':82, 
	 'S':83, 
	 'T':84, 
	 'U':85, 
	 'V':86, 
	 'W':87, 
	 'X':88, 
	 'Y':89, 
	 'Z':90, 
	 'a':97, 
	 'b':98, 
	 'c':99, 
	 'd':100, 
	 'e':101, 
	 'f':102, 
	 'g':103, 
	 'h':104, 
	 'i':105, 
	 'j':106, 
	 'k':107, 
	 'l':108, 
	 'm':109, 
	 'n':110, 
	 'o':111, 
	 'p':112, 
	 'q':113, 
	 'r':114, 
	 's':115, 
	 't':116, 
	 'u':117, 
	 'v':118, 
	 'w':119, 
	 'x':120, 
	 'y':121, 
	 'z':122, 
	 '@':64, 
	 ' ':32, 
	 '!':33, 
	 '"':34, 
	 '#':35, 
	 '♯':35, 
	 '.':46, 
	 ',':44, 
	 ':':58, 
	 ';':59, 
	 '?':63, 
	 '<':60, 
	 '>':62, 
	 '[':91, 
	 ']':93, 
	 '_':95, 
	 '-':45, 
	 '|':124, 
	 '&':38, 
	 '^':94, 
	 '~':126, 
	 '`':96, 
	 "'":39, 
	 '%':37, 
	 '(':40, 
	 ')':41, 
	 '/':47, 
	 '\\':92, 
	 '*':42, 
	 '+':43}

"""These are the scales we have available.  You can freely add your own scales to this """
SCALES = 	{'Mod':[0,1,2,3,4,5,6,7,8,9,10,11],
			'Session':[0,1,2,3,4,5,6,7,8,9,10,11],
			'Keys':[0,2,4,5,7,9,11,12,1,3,3,6,8,10,10,13],
			'Auto':[0,1,2,3,4,5,6,7,8,9,10,11],
			'Chromatic':[0,1,2,3,4,5,6,7,8,9,10,11],
			'DrumPad':[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
			'Major':[0,2,4,5,7,9,11],
			'Minor':[0,2,3,5,7,8,10],
			'Dorian':[0,2,3,5,7,9,10],
			'Mixolydian':[0,2,4,5,7,9,10],
			'Lydian':[0,2,4,6,7,9,11],
			'Phrygian':[0,1,3,5,7,8,10],
			'Locrian':[0,1,3,4,7,8,10],
			'Diminished':[0,1,3,4,6,7,9,10],
			'Whole-half':[0,2,3,5,6,8,9,11],
			'Whole_Tone':[0,2,4,6,8,10],
			'Minor_Blues':[0,3,5,6,7,10],
			'Minor_Pentatonic':[0,3,5,7,10],
			'Major_Pentatonic':[0,2,4,7,9],
			'Harmonic_Minor':[0,2,3,5,7,8,11],
			'Melodic_Minor':[0,2,3,5,7,9,11],
			'Dominant_Sus':[0,2,5,7,9,10],
			'Super_Locrian':[0,1,3,4,6,8,10],
			'Neopolitan_Minor':[0,1,3,5,7,8,11],
			'Neopolitan_Major':[0,1,3,5,7,9,11],
			'Enigmatic_Minor':[0,1,3,6,7,10,11],
			'Enigmatic':[0,1,4,6,8,10,11],
			'Composite':[0,1,4,6,7,8,11],
			'Bebop_Locrian':[0,2,3,5,6,8,10,11],
			'Bebop_Dominant':[0,2,4,5,7,9,10,11],
			'Bebop_Major':[0,2,4,5,7,8,9,11],
			'Bhairav':[0,1,4,5,7,8,11],
			'Hungarian_Minor':[0,2,3,6,7,8,11],
			'Minor_Gypsy':[0,1,4,5,7,8,10],
			'Persian':[0,1,4,5,6,8,11],
			'Hirojoshi':[0,2,3,7,8],
			'In-Sen':[0,1,5,7,10],
			'Iwato':[0,1,5,6,10],
			'Kumoi':[0,2,3,7,9],
			'Pelog':[0,1,3,4,7,8],
			'Spanish':[0,1,3,4,5,6,8,10]
			}

SCALEABBREVS = {'Auto':'-A','Keys':'-K','Chromatic':'12','DrumPad':'-D','Major':'M-','Minor':'m-','Dorian':'II','Mixolydian':'V',
			'Lydian':'IV','Phrygian':'IH','Locrian':'VH','Diminished':'d-','Whole-half':'Wh','Whole_Tone':'WT','Minor_Blues':'mB',
			'Minor_Pentatonic':'mP','Major_Pentatonic':'MP','Harmonic_Minor':'mH','Melodic_Minor':'mM','Dominant_Sus':'D+','Super_Locrian':'SL',
			'Neopolitan_Minor':'mN','Neopolitan_Major':'MN','Enigmatic_Minor':'mE','Enigmatic':'ME','Composite':'Cp','Bebop_Locrian':'lB',
			'Bebop_Dominant':'DB','Bebop_Major':'MB','Bhairav':'Bv','Hungarian_Minor':'mH','Minor_Gypsy':'mG','Persian':'Pr',
			'Hirojoshi':'Hr','In-Sen':'IS','Iwato':'Iw','Kumoi':'Km','Pelog':'Pg','Spanish':'Sp'}


"""This is the default scale used by Auto when something other than a drumrack is detected for the selected track"""
DEFAULT_AUTO_SCALE = 'Chromatic'

"""This is the default Vertical Offset for any scale other than DrumPad """
DEFAULT_VERTOFFSET = 4

"""This is the default NoteOffset, aka RootNote, used for scales other than DrumPad"""
DEFAULT_OFFSET = 48

"""This is the default NoteOffset, aka RootNote, used for the DrumPad scale;  it is a multiple of 4, so an offset of 4 is actually a RootNote of 16"""
DEFAULT_DRUMOFFSET = 9

"""This is the default Scale used for all MIDI Channels"""
DEFAULT_SCALE = 'Auto'

"""This is the default SplitMode used for all MIDI Channels"""
DEFAULT_MODE = 'seq'

SCALENAMES = [scale for scale in sorted(SCALES.keys())]

"""It is possible to create a custom list of scales to be used by the script.  For instance, the list below would include major, minor, auto, drumpad, and chromatic scales, in that order."""
#SCALENAMES = ['Major', 'Minor', 'Auto', 'DrumPad', 'Chromatic']

DEFAULT_INSTRUMENT_SETTINGS = {'Scales':SCALES,
								'ScaleAbbrevs':SCALEABBREVS,
								'ScaleNames':SCALENAMES,
								'DefaultAutoScale':DEFAULT_AUTO_SCALE,
								'DefaultVertOffset':DEFAULT_VERTOFFSET,
								'DefaultOffset':DEFAULT_OFFSET,
								'DefaultDrumOffset':DEFAULT_DRUMOFFSET,
								'DefaultScale':DEFAULT_SCALE,
								'DefaultMode':DEFAULT_MODE,
								'Channels':CHANNELS}

# class ModGridRGB:

# 	OFF = MonoColor(0)
# 	WHITE = MonoColor(1)
# 	YELLOW = MonoColor(2)
# 	CYAN = MonoColor(3)
# 	MAGENTA = MonoColor(4)
# 	RED = MonoColor(5)
# 	GREEN = MonoColor(6)
# 	BLUE = MonoColor(7)

class FlashingColor(Color):


	def __init__(self, flash_color = 1, unflash_color = 0, *a, **k):
		self._flash_color = flash_color
		self._unflash_color = unflash_color
		super(FlashingColor, self).__init__(*a, **k)


	def draw(self, interface):
		try:
			interface._animation_handler.add_interface(interface, [self._flash_color, self._unflash_color])
		except:
			pass
		super(FlashingColor, self).draw(interface)


class ModGridRGB:
	OFF = MonoColor(0)
	BLACK = MonoColor(0)
	GREY = MonoColor(70)
	DARK_GREY = MonoColor(117)
	WHITE = MonoColor(1)
	YELLOW = MonoColor(2)
	DARK_YELLOW = MonoColor(14)
	CYAN = MonoColor(3)
	DARK_CYAN = MonoColor(38)
	MAGENTA = MonoColor(4)
	DARK_MAGENTA = MonoColor(54)
	RED = MonoColor(5)
	DARK_RED = MonoColor(10)
	GREEN = MonoColor(6)
	DARK_GREEN = MonoColor(22)
	BLUE = MonoColor(7)
	DARK_BLUE = MonoColor(46)
	ORANGE = MonoColor(96)
	DARK_ORANGE = MonoColor(126)
	PURPLE = MonoColor(49)
	DARK_PURPLE = MonoColor(93)

	SALMON = MonoColor(8)
	CANARY = MonoColor(12)
	LIME = MonoColor(17)
	SPRING = MonoColor(25)
	TURQUOISE = MonoColor(29)
	SKY = MonoColor(37)
	OCEAN = MonoColor(41)
	ORCHID = MonoColor(49)
	PINK = MonoColor(52)
	FUSCIA = MonoColor(56)

	FLASHING_WHITE = FlashingColor(1, 70)
	FLASHING_GREEN = FlashingColor(6, 22)
	FLASHING_YELLOW = FlashingColor(2, 14)
	FLASHING_CYAN = FlashingColor(3, 38)
	FLASHING_MAGENTA = FlashingColor(4, 54)
	FLASHING_RED = FlashingColor(5, 10)
	FLASHING_BLUE = FlashingColor(7, 46)
	FLASHING_ORANGE = FlashingColor(96, 126)
	FLASHING_PURPLE = FlashingColor(49, 93)












class UtilColors:

	class MainModes:
		Main = ModGridRGB.OFF
		Main_shifted = ModGridRGB.WHITE
		Full = ModGridRGB.OFF
		Full_shifted = ModGridRGB.WHITE

	class Option:
		Selected = ModGridRGB.WHITE
		Unselected = ModGridRGB.CYAN
		On = ModGridRGB.WHITE
		Off = ModGridRGB.BLUE
		Unused = ModGridRGB.OFF

	class ItemNavigation:
		ItemNotSelected = ModGridRGB.MAGENTA
		ItemNotSelectedOff = ModGridRGB.DARK_MAGENTA
		ItemSelected = ModGridRGB.WHITE
		ItemSelectedOff = ModGridRGB.GREY
		NoItem = ModGridRGB.OFF
		ScrollingIndicator = ModGridRGB.BLUE

	class EditModeOptions:
		ItemNotSelected = ModGridRGB.DARK_YELLOW
		ItemSelected = ModGridRGB.YELLOW
		NoItem = ModGridRGB.OFF

	class DeviceNavigation:
		ItemNotSelected = ModGridRGB.MAGENTA
		ItemNotSelectedOff = ModGridRGB.DARK_MAGENTA
		ItemSelected = ModGridRGB.CYAN
		ItemSelectedOff = ModGridRGB.DARK_CYAN
		NoItem = ModGridRGB.OFF
		ScrollingIndicator = ModGridRGB.BLUE

	class BankSelection:
		ItemNotSelected = ModGridRGB.YELLOW
		ItemSelected = ModGridRGB.DARK_YELLOW
		NoItem = ModGridRGB.OFF
		ScrollingIndicator = ModGridRGB.BLUE


	class ChainNavigation:
		ItemNotSelected = ModGridRGB.GREEN
		ItemSelected = ModGridRGB.DARK_GREEN
		NoItem = ModGridRGB.OFF
		ScrollingIndicator = ModGridRGB.BLUE


	class ModeButtons:
		Main = ModGridRGB.WHITE
		Select = ModGridRGB.RED
		Clips = ModGridRGB.GREEN


	class DefaultButton:
		On = ModGridRGB.WHITE
		Off = ModGridRGB.OFF
		Disabled = ModGridRGB.OFF
		Alert = ModGridRGB.RED
		Transparent = ModGridRGB.GREY

	class List:
		ScrollerOn = ModGridRGB.GREEN
		ScrollerOff = ModGridRGB.MAGENTA

	class Session:
		StopClipDisabled = ModGridRGB.OFF
		StopClipTriggered = ModGridRGB.FLASHING_BLUE
		StopClip = ModGridRGB.BLUE
		Scene = ModGridRGB.CYAN
		NoScene = ModGridRGB.OFF
		SceneTriggered = ModGridRGB.GREEN
		ClipTriggeredPlay = ModGridRGB.FLASHING_GREEN
		ClipTriggeredRecord = ModGridRGB.FLASHING_RED
		RecordButton = ModGridRGB.OFF
		ClipEmpty = ModGridRGB.OFF
		ClipStopped = ModGridRGB.WHITE
		# ClipStarted = ModGridRGB.GREEN
		ClipStarted = ModGridRGB.FLASHING_GREEN
		ClipRecording = ModGridRGB.FLASHING_RED
		NavigationButtonOn = ModGridRGB.CYAN
		NavigationButtonOff = ModGridRGB.YELLOW
		ZoomOn = ModGridRGB.WHITE
		ZoomOff = ModGridRGB.WHITE
		FireNextArm = ModGridRGB.RED
		Delete = ModGridRGB.BLUE
		DeletePressed = ModGridRGB.WHITE
		Select = ModGridRGB.BLUE
		SelectPressed = ModGridRGB.WHITE
		Duplicate = Color(70)
		DuplicatePressed = Color(80)

	class Zooming:
		Selected = ModGridRGB.YELLOW
		Stopped = ModGridRGB.WHITE
		Playing = ModGridRGB.GREEN
		Empty = ModGridRGB.OFF


	class LoopSelector:
		Playhead = ModGridRGB.YELLOW
		OutsideLoop = ModGridRGB.BLUE
		InsideLoopStartBar = ModGridRGB.CYAN
		SelectedPage = ModGridRGB.WHITE
		InsideLoop = ModGridRGB.CYAN
		PlayheadRecord = ModGridRGB.RED
		Bank = ModGridRGB.MAGENTA
		ShiftLoop = ModGridRGB.WHITE
		LatestLoop = ModGridRGB.YELLOW


	class Transport:
		PlayOn = ModGridRGB.GREEN
		PlayOff = ModGridRGB.DARK_GREEN
		StopOn = ModGridRGB.GREY
		StopOff = ModGridRGB.DARK_GREY
		RecordOn = ModGridRGB.RED
		RecordOff = ModGridRGB.DARK_RED
		OverdubOn = ModGridRGB.MAGENTA
		OverdubOff = ModGridRGB.DARK_MAGENTA
		SeekBackwardOn = ModGridRGB.CYAN
		SeekBackwardOff = ModGridRGB.CYAN
		LoopOn = ModGridRGB.YELLOW
		LoopOff = ModGridRGB.DARK_YELLOW
		MetroOn = ModGridRGB.CYAN
		MetroOff = ModGridRGB.DARK_CYAN

	class Auto_Arm:
		Enabled = ModGridRGB.RED
		Disabled = ModGridRGB.DARK_RED

	class DeviceSelector:
		AssignOn = ModGridRGB.GREEN
		AssignOff = ModGridRGB.DARK_GREEN

	class Mixer:
		SoloOn = ModGridRGB.BLUE
		SoloOff = ModGridRGB.DARK_BLUE
		MuteOn = ModGridRGB.YELLOW
		MuteOff = ModGridRGB.DARK_YELLOW
		ArmSelected = ModGridRGB.RED
		ArmSelectedImplicit = ModGridRGB.PINK
		ArmUnselected = ModGridRGB.RED
		ArmOff = ModGridRGB.DARK_RED
		StopClip = ModGridRGB.GREY
		SelectedOn = ModGridRGB.WHITE
		SelectedOff = ModGridRGB.DARK_GREY
		ArmOn = ModGridRGB.RED

	class MasterTrack:
		On = ModGridRGB.RED
		Off = ModGridRGB.DARK_GREY


	class Recording:
		On = ModGridRGB.RED
		Transition = ModGridRGB.PURPLE
		Off = ModGridRGB.DARK_RED


	class Automation:
		On = ModGridRGB.ORANGE
		Off = ModGridRGB.DARK_ORANGE


	class Recorder:
		On = ModGridRGB.WHITE
		Off = ModGridRGB.GREY
		NewOn = ModGridRGB.YELLOW
		NewOff = ModGridRGB.DARK_YELLOW
		FixedOn = ModGridRGB.CYAN
		FixedOff = ModGridRGB.DARK_CYAN
		RecordOn = ModGridRGB.MAGENTA
		RecordOff = ModGridRGB.DARK_MAGENTA
		AutomationOn = ModGridRGB.ORANGE
		AutomationOff = ModGridRGB.DARK_ORANGE
		FixedAssigned = ModGridRGB.MAGENTA
		FixedNotAssigned = ModGridRGB.DARK_MAGENTA


	class Device:
		NavOn = ModGridRGB.MAGENTA
		NavOff = ModGridRGB.DARK_MAGENTA
		BankOn = ModGridRGB.YELLOW
		BankOff = ModGridRGB.DARK_YELLOW
		ChainNavOn = ModGridRGB.RED
		ChainNavOff = ModGridRGB.DARK_RED
		ContainNavOn = ModGridRGB.CYAN
		ContainNavOff = ModGridRGB.DARK_CYAN


	class NoteEditor:


		class Step:
			Low = ModGridRGB.CYAN
			High = ModGridRGB.WHITE
			Full = ModGridRGB.YELLOW
			Muted = ModGridRGB.YELLOW
			StepEmpty = ModGridRGB.OFF


		class StepEditing:
			High = ModGridRGB.GREEN
			Low = ModGridRGB.CYAN
			Full = ModGridRGB.YELLOW
			Muted = ModGridRGB.WHITE


		StepEmpty = ModGridRGB.OFF
		StepEmptyBase = ModGridRGB.OFF
		StepEmptyScale = ModGridRGB.OFF
		StepDisabled = ModGridRGB.OFF
		Playhead = Color(31)
		PlayheadRecord = Color(31)
		StepSelected = ModGridRGB.GREEN
		QuantizationSelected = ModGridRGB.RED
		QuantizationUnselected = ModGridRGB.MAGENTA


	class DrumGroup:
		PadAction = ModGridRGB.WHITE
		PadFilled = ModGridRGB.GREEN
		PadFilledAlt = ModGridRGB.MAGENTA
		PadSelected = ModGridRGB.WHITE
		PadSelectedNotSoloed = ModGridRGB.WHITE
		PadEmpty = ModGridRGB.OFF
		PadMuted = ModGridRGB.YELLOW
		PadSoloed = ModGridRGB.CYAN
		PadMutedSelected = ModGridRGB.BLUE
		PadSoloedSelected = ModGridRGB.BLUE
		PadInvisible = ModGridRGB.OFF
		PadAction = ModGridRGB.RED


	class MonoInstrument:


		PressFlash = ModGridRGB.WHITE
		OffsetOnValue = ModGridRGB.GREEN
		OffsetOffValue = ModGridRGB.DARK_GREEN
		ScaleOffsetOnValue = ModGridRGB.RED
		ScaleOffsetOffValue = ModGridRGB.DARK_RED
		SplitModeOnValue = ModGridRGB.WHITE
		SplitModeOffValue = ModGridRGB.GREY
		SequencerModeOnValue = ModGridRGB.CYAN
		SequencerModeOffValue = ModGridRGB.DARK_CYAN
		DrumOffsetOnValue = ModGridRGB.MAGENTA
		DrumOffsetOffValue = ModGridRGB.DARK_MAGENTA
		VerticalOffsetOnValue = ModGridRGB.BLUE
		VerticalOffsetOffValue = ModGridRGB.DARK_BLUE


		class Keys:
			SelectedNote = ModGridRGB.ORANGE
			RootWhiteValue = ModGridRGB.RED
			RootBlackValue = ModGridRGB.BLUE
			WhiteValue = ModGridRGB.WHITE
			BlackValue = ModGridRGB.BLACK


		class Drums:
			SelectedNote = ModGridRGB.BLUE
			EvenValue = ModGridRGB.GREEN
			OddValue = ModGridRGB.MAGENTA


class ModGridColors:


	class DefaultButton:
		On = LividRGB.WHITE
		Off = LividRGB.OFF
		Disabled = LividRGB.OFF
		Alert = LividRGB.BlinkFast.WHITE


	class DrumGroup:
		PadAction = LividRGB.WHITE
		PadFilled = LividRGB.GREEN
		PadFilledAlt = LividRGB.MAGENTA
		PadSelected = LividRGB.WHITE
		PadSelectedNotSoloed = LividRGB.WHITE
		PadEmpty = LividRGB.OFF
		PadMuted = LividRGB.YELLOW
		PadSoloed = LividRGB.CYAN
		PadMutedSelected = LividRGB.BLUE
		PadSoloedSelected = LividRGB.BLUE
		PadInvisible = LividRGB.OFF
		PadAction = LividRGB.RED


	class Mod:
		class Nav:
			OnValue = LividRGB.RED
			OffValue = LividRGB.WHITE

