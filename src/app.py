import os
import sys
from pathlib import Path
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageGrab
from content import Library
from native import Bridge, dpi_aware

BG = '#f7f9fc'
PANEL = '#ffffff'
FG = '#171b23'
MUTED = '#596576'
ACCENT = '#c52b30'
LINE = '#dce2e9'

def window_icon(window):
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    icon = base / 'assets' / 'Stillpin.ico'
    if icon.exists():
        window.iconbitmap(default=str(icon))

def button(parent, text, command, accent=False):
    return tk.Button(parent, text=text, command=command, bg=ACCENT if accent else PANEL,
                     fg='#ffffff' if accent else FG, activebackground='#a62227' if accent else '#e8edf3', activeforeground='#ffffff' if accent else FG,
                     relief='flat', bd=0, padx=12, pady=7, cursor='hand2', font=('Microsoft YaHei UI', 10),
                     highlightthickness=1, highlightbackground=ACCENT if accent else LINE,
                     highlightcolor=FG, takefocus=True)

class Pin:
    def __init__(self, app, item):
        self.app, self.item = app, dict(item)
        self.page_number = max(0, min(int(item.get('page', 0)), item['pages'] - 1))
        self.scale, self.offset = 1., [0, 0]
        self.fitted = True
        self.win = tk.Toplevel(app.root)
        self.win.title('Stillpin · ' + item['name'])
        window_icon(self.win)
        self.win.configure(bg=BG)
        self.win.geometry(item.get('geometry', '560x460+160+140'))
        self.win.minsize(480, 220)
        self.top = tk.BooleanVar(value=item.get('topmost', True))
        self.win.attributes('-topmost', self.top.get())
        self.win.protocol('WM_DELETE_WINDOW', self.close)
        bar = tk.Frame(self.win, bg=BG)
        bar.pack(fill='x', padx=10, pady=8)
        self.pin_button = button(bar, '已置顶', self.toggle_top)
        self.pin_button.pack(side='left')
        button(bar, '适应', self.fit).pack(side='left', padx=2)
        button(bar, '1:1', self.actual).pack(side='left')
        button(bar, '另存', self.export).pack(side='right')
        self.alpha = tk.DoubleVar(value=max(.3, min(1., float(item.get('opacity', 1.)))))
        tk.Scale(bar, from_=.3, to=1., resolution=.05, orient='horizontal', variable=self.alpha,
                 command=self.opacity, showvalue=False, length=85, bg=BG, troughcolor=PANEL,
                 highlightthickness=0, bd=0).pack(side='right', padx=4)
        tk.Label(bar, text='透明度', fg=MUTED, bg=BG, font=('Microsoft YaHei UI', 9)).pack(side='right')
        self.status = tk.StringVar()
        footer = tk.Frame(self.win, bg=BG)
        footer.pack(side='bottom', fill='x', padx=12, pady=7)
        if item['kind'] == 'pdf':
            button(footer, '‹', lambda: self.turn(-1)).pack(side='left')
            button(footer, '›', lambda: self.turn(1)).pack(side='left', padx=3)
        tk.Label(footer, textvariable=self.status, fg=MUTED, bg=BG, font=('Microsoft YaHei UI', 9)).pack(side='left')
        if item['kind'] == 'text':
            frame = tk.Frame(self.win, bg=PANEL)
            frame.pack(fill='both', expand=True)
            scroll = ttk.Scrollbar(frame)
            scroll.pack(side='right', fill='y')
            text = tk.Text(frame, bg=PANEL, fg=FG, insertbackground=FG, wrap='word', bd=0,
                           padx=16, pady=16, font=('Microsoft YaHei UI', 11), yscrollcommand=scroll.set)
            text.pack(fill='both', expand=True)
            scroll.config(command=text.yview)
            text.insert('1.0', app.library.text(item))
            text.config(state='disabled')
            self.image = None
            self.status.set('文本预览 · 可选择复制')
        else:
            self.image = app.library.page(item, self.page_number)
            self.canvas = tk.Canvas(self.win, bg='#edf1f6', highlightthickness=0, cursor='fleur')
            self.canvas.pack(fill='both', expand=True)
            self.canvas.bind('<Configure>', lambda e: self.render())
            self.canvas.bind('<MouseWheel>', self.wheel)
            self.canvas.bind('<ButtonPress-1>', self.pan_start)
            self.canvas.bind('<B1-Motion>', self.pan)
            self.canvas.bind('<Double-Button-1>', lambda e: self.fit())
        self.win.bind('<Control-v>', lambda e: app.paste())
        self.win.bind('<Escape>', lambda e: app.show_manager())
        self.win.bind('<Control-s>', lambda e: self.export())
        self.win.bind('<Left>', lambda e: self.turn(-1))
        self.win.bind('<Right>', lambda e: self.turn(1))
        self.toggle_top(update_only=True)
        self.opacity()
        self.win.after(80, self.fit)

    def toggle_top(self, update_only=False):
        if not update_only:
            self.top.set(not self.top.get())
        self.win.attributes('-topmost', self.top.get())
        self.pin_button.config(text='已置顶' if self.top.get() else '置顶')

    def opacity(self, *_):
        self.win.attributes('-alpha', self.alpha.get())

    def fit(self):
        if self.image is not None:
            self.fitted = True
            self.offset = [0, 0]
            self.render()

    def actual(self):
        if self.image is not None:
            self.fitted = False
            self.scale = 1.
            self.offset = [0, 0]
            self.render()

    def render(self):
        if self.image is None:
            return
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 5 or h < 5:
            return
        if self.fitted:
            self.scale = min((w-16) / self.image.width, (h-16) / self.image.height)
        self.scale = max(.02, min(self.scale, 8., 7000 / max(self.image.size)))
        size = (max(1, round(self.image.width*self.scale)), max(1, round(self.image.height*self.scale)))
        image = self.image.resize(size, Image.Resampling.LANCZOS)
        if image.mode == 'RGBA':
            bg = Image.new('RGBA', image.size, '#e5e9ef')
            bg.alpha_composite(image)
            image = bg.convert('RGB')
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.delete('all')
        self.canvas.create_image(w/2+self.offset[0], h/2+self.offset[1], image=self.photo)
        page = f'第 {self.page_number+1}/{self.item["pages"]} 页 · ' if self.item['kind'] == 'pdf' else ''
        self.status.set(f'{page}{self.scale:.0%} · 滚轮缩放 / 拖动平移')

    def wheel(self, event):
        old = self.scale
        self.fitted = False
        self.scale = max(.02, min(8., old * (1.15 if event.delta > 0 else 1/1.15)))
        factor = self.scale / old
        self.offset = [(self.offset[0] - (event.x-self.canvas.winfo_width()/2))*factor + event.x-self.canvas.winfo_width()/2,
                       (self.offset[1] - (event.y-self.canvas.winfo_height()/2))*factor + event.y-self.canvas.winfo_height()/2]
        self.render()

    def pan_start(self, event):
        self.drag = (event.x, event.y, *self.offset)

    def pan(self, event):
        self.offset = [self.drag[2]+event.x-self.drag[0], self.drag[3]+event.y-self.drag[1]]
        self.render()

    def turn(self, delta):
        if self.item['kind'] != 'pdf':
            return
        new = self.page_number + delta
        if 0 <= new < self.item['pages']:
            try:
                image = self.app.library.page(self.item, new)
                self.page_number, self.image = new, image
                self.fit()
            except Exception as exc:
                messagebox.showerror('无法翻页', str(exc), parent=self.win)

    def export(self):
        folder = self.app.library.root / 'exports'
        folder.mkdir(exist_ok=True)
        if self.image is None:
            suffix, default = '.txt', Path(self.item['name']).stem + '.txt'
        else:
            suffix, default = '.png', Path(self.item['name']).stem + f'_{self.page_number+1}.png'
        name = filedialog.asksaveasfilename(parent=self.win, initialdir=folder, initialfile=default,
                                           defaultextension=suffix, filetypes=[('预览内容', '*'+suffix)])
        if name:
            try:
                if self.image is None:
                    Path(name).write_text(self.app.library.text(self.item), encoding='utf-8')
                else:
                    self.image.save(name, 'PNG')
            except Exception as exc:
                messagebox.showerror('保存失败', str(exc), parent=self.win)

    def state(self):
        return dict(self.item, geometry=self.win.geometry(), page=self.page_number,
                    opacity=self.alpha.get(), topmost=self.top.get())

    def close(self):
        self.app.pins.remove(self)
        self.win.destroy()
        self.app.refresh()
        self.app.save()

