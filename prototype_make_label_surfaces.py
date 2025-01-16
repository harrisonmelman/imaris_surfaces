import sys
import subprocess
import time
import pickle

# currently unused imports. consider removing
import numpy as np
import math as m
import random
import nrrd
import imagej
import csv
import imaris_surface_helpers

# these append statements are required to correctly find ImarisLib and all of its dependencies
# this sys.path.append is the correct way to modify your PYTHONPATH variable
sys.path.append(r'C:\Program Files\Bitplane\Imaris 9.9.0\XT\python3'.replace(r'\\', '/'))
sys.path.insert(0, 'k:/workstation/code/shared/pipeline_utilities/imaris')
# this is all of a sudden giving me a DLL load failre
# maybe it is a shortcoming of pycharm console??
# no module. wrong py version?
#import ImarisLib





########### MAIN ###########
RCCF_tree_file = "B:/ProjectSpace/hmm56/imaris_surfaces/RCCF_tree.pkl"
with open(RCCF_tree_file, 'wb') as f:
    RCCF_tree = pickle.load(f)

output_dir = "B:/ProjectSpace/hmm56/imaris_surfaces/test_results"
# TODO change to symmnetric15 labels, DMBA labels are out of date
RCCF_csv_file = "K:/workstation/static_data/atlas/symmetric15um/labels/RCCF/symmetric15um_RCCF_labels_lookup.txt"
#RCCF_csv_file = "B:/22.gaj.49/DMBA/Aligned-Data-RAS/labels/RCCF/DMBA_RCCF_labels_lookup.txt"
RCCF_label_colors = imaris_surface_helpers.read_csv_into_memory(RCCF_csv_file)
#sys.exit("testing")

label_indices = list(range(1, 181, 30)) + list(range(1001, 1181, 30))

# TODO: loading data into imaris is failing now. double check what I did for NeuronCounting
# launch imaris
imaris_process = subprocess.Popen(['C:\\Program Files\\Bitplane\\Imaris 10.1.1\\Imaris.exe', 'id101'])
# give imaris enough time to open
time.sleep(10)

# find the imaris application to interact with it (opened by the setup script)
vServer = imaris_surface_helpers.GetServer()
vImarisLib = ImarisLib.ImarisLib()
v = vImarisLib.GetApplication(101)

# probably not necessary for this task
#ij = imagej.init(r'K:\CIVM_Apps\Fiji.app', mode='interactive')

# input data
label_imaris_path = "B:\22.gaj.49\DMBA\Aligned-Data\Other\ims\labels\RCCF\DMBA_RCCF_labels.ims"

# load data into imaris
load_options = ""
#v.FileOpen(label_imaris_path, load_options)

# load only the label volume. Then, volume 0 is the labelset
img = v.GetImage(0)
vExtentMin = [img.GetExtendMinX(), img.GetExtendMinY(), img.GetExtendMinZ()]
vExtentMax = [img.GetExtendMaxX(), img.GetExtendMaxY(), img.GetExtendMaxZ()]
print('vExtentMin:', vExtentMin)
aChannel = 0

label_indices = [1, 15, 30, 90, 145]
# 0x means hex number
# but hex gives an error
# values in 0-255 give good values
colors = [0xFFFF00FF, 0xFF00FFFF, 0xFF0000FF, 0xFFFF0000, 0xFF00FF00]
#colors = [0, 230, 45, 145, 255]
i = 0
# generate a surface for each label
for x in label_indices:
    label_bounds = [x-0.5, x+0.5]
    vSur = v.GetImageProcessing().DetectSurfacesWithUpperThreshold(img, [], aChannel, 0, 0, True, False, label_bounds[0], True, False, label_bounds[1], None)
    vSur.SetName('Surface ' + str(x))
    # color = colors[i]

    color = imaris_surface_helpers.get_color_from_RCCF_csv(RCCF_label_colors, x)
    # aValue consists in four bytes encoding the red (least significant byte), green, blue and alpha (most significant byte) components of the color to be set.
    # The range of each component is 0-255. An alpha value of 0 represents full opacity, while 255 means full transparency.
    #vSur.SetColorRGBA(color)
    color = imaris_surface_helpers.get_random_color()
    gotten_color = vSur.GetColorRGBA()
    print("working on ROI: {}".format(x))
    print("got color: {}".format(gotten_color))
    print("setting color to: {}".format(color))

    vSur.SetColorRGBA(color)
    v.GetSurpassScene().AddChild(vSur, 1)
    i = i + 1





"""factory = v.GetFactory()
# create new folder (generic name)
container=factory.CreateDataContainer()
# add folder to scene
v.GetSurpassScene().AddChild(container)
# add a surface to the new container
container.AddChild(surface,-1)"""



