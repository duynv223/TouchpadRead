# -*-coding:utf-8-*-
from PyQt5.QtWidgets import *
from tpreader import TpReport


class TpFrameViewer(QTableWidget):
    def __init__(self, parent):
        QTableWidget.__init__(self, parent)

        self.setRowCount(4)
        self.setColumnCount(2)

        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.verticalHeader().setDefaultSectionSize(20)
        self.horizontalHeader().setDefaultSectionSize(75)

        self.setItem(0, 0, QTableWidgetItem("Touch X"))
        self.setItem(1, 0, QTableWidgetItem("Touch Y"))
        self.setItem(2, 0, QTableWidgetItem("Touch Stt"))
        self.setItem(3, 0, QTableWidgetItem("Button Stt"))

    def update_frame(self, report: TpReport):
        self.setItem(0, 1, QTableWidgetItem("%d" % report.r_touch_pos_x))
        self.setItem(1, 1, QTableWidgetItem("%d" % report.r_touch_pos_y))
        self.setItem(2, 1, QTableWidgetItem("0x%02x" % report.touch_status))
        self.setItem(3, 1, QTableWidgetItem("0x%02x" % report.button_status))




