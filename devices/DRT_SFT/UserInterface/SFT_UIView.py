from tkinter.ttk import Label, LabelFrame, Button, Checkbutton
from tkinter.ttk import Frame, Notebook
from tkinter import Tk, StringVar, BOTH
from tkinter import Label as tkLabel
from queue import SimpleQueue
from devices.DRT_SFT.UserInterface import SFT_UIPlotter


class SFTTabbedControls:
    def __init__(self, win: Tk):
        self._win = win

        self._frame = Frame(win)

        self._tabs = dict()

        # Notebook - Tabs
        self.NB = Notebook(self._frame)
        self.NB.grid(row=0, column=0, sticky='NEWS')

        self._tab_f = dict()

        # Callbacks
        self._rt_checkbox_cb = None
        self._state_checkbox_cb = None
        self._vib_cb = None
        self._led_cb = None
        self._aud_cb = None
        self._configure_clicked_cb = None
        self._rescan_network_cb = None

    def build_tab(self, dev_id) -> dict:
        self._tab_f.clear()

        # Build tab
        self._tab_add_main_frame(dev_id)
        self._tab_embed_main_frame_in_nb(dev_id)
        self._tab_add_plot(dev_id)
        self._tab_add_manual_controls()
        self._tab_add_results()
        self._tab_add_configure()

        return self._tab_f.copy()

    def _tab_add_main_frame(self, dev_id):
        self._tab_f['frame'] = Frame(self.NB, name=dev_id.lower())
        self._tab_f['frame'].grid(row=0, column=1)
        self._tab_f['frame'].grid_columnconfigure(0, weight=1)
        self._tab_f['frame'].grid_rowconfigure(3, weight=1)

    def _tab_embed_main_frame_in_nb(self, name):
        self.NB.add(self._tab_f['frame'], text=name)

    def _tab_add_plot(self, dev_id):
        self._tab_f['plot'] = SFT_UIPlotter.Plotter(self._tab_f['frame'])
        self._tab_f['plot'].set_rt_and_state_lines(dev_id)

    def _tab_add_manual_controls(self):
        lf = LabelFrame(self._tab_f['frame'], text="Toggle Stimuli")
        lf.grid(row=1, column=1, sticky='NEWS')
        lf.grid_columnconfigure(0, weight=1)

        # Vibration Motor Controls
        self._tab_f['on_vib'] = Button(lf, text="VIB", command=self._vib_cb)
        self._tab_f['on_vib'].grid(row=0, column=0, sticky='NEWS')

        # LED controls
        self._tab_f['on_led'] = Button(lf, text="LED", command=self._led_cb)
        self._tab_f['on_led'].grid(row=1, column=0, sticky='NEWS')

        # Auditory controls
        self._tab_f['on_aud'] = Button(lf, text="AUD", command=self._aud_cb)
        self._tab_f['on_aud'].grid(row=2, column=0, sticky='NEWS')


    def _tab_add_results(self):
        lf = LabelFrame(self._tab_f['frame'], text="Results")
        lf.grid(row=4, column=1, sticky='NEWS')
        lf.grid_columnconfigure(1, weight=1)

        self._tab_f['trl_n'] = StringVar()
        self._tab_f['trl_n'].set("NA")
        Label(lf, text="Trial Number:").grid(row=0, column=0, sticky='NEWS')
        Label(lf, textvariable=self._tab_f['trl_n']).grid(row=0, column=1, sticky="E")

        self._tab_f['rt'] = StringVar()
        self._tab_f['rt'].set("NA")
        Label(lf, text="Reaction Time:").grid(row=1, column=0, sticky='NEWS')
        Label(lf, textvariable=self._tab_f['rt']).grid(row=1, column=1, sticky="E")

        self._tab_f['clicks'] = StringVar()
        self._tab_f['clicks'].set("NA")
        Label(lf, text="Response Count:").grid(row=2, column=0, sticky='NEWS')
        Label(lf, textvariable=self._tab_f['clicks']).grid(row=2, column=1, sticky="E")

    def _tab_add_configure(self):
        f = Frame(self._tab_f['frame'])
        f.grid(row=5, column=1, sticky="NEWS")
        f.grid_columnconfigure(0, weight=1)

        self._tab_f['configure'] = Button(f, text="Configure Unit", command=self._configure_clicked_cb)
        self._tab_f['configure'].grid(row=0, column=0, sticky='NEWS')

    # Events and Callbacks
    def register_rt_checkbox_cb(self, cb):
        self._rt_checkbox_cb = cb

    def register_state_checkbox_cb(self, cb):
        self._state_checkbox_cb = cb

    def register_vib_cb(self, cb):
        self._vib_cb = cb

    def register_led_cb(self, cb):
        self._led_cb = cb

    def register_aud_cb(self, cb):
        self._aud_cb = cb

    def register_configure_clicked_cb(self, cb):
        self._configure_clicked_cb = cb

    def register_rescan_network(self, cb):
        self._rescan_network_cb = cb

    def show(self):
        self._frame.pack(fill=BOTH, expand=1)
        self._frame.columnconfigure(0, weight=1)
        self._frame.rowconfigure(0, weight=1)

    def hide(self):
        self._frame.pack_forget()








