from justwatch import JustWatch

import json
import csv
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys

import os
clear = lambda: os.system('cls')
clear()

just_watch = JustWatch(country='ES')

path="ml-latest"
        
def GenreIdToGenero(genre):
        
    if genre == 1:
        return "Acción"
    elif genre == 2:
        return "Animación"
    elif genre == "Children":
        return "Infantil"
    elif genre == 3:
        return "Comedia"
    elif genre == 4:
        return "Crimen"
    elif genre == 5:
        return "Documental"
    elif genre == 6:
        return "Drama"
    elif genre == 7:
        return "Fantasía"
    elif genre == 8:
        return "Historia"
    elif genre == 9:
        return "Terror"
    elif genre == 10:
        return "Familia"
    elif genre == 11:
        return "Musica"
    elif genre == 12:
        return "Thriller"
    elif genre == 13:
        return "Romance"
    elif genre == 14:
        return "Ciencia Ficción"
    elif genre == 15:
        return "Deporte"    
    elif genre == 16:
        return "Guerra"
    elif genre == 17:
        return "Western"
    elif genre == 18:
        return "Europea"
    else:
        return "Otro"    
 

with open(path+'/jw.csv', mode='w', newline='') as file:
    
    fieldnames = ['jwId', 'tmdbId', 'title','genres']
    
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    
    writer.writeheader()
        
    pageSize = 30
    
    peliculas = []
    
    first = just_watch.search_for_item(
            content_types = ['movie'], 
            release_year_from = 1970,
            page = 1,
            scoring_filter_types={"imdb:score": {"min_scoring_value":5}},
            page_size = pageSize
            )
    
    for item in first['items']:
        peliculas.append(item['id'])                    
    
    total = first['total_results']    
    totalPages = math.ceil(total/pageSize)
    
    print('Página 1/'+str(totalPages))
    
    count = 2
    
    while count <= totalPages:
        
        page = just_watch.search_for_item(
            content_types=['movie'], 
            release_year_from=1970,
            page = count,
            scoring_filter_types={"tomato:score": {"min_scoring_value":5}},
            page_size = pageSize
            )
        
        for item in page['items']:
            peliculas.append(item['id'])
          
        print('Página '+str(count) +'/'+str(totalPages))
            
        count += 1        
                
    count = 0
    
    while (count<len(peliculas)):
         
        try:
            movie = just_watch.get_title(title_id=peliculas[count])

            # print(json.dumps(movie, indent=4, sort_keys=True))

            if((movie['object_type'] == 'movie') & ("offers" in movie)):        

                name = movie['title'] + ' (' + str(movie['original_release_year']) + ')'

                genresId = movie['genre_ids']

                i = 0 
                genres = []

                for id in genresId:
                    genres.append(GenreIdToGenero(id))

                seperator = '|' 

                for externalId in movie['external_ids']:
                    if externalId['provider'] == 'tmdb':
                        tmdbId = externalId['external_id']

                print('jwId: ' + str(peliculas[count]) + ' | tmdbId: ' + str(tmdbId) + ' | title: ' + name + ' | genres: ' + seperator.join(genres))

                writer.writerow({'jwId': peliculas[count], 'tmdbId': tmdbId, 'title': name, 'genres': seperator.join(genres)})
                                
        except:
            print('Error en la película con id: ' + str(count))
                
        count += 1
                
file.close()

movies = pd.read_csv(path+'/jw.csv', sep=',', encoding='latin-1', usecols=['jwId', 'tmdbId', 'title','genres'])

links = pd.read_csv(path+'/links.csv', sep=',', encoding='latin-1', usecols=['movieId','tmdbId'])

data = links.merge(movies, how = 'inner', left_on = 'tmdbId', right_on = 'tmdbId').sort_values(['movieId'])

data = data[pd.notnull(data['title'])]

data['jwId'] = data['jwId'].astype(int)
data['tmdbId'] = data['tmdbId'].astype(int)

df = pd.DataFrame(data)

df.to_csv(path+'/jw.csv',mode = 'w', index=False, encoding='latin-1')

ratings = pd.read_csv(path+'-small/ratings.csv', sep=',', encoding='latin-1', usecols=["userId","movieId","rating"])

ratings = ratings.drop_duplicates()

movies = data

last = pd.DataFrame()

for index, row in movies.iterrows():
    
    new = ratings[ratings.movieId == row.movieId]
    
    last = pd.concat([last,new])
    
df = pd.DataFrame(last)

df = df.groupby('movieId').filter(lambda x : len(x)>10)

df.to_csv(path+'/jw_ratings.csv',mode = 'w', index=False, encoding='latin-1')



