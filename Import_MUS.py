# Dialog to create rs_BlendMaterials based on the names entered.

import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui
import PySide2.QtCore as QtCore
import shiboken2
import maya.OpenMayaUI as omui
import pymel.core as pm
import string
import os

def get_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

def load_redshift():
    pm.loadPlugin("redshift4maya", quiet=True)

class ImportMUS(QtWidgets.QDialog):
    def __init__(self, parent=get_main_window()):
        super(ImportMUS, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(400, 80)
        self.setWindowTitle("MUS importer")

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.inputfield_lbl = QtWidgets.QLabel("list of parts:")
        self.inputfield_txe = QtWidgets.QPlainTextEdit("materials to be assigned to the GEO")
        self.inputfield_txe.selectAll()

        self.input_layout = QtWidgets.QVBoxLayout(self)
        self.input_layout.addWidget(self.inputfield_lbl)
        self.input_layout.addWidget(self.inputfield_txe)

        self.ok_btn = QtWidgets.QPushButton("Apply")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        self.ok_btn.clicked.connect(self.apply)
        self.cancel_btn.clicked.connect(self.cancel)

        self.action_layout = QtWidgets.QHBoxLayout(self)
        self.action_layout.setAlignment(QtCore.Qt.AlignRight)
        self.action_layout.addWidget(self.ok_btn)
        self.action_layout.addWidget(self.cancel_btn)

        self.main_layout.addLayout(self.input_layout)
        self.main_layout.addLayout(self.action_layout)

    def apply(self):
        part_names = self.cleanup_input(self.inputfield_txe.toPlainText())
        for i, name in enumerate(part_names):
            self.create_rs_blend_material(str(i+1).zfill(2) + "_" + name)
        self.close()

    def cancel(self):
        self.close()

    def cleanup_input(self, text_input):
        alpha_numeric = (string.ascii_letters + string.digits + "_-,")
        comma_separated = text_input.replace(" ", "_").split(",")
        clean_input = []
        for t in comma_separated:
            for line in [s for s in t.splitlines() if s]:
                illegal_chars_removed = "".join([c for c in line if c in alpha_numeric])
                if not illegal_chars_removed[0] in (string.digits + "_-"):
                    if illegal_chars_removed !="":
                        clean_input.append(illegal_chars_removed)
                else:
                    while illegal_chars_removed[0] in (string.digits + "_-"):
                        illegal_chars_removed = illegal_chars_removed[1:]
                        if len(illegal_chars_removed) == 0:
                            break
                    if illegal_chars_removed != "":
                        clean_input.append(illegal_chars_removed)
        if len(clean_input) > 0:
            return clean_input



    def create_rs_blend_material(self,material_name):
        blend_material = pm.shadingNode("RedshiftMaterialBlender", asShader=True, name="rs_" + material_name)


if __name__ == "__main__":
    for entry in QtWidgets.QApplication.allWidgets():
        if entry.objectName() == "MUS_dialog":
            entry.close()
    load_redshift()
    MUS_dialog = ImportMUS()
    MUS_dialog.show()
