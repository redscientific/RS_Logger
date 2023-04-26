from tkinter.ttk import Checkbutton, LabelFrame, Label, Button,  Separator, Entry
from tkinter import IntVar, OptionMenu, Toplevel, StringVar

from queue import SimpleQueue
from math import ceil
from os import path


class VOGConfigWin:
    def __init__(self, q_out):
        self._q_out = q_out
        self._UISettings = {"darkOpacity": StringVar(), "clearOpacity": StringVar(), "closeDuration": StringVar(),
                            "openDuration": StringVar(), "debounce": StringVar(),
                            "startOpen": StringVar(), "printCycle": StringVar(),
                            "expType": StringVar()}
        self._infSettings = {"openInf": IntVar(), "closeInf": IntVar()}

        self.button_control = ("Trial", "Lens", "Peek")
        self.click_mode = ("Hold", "Click")

        self._active_tab = None

        self._config_callback = None

    def show(self, uid):
        self._active_tab = uid

        win = Toplevel()
        win.withdraw()
        win.grab_set()
        win.title("")

        path_to_icon = path.abspath(path.join(path.dirname(__file__), '../../img/rs_icon.ico'))
        win.iconbitmap(path_to_icon)

        win.focus_force()
        win.resizable(False, False)

        lf = LabelFrame(win, text="Configuration")
        lf.grid(row=0, column=2, sticky="NEWS", pady=2, padx=2)
        lf.grid_columnconfigure(0, weight=1)
        lf.grid_rowconfigure(9, weight=1)

        # Current Configuration
        Label(lf, text="Name:").grid(row=0, column=0, sticky="NEWS")
        Entry(lf, textvariable=self._UISettings["expType"], width=17).grid(row=0, column=1, sticky="E", columnspan=2)

        # Separator
        Separator(lf).grid(row=1, column=0, columnspan=3, sticky="NEWS", pady=5)

        # Open Duration
        Label(lf, text="Open Duration (ms):").grid(row=2, column=0, sticky="NEWS")
        Entry(lf, textvariable=self._UISettings["openDuration"], width=7).grid(row=2, column=1, sticky="W")

        cb_open_inf = Checkbutton(lf, text="INF", command=self._open_inf_clicked,
                                  variable=self._infSettings['openInf'], onvalue=1, offvalue=0)
        cb_open_inf.grid(row=2, column=2)

        # Close Duration
        Label(lf, text="Closed Duration (ms):").grid(row=3, column=0, sticky="NEWS")
        Entry(lf, textvariable=self._UISettings["closeDuration"], width=7).grid(row=3, column=1, sticky="W")

        cb_close_inf = Checkbutton(lf, text="INF", command=self._close_inf_clicked,
                                   variable=self._infSettings['closeInf'], onvalue=1, offvalue=0)
        cb_close_inf.grid(row=3, column=2)

        # Debounce
        Label(lf, text="Debounce Time (ms):").grid(row=4, column=0, sticky="NEWS")
        Entry(lf, textvariable=self._UISettings["debounce"], width=7).grid(row=4, column=1, sticky="W")

        # Separator
        Separator(lf).grid(row=5, column=0, columnspan=3, sticky="NEWS", pady=5)

        # Button Mode
        open_state = Checkbutton(lf, text="Start Clear",
                                  variable=self._UISettings['startOpen'], onvalue=1, offvalue=0)
        open_state.grid(row=6, column=0, sticky="EW", columnspan=2)

        # Control Mode
        control_mode = Checkbutton(lf, text="Verbose Output:",
                                  variable=self._UISettings['printCycle'], onvalue=1, offvalue=0)
        control_mode.grid(row=6, column=1, sticky="EW", columnspan=2)

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

        self.button_glance = Button(f, text="Peek", command=self._set_peek_cb, state='enabled')
        self.button_glance.grid(row=0, column=1, sticky="NEWS")

        button_e_blindfold = Button(f, text="eBlindfold", command=self._set_eblindfold_cb)
        button_e_blindfold.grid(row=0, column=2, sticky="NEWS")

        button_direct = Button(f, text="Direct", command=self._set_direct_cb)
        button_direct.grid(row=0, column=3, sticky="NEWS")

        win.deiconify()

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
        if self._infSettings['openInf'].get() == 1:
            self._UISettings["openDuration"].set('2147483647')
            self._UISettings["closeDuration"].set('0')
            self._infSettings['closeInf'].set(0)

    def _close_inf_clicked(self):
        if self._infSettings['closeInf'].get() == 1:
            self._UISettings["closeDuration"].set('2147483647')
            self._UISettings["openDuration"].set('0')
            self._infSettings['openInf'].set(0)

    def _set_custom(self):
        self._push_settings_to_device()

    def _set_nhtsa_cb(self):
        self._UISettings['expType'].set('cycle')
        self._UISettings['openDuration'].set('1500')
        self._UISettings['closeDuration'].set('1500')
        self._UISettings['startOpen'].set('1')
        self._push_settings_to_device()

    def _set_peek_cb(self):
        self._UISettings['expType'].set('peek')
        self._UISettings['startOpen'].set('0')
        self._push_settings_to_device()

    def _set_eblindfold_cb(self):
        self._UISettings['expType'].set('eBlindfold')
        self._UISettings['openDuration'].set('2147483647')
        self._UISettings['closeDuration'].set('0')
        self._UISettings['startOpen'].set('1')
        self._push_settings_to_device()

    def _set_direct_cb(self):
        self._UISettings['expType'].set('direct')
        self._push_settings_to_device()

    def _push_settings_to_device(self):
        def recode_config(key):
            return {
                'darkOpacity': 'drk',
                'clearOpacity': 'clr',
                'closeDuration': 'cls',
                'openDuration': 'opn',
                'debounce': 'dbc',
                'startOpen': 'srt',
                'printCycle': 'dta',
                'expType': 'typ'
            }[key]

        vals = ''
        for setting in self._UISettings:
            vals += f'{recode_config(setting)}:{self._UISettings[setting].get()},'
        self._q_out.put(f'wVOG,{self._active_tab}>set_cfg>{vals}')
        self._clear_fields()

    def _clear_fields(self):
        for val in self._UISettings:
            self._UISettings[val].set("")
        for val in self._infSettings:
            self._infSettings[val].set(0)

    def parse_config(self, vals):
        def recode_config(key):
            return {
                'drk': 'darkOpacity',
                'clr': 'clearOpacity',
                'cls': 'closeDuration',
                'opn': 'openDuration',
                'dbc': 'debounce',
                'srt': 'startOpen',
                'dta': 'printCycle',
                'typ': 'expType',
            }[key]

        vals = vals.split(',')
        for kv in vals:
            # try:
            kv = kv.split(":")
            if len(kv) == 2:
                new_key = recode_config(kv[0].strip(' '))
                fnc = self._UISettings.get(new_key, None)
                if fnc:
                    fnc.set(kv[1])
                    if new_key == 'openDuration':
                        self._infSettings['openInf'].set(1) if kv[1] == '2147483647' \
                            else self._infSettings['openInf'].set(0)
                    elif new_key == 'closeDuration':
                        self._infSettings['closeInf'].set(1) if kv[1] == '2147483647' \
                            else self._infSettings['closeInf'].set(0)

            # except:
                # print(f"WVOG config KV error: {kv}")
