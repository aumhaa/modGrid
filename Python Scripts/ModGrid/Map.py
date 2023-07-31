# by amounra 0120 : http://www.aumhaa.com
# written against Live 10.1.7 release on 011720


from ableton.v2.control_surface.elements.color import Color
from aumhaa.v2.livid.colors import *

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



class UtilColors:

	class MainModes:
		Main = LividRGB.OFF
		Main_shifted = LividRGB.WHITE
		Full = LividRGB.OFF
		Full_shifted = LividRGB.WHITE


	class Option:
		Selected = LividRGB.WHITE
		Unselected = LividRGB.CYAN
		On = LividRGB.WHITE
		Off = LividRGB.BLUE
		Unused = LividRGB.OFF

	class ItemNavigation:
		ItemNotSelected = LividRGB.MAGENTA
		ItemNotSelectedOff = LividRGB.OFF
		ItemSelected = LividRGB.CYAN
		ItemSelectedOff = LividRGB.WHITE
		NoItem = LividRGB.OFF

	class EditModeOptions:
		ItemNotSelected = LividRGB.BLUE
		ItemSelected = LividRGB.YELLOW
		NoItem = LividRGB.OFF

	class DeviceNavigation:
		ItemNotSelected = LividRGB.MAGENTA
		ItemNotSelectedOff = LividRGB.OFF
		ItemSelected = LividRGB.CYAN
		ItemSelectedOff = LividRGB.WHITE
		NoItem = LividRGB.OFF

	class BankSelection:
		ItemNotSelected = LividRGB.MAGENTA
		ItemSelected = LividRGB.CYAN
		NoItem = LividRGB.OFF


	class ChainNavigation:
		ItemNotSelected = LividRGB.GREEN
		ItemSelected = LividRGB.RED
		NoItem = LividRGB.OFF


	class ModeButtons:
		Main = LividRGB.WHITE
		Select = LividRGB.RED
		Clips = LividRGB.GREEN


	class DefaultButton:
		On = LividRGB.WHITE
		Off = LividRGB.OFF
		Disabled = LividRGB.OFF
		Alert = LividRGB.RED
		Transparent = LividRGB.WHITE

	class List:
		ScrollerOn = LividRGB.GREEN
		ScrollerOff = LividRGB.MAGENTA

	class Session:
		StopClipDisabled = LividRGB.OFF
		StopClipTriggered = LividRGB.BLUE
		StopClip = LividRGB.BLUE
		Scene = LividRGB.CYAN
		NoScene = LividRGB.OFF
		SceneTriggered = LividRGB.GREEN
		ClipTriggeredPlay = LividRGB.GREEN
		ClipTriggeredRecord = LividRGB.RED
		RecordButton = LividRGB.OFF
		ClipEmpty = LividRGB.OFF
		ClipStopped = LividRGB.WHITE
		ClipStarted = LividRGB.GREEN
		ClipRecording = LividRGB.RED
		NavigationButtonOn = LividRGB.CYAN
		NavigationButtonOff = LividRGB.YELLOW
		ZoomOn = LividRGB.WHITE
		ZoomOff = LividRGB.WHITE
		FireNextArm = LividRGB.RED
		Delete = LividRGB.BLUE
		DeletePressed = LividRGB.WHITE
		Select = LividRGB.BLUE
		SelectPressed = LividRGB.WHITE
		Duplicate = Color(70)
		DuplicatePressed = Color(80)

	class Zooming:
		Selected = LividRGB.YELLOW
		Stopped = LividRGB.WHITE
		Playing = LividRGB.GREEN
		Empty = LividRGB.OFF


	class LoopSelector:
		Playhead = LividRGB.YELLOW
		OutsideLoop = LividRGB.BLUE
		InsideLoopStartBar = LividRGB.CYAN
		SelectedPage = LividRGB.WHITE
		InsideLoop = LividRGB.CYAN
		PlayheadRecord = LividRGB.RED
		Bank = LividRGB.MAGENTA
		ShiftLoop = LividRGB.WHITE
		LatestLoop = LividRGB.YELLOW


	class Transport:
		PlayOn = LividRGB.GREEN
		PlayOff = LividRGB.OFF
		StopOn = LividRGB.BLUE
		StopOff = LividRGB.BLUE
		RecordOn = LividRGB.RED
		RecordOff = LividRGB.BLUE
		OverdubOn = LividRGB.RED
		OverdubOff = LividRGB.MAGENTA
		SeekBackwardOn = LividRGB.CYAN
		SeekBackwardOff = LividRGB.CYAN
		LoopOn = LividRGB.YELLOW
		LoopOff = LividRGB.OFF
		MetroOn = LividRGB.BLUE
		MetroOff = LividRGB.CYAN

	class Auto_Arm:
		Enabled = LividRGB.RED
		Disabled = LividRGB.WHITE

	class Mixer:
		SoloOn = LividRGB.BLUE
		SoloOff = LividRGB.WHITE
		MuteOn = LividRGB.YELLOW
		MuteOff = LividRGB.WHITE
		ArmSelected = LividRGB.RED
		ArmSelectedImplicit = LividRGB.MAGENTA
		ArmUnselected = LividRGB.RED
		ArmOff = LividRGB.WHITE
		StopClip = LividRGB.BLUE
		SelectedOn = LividRGB.WHITE
		SelectedOff = LividRGB.OFF
		ArmOn = LividRGB.RED


	class Recording:
		On = LividRGB.RED
		Transition = LividRGB.MAGENTA
		Off = LividRGB.MAGENTA


	class Automation:
		On = LividRGB.WHITE
		Off = LividRGB.YELLOW


	class Recorder:
		On = LividRGB.WHITE
		Off = LividRGB.BLUE
		NewOn = LividRGB.YELLOW
		NewOff = LividRGB.YELLOW
		FixedOn = LividRGB.CYAN
		FixedOff = LividRGB.CYAN
		RecordOn = LividRGB.MAGENTA
		RecordOff = LividRGB.MAGENTA
		AutomationOn = LividRGB.YELLOW
		AutomationOff = LividRGB.YELLOW
		FixedAssigned = LividRGB.MAGENTA
		FixedNotAssigned = LividRGB.OFF


	class Device:
		NavOn = LividRGB.MAGENTA
		NavOff = LividRGB.OFF
		BankOn = LividRGB.YELLOW
		BankOff = LividRGB.OFF
		ChainNavOn = LividRGB.RED
		ChainNavOff = LividRGB.OFF
		ContainNavOn = LividRGB.CYAN
		ContainNavOff = LividRGB.OFF

	class NoteEditor:

		class Step:
			Low = LividRGB.CYAN
			High = LividRGB.WHITE
			Full = LividRGB.YELLOW
			Muted = LividRGB.YELLOW
			StepEmpty = LividRGB.OFF


		class StepEditing:
			High = LividRGB.GREEN
			Low = LividRGB.CYAN
			Full = LividRGB.YELLOW
			Muted = LividRGB.WHITE


		StepEmpty = LividRGB.OFF
		StepEmptyBase = LividRGB.OFF
		StepEmptyScale = LividRGB.OFF
		StepDisabled = LividRGB.OFF
		Playhead = Color(31)
		PlayheadRecord = Color(31)
		StepSelected = LividRGB.GREEN
		QuantizationSelected = LividRGB.RED
		QuantizationUnselected = LividRGB.MAGENTA


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

	class MonoInstrument:

		PressFlash = LividRGB.WHITE
		OffsetOnValue = LividRGB.GREEN
		OffsetOffValue = LividRGB.OFF
		ScaleOffsetOnValue = LividRGB.RED
		ScaleOffsetOffValue = LividRGB.OFF
		SplitModeOnValue = LividRGB.WHITE
		SplitModeOffValue = LividRGB.OFF
		SequencerModeOnValue = LividRGB.CYAN
		SequencerModeOffValue = LividRGB.OFF
		DrumOffsetOnValue = LividRGB.MAGENTA
		DrumOffsetOffValue = LividRGB.OFF
		VerticalOffsetOnValue = LividRGB.BLUE
		VerticalOffsetOffValue = LividRGB.OFF

		class Keys:
			SelectedNote = LividRGB.GREEN
			RootWhiteValue = LividRGB.RED
			RootBlackValue = LividRGB.MAGENTA
			WhiteValue = LividRGB.CYAN
			BlackValue = LividRGB.BLUE


		class Drums:
			SelectedNote = LividRGB.BLUE
			EvenValue = LividRGB.GREEN
			OddValue = LividRGB.MAGENTA
