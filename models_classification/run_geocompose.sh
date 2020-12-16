#!/bin/bash
# Your job will use 1 node, 28 cores, and 168gb of memory total.
#PBS -q standard
#PBS -l select=1:ncpus=28:mem=224gb:np100s=1:os7=True
### Specify a name for the job
#PBS -N text_on1
### Specify the group name
#PBS -W group_list=msurdeanu
### Used if job requires partial node only
#PBS -l place=pack:exclhost
### CPUtime required in hhh:mm:ss.
### Leading 0's can be omitted e.g 48:0:0 sets 48 hours
#PBS -l cput=140:00:00
### Walltime is how long your job will run
#PBS -l walltime=5:00:00
#PBS -e /home/u12/zeyuzhang/Multi_Model_QA/QA_image_augmentation/transformers_text_only/logs/error_epoch3
#PBS -o /home/u12/zeyuzhang/Multi_Model_QA/QA_image_augmentation/transformers_text_only/logs/output_epoch3

#####module load cuda80/neuralnet/6/6.0
#####module load cuda80/toolkit/8.0.61
module load singularity/3/3.6.4

cd $PBS_O_WORKDIR

singularity exec --nv /xdisk/bethard/mig2020/extra/zeyuzhang/image/hpc-ml_centos7-python37.sif python3.7 run_glue.py \
--task_name geocompose \
--model_type bert \
--model_name_or_path bert-base-uncased \
--do_train \
--do_eval \
--eval_all_checkpoints \
--data_dir ../geocode-data/collection_samples \
--n_labels 1 \
--learning_rate 5e-6 \
--num_train_epochs 50 \
--max_seq_length 400 \
--per_gpu_train_batch_size 8 \
--gradient_accumulation_steps 8 \
--save_steps 1000 \
--output_dir output_epoch50/
