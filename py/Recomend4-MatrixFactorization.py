import pandas as pd
import numpy as np
import sys

import os
clear = lambda: os.system('cls')
clear()

print("\n4. FACTORIZACIÓN MATRICIAL\n")

path="ml-latest-small"

movies = pd.read_csv(path+'/moviesES.csv', sep=',', encoding='latin-1', usecols=['movieId', 'title', 'genres'])
ratings = pd.read_csv(path+'/ratings.csv', sep=',', encoding='latin-1', usecols=['userId', 'movieId', 'rating'])

n_users = ratings.userId.unique().shape[0]
n_movies = ratings.movieId.unique().shape[0]

print('Numero total de usuarios = ' + str(n_users) + ' | Numero de películas = ' + str(n_movies) + "\n")

pivot_ratings = ratings.pivot(index = 'userId', columns ='movieId', values = 'rating').fillna(0)

R = pivot_ratings.to_numpy()

user_ratings_mean = np.mean(R, axis = 1)

Ratings_demeaned = R - user_ratings_mean.reshape(-1, 1)

from scipy.sparse.linalg import svds

U, sigma, Vt = svds(Ratings_demeaned, k = 50)

sigma = np.diag(sigma)

all_user_predicted_ratings = np.dot(np.dot(U, sigma), Vt) + user_ratings_mean.reshape(-1, 1)

preds = pd.DataFrame(all_user_predicted_ratings, columns = pivot_ratings.columns)

def recommend_movies(predictions, userID, movies, original_ratings, num_recommendations):
        
    user_row_number = userID - 1    
    sorted_user_predictions = preds.iloc[user_row_number].sort_values(ascending=False) 
    
    user_data = original_ratings[original_ratings.userId == (userID)]
    user_full = (user_data.merge(movies, how = 'left', left_on = 'movieId', right_on = 'movieId').sort_values(['rating'], ascending=False))
    
    print('El usuario {0} ha valorado {1} películas.\n'.format(userID, user_full.shape[0]))
    
    # Recommend the highest predicted rating movies that the user hasn't seen yet.
    recommendations = (movies[~movies['movieId'].isin(user_full['movieId'])].merge(pd.DataFrame(sorted_user_predictions).reset_index(), how = 'left', left_on = 'movieId', right_on = 'movieId').rename(columns = {user_row_number: 'Predictions'}).sort_values('Predictions', ascending = False).iloc[:num_recommendations, :-1])

    return user_full, recommendations

if(len(sys.argv)>1):
    if(int(sys.argv[1]) <= n_users):
        arg = int(sys.argv[1])
else:
    arg = 1

already_rated, predictions = recommend_movies(preds, arg, movies, ratings, 20)

print('\nTop 20 películas valoradas del usuario {0}: \n'.format(arg ))
print(already_rated.head(20))

print('\nRecomendaciones para el usuario {0}: \n'.format(arg ))
print(predictions.head(20))

print('\n')
