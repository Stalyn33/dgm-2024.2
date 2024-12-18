from typing import Any
import torch
import torch.nn as nn

class Regularizer:
    def __init__(self, regularization_type):
        self.L1norm = None
        self.L2norm = None
        if regularization_type is not None:
            if not isinstance(regularization_type, list):
                self.regularization_type = [regularization_type]
            else:
                self.regularization_type = regularization_type
                
            for reg in self.regularization_type:
                if 'MAE' in reg:
                    self.L1norm = nn.L1Loss()
                elif 'MSE' in reg:
                    self.L2norm = nn.MSELoss()
        else:
            self.regularization_type = None
        
    def __call__(self, regularization_level, input_mask, input_img, gen_img, device):
        if self.regularization_type is not None:
            if not isinstance(regularization_level, list):
                regularization_level = [regularization_level]

            regularization = torch.tensor(0,dtype=torch.float32).to(device)
            for idx,reg in enumerate(self.regularization_type):
                if reg == 'MAE':
                    regularization += regularization_level[idx]*self.L1norm(gen_img,input_img)
                elif reg == 'MSE':
                    regularization += regularization_level[idx]*self.L2norm(gen_img,input_img)
                elif reg == 'MAE_mask':
                    regularization += regularization_level[idx]*self.L1norm(input_mask*gen_img,input_mask*input_img)
                elif reg == 'MSE_mask':
                    regularization += regularization_level[idx]*self.L2norm(input_mask*gen_img,input_mask*input_img)
                elif reg == 'MAE_outside_mask':
                    regularization += regularization_level[idx]*self.L1norm((1-input_mask)*gen_img,(1-input_mask)*input_img)
                elif reg == 'MSE_outside_mask':
                    regularization += regularization_level[idx]*self.L2norm((1-input_mask)*gen_img,(1-input_mask)*input_img)
                else:
                    raise ValueError(f"Invalid regularizer_type: {reg}, check losses.py and add the desired regularization.")
            return regularization
        else:
            return torch.tensor(0)


def get_disc_loss(gen, disc, criterion, input_mask, input_img):
    gen_img = gen(input_mask).detach()
    ans_gen = disc(input_mask,gen_img)
    gt_gen = torch.zeros_like(ans_gen)
    ans_real = disc(input_mask,input_img)
    gt_real = torch.ones_like(ans_real)
    ##old implementation
    # Concatenando os vetores do output do discriminador das reais com as geradas
    #x = torch.cat((ans_real.reshape(-1), ans_gen.reshape(-1)))
    # Concatenando os vetores dos labels reais das images reais com as geradas
    #y = torch.cat((gt_real.reshape(-1), gt_gen.reshape(-1)))
    #loss = criterion(x, y)

    loss_fake = criterion(ans_gen,gt_gen)
    loss_real = criterion(ans_real,gt_real)
    loss = (loss_fake+loss_real)*0.5
    # The regularization (l1 norm) is not important here: is independent of D
    return loss


def get_gen_loss(gen, disc, criterion, input_mask, input_img, device, regularizer=None, regularization_level=None):
    gen_img = gen(input_mask)
    ans_gen = disc(input_mask,gen_img)
    # we want ans_gen close to 1: to trick the disc
    gt_gen = torch.ones_like(ans_gen)
    loss = criterion(ans_gen, gt_gen).mean()
    if regularizer is not None:
        regularization = regularizer(regularization_level=regularization_level, input_mask=input_mask, 
                                     input_img=input_img, gen_img=gen_img, device=device)
        loss += regularization
    return loss
