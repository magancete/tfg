const functions = require('firebase-functions');

const admin = require('firebase-admin');

const {
    Card,
    Suggestion,
    WebhookClient,
    Payload
} = require('dialogflow-fulfillment');

const {
    BasicCard,
    Button,
    Image,
    Suggestions
} = require('actions-on-google');

const JustWatch = require('justwatch-api');

admin.initializeApp(functions.config().firebase);
const db = admin.firestore();

const tmdb = require('tmdbv3').init('26dbb8a0a01225766314aa8bd1ed7e25');

process.env.DEBUG = 'dialogflow:debug';

const inicioTitle = 'Recomendador de películas';
const inicioImageUrl = 'http://marcianosmx.com/wp-content/uploads/2015/09/posters-80-peliculas.jpg';
const inicioText = 'Proyecto realizado por Carlos Magán para la Universidad Carlos III de Madrid.';

exports.dialogflowFirebaseFulfillment = functions.https.onRequest((request, response) => {

    const agent = new WebhookClient({
        request,
        response
    });

    var conv = agent.conv();

    var hasScreen = conv.surface.capabilities.has('actions.capability.SCREEN_OUTPUT');

    //////////////////////////////////// INICIO ////////////////////////////////////

    function inicio(agent) {

        /*
        agent.add(new Image('https://avatars1.githubusercontent.com/u/36980416');
        agent.add(new Payload(agent.ACTIONS_ON_GOOGLE, {'your Google payload here'});
        agent.setContext({
            name: 'Destination',
            lifespan: 5,
            parameters: {
                Destination: Destination
            }
        });
        */

        if (conv.user.storage.userId === undefined) {

            agent.add(new Card({
                title: inicioTitle,
                imageUrl: inicioImageUrl,
                text: inicioText
            }));
            agent.setFollowupEvent('newUser');

        } else {

            conv.ask('Bienvenido de nuevo ' + conv.user.storage.nombre + '!');
            conv.ask(new BasicCard({
                text: inicioText,
                title: inicioTitle,
                image: new Image({
                    url: inicioImageUrl,
                    alt: "Collage",
                }),
            }));
            conv.ask(new Suggestions('Buscar película'));
            conv.ask(new Suggestions('Perfil'));
            conv.ask(new Suggestions('Salir'));

            conv.user.storage.lastRecomendation = 0;

            return new Promise((resolve, reject) => {

                let recomendations = db.collection('predicciones').doc('usuario_' + conv.user.storage.userId);
                recomendations.get().then(doc => {
                        if (!doc.exists) {
                            console.log('Usuario no encontrado!');
                        } else {
                            conv.user.storage.recomendations = JSON.stringify(doc.data().predicciones);
                        }
                        agent.add(conv);
                        return resolve();
                    })
                    .catch(err => {
                        console.log('Error getting document', err);
                        return resolve();
                    });
            })

        }
    }

    //////////////////////////////////// NUEVO USUARIO ////////////////////////////////////

    function nuevoUsuario(agent) {

        agent.add(new Card({
            title: inicioTitle,
            imageUrl: inicioImageUrl,
            text: inicioText
        }));

        agent.add('¡Bienvenido a tu recomendador de películas!  \nVeo que eres un nuevo usuario. ¿Quieres crear un nuevo perfil?');
        agent.add(new Suggestion('Si'));
        agent.add(new Suggestion('No'));

    }

    function nuevoUsuarioYes(agent) {

        agent.add('¿Cuál es tu nombre?');

    }

    function nuevoUsuarioNo(agent) {

        conv.ask('Lo siento pero sin un usuario no puedes continuar.')
        conv.close('Hasta luego.');
        agent.add(conv)

    }

    function nuevoUsuarioYesName(agent) {

        const nombre = agent.parameters.Nombre;

        return new Promise((resolve, reject) => {

            var dialogflowAgentDoc = db.collection('predicciones').doc('info');

            db.runTransaction(t => {
                return t.get(dialogflowAgentDoc)
                    .then(doc => {
                        conv.user.storage.userId = doc.data().usuarios + 1;
                        t.update(dialogflowAgentDoc, {
                            usuarios: doc.data().usuarios + 1
                        });

                        conv.user.storage.nombre = nombre;

                        let newUser = db.collection('predicciones').doc('usuario_' + (doc.data().usuarios + 1));

                        newUser.set({
                            'media': 0,
                            'vistas': 0,
                            'predicciones': doc.data().top
                        });

                        conv.ask('Usuario creado correctamente, bienvenido ' + nombre);

                        if (hasScreen) {
                            conv.ask(new BasicCard({
                                text: inicioText,
                                title: inicioTitle,
                                image: new Image({
                                    url: inicioImageUrl,
                                    alt: "Collage",
                                }),
                            }));
                            conv.ask(new Suggestions('Buscar película'));
                            conv.ask(new Suggestions('Perfil'));
                            conv.ask(new Suggestions('Salir'));
                        }

                        agent.add(conv);

                        return resolve();

                    });
            }).then(result => {
                return resolve();
            }).catch(err => {
                console.log('Transaction failure:', err);
            });

        });
    }

    //////////////////////////////////// AYUDA ////////////////////////////////////

    function ayuda(agent) {

        if (conv.user.storage.userId === undefined) {
            agent.setFollowupEvent('newUser');
        } else {
            agent.add("Para buscar una película di: \"Buscar película\".  \nPara mirar tu perfil di: \"Perfil\".  \nPara eliminar tu perfil di: \"Eliminar Datos\".  \nPara volver al menú princial di: \"Inicio\".  \nPara salir di: \"Salir\".");
        }
    }

    //////////////////////////////////// OBTENER DATOS ////////////////////////////////////

    function datos(agent) {

        if (conv.user.storage.userId === undefined) {
            agent.setFollowupEvent('newUser');
        } else {

            agent.add("Este es tu perfil de usuario:");

            return new Promise((resolve, reject) => {

                let datos = db.collection('predicciones').doc('usuario_' + conv.user.storage.userId);

                datos.get().then(doc => {

                        let vistas = doc.data().vistas;
                        let media = doc.data().media;

                        if (hasScreen) {

                            agent.add(new Card({
                                title: 'Datos de usuario',
                                text: '- Id: ' + conv.user.storage.userId + '  \n- Nombre: ' + conv.user.storage.nombre + '  \n- Películas vistas: ' + vistas + '  \n- Valoración media: ' + media
                            }));
                            agent.add(new Suggestion('Menú principal'));
                            agent.add(new Suggestion('Cambiar nombre'));
                            agent.add(new Suggestion('Eliminar datos'));

                        } else {
                            agent.add("Id: " + conv.user.storage.userId + '  \nNombre: ' + conv.user.storage.nombre + '  \nPelículas vistas: ' + vistas + '  \nValoración media: ' + media);
                        }
                        return resolve();

                    })
                    .catch(err => {
                        console.log('Error getting document', err);
                        return resolve();
                    });
            });
        }
    }

    //////////////////////////////////// CAMBIAR NOMBRE ////////////////////////////////////

    function cambiarNombre(agent) {

        if (conv.user.storage.userId === undefined) {
            agent.setFollowupEvent('newUser');
        } else {
            agent.add('¿Quieres cambiar tu nombre ' + conv.user.storage.nombre + '?');
            agent.add(new Suggestion('Si'));
            agent.add(new Suggestion('No'));
        }

    }

    function cambiarNombreYes(agent) {

        agent.add('¿Cuál es tu nombre?');

    }

    function cambiarNombreNo(agent) {

        agent.add('Perfecto');
        agent.setFollowupEvent('inicio');

    }

    function cambiarNombreYesNombre(agent) {

        const nombre = agent.parameters.Nombre;

        conv.user.storage.nombre = nombre;
        conv.ask('Nombre cambiado correctamente ' + nombre);

        if (hasScreen) {
            conv.ask(new BasicCard({
                text: inicioText,
                title: inicioTitle,
                image: new Image({
                    url: inicioImageUrl,
                    alt: "Collage",
                }),
            }));
            conv.ask(new Suggestions('Buscar película'));
            conv.ask(new Suggestions('Perfil'));
            conv.ask(new Suggestions('Salir'));
        }

        agent.add(conv)

    }

    //////////////////////////////////// ELIMINAR DATOS ////////////////////////////////////

    function eliminarDatos(agent) {
        if (conv.user.storage.userId === undefined) {
            agent.setFollowupEvent('newUser');
        } else {
            agent.add("¿Seguro que quieres eliminar tus datos personales? No podré recomendarte películas si sigues adelante.");
            agent.add(new Suggestion('Si'));
            agent.add(new Suggestion('No'));
        }
    }

    function eliminarDatosYes(agent) {
        conv.user.storage.userId = undefined;
        conv.user.storage.nombre = undefined;
        conv.user.storage.lastRecomendation = undefined;
        conv.close('Tus datos han sido eliminados correctamente. Hasta otra ocasión.');
        agent.add(conv)
    }

    function eliminarDatosNo(agent) {
        agent.add('Perfecto');
        agent.setFollowupEvent('inicio');
    }

    //////////////////////////////////// BUSCAR PELÍCULA ////////////////////////////////////

    function buscar(agent) {

        if (conv.user.storage.userId === undefined) {
            agent.setFollowupEvent('newUser');
        } else {

            let movieId = 85;
            let userRecomendation = conv.user.storage.lastRecomendation;

            try {
                movieId = JSON.parse(conv.user.storage.recomendations)[conv.user.storage.lastRecomendation];
            } catch (e) {
                console.log(e);
            }

            return new Promise((resolve, reject) => {

                tmdb.movie.info(movieId, 'es', (err, res) => {

                    if (err) {
                        console.log(err);
                    }

                    let title = '';
                    let imageUrl = '';
                    let text = '';

                    if (res.hasOwnProperty('title')) {
                        title = res.title;
                    } else {
                        title = res.original_title;
                    }

                    if (res.hasOwnProperty('poster_path')) {
                        imageUrl = 'https://image.tmdb.org/t/p/original' + res.poster_path;
                    }

                    if (res.hasOwnProperty('overview')) {
                        text = res.overview;
                    }

                    console.log(movieId + ' | ' + title + ' | ' + imageUrl + ' | ' + text);

                    if (hasScreen) {
                        conv.ask('¿Has visto esta película?');
                        conv.ask(new BasicCard({
                            text: text,
                            title: title,
                            image: new Image({
                                url: imageUrl,
                                alt: title,
                            }),
                        }));

                        conv.ask(new Suggestions('Si'));
                        conv.ask(new Suggestions('Resumen'));
                        conv.ask(new Suggestions('No'));
                    } else {
                        conv.ask('¿Has visto la película ' + title + '?');
                    }

                    conv.user.storage.lastRecomendation = conv.user.storage.lastRecomendation + 1
                    conv.user.storage.lastMovieTitle = title;
                    conv.user.storage.lastMovieId = movieId;
                    conv.user.storage.lastOverview = text;

                    agent.add(conv)

                    return resolve();

                });
            });


        }
    }

    function buscarResumen(agent) {


        agent.add(new Suggestion('Si'));
        agent.add(new Suggestion('No'));
        agent.add(conv.user.storage.lastOverview);
        agent.add("¿La has visto?");

    }

    function buscarNo(agent) {

        agent.add("¿Te apetece verla?");
        agent.add(new Suggestion('Si'));
        agent.add(new Suggestion('Resumen'));
        agent.add(new Suggestion('No'));

    }

    function buscarNoOverview(agent) {

        agent.add(new Suggestion('Si'));
        agent.add(new Suggestion('No'));
        agent.add(conv.user.storage.lastOverview);
        agent.add("¿Te apetece verla?");


    }

    function buscarNoNo(agent) {

        agent.add('OK');
        agent.setFollowupEvent('pelicula');

    }

    function buscarNoYes(agent) {

        return new Promise((resolve, reject) => {

            var jw = new JustWatch("es_ES");

            jw.getTitleProviders({
                query: conv.user.storage.lastMovieTitle
            }).then(response => {

                let offers = response.offers;

                getProvider(offers);

                return resolve();

            }).catch(e => {
                console.log(e)
                agent.add('Error');
                return resolve();
            })
        });

    }

    function buscarYes(agent) {

        agent.add('Del 1 al 10 ¿cómo valorarías la película?');
        agent.add(new Suggestion('10'));
        agent.add(new Suggestion('9'));
        agent.add(new Suggestion('8'));
        agent.add(new Suggestion('7'));
        agent.add(new Suggestion('6'));
        agent.add(new Suggestion('5'));
        agent.add(new Suggestion('4'));
        agent.add(new Suggestion('3'));
        agent.add(new Suggestion('2'));
        agent.add(new Suggestion('1'));

    }

    function buscarYesNumber(agent) {

        if (parseInt(agent.parameters.number) < 1 || parseInt(agent.parameters.number) > 10) {

            agent.add('OK');
            agent.setFollowupEvent('number');

        } else {

            var valoracion = parseInt(agent.parameters.number);

            agent.add('Valoración guardada correctamente!');
            agent.setFollowupEvent('pelicula');

            return new Promise((resolve, reject) => {
                db.collection('valoraciones').add({
                    pelicula: conv.user.storage.lastMovieId,
                    usuario: conv.user.storage.userId,
                    valoracion: valoracion
                }).then(ref => {

                    console.log(conv.user.storage.lastMovieId + ' | ' + conv.user.storage.lastMovieTitle + ' valorada con un ' + valoracion);

                    let update = db.collection('predicciones').doc('usuario_' + conv.user.storage.userId);
                    return db.runTransaction(t => {
                        return t.get(update)
                            .then(doc => {

                                let vistas = doc.data().vistas;
                                let media = ((doc.data().media * vistas) + valoracion) / (vistas + 1);
                                return t.update(update, {
                                    media: media,
                                    vistas: (vistas + 1)
                                });
                            });

                    }).then(result => {
                        console.log('Perfil de usuario actualizado');
                        return resolve();
                    }).catch(err => {
                        console.log('Error al actualziar el perfil del usuario: ', err);
                    });

                }).catch(err => {
                    console.log('Error escribiendo la valoración: ', err);
                });
            })
        }
    }

    //////////////////////////////////// UTILS ////////////////////////////////////

    function getProvider(providers) {

        let stream = [];
        let rent = [];
        let buy = [];

        for (let i = 0; i < providers.length; i++) {
            if (providers[i].monetization_type === 'flatrate') {
                stream[i] = getProviderName(providers[i].provider_id);
            } else if (providers[i].monetization_type === 'rent') {
                rent[i] = getProviderName(providers[i].provider_id);
            } else if (providers[i].monetization_type === 'buy') {
                buy[i] = getProviderName(providers[i].provider_id);
            }
        }

        buy = buy.filter((item, pos) => {
            return buy.indexOf(item) === pos;
        })

        stream = stream.filter((item, pos) => {
            return stream.indexOf(item) === pos;
        })

        rent = rent.filter((item, pos) => {
            return rent.indexOf(item) === pos;
        })


        if (buy.length === 0 && stream.length === 0 && rent.length === 0) {
            agent.add("La película \"" + conv.user.storage.lastMovieTitle + "\" no se encuentra disponible en ninguna plataforma.");
        } else {
            let text = "La película \"" + conv.user.storage.lastMovieTitle + "\" se encuentra disponible en las siguientes plataformas:";
            if (stream.length > 0) {
                if (rent.length === 1) {
                    text = text + '  \n- Puedes verla online en ' + stream.join(', ') + '.';
                } else {
                    text = text + '  \n- Puedes verla online en ' + stream.slice(0, -1).join(', ') + ' y ' + stream.slice(-1) + '.';
                }
            }
            if (rent.length > 0) {
                if (rent.length === 1) {
                    text = text + '  \n- Puedes alquilarla en ' + rent.join(', ') + '.';
                } else {
                    text = text + '  \n- Puedes alquilarla en ' + rent.slice(0, -1).join(', ') + ' y ' + rent.slice(-1) + '.';
                }
            }
            if (buy.length > 0) {
                if (buy.length === 1) {
                    text = text + '  \n- Puedes comprarla en ' + buy.join(', ') + '.';
                } else {
                    text = text + '  \n- Puedes comprarla en ' + buy.slice(0, -1).join(', ') + ' y ' + buy.slice(-1) + '.';
                }

            }
            text = text + '  \n  \nDisfruta de la película.';
            conv.close(text);
            agent.add(conv)
        }
    }

    function getProviderName(id) {

        let providerName = '';

        switch (id) {
            case 8:
                providerName = 'Netflix';
                break;
            case 136:
                providerName = 'Netflix';
                break;
            case 119:
                providerName = 'Amazon Prime Video';
                break;
            case 149:
                providerName = 'Movistar Plus';
                break;
            case 329:
                providerName = 'Vodafone TV';
                break;
            case 63:
                providerName = 'Filmin';
                break;
            case 64:
                providerName = 'Filmin Plus';
                break;
            case 118:
                providerName = 'HBO';
                break;
            case 35:
                providerName = 'Rakuten TV';
                break;
            case 62:
                providerName = 'Atres Player';
                break;
            case 2:
                providerName = 'Apple iTunes';
                break;
            case 3:
                providerName = 'Google Play Movies';
                break;
            case 18:
                providerName = 'PlayStation';
                break;
            case 68:
                providerName = 'Microsoft Store';
                break;
            case 11:
                providerName = 'Mubi';
                break;
            case 100:
                providerName = 'GuideDoc';
                break;
            case 188:
                providerName = 'YouTube Premium';
                break;
            case 257:
                providerName = 'fuboTV';
                break;
            case 283:
                providerName = 'Crunchyroll';
                break;
            default:
                providerName = 'Desconocido';
                break;
        }

        return providerName;

    }

    //////////////////////////////////// AÑADIR FUNCIONES ////////////////////////////////////

    let intentMap = new Map();

    intentMap.set('Inicio', inicio);

    intentMap.set('NuevoUsuario', nuevoUsuario);
    intentMap.set('NuevoUsuario - no', nuevoUsuarioNo);
    intentMap.set('NuevoUsuario - yes', nuevoUsuarioYes);
    intentMap.set('NuevoUsuario - yes - name', nuevoUsuarioYesName);

    intentMap.set('Buscar', buscar);
    intentMap.set('Buscar - overview', buscarResumen);
    intentMap.set('Buscar - no', buscarNo);
    intentMap.set('Buscar - no - overview', buscarNoOverview);
    intentMap.set('Buscar - no - no', buscarNoNo);
    intentMap.set('Buscar - no - yes', buscarNoYes);
    intentMap.set('Buscar - yes', buscarYes);
    intentMap.set('Buscar - yes - select.number', buscarYesNumber);

    intentMap.set('Ayuda', ayuda);

    intentMap.set('Datos', datos);

    intentMap.set('CambiarNombre', cambiarNombre);
    intentMap.set('CambiarNombre - no', cambiarNombreNo);
    intentMap.set('CambiarNombre - yes', cambiarNombreYes);
    intentMap.set('CambiarNombre - yes - name', cambiarNombreYesNombre);

    intentMap.set('EliminarDatos', eliminarDatos);
    intentMap.set('EliminarDatos - no', eliminarDatosNo);
    intentMap.set('EliminarDatos - yes', eliminarDatosYes);

    agent.handleRequest(intentMap);

});
