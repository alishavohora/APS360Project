# -*- coding: utf-8 -*-
"""DEMOLoadModel.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ULVYJepOQGYhj99AmxiCnq5zPS0TkvQ-
"""

import torch
import csv
import time
import torchtext
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import random
import matplotlib.pyplot as plt
from torch.nn.utils.rnn import pad_sequence
from google.colab import drive
from collections import defaultdict
drive.mount('/content/gdrive')


embeddingSize = 200

# #####  model architecture #####
class GenreRNN(nn.Module):
    def __init__(self, input_size=200, hidden_size=150, num_classes=5):
        super(GenreRNN, self).__init__()
        self.name = "GenreRNN"
        self.hidden_size = hidden_size
        self.num_classes = num_classes
        self.gru = nn.GRU(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)
    
    def forward(self, x):
        # Set an initial hidden state
        h0 = torch.zeros(1, x.size(0), self.hidden_size)
        #c0 = torch.zeros(1, x.size(0), self.hidden_size)
        # Forward propagate the RNN
        out, _ = self.gru(x, h0)
        # Pass the output of the last time step to the classifier
        out = self.fc(out[:, -1, :])
        return out

testRNN = GenreRNN()
state = torch.load("/content/gdrive/My Drive/Colab Notebooks/APS360/Project/GenreRNN, learning rate 0.0001, epoch14")
testRNN.load_state_dict(state)

import numpy as np

def loadGloveModel(File):
    print("Loading Glove Model")
    f = open(File,'r')
    gloveModel = defaultdict(lambda: torch.zeros(embeddingSize, dtype=torch.float64))
    for line in f:
        splitLines = line.split()
        word = splitLines[0]
        wordEmbedding = torch.from_numpy(np.array([float(value) for value in splitLines[1:]]))
        gloveModel[word] = wordEmbedding
    print(len(gloveModel)," words loaded")
    return gloveModel

model_path = "/content/gdrive/My Drive/Colab Notebooks/APS360/Project/200d.txt" #use 50d.txt, 100d.txt, 200d.txt for alt. dimensions
glove = loadGloveModel(model_path)

##### Helper functions used during training and validation #####

def toEmbedded (batch): 
  #converts a pytorch tensor batch embedded in our vocab embedding into a pytorch tensor batch embedded using glove

  count = 0
  dim1 = list(np.shape(batch)) [0]
  dim2 = list(np.shape(batch)) [1]
  embBatch = torch.empty(dim1, dim2, embeddingSize) #creating an empty tensor to recieve the new data
  for i, sample in enumerate (batch):
    for j, index in enumerate (sample):
      embBatch[i][j] = glove[text_field.vocab.itos[index]] #this line basically does the entire conversion
  return embBatch

def get_stats(model, data_loader, criterion, lossEnable = False): 
  #gets accuracy and loss (if lossenable is set to true manually)
  #returns it in a list with the form [loss, accuracy]

  correct, total, totalLoss, lossNums = 0, 0, 0, 0
  counter=0
  accuracy_test=0
  genre = ['horror', 'mystery', 'romance', 'fantasy', 'science fiction']

  for desc, labels in data_loader:
    counter+=1
    #converts data to glove embeddings and feeds into model
    embDesc = toEmbedded(desc[0])
    pred = model(embDesc)
    value, index=pred.max(1)
    prediction = genre[index]
    real = genre[labels]
    if (prediction == real):
      accuracy_test+=1
    print("Genre Prediction: " + prediction + " | " + "Genre Label: " + real)
    if (counter==20): break


  print("Accuracy: " + str((accuracy_test/20)*100))

##### Loading Data #####

text_field = torchtext.data.Field(sequential=True,      # text sequence
                                  tokenize=lambda x: x, # because are building a character-RNN
                                  include_lengths=True, # to track the length of sequences, for batching
                                  batch_first=True,
                                  use_vocab=True)       # to turn each character into an integer index
label_field = torchtext.data.Field(sequential=False,    # not a sequence
                                   use_vocab=False,     # don't need to track vocabulary
                                   is_target=True,      
                                   batch_first=True) # convert text to 0 and 1

path_tian = "/content/gdrive/My Drive/Colab Notebooks/APS360 Project"
path_alisha = "/content/drive/My Drive/4th year/APS360"
path_samin = "/content/gdrive/My Drive/Colab Notebooks/APS360/Project"

fields = [('label', label_field), ('desc', text_field)]

## if you're loading in test data
testDataSet = torchtext.data.TabularDataset(path_samin+ "/testCleanData.csv", # name of the file
                                       "csv",               # fields are separated by a comma
                                       fields)

##### prelim data formatting, creation of vocab and iterator objects #####

# splits the description property of the dataset into a list of words. Needed to build word based vocab. Otherwise vocab is built with just characters
# ex: "this is a description" => ["this", "is", "a", "description"]
genreDict = {'horror' : 0 , 'mystery' : 1, 'romance' : 2, 'fantasy' : 3, 'science fiction' : 4}

#final preprocessing on the testing data set
if (type(testDataSet[0].desc) is str):
  for i in range (0, len(testDataSet)):
    testDataSet[i].label = genreDict[testDataSet[i].label] #changes each label into a number - crossentropyloss doesn't take onehot, it takes index based
    testDataSet[i].desc = testDataSet[i].desc.split() #splitting words in descriptions into a list for build_vocab to work


#build a vocab (basically assign each word to an index)
text_field.build_vocab(testDataSet)

# bucketiterators created, needed to create batches that have similar lengths (minimize padding)
test_iter = torchtext.data.BucketIterator(testDataSet,
                                           batch_size=1,
                                           sort_key=lambda x: len(x.desc), # to minimize padding
                                           sort_within_batch=True,        # sort within each batch
                                           repeat=False)                  # repeat the iterator for many epochs

#get_stats(testRNN, data_loader=test_iter, criterion=nn.CrossEntropyLoss(), lossEnable = False): 
#testRNN.get_stats()
nn.CrossEntropyLoss()
get_stats(model=testRNN,data_loader=test_iter, criterion=nn.CrossEntropyLoss(), lossEnable = False)

