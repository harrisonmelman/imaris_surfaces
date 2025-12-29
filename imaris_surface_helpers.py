# remove unused import statenments
import numpy as np
import random
import sys
import csv
import os 
import logging
import pandas as pd


# TODO: this is actually called 8-bit color, right?
def convert_color_to_8bit(red, green, blue, alpha=0):
    vRGBA = np.array([red, green, blue, alpha], dtype="uint32")
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


def import_ImarisLib():
    # setup imaris connection
    # these append statements are required to correctly find ImarisLib and all of its dependencies
    # this sys.path.append is the correct way to modify your PYTHONPATH variable
    logger = logging.getLogger(__name__)
    logger.debug("sys.path before modification: %s", sys.path)

    imaris_path = r"C:/Program Files/Bitplane/Imaris 11.0.0/Imaris.exe"
    xt_path = r"C:/Program Files/Bitplane/Imaris 11.0.0/XT/python3"
    workstation_imaris_path = "{}/code/shared/pipeline_utilities/imaris".format(os.environ["WORKSTATION_HOME"])
    sys.path.append(imaris_path.replace("/","\\"))
    sys.path.append(xt_path.replace("/","\\"))
    workstation_imaris_path = workstation_imaris_path.replace("/","\\")
    # insert at 0 to put it at front of search path.
    sys.path.insert(0, workstation_imaris_path)
    logger.debug("sys.path after modification: %s", sys.path)
    # only works python > 3.8
    os.add_dll_directory(workstation_imaris_path)
    os.add_dll_directory(xt_path)

    # must run this after modifying PYTHONPATH
    import ImarisLib
    return ImarisLib,imaris_path


def load_white_list(file_path):
    # Read the Excel file into a DataFrame
    # excel is a full 360 rows color lookup table
    # has an extra column at the end called 'in_manuscript_figure' which is either 'yes' or 'nan'
    df = pd.read_excel(file_path)
    length = df.shape[0]
    white_list = [int(df["# ROI"][x]) for x in range(length) if df['in_manuscript_figure'][x] == 'yes']
    return white_list


def check_if_dead_end(node, RCCF_tree):
    # if a node is not an ROI, then it should become a folder
    # BUT, if it does not have any children who are ROI, then we want to ignore it
    # recursively check children to see if we end up with a real ROI
    # if we do not, then we should skip this branch without making a folder
    # only if there are NO real regions in that ENTIRE BRANCH
    #logger.debug("CHECK IF DEAD END was passed node: %s", node)
    if node["ROI_num"] == "NaN":
        # then we are some type of folder
        if not node["children"]:
            # then we have no children. dead end.
            return True
        else:
            # then check each child for dead-endedness
            for child in node["children"]:
                # loop through and if ANY branch is nonempty, then we return false
                if not check_if_dead_end(RCCF_tree[child],RCCF_tree):
                    #logger.debug("Descendents here. Not a dead end. Return false")
                    return False
            # only if we loop trhough all and find no descendents, then do we return True
            #logger.debug("DEAD END")
            return True
    # if ROI_num is a number, then it is an RCCF region. absolutely not a dead end.
    return False