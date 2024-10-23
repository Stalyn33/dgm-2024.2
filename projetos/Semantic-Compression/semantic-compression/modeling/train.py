import argparse
from tqdm.auto import tqdm
from gan import GCGAN
from keras.utils import image_dataset_from_directory
from keras import optimizers, losses
import numpy as np


def train(model, dataloader_train, dataloader_val, epochs, save_every, model_fname):
    gan_losses_train = []
    l2_losses_train = []
    gan_losses_val = []
    l2_losses_val = []
    pbar = tqdm(range(1, epochs+1))
    for epoch in pbar:
        gan_train, l2_train = model.train_step(dataloader_train)
        gan_val, l2_val = model.test_step(dataloader_val)
        gan_losses_train.append(gan_train)
        l2_losses_train.append(l2_train)
        gan_losses_val.append(gan_val)
        l2_losses_val.append(l2_val)
        if epoch % save_every == 0:
            model.save(f'../models/{model_fname}_{epoch}.keras')
            model.save_weights(f'../models/{model_fname}_{epoch}.weights.h5')
        pbar.set_description(f'train: ({tdl:.2f}; {tgl:.2f}); val: ({vdl:.2f}; {vgl:.2f})')
    return gan_losses_train, l2_losses_train, gan_losses_val, l2_losses_val


def main(path_train, path_val, H, W, filters, n_blocks, channels, momentum, batch_size, ae_lr, gan_lr, epochs, save_every):
    model_fname = f"{H:04d}{W:04d}{filters:03d}{n_blocks:02d}{channels:01d}{int(momentum*100):02d}{batch_size:03d}{int(ae_lr*1e5):05d}{int(gan_lr*1e5):05d}"

    train_set = image_dataset_from_directory(
        path_train, labels=None, batch_size=batch_size, image_size=(H, W), shuffle=True
    )
    val_set = image_dataset_from_directory(
        path_val, labels=None, batch_size=batch_size, image_size=(H, W), shuffle=True
    )
    
    gan = GCGAN(
        filters, n_blocks, channels, n_convs=4, sigma=1000, levels=5, l_min=-2, l_max=2, lambda_d=10, momentum=momentum,
    )
    gan.compile(
        optimizer_1=optimizers.Adam(learning_rate=ae_lr),
        optimizer_2=optimizers.Adam(learning_rate=gan_lr),
    )

    gan_losses_train, l2_losses_train, gan_losses_val, l2_losses_val = train(gan, train_set, val_set, epochs, save_every, model_fname)
    np.savetxt(f"../models/{model_fname}_losses.txt", np.array([gan_losses_train, l2_losses_train, gan_losses_val, l2_losses_val]))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Treinamento de Generative Compression GAN")

    parser.add_argument('--path_train', type=str, default='../data/train', help='Caminho para o dataset de treino')
    parser.add_argument('--path_val', type=str, default='../data/test', help='Caminho para o dataset de validação')
    parser.add_argument('--H', type=int, default=256, help='Altura das imagens')
    parser.add_argument('--W', type=int, default=512, help='Largura das imagens')
    parser.add_argument('--width', type=int, default=128, help='Número de filtros de largura do GAN')
    parser.add_argument('--depth', type=int, default=5, help='Número de blocos de profundidade do GAN')
    parser.add_argument('--batch_size', type=int, default=32, help='Tamanho do batch para treinamento')
    parser.add_argument('--d_lr', type=float, default=0.001, help='Taxa de aprendizado do discriminador')
    parser.add_argument('--g_lr', type=float, default=0.001, help='Taxa de aprendizado do gerador')
    parser.add_argument('--epochs', type=int, default=100, help='Número de épocas de treinamento')
    parser.add_argument('--save_every', type=int, default=100, help='Salvar pesos a cada número de épocas')

    args = parser.parse_args()

    path_train = args.path_train
    path_val = args.path_val
    H = args.H
    W = args.W
    width = args.width
    depth = args.depth
    batch_size = args.batch_size
    d_lr = args.d_lr
    g_lr = args.g_lr
    epochs = args.epochs
    save_every = args.save_every

    main(path_train, path_val, H, W, width, depth, batch_size, d_lr, g_lr, epochs, save_every)
