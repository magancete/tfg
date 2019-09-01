import os
os.environ['TF_CPP_MIN_VLOG_LEVEL'] = '3'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from tensorflow import logging
logging.set_verbosity(logging.INFO)
from keras.constraints import maxnorm
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from keras.models import Model, load_model
from keras.layers import Input, Reshape, Dot
from keras.layers.embeddings import Embedding
from keras.optimizers import Adam
from keras.regularizers import l2
from keras.layers import Add, Activation, Lambda
from keras.callbacks import Callback, EarlyStopping, ModelCheckpoint
from keras import backend
from matplotlib import pyplot
import math
import sys

clear = lambda: os.system('cls')
clear()

path="ml-latest"

ratings = pd.read_csv(path+'/jw_ratings.csv', sep=',', encoding='latin-1', usecols=['userId', 'movieId', 'rating'])

movies = pd.read_csv(path+'/jw.csv', sep=',', encoding='latin-1', usecols=['movieId', 'title', 'genres'])

user_enc = LabelEncoder()
ratings['user'] = user_enc.fit_transform(ratings['userId'].values)
n_users = ratings['user'].nunique()

item_enc = LabelEncoder()
ratings['movie'] = item_enc.fit_transform(ratings['movieId'].values)
n_movies = ratings['movie'].nunique()

ratings['rating'] = ratings['rating'].values.astype(np.float32)

min_rating = min(ratings['rating'])
max_rating = max(ratings['rating'])

print('Numero de usuarios: ' + str(n_users))
print('Numero de películas: ' + str(n_movies))
print('Valoración mínima: ' + str(min_rating*2))
print('Valoración máxima: ' + str(max_rating*2))
print('\n')

X = ratings[['user', 'movie']].values
y = ratings['rating'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

n_factors = 50
X_train_array = [X_train[:, 0], X_train[:, 1]]
X_test_array = [X_test[:, 0], X_test[:, 1]]

X_train_array = [X_train[:, 0], X_train[:, 1]]
X_test_array = [X_test[:, 0], X_test[:, 1]]

class EmbeddingLayer:
    def __init__(self, n_items, n_factors):
        self.n_items = n_items
        self.n_factors = n_factors
    
    def __call__(self, x):
        x = Embedding(self.n_items, self.n_factors, embeddings_initializer='he_normal', embeddings_regularizer=l2(1e-6))(x)
        x = Reshape((self.n_factors,))(x)
        return x    

def Recommender(n_users, n_movies, n_factors, min_rating, max_rating):
    user = Input(shape=(1,))
    u = EmbeddingLayer(n_users, n_factors)(user)
    ub = EmbeddingLayer(n_users, 1)(user)
    
    movie = Input(shape=(1,))
    m = EmbeddingLayer(n_movies, n_factors)(movie)
    mb = EmbeddingLayer(n_movies, 1)(movie)
    x = Dot(axes=1)([u, m])
    x = Add()([x, ub, mb])
    x = Activation('sigmoid')(x)
    x = Lambda(lambda x: x * (max_rating - min_rating) + min_rating)(x)
    model = Model(inputs=[user, movie], outputs=x)
    opt = Adam(lr=0.001)
    model.compile(loss='mse', optimizer=opt, metrics=['mse'])
    return model


###################################################

model = Recommender(n_users, n_movies, n_factors, min_rating, max_rating)

# model.summary()

callbacks = [EarlyStopping('val_loss', patience=5), ModelCheckpoint('model/model.h5', save_best_only=True,save_weights_only=False)]

history = model.fit(x=X_train_array, y=y_train, batch_size=64, epochs=10, verbose=1, validation_data=(X_test_array, y_test),callbacks=callbacks)

min_val_loss, idx = min((val, idx) for (idx, val) in enumerate(history.history['val_loss']))

print('\nMínimo RMSE en la época {:d}'.format(idx+1) + ' = {:.4f}\n'.format(math.sqrt(min_val_loss)))

pyplot.plot(history.history['mean_squared_error'],label='MSE')
pyplot.plot(history.history['val_mean_squared_error'],label='Validation MSE')

# pyplot.plot(history.history['val_rmse'],label='RMSE')
# pyplot.plot(history.history['rmse'],label='Validation RMSE')

pyplot.legend()

pyplot.show()

###################################################

if(len(sys.argv)>1):    
    arg = int(sys.argv[1])
else:
    arg = 1

# Use the pre-trained model with its weights
trained_model = load_model('model/model.h5')

# Function to predict the ratings given User ID and Movie ID
def predict_rating(user_id, movie_id):
    return trained_model.predict([np.array([user_id]), np.array([movie_id])])[0][0]


print('\nTop 20 películas valoradas por el usuario {0}\n'.format(arg))

user_ratings = ratings[ratings['userId'] == arg][['user','userId', 'movie','movieId', 'rating']]
user_ratings['prediction'] = (user_ratings.apply(lambda x: predict_rating(x['user'], x['movie']), axis=1))*2
user_ratings['rating'] = user_ratings['rating']*2
user_ratings.sort_values(by=['prediction'], ascending=False,inplace=True)
user_ratings = user_ratings.merge(movies, on='movieId', how='inner', suffixes=['_u', '_m'])
user_ratings_new = user_ratings[['userId','movieId','rating','prediction','title','genres']]
print(user_ratings_new.head(20))

print('\nTop 20 películas recomendadas para el usuario {0}\n'.format(arg))

recommendations = ratings[ratings['movieId'].isin(user_ratings['movieId']) == False][['movie','movieId']].drop_duplicates()
recommendations['prediction'] = recommendations.apply(lambda x: predict_rating(user_ratings['user'][0], x['movie']), axis=1)*2
recommendations.sort_values(by='prediction', ascending=False,inplace=True)
recommendations = recommendations.merge(movies, on='movieId', how='inner', suffixes=['_u', '_m'])
recommendations['userId'] = user_ratings['userId'][0]
recommendations_new = recommendations[['userId','movieId','prediction','title','genres']]
print(recommendations_new.head(20))

print('\n')
  