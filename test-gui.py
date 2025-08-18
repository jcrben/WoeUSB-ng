#!/usr/bin/env python3
"""
Minimal test to check if GUI can start without crashing
"""
import os
import sys

# Set environment before importing wx
os.environ['GTK_A11Y'] = 'none'
os.environ['GTK_DEBUG'] = ''
os.environ['WX_USE_GENERIC_CONTROLS'] = '1'
os.environ['WX_DISABLE_NATIVE_DIALOGS'] = '1'
os.environ['GDK_BACKEND'] = 'x11'

# Import our patches first
try:
    import wx_patch
    print("wx_patch imported successfully")
except Exception as e:
    print(f"Failed to import wx_patch: {e}")

try:
    import wx
    print("wxPython imported successfully")
    
    app = wx.App()
    print("wxApp created successfully")
    
    # Create a simple test window
    frame = wx.Frame(None, title="Test GUI", size=(300, 200))
    panel = wx.Panel(frame)
    sizer = wx.BoxSizer(wx.VERTICAL)
    
    label = wx.StaticText(panel, label="GUI Test - No File Dialogs")
    button = wx.Button(panel, label="Test Button")
    
    sizer.Add(label, 0, wx.ALL | wx.CENTER, 10)
    sizer.Add(button, 0, wx.ALL | wx.CENTER, 10)
    
    panel.SetSizer(sizer)
    frame.Show()
    print("Test window created and shown")
    
    app.MainLoop()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
