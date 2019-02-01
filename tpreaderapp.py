# -*-coding:utf-8-*-
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from open_serial_dialog import OpenSerialDialog

from tptracker import TpTracker
from tpreader import TpReader, TpReport
from tpconfig import TpConfig
from tpframeviewer import TpFrameViewer


class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = 'Touch Reader'
        self.left = 50
        self.top = 50
        self.width = 640
        self.height = 400

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # self.__tptracker = TpTracker()

        self.__config = TpConfig().config

        self.__tp_reader = TpReader()
        self.__tp_reader.error.connect(self.on_tp_error)
        self.__tp_reader.new_report.connect(self.on_new_report)


        # -------------------------------------------------------------
        # Menu Bar                                                    -
        # -------------------------------------------------------------
        main_menu = self.menuBar()
        file_menu = main_menu.addMenu('File')
        edit_menu = main_menu.addMenu('Edit')
        # view_menu = main_menu.addMenu('View')
        # search_menu = main_menu.addMenu('Search')
        tools_menu = main_menu.addMenu('Tools')
        # help_menu = main_menu.addMenu('Help')

        # -------------------------------------------------------------
        # Action                                                      -
        # -------------------------------------------------------------
        # open serial port
        self.connect_device_action = QAction(QIcon(':/images/connect.png'), 'Connect Device', self)
        self.connect_device_action.setStatusTip('Connect Device')
        self.connect_device_action.triggered.connect(self.on_connect)
        file_menu.addAction(self.connect_device_action)

        self.disconnect_device_action = QAction(QIcon(':/images/connect.png'), 'Disconnect Device', self)
        self.disconnect_device_action.setStatusTip('Disconnect Device')
        self.disconnect_device_action.triggered.connect(self.on_disconnect)
        file_menu.addAction(self.disconnect_device_action)

        self.setting_action = QAction(QIcon(':/images/connect.png'), 'Setting', self)
        self.setting_action.setStatusTip('Connect Device')
        self.setting_action.triggered.connect(self.on_setting)
        file_menu.addAction(self.setting_action)

        # -------------------------------------------------------------
        # Action                                                      -
        # -------------------------------------------------------------
        self.__frame_viewer = TpFrameViewer(self)
        self.setCentralWidget(self.__frame_viewer)

        self.show()

    def on_open_serial(self):
        dialog = OpenSerialDialog(self)
        if dialog.exec_():
            print('OK')
        else:
            print('Cancel')

    def on_connect(self):
        if self.__tp_reader.is_run():
            return
        port = self.__config['port']
        speed = self.__config['speed']
        read_cycle = self.__config['read_cycle']

        self.__tp_reader.set_serial(port, speed)
        self.__tp_reader.set_read_cycle(read_cycle)

        self.__tp_reader.start()

    def on_disconnect(self):
        self.__tp_reader.stop()

    def on_setting(self):
        pass

    def on_clear_touch_tracker(self):
        pass

    def on_new_report(self, num, report: TpReport):
        print("[%d][%3d][3d]", num, report.r_touch_pos_x, report.r_touch_pos_y)
        self.__frame_viewer.update_frame(report)

    def on_tp_error(self, error):
        print("tp error: ", error)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
