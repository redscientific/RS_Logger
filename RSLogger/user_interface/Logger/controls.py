import os
from tkinter import StringVar, LEFT, filedialog, messagebox
from tkinter.ttk import Button, Label, Entry, LabelFrame
from PIL import Image, ImageTk
from queue import SimpleQueue
from time import time
from os import path
from threading import Thread


class ExpControls:
    def __init__(self, widget_frame, q_out: SimpleQueue, fpath_cb):

        self._q_out = q_out
        self._ctrl_cb = fpath_cb
        self._file_path = None

        # Main widget label frame
        self._widget_lf = LabelFrame(widget_frame, text='Controls')
        self._widget_lf.pack(side=LEFT)
        self._widget_lf.grid_columnconfigure(0, weight=1)
        self._widget_lf.grid_rowconfigure(0, weight=1)

        # Widget Variables
        self.var_cond_name = StringVar()
        self.var_cond_name.trace_add("write", self._block_cb)

        # Init Log Button
        self._log_running = False
        self._log_button = Button(self._widget_lf, text="\nInitialize\n", command=self._log_button_cb)
        self._log_button.grid(row=0, column=0, pady=0, padx=2, sticky='NEWS', columnspan=2)

        # Record / Pause button
        self._record_running = False
        record_path = path.abspath(path.join(path.dirname(__file__), '../../img/record.png'))
        pause_path = path.abspath(path.join(path.dirname(__file__), '../../img/pause.png'))

        self._record_img = ImageTk.PhotoImage(Image.open(record_path))
        self._pause_img = ImageTk.PhotoImage(Image.open(pause_path))

        self._record_button = Button(self._widget_lf, image=self._record_img, command=self._record_button_cb)
        # self._record_button = Button(self._widget_lf, text="Record", command=self._record_button_cb)

        self._record_button.grid(row=0, column=2, pady=0, padx=2, sticky='NEWS')
        self._record_button.config(state="disabled")

        # Trial Name Entry
        Label(self._widget_lf, text="Label:", anchor='w') \
            .grid(row=1, column=0, pady=4, padx=2, sticky='NEWS')

        self.entry = Entry(self._widget_lf, textvariable=self.var_cond_name, width=20)
        self.entry.grid(row=1, column=1, pady=4, padx=2, sticky='EW', columnspan=2)

    def set_file_path(self, path):
        pass

    def handle_log_init(self, timestamp):
        self._log_running = True
        self._record_button['state'] = "normal"
        self._log_button['text'] = "\nClose\n"
        self._log_controls('initialize', timestamp)

    def handle_log_close(self, timestamp):
        if self._record_running:
            self.handle_data_pause(timestamp)

        self._log_running = False
        self._record_button['state'] = 'disabled'
        self._log_button['text'] = "\nInitialize\n"
        self._log_controls('close', timestamp)

    def handle_data_record(self, timestamp):
        if not self._log_running:
            self._log_button_cb()

        if self._file_path:
            self._record_running = True
            self._log_button['state'] = 'disabled'
            self.entry['state'] = 'disabled'
            self._record_button.config(image=self._pause_img)
            self._log_controls('record', timestamp)

    def handle_data_pause(self, timestamp):
        self._record_running = False
        self.entry['state'] = 'normal'
        self._log_button['state'] = 'normal'
        self._record_button.config(image=self._record_img)
        self._log_controls('pause', timestamp)

    # File Paths
    def _ask_file_dialog(self):
        title_ = "Folder NOT empty Warning!!!"
        message_ = "The selected folder is NOT empty." \
                   " Any Log files will be APPENDED and any video OVERWRITTEN.\n\n Do you wish to continue?"
        file_path = filedialog.askdirectory()
        if file_path:
            ans = ''
            file_count = len(os.listdir(path=file_path))
            if file_count != 0:
                ans = messagebox.askquestion(
                    title=title_,
                    message=message_)
            if ans == 'yes' or file_count == 0:
                self._file_path = file_path
                self._q_out.put(f'all>all>fpath>{file_path}')
                self._ctrl_cb('fpath', file_path)
            else:
                self._file_path = None
        else:
            self._file_path = None

    # Button Callbacks
    def _log_button_cb(self):
        timestamp = time()
        if not self._log_running:
            self._ask_file_dialog()
            if self._file_path:
                self._ctrl_cb('init', timestamp)
                self._q_out.put(f'all>all>init>')
        else:
            self._ctrl_cb('close', timestamp)
            self._q_out.put(f'all>all>close>')

    def _record_button_cb(self):
        timestamp = time()
        if not self._record_running:
            self._ctrl_cb('start', timestamp)
            self._q_out.put(f'all>all>start>')
        else:
            self._ctrl_cb('stop', timestamp)
            self._q_out.put(f'all>all>stop>')

    def _block_cb(self, a, b, c):
        self._q_out.put(f'all>all>cond>{self.var_cond_name.get()}')

    def _log_controls(self, state, timestamp):
        def _write(_path, _results):
            try:
                with open(_path, 'a') as writer:
                    writer.write(_results + '\n')
            except (PermissionError, FileNotFoundError):
                pass
        if timestamp != 'ALL':
            data = f"control,{state},{timestamp}"
            file_path = f"{self._file_path}/controls.txt"

            t = Thread(target=_write, args=(file_path, data))
            t.start()
