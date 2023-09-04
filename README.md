# modGrid
Max and Python support for modGrid Beta

Built against Live Beta 11.3.20b1.
Add the folders from Python Scripts (aumhaa, modGrid) to your Ableton User Libraries Remote Scripts folder (you may need to create it).  
Normally, this will be at ~/Music/Ableton/User Library/Remote Scripts/.  If you've set a custom path, you should be able to find the correct location by looking in Ableton's file settings. 

Documentation for modGrid app forthcoming...


Changelog:  

Beta(4.0) - 9.3.23:
    Moved aumhaa dependencies to v3 to avoid conflicts with older scripts.
    Drumrack and Session now mirror colors from Live's GUI.
    New skinning for many controls.  
    Buttons now flash when pressed via App.
    New Device Selection Component added to top row buttons while holding down Device mode button.
    New Dial Look.
    Added modLock, so that grid can be locked to mod but device component can still be navigated to selected device in Live's GUI.
    Added Support for ModViews:  Full, Half, Quarter, Tall, Wide, Dial, Mixer, Sequencer.  (View currently only accessible through unpublished mods)
    Fix for text labels on grid buttons below 4th row.
    General improvements and bugfixes for script, a lot of internal refactoring.


Beta(3.0) - 7.31.23:
    Added Piano Keyboard view (Alt + Instrument)
    Added Initial MiraWeb implementation (requires new modObject, forthcoming)
    Device Navigation updates:
        Single device button press now disables bank mode when in bank mode.
        Long device button press now toggles device on/off
        Improved coloring
    New button now initiates recording instead of merely advancing to next empty clipslot.
    Duplicate moved to Alt+O.





