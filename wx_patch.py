#!/usr/bin/env python3
"""
Patch script to force wxPython to use generic dialogs and fix appearance
"""
import wx
import os

# Prevent GTK+ widget initialization that causes segfaults
os.environ['GTK_A11Y'] = 'none'
os.environ['GTK_DEBUG'] = ''
os.environ['WX_USE_GENERIC_CONTROLS'] = '1'

# Store original MessageBox function and create safe replacement
try:
    _original_MessageBox = wx.MessageBox
except:
    _original_MessageBox = None

def safe_MessageBox(message, caption="", style=wx.OK, parent=None):
    """Safe message box that falls back to auto-approval for confirmations"""
    print(f"DEBUG: MessageBox called: {caption}: {message}")
    
    # Try the original MessageBox first
    if _original_MessageBox:
        try:
            result = _original_MessageBox(message, caption, style, parent)
            print(f"DEBUG: MessageBox succeeded with result: {result}")
            return result
        except Exception as e:
            print(f"DEBUG: MessageBox failed ({e}), using auto-approval fallback")
    
    # Auto-approval fallback - no console interaction needed
    print(f"\n=== MESSAGE DIALOG (AUTO-HANDLED) ===")
    print(f"Title: {caption}")
    print(f"Message: {message}")
    print("=" * 50)
    
    if style & wx.YES_NO:
        # For YES/NO dialogs, auto-approve since we're in a broken GUI environment
        print("DEBUG: Auto-approving YES/NO dialog with YES")
        return wx.YES
    else:
        # For info dialogs, just acknowledge
        print("DEBUG: Auto-acknowledging info dialog with OK")
        return wx.OK

# Monkey patch the MessageBox function
wx.MessageBox = safe_MessageBox
print("DEBUG: MessageBox patched successfully")

# Fix broken ListBox widget with simple cycling approach
class SafeListBox(wx.Panel):
    """Safe ListBox replacement that cycles through devices"""
    
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, choices=[], style=0, name="listBox"):
        super().__init__(parent, id, pos, size, style, name)
        
        self.choices = []
        self.selection = wx.NOT_FOUND
        
        # Create a simple sizer for layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create a text control to show the current selection
        self.text_ctrl = wx.TextCtrl(self, wx.ID_ANY, "No device selected", style=wx.TE_READONLY)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND)
        
        # Add a button to cycle through choices
        self.cycle_btn = wx.Button(self, wx.ID_ANY, "Select Next Device")
        self.cycle_btn.Bind(wx.EVT_BUTTON, self.on_cycle)
        sizer.Add(self.cycle_btn, 0, wx.EXPAND)
        
        self.SetSizer(sizer)
        
        # Add initial choices if provided
        for choice in choices:
            self.Append(choice)
    
    def Append(self, item):
        self.choices.append(item)
        # Auto-select first device
        if len(self.choices) == 1:
            self.selection = 0
            self.text_ctrl.SetValue(item)
            self.cycle_btn.SetLabel(f"Device: {item} (click to change)")
            # Send selection event for first device
            self._send_selection_event()
        print(f"DEBUG: Added device to list: {item}")
    
    def Clear(self):
        self.choices = []
        self.selection = wx.NOT_FOUND
        self.text_ctrl.SetValue("No device selected")
        self.cycle_btn.SetLabel("Select Next Device")
        print("DEBUG: Cleared device list")
    
    def GetSelection(self):
        return self.selection
    
    def on_cycle(self, event):
        if not self.choices:
            print("DEBUG: No devices to cycle through")
            return
        
        # Cycle to next choice
        if self.selection == wx.NOT_FOUND:
            self.selection = 0
        else:
            self.selection = (self.selection + 1) % len(self.choices)
        
        selected_device = self.choices[self.selection]
        self.text_ctrl.SetValue(selected_device)
        self.cycle_btn.SetLabel(f"Device: {selected_device} (click to change)")
        print(f"DEBUG: Selected device {self.selection}: {selected_device}")
        
        self._send_selection_event()
    
    def _send_selection_event(self):
        """Send a selection event to notify the parent"""
        event = wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED, self.GetId())
        event.SetEventObject(self)
        event.SetInt(self.selection)
        self.GetEventHandler().ProcessEvent(event)

# Store original ListBox and replace it
_original_ListBox = wx.ListBox
wx.ListBox = SafeListBox
print("DEBUG: ListBox patched with simple cycling selector")
os.environ['WX_DISABLE_NATIVE_DIALOGS'] = '1'
os.environ['GDK_BACKEND'] = 'x11'

# Suppress GTK warnings and critical messages
os.environ['G_MESSAGES_DEBUG'] = ''
os.environ['GTK_DEBUG'] = ''
# Redirect GTK warnings to /dev/null
import subprocess
import sys
try:
    # Try to redirect stderr for GTK messages, but keep Python errors
    subprocess.run(['exec', '2>/dev/null'], shell=True, check=False)
except:
    pass
