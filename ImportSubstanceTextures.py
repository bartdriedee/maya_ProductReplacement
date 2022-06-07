#Dialog to load textures exported from substance and create a rs_Material with these textures connected.

import pymel.core as pm
import os
import collections
import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui
import PySide2.QtCore as QtCore
import shiboken2
import maya.OpenMayaUI as omui
import maya.OpenMaya as om


def getMainWindow():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

def loadRedShift():
    pm.loadPlugin("redshift4maya", quiet=True)


map_types = ["anisotropyangle", "anisotropylevel", "basecolor", "clearcoatlevel", "clearcoatnormal", "height", "metallic", "normal", "roughness", "specularlevel"]
slots = ["refl_aniso_rotation", "refl_aniso", "diffuse_color", "coat_weight", "coat_bump_input", "bump_input","refl_metalness", "bump_input", "refl_roughness","refl_reflectivity"]

def SetupMaterials(my_path):
    loadRedShift()
    texture_dicts = getTextureDicts(my_path)
    material_names = getMaterialNames(texture_dicts)

    for i, mat in enumerate(material_names):
        material = createMaterial(mat)
        textures_per_material = [tex for tex in texture_dicts if tex["material"] == material_names[i]]
        for tex in textures_per_material:
            file_texture = createFileTexture(tex)
            connectTexture(material, file_texture)

def setTextureProperties(folder, filename):
    texture = {
    "name" : filename[:-4],
    "path" : os.path.join(folder, filename),
    "material" : filename[:-4][:filename.rfind("_")],
    "map_type" : filename[:-4][filename[:-4].rfind("_")+1:]
    }
    return texture

def getTextureDicts(search_path):
    file_texture_names = []
    for filename in os.listdir(search_path):
        name, extension = os.path.splitext(filename)
        if extension == ".exr".lower() or extension == ".jpg".lower() or extension == ".png".lower():
            new_texture = setTextureProperties(search_path,filename)
            if new_texture["map_type"] in map_types:
                file_texture_names.append(new_texture)
    return file_texture_names

def getMaterialNames(texture_list):
    materials = []
    for t in texture_list:
        materials.append(t["material"])
    return list(collections.Counter(materials))

def createMaterial(material_name):
    material = pm.shadingNode("RedshiftMaterial", asShader=True, name="rs_"+material_name)
    pm.setAttr(material.refl_fresnel_mode, 2)
    pm.setAttr(material.refl_brdf, 1)
    return material

def createFileTexture(texture):
    file_texture_node = pm.shadingNode('file', asTexture=True, isColorManaged=True, name=texture["map_type"])
    pm.setAttr(file_texture_node.fileTextureName, texture["path"])
    if texture["map_type"]=="basecolor" or texture["map_type"]=="specularlevel":
        pm.setAttr(file_texture_node.colorSpace, "sRGB")
    else:
        pm.setAttr(file_texture_node.colorSpace, "Raw")
    p2d = pm.shadingNode('place2dTexture', name=texture["map_type"] + "_p2d", asUtility=True)
    pm.connectAttr(p2d.outUV, file_texture_node.uvCoord)
    pm.connectAttr(p2d.outUvFilterSize, file_texture_node.uvFilterSize)
    pm.connectAttr(p2d.vertexCameraOne, file_texture_node.vertexCameraOne)
    pm.connectAttr(p2d.vertexUvOne, file_texture_node.vertexUvOne)
    pm.connectAttr(p2d.vertexUvThree, file_texture_node.vertexUvThree)
    pm.connectAttr(p2d.vertexUvTwo, file_texture_node.vertexUvTwo)
    pm.connectAttr(p2d.coverage, file_texture_node.coverage)
    pm.connectAttr(p2d.mirrorU, file_texture_node.mirrorU)
    pm.connectAttr(p2d.mirrorV, file_texture_node.mirrorV)
    pm.connectAttr(p2d.noiseUV, file_texture_node.noiseUV)
    pm.connectAttr(p2d.offset, file_texture_node.offset)
    pm.connectAttr(p2d.repeatUV, file_texture_node.repeatUV)
    pm.connectAttr(p2d.rotateFrame, file_texture_node.rotateFrame)
    pm.connectAttr(p2d.rotateUV, file_texture_node.rotateUV)
    pm.connectAttr(p2d.stagger, file_texture_node.stagger)
    pm.connectAttr(p2d.translateFrame, file_texture_node.translateFrame)
    pm.connectAttr(p2d.wrapU, file_texture_node.wrapU)
    pm.connectAttr(p2d.wrapV, file_texture_node.wrapV)
    texture["node"]=file_texture_node
    return texture

def connectTexture(material,texture):
    index = map_types.index(texture["map_type"])
    input_slot = (material + "." + slots[index])

    if index <2 or index ==3 or index ==6 or index==8:
        output= (texture["node"]+".outAlpha")
    else:
        output = (texture["node"] + ".outColor")

    # if bump- or normal-maps:
    if index ==4 or index ==5 or index == 7:
        # insert blender before bumpnode
        if not pm.listConnections(input_slot):
            bb = pm.shadingNode("RedshiftBumpBlender", asUtility=True, name=material._name+"_bb")
            pm.connectAttr(bb.outColor, input_slot)
            pm.setAttr(bb.additive, 1)
        else:
            bb = pm.listConnections(input_slot)[0]

        bm = pm.shadingNode("RedshiftBumpMap", asUtility=True, name=material._name + "_bm")

        # connect bumpnode to blender
        if not pm.listConnections(bb, s=True, d=False):
            pm.connectAttr(bm.out, bb.baseInput)
        else:
            connection_number = len(pm.listConnections(bb, s=True, d=False))-1
            pm.connectAttr(bm.out, (bb +".bumpInput"+str(connection_number)))
            pm.setAttr((bb + ".bumpWeight" + str(connection_number)), 1)

        # set bump type
        if index == 5:
            # set inputType to Height
            pm.setAttr(bm.inputType, 0)
        else:
            # set inputType to TangentSpace Normals
            pm.setAttr(bm.inputType, 1)
        input_slot = bm.input

    pm.connectAttr(output, input_slot)


class SubstanceTextureImporter(QtWidgets.QDialog):
    def __init__(self, parent=getMainWindow()):
        super(SubstanceTextureImporter, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(400, 80)
        self.setWindowTitle("Substance Texture Importer")
        self.setObjectName("subs_texture_dialog")

        self.inputfield_lbl = QtWidgets.QLabel("texture files:")
        self.inputfield_lne = QtWidgets.QLineEdit()

        self.path_btn = QtWidgets.QPushButton()
        self.path_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.path_btn.setToolTip("select folder with texture maps")

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
            self.import_textures(self.inputfield_lne.text())
            self.close()
        else:
            om.MGlobal.displayError("Path is invalid")

    def cancel(self):
        self.close()

    def import_textures(self, search_path):
        print "importing"
        SetupMaterials(search_path)


if __name__== "__main__":
    for entry in QtWidgets.QApplication.allWidgets():
        if entry.objectName() == "subs_texture_dialog":
            entry.close()

    tex_dialog = SubstanceTextureImporter()
    tex_dialog.show()
