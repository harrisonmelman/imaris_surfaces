# scratchpad for traversing the ROI "tree" in the RCCF_labels csv file

# this creates a pickled version of the tree for later use?

# check this out
# import seaborn
import sys
import logging
import pickle
# currently unused
# import treelib
# import csv

# put your internal imports last
from imaris_surface_helpers import read_csv_into_memory, safe_sort_field

# log
logging.basicConfig()
logging.root.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

# read in as a list of lists of strings

# the existing one in atlas folder had a problem. I made a copy and manually edited to keep working
# james has been notified of the LUT error

# RCCF_csv_file = "K:/workstation/static_data/atlas/symmetric15um/labels/RCCF/symmetric15um_RCCF_labels_lookup.txt"
# *_manual_fixed was fixed in notepad++. this was failed to read by the python script
# *AON_graph_index_fixed was editied in open office. This worked fine.
# RCCF_csv_file = "B:/ProjectSpace/hmm56/imaris_surfaces/symmetric15um_RCCF_labels_lookup_manual_fix.txt"
RCCF_csv_file = "B:/ProjectSpace/hmm56/imaris_surfaces/symmetric15um_RCCF_labels_lookup_AON_graph_index_fixed.csv"
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

    # TODO: these graph index assumptions are INCORRECT
    # the decimal place number can continue to increase as more layers cascade.
    # or... is it 156 is the parent
    # and then 156.x is the child. there can be more than one child branch...??? unsure.
    # these are the reasons to FULLY SKIP a region:
    # if is a left/right region (graph_index looks like x.1)
    # if it is an uncharted region (graph index looks like x.2)
    # if ROI_num is empty string (then this is a bogus row)
    # ALL LEAFS ARE ONE-SIDED, therefore they all will have a 0.1 on it bc all are L/R
    # want to ignore ones where not is integer AND ROI is nan
    # TODO: remove this filter for full functionality
    # initial test will ignore all L/R sides. all regions (except actual ROIs) will be bilateral.
    TESTING = True
    if TESTING:
        if not graph_index.is_integer() and ROI_num == "NaN" and (
            "_left" in structure_name or "_right" in structure_name):
            logging.info(
                "SKIP index {} because ROI_num is {}. structure_id: {}. name: {}".format(graph_index, ROI_num, row[17],
                                                                                         structure_name))
            continue

    # use structure_id (not name) to define the tree
    # this is NaN-safe casting. Will remain a string as NaN if that is what it is.
    # TODO: instead cast to float. float can handle nan value
    structure_id = row[17] if row[17] == "NaN" else int(row[17])
    parent_structure_id = row[18] if row[18] == "NaN" else int(row[18])

    red = int(row[2])
    green = int(row[3])
    blue = int(row[4])

    logging.info(
        "\nWORKING ON:\n\tgraph_index = {}\n\tROI_num = {}\n\tstructure_name = {}\n\tstructure_id = {}\n\tparent_structure_id = {}".format(
            graph_index, ROI_num, structure_name, structure_id, parent_structure_id))

    if parent_structure_id == "NaN":
        # then this is the root node. mark for later. This is where we start tree traversal later.
        root_structure = structure_id

    # TODO: if leaf node, then parent structure id gets ambiguous
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
        # if we are here, then we have an ROI
        # the L/R should be placed underneath the whole ROI folder
        # currently itis placed adjacent to it
        # this will probably break uncharted regions.
        # TODO: this is where my issue for NESTED Left then Right ROIs comes from
        # happens in the case where the FIRST entry in the csv with this ID was a bare ROI
        # this means its parent was not created. but right here I fully assume that the previously created one is CLEARLY the parent
        # this was bad assumption. unsure how to fix
        # need logic to determine if this structure ID actually has validity as a parent
        # if ROI is nan (of the PARENT STRUCTURE ID)
        if RCCF_tree[parent_structure_id]["ROI_num"] == "NaN":
            # then this structure can validly be a PARENT (a folder in Imaris)
            print("parent ROI is NaN")
            parent_structure_id = structure_id
        else:
            # otherwise, then go find the "grandparent" (truthfully, your already-correctly-sorted sibling's parent)
            # I'm going to kick myself for these shitty comments...
            parent_structure_id = RCCF_tree[parent_structure_id]["parent_structure_id"]
        structure_id = "{}-{}".format(structure_id, ROI_num)
        tree_node["structure_id"] = structure_id
        tree_node["parent_structure_id"] = parent_structure_id
        RCCF_tree[structure_id] = tree_node
        logging.info("adding new node to the tree: {}".format(structure_id))
        # logger.error("FOUND DUPLICATE STRUCTURE: {} {}".format(structure_id, structure_name))
        # break
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
        logger.warning(
            "cannot find the parent structure for {} -- parent={}\n\n".format(structure_id, parent_structure_id))

out_file = "B:/ProjectSpace/hmm56/imaris_surfaces/RCCF_tree.pkl"
with open(out_file, 'wb') as f:
    print("DUMP MY PICKLE")
    pickle.dump(RCCF_tree, f, pickle.HIGHEST_PROTOCOL)
    print("finished dump")

from pprint import pprint

pprint(RCCF_tree)

# container = factory.CreateDataContainer()
# container.SetName(structure_name)
# this is what to do if the folder is at the root. -1 means place it at the bottom of the list
# -1 also means it can be indexed by scene.GetChild[-1]x
# scene.AddChild(container, -1)
# what to do if i wanna make a subfolder?