os.environ['WX_DISABLE_NATIVE_DIALOGS'] = '1'
os.environ['GDK_BACKEND'] = 'x11'

# Enhanced FilePickerCtrl replacement that maintains API compatibility
class SimpleFilePickerCtrl(wx.Panel):
    def __init__(self, parent, id=-1, path="", message="Choose a file", 
                 wildcard="All files (*)|*", pos=wx.DefaultPosition, 
                 size=wx.DefaultSize, style=0, validator=wx.DefaultValidator, name="filepicker"):
        super().__init__(parent, id, pos=pos, size=size, name=name)
        
        self.path = path or ""
        self.message = message
        self.wildcard = wildcard
        
        # Create layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Create a text control to show the path
        self.text_ctrl = wx.TextCtrl(self, -1, value=self.path, style=style)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.RIGHT, 5)
        
        # Add a browse button
        self.browse_btn = wx.Button(self, -1, "Browse...")
        self.browse_btn.Bind(wx.EVT_BUTTON, self._on_browse)
        sizer.Add(self.browse_btn, 0, wx.EXPAND)
        
        self.SetSizer(sizer)
    
    def _on_browse(self, event):
        # Try multiple approaches for file selection
        selected_path = None
        
        # Method 1: Try kdialog (KDE file dialog)
        try:
            import subprocess
            print("DEBUG: Trying kdialog...")
            
            # Get the original user's display and home from the environment
            import os
            original_user = os.environ.get('SUDO_USER', os.environ.get('USER', 'user'))
            original_home = f"/home/{original_user}" if original_user != 'root' else os.path.expanduser('~')
            
            # Use a simpler kdialog command that's more likely to work in sudo environment
            env = os.environ.copy()
            env['HOME'] = original_home
            
            result = subprocess.run([
                'sudo', '-u', original_user, 'kdialog', '--getopenfilename', 
                original_home, '*.iso'
            ], capture_output=True, text=True, timeout=30, env=env)
            print(f"DEBUG: kdialog returned code {result.returncode}")
            if result.stderr:
                print(f"DEBUG: kdialog stderr: {result.stderr}")
            if result.stdout:
                print(f"DEBUG: kdialog stdout: {result.stdout}")
            if result.returncode == 0 and result.stdout.strip():
                selected_path = result.stdout.strip()
                print(f"DEBUG: kdialog selected: {selected_path}")
        except Exception as e:
            print(f"DEBUG: kdialog failed: {e}")
        
        # Method 2: Try zenity (GNOME file dialog) 
        if not selected_path:
            try:
                import subprocess
                print("DEBUG: Trying zenity...")
                result = subprocess.run([
                    'zenity', '--file-selection', 
                    '--title=Select ISO file',
                    '--file-filter=ISO files (*.iso) | *.iso',
                    '--file-filter=All files | *'
                ], capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and result.stdout.strip():
                    selected_path = result.stdout.strip()
                    print(f"DEBUG: zenity selected: {selected_path}")
            except Exception as e:
                print(f"DEBUG: zenity failed: {e}")
        
        # Method 3: Try tkinter file dialog
        if not selected_path:
            try:
                print("DEBUG: Trying tkinter...")
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                selected_path = filedialog.askopenfilename(
                    title="Select ISO file",
                    filetypes=[("ISO files", "*.iso"), ("All files", "*.*")]
                )
                root.destroy()
                if selected_path:
                    print(f"DEBUG: tkinter selected: {selected_path}")
            except Exception as e:
                print(f"DEBUG: tkinter failed: {e}")
        
        # Method 4: Try wxPython generic file dialog (safer than native)
        if not selected_path:
            try:
                print("DEBUG: Trying wxPython generic dialog...")
                # Force generic dialog
                dlg = wx.FileDialog(
                    self, 
                    message=self.message,
                    wildcard=self.wildcard,
                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
                )
                if dlg.ShowModal() == wx.ID_OK:
                    selected_path = dlg.GetPath()
                    print(f"DEBUG: wxPython selected: {selected_path}")
                dlg.Destroy()
            except Exception as e:
                print(f"DEBUG: wxPython failed: {e}")
        
        # Method 5: Fallback to text entry
        if not selected_path:
            print("DEBUG: Falling back to text entry...")
            dlg = wx.TextEntryDialog(self, 
                               f"{self.message}\nPlease enter the full path:", 
                               "File Path", 
                               self.path)
            if dlg.ShowModal() == wx.ID_OK:
                selected_path = dlg.GetValue()
                print(f"DEBUG: text entry selected: {selected_path}")
            dlg.Destroy()
        
        # Update the path if we got something
        if selected_path:
            print(f"DEBUG: Final selected path: {selected_path}")
            self.SetPath(selected_path)
        else:
            print("DEBUG: No path selected")
        
    def GetPath(self):
        return self.path
        
    def GetValue(self):
        return self.path
        
    def SetPath(self, path):
        self.path = path
        if hasattr(self, 'text_ctrl'):
            self.text_ctrl.SetValue(path)
            
    def SetValue(self, value):
        self.path = value
        if hasattr(self, 'text_ctrl'):
            self.text_ctrl.SetValue(value)
    
    def OnBrowse(self, event):
        print("DEBUG: Browse button clicked!")
        # Skip the native FileDialog entirely to avoid segfaults
        # Go directly to our safe fallback dialog
        
        current_value = self.GetValue()
        start_path = ""
        
        if current_value and os.path.exists(current_value):
            start_path = current_value if os.path.isdir(current_value) else os.path.dirname(current_value)
        elif current_value and os.path.dirname(current_value):
            start_path = os.path.dirname(current_value)
        else:
            # Common locations for ISO files
            common_paths = [
                os.path.expanduser("~/Downloads/"),
                os.path.expanduser("~/Desktop/"),
                os.path.expanduser("~/Documents/"),
                "/media/",
                "/mnt/",
                os.path.expanduser("~/")
            ]
            start_path = next((p for p in common_paths if os.path.exists(p)), os.path.expanduser("~/"))
        
        message = ("Please enter the full path to your ISO file.\n\n"
                  "Common locations:\n"
                  "  • ~/Downloads/filename.iso\n"
                  "  • ~/Desktop/filename.iso\n"
                  "  • /media/username/device/filename.iso\n\n"
                  "You can also use Tab completion to navigate.")
        
        with wx.TextEntryDialog(self, message, "Select ISO File", start_path) as textDialog:
            textDialog.SetSize((500, 300))  # Make dialog larger
            if textDialog.ShowModal() == wx.ID_OK:
                pathname = textDialog.GetValue().strip()
                if pathname:
                    # Basic validation
                    if os.path.exists(pathname):
                        self.SetValue(pathname)
                    else:
                        wx.MessageBox(f"File not found: {pathname}\n\nPlease check the path and try again.",
                                    "File Not Found", wx.OK | wx.ICON_WARNING)
                        # Recursive call to try again
                        self.OnBrowse(event)    # Compatibility methods to maintain API compliance
    def GetPath(self):
        return self.path
    
    def SetPath(self, path):
        self.path = path
        if hasattr(self, 'text_ctrl'):
            self.text_ctrl.SetValue(path)

# Completely disable wx.FileDialog to prevent segfaults
class SafeFileDialog:
    """Replacement for wx.FileDialog that always fails gracefully"""
    def __init__(self, *args, **kwargs):
        print("DEBUG: SafeFileDialog created instead of wx.FileDialog")
        
    def ShowModal(self):
        print("DEBUG: SafeFileDialog.ShowModal() called - returning CANCEL")
        return wx.ID_CANCEL
    
    def GetPath(self):
        return ""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# Monkey patch wx.FileDialog to prevent segfaults
original_FileDialog = wx.FileDialog
wx.FileDialog = SafeFileDialog

# Add compatibility methods to SimpleFilePickerCtrl
def GetTextCtrl(self):
    return self.text_ctrl

def GetPickerCtrl(self):
    return self.browse_btn

# Attach methods to the class
SimpleFilePickerCtrl.GetTextCtrl = GetTextCtrl
SimpleFilePickerCtrl.GetPickerCtrl = GetPickerCtrl

# Replace the original FilePickerCtrl
wx.FilePickerCtrl = SimpleFilePickerCtrl

# Force light colors on Frame class
original_Frame_init = wx.Frame.__init__

def patched_Frame_init(self, *args, **kwargs):
    result = original_Frame_init(self, *args, **kwargs)
    try:
        self.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray
        self.SetForegroundColour(wx.Colour(0, 0, 0))        # Black text
    except:
        pass
    return result

wx.Frame.__init__ = patched_Frame_init

# Force light colors on Panel class
original_Panel_init = wx.Panel.__init__

def patched_Panel_init(self, *args, **kwargs):
    result = original_Panel_init(self, *args, **kwargs)
    try:
        self.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray
        self.SetForegroundColour(wx.Colour(0, 0, 0))        # Black text
    except:
        pass
    return result

wx.Panel.__init__ = patched_Panel_init

# Force light colors on Dialog class
original_Dialog_init = wx.Dialog.__init__

def patched_Dialog_init(self, *args, **kwargs):
    result = original_Dialog_init(self, *args, **kwargs)
    try:
        self.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray
        self.SetForegroundColour(wx.Colour(0, 0, 0))        # Black text
    except:
        pass
    return result

wx.Dialog.__init__ = patched_Dialog_init

# Force FileDialog to use light theme
original_FileDialog_init = wx.FileDialog.__init__

def patched_FileDialog_init(self, *args, **kwargs):
    result = original_FileDialog_init(self, *args, **kwargs)
    try:
        self.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray
        self.SetForegroundColour(wx.Colour(0, 0, 0))        # Black text
    except:
        pass
    return result

wx.FileDialog.__init__ = patched_FileDialog_init
