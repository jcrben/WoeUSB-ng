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
            result = subprocess.run([
                'kdialog', '--getopenfilename', 
                '.', 'ISO files (*.iso)|*.iso All files (*)|*'
            ], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                selected_path = result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Method 2: Try zenity (GNOME file dialog) 
        if not selected_path:
            try:
                import subprocess
                result = subprocess.run([
                    'zenity', '--file-selection', 
                    '--title=Select ISO file',
                    '--file-filter=ISO files (*.iso) | *.iso',
                    '--file-filter=All files | *'
                ], capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    selected_path = result.stdout.strip()
            except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        # Method 3: Try tkinter file dialog
        if not selected_path:
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                selected_path = filedialog.askopenfilename(
                    title="Select ISO file",
                    filetypes=[("ISO files", "*.iso"), ("All files", "*.*")]
                )
                root.destroy()
            except Exception:
                pass
        
        # Method 4: Try wxPython generic file dialog (safer than native)
        if not selected_path:
            try:
                # Force generic dialog
                dlg = wx.FileDialog(
                    self, 
                    message=self.message,
                    wildcard=self.wildcard,
                    style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
                )
                if dlg.ShowModal() == wx.ID_OK:
                    selected_path = dlg.GetPath()
                dlg.Destroy()
            except Exception:
                pass
        
        # Method 5: Fallback to text entry
        if not selected_path:
            dlg = wx.TextEntryDialog(self, 
                               f"{self.message}\nPlease enter the full path:", 
                               "File Path", 
                               self.path)
            if dlg.ShowModal() == wx.ID_OK:
                selected_path = dlg.GetValue()
            dlg.Destroy()
        
        # Update the path if we got something
        if selected_path:
            self.SetPath(selected_path)
        
    def GetPath(self):
        return self.path
        
    def GetValue(self):
        return self.path
        
    def SetPath(self, path):
        self.path = path
        if hasattr(self, 'text_ctrl'):
            self.text_ctrl.SetValue(path)
            
    def SetValue(self, value):
        self.SetPath(value)
    
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
        return self.GetValue()
    
    def SetPath(self, path):
        self.SetValue(path)

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
