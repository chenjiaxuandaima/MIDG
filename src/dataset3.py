import os
import glob

import cv2
import scipy
import torch
import random
import numpy as np
import torchvision.transforms.functional as F
from torch.utils.data import DataLoader
from PIL import Image
# from scipy.misc import imread
import imageio
from skimage.transform import resize
from skimage.feature import canny
from skimage.color import rgb2gray, gray2rgb
from .utils import create_mask
from torchvision import transforms


class Dataset(torch.utils.data.Dataset):
    def __init__(self, config, flist, inpaint_flist, edge_flist, mask_flist, augment=True, training=True):
        super(Dataset, self).__init__()
        self.augment = augment
        self.training = training
        self.data = self.load_flist(flist)
        self.edge_data = self.load_flist(edge_flist)
        self.mask_data = self.load_flist(mask_flist)
        self.inpaint_data = self.load_flist(inpaint_flist)


        self.input_size = config.INPUT_SIZE
        self.sigma = config.SIGMA
        self.edge = config.EDGE
        self.mask = config.MASK
        self.nms = config.NMS

        # in test mode, there's a one-to-one relationship between mask and image
        # masks are loaded non random
        if config.MODE == 2:
            self.mask = 6

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        try:
            item = self.load_item(index)
        except:
            print('loading error: ' + self.data[index])
            item = self.load_item(0)

        return item

    def load_name(self, index):
        name = self.data[index]
        return os.path.basename(name)

    def load_item(self, index):

        size = self.input_size

        # load image
        # img = imread(self.data[index])
        img = imageio.imread(self.data[index])
        inpaint_img = imageio.imread(self.inpaint_data[index])

        # gray to rgb
        if len(img.shape) < 3:
            img = gray2rgb(img)
            inpaint_img=gray2rgb(inpaint_img)
        # resize/crop if needed
        if size != 0:
            img = self.resize(img, size, size)
            inpaint_img= self.resize(inpaint_img, size, size)

        # create grayscale image
        img_gray = rgb2gray(img)

        # load mask
        mask,masks_noi = self.load_mask(img, index)

        # load edge
        edge = self.load_edge(img_gray, index, mask)

        # augment data
        if self.augment and np.random.binomial(1, 0.5) > 0:
            img = img[:, ::-1, ...]
            inpaint_img=inpaint_img[:, ::-1, ...]
            img_gray = img_gray[:, ::-1, ...]
            edge = edge[:, ::-1, ...]
            mask = mask[:, ::-1, ...]

        if self.training:
            img_tensor = self.to_tensor(img)
            inpaintimg_tensor=self.to_tensor(inpaint_img)
            imggray_tensor = self.to_tensor(img_gray)
            edge_tensor = self.to_tensor(edge)
            mask_tensor = self.maskto_tensor(mask)
            mask_tensor2 = self.maskto_tensor(masks_noi)

        else:
            inpaintimg_tensor = self.maskto_tensor(inpaint_img)
            img_tensor = self.maskto_tensor(img)
            imggray_tensor = self.maskto_tensor(img_gray)
            edge_tensor = self.maskto_tensor(edge)
            mask_tensor = self.maskto_tensor(mask)
            mask_tensor2 = self.maskto_tensor(masks_noi)
        return img_tensor, imggray_tensor, edge_tensor, mask_tensor,inpaintimg_tensor,mask_tensor2

    def load_edge(self, img, index, mask):
        sigma = self.sigma

        # in test mode images are masked (with masked regions),
        # using 'mask' parameter prevents canny to detect edges for the masked regions
        mask = None if self.training else (1 - mask / 255).astype(bool)

        # canny
        if self.edge == 1:
            # no edge
            if sigma == -1:
                return np.zeros(img.shape).astype(np.float64)

            # random sigma
            if sigma == 0:
                sigma = random.randint(1, 4)

            return canny(img, sigma=sigma, mask=mask).astype(np.float64)

        # external
        else:
            imgh, imgw = img.shape[0:2]
            # edge = imread(self.edge_data[index])
            edge = imageio.imread(self.edge_data[index])
            edge = self.resize(edge, imgh, imgw)

            # non-max suppression
            if self.nms == 1:
                edge = edge * canny(img, sigma=sigma, mask=mask)

            return edge

    def load_mask(self, img, index):
        imgh, imgw = img.shape[0:2]
        mask_type = self.mask

        # external + random block
        if mask_type == 4:
            mask_type = 1 if np.random.binomial(1, 0.5) == 1 else 3

        # external + random block + half
        elif mask_type == 5:
            mask_type = np.random.randint(1, 4)

        # random block
        if mask_type == 1:
            return create_mask(imgw, imgh, imgw // 2, imgh // 2)

        # half
        if mask_type == 2:
            # randomly choose right or left
            return create_mask(imgw, imgh, imgw // 2, imgh, 0 if random.random() < 0.5 else imgw // 2, 0)

        # external
        if mask_type == 3:
            mask_index = random.randint(0, len(self.mask_data) - 1)
            # mask = imread(self.mask_data[mask_index])
            mask = imageio.imread(self.mask_data[mask_index])
            mask = self.resize(mask, imgh, imgw)
            mask = (mask > 0).astype(np.uint8) * 255       # threshold due to interpolation
            return mask

        # test mode: load mask non random
        if mask_type == 6:
            # mask = imread(self.mask_data[index])
            mask = imageio.imread(self.mask_data[index])
            mask = self.resize(mask, imgh, imgw, centerCrop=False)
            # mask = rgb2gray(mask)
            mask = (mask > 0).astype(np.uint8) * 255
            # 二值化处理
            _, binary_image = cv2.threshold(mask, 128, 255, cv2.THRESH_BINARY)

            # 查找轮廓
            contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 遍历每个轮廓
            for contour in contours:
                # 计算轮廓的边界框（假设它是矩形）
                x, y, w, h = cv2.boundingRect(contour)

                # 生成噪声
                noise = np.random.randint(0, 256, (h, w), dtype=np.uint8)

                # 将矩形区域内的像素替换为噪声
                binary_image[y:y + h, x:x + w] = noise

                # 保存修改后的图像
            # cv2.imwrite('modified_image_with_noise.png', binary_image)
            return mask,binary_image

    # def to_tensor(self, img):
    #     img = Image.fromarray(img)
    #     img_t = F.to_tensor(img).float()
    #     return img_t

    def maskto_tensor(self, img):

        img = Image.fromarray(img)
        img_t = F.to_tensor(img).float()
        return img_t

    def maskto_tensor1(self, img):

        img = Image.fromarray(np.uint8(img))
        img_t = F.to_tensor(img).float()
        return img_t

    def to_tensor(self, img):
        # print(type(img))
        # imageio.imwrite('./checkpoints/results/fpc5train1.png', img)
        img = Image.fromarray(np.uint8(img*255))

        loader = transforms.Compose([transforms.ToTensor()])
        # image = loader(img).unsqueeze(0)
        # return image.to(self.device, torch.float)
        # img = Image.fromarray(np.uint8(img))
        # img.save('./checkpoints/results/fpc5test.png')
        # img = img[:, :, ::-1].copy()
        img_t = loader(img)
        # print(img.size)
        # unloader = transforms.ToPILImage()
        # # dir = 'results'
        # image = img_t.cpu().clone()  # we clone the tensor to not do changes on it
        # # image = image.squeeze(0)  # remove the fake batch dimension
        # # print(self.to_tensor(img).shape)
        # image = unloader(image)
        # # if not osp.exists(dir):
        # #     os.makedirs(dir)
        # image.save('./checkpoints/results/fpc5train.png')

        return img_t

    # def resize(self, img, height, width, centerCrop=True):
    #     imgh, imgw = img.shape[0:2]
    #
    #     if centerCrop and imgh != imgw:
    #         # center crop
    #         side = np.minimum(imgh, imgw)
    #         j = (imgh - side) // 2
    #         i = (imgw - side) // 2
    #         img = img[j:j + side, i:i + side, ...]
    #
    #     img = scipy.misc.imresize(img, [height, width])
    #
    #     return img

    def resize(self, img, height, width, centerCrop=True):
        imgh, imgw = img.shape[0:2]

        if centerCrop and imgh != imgw:
            # center crop
            side = np.minimum(imgh, imgw)
            j = (imgh - side) // 2
            i = (imgw - side) // 2
            img = img[j:j + side, i:i + side, ...]

        img = resize(img, [height, width])
        return img

    def load_flist(self, flist):
        if isinstance(flist, list):
            return flist

        # flist: image file path, image directory path, text file flist path
        if isinstance(flist, str):
            if os.path.isdir(flist):
                flist = list(glob.glob(flist + '/*.jpg')) + list(glob.glob(flist + '/*.png'))
                flist.sort()
                return flist

            if os.path.isfile(flist):
                try:
                    return np.genfromtxt(flist, dtype=np.str_, encoding='utf-8')
                except:
                    return [flist]

        return []

    def create_iterator(self, batch_size):
        while True:
            sample_loader = DataLoader(
                dataset=self,
                batch_size=batch_size,
                drop_last=True
            )

            for item in sample_loader:
                yield item



