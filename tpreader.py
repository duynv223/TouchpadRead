from enum import Enum
# import threading
from PyQt5.QtCore import *
import time
import serial


class TpReadMode(Enum):
    TP_READ_MODE_SEQUENCE = 0,
    TP_READ_MODE_PIPELINE = 1


class TpReader(QObject):
    new_report = pyqtSignal(int, object)
    error = pyqtSignal(str)
    warning = pyqtSignal(str)

    def __init__(self):
        QObject.__init__(self)

        self.__s_port = None
        self.__s_speed = None
        self.__s_stream: serial.Serial = None
        self.__read_cycle = 0.05
        self.__read_mode = TpReadMode.TP_READ_MODE_PIPELINE
        self.__report_rcv_handler = lambda: None
        self.__error_handler = lambda: None

        self.__snd_thread: DeviceSendingThread = None
        self.__rcv_thread: DeviceReceiveThread = None

        self.__is_run = False

    def set_serial(self, port, speed):
        self.__s_port = port
        self.__s_speed = speed

    def set_mode(self, mode):
        self.__read_mode = mode

    def set_read_cycle(self, rate):
        self.__read_cycle = rate

    def start(self):
        print('tpreader.start()')
        # open serial
        try:
            self.__s_stream = serial.Serial(
                port=self.__s_port,
                baudrate=self.__s_speed
            )
        except (OSError, serial.SerialException):
            self.error.emit("Can not open %s" % self.__s_port)
            return

        # create sender/receiver thread
        self.__snd_thread = DeviceSendingThread(self.__s_stream)
        self.__snd_thread.set_read_cycle(self.__read_cycle)
        self.__snd_thread.error.connect(lambda error: self.__error('[SND]' + error))
        # self.__snd_thread.register_snd_done_handler()

        self.__rcv_thread = DeviceReceiveThread(self.__s_stream)
        self.__rcv_thread.error.connect(lambda error: self.__error('[RCV]' + error))
        self.__rcv_thread.msg_received.connect(self.__msg_received_handler)

        self.__rcv_thread.start()
        self.__snd_thread.start()

        self.__is_run = True

    def stop(self):
        print('tpreader.stop()')
        self.__rcv_thread.stop()
        self.__snd_thread.stop()

        self.__s_stream.close()

        self.__is_run = False

    def __error(self, error):
        self.stop()
        self.error.emit(error)

    def is_run(self):
        return self.__is_run

    def __msg_received_handler(self, num, frame_bytes):
        if frame_bytes.__len__() != 22 or frame_bytes[2] != 0x08:
            print('unexpected respond')
            return
        tp_report = TpReport(frame_bytes)
        self.new_report.emit(num, tp_report)


class TpReport(QObject):
    def __init__(self, frame_bytes):
        self.header =               frame_bytes[0]
        self.len =                  frame_bytes[1]
        self.cmd_id =               frame_bytes[2]
        self.rw =                   frame_bytes[3]
        self.start_address =        frame_bytes[4]
        self.cnt =                  frame_bytes[5]
        self.version_h =            frame_bytes[6]
        self.version_l =            frame_bytes[7]
        self.device_id =            frame_bytes[8]
        self.touch_status =         frame_bytes[9]
        self.button_status =        frame_bytes[10]
        self.encoder_info =         frame_bytes[11]
        # reverse
        self.l_touch_pos_x =        frame_bytes[13]
        # reverse
        self.l_touch_pos_y =        frame_bytes[15]
        self.l_touch_pos =          frame_bytes[16]
        self.r_touch_pos_x1 =       frame_bytes[17]
        self.r_touch_pos_x2 =       frame_bytes[18]
        self.r_touch_pos_y1 =       frame_bytes[19]
        self.r_touch_pos_y2 =       frame_bytes[20]
        self.r_touch_pos =          frame_bytes[21]

        self.r_touch_pos_x = self.r_touch_pos_x1 + 0XFF * self.r_touch_pos_x2
        self.r_touch_pos_y = self.r_touch_pos_y1 + 0XFF * self.r_touch_pos_y2


