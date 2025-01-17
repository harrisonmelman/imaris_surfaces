# remove unused import statenments
import numpy as np
import math as m
import random
import nrrd
import sys
import subprocess
import imagej
import time
import csv
import pickle


# TODO: this is actually called 8-bit color, right?
def convert_color_to_8bit(red, green, blue, alpha=0):
    vRGBA = np.array([red, green, blue, alpha], dtype="uint32")
    # my values are already 0-255 scaled, this example assumed 0-1 scale
    # vRGBA = 255 * vRGBA
    # vRGBA = vRGBA.round()
    print("type: {}".format(type(vRGBA)))
    print("type: {}".format(type(vRGBA[0])))
    print("PRE-DOT-PRODUCT vrgba: {}".format(vRGBA))
    vRGBA = np.dot(vRGBA, np.array([1, 256, 256 * 256, 256 * 256 * 256]))
    print("vrgba: {}".format(vRGBA))
    print("type: {}".format(type(vRGBA)))
    vRGBA = np.uint32(np.int32(vRGBA))
    print("after cast: {}".format(vRGBA))
    return vRGBA


def get_color_from_RCCF_csv(csv, index):
    # deprecated function. the tree dict has the color information. just call convert_color_to_8bit with that rgba vals
    return
    # given an ROI value, return the RGBA (in 0-255 values) for the relevant region
    internal_index = index + 3  # to offset from the headers
    # internal_index = index + 3  # for longer Rob header
    r = csv[internal_index][2]
    g = csv[internal_index][3]
    b = csv[internal_index][4]
    a = csv[internal_index][5]
    # temp override of alpha value. csv and imaris assumptions are inverted, but we always want full opacity
    a = 0
    print("RGBA = {} | {} | {} | {}".format(r, g, b, a))
    return convert_color_to_8bit(r, g, b, a)


# TODO:
# find parent structure ID columns
# find structure ID column
# structure ids are only bilateral. will have to manually sort out (by roi number) the left or the right side
# only try to make a bilateral tree (no left parent or right parent. just total parent)
def read_csv_into_memory(csv_file):
    # data[3] is the first row with ROI values (this is 0, exterior)
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


# gives me nice numerical sorting when my inputs are strings
# helps handle NaN and empty string and other non numerical issues
def safe_sort_field(x):
    print('SAFE SORT')
    print(x)
    if len(x) == 0:
        return -1
    return float(x)


def get_random_color():
    # Set the DataItem's color.
    # aValue consists in four bytes encoding the red (least significant byte), green, blue and alpha (most significant byte) components of the color to be set.
    # The range of each component is 0-255. An alpha value of 0 represents full opacity, while 255 means full transparency.
    # \par Example in Matlab:
    # vDataItem = vImarisApplication.GetSurpassSelection;
    vRed = 0.1
    vGreen = 0.2
    vBlue = 0.3
    vAlpha = 0
    vRed = random.random()
    vGreen = random.random()
    vBlue = random.random()
    # vAlpha = 1
    # example matlab code I translated from
    # disp(sprintf('Range 0-1: Red = %%f, green = %%f, blue = %%f, alpha = %%f', vRed, vGreen, vBlue, vAlpha))
    # vRGBA = round(vRGBA * 255); # need integer values scaled to range 0-255
    # vRGBA = uint32(vRGBA * [1, 256, 256*256, 256*256*256]); # combine different components (four bytes) into one integer
    # vDataItem.SetColorRGBA(vRGBA);
    vRGBA = np.array([vRed, vGreen, vBlue, vAlpha]);
    vRGBA = 255 * vRGBA
    vRGBA = vRGBA.round()
    vRGBA = np.dot(vRGBA, np.array([1, 256, 256 * 256, 256 * 256 * 256]))
    vRGBA = np.uint32(np.int32(vRGBA))
    return vRGBA


def GetServer():
    imaris_lib = ImarisLib.ImarisLib()
    imaris_server = imaris_lib.GetServer()
    return imaris_server
