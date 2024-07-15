# scratchpad for traversing the ROI "tree" in the RCCF_labels csv file

# check this out
# import seaborn
import sys
import treelib
#from prototype_make_label_surfaces import read_csv_into_memory
import logging
import csv
import pickle

"""
# this bits just copy pasted from make_label_surfaces as a helpful reference
sys.path.append(r'C:\Program Files\Bitplane\Imaris 9.9.0\XT\python3'.replace(r'\\', '/'))
sys.path.insert(0, 'k:/workstation/code/shared/pipeline_utilities/imaris')
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
"""


# gives me nice numerical sorting when my inputs are strings
# helps handle NaN and empty string and other non numerical issues
def safe_sort_field(x):
    if len(x) == 0:
        return -1
    return float(x)


# copied because my import statement keeps failing.
# i think it is an issue with pycharm setup.
def read_csv_into_memory(csv_file):
    with open(csv_file, mode="r") as f:
        csv_reader = csv.reader(f, delimiter="\t")
        data = [row for row in csv_reader]
    return data


# log
logging.basicConfig()
logging.root.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

# read in as a list of lists of strings

RCCF_csv_file = "K:/workstation/static_data/atlas/symmetric15um/labels/RCCF/symmetric15um_RCCF_labels_lookup.txt"
RCCF_data = read_csv_into_memory(RCCF_csv_file)
# TODO: automatically find the first rows of the LUT. james has a tool for this
# currently, row 27 (0 index) is the first "old style" header line
# exterior, ROI = 0 is found at RCCF_data[30]. The useful header is at 27.
header = RCCF_data[27]
RCCF_data = RCCF_data[30:None]

print(header)

# sort data on graph_index (it is read in as a string. must cast first)
# casting empty string to float raises exceptions
# graph index is always positive. if it is empty, then replace it with -1
# i will have to know to look out for -1 instead of empty when I filter later on
# NaN is also a possible value. set NaN ones to -2
# RCCF_data.sort(key=lambda x: x[29])
# this still gives error casting "" to float. unsure why, but it works within a non-anonymous function
# RCCF_data.sort(key=lambda x: -1 if len(x) == 0 else float(x[29]))
RCCF_data.sort(key=lambda x: safe_sort_field(x[29]))

# this will be the hierarchical RCCF structure
# after I have the tree fully built, then START AT ROOT NODE
# create a recursive function. loop through all children in the root node and recall
# if a node has no children, then it is a root node and I need to create the actual structure surface
    # all children that are not leaves, will become groups (folders)
    # unsure what is the correct order of operations of when to create/ add things to folders
RCCF_tree = {}
# to know where to start the tree traversal later. This structure will not have any parent.
root_structure = 0

for row in RCCF_data:
    ROI_num = row[0]
    structure_name = row[1]
    graph_index = row[29]

    # sometimes, graph index is NaN. filter for that.
    if graph_index == "NaN" or len(graph_index) == 0:
        continue

    # cast it to float now that it is safe to do so.
    # this is field used to sort, and to filter out L/R regions
    graph_index = float(graph_index)

    # TODO: remove this filter for full functionality
    # initial test will ignore all L/R sides. all regions (except actual ROIs) will be bilateral.
    TESTING = True
    if TESTING:
        if not graph_index.is_integer() and ROI_num == "NaN":
            continue

    # these are the reasons to FULLY SKIP a region:
        # if is a left/right region (graph_index looks like x.1)
        # if it is an uncharted region (graph index looks like x.2)
        # if ROI_num is empty string (then this is a bogus row)
    # TODO: this is too strict of a filter
    # ALL LEAFS ARE ONE-SIDED, therefore they all will have a 0.1 on it bc all are L/R
    # want to ignore ones where not is integer AND ROI is nan
    if not graph_index.is_integer() and ROI_num == "NaN":
        logging.info("SKIP index {} because ROI_num is {}".format(graph_index, ROI_num))
        continue

    # use structure_id (not name) to define the tree
    # this is NaN-safe casting. Will remain a string as NaN if that is what it is.
    structure_id = row[17] if row[17] == "NaN" else int(row[17])
    parent_structure_id = row[18] if row[18] == "NaN" else int(row[18])

    red = int(row[2])
    green = int(row[3])
    blue = int(row[4])

    logging.info("\nWORKING ON:\n\tgraph_index = {}\n\tROI_num = {}\n\tstructure_name = {}\n\tstructure_id = {}\n\tparent_structure_id = {}".format(graph_index, ROI_num, structure_name, structure_id, parent_structure_id))

    if parent_structure_id == "NaN":
        # then this is the root node. mark for later. This is where we start tree traversal later.
        root_structure = structure_id

    # TODO: this should be a class?
    # one class for Tree, which is a dict of TreeNodes (which themselves are dict)
    # one class for TreeNode, which is a dict
    # TODO: populate the children field
        # do this every time I get a new node
        # search for the parent structure in the tree
        # if it already exists, then add current node as a child
        # if it does not exist, then we have issues??
    # TODO: I will know if an roi is a LEAF if it has an integer for ROI_num (parent fields have ROI_num="NaN")
    tree_node = {"ROI_num": ROI_num,
                 "structure_id": structure_id,
                 "parent_structure_id": parent_structure_id,
                 "children": [],
                 "graph_index": graph_index,
                 "structure_name": structure_name,
                 "red": red,
                 "green": green,
                 "blue": blue
                 }
    # this check is not necessary because already filtered L/R and uncharted regions out above
    if structure_id not in RCCF_tree:
        RCCF_tree[structure_id] = tree_node
        logging.info("adding new node to the tree: {}".format(structure_id))
    # TODO: IDK what to do with this yet. currently I ignore L/R structures. This is NOT OKAY.
    # structure ID is NOT a unique ID. struct, struct_L, and struct_R will all have the same structure_id
    # that's OK... idea:
        # IF the current region has a (non-NaN) value for ROI_num, then it is an actual region
        # this means it is a leaf node and will not have any children! this is great because we won't need to refer back to it
        # let it's "structure_id" value be "structure_id-ROI_num"
    else:
        if ROI_num == "NaN":
            continue
        structure_id = "{}-{}".format(structure_id, ROI_num)
        RCCF_tree[structure_id] = tree_node
        logging.info("adding new node to the tree: {}".format(structure_id))
        #logger.error("FOUND DUPLICATE STRUCTURE: {} {}".format(structure_id, structure_name))
        #break
    if parent_structure_id in RCCF_tree:
        # then add this node to the "children" list of its parent
        # then child node already has a reference to its parent
        RCCF_tree[parent_structure_id]["children"].append(structure_id)
        logging.info("adding child {} to parent {}\n\n".format(structure_id, parent_structure_id))
    elif parent_structure_id == "NaN":
        # then this node is the whole brain ROOT. no work to do.
        logging.info("returned to the root. continuing on to the next root child structure")
        continue
    else:
        logger.warning("cannot find the parent structure for {} -- parent={}\n\n".format(structure_id, parent_structure_id))

out_file = "B:/ProjectSpace/hmm56/imaris_surfaces/RCCF_tree.pkl"
with open(out_file, 'wb') as f:
    pickle.dump(RCCF_tree, f)

from pprint import pprint
pprint(RCCF_tree)


#container = factory.CreateDataContainer()
#container.SetName(structure_name)
# this is what to do if the folder is at the root. -1 means place it at the bottom of the list
# -1 also means it can be indexed by scene.GetChild[-1]x
#scene.AddChild(container, -1)
# what to do if i wanna make a subfolder?

