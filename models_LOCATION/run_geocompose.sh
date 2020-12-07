python run_glue.py \
--task_name geocompose \
--model_type bert \
--model_name_or_path bert-base-uncased \
--do_train \
--do_eval \
--eval_all_checkpoints \
--data_dir /home/zeyuzhang/PycharmProjects/Geo_Compositional/geocode-data/collection_samples \
--n_labels 1 \
--learning_rate 5e-5 \
--num_train_epochs 300 \
--max_seq_length 400 \
--per_gpu_train_batch_size 8 \
--gradient_accumulation_steps 8 \
--save_steps 1000 \
--output_dir output_epoch300_5e5_LOCATION/
