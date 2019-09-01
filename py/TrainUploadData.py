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
import time
import csv
import subprocess

clear = lambda: os.system('cls')
clear()

def checkArg(arg):
   return arg in sys.argv

import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

path="ml-latest"

###############################################################

docs = db.collection(u'valoraciones').stream()

new = False

for doc in docs:
    pelicula = doc.to_dict()['pelicula']
    usuario = doc.to_dict()['usuario']
    valoracion = doc.to_dict()['valoracion']
    new=True
    with open(path+'-small/ratings.csv','a') as f:
        writer=csv.writer(f)
        writer.writerow([usuario,pelicula,float(valoracion/2),int(round(time.time() * 1000))])        

def delete_collection(coll_ref, batch_size):
    docs = coll_ref.limit(10).get()
    deleted = 0
    for doc in docs:        
        doc.reference.delete()
        deleted = deleted + 1
    if(deleted >= batch_size):
        return delete_collection(coll_ref, batch_size)        

if(new): 
    delete_collection(db.collection(u'valoraciones'), 10)
    subprocess.call(["python", "GenerateJustWatchDataset.py"])

###############################################################

ratings = pd.read_csv(path+'/jw_ratings.csv', sep=',', encoding='latin-1', usecols=['userId', 'movieId', 'rating'])

movies = pd.read_csv(path+'/jw.csv', sep=',', encoding='latin-1', usecols=['movieId','tmdbId', 'title', 'genres'])

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

if(checkArg('--train')):
    
    model = Recommender(n_users, n_movies, n_factors, min_rating, max_rating)

    # model.summary()

    callbacks = [EarlyStopping('val_loss', patience=5), ModelCheckpoint('model/model.h5', save_best_only=True,save_weights_only=False)]

    history = model.fit(x=X_train_array, y=y_train, batch_size=64, epochs=10, verbose=1, validation_data=(X_test_array, y_test),callbacks=callbacks)

    min_val_loss, idx = min((val, idx) for (idx, val) in enumerate(history.history['val_loss']))

    print('Entrenamiento completo')
    
else:    
    model = load_model('model/model.h5')

###################################################

# Function to predict the ratings given User ID and Movie ID
def predict_rating(user_id, movie_id):
    return model.predict([np.array([user_id]), np.array([movie_id])])[0][0]

################################## UPLOAD TO FIRESTORE ##################################


top = ratings[['movieId','rating']]
top['count'] = top.groupby('movieId', as_index=False)['movieId'].transform(lambda x: x.count())
top = top[top['count'] >= 100]
top = top.groupby(['movieId']).mean().reset_index()
top = top.merge(movies, on='movieId', how='inner', suffixes=['_u', '_m'])[['tmdbId','rating']]
top.sort_values(by=['rating'], ascending=[False], inplace=True)
doc_ref = db.collection(u'predicciones').document(u'info')
doc_ref.set({
    u'usuarios': max(int(ratings['userId'].max()), doc_ref.get().to_dict()['usuarios']),
    u'peliculas': n_movies,
    u'valoraciones': ratings.shape[0],
    u'top': top['tmdbId'].tolist()[:30]         
})

count = 0
while count < n_users:
    
    print('Usuario ' + str(count+1) + '/' + str(n_users))
    
    media = float('%.3f'%(ratings[ratings['user'] == count].loc[:,"rating"].mean()*2))
    
    vistas = ratings[ratings['user'] == count].shape[0]
        
    user_ratings = ratings[ratings['user'] == count][['user','userId', 'movie','movieId', 'rating']]
    
    userId = user_ratings['userId'].iloc[0]       
    
    recommendations = ratings[ratings['movieId'].isin(user_ratings['movieId']) == False][['movie','movieId']].drop_duplicates()    
    recommendations['prediction'] = recommendations.apply(lambda x: predict_rating(count, x['movie']), axis=1)
    recommendations = recommendations.merge(movies, on='movieId', how='inner', suffixes=['_u', '_m'])[['tmdbId','prediction']]
    recommendations.sort_values(by='prediction', ascending=False,inplace=True)
    
    r = recommendations['tmdbId'].tolist()[:30]       
    
    doc_ref = db.collection(u'predicciones').document(u'usuario_' + str(userId))
    doc_ref.set({
        u'media': media,
        u'predicciones': r,
        u'vistas': vistas
    })
    count += 1

#########################################################################################