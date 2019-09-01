import pandas as pd
import numpy as np
import sys
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import pairwise_distances

import os
clear = lambda: os.system('cls')
clear()

print("\n3. FILTRO COLABORATIVO\n")

path="ml-latest-small"

movies = pd.read_csv(path+'/moviesES.csv', sep=',', encoding='latin-1', usecols=['movieId', 'title', 'genres'])
ratings = pd.read_csv(path+'/ratings.csv', sep=',', encoding='latin-1', usecols=['userId', 'movieId', 'rating'])

ratings['userId'] = ratings['userId'].fillna(0)
ratings['movieId'] = ratings['movieId'].fillna(0)

ratings['rating'] = ratings['rating'].fillna(ratings['rating'].mean())

small_data = ratings.sample(frac=0.3)

train_data, test_data = train_test_split(small_data, test_size=0.2)

train_data_matrix = train_data.to_numpy()
test_data_matrix = test_data.to_numpy()

user_correlation = 1 - pairwise_distances(train_data, metric='correlation')
user_correlation[np.isnan(user_correlation)] = 0

# Item Similarity Matrix
item_correlation = 1 - pairwise_distances(train_data_matrix.T, metric='correlation')
item_correlation[np.isnan(item_correlation)] = 0

# Function to predict ratings
def predict(ratings, similarity, type='user'):
    if type == 'user':
        mean_user_rating = ratings.mean(axis=1)
        # Use np.newaxis so that mean_user_rating has same format as ratings
        ratings_diff = (ratings - mean_user_rating[:, np.newaxis])
        pred = mean_user_rating[:, np.newaxis] + similarity.dot(ratings_diff) / np.array([np.abs(similarity).sum(axis=1)]).T
    elif type == 'item':
        pred = ratings.dot(similarity) / np.array([np.abs(similarity).sum(axis=1)])
    return pred   

from sklearn.metrics import mean_squared_error
from math import sqrt

# Function to calculate RMSE
def rmse(pred, actual):
    # Ignore nonzero terms.
    pred = pred[actual.nonzero()].flatten()
    actual = actual[actual.nonzero()].flatten()
    return sqrt(mean_squared_error(pred, actual))
# Predict ratings on the training data with both similarity score
user_prediction = predict(train_data_matrix, user_correlation, type='user')
item_prediction = predict(train_data_matrix, item_correlation, type='item')
# RMSE on the train data
print('User-based CF RMSE: ' + str(rmse(user_prediction, train_data_matrix)))
print('Item-based CF RMSE: ' + str(rmse(item_prediction, train_data_matrix)))
print('')