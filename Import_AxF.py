# TODO:
#   - import shaderball scene
#   - exclude files starting with "."

# Dialog to load AxF files into newly created V-Ray AxF_Materials
import maya.app.renderSetup.model.renderLayer as renderLayer
import maya.app.renderSetup.model.renderSetup as renderSetup
import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui
import PySide2.QtCore as QtCore
import shiboken2
import maya.OpenMayaUI as omui
import maya.OpenMaya as om
import pymel.core as pm
import os

def getMainWindow():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

def loadVray():
    pm.loadPlugin("vrayformaya", quiet=True)


class AxFImporter(QtWidgets.QDialog):
    def __init__(self, parent=getMainWindow()):
        super(AxFImporter, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(400, 80)
        self.setWindowTitle("AxFImporter")
        self.setObjectName("AxF_dialog")

        self.inputfield_lbl = QtWidgets.QLabel("AxF files:")
        self.inputfield_lne = QtWidgets.QLineEdit()

        self.path_btn = QtWidgets.QPushButton()
        self.path_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.path_btn.setToolTip("select folder with AxFfiles")

        self.ok_btn = QtWidgets.QPushButton("Apply")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.input_layout = QtWidgets.QHBoxLayout(self)
        self.action_layout = QtWidgets.QHBoxLayout(self)
        self.action_layout.setAlignment(QtCore.Qt.AlignRight)

        self.input_layout.addWidget(self.inputfield_lbl)
        self.input_layout.addWidget(self.inputfield_lne)
        self.input_layout.addWidget(self.path_btn)

        self.action_layout.addWidget(self.ok_btn)
        self.action_layout.addWidget(self.cancel_btn)


        self.main_layout.addLayout(self.input_layout)
        self.main_layout.addLayout(self.action_layout)

        self.path_btn.clicked.connect(self.openDialog)
        self.ok_btn.clicked.connect(self.apply)
        self.cancel_btn.clicked.connect(self.cancel)

    def openDialog(self):
        folder_dialog = QtWidgets.QFileDialog()
        folder = folder_dialog.getExistingDirectory(self, "Select Folder", options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if folder:
            self.inputfield_lne.setText(folder)

    def apply(self):
        if os.path.exists(self.inputfield_lne.text()):
            materials = self.makeMaterials(self.inputfield_lne.text())
            self.doRenderSetup(materials)
            self.setRenderSettings()
            self.close()
        else:
            om.MGlobal.displayError("Path is invalid")

    def cancel(self):
        self.close()

    def makeMaterials(self, search_path):
        materials=[]
        axfs = self.filterAxF(search_path)
        for axf_file in axfs:
            full_path = os.path.join(search_path, axf_file)
            shader_name = "AxF_" + axf_file[:-4]
            # Make material nodes
            material = pm.shadingNode("AxfMaterial", asShader=True, name=shader_name)
            materials.append(material)
            # Point material to AxF file
            pm.setAttr(str(material.AxFFilename), full_path)
        print("{0} AxF materials created".format(len(axfs)))
        return materials


    def doRenderSetup(self,materials):
        # Delete all renderlayers
        render_setup = renderSetup.instance()
        all_render_layers = render_setup.getRenderLayers()
        for i in all_render_layers:
            renderLayer.delete(i)

        for i,material in enumerate(materials):
            # Create and append the render layer
            rl = render_setup.createRenderLayer("Maya_" + material._name)

            # Create and append collections
            my_collection = rl.createCollection("AxF_{0}_collection".format(i))

            # add the object we're overriding to the collection
            my_selector = my_collection.getSelector()
            my_selector.setFilterType(0)
            my_selector.staticSelection.add(["SB_Blend", "CAMERA", "LIGHTS", "GEO"])

            # create a connection override
            my_override = my_collection.createConnectionOverride("SB_Blend", "base_material")
            # give it a name so we can connect to it
            my_override.setName("SB_Blend_{0}_override".format(i))
            # make the connection, note the name of the slot is attrValue
            pm.connectAttr(material._name+".outColor", "SB_Blend_{0}_override.attrValue".format(i), f=True)


    def filterAxF(self, searchPath):
        all_files = os.listdir(searchPath)
        axfs = []
        for file in all_files:
            extension = os.path.splitext(file)[-1][1:]
            if extension.lower() == "axf":
                axfs.append(file)
        return axfs

    def setRenderSettings(self):
        pm.setAttr("perspShape.renderable", 0)
        pm.setAttr("vraySettings.giOn", 1)
        pm.setAttr("vraySettings.imageFormatStr", "png")
        pm.setAttr("vraySettings.fileNamePrefix", "<Camera>/<Scene>/<Layer>", type="string")
        pm.setAttr("vraySettings.width", 1280)
        pm.setAttr("vraySettings.height", 1024)
        pm.setAttr("defaultRenderGlobals.endFrame", 0)
        pm.setAttr("defaultRenderGlobals.startFrame", 0)

if __name__== "__main__":
    for entry in QtWidgets.QApplication.allWidgets():
        if entry.objectName() == "AxF_dialog":
            entry.close()
    loadVray()
    AxF_dialog = AxFImporter()
    AxF_dialog.show()
    print AxF_dialog.objectName()