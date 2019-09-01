import pandas as pd
import numpy as np
import sys

import os
clear = lambda: os.system('cls')
clear()

print("\n3. FILTRO BASADO EN CONTENIDO: PALABRAS CLAVES\n")

path="ml-latest-small"

movies = pd.read_csv(path+'/moviesES.csv', sep=',', encoding='latin-1', usecols=['movieId', 'title', 'genres'])
ratings = pd.read_csv(path+'/ratings.csv', sep=',', encoding='latin-1', usecols=['movieId', 'rating'])
tags = pd.read_csv(path+'/tags.csv', sep=',', encoding='latin-1', usecols=['movieId', 'tag'])

tags['movieId'] = tags['movieId'].fillna(0)
ratings['movieId'] = ratings['movieId'].fillna(0)

dataset = pd.merge(movies, tags, on='movieId')

data = dataset.groupby(['title','movieId'])['tag'].apply(' '.join).reset_index()
data.sort_values(by=['movieId'], inplace=True)
data = data.reset_index()

movieId = data['movieId']
title = data['title']
tag = data['tag']

result = pd.concat([movieId, title,tag],axis=1)


from sklearn.feature_extraction.text import TfidfVectorizer

tf = TfidfVectorizer(analyzer='word',ngram_range=(1, 2),min_df=0)

tfidf_matrix = tf.fit_transform(result['tag'])

from sklearn.metrics.pairwise import linear_kernel

cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

indices = pd.Series(result.index, index=result['movieId'])

# Function that get movie recommendations based on the cosine similarity score of movie genres
def tag_recommendations(movieId):
    idx = indices[movieId]
    print("Pelicula seleccionada: " + result['title'][idx] + "\nTags: " + result['tag'][idx] + "\n")
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:21]
    movie_indices = [i[0] for i in sim_scores]
    return result.iloc[movie_indices, [0,1,2]]

if(len(sys.argv)>1):    
    arg = int(sys.argv[1])
else:
    arg = 1

print(tag_recommendations(arg))
print("\n")


