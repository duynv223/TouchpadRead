# -*-coding:utf-8-*-
import sys
import glob
import serial

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QComboBox
from PyQt5.QtCore import pyqtSlot
from tpconfig import TpConfig


def _get_serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


class OpenSerialDialog(QDialog):
    open_clicked = pyqtSlot(str, str)

    # (port, speed)

    def __init__(self, parent, now_port='', now_baudrate=''):
        super().__init__(parent)
        self.parent = parent
        self.baudrates = ['115200', '9600', '4800']
        self.port = None,
        self.baudrate = None
        self.setWindowTitle("Open Serial")
        layout = QtWidgets.QGridLayout()

        # label
        layout.addWidget(QtWidgets.QLabel('Port'), 0, 0)
        layout.addWidget(QtWidgets.QLabel('Speed'), 1, 0)

        # combo box
        # --port name
        self.port_cb = QComboBox()
        ports = _get_serial_ports()
        self.port_cb.addItems(ports)

        if now_port in ports:
            self.port_cb.setCurrentIndex(ports.index(now_port))
        else:
            self.port_cb.setCurrentIndex(0)

        # --baud rate
        self.speed_cb = QtWidgets.QComboBox()
        self.speed_cb.addItems(self.baudrates)

        if now_baudrate in self.baudrates:
            self.speed_cb.setCurrentIndex(self.baudrates.index(now_baudrate))
        else:
            self.speed_cb.setCurrentIndex(0)

        layout.addWidget(self.port_cb, 0, 1)
        layout.addWidget(self.speed_cb, 1, 1)

        # button
        ok_btn = QtWidgets.QPushButton('Open')
        ok_btn.clicked.connect(self.open_slot)
        cancel_btn = QtWidgets.QPushButton('Cancel')
        cancel_btn.clicked.connect(self.close)

        layout.addWidget(ok_btn, 0, 2)
        layout.addWidget(cancel_btn, 1, 2)

        self.setLayout(layout)

    @pyqtSlot()
    def open_slot(self):
        self.port = self.port_cb.currentText()
        self.baudrate = self.speed_cb.currentText()
        if self.port and self.baudrate:
            self.accept()
        else:
            self.reject()

