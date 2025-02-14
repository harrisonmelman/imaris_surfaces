# the RCCF tree has many dead ends
# this is where there is a branch that doesnot eventually have a root node

# root node is defined as having :
    # no children (node["children"] == [])
    # node["ROI_num"] != NaN

# currently, the code creates all folders, and if there is no root node ROI, then some folders end up empty, or with
# nested folders of folders, with no real objects inside
import pickle


def check_if_dead_end(node, parent):
    # node is who am I
    # parent is where did I come from
    pass


def prune_tree(tree, root_key):
    root = tree[root_key]
    pass


root_structure_id = 997
in_file = "B:/ProjectSpace/hmm56/imaris_surfaces/data/templates/RCCF_tree.pkl"
out_file = "B:/ProjectSpace/hmm56/imaris_surfaces/data/templates/RCCF_tree-pruned.pkl"


with open(in_file, "rb") as f:
    RCCF_tree = pickle.load(f)
    root = RCCF_tree[root_structure_id]
    # the parent of the root node is the root of the imaris filesystem
    prune_tree(RCCF_tree, root)
