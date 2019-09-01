import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

path="ml-latest-small"

movies = pd.read_csv(path+'/moviesES.csv', sep=',', encoding='latin-1', usecols=['movieId', 'title', 'genres'])

import wordcloud
from wordcloud import WordCloud, STOPWORDS

stopwords = set(STOPWORDS)
stopwords.update(["el", "la", "lo", "los", "las","ello","ella","ellos","ellas", "un", "una", "unos", "unas", "a", "al", "ante", "bajo", "con", "contra", "de", "del", "desde", "durante", "en", "entre", "hacia", "hasta", "mediante", "para", "por", "según", "sin", "sobre", "tras", "mi", "tu", "te", "su", "mis", "tus", "sus","yo","nosotros","vosotros", "y", "e", "ni", "que", "pero", "mas", "aunque", "sino", "siquiera", "o", "u"])

# Create a wordcloud of the movie titles
movies['title'] = movies['title'].fillna("").astype('str')
title_corpus = ' '.join(movies['title'])
title_wordcloud = WordCloud(stopwords=stopwords, background_color='white', height=2000, width=4000).generate(title_corpus)

# Plot the wordcloud
plt.figure(figsize=(16,8))
plt.imshow(title_wordcloud)
plt.axis('off')
plt.show()