import numpy as np
import math as m
import random
import nrrd
import sys
import subprocess
import imagej
import time
import csv

# these append statements are required to correctly find ImarisLib and all of its dependencies
# this sys.path.append is the correct way to modify your PYTHONPATH variable
sys.path.append(r'C:\Program Files\Bitplane\Imaris 9.9.0\XT\python3'.replace(r'\\', '/'))
sys.path.insert(0, 'k:/workstation/code/shared/pipeline_utilities/imaris')
import ImarisLib

# TODO: this is actually called 8-bit color, right?
def convert_color_to_8bit(red, green, blue, alpha=0):
    vRGBA = np.array([red, green, blue, alpha], dtype="uint32");
    # my values are already 0-255 scaled, this example assumed 0-1 scale
    #vRGBA = 255 * vRGBA
    #vRGBA = vRGBA.round()
    print("type: {}".format(type(vRGBA)))
    print("type: {}".format(type(vRGBA[0])))
    print("PRE-DOT-PRODUCT vrgba: {}".format(vRGBA))
    vRGBA = np.dot(vRGBA, np.array([1, 256, 256*256, 256*256*256]))
    print("vrgba: {}".format(vRGBA))
    print("type: {}".format(type(vRGBA)))
    vRGBA = np.uint32(np.int32(vRGBA))
    print("after cast: {}".format(vRGBA))
    return vRGBA

def get_color_from_RCCF_csv(csv, index):
    # given an ROI value, return the RGBA (in 0-255 values) for the relevant region
    internal_index = index+3 # to offset from the headers
    print(csv[internal_index])
    r = csv[internal_index][2]
    g = csv[internal_index][3]
    b = csv[internal_index][4]
    a = csv[internal_index][5]
    # temp override of alpha value. csv and imaris assumptions are inverted, but we always want full opacity
    a = 0
    print("RGBA = {} | {} | {} | {}".format(r,g,b,a))
    return convert_color_to_8bit(r, g, b, a)


def read_csv_into_memory(csv_file):
    #data[3] is the first row with ROI values (this is 0, exterior)
    # rows 0-2 are headers. 0 gives short header name, 2 gives more detailed header name. 1 gives???
    # column 0 is ROI number (used for lookup)
    # columns 2,3,4,5 are R,G,B,A channels respectively
        # in 0-255 values
        # in lookup table, alpha=255 is full opacity. Full opacity in imaris is alpha=0
        # note alpha is INVERTED from what imaris expects
    with open(csv_file, mode="r") as f:
        csv_reader = csv.reader(f, delimiter="\t")
        data = [row for row in csv_reader]

    # is there a better way to deal with this?
    # probably I should DELETE the header rows
    # so that for ROI=45, I can just use
        # R = data[45][2]
    # or I could format this down even more to a 360x6 matrix where each row only has:
        # roi_num, roi_name, R, G, B, A
        # i want to keep the name so that I can nicely name the ROIs
    return data


def get_random_color():
#Set the DataItem's color.
    #aValue consists in four bytes encoding the red (least significant byte), green, blue and alpha (most significant byte) components of the color to be set.
    #The range of each component is 0-255. An alpha value of 0 represents full opacity, while 255 means full transparency.
    #\par Example in Matlab:
    #vDataItem = vImarisApplication.GetSurpassSelection;
    vRed = 0.1
    vGreen = 0.2
    vBlue = 0.3
    vAlpha = 0
    vRed = random.random()
    vGreen = random.random()
    vBlue = random.random()
    #vAlpha = 1
    # example matlab code I translated from
    #disp(sprintf('Range 0-1: Red = %%f, green = %%f, blue = %%f, alpha = %%f', vRed, vGreen, vBlue, vAlpha))
    #vRGBA = round(vRGBA * 255); # need integer values scaled to range 0-255
    #vRGBA = uint32(vRGBA * [1, 256, 256*256, 256*256*256]); # combine different components (four bytes) into one integer
    #vDataItem.SetColorRGBA(vRGBA);
    vRGBA = np.array([vRed, vGreen, vBlue, vAlpha]);
    vRGBA = 255 * vRGBA
    vRGBA = vRGBA.round()
    vRGBA = np.dot(vRGBA, np.array([1, 256, 256*256, 256*256*256]))
    vRGBA = np.uint32(np.int32(vRGBA))
    return vRGBA


def GetServer():
    vImarisLib = ImarisLib.ImarisLib()
    vServer = vImarisLib.GetServer()
    return vServer;




output_dir = "B:/ProjectSpace/hmm56/imaris_surfaces/test_results"
RCCF_csv_file = "B:/22.gaj.49/DMBA/Aligned-Data-RAS/labels/RCCF/DMBA_RCCF_labels_lookup.txt"
RCCF_label_colors = read_csv_into_memory(RCCF_csv_file)
#sys.exit("testing")

label_indices = list(range(1, 181, 30)) + list(range(1001, 1181, 30))

# TODO: loading data into imaris is failing now. double check what I did for NeuronCounting
# launch imaris
#imaris_process = subprocess.Popen(['C:\\Program Files\\Bitplane\\Imaris 10.0.0\\Imaris.exe', 'id101'])
# give imaris enough time to open
#time.sleep(10)

# find the imaris application to interact with it (opened by the setup script)
vServer = GetServer()
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
vExtentMin = [img.GetExtendMinX(),img.GetExtendMinY(),img.GetExtendMinZ()]
vExtentMax = [img.GetExtendMaxX(), img.GetExtendMaxY(), img.GetExtendMaxZ()]
print('vExtentMin:',vExtentMin)
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
    v.GetSurpassScene().AddChild(vSur, 1)
    vSur.SetName('Surface ' + str(x))
    # color = colors[i]
    color = get_color_from_RCCF_csv(RCCF_label_colors, x)
    # aValue consists in four bytes encoding the red (least significant byte), green, blue and alpha (most significant byte) components of the color to be set.
    # The range of each component is 0-255. An alpha value of 0 represents full opacity, while 255 means full transparency.
    #vSur.SetColorRGBA(color)
    color = get_random_color()
    gotten_color = vSur.GetColorRGBA()
    print("working on ROI: {}".format(x))
    print("got color: {}".format(gotten_color))
    print("setting color to: {}".format(color))
    vSur.SetColorRGBA(color)
    out_file_path = "{}/{}_surface.ims".format(output_dir, x)

    # TODO: this does not work as expected. It saves the WHOLE IMARIS SCENE
    #v.FileSave(out_file_path, "")
    i = i + 1



