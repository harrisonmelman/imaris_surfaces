import pickle
import sys
import subprocess
import time
# currently unused
# import os
# from pprint import pprint
import imaris_surface_helpers as imsurf

"""
# this bits just copy pasted from make_label_surfaces as a helpful reference
sys.path.append(r"C:\Program Files\Bitplane\Imaris 9.9.0\XT\python3".replace(r"\\", "/"))
sys.path.insert(0, "k:/workstation/code/shared/pipeline_utilities/imaris")
import ImarisLib
from prototype_make_label_surfaces import read_csv_into_memory, GetServer
vServer = GetServer()
vImarisLib = ImarisLib.ImarisLib()
v = vImarisLib.GetApplication(101)
# the factory creates objects
factory = v.GetFactory()
# the scene handles adding forged objects to the scene
# there must be at least one item in the scene before this is ran or scene will be set to None
scene = v.GetSurpassScene()


factory = v.GetFactory()
# create new folder (generic name)
container=factory.CreateDataContainer()
# add folder to scene
v.GetSurpassScene().AddChild(container)
# add a surface to the new container
container.AddChild(surface,-1)
"""


# def create_surface(roi_num, RCCF_label_colors):
def create_surface(node):
    roi_num = int(node["ROI_num"])
    label_bounds = [roi_num - 0.5, roi_num + 0.5]
    surface = imaris_app.GetImageProcessing().DetectSurfacesWithUpperThreshold(img, [], 0, 0, 0, True, False,
                                                                               label_bounds[0], True, False,
                                                                               label_bounds[1], None)
    print("create surface for ROI: {}".format(roi_num))
    # last argument is alpha. 0 gives full opacity
    color = imsurf.convert_color_to_8bit(node["red"], node["green"], node["blue"], 0)
    surface.SetColorRGBA(color)
    return surface


# node is a Dict entry in the RCCF label tree
# parent_group is an imaris group object (a folder)
def traverse(node, parent_group):
    if node is None:
        return
    # children = node["children"]
    # name = node["structure_name"]
    # then create surface
    # if children is None:
    # checking for empty list
    if not node["children"]:
        # TODO: what do I do with these? Ignore them?
        if node["ROI_num"] == "NaN":
            return
        print("THIS IS AN EXPLICIT ROI. CREATING SURFACE")
        # pprint(node)
        # TODO: name the surface as node["structure_name"]
        print("\troi: {}\n\tstructure_id: {}\n\tstructure_name: {}".format(node["ROI_num"], node["structure_id"],
                                                                           node["structure_name"]))
        surface = create_surface(node)
        surface.SetName(node["structure_name"])
        parent_group.AddChild(surface, -1)
        return
    # else it is a group
    container = factory.CreateDataContainer()
    container.SetName(node["structure_name"])
    parent_group.AddChild(container, -1)
    for child in node["children"]:
        traverse(RCCF_tree[child], container)
    return


# MAIN
# if you want this script to handle imaris launch and data load
# if false, will only sea4rch for application 101 and load image 0 from the scene. be careful.
open_imaris = False

# whole brain root
root_structure_id = 997
output_dir = "B:/ProjectSpace/hmm56/imaris_surfaces/test_results"
RCCF_tree_file = "B:/ProjectSpace/hmm56/imaris_surfaces/RCCF_tree.pkl"
RCCF_csv_file = "K:/workstation/static_data/atlas/symmetric15um/labels/RCCF/symmetric15um_RCCF_labels_lookup.txt"
label_imaris_path = r"B:\22.gaj.49\DMBA\Aligned-Data\Other\ims\labels\RCCF\DMBA_RCCF_labels.ims"
RCCF_label_colors = imsurf.read_csv_into_memory(RCCF_csv_file)

# launch imaris
# old version
# imaris_path = r"C:\Program Files\Bitplane\Imaris 10.1.1\Imaris.exe"
# xt_path = r"C:\Program Files\Bitplane\Imaris 10.1.1\XT\python3"
imaris_path = r"C:/Program Files/Bitplane/Imaris 10.1.1/Imaris.exe"
xt_path = r"C:/Program Files/Bitplane/Imaris 10.1.1/XT/python3"
imaris_path = r"C:/Program Files/Bitplane/Imaris 10.1.1/Imaris.exe"
xt_path = 'C:\\Program Files\\Bitplane\\Imaris 10.1.1\\XT\\python3'

if open_imaris:
    imaris_process = subprocess.Popen([imaris_path, "id101"])
    # give imaris enough time to open
    time.sleep(10)

# TODO: maybe put this whole bundle of code into a module function. returns imaris_[lib,server,app]
# setup imaris connection
# these append statements are required to correctly find ImarisLib and all of its dependencies
# this sys.path.append is the correct way to modify your PYTHONPATH variable
sys.path.append(imaris_path)
sys.path.append(xt_path)
sys.path.insert(0, "k:/workstation/code/shared/pipeline_utilities/imaris")
# to fix DLL load failure. only loads from trusted sources.
# probably will not work since pthon < 3.8
import ImarisLib

imaris_lib = ImarisLib.ImarisLib()
imaris_server = imaris_lib.GetServer()
# previously v
imaris_app = imaris_lib.GetApplication(101)
factory = imaris_app.GetFactory()
# load label file programatically
load_options = ""
if open_imaris:
    imaris_app.FileOpen(label_imaris_path, load_options)
# load only the label file so that this is unambiguous
img = imaris_app.GetImage(0)

from pprint import pprint

with open(RCCF_tree_file, "rb") as f:
    RCCF_tree = pickle.load(f)
    root = RCCF_tree[root_structure_id]
    # the parent of the root node is the root of the imaris filesystem
    traverse(root, imaris_app.GetSurpassScene())
