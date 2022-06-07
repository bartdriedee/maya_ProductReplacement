# Simple 2 column interface to set the baseColor for all rs_BlendMaterials in a scene.

import PySide2.QtWidgets as QtWidgets
import PySide2.QtCore as QtCore
import shiboken2
import maya.OpenMayaUI as omui
import pymel.core as pm


def getMainWindow():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(long(main_window_ptr), QtWidgets.QWidget)


def loadVray():
    pm.loadPlugin("vrayformaya", quiet=True)


class MaterialLinker(QtWidgets.QDialog):
    def __init__(self, parent=getMainWindow()):
        super(MaterialLinker, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(450, 80)
        self.setWindowTitle("Material Linker")
        self.setObjectName("MaterialLinker")

        self.ok_btn = QtWidgets.QPushButton("Apply")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")

        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.blend_materials_layout = QtWidgets.QVBoxLayout(self)
        self.base_materials_layout = QtWidgets.QVBoxLayout(self)
        self.materials_layout = QtWidgets.QHBoxLayout(self)
        self.materials_layout.addLayout(self.blend_materials_layout)
        self.materials_layout.addLayout(self.base_materials_layout)
        self.fillMaterialLayout()

        self.action_layout = QtWidgets.QHBoxLayout(self)
        self.action_layout.setAlignment(QtCore.Qt.AlignRight)

        self.action_layout.addWidget(self.ok_btn)
        self.action_layout.addWidget(self.cancel_btn)

        self.materials_intermediate_widget = QtWidgets.QWidget()
        self.materials_intermediate_widget.setLayout(self.materials_layout)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setFocusPolicy(QtCore.Qt.NoFocus)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame);
        self.scroll_area.setWidget(self.materials_intermediate_widget)

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.addLayout(self.action_layout)

        self.ok_btn.clicked.connect(self.apply)
        self.cancel_btn.clicked.connect(self.cancel)

    def apply(self):
        self.doSomething()

    def cancel(self):
        self.close()

    def doSomething(self):
        for i in range(self.blend_materials_layout.count()):
            pm.connectAttr(pm.PyNode(self.base_materials_layout.itemAt(i).widget().currentText()).outColor, pm.PyNode(self.blend_materials_layout.itemAt(i).widget().text()).baseColor, force=True)
        self.close()

    def fillMaterialLayout(self):
        for lbl in self.getBlendMaterials():
            self.blend_materials_layout.addWidget(lbl)
            dropdown = self.getBaseMaterials()
            self.base_materials_layout.addWidget(dropdown)
        self.setBaseMaterials(dropdown)

    def getBlendMaterials(self):
        materials = [material for material in pm.ls(mat=True) if material.type() == "RedshiftMaterialBlender"]
        blend_lbls = []
        for material in materials:
            blend_lbls.append(QtWidgets.QLabel(material._name))
            blend_lbls[-1].setMinimumHeight(35)
        return blend_lbls

    def getBaseMaterials(self):
        materials = [material for material in pm.ls(mat=True) if material.type() == "RedshiftMaterial"]
        str_materials = map(lambda x: x._name, materials)
        str_materials.sort()
        base_cbx = QtWidgets.QComboBox()
        base_cbx.setMinimumHeight(35)
        base_cbx.addItems(str_materials)
        return base_cbx

    def setBaseMaterials(self,dropdown):
        for i in range(self.blend_materials_layout.count()):
            if pm.listConnections(pm.PyNode(self.blend_materials_layout.itemAt(i).widget().text()).baseColor):
                for x in range(dropdown.count()):
                    if dropdown.itemText(x) == pm.listConnections(pm.PyNode(self.blend_materials_layout.itemAt(i).widget().text()).baseColor)[0]._name:
                        self.base_materials_layout.itemAt(i).widget().setCurrentIndex(x)


if __name__ == "__main__":
    for entry in QtWidgets.QApplication.allWidgets():
        if entry.objectName() == "MaterialLinker":
            entry.close()
    loadVray()
    material_linker_dialog = MaterialLinker()
    material_linker_dialog.show()