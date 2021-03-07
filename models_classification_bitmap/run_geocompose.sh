python run_glue.py \
--task_name geocompose \
--model_type bert \
--model_name_or_path bert-base-uncased \
--do_train \
--do_eval \
--do_relative \
--do_boundary \
--num_tiles 10 \
--num_links_topairs 6 \
--eval_all_checkpoints \
--data_dir ../geocode-data/collection_samples \
--n_labels 100 \
--learning_rate 5e-6 \
--num_train_epochs 100 \
--max_seq_length 400 \
--per_gpu_train_batch_size 8 \
--gradient_accumulation_steps 8 \
--save_steps 50 \
--output_dir output_bitmap_10_6_epoch100/
