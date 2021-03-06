import urllib.request
from urllib.error import URLError
import webbrowser
from tkinter import Tk, BOTH, messagebox
from tkinter.ttk import Frame
from os import path

from main import __version__

# User Interface
from RSLogger.UserInterface.SFT_UI import SFT_UIController
from RSLogger.UserInterface.DRT_UI import DRT_UIController
from RSLogger.UserInterface.VOG_UI import VOG_UIController
from RSLogger.UserInterface.wDRT_UI import WDRT_UIController

# Widgets
from RSLogger.UserInterface.Logger.controls import ExpControls
from RSLogger.UserInterface.Logger.key_logger import KeyFlagger
from RSLogger.UserInterface.Logger.note_logger import NoteTaker
from RSLogger.UserInterface.Logger.log_timers import InfoDisplay
from RSLogger.UserInterface.Logger.usb_cameras.cam_ui import CameraWidget


class LoggerUI:
    def __init__(self, queues):
        self._q_in = queues['ui_logger']
        # DRT_UI Thread - This is the main thread where a tkinter loop is used
        self.win: Tk = Tk()
        self.win.withdraw()  # hide the window

        self.win.resizable(True, True)
        self.win.minsize(816, 105)
        self.win.title(f"RS Logger {__version__}")
        path_to_icon = path.abspath(path.join(path.dirname(__file__), '../img/rs_icon.ico'))
        self.win.iconbitmap(path_to_icon)

        # Widgets
        self.widget_frame = Frame(self.win)
        self.widget_frame.pack(fill=BOTH)
        self.widget_frame.columnconfigure(4, weight=1)

        self._widgets = {'control': ExpControls(self.widget_frame, queues['main']),
                         'key_flag': KeyFlagger(self.win, self.widget_frame),
                         'note': NoteTaker(self.widget_frame, queues['main']),
                         'info': InfoDisplay(self.widget_frame, queues['main']),
                         'cam': CameraWidget(self.win, self.widget_frame, queues['main']),
                         }

        # Devices
        self._devices = {'sft': SFT_UIController.SFTUIController(self.win, queues['main'], queues['ui_sft']),
                         'drt': DRT_UIController.DRTUIController(self.win, queues['main'], queues['ui_drt']),
                         'wdrt': WDRT_UIController.WDRTUIController(self.win, queues['main'], queues['ui_wdrt']),
                         'vog': VOG_UIController.VOGUIController(self.win, queues['main'], queues['ui_vog'])
                         }

        self._queue_monitor()

        self.check_version()

        # Tkinter loop
        self.win.after(0, self.win.deiconify)
        self.win.mainloop()

    def _queue_monitor(self):
        while not self._q_in.empty():
            msg = self._q_in.get()
            address, key, val = msg.split('>')

            for w in self._widgets:
                try:
                    if key == 'fpath':
                        self._widgets[w].set_file_path(val)
                    elif key == 'init':
                        self._widgets[w].handle_log_init(val)
                    elif key == 'close':
                        self._widgets[w].handle_log_close(val)
                    elif key == 'start':
                        self._widgets[w].handle_data_record(val)
                    elif key == 'stop':
                        self._widgets[w].handle_data_pause(val)
                except AttributeError:
                    pass

        self.win.after(10, self._queue_monitor)

    def check_version(self):
        try:
            version = urllib.request.urlopen("https://raw.githubusercontent.com/redscientific/RS_Logger/master/version.txt")
            version = str(version.read().decode('utf-8'))
            version = version.strip()
            if version != __version__:
                ans = messagebox.askquestion(
                    title="Notification",
                    message=f"You are running RSLogger version {__version__}\n\n"
                            f"The most recent version is {version}\n\n"
                            f"would you like to download the most recent version now?")
                if ans == 'yes':
                    url = f"https://github.com/redscientific/RS_Logger/raw/master/dist/Output/RSLogger_v{version}.exe"
                    webbrowser.open_new(url)
        except URLError:
            messagebox.showwarning(title="No Internet Connection!",
                                   message="Your software may be out of date.\n\n"
                                           "Please go to redscientific.com to check for updates.")




