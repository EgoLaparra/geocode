#!/bin/bash
# Your job will use 1 node, 28 cores, and 168gb of memory total.
#PBS -q standard
#PBS -l select=1:ncpus=16:mem=62gb:pcmem=4gb
### Specify a name for the job
#PBS -N 10_large_train
### Specify the group name
#PBS -W group_list=nlp
### Used if job requires partial node only
#PBS -l place=pack:exclhost
### CPUtime required in hhh:mm:ss.
### Leading 0's can be omitted e.g 48:0:0 sets 48 hours
#PBS -l cput=980:00:00
### Walltime is how long your job will run
#PBS -l walltime=35:00:00
#PBS -e /home/u12/zeyuzhang/Geo_Compositional/geocode/utils/logs/error_boundary_10_large_train
#PBS -o /home/u12/zeyuzhang/Geo_Compositional/geocode/utils/logs/output_boundary_10_large_train

module load singularity

cd $PBS_O_WORKDIR

singularity exec --nv /xdisk/bethard/hpc-ml_centos7-python3.7-transformers3.2.0.sif python3.7 get_simplify_shapes_classification_relative_boundary_large.py \
--xml_filepath_train ../../geocode-data/collection_samples/train_samples_large.xml \
--output_target_train ../../geocode-data/collection_samples/model_input_target_classification_relative_boundary_10_large_train.pkl \
--output_paras_train ../../geocode-data/collection_samples/model_input_paras_classification_relative_boundary_10_large_train.pkl \
--output_desc_train ../../geocode-data/collection_samples/model_input_desc_classification_relative_boundary_10_large_train.pkl \
--output_boundary_train ../../geocode-data/collection_samples/model_input_boundary_classification_relative_boundary_10_large_train.pkl \
--polygon_size 10