class Capture:
    def __init__(self, app, image, origin):
        self.app, self.image, self.origin = app, image, origin
        self.win = tk.Toplevel(app.root)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        x, y = origin
        # wm_geometry treats negative coordinates as right/bottom offsets; move with Win32 instead.
        self.win.geometry(f'{image.width}x{image.height}+0+0')
        self.canvas = tk.Canvas(self.win, highlightthickness=0, cursor='crosshair')
        self.canvas.pack(fill='both', expand=True)
        self.photo = ImageTk.PhotoImage(image)
        self.canvas.create_image(0, 0, anchor='nw', image=self.photo)
        self.canvas.create_rectangle(16, 16, 560, 58, fill=BG, outline=ACCENT)
        self.canvas.create_text(30, 37, anchor='w', text='拖动框选区域 · 松开即贴图 · Esc 取消',
                                fill=FG, font=('Microsoft YaHei UI', 13))
        self.canvas.bind('<ButtonPress-1>', self.start)
        self.canvas.bind('<B1-Motion>', self.move)
        self.canvas.bind('<ButtonRelease-1>', self.finish)
        self.win.bind('<Escape>', lambda e: self.cancel())
        self.win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(self.win.winfo_id())
        ctypes.windll.user32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
        ctypes.windll.user32.SetWindowPos(hwnd, -1, x, y, image.width, image.height, 0x40)
        self.win.focus_force()
        self.win.grab_set()
        self.rectangle = None

    def start(self, event):
        self.begin = (event.x, event.y)
        if self.rectangle:
            self.canvas.delete(self.rectangle)
        self.rectangle = self.canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                                      outline=ACCENT, width=3)

    def move(self, event):
        if hasattr(self, 'begin'):
            self.canvas.coords(self.rectangle, *self.begin, event.x, event.y)

    def finish(self, event):
        if not hasattr(self, 'begin'):
            return
        x0, x1 = sorted((self.begin[0], event.x))
        y0, y1 = sorted((self.begin[1], event.y))
        box = (max(0, x0), max(0, y0), min(self.image.width, x1), min(self.image.height, y1))
        self.cancel()
        if box[2]-box[0] > 3 and box[3]-box[1] > 3:
            self.app.add(self.app.library.import_image(self.image.crop(box), '区域截图'))

    def cancel(self):
        self.win.grab_release()
        self.win.destroy()
        self.app.capture = None
        self.app.restore_windows()