class DeviceSendingThread(QThread):
    # read_cmd = bytearray([0xFA, 0x06, 0x08, 0x00, 0x0E, 0x10])
    #                        1     2     3     4     5     6     7     8     9    10    11    12    13    14    15    16    17    18    19    20    21    22
    read_cmd = bytearray([0xFA, 0x16, 0x08, 0x00, 0x0E, 0x10, 0x20, 0x00, 0x30, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x12, 0x00, 0x34, 0x00, 0x0C])

    error = pyqtSignal(str)
    warning = pyqtSignal(str)
    msg_sent = pyqtSignal(int)

    def __init__(self, serial_stream):
        QThread.__init__(self)

        self.__serial_stream: serial.Serial = serial_stream
        self.__read_cycle = 0.05
        self.__stop_req = False
        self.__send_done_handler = lambda: None
        self.__error_handler = lambda: None
        self.__cnt = 0

    def set_read_cycle(self, read_cycle):
        self.__read_cycle = read_cycle

    def register_snd_done_handler(self, f):
        self.__send_done_handler = f

    def register_error_handler(self, f):
        self.__error_handler = f

    def run(self):
        while not self.__stop_req:
            t_start = time.time()
            try:
                self.__serial_stream.write(self.read_cmd)
                self.__cnt += 1
                self.msg_sent.emit(self.__cnt)
            except (OSError, serial.SerialException):
                self.error.emit("Serial writing error")
                return

            t_elapsed = time.time() - t_start
            t_sleep = self.__read_cycle - t_elapsed
            if t_sleep < 0:
                self.warning.emit("Send overload")
            else:
                time.sleep(t_sleep)

    def stop(self):
        self.__stop_req = True


class ReadState(Enum):
    READ_WAIT_HEADER = 1
    READ_WAIT_LENGTH = 2
    READ_PAYLOAD = 3


class DeviceReceiveThread(QThread):
    error = pyqtSignal(str)
    warning = pyqtSignal(str)
    msg_received = pyqtSignal(int, bytearray)

    def __init__(self, serial_stream):
        QThread.__init__(self)

        self.__serial_stream: serial.Serial = serial_stream

        self.__frame_state: ReadState = ReadState.READ_WAIT_HEADER
        self.__frame_len = 0
        self.__frame_bytes = bytearray()
        self.__cnt = 0
        self.__stop_req = False

    def stop(self):
        self.__stop_req = True

    def run(self):
        while not self.__stop_req:
            try:
                rcv_byte = self.__serial_stream.read()
            except (OSError, serial.SerialException):
                self.error.emit('Serial reading error')
                return
            if rcv_byte.__len__() == 0:
                return
            rcv_byte = rcv_byte[0]
            self.process_chr(rcv_byte)

    def start_frame(self):
        self.__frame_bytes = bytearray([0XFA])

    def process_chr(self, rcv_byte):
        if rcv_byte == 0xFA and self.__frame_state != ReadState.READ_WAIT_HEADER:
            self.__frame_fail()
            self.__frame_state = ReadState.READ_WAIT_HEADER
            self.start_frame()

        # >>> READ_WAIT_HEADER <<<<
        if self.__frame_state == ReadState.READ_WAIT_HEADER:
            if rcv_byte == 0xFA:
                self.__frame_state = ReadState.READ_WAIT_LENGTH
                self.start_frame()
            else:
                # >>>>>> FAIL
                self.__frame_fail()
                pass

        # >>> READ_WAIT_LENGTH <<<
        elif self.__frame_state == ReadState.READ_WAIT_LENGTH:
            self.__frame_len = rcv_byte
            self.__frame_bytes.append(rcv_byte)
            self.__frame_state = ReadState.READ_PAYLOAD

        # >>> READ_PAYLOAD <<<
        elif self.__frame_state == ReadState.READ_PAYLOAD:
            self.__frame_bytes.append(rcv_byte)
            if self.__frame_bytes.__len__() == self.__frame_len:
                # >>>>>> DONE
                self.__frame_done(self.__frame_bytes)
                self.__frame_state = ReadState.READ_WAIT_HEADER

    def __frame_done(self, frame_bytes):
        self.__cnt += 1
        self.msg_received.emit(self.__cnt, frame_bytes)

    def __frame_fail(self):
        self.warning.emit("Frame Error")
