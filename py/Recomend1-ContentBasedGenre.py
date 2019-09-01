import pandas as pd
import numpy as np
import sys

import os
clear = lambda: os.system('cls')
clear()

print("\n1. FILTRO BASADO EN CONTENIDO: GÉNEROS\n")

path="ml-latest-small"

movies = pd.read_csv(path+'/moviesES.csv', sep=',', encoding='latin-1', usecols=['movieId', 'title', 'genres'])
ratings = pd.read_csv(path+'/ratings.csv', sep=',', encoding='latin-1', usecols=['userId', 'movieId', 'rating'])

dataset = pd.merge(movies, ratings, on='movieId')

dataset['count'] = dataset.groupby('title', as_index=False)['title'].transform(lambda x: x.count())

data = dataset.groupby(['title','genres']).mean()
data.sort_values(by=['movieId'], inplace=True)
data = data.reset_index()

movieId = data['movieId'].astype(int)
title = data['title']
rating = np.round(data['rating'],decimals=4)
count = data['count'].astype(int)
genres = data['genres']

result = pd.concat([movieId, title,genres,rating,count],axis=1)

from sklearn.feature_extraction.text import TfidfVectorizer

tf = TfidfVectorizer(analyzer='word',ngram_range=(1, 2),min_df=0)

tfidf_matrix = tf.fit_transform(result['genres'])

from sklearn.metrics.pairwise import linear_kernel

cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

indices = pd.Series(result.index, index=result['movieId'])

# Function that get movie recommendations based on the cosine similarity score of movie genres
def genre_recommendations(movieId):
    idx = indices[movieId]
    print("Pelicula seleccionada: " + result['title'][idx] + "\nGéneros: " + result['genres'][idx] + "\n")
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:21]
    movie_indices = [i[0] for i in sim_scores]
    return result.iloc[movie_indices, [0,1,2]]


if(len(sys.argv)>1):
    arg = int(sys.argv[1])
else:
    arg = 1

print(genre_recommendations(arg))
print("\n")