class App:
    def __init__(self, root, data):
        self.root, self.library = root, Library(data)
        self.pins, self.capture = [], None
        root.title('Stillpin · 截图贴图板')
        window_icon(root)
        root.geometry('580x600+60+80')
        root.minsize(550, 460)
        root.configure(bg=BG)
        root.option_add('*Font', ('Microsoft YaHei UI', 10))
        root.protocol('WM_DELETE_WINDOW', self.quit)
        top = tk.Frame(root, bg=BG)
        top.pack(fill='x', padx=28, pady=(30, 23))
        tk.Label(top, text='Stillpin', fg=FG, bg=BG, font=('Segoe UI', 29, 'bold')).pack(side='left', anchor='s')
        tk.Label(top, text='截图贴图板', fg=MUTED, bg=BG, font=('Microsoft YaHei UI', 10)).pack(side='right', anchor='s', pady=7)
        tk.Frame(root, height=1, bg=FG).pack(fill='x', padx=28)
        actions = tk.Frame(root, bg=BG)
        actions.pack(fill='x', padx=28, pady=(24, 12))
        button(actions, '区域截图', self.screenshot, True).pack(side='left', padx=(0, 8))
        button(actions, '粘贴图片', self.paste).pack(side='left', padx=(0, 8))
        button(actions, '打开文件', self.open_files).pack(side='left')
        self.hint = tk.StringVar(value='Ctrl+Alt+A 截图 · Ctrl+V 粘贴 · 支持拖入文件')
        tk.Label(root, textvariable=self.hint, fg=MUTED, bg=BG, anchor='w', font=('Microsoft YaHei UI', 9)).pack(fill='x', padx=28, pady=(0, 28))
        label_row = tk.Frame(root, bg=BG)
        label_row.pack(fill='x', padx=28, pady=(0, 10))
        tk.Label(label_row, text='参考文件', fg=FG, bg=BG, font=('Microsoft YaHei UI', 11, 'bold')).pack(side='left')
        self.count = tk.StringVar(value='0 项')
        tk.Label(label_row, textvariable=self.count, fg=MUTED, bg=BG, font=('Microsoft YaHei UI', 9)).pack(side='right')
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('Swiss.Treeview', background=PANEL, fieldbackground=PANEL, foreground=FG,
                        borderwidth=0, relief='flat', rowheight=42, font=('Microsoft YaHei UI', 10))
        style.configure('Swiss.Treeview.Heading', background=BG, foreground=MUTED,
                        relief='flat', borderwidth=0, font=('Microsoft YaHei UI', 9), padding=(12, 8))
        style.map('Swiss.Treeview', background=[('selected', '#e2e8f1')], foreground=[('selected', FG)])
        style.map('Swiss.Treeview.Heading', background=[('active', BG)])
        self.list_frame = tk.Frame(root, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        self.list_frame.pack(fill='both', expand=True, padx=28, pady=(0, 16))
        self.list = ttk.Treeview(self.list_frame, columns=('name', 'kind'), show='headings', style='Swiss.Treeview', selectmode='browse')
        self.list.heading('name', text='名称', anchor='w')
        self.list.heading('kind', text='格式', anchor='w')
        self.list.column('name', width=350, minwidth=120, anchor='w')
        self.list.column('kind', width=75, minwidth=60, stretch=False, anchor='w')
        scrollbar = ttk.Scrollbar(self.list_frame, orient='vertical', command=self.list.yview)
        scrollbar.pack(side='right', fill='y')
        self.list.configure(yscrollcommand=scrollbar.set)
        self.list.pack(fill='both', expand=True)
        self.empty = tk.Label(self.list_frame, text='添加一张参考图\n\n截图、粘贴或拖入文件', bg=PANEL, fg=MUTED,
                              font=('Microsoft YaHei UI', 11), justify='center')
        self.list.bind('<Double-Button-1>', lambda e: self.focus_pin())
        row = tk.Frame(root, bg=BG)
        row.pack(side='bottom', fill='x', padx=28, pady=(0, 18))
        button(row, '显示 / 聚焦', self.focus_pin).pack(side='left')
        button(row, '隐藏 / 显示全部', self.toggle_all).pack(side='left', padx=6)
        button(row, '收起面板', root.iconify).pack(side='right')
        tk.Label(root, text='独立置顶  /  缩放平移  /  自动恢复',
                 anchor='w', fg=MUTED, bg=BG, font=('Microsoft YaHei UI', 9)).pack(side='bottom', fill='x', padx=28, pady=(12, 18))
        tk.Frame(root, height=1, bg=LINE).pack(side='bottom', fill='x', padx=28)
        # Allocate the fixed toolbar before the expanding list, including at minimum height.
        self.list_frame.pack_forget()
        self.list_frame.pack(fill='both', expand=True, padx=28, pady=(0, 16))
        root.bind('<Control-v>', lambda e: self.paste())
        root.update_idletasks()
        self.bridge = Bridge(root, self.import_paths, self.screenshot)
        if self.bridge.hotkey:
            self.hint.set(self.bridge.hotkey_label + ' 截图 · Ctrl+V 粘贴 · 可拖入文件')
        else:
            self.hint.set('截图快捷键被占用，请点击「区域截图」· Ctrl+V 粘贴')
        for item in self.library.load():
            self.add(item, save=False)
        self.refresh()
        self.save_timer = root.after(3000, self.autosave)

    def add(self, item, save=True):
        try:
            pin = Pin(self, item)
            self.pins.append(pin)
            self.refresh()
            if save:
                self.save()
            return pin
        except Exception as exc:
            # Clean up an incomplete preview window, keeping the main panel usable.
            for child in self.root.winfo_children():
                if isinstance(child, tk.Toplevel) and all(p.win != child for p in self.pins):
                    child.destroy()
            messagebox.showerror('无法预览', str(exc), parent=self.root)

    def refresh(self):
        self.list.delete(*self.list.get_children())
        for i, pin in enumerate(self.pins):
            tag = {'pdf': 'PDF', 'image': '图片', 'text': '文本'}[pin.item['kind']]
            self.list.insert('', 'end', iid=str(i), values=(pin.item['name'], tag))
        self.count.set(f'{len(self.pins)} 项')
        if self.pins:
            self.empty.place_forget()
        else:
            self.empty.place(relx=.5, rely=.55, anchor='center')

    def import_paths(self, paths):
        for path in paths:
            try:
                self.add(self.library.import_file(path))
            except Exception as exc:
                messagebox.showerror('导入失败', f'{Path(path).name}\n{exc}', parent=self.root)

    def open_files(self):
        files = filedialog.askopenfilenames(parent=self.root, initialdir=self.library.root.parent,
                    title='打开参考图 / PDF / 文本', filetypes=[('参考文件', '*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tif *.tiff *.pdf *.txt *.md *.py *.json *.csv'), ('所有文件', '*.*')])
        self.import_paths(files)

    def paste(self):
        try:
            data = ImageGrab.grabclipboard()
            if isinstance(data, Image.Image):
                self.add(self.library.import_image(data))
            elif isinstance(data, list):
                self.import_paths(data)
            else:
                messagebox.showinfo('粘贴图片', '剪贴板中没有图片或文件。可先用 Win+Shift+S 截图，再按 Ctrl+V。', parent=self.root)
        except Exception as exc:
            messagebox.showerror('粘贴失败', str(exc), parent=self.root)

    def focus_pin(self):
        selected = self.list.selection()
        if selected:
            win = self.pins[int(selected[0])].win
            win.deiconify()
            win.lift()
            win.focus_force()

    def show_manager(self):
        self.root.deiconify()
        self.root.lift()

    def toggle_all(self):
        show = any(pin.win.state() == 'withdrawn' for pin in self.pins)
        for pin in self.pins:
            pin.win.deiconify() if show else pin.win.withdraw()

    def screenshot(self):
        if self.capture is not None or getattr(self, 'capturing', False):
            return
        self.capturing = True
        self.hidden = [(win, win.state()) for win in [self.root] + [p.win for p in self.pins]]
        for win, _ in self.hidden:
            win.withdraw()
        self.root.after(220, self.start_capture)

    def start_capture(self):
        try:
            image = ImageGrab.grab(all_screens=True)
            user = ctypes.windll.user32
            origin = (user.GetSystemMetrics(76), user.GetSystemMetrics(77))
            self.capture = Capture(self, image, origin)
        except Exception as exc:
            self.restore_windows()
            messagebox.showerror('截图失败', str(exc), parent=self.root)
        finally:
            self.capturing = False

    def restore_windows(self):
        for win, state in getattr(self, 'hidden', []):
            if state == 'normal':
                win.deiconify()
            elif state == 'iconic':
                win.iconify()

    def save(self):
        try:
            self.library.save([pin.state() for pin in self.pins])
        except OSError as exc:
            self.hint.set('保存失败：' + str(exc))

    def autosave(self):
        if self.capture is None and not getattr(self, 'capturing', False):
            self.save()
        self.save_timer = self.root.after(3000, self.autosave)

    def quit(self):
        self.root.after_cancel(self.save_timer)
        self.save()
        self.bridge.close()
        self.root.destroy()

def main():
    dpi_aware()
    base = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
    data = base / 'data'
    if '--data' in sys.argv:
        data = Path(sys.argv[sys.argv.index('--data') + 1])
    root = tk.Tk()
    app = App(root, data)
    for path in sys.argv[1:] if '--data' not in sys.argv else []:
        app.import_paths([path])
    root.mainloop()

if __name__ == '__main__':
    main()
