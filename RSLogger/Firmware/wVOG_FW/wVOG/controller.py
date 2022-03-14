import uasyncio as asyncio
from wVOG import xb, config, lenses, battery, mmc, experiments, timers


class WirelessVOG:
    def __init__(self, serial):
        self.serial = serial

        # Lenses
        self.lenses = lenses.Lenses()

        # Battery
        self.battery = battery.LipoReader()

        # MMC Save - The flash module stuck to the bottom of the unit
        self.headers = "Device_Unit,,, Block_ms, Trial, Reaction Time, Responses, UTC, Battery\n"
        self.mmc = mmc.MMC()

        # XB
        self.xb = xb.XB()
        self.xb.register_incoming_message_cb(self.handle_xb_msg)

        # Config
        self.cfg = config.Configurator('wVOG/config.jsn')

        # Experiments
        self.exp_peek = experiments.Peek(self.cfg.config, self.broadcast)

    def update(self):
        await asyncio.gather(
            self.handle_serial_msg(),
        )

    ################################################
    # Listen for incoming messages
    async def handle_serial_msg(self):
        while True:
            if self.serial.any():
                cmd = self.serial.read()
                cmd = cmd.strip().decode('utf-8')
                self.parse_cmd(cmd)
            await asyncio.sleep(.01)

    def handle_xb_msg(self, cmd):
        self.parse_cmd(cmd)

    def parse_cmd(self, cmd):
        try:
            action, key, val = cmd.split(">")

            if action == 'do':
                self.handle_do(key, val)
            elif action == 'get':
                self.handle_get(key, val)
            elif action == 'set':
                self.handle_set(key, val)

        except ValueError:
            print("ERROR: Malformed command")

    ################################################
    # Handle Incoming Commands

    #### DO Commands
    def handle_do(self, key, val):
        if key == 'lens':
            self.update_lens_states(key, val)
        elif key == 'start':
            self.start_experiment(val)
        elif key == 'stop':
            self.stop_experiment(val)

    def update_lens_states(self, key, val):
        # 'do>lens>[open, close]:[a, b]'  :Example - 'do>lens>close:' or 'do>lens>open:a'
        key, val = val.split(":")
        lenses = ['a', 'b']
        if val in lenses: lenses = val

        if key == 'open':
            self.lenses.clear(lenses)
        elif key == 'close':
            self.lenses.opaque(lenses)

    #### GET Commands
    def handle_get(self, key, val):
        if key == 'cfg':
            self.get_config(val)
        elif key == 'bat':
            self.get_battery()

    def get_config(self, val):
        # Example: 'get>cfg>' or 'get>cfg>open'
        if val in self.cfg.config.keys():
            self.broadcast(f'cfg>{val}:{self.cfg.config[val]}')
        else:
            self.broadcast(f'cfg>{self.cfg.get_config_str()}')

    def get_battery(self):
        self.broadcast(f'bty>{self.battery.percent()}')

    #### SET Commands - Sets configurations in the config.jsn file with the same names
    def handle_set(self, key, val):
        if key == 'cfg': self.set_config(val)

    def set_config(self, kv):
        # Example: 'set>cfg>open:1500'
        key, val = kv.split(":")
        # Example: 'set>open>1400' or 'set>debounce>45'
        self.cfg.update(f"{key}:{val}")
        self.broadcast(f'cfg>{key}:{self.cfg.config[key]}')

    ################################################
    # Experiments
    # Peek
    def start_experiment(self, val):
        if val == "peek":
            self.exp_peek.begin_trial()
        elif val == "cycle":
            self.exp_cycle.begin_trial()
        elif val == "direct":
            self.exp_direct.run()

    def stop_experiment(self, val):
        if val == "peek":
            self.exp_peek.end_trial()
        elif val == "cycle":
            self.exp_cycle.end_trial()

    ################################################
    #
    def broadcast(self, msg):
        self.serial.write(msg + '\n')
        asyncio.create_task(self.xb.transmit(msg + '\n'))
