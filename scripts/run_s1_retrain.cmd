@echo off
cd /d "C:\Users\lovilocal.adm\Desktop\Claude Projects\KHANYA"
set KHANYA_SUBSET=S1
set KHANYA_PATCHES_PER_EPOCH=128
set KHANYA_VAL_PATCHES=48
set KHANYA_EPOCHS=20
.venv\Scripts\python.exe -u -m src.segmentation.train_patches >> s1_retrain.log 2>&1
