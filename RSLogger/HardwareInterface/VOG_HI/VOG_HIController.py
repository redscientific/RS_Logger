from RSLogger.HardwareInterface._utilities import USBConnect
from threading import Thread
from queue import SimpleQueue
from asyncio import create_task, sleep
from time import time
from serial import SerialException


class VOGController:
    def __init__(self, q_out, q_in):
        self._q_out: SimpleQueue = q_out
        self._q_in: SimpleQueue = q_in

        self._connection_manager = USBConnect.ConnectionManager(name='vog', vid='16C0', pid='0483')

        self._connected_vog_devices = None
        self._connected_vog_ports = None

        # uart port
        self.msg_time_stamp = None
        self.msg_port = None
        self._run = True

        self._file_path = None

        # results
        self._clicks = '0'
        self._cond_name = ''

    def run(self):
        create_task(self._handle_messages_from_vog_devices())
        create_task(self._connection_manager.update())
        create_task(self._connect_event())

        create_task(self._queue_monitor())

    async def _connect_event(self):
        while 1:
            self._connected_vog_devices = await self._connection_manager.new_connection()
            self._connected_vog_ports = ','.join(list(self._connected_vog_devices.keys()))
            msg = f'ui_vog>devices>{self._connected_vog_ports}'
            self._q_out.put(msg)

            if self._connected_vog_devices:
                self._listen_to_connected_vog = True
            else:
                self._listen_to_connected_vog = False

    async def _handle_messages_from_vog_devices(self):
        while 1:
            if self._connected_vog_devices:
                for port in self._connected_vog_devices:
                    try:
                        if self._connected_vog_devices[port].inWaiting():
                            timestamp = time()
                            msg = self._connected_vog_devices[port].read_until(b'\r\n')
                            print(msg)
                            msg = str(msg, 'utf-8').strip()
                            if msg in ['peekOpen', 'peekClose']:
                                pass
                            elif any([i in msg for i in ['config', 'button', 'device', 'stm', 'data']]):
                                key, val = msg.split('|')
                                self._q_out.put(f'ui_vog>{key}>{val}')
                                if key == 'data':
                                    self._log_results(port, timestamp, val)
                    except SerialException:
                        pass

            await sleep(0.0001)

    async def _queue_monitor(self):
        while 1:
            if self._connected_vog_devices:
                while not self._q_in.empty():
                    msg = self._q_in.get()
                    address, key, val = msg.split(">")

                    if val == 'ALL':
                        if 'cond' in key:
                            self._cond_name = key.split(':')[1]
                        else:
                            for val in self._connected_vog_devices:
                                create_task(self._message_device(self._connected_vog_devices[val], key))
                    elif key == 'fpath':
                        self._file_path = val
                    elif 'COM' in key:
                        key, val = val, key
                        create_task(self._message_device(self._connected_vog_devices[val], key))
                    else:
                        create_task(self._message_device(self._connected_vog_devices[val], key))
            await sleep(0.0001)

    def _log_results(self, port, timestamp, data):
        d = data.split(',')
        data = ', '.join(d)
        packet = f'vog_{port}, {self._cond_name}, {timestamp}, {data}'

        def _write(_path, _results):
            try:
                with open(_path, 'a') as writer:
                    writer.write(_results + '\n')
            except (PermissionError, FileNotFoundError):
                print("Control write error")

        file_path = f"{self._file_path}/vog.txt"
        t = Thread(target=_write, args=(file_path, packet))
        t.start()

    @staticmethod
    async def _message_device(serial_conn, cmd):
        if cmd == 'init':
            serial_conn.write(str.encode('>do_expStart|<<\n'))
        elif cmd == 'close':
            serial_conn.write(str.encode('>do_expStop|<<\n'))
        elif cmd == 'start':
            serial_conn.write(str.encode('>do_trialStart|<<\n'))
        elif cmd == 'stop':
            serial_conn.write(str.encode('>do_trialStop|<<\n'))
        elif cmd in ['do_peekOpen', 'do_peekClose']:
            serial_conn.write(str.encode(f'>{cmd}|<<\n'))
        elif cmd == 'nhtsa':
            for msg in ['set_lowerISI 3000', 'set_upperISI 5000', 'set_stimDur 1000', 'set_intensity 255']:
                serial_conn.write(str.encode(f'{msg}\n'))
                await sleep(0.0001)
        elif cmd == 'get_config':
            for msg in ['get_deviceVer', 'get_configName', 'get_configMaxOpen', 'get_configMaxClose',
                        'get_configDebounce', 'get_configClickMode', 'get_configButtonControl']:
                serial_conn.write(str.encode(f'>{msg}|<<\n'))
        elif 'cfg' in cmd:
            cmds = ['set_configName', 'set_configMaxOpen', 'set_configMaxClose',
                    'set_configDebounce', 'set_configClickMode', 'set_configButtonControl']
            cmd_split = cmd.split(',')[1:]
            for i, msg in enumerate(cmd_split):
                packet = str.encode(f'>{cmds[i]}|{msg}<<\n')
                serial_conn.write(packet)
        else:
            print(f'VOG_HIController {cmd} not handled')
        await sleep(0.0001)

    @staticmethod
    async def _send(serial_conn, msg):
        serial_conn.write(str.encode(f'{msg}\n'))

    def _exit_async_loop(self):
        self._run = False
