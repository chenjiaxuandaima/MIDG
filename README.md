## Mask inpainting-based data generation architecture for surface defect images with complex backgrounds
[Paper](https://doi.org/10.1007/s11760-025-03987-y) | [BibTex](#citation)
### Introduction:
In the electronic manufacturing process, deep learning (DL)-based defect detection models often suffer from limited training defect datasets. To enhance training data, a novel mask inpainting-based data generation architecture (MIDG) is developed for surface defect images with complex backgrounds. It consists of a mask inpainting block, an edge generation block, followed by a defect generation module. The defect generation module is proposed based on an encoder-decoder model with an edge attention block, which hybridizes the information from inpainted normal images and edge maps simultaneously, where the first focuses on texture information and the second on edge structure, generated respectively from the mask inpainting and edge generation blocks. Besides, an annotation strategy is developed, which is at the rectangular mask level and can be easily executed. Experimental results demonstrate that our proposed method can generate various and high-quality defects on flexible printed circuit (FPC) surfaces with irregular circuit lines and copper-covered regions. After adding the generated samples to the training set, the mean Average Precision (mAP) of DL-based detection models such as Faster RCNN, YOLOv8, and YOLOv5 for FPC defect detection increases by 3.1%, 2.7%, and 3.0%, respectively. Detailed description can be found in our [paper](https://doi.org/10.1007/s11760-025-03987-y).

The architecture of our proposed method MIDG:
<p align='center'>  
  <img src='https://github.com/user-attachments/assets/6c4e08be-d3b6-464a-bf31-dd76a73ae305' width='870'/>
</p>



## Prerequisites
- Python 3
- PyTorch
- NVIDIA GPU + CUDA cuDNN
## Installation
- Clone this repo:
```bash
git clone https://github.com/chenjiaxuandaima/MIDG.git
cd MIDG
```
- Install PyTorch and dependencies from http://pytorch.org

The project is compatible with general versions, and the version used in our project is:
```bash
pytorch 1.7.1  py3.8_cuda11.0.221_cudnn8.0.5_0 tensorboard 2.12.1
```
- Install python requirements:
```bash
pip install -r requirements.txt
```
## Dataset
- Prepare the dataset in the following format:
```bash
dataset/kinds/defect_kind
  --images
     --train
     --test
  --mask
     --train
     --test
  --inpaint
     --train
     --test
```
The folder images contains defect images, mask contains binary images indicating defect locations, and inpaint contains inpainted defect-free images.
Defect-free images are obtained using the LaMa inpainting method. You can run the following code to generate them:
```bash
pip install iopaint
iopaint run --model=lama --device=cpu --image=dataset/kinds/defect_kind/images/train --mask=dataset/kinds/defect_kind/mask/train --output=dataset/kinds/defect_kind/inpaint/train
```
## Running
- Set file list of dataset:
```bash
python scripts/flist2.py --path ./dataset/
```
- Set the configuration file, refer to checkpoints/exposed_copper/config.yml
### Training
- Train the edge generation block:
```bash
python train.py --model 1 --checkpoints ./checkpoints/exposed_copper/
```
- Train the defect generation module:
```bash
python train.py --model 3 --checkpoints ./checkpoints/exposed_copper/
```
### Testing
- Generate defect edge:
```bash
python test.py --model 1 --checkpoints ./checkpoints/exposed_copper/
```
- Generate defect:
```bash
python test.py --model 3 --checkpoints ./checkpoints/exposed_copper/
```
### Evaluating
```bash
python ./scripts/metrics.py --data datasets/kind/exposed_copper/test --output ./checkpoints/exposed_copper/result
```
## Acknowledgments
- This project is developed based on the [EC](https://github.com/knazeri/edge-connect.git) and [LaMa](https://github.com/advimman/lama) projects. We sincerely appreciate their outstanding work.

- We also thank our lab for the support and welcome you to visit our [lab](https://github.com/luojxscut/LABCODE) to gain more industrial intelligence projects.
## Citation
- If you found our work helpful, please consider citing our papers <a href="https://doi.org/10.1007/s11760-025-03987-y">Mask inpainting-based data generation architecture for surface defect images with complex backgrounds</a> :

```
@InProceedings{Luo_2025_MIDG,
  title = {Mask inpainting-based data generation architecture for surface defect images with complex backgrounds},
  author = {Jiaxiang Luo,Jiaxuan Chen},
  journal= {Signal, Image and Video Processing},
  year = {2025},
  volume = {19},
  number = {5},
  pages = {405},
  DOI = {10.1007/s11760-025-03987-y},
  type = {Journal Article}
}
```
## Generation Results:
- This section showcases some generation results of the project.

Comparison with excellent image inpainting methods:
<p align='center'>  
  <img src='https://github.com/user-attachments/assets/f95abe12-9aa3-4239-a6aa-a177164ddd19' width='1070'/>
</p>


Display of various defect images generated by changing the position and size of the mask:

<p align='center'>  
  <img src='https://github.com/user-attachments/assets/73c58ac3-307e-4d86-986d-94bb9b5863c3' width='870'/>
</p>


Display of defect images with controllable shapes:

<p align='center'>  
  <img src='https://github.com/user-attachments/assets/d8092d0c-97db-4efc-b0c3-b9d84b6246c3' width='870'/>
</p>


Display of various defect images generated by our proposed method:

<p align='center'>  
  <img src='https://github.com/user-attachments/assets/614d2e95-51c2-4ac5-be0e-7e36dc73296c' width='870'/>
</p>


Generated images during the process of our method:

<p align='center'>  
  <img src='https://github.com/user-attachments/assets/b0d7ea2f-5325-422e-a719-0410d2fa81b8' width='670'/>
</p>


Display of various defect images generated by changing the position:

<p align='center'>  
  <img src='https://github.com/user-attachments/assets/79cadc09-daac-4618-9760-07bcd919042c' width='770'/>
</p>


