from tkinter.ttk import Checkbutton, LabelFrame, Label, Button,  Separator, Entry
from tkinter import IntVar, OptionMenu, Toplevel, StringVar

from queue import SimpleQueue
from math import ceil
from os import path


class VOGConfigWin:
    def __init__(self, q_out: SimpleQueue):
        self._q_out = q_out
        self._UISettings = {"deviceVer": StringVar(), "configName": StringVar(), "configMaxOpen": StringVar(),
                            "configMaxClose": StringVar(), "configDebounce": StringVar(),
                            "configClickMode": StringVar(), "buttonControl": StringVar(),
                            "openInf": IntVar(), "closeInf": IntVar()}

        self.button_control = ("Trial", "Lens", "Peek")
        self.click_mode = ("Hold", "Click")

        self._active_tab = None



    def show(self, uid):
        self._active_tab = uid

        win = Toplevel()
        win.withdraw()
        win.grab_set()
        win.title("")

        path_to_icon = path.abspath(path.join(path.dirname(__file__), '../../../rs_icon.ico'))
        win.iconbitmap(path_to_icon)

        win.focus_force()
        win.resizable(False, False)

        lf = LabelFrame(win, text="Configuration")
        lf.grid(row=0, column=2, sticky="NEWS", pady=2, padx=2)
        lf.grid_columnconfigure(0, weight=1)
        lf.grid_rowconfigure(9, weight=1)

        # Current Configuration
        Label(lf, text="Name:").grid(row=0, column=0, sticky="NEWS")
        Entry(lf, textvariable=self._UISettings["configName"], width=17).grid(row=0, column=1, sticky="E", columnspan=2)

        # Separator
        Separator(lf).grid(row=1, column=0, columnspan=3, sticky="NEWS", pady=5)

        # Open Duration
        Label(lf, text="Open Duration (ms):").grid(row=2, column=0, sticky="NEWS")
        Entry(lf, textvariable=self._UISettings["configMaxOpen"], width=7).grid(row=2, column=1, sticky="W")

        cb_open_inf = Checkbutton(lf, text="INF", command=self._open_inf_clicked,
                                  variable=self._UISettings['openInf'], onvalue=1, offvalue=0)
        cb_open_inf.grid(row=2, column=2)

        # Close Duration
        Label(lf, text="Closed Duration (ms):").grid(row=3, column=0, sticky="NEWS")
        Entry(lf, textvariable=self._UISettings["configMaxClose"], width=7).grid(row=3, column=1, sticky="W")

        cb_close_inf = Checkbutton(lf, text="INF", command=self._close_inf_clicked,
                                   variable=self._UISettings['closeInf'], onvalue=1, offvalue=0)
        cb_close_inf.grid(row=3, column=2)

        # Debounce
        Label(lf, text="Debounce Time (ms):").grid(row=4, column=0, sticky="NEWS")
        Entry(lf, textvariable=self._UISettings["configDebounce"], width=7).grid(row=4, column=1, sticky="W")

        # Separator
        # Separator(lf).grid(row=5, column=0, columnspan=3, sticky="NEWS", pady=5)

        # Button Mode
        # Label(lf, text="Click Mode:").grid(row=6, column=0, sticky="NEWS")
        # button_mode = OptionMenu(lf, self._UISettings['configClickMode'], *self.click_mode)
        # button_mode.grid(row=6, column=2, sticky="EW", columnspan=2)

        # Control Mode
        # Label(lf, text="Button Control Mode:").grid(row=7, column=0, sticky="NEWS")
        # control_mode = OptionMenu(lf, self._UISettings['buttonControl'], *self.button_control)
        # control_mode.grid(row=7, column=2, sticky="EW", columnspan=2)

        # Separator
        Separator(lf).grid(row=8, column=0, columnspan=3, sticky="NEWS", pady=5)

        # Upload
        button_upload = Button(lf, text="Upload Settings", command=self._set_custom)
        button_upload.grid(row=9, column=0, columnspan=4, sticky="NEWS", padx=20, pady=5)

        # Presets
        f = LabelFrame(win, text="Preset Configurations:")
        f.grid(row=1, column=2, sticky="S")
        f.grid_rowconfigure(1, weight=1)

        button_nhtsa = Button(f, text="NHTSA", command=self._set_nhtsa_cb)
        button_nhtsa.grid(row=0, column=0, sticky="NEWS")

        self.button_glance = Button(f, text="Glance", command=self._set_glance_cb, state='disabled')
        self.button_glance.grid(row=0, column=1, sticky="NEWS")

        button_e_blindfold = Button(f, text="eBlindfold", command=self._set_eblindfold_cb)
        button_e_blindfold.grid(row=0, column=2, sticky="NEWS")

        button_direct = Button(f, text="Direct", command=self._set_direct_cb)
        button_direct.grid(row=0, column=3, sticky="NEWS")

        win.after(0, win.deiconify())

    @staticmethod
    def _filter_entry(val, default_value,  lower, upper):
        if val.isnumeric():
            val = int(val)
            if val < lower or val > upper:
                val = default_value
        else:
            return default_value
        return val

    ################################
    # Callbacks
    def _open_inf_clicked(self):
        if self._UISettings['openInf'].get() == 1:
            self._UISettings["configMaxOpen"].set('2147483647')
            self._UISettings["configMaxClose"].set('0')
            self._UISettings['closeInf'].set(0)

    def _close_inf_clicked(self):
        if self._UISettings['closeInf'].get() == 1:
            self._UISettings["configMaxClose"].set('2147483647')
            self._UISettings["configMaxOpen"].set('0')
            self._UISettings['openInf'].set(0)

    def _set_custom(self):
        clk_mode = {'Hold': '0', 'Click': '1'}[self._UISettings['configClickMode'].get()]
        btn_mode = {'Trial': '0', 'Lens': '1', 'Peek': '2'}[self._UISettings['buttonControl'].get()]

        vals = [self._UISettings['configName'].get(), self._UISettings['configMaxOpen'].get(), self._UISettings['configMaxClose'].get(),
                self._UISettings['configDebounce'].get(), clk_mode, btn_mode]
        self._push_config(f'cfg,{",".join(vals)}')

    def _set_nhtsa_cb(self):
        vals = ['NHTSA', '1500', '1500', '20', '1', '0']
        self._push_config(f'cfg,{",".join(vals)}')

    def _set_glance_cb(self):
        vals = ['Glance', '1500', '1500', '20', '1', '2']
        self._push_config(f'cfg,{",".join(vals)}')

    def _set_eblindfold_cb(self):
        vals = ['eBlindfold', '2147483647', '0', '100', '1', '0']
        self._push_config(f'cfg,{",".join(vals)}')

    def _set_direct_cb(self):
        vals = ['Direct', '2147483647', '0', '100', '0', '1']
        self._push_config(f'cfg,{",".join(vals)}')

    def _push_config(self, vals):
        self._q_out.put(f"hi_vog>{self._active_tab}>{vals}")

    def update_fields(self, key, val):
        if key == 'configClickMode':
            val = self.click_mode[int(val)]
        elif key == 'configButtonControl' or key == 'buttonControl':
            key = 'buttonControl'
            val = self.button_control[int(val)]
        elif key == 'configMaxOpen':
            if val == '2147483647':
                self._UISettings['openInf'].set(1)
            else:
                self._UISettings['openInf'].set(0)
        elif key == 'deviceVer':
            if float(val) >= 2.2:
                self.button_glance.config(state='normal')
        elif key == 'configMaxClose':
            if val == '2147483647':
                self._UISettings['closeInf'].set(1)
            else:
                self._UISettings['closeInf'].set(0)

        self._UISettings[key].set(val)
