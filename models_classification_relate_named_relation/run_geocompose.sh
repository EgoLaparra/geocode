#!/bin/bash
# Your job will use 1 node, 28 cores, and 168gb of memory total.
#PBS -q standard
#PBS -l select=1:ncpus=28:mem=224gb:np100s=1:os7=True
### Specify a name for the job
#PBS -N rela_epo5
### Specify the group name
#PBS -W group_list=nlp
### Used if job requires partial node only
#PBS -l place=pack:exclhost
### CPUtime required in hhh:mm:ss.
### Leading 0's can be omitted e.g 48:0:0 sets 48 hours
#PBS -l cput=840:00:00
### Walltime is how long your job will run
#PBS -l walltime=30:00:00
#PBS -e /home/u12/zeyuzhang/Geo_Compositional/geocode/models_classification_relate_named_relation/logs/error_named_relation_epoch5
#PBS -o /home/u12/zeyuzhang/Geo_Compositional/geocode/models_classification_relate_named_relation/logs/output_named_relation_epoch5

#####module load cuda80/neuralnet/6/6.0
#####module load cuda80/toolkit/8.0.61
module load singularity/3/3.6.4

cd $PBS_O_WORKDIR

singularity exec --nv /xdisk/bethard/zeyuzhang/hpc-ml_centos7-python3.7-transformers2.11.sif python3.7 run_glue.py \
--task_name geocompose \
--model_type bert \
--model_name_or_path bert-base-uncased \
--do_train \
--do_eval \
--eval_all_checkpoints \
--data_dir /xdisk/bethard/zeyuzhang/Geo-Compositional_data/ \
--n_labels 8 \
--learning_rate 5e-6 \
--num_train_epochs 5 \
--max_seq_length 400 \
--per_gpu_train_batch_size 8 \
--gradient_accumulation_steps 8 \
--save_steps 200 \
--output_dir /xdisk/bethard/zeyuzhang/models_classification_relate_named_relation/output_epoch5/