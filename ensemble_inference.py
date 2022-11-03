import os
import random
import pandas as pd
import numpy as np

import torch

import argparse
from omegaconf import OmegaConf
from dataloader.dataloader import DataLoader, ElectraDataLoader
from models.model import Model
from models.contrastive_model import ContrastiveLearnedElectraModel

import pytorch_lightning as pl




# set seed
def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)  # if use multi-GPU
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    pl.seed_everything(seed, workers=True)


def main(config):
    print("⚡ get DataLoader")
    dataloader = DataLoader(
        config.model.name,
        config.train.batch_size,
        config.data.shuffle,
        config.path.train_path,
        config.path.dev_path,
        config.path.test_path,
        config.path.predict_path,
    )

    print("⚡ get ElectraDataLoader")
    dataloader = ElectraDataLoader(
        config.model.name,
        config.train.batch_size,
        config.data.shuffle,
        config.path.train_path,
        config.path.dev_path,
        config.path.test_path,
        config.path.predict_path,
    )

    # print("⚡ get Model from checkpoint")

    print("⚡ get CLElectraModel from checkpoint")
    model = ContrastiveLearnedElectraModel.load_from_checkpoint(
        config.model.saved_contrastive_checkpoint + "/" + config.model.model_ckpt_path
    )

    print("⚡ get trainer")
    trainer = pl.Trainer(
        accelerator="gpu",
        devices=1,
        max_epochs=config.train.max_epoch,
        log_every_n_steps=1,
    )
    pred = trainer.predict(model=model, datamodule=dataloader)

    pred = list(round(float(i), 1) for i in torch.cat(pred))
    print(pred)
    
    # 여기서 단순히 pred = CL_pred1 * 0.5 + Electra_pred2 * 0.5

    # output = pd.read_csv("./data/submission_format.csv")
    # output["target"] = predictions
    # output.to_csv("output.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="ensemble_config")
    args, _ = parser.parse_known_args()
    config = OmegaConf.load(f"./configs/{args.config}.yaml")

    seed_everything(config.train.seed)

    main(config)
