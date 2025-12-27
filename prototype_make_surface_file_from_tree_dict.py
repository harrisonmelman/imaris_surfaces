import logging
import pickle
import sys
import subprocess
import time
import os

# from pprint import pprint
import imaris_surface_helpers as imsurf
import pandas as pd

# Define logger at the module level
logger = logging.getLogger(__name__)

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
DEBUG=True

# def create_surface(roi_num, RCCF_label_colors):
def create_surface(node):
    roi_num = int(node["ROI_num"])
    label_bounds = [roi_num - 0.5, roi_num + 0.5]
    surface = imaris_app.GetImageProcessing().DetectSurfacesWithUpperThreshold(img, [], 0, 0, 0, True, False,
                                                                               label_bounds[0], True, False,
                                                                               label_bounds[1], None)
    logger.info("Creating surface for ROI: %s", roi_num)
    # last argument is alpha. 0 gives full opacity
    color = imsurf.convert_color_to_8bit(node["red"], node["green"], node["blue"], 0)
    surface.SetColorRGBA(color)
    return surface


def check_if_dead_end(node):
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
                if not check_if_dead_end(RCCF_tree[child]):
                    #logger.debug("Descendents here. Not a dead end. Return false")
                    return False
            # only if we loop trhough all and find no descendents, then do we return True
            #logger.debug("DEAD END")
            return True
    # if ROI_num is a number, then it is an RCCF region. absolutely not a dead end. 
    return False


# node is a Dict entry in the RCCF label tree
# parent_group is an Imaris group object (a folder)
def traverse(node, parent_group):
    """Creates a single imaris file with a hierarchial RCCF tree surfaces object
    group strutures are represented as groups (folders) and rois are represented as surface objects"""
    logger.debug("Current node in traverse: %s", node)
    if node is None:
        logger.debug("Node is None in traverse. Return.")
        return
    # checking for empty list
    if not node["children"]:
        # TODO: what do I do with these? Ignore them?
        if node["ROI_num"] == "NaN":
            return
        logger.info("Explicit ROI found in traverse. Creating surface.")
        # pprint(node)
        # TODO: name the surface as node["structure_name"]
        logger.info("ROI Details: Number: %s, ID: %s, Name: %s",
                    node["ROI_num"], node["structure_id"], node["structure_name"])
        surface = create_surface(node)
        surface.SetName(node["structure_name"])
        parent_group.AddChild(surface, -1)
        return
    # else it is a group
    logger.debug("Return value of check_if_dead_end for node %s: %s", node.get("structure_id", "N/A"), check_if_dead_end(node))
    if not check_if_dead_end(node):
        logger.debug("Node %s is a group and not a dead end. Keep traversing.", node.get("structure_id", "N/A"))
        container = factory.CreateDataContainer()
        container.SetName(node["structure_name"])
        parent_group.AddChild(container, -1)
        for child in node["children"]:
            logger.debug("Calling traverse on child: %s", child)
            traverse(RCCF_tree[child], container)
        return
    else:
        logger.debug("Node %s is a dead end or already processed. Return.", node.get("structure_id", "N/A"))
        return


def flat_traverse(node,
                  default_parent_group,
                  white_list=None,
                  left_right_split=False,
                  left_container_for_split=None,
                  right_container_for_split=None):
    """This approach ignores the hierarchy. Creates a surface object per roi
    This function should save all of the regions to separate files"""
    # basically, it traverses as normally
    # but it always passes the root node as parent_group to prevent hierarchies
    # and it does not create the folder structure
    # white list is an optional argument, if True, it will generate ONLY the asked for regions
    #logger.debug("passed white_list: %s", white_list) if white_list is not None else logger.debug("white_list is None")
    if node is None:
        logger.debug("Node is None in flat_traverse. Return.")
        return
    # checking for empty list
    if not node["children"]:
        if node["ROI_num"] == "NaN":
            return
        if white_list is not None:
            try:
                current_roi_num_int = int(node["ROI_num"])
                if current_roi_num_int not in white_list:
                    logger.debug("ROI %s is not in the white list. Skipping.", current_roi_num_int)
                    return
                logger.debug("ROI %s is in the white list. Creating surface.", current_roi_num_int)
            except ValueError:
                logger.warning("Invalid ROI_num '%s' for node %s while checking whitelist. Skipping.", node["ROI_num"], node["structure_name"])
                return

        logger.info("Explicit ROI found in flat_traverse. Creating surface.")
        logger.info("ROI Details: Number: %s, ID: %s, Name: %s",
                    node["ROI_num"], node["structure_id"], node["structure_name"])
        surface = create_surface(node)
        surface.SetName(node["structure_name"])

        # Decide where to add the surface
        if left_right_split and left_container_for_split and right_container_for_split:
            try:
                roi_num_int = int(node["ROI_num"])
                if roi_num_int < 181:  # Condition for "left"
                    left_container_for_split.AddChild(surface, -1)
                    logger.info("Added surface '%s' (ROI %s) to LEFT container '%s'", node["structure_name"], roi_num_int, left_container_for_split.GetName())
                else:
                    right_container_for_split.AddChild(surface, -1)
                    logger.info("Added surface '%s' (ROI %s) to RIGHT container '%s'", node["structure_name"], roi_num_int, right_container_for_split.GetName())
            except ValueError:
                logger.warning("Could not convert ROI_num '%s' to int for L/R split. Adding to default parent.", node["ROI_num"])
                default_parent_group.AddChild(surface, -1)
        else:
            default_parent_group.AddChild(surface, -1)
            logger.info("Added surface '%s' (ROI %s) to default parent group '%s'", node["structure_name"], node["ROI_num"], default_parent_group.GetName())
        return
    # else it is a group
    if not check_if_dead_end(node):
        for child in node["children"]:
            flat_traverse(RCCF_tree[child], default_parent_group,
                          white_list=white_list, left_right_split=left_right_split,
                          left_container_for_split=left_container_for_split,
                          right_container_for_split=right_container_for_split)
        return
    else:
        #logger.debug("Node %s is a dead end or already processed in flat_traverse. Return.", node.get("structure_id", "N/A"))
        return


