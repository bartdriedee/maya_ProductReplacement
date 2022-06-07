import pymel.core as pm
import os, json
import maya.OpenMaya as om
from shutil import copyfile

def loadVray():
    pm.loadPlugin("vrayformaya", quiet=True)


class shaderballs():
    def __init__(self):
        self.my_path = "C:/Users/wen/PycharmProjects/Maya/ShaderBall"
        asset = self.get_asset(self.my_path)
        self.copy_textures(asset)
        pm.importFile(os.path.join(self.my_path, asset["maPath"]))

    def get_asset(self, asset_path):
        with open(os.path.join(asset_path, os.path.basename(asset_path) + ".json"), "r") as json_file:
            my_json = json.load(json_file)
            return my_json

    def copy_textures(self, asset):
        for texture in asset["textureFiles"]:
            src = os.path.join(self.my_path, texture)
            dst = os.path.join(pm.workspace(q=True, rootDirectory=True), "sourceimages", os.path.basename(src))
            if os.path.exists(os.path.dirname(dst)):
                if not os.path.exists(dst):
                    copyfile(src, dst)
            else:
                om.MGlobal.displayError("Path is invalid")



shaderballs()