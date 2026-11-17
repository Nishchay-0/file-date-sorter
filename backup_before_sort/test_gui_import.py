import sys
import os
sys.path.insert(0, os.getcwd())

try:
    # Try to import the main GUI class from gui_modules.app
    from gui_modules.app import SmartFileOrganizerGUI
    print("Imported SmartFileOrganizerGUI successfully")
except Exception as e:
    print(f"Failed to import SmartFileOrganizerGUI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try to instantiate (this might fail if we don't have a display, but we can catch tkinter errors)
try:
    # We'll create an instance but not run the mainloop
    # We need to mock the master? Actually, the class likely expects a master Tk instance.
    # Let's see the constructor signature by looking at the source? We'll just try to import and see if there are any immediate errors.
    pass
except Exception as e:
    print(f"Error during instantiation: {e}")
    traceback.print_exc()

print("GUI import test completed")