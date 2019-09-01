import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

path="ml-latest-small"

ratings = pd.read_csv(path+'/ratings10.csv', sep=',', encoding='latin-1', usecols=['userId', 'movieId', 'rating'])
movies = pd.read_csv(path+'/moviesES.csv', sep=',', encoding='latin-1', usecols=['movieId', 'title', 'genres'])

print("\nDetalles de la base de datos:")
print(ratings['rating'].describe())


dataset = pd.merge(movies, ratings, on='movieId')

dataset['count'] = dataset.groupby('title', as_index=False)['title'].transform(lambda x: x.count())

print("\n\n20 Películas más valoradas:")

dataset = dataset.groupby(['title']).mean()
dataset.sort_values(by=['count'], ascending=[False], inplace=True)

print(dataset.head(20))

import seaborn as sns
sns.set_style('whitegrid')
sns.set(font_scale=1.5)

fig, ax = plt.subplots()

sns.distplot(ratings['rating'].fillna(ratings['rating'].median()))

ax.set_xticks(range(1,11))
ax.set_xlim(0,11)

ax.set(xlabel='')

plt.show()

