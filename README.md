# Interfaz conversacional en Dialogflow para recomendación de películas

Este proyecto consiste en la realización de un chatbot en la plataforma Dialogflow que recomiende que película ver en un sistema de vídeo bajo demanda. El proyecto está dividido en dos partes: en primer lugar, el entrenamiento de la red neuronal y por otra parte el desarrollo del chatbot.

## Requisitos

* Descargar la base de datos [MovieLens](https://grouplens.org/datasets/movielens/)
* Python 3.6 o posterior
* Librerías Python: pandas, numpy, scipy, matplotlib, sklearn, wordcloud, searborn, surprise, keras, h5py, tensorflow, firebase_admin
* [JustWatch API para Python](https://github.com/magancete/node-justwatch-api)
* [TMDB API para Python](https://github.com/raqqa/node-tmdb/)

## Estructura del código y utilización

### 1. Procesar la base de datos

Para el análisis de la base de datos se utilizan los  archivos

```
AnalysisGenres.py
AnalysisMovies.py
AnalysisRatings.py
```

### 2. Entrenamiento

Diferentes aproximaciones al problema de la recomendación:
```
Recomend1-ContentBasedGenre.py
Recomend2-ContentBasedTag.py
Recomend3-ColaborativeFilter.py
Recomend4-MatrixFactorization.py
Recomend5-DeepLearning.py
```

Para re-entrenar y subir nuevos datos a la base de datos:
```
TrainUploadData.py
```

### 3. Dialogflow Webhook 

En la carpeta functions se encuentra la función `index.js` con el Webhook para Dialogflow.

## Author

Carlos Magán López, Agosto 2019
