# how to run the NeuronCounting pipeline
# allows you to run this code from anywhere and the internal relative paths still work fine
cd "$(dirname ${BASH_SOURCE[0]})" || exit;
# first, run the environment setup script. This makes sure that the shell and python all know where imaris etc are
bash environment_setup.bash


# input arguments
label_imaris_path="B:/22.gaj.49/DMBA/ims/labels/RCCF/DMBA_RCCF_labels.ims";
label_nhdr_path="B:/22.gaj.49/DMBA/Aligned-Data-RAS/labels/RCCF/DMBA_RCCF_labels.nhdr";
image_imaris_path="B:/22.gaj.49/DMBA/ims/LSFM/201026-1_1_PV.ims";
work_dir="B:/ProjectSpace/hmm56/NeuronCounting_test/201026-1_1_PV"

# your regions dict should have the same basename as your imaris file ${specid}_${contrast}.ims vs ${specid}_${contrast}.json
# and it should be in the ${NEURON_COUNTING_CODE_FOLDER}/region_dictionaries folder
# TODO: maybe move this logic of finding json to MainAlgor main function, user can optionally override it with an input argument (just like how work_dir is handled)
temp=$(basename ${image_imaris_path});
temp=${temp%%.ims};
regions_dict_path="../region_dictionaries/${temp}.json";

# work_dir is set by default to ${ims_dir}/NeuronCounting/${specimen_id}/${contrast}
# this only works for specimen ims files that are named like ${ims_dir}/${specimen_id}_${contrast}.ims
# script will create new subfolders within work_dir, one for each ROI to process.
# this will be overridden if you provide 4 arguments
python "prototype_make_label_surfaces.py"

# this one will infer the output directory and create it (creates a subdirectory wherever your ims file is)
#python "../MainAlgor - multiRegions.py" ${label_imaris_path} ${label_nhdr_path} ${image_imaris_path} ${regions_dict_path}
