from queue import SimpleQueue
from tkinter import Tk, TclError
from RSLogger.user_interface.wVOG_UI import WVOG_UIView, WVOG_UIConfig
from numpy import nan


class WVOGUIController:
    def __init__(self, win, q_out):
        self._win: Tk = win
        self._q_2_hi: SimpleQueue = q_out

        self.devices = dict()

        # Experiment
        self._running = False

        # wVOG_UI
        self._view = WVOG_UIView.wVOGTabbedControls(win)
        self._view.NB.bind("<<NotebookTabChanged>>", self._tab_changed_cb)

        self._view.register_stimulus_a_toggle_cb(self._stimulus_a_toggle_cb)
        self._view.register_stimulus_b_toggle_cb(self._stimulus_b_toggle_cb)
        self._view.register_stimulus_ab_toggle_cb(self._stimulus_ab_toggle_cb)

        self._view.register_configure_clicked_cb(self._configure_button_cb)
        self._active_tab = None

        self._view.register_rescan_network(self._rescan_network_cb)

        # Configure Window
        self._cnf_win = WVOG_UIConfig.VOGConfigWin(self._q_2_hi)

    def handle_command(self, com, key, val):
        # Tab Events
        if key == 'devices':
            self._update_devices(val)
        elif key == 'remove' : self._remove_tab(val)

        # Plot Commands
        elif key == 'clear'  : self._clear_plot()

        # Messages from wVOG unit
        elif key == 'cfg'    : self._update_configuration(val)

        elif key in ['a', 'b', 'x']:
            self._update_stim_state(val, com)

        elif key == 'dta'    : self._update_tsot_tsct_data(val, com)
        elif key == 'bty'    : self._update_battery_soc(val, com)

        elif key == 'fpath'  : self._update_file_path(val)

    def handle_control_command(self, key, val):
        if   key == 'init'    : self._log_init(val)
        elif key == 'close'   : self._log_close(val)
        elif key == 'start'   : self._data_record(val)
        elif key == 'stop'    : self._data_pause(val)

    def _update_devices(self, devices=None):
        units = list()
        if devices:
            units = devices.split(",")
            self._view.show()
        else:
            self._view.hide()

        to_add = set(units) - set(self.devices)
        if to_add:
            for id_ in to_add:
                if id_ not in self.devices:
                    self.devices[id_] = self._view.build_tab(id_)

        to_remove = set(self.devices) - set(units)
        if to_remove:
            for id_ in to_remove:
                if id_ in self.devices.keys():
                    self.devices.pop(id_)
                    self._view.NB.forget(self._view.NB.children[id_.lower()])

    def _add_tab(self, dev_ids):
        for id_ in dev_ids:
            if id_ not in self.devices:
                self.devices[id_] = self._view.build_tab(id_)

    def _remove_tab(self, dev_ids):
        for id_ in dev_ids:
            if id_ in self.devices.keys():
                self.devices.pop(id_)
                self._view.NB.forget(self._view.NB.children[id_.lower()])

    # wVOG_UI Parent
    def _log_init(self, arg):
        self._toggle_state('disabled')
        self._running = True
        for d in self.devices:
            self.devices[self._view.NB.tab(self._view.NB.select(), "text")]['plot'].clear_all()
            self.devices[d]['plot'].run = True
            self.devices[d]['plot'].clear_all()
            self.devices[d]['plot'].run = True
            self._reset_results_text()

    def _log_close(self, arg):
        self._running = False
        self._toggle_state('normal')
        for d in self.devices:
            self.devices[d]['plot'].run = False

    def _data_record(self, arg):
        for d in self.devices:
            self.devices[d]['plot'].recording = True

    def _data_pause(self, arg):
        for d in self.devices:
            self.devices[d]['plot'].state_update(d, nan)
            self.devices[d]['plot'].recording = False

    def _toggle_state(self, state):
        for d in self.devices:

            self.devices[d]['a_toggle'].configure(state=state)
            self.devices[d]['b_toggle'].configure(state=state)
            self.devices[d]['ab_toggle'].configure(state=state)
            self.devices[d]['configure'].configure(state=state)
            try:
                self.devices[d]['refresh'].config(state=state)
            except KeyError:
                pass

    def _update_file_path(self, arg):
        pass

    # Registered Callbacks with wVOG UI
    def _tab_changed_cb(self, e):
        if self.devices:
            try:
                # Clean up old tab and device
                if self._running:
                    self.devices[self._active_tab]['plot'].run = False
                    self.devices[self._active_tab]['plot'].clear_all()

                # Start new tab and device
                self._active_tab = self._view.NB.tab(self._view.NB.select(), "text")
                if not 'COM' in self._active_tab:
                    self._q_2_hi.put(f"wVOG,{self._active_tab}>get_bat>")
                if self._running:
                    self.devices[self._active_tab]['plot'].run = True
                    self.devices[self._active_tab]['plot'].clear_all()
            except Exception as e:
                pass
                # print(f"vController _tab_changed_cb: {e}")

    def _lens_change_cb(self, lens, state):
        self._q_2_hi.put(f"wVOG,{self._active_tab}>{lens}_{state}>")

    def _configure_button_cb(self):
        self._cnf_win.show(self._active_tab)
        self._q_2_hi.put(f"wVOG,{self._active_tab}>get_cfg>")

    def _rescan_network_cb(self):
        for c in self._view.NB.winfo_children():
            try:
                self._view.NB.forget(c)
            except TclError:
                pass
        self.devices.clear()
        self._q_2_hi.put(f"wVOG,{self._active_tab}>net_scn>")
        self._view.hide()

    # Messages from vog hardware
    def _update_tsot_plot(self, arg):
        port = self._view.NB.tab(self._view.NB.select(), "text")
        if self._running:
            trial, opened, closed = arg.split(',')
            opened = int(opened)
            closed = int(closed)

            self.devices[port]['trl_n'].set(trial)
            self.devices[port]['tsot'].set(opened)
            self.devices[port]['tsct'].set(closed)

            self.devices[port]['plot'].tsot_update(port, opened)

            self.devices[port]['plot'].tsct_update(port, closed)

    def _reset_results_text(self):
        for d in self.devices:
            self._update_trial_text(d, '0')
            self._update_tsot_text(d, '0')
            self._update_tsct_text(d, '0')

    def _update_trial_text(self, unit_id, cnt):
        if self._running:
            self.devices[unit_id]['trl_n'].set(cnt)

    def _update_tsot_text(self, unit_id, tsot):
        if self._running:
            self.devices[unit_id]['tsot'].set(tsot)

    def _update_tsct_text(self, unit_id, tsct):
        if self._running:
            self.devices[unit_id]['tsct'].set(tsct)

        # Plot Commands

    def _clear_plot(self):
        for d in self.devices:
            self.devices[d]['plot'].clear_all()

    def _stop_plotter(self):
        for d in self.devices:
            self.devices[d]['plot'].run = False

    def _stimulus_a_toggle_cb(self):
        com = self._view.NB.tab(self._view.NB.select(), 'text')
        if self.devices[com]['a_toggle']['text'] == 'A Open':
            self.devices[com]['a_toggle']['text'] = 'A Close'
            self._q_2_hi.put(f"wVOG,{com}>a_on>")
        else:
            self.devices[com]['a_toggle']['text'] = 'A Open'
            self._q_2_hi.put(f"wVOG,{com}>a_off>")

    def _stimulus_b_toggle_cb(self):
        com = self._view.NB.tab(self._view.NB.select(), 'text')
        if self.devices[com]['b_toggle']['text'] == 'B Open':
            self.devices[com]['b_toggle']['text'] = 'B Close'
            self._q_2_hi.put(f"wVOG,{com}>b_on>")
        else:
            self.devices[com]['b_toggle']['text'] = 'B Open'
            self._q_2_hi.put(f"wVOG,{com}>b_off>")

    def _stimulus_ab_toggle_cb(self):
        com = self._view.NB.tab(self._view.NB.select(), 'text')
        if self.devices[com]['ab_toggle']['text'] == 'AB Open':
            self.devices[com]['ab_toggle']['text'] = 'AB Close'
            self._q_2_hi.put(f"wVOG,{com}>ab_on>")
        else:
            self.devices[com]['ab_toggle']['text'] = 'AB Open'
            self._q_2_hi.put(f"wVOG,{com}>ab_off>")

    # Plotter
    def _update_stim_state(self, arg, unit_id):
        if self._running:
            self.devices[unit_id]['plot'].state_update(unit_id, arg)

    def _update_tsot_tsct_data(self, arg, unit_id):
        if self._running:
            c_utc, trial_n, j3, ttt, tsct, tsot, bat, utc = arg.strip().split(',')
            if unit_id == self._active_tab:
                self._update_battery_soc(bat, unit_id)
                self.devices[unit_id]['trl_n'].set(trial_n)
                self.devices[unit_id]['tsot'].set(tsot)
                self.devices[unit_id]['tsct'].set(tsct)
            self.devices[unit_id]['plot'].tsot_update(unit_id, tsot)
            self.devices[unit_id]['plot'].tsct_update(unit_id, tsct)

    def _update_battery_soc(self, arg, unit_id=None):
        if 'COM' not in unit_id:
            soc = arg
            if isinstance(arg, list):
                unit_id, soc = arg[0].strip().split(',')

            p = int(soc) // 10
            for i in range(10):
                color = 'white'
                if p >= i + 1:
                    color = 'black' if p > 2 else 'red'
                self.devices[unit_id][f'b_{i}'].config(bg=color)

    # Configuration Window
    # ---- Registered Callbacks
    def _custom_button_cb(self, msg):
        self._q_2_hi.put(f"wVOG,{self._active_tab}>set_cfg>{msg}")

    def _nhtsa_button_cb(self):
        self._q_2_hi.put(f"wVOG,{self._active_tab}>set_nhtsa>")

    # ---- msg from wVOG unit
    def _update_configuration(self, args):
        self._cnf_win.parse_config(args)