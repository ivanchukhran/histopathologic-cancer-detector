import datetime
import os

import matplotlib.pyplot as plt
import torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader, random_split
from torchvision.transforms import transforms

from dataset import HistopathologicDataset
from models import ConvNet, train, SimpleConv, CD2Conv, init_weight
from utils import fetch_json, save_json


def main() -> None:
    TRAIN_BATCH_SIZE = 64
    VALIDATION_BATCH_SIZE = 512

    # Set only if you don't have memory enough to work with the batch
    torch.cuda.set_per_process_memory_fraction(0.5, 0)

    transform = transforms.Compose([
        transforms.CenterCrop(64),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    ds = HistopathologicDataset('train', 'processed_labels.csv', transform)
    train_size = int(0.9 * len(ds))
    validation_size = len(ds) - train_size
    train_ds, validation_ds = random_split(ds, [train_size, validation_size])

    train_dl = DataLoader(train_ds,
                          batch_size=TRAIN_BATCH_SIZE,
                          shuffle=True)
    validation_dl = DataLoader(validation_ds,
                               batch_size=VALIDATION_BATCH_SIZE,
                               shuffle=True)
    dataloaders = {
        'train': train_dl,
        'validation': validation_dl
    }

    models = [ConvNet((64, 64))]
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    criterion = nn.BCEWithLogitsLoss()
    results_dir = 'result/64/stats_on_2_dropout_100_epochs.json'
    if not os.path.exists(results_dir):
        if not os.path.exists('result/64'):
            os.mkdir('result/64')
        save_json({}, results_dir)
    for model in models:

        model = model.to(device)
        model.apply(init_weight)
        optimizer = Adam(model.parameters(), lr=1e-4)
        _stats = {
            'train': {
                'loss': [],
                'accuracy': []
            },
            'validation': {
                'loss': [],
                'accuracy': []
            }
        }
        model_name = model.__class__.__name__
        print(f"Training model: {model_name}")
        train(model, dataloaders, criterion, optimizer, epochs=100, stats=_stats, device=device)
        print("loading previous training results...")
        all_stats = fetch_json(results_dir)
        all_stats[model_name] = _stats
        print("saving current training results...")
        save_json(all_stats, results_dir)


def show_stats(statistics: dict):
    for model in statistics.keys():
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
        ax1.plot(statistics[model]['train']['loss'], label='train')
        ax1.plot(statistics[model]['validation']['loss'], label='validation')
        ax2.plot(statistics[model]['train']['accuracy'], label='train')
        ax2.plot(statistics[model]['validation']['accuracy'], label='validation')
        ax1.set_title('Loss')
        ax2.set_title('Accuracy')
        plt.title(model)
        plt.legend()
        plt.show()
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2, figsize=(10, 10))
    for model in statistics.keys():
        ax1.plot(statistics[model]['train']['loss'], label=model)
        ax2.plot(statistics[model]['train']['accuracy'], label=model)
        ax3.plot(statistics[model]['validation']['loss'], label=model)
        ax4.plot(statistics[model]['validation']['accuracy'], label=model)
    ax1.set_title('Train Loss')
    ax2.set_title('Train accuracy')
    ax3.set_title('Validation Loss')
    ax4.set_title("Validation accuracy")
    plt.legend()
    plt.show()


if __name__ == '__main__':
    main()
    stats = fetch_json('result/64/stats_on_2_dropout_100_epochs.json')
    show_stats(stats)
