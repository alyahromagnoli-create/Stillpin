"""Windows hotkey / Explorer file drop integration, with safe teardown."""
import ctypes as C
from ctypes import wintypes as W

def dpi_aware():
    try:
        C.windll.user32.SetProcessDpiAwarenessContext(C.c_void_p(-4))
    except (AttributeError, OSError):
        C.windll.user32.SetProcessDPIAware()

class Bridge:
    def __init__(self, widget, on_files, on_capture,register_hotkeys=True):
        self.widget = widget
        self.user = C.windll.user32
        self.shell = C.windll.shell32
        self.user.GetParent.argtypes = [W.HWND]
        self.user.GetParent.restype = W.HWND
        self.hwnd = self.user.GetParent(widget.winfo_id()) or widget.winfo_id()
        self.proc_type = C.WINFUNCTYPE(C.c_ssize_t, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
        self.user.SetWindowLongPtrW.argtypes = [W.HWND, C.c_int, C.c_void_p]
        self.user.SetWindowLongPtrW.restype = C.c_void_p
        self.user.CallWindowProcW.argtypes = [C.c_void_p, W.HWND, W.UINT, W.WPARAM, W.LPARAM]
        self.user.CallWindowProcW.restype = C.c_ssize_t
        self.shell.DragQueryFileW.argtypes = [W.HANDLE, W.UINT, W.LPWSTR, W.UINT]
        self.shell.DragFinish.argtypes = [W.HANDLE]
        self.shell.DragAcceptFiles.argtypes = [W.HWND, W.BOOL]
        self.user.RegisterHotKey.argtypes = [W.HWND, C.c_int, W.UINT, W.UINT]
        self.user.UnregisterHotKey.argtypes = [W.HWND, C.c_int]

        def handler(hwnd, msg, wp, lp):
            if msg == 0x233:
                paths = []
                try:
                    count = self.shell.DragQueryFileW(wp, 0xFFFFFFFF, None, 0)
                    for i in range(count):
                        size = self.shell.DragQueryFileW(wp, i, None, 0)
                        buf = C.create_unicode_buffer(size + 1)
                        self.shell.DragQueryFileW(wp, i, buf, size + 1)
                        paths.append(buf.value)
                finally:
                    self.shell.DragFinish(wp)
                widget.after_idle(lambda: on_files(paths))
                return 0
            if msg == 0x312 and wp == 0xB041:
                widget.after_idle(on_capture)
                return 0
            return self.user.CallWindowProcW(self.previous, hwnd, msg, wp, lp)

        self.callback = self.proc_type(handler)
        self.previous = self.user.SetWindowLongPtrW(self.hwnd, -4, C.cast(self.callback, C.c_void_p))
        self.shell.DragAcceptFiles(self.hwnd, True)
        self.hotkey = False
        self.hotkey_label = ''
        choices=((6, ord('A'), 'Ctrl+Alt+A'), (7, ord('A'), 'Ctrl+Alt+Shift+A'), (6, 0x71, 'Ctrl+Alt+F2')) if register_hotkeys else ()
        for modifiers, key, label in choices:
            if self.user.RegisterHotKey(self.hwnd, 0xB041, 0x4000 | modifiers, key):
                self.hotkey = True
                self.hotkey_label = label
                break

    def close(self):
        if self.hotkey:
            self.user.UnregisterHotKey(self.hwnd, 0xB041)
        self.shell.DragAcceptFiles(self.hwnd, False)
        self.user.SetWindowLongPtrW(self.hwnd, -4, self.previous)
