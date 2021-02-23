import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import PIL
from sklearn.preprocessing import LabelEncoder
import torch
import torch.nn.functional as F
import torchvision
from torchvision import transforms
from torch.utils.data.dataset import Dataset
from torch.utils.data import DataLoader
from CustomisedResnet18 import CustomizedResNet18
from SimpleNN import  SimpleNN
from DogBreed import DogBreed

batch_size = 4
device = torch.device('cuda')


class TestDataset(Dataset):
    def __init__(self, dataframe, transform=None):
        self.dataframe = dataframe
        self.transform = transform

    def __getitem__(self, index):
        return self.transform(self.dataframe.iloc[index, 0])

    def __len__(self):
        return self.dataframe.shape[0]


resNettf = transforms.Compose([
    lambda x: PIL.Image.open(x).convert('RGB'),  # string path= > image data
    transforms.Resize((int(224 * 1.25), int(224 * 1.25))),
    transforms.RandomRotation(15),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

simpleNNtf = transform = transforms.Compose([
            lambda x: PIL.Image.open(x).convert('L'),  # string path= > image data
            transforms.Resize((int(128 * 1.25), int(128 * 1.25))),
            transforms.RandomRotation(15),
            transforms.CenterCrop(128),
            transforms.ToTensor(),
        ])


test_df = pd.read_csv('./sample_submission.csv')
test_dir = '../test'
test_df = test_df[['id']]
test_df.id = test_df.id.apply(lambda x: x+'.jpg')
test_df.id = test_df.id.apply(lambda x: test_dir+'/'+x)
test_set = TestDataset(test_df, transform=simpleNNtf)
test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False)


# model = CustomizedResNet18(120).to(device)
model = SimpleNN().to(device)
model.load_state_dict(torch.load("simpleNN-best.mdl"))
predictions = torch.tensor([])
for x in test_loader:
    if torch.cuda.is_available():
        x = x.to(device)
        x = x.view(x.size(0), -1)
        y_hat = model(x)
        predictions = torch.cat([predictions, y_hat.cpu()])
train_db = DogBreed("../", 224, mode='train')
predictions = F.softmax(predictions,dim=1).detach().numpy()
result_id = pd.read_csv('./sample_submission.csv').id.tolist()
predictions_df = pd.DataFrame(predictions, index=result_id)
predictions_df.columns = predictions_df.columns.map(train_db.dog_breed_dic)
predictions_df.rename_axis('id', inplace=True)
predictions_df.to_csv('submission.csv')