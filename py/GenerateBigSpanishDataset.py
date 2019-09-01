import pandas as pd
from justwatch import JustWatch
from tmdbv3api import TMDb
import json

import os
clear = lambda: os.system('cls')
clear()

tmdb = TMDb()
tmdb.api_key = '26dbb8a0a01225766314aa8bd1ed7e25'

tmdb.language = 'es'
tmdb.debug = False

from tmdbv3api import Movie

movie = Movie()
    
path="ml-latest"

movies = pd.read_csv(path+'/movies.csv', sep=',', encoding='latin-1', usecols=['movieId', 'title', 'genres'])
links = pd.read_csv(path+'/links.csv', sep=',', encoding='latin-1', usecols=['tmdbId'])

movies['movieId'] = movies['movieId'].drop_duplicates()
movies['title'] = movies['title'].drop_duplicates()

import csv

def GenreToGenero(genre):
    
    if genre == "Action":
        return "Acción"
    elif genre == "Adventure":
        return "Aventura"
    elif genre == "Animation":
        return "Animación"
    elif genre == "Children":
        return "Infantil"
    elif genre == "Comedy":
        return "Comedia"
    elif genre == "Crime":
        return "Crimen"
    elif genre == "Documentary":
        return "Documental"
    elif genre == "Drama":
        return "Drama"
    elif genre == "Fantasy":
        return "Fantasía"
    elif genre == "Film-Noir":
        return "Cine Negro"
    elif genre == "Horror":
        return "Terror"
    elif genre == "Musical":
        return "Musical"
    elif genre == "Mystery":
        return "Misterio"
    elif genre == "Romance":
        return "Romance"
    elif genre == "Sci-Fi":
        return "Ciencia Ficción"
    elif genre == "Thriller":
        return "Thriller"
    elif genre == "War":
        return "Guerra"
    elif genre == "Western":
        return "Western"
    else:
        return "Otro"
    
last = pd.read_csv(path+'/moviesES.csv', sep=',', encoding='latin-1', usecols=['movieId'])
count = len(last.index)

with open(path+'/moviesES.csv', mode='a+', newline='') as file:    
    
    fieldnames = ['movieId', 'title', 'genres']
    writer = csv.DictWriter(file, fieldnames=fieldnames)   
    
    if(count==1):         
        writer.writeheader()  
    
    while count<links.shape[0]:   
                        
        m = movie.details(links['tmdbId'][count])
        
        if(hasattr(m,'status_code')):
            if(m.status_code != 1):
                name = movies['title'][count]
        else:
            if(hasattr(m,'title')):     
                title = m.title.encode('latin-1', 'replace').decode('latin-1')
            elif(hasattr(m,'original_title')):
                title = m.original_title.encode('latin-1', 'replace').decode('latin-1')

            if(hasattr(m,'release_date')):        
                year = m.release_date.split("-",1)[0] 
                name = title + " ("+year+")" 
            else:            
                name = movies['title'][count].encode('latin-1', 'replace').decode('latin-1')
            
        genres = movies['genres'][count].split("|") 

        x = 0
        for i in genres: 
            genres[x]=GenreToGenero(i)  
            x += 1

        seperator = '|' 
        
        writer.writerow({'movieId': movies['movieId'][count], 'title': name, 'genres': seperator.join(genres)})
        
        print(("{0} " + name + " " + seperator.join(genres) + "\n").format(count))
        
        count += 1
        
file.close()   