def load_white_list(file_path):
    # Read the Excel file into a DataFrame
    # excel is a full 360 rows color lookup table
    # has an extra column at the end called 'in_manuscript_figure' which is either 'yes' or 'nan'
    df = pd.read_excel(file_path)
    length = df.shape[0]
    white_list = [int(df["# ROI"][x]) for x in range(length) if df['in_manuscript_figure'][x] == 'yes']
    return white_list


if __name__ == "__main__":
    # Configure logging as the first thing in the main execution block
    log_level = logging.DEBUG if DEBUG else logging.INFO
    logging.basicConfig(
        level=log_level,
        stream=sys.stdout,  # Direct logs to stdout
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # if you want this script to handle imaris launch and data load
    # if false, will only search for application 101 and load image 0 from the scene. be careful.
    open_imaris = False
    SPLIT_LEFT_RIGHT = True # Set to True to enable left/right group splitting

    white_list_file = "B:/20.5xfad.01/BXD77_paper/imaris_figure/bxd77_5xfadpaper_figure_colors.xlsx"
    white_list = load_white_list(white_list_file)
    logging.debug("Found white list: %s", white_list) if white_list is not None else logging.debug("white_list not found")

    output_dir = "B:/ProjectSpace/hmm56/imaris_surfaces/test_results/2025"
    RCCF_tree_file = "B:/ProjectSpace/hmm56/imaris_surfaces/data/templates/RCCF_tree-reduced.pkl"
    label_imaris_path = "B:/22.gaj.49/DMBA/Aligned-Data-0.3/Other/ims/labels/RCCF/DMBA_RCCF_labels.ims"
    RCCF_csv_file = "K:/workstation/static_data/atlas/symmetric15um/labels/RCCF/symmetric15um_RCCF_labels_lookup.txt"
    RCCF_label_colors = imsurf.read_csv_into_memory(RCCF_csv_file)

    # whole brain root. I believe this always stays the same
    root_structure_id = 997

    # launch imaris
    imaris_path = r"C:/Program Files/Bitplane/Imaris 10.2.0/Imaris.exe"
    xt_path = r"C:/Program Files/Bitplane/Imaris 10.2.0/XT/python3"

    if open_imaris:
        imaris_process = subprocess.Popen([imaris_path, "id101"])
        # give imaris enough time to open
        time.sleep(10)

    # TODO: maybe put this whole bundle of code into a module function. returns imaris_[lib,server,app]
    # setup imaris connection
    # these append statements are required to correctly find ImarisLib and all of its dependencies
    # this sys.path.append is the correct way to modify your PYTHONPATH variable
    workstation_imaris_path = "{}/code/shared/pipeline_utilities/imaris".format(os.environ["WORKSTATION_HOME"])
    sys.path.append(imaris_path.replace("/","\\"))
    sys.path.append(xt_path.replace("/","\\"))
    workstation_imaris_path = workstation_imaris_path.replace("/","\\")
    # insert at 0 to put it at front of search path.
    sys.path.insert(0, workstation_imaris_path)
    logger.debug("sys.path after modification: %s", sys.path)
    # only works python > 3.8
    # os.add_dll_directory(workstation_imaris_path)
    # os.add_dll_directory(xt_path)

    # must run this after modifying PYTHONPATH
    import ImarisLib

    imaris_lib = ImarisLib.ImarisLib()
    imaris_server = imaris_lib.GetServer()
    # previously v
    imaris_app = imaris_lib.GetApplication(101)
    factory = imaris_app.GetFactory()
    # load label file programmatically
    load_options = ""
    if open_imaris:
        imaris_app.FileOpen(label_imaris_path, load_options)
        time.sleep(10)
    # load only the label file so that this is unambiguous
    img = imaris_app.GetImage(0)

    logger.info("Attempting to open RCCF tree file: %s", RCCF_tree_file)
    with open(RCCF_tree_file, "rb") as f:
        RCCF_tree = pickle.load(f)

    root = RCCF_tree[root_structure_id]
    main_scene_parent = imaris_app.GetSurpassScene()

    left_container = None
    right_container = None

    if SPLIT_LEFT_RIGHT:
        container_base_name = root["structure_name"] if root else "RCCF_Split"

        left_container = factory.CreateDataContainer()
        left_container.SetName(f"{container_base_name} Left")
        main_scene_parent.AddChild(left_container, -1)
        logger.info("Created LEFT root container: %s", left_container.GetName())

        right_container = factory.CreateDataContainer()
        right_container.SetName(f"{container_base_name} Right")
        main_scene_parent.AddChild(right_container, -1)
        logger.info("Created RIGHT root container: %s", right_container.GetName())

    flat_traverse(root,
                  default_parent_group=main_scene_parent,
                  white_list=white_list,
                  left_right_split=SPLIT_LEFT_RIGHT,
                  left_container_for_split=left_container,
                  right_container_for_split=right_container)
