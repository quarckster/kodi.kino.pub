# -*- coding: utf-8 -*-

actionIndex_response = {
    u"status": 200, u"items": [
        {u"id": u"movie", u"title": u"Фильмы"},
        {u"id": u"serial", u"title": u"Сериалы"},
        {u"id": u"tvshow", u"title": u"ТВ шоу"},
        {u"id": u"4k", u"title": u"4K"},
        {u"id": u"3d", u"title": u"3D"},
        {u"id": u"concert", u"title": u"Концерты"},
        {u"id": u"documovie", u"title": u"Документальные фильмы"},
        {u"id": u"docuserial", u"title": u"Документальные сериалы"}
    ]
}

actionPlay_response = {
    u"status": 200,
    u"item": {
        u"rating": 3,
        u"videos": [
            {
                u"files": [
                    {
                        u"url": {
                            u"hls": u"https://example.com/hls/480",
                            u"hls2": u"https://example.com/hls2/480",
                            u"http": u"https://example.com/http/480",
                            u"hls4": u"https://example.com/hls4/480"
                        },
                        u"h": 304,
                        u"quality": u"480p",
                        u"w": 720
                    },
                    {
                        u"url": {
                            u"hls": u"https://example.com/hls/720",
                            u"hls2": u"https://example.com/hls2/720",
                            u"http": u"https://example.com/http/720",
                            u"hls4": u"https://example.com/hls4/720"
                        },
                        u"h": 540,
                        u"quality": u"720p",
                        u"w": 1280
                    },
                    {
                        u"url": {
                            u"hls": u"https://example.com/hls/1080",
                            u"hls2": u"https://example.com/hls2/1080",
                            u"http": u"https://example.com/http/1080",
                            u"hls4": u"https://example.com/hls4/1080"
                        },
                        u"h": 808,
                        u"quality": u"1080p",
                        u"w": 1912
                    }
                ],
                u"title": "",
                u"watching": {
                    u"status": -1,
                    u"time": 0
                },
                u"number": 1,
                u"id": 22000,
                u"ac3": 0,
                u"tracks": 3,
                u"duration": 5631,
                u"watched": -1,
                u"thumbnail": u"https://example.com/480x270.jpg",
                u"subtitles": []
            }
        ],
        u"imdb": 306841,
        u"year": 2003,
        u"duration": {
            u"average": 5631,
            u"total": 5631
        },
        u"bookmarks": [],
        u"ac3": 0,
        u"quality": 1080,
        u"id": 8086,
        u"kinopoisk": 300,
        u"plot": u"Тринадцатилетняя школьница Лиззи Магуайер и ее приятели Гордо, Кейт и Эсан собираются оттянуться по полной программе во время их поездки с классом в Италию.\r\nНо там случается весьма неожиданное происшествие: девочку ошибочно принимают за итальянскую поп-звезду Изабеллу, да к тому же девушка влюбляется в бывшего дружка Изабеллы Паоло. Когда родители Лизи обо всем узнают, они вместе с ее братом Мэттом срочно вылетают в Италию.\r\nНо Лиззи уже не та закомплексованная девочка-подросток, кем была раньше, она до такой степени вжилась в роль певицы, что и на самом деле стала самой настоящей звездой.",
        u"genres": [
            {
                u"id": 1,
                u"title": u"Комедия"
            },
            {
                u"id": 6,
                u"title": u"Семейный"
            },
            {
                u"id": 8,
                u"title": u"Приключения"
            },
            {
                u"id": 10,
                u"title": u"Мелодрама"
            },
            {
                u"id": 19,
                u"title": u"Музыкальный"
            }
        ],
        u"title": u"Лиззи Магуайр / The Lizzie McGuire Movie",
        u"comments": 2,
        u"advert": False,
        u"imdb_votes": 30319,
        u"subtype": "",
        u"type": u"movie",
        u"views": 31,
        u"director": u"Джим Фолл",
        u"finished": False,
        u"posters": {
            u"small": u"https://example.com/small/8086.jpg",
            u"big": u"https://example.com/big/8086.jpg",
            u"medium": u"https://example.com/medium/8086.jpg"
        },
        u"langs": 3,
        u"kinopoisk_votes": 8307,
        u"rating_votes": u"7",
        u"subtitles": u"0",
        u"kinopoisk_rating": 6.322,
        u"countries": [
            {
                u"id": 1,
                u"title": u"США"
            }
        ],
        u"tracklist": [],
        u"rating_percentage": u"71.43",
        u"cast": u"Хилари Дафф, Адам Лэмберг, Халли Морган, Роберт Кэрредин, Джейк Томас, Эшли Брилло, Клэйтон Снайдер, Алекс Борштейн, Яни Гельман, Брендан Келли, Карли Шредер, Дэниэл Эскобар, Джоди Расикот, Питер Келамис, Терра С. Маклеод",
        u"poor_quality": False,
        u"imdb_rating": 5.4,
        u"voice": "",
        u"trailer": {
            u"url": u"http://www.youtube.com/watch?v=eIm8g4IA_1Y",
            u"id": u"eIm8g4IA_1Y"
        }
    }
}


actionItems_response = {
    u"status": 200,
    u"items": [
        {
            u"rating": 0,
            u"imdb": 7544820,
            u"year": 2017,
            u"duration": {
                u"average": 5946,
                u"total": 5946
            },
            u"quality": 720,
            u"id": 35431,
            u"kinopoisk": 726439,
            u"plot": u"Авторы, участники и продюсеры рассказывают о создании Шоу Дана Карви. Неприемлемые для аудитории праймтайма ЭйБиСи отрывки и образы, продержались в эфире всего 8 выпусков, но открыли миру команду талантливых актеров, сценаристов, писателей и продюсеров.",
            u"genres": [
                {
                    u"id": 82,
                    u"title": u"Кино"
                }
            ],
            u"title": u"Слишком смешные, чтобы провалиться. Жизнь и смерть шоу Дана Карви / Too Funny to Fail: The Life & Death of The Dana Carvey Show",
            u"comments": 0,
            u"advert": True,
            u"imdb_votes": 694,
            u"subtype": "",
            u"type": u"documovie",
            u"views": 0,
            u"director": u"Джош Гринбаум",
            u"finished": False,
            u"posters": {
                u"small": u"https://example.com/small/35431.jpg",
                u"big": u"https://example.com/big/35431.jpg",
                u"medium": u"https://example.com/medium/35431.jpg"
            },
            u"langs": 1,
            u"kinopoisk_votes": 25,
            u"rating_votes": u"0",
            u"subtitles": u"0",
            u"kinopoisk_rating": 0,
            u"countries": [
                {
                    u"id": 1,
                    u"title": u"США"
                }
            ],
            u"tracklist": [],
            u"rating_percentage": u"0",
            u"cast": "",
            u"poor_quality": False,
            u"imdb_rating": 7.3,
            u"voice": None,
            u"trailer": None
        },
        {
            u"rating": 0,
            u"imdb": None,
            u"year": 2018,
            u"duration": {
                u"average": 5606,
                u"total": 5606
            },
            u"quality": 1080,
            u"id": 35584,
            u"kinopoisk": 1181557,
            u"plot": u"Детство вспоминается беспечным отрезком жизни лишь с\xa0высоты прожитых лет.. Но\xa0для детей это\xa0время, когда они\xa0впервые сталкиваются с\xa0ответственностью, принимают решения, учатся признавать ошибки, прощать, любить. Киноальманах 11+ подходит для\xa0просмотра всей семьёй. Порой бывает сложно рассказать своим детям о\xa0чем-то важном для\xa0себя и\xa0для них. В\xa0сборник короткометражек \xab11+\xbb вошли три\xa0очень разных фильма, которые помогут пережить важный опыт взросления, почувствовать то, о\xa0чем сложно сказать.",
            u"genres": [
                {
                    u"id": 1,
                    u"title": u"Комедия"
                },
                {
                    u"id": 6,
                    u"title": u"Семейный"
                },
                {
                    u"id": 10,
                    u"title": u"Мелодрама"
                }
            ],
            u"title": u"11+",
            u"comments": 0,
            u"advert": True,
            u"imdb_votes": None,
            u"subtype": "",
            u"type": u"movie",
            u"views": 0,
            u"director": u"Мария Сопова",
            u"finished": False,
            u"posters": {
                u"small": u"https://example.com/small/35584.jpg",
                u"big": u"https://example.com/big/35584.jpg",
                u"medium": u"https://example.com/medium/35584.jpg"
            },
            u"langs": 1,
            u"kinopoisk_votes": 0,
            u"rating_votes": u"0",
            u"subtitles": u"0",
            u"kinopoisk_rating": 0,
            u"countries": [
                {
                    u"id": 2,
                    u"title": u"Россия"
                }
            ],
            u"tracklist": [],
            u"rating_percentage": u"0",
            u"cast": u"Александр Алёшкин, Елена Лямина, Михаил Новоженин, Дмитрий Белоцерковский, Татьяна Плетнева, Сергей Новоженин, Дарья Хитарова, Ксения Голубева, Никита Любимов, Полина Тарасова",
            u"poor_quality": False,
            u"imdb_rating": 0,
            u"voice": None,
            u"trailer": None
        },
        {
            u"rating": 9,
            u"imdb": None,
            u"year": 2011,
            u"duration": {
                u"average": 2838.287598944591,
                u"total": 1075711
            },
            u"quality": 480,
            u"id": 16015,
            u"kinopoisk": 762373,
            u"plot": u"Каждые выходные двое ведущих отправляются в различные города мира. По правилам программы один ведущий должен прожить субботу и воскресенье на 100 долларов, а второй может тратить неограниченные средства, которые хранятся на золотой карте. Чтобы решить, кто из них будет жить как миллионер, а кто будет учиться выживанию, ведущие перед каждым путешествиям бросают монету, и каждый раз всё решает Орёл или решка.",
            u"genres": [
                {
                    u"id": 112,
                    u"title": u"Путешествия"
                }
            ],
            u"subscribed": False,
            u"title": u"Орёл и решка",
            u"comments": 1,
            u"in_watchlist": False,
            u"advert": False,
            u"imdb_votes": 59,
            u"subtype": "",
            u"type": u"tvshow",
            u"views": 63612,
            u"director": "",
            u"finished": False,
            u"posters": {
                u"small": u"https://example.com/small/16015.jpg",
                u"big": u"https://example.com/big/16015.jpg",
                u"medium": u"https://example.com/medium/16015.jpg"
            },
            u"langs": 381,
            u"kinopoisk_votes": 19205,
            u"rating_votes": u"13",
            u"subtitles": u"0",
            u"kinopoisk_rating": 8.323,
            u"countries": [
                {
                    u"id": 23,
                    u"title": u"Украина"
                }
            ],
            u"tracklist": [],
            u"rating_percentage": u"84.62",
            u"cast": u"Андрей Бедняков, Алан Бадоев, Жанна Бадоева, Анастасия Короткая, Леся Никитюк, Николай Серга, Регина Тодоренко, Евгений Синельников",
            u"poor_quality": False,
            u"imdb_rating": 8.4,
            u"voice": None,
            u"trailer": None
        },
        {
            u"rating": 13,
            u"imdb": 3314218,
            u"year": 2015,
            u"duration": {
                u"average": 2518.5,
                u"total": 95703
            },
            u"quality": 480,
            u"id": 10892,
            u"kinopoisk": 807444,
            u"plot": u"Настоящий хаос окружает съемки любовных реалити-шоу. За кулисами может оказаться всё гораздо интереснее, чем в эфире. В погоне за рейтингами приходится всячески манипулировать конкурсантами, чтобы те выдали необходимый \xabматериал\xbb для шоу. А продюсер может уволить кого угодно за малейший недочёт.",
            u"genres": [
                {
                    u"id": 9,
                    u"title": u"Драма"
                }
            ],
            u"subscribed": False,
            u"title": u"Нереально / UnREAL",
            u"comments": 5,
            u"in_watchlist": False,
            u"advert": True,
            u"imdb_votes": 11148,
            u"subtype": "",
            u"type": u"serial",
            u"views": 6921,
            u"director": u"Питер О’Фаллон, Ута Бризвитц, Лев Л. Спиро, Питер Уэрнер, Адам Кэйн, Дэвид Соломон, Шири Эпплби, Дженис Кук-Леонард, Сара Шапиро, Зинга Стюарт",
            u"finished": False,
            u"posters": {
                u"small": u"https://example.com/small/10892.jpg",
                u"big": u"https://example.com/big/10892.jpg",
                u"medium": u"https://example.com/medium/10892.jpg"
            },
            u"langs": 84,
            u"kinopoisk_votes": 1634,
            u"rating_votes": u"15",
            u"subtitles": u"0",
            u"kinopoisk_rating": 7.292,
            u"countries": [
                {
                    u"id": 1,
                    u"title": u"США"
                }
            ],
            u"tracklist": [],
            u"rating_percentage": u"93.33",
            u"cast": u"Шири Эпплби, Констанс Зиммер, Крэйг Бирко, Джеффри Бауэр-Чепман, Джош Келли, Бреннан Эллиотт, Женевьев Бюкнер, Эми Хилл, Фредди Строма, Моника Барбаро, Джоанна Э. Брэдди, Б.Дж. Бритт, Натали Келли, Кимберли Матула, Майкл Рэди",
            u"poor_quality": False,
            u"imdb_rating": 7.9,
            u"voice": u"Gears Media, IdeaFilm (3,4 сезон)",
            u"trailer": None
        },
         {
            u"rating": 0,
            u"imdb": None,
            u"year": 2003,
            u"duration": {
                u"average": 1832,
                u"total": 9160
            },
            u"quality": 480,
            u"id": 35590,
            u"kinopoisk": None,
            u"plot": u"Тысячи лет природа и сам человек создавали и разрушали целые культуры и цивилизации. Многое из того, что веками олицетворяло собой облик земной расы, ушло безвозвратно или породило множество тайн и загадок, обросших невероятным количеством легенд и преданий. Многие поколения археологов, историков и просто ловцов удачи пытаются на свой страх и риск найти и раскрыть некоторые из них.",
            u"genres": [
                {
                    u"id": 51,
                    u"title": u"История"
                }
            ],
            u"subscribed": False,
            u"title": u"Античные секреты / The Travel Channel. Ancient Secrets",
            u"comments": 0,
            u"in_watchlist": False,
            u"advert": False,
            u"imdb_votes": None,
            u"subtype": "",
            u"type": u"docuserial",
            u"views": 17,
            u"director": u"Энн Кэролл, Джозеф Хиннеген, Марк Мастерс",
            u"finished": True,
            u"posters": {
                u"small": u"https://example.com/small/35590.jpg",
                u"big": u"https://example.com/big/35590.jpg",
                u"medium": u"https://example.com/medium/35590.jpg"
            },
            u"langs": 3,
            u"kinopoisk_votes": None,
            u"rating_votes": u"0",
            u"subtitles": u"0",
            u"kinopoisk_rating": None,
            u"countries": [
                {
                    u"id": 1,
                    u"title": u"США"
                }
            ],
            u"tracklist": [],
            u"rating_percentage": u"0",
            u"cast": "",
            u"poor_quality": False,
            u"imdb_rating": None,
            u"voice": None,
            u"trailer": None
        },
    ],
    u"pagination": {
        u"current": 1,
        u"total_items": 27979,
        u"total": 1399,
        u"perpage": 20
    }
}


actionView_seasons_response = {
    u"status": 200,
    u"item": {
        u"rating": 11,
        u"seasons": [
            {
                u"episodes": [
                    {
                        u"files": [
                            {
                                u"url": {
                                    u"hls": u"https://example.com/hls/480p",
                                    u"hls2": u"https://example.com/hls2/480p",
                                    u"http": u"https://example.com/http/480p",
                                    u"hls4": u"https://example.com/hls4/480p"
                                },
                                u"h": 406,
                                u"quality": u"480p",
                                u"w": 720
                            },
                            {
                                u"url": {
                                    u"hls": u"https://example.com/hls/720p",
                                    u"hls2": u"https://example.com/hls2/720p",
                                    u"http": u"https://example.com/http/720p",
                                    u"hls4": u"https://example.com/hls4/720p"
                                },
                                u"h": 406,
                                u"quality": u"720p",
                                u"w": 960
                            }
                        ],
                        u"title": u"Большой взрыв",
                        u"watching": {
                            u"status": -1,
                            u"time": 0
                        },
                        u"number": 2,
                        u"id": 128671,
                        u"ac3": 0,
                        u"tracks": 1,
                        u"duration": 2628,
                        u"watched": -1,
                        u"thumbnail": u"https://example.com/480x270.jpg",
                        u"subtitles": []
                    }
                ],
                u"watching": {
                    u"status": -1
                },
                u"number": 1,
                u"title": u"1 сезон"
            }
        ],
        u"imdb": 1832668,
        u"year": 2010,
        u"duration": {
            u"average": 2601.9166666666665,
            u"total": 124892
        },
        u"bookmarks": [],
        u"ac3": 0,
        u"quality": 480,
        u"id": 9475,
        u"kinopoisk": 615680,
        u"plot": u"Это история о создании всего в этом мире. Программа исследует, как Вселенная возникла из ничего, и как она выросла с точки незначительно меньше, чем атомные частицы, до огромного космоса.",
        u"genres": [
            {
                u"id": 60,
                u"title": u"Космос"
            },
            {
                u"id": 81,
                u"title": u"Вселенная"
            }
        ],
        u"subscribed": False,
        u"title": u"Как устроена Вселенная / How the Universe Works",
        u"comments": 0,
        u"in_watchlist": False,
        u"advert": False,
        u"imdb_votes": 4238,
        u"subtype": u"",
        u"type": u"docuserial",
        u"views": 3213,
        u"director": u"Адам Уорнер, Питер Чинн, Луиз Сай, Лорни Тауненд, Шон Тревисик, Кейт Дарт, Джордж Харрис, Алекс Хирл",
        u"finished": False,
        u"posters": {
            u"small": u"https://example.com/small/9475.jpg",
            u"big": u"https://example.com/big/9475.jpg",
            u"medium": u"https://example.com/medium/9475.jpg"
        },
        u"langs": 49,
        u"kinopoisk_votes": 2848,
        u"rating_votes": u"13",
        u"subtitles": u"",
        u"kinopoisk_rating": 8.739,
        u"countries": [
            {
                u"id": 1,
                u"title": u"США"
            }
        ],
        u"tracklist": [],
        u"rating_percentage": u"92.31",
        u"cast": u"Фил Плейт, Майк Роу, Мишель Таллер, Лоуренс Краусс, Мичио Каку, Ричард Линтерн, Дэн Дарда, Джофф Марси, Эрик Деллумс, Крис МакКэй, Дэвид Гринспун, Алекс Филиппенко, Дэвид Спергел, Питер Шульц, Шон Кэрролл",
        u"poor_quality": False,
        u"imdb_rating": 9,
        u"voice": u"",
        u"trailer": None
    }
}

actionView_without_seasons_response = {
    u"status": 200,
    u"item": {
        u"rating": 1,
        u"videos": [
            {
                u"files": [
                    {
                        u"url": {
                            u"hls": u"https://example.com/hls/480",
                            u"hls2": u"https://example.com/hls2/480",
                            u"http": u"https://example.com/http/480",
                            u"hls4": u"https://example.com/hls4/480"
                        },
                        u"h": 400,
                        u"quality": u"480p",
                        u"w": 720
                    }
                ],
                u"title": u"От пещерных людей до королей",
                u"watching": {
                    u"status": -1,
                    u"time": 0
                },
                u"number": 1,
                u"id": 520081,
                u"ac3": 0,
                u"tracks": 1,
                u"duration": 2635,
                u"watched": -1,
                u"thumbnail": u"https://example.com/480x270.jpg",
                u"subtitles": []
            },
            {
                u"files": [
                    {
                        u"url": {
                            u"hls": u"https://example.com/hls/480",
                            u"hls2": u"https://example.com/hls2/480",
                            u"http": u"https://example.com/http/480",
                            u"hls4": u"https://example.com/hls4/480"
                        },
                        u"h": 400,
                        u"quality": u"480p",
                        u"w": 720
                    }
                ],
                u"title": u"Яблоко раздора",
                u"watching": {
                    u"status": -1,
                    u"time": 0
                },
                u"number": 2,
                u"id": 520078,
                u"ac3": 0,
                u"tracks": 1,
                u"duration": 2615,
                u"watched": -1,
                u"thumbnail": u"https://example.com/480x270.jpg",
                u"subtitles": []
            }
        ],
        u"imdb": 5848928,
        u"year": 2016,
        u"duration": {
            u"average": 5250,
            u"total": 5250
        },
        u"bookmarks": [],
        u"ac3": 0,
        u"quality": 480,
        u"id": 35467,
        u"kinopoisk": None,
        u"plot": u"Это были удивительные люди, рождённые белыми скалами и синем морем. Они изобрели демократию, отделили логику от разума, они передали глубочайшие душевные переживания в своих драмах, а совершенство человеческого тела - в спорте и искусствах. Греки - это люди, которые создали наш мир.",
        u"genres": [
            {
                u"id": 51,
                u"title": u"История"
            }
        ],
        u"title": u"NG: Древние греки / The Greeks",
        u"comments": 0,
        u"advert": False,
        u"imdb_votes": None,
        u"subtype": u"multi",
        u"type": u"documovie",
        u"views": 41,
        u"director": u"Кэтрин Еллоз",
        u"finished": False,
        u"posters": {
            u"small": u"https://example.com/small/35467.jpg",
            u"big": u"https://example.com/big/35467.jpg",
            u"medium": u"https://example.com/medium/35467.jpg"
        },
        u"langs": 2,
        u"kinopoisk_votes": None,
        u"rating_votes": u"1",
        u"subtitles": u"0",
        u"kinopoisk_rating": None,
        u"countries": [
            {
                u"id": 1,
                u"title": u"США"
            }
        ],
        u"tracklist": [],
        u"rating_percentage": u"100",
        u"cast": u"Беттани Хьюз",
        u"poor_quality": False,
        u"imdb_rating": None,
        u"voice": None,
        u"trailer": None
    }
}


watching_info_response_with_seasons = {
    u"status": 200,
    u"item": {
        u"watched": 0,
        u"seasons": [
            {
                u"status": -1,
                u"watched": 0,
                u"episodes": [
                    {
                        u"status": -1,
                        u"updated": None,
                        u"title": "\u0411\u043e\u043b\u044c\u0448\u043e\u0439 \u0432\u0437\u0440\u044b\u0432",
                        u"number": 2,
                        u"time": 0,
                        u"duration": 2628,
                        u"id": 128671
                    }
                ],
                u"id": 1147,
                u"number": 1
            }
        ],
        u"type": u"docuserial",
        u"id": 9475,
        u"title": "\u041a\u0430\u043a \u0443\u0441\u0442\u0440\u043e\u0435\u043d\u0430 \u0412\u0441\u0435\u043b\u0435\u043d\u043d\u0430\u044f / How the Universe Works"
    }
}

watching_info_response_without_seasons = {
    u"status": 200,
    u"item": {
        u"status": -1,
        u"type": u"documovie",
        u"id": 35467,
        u"videos": [
            {
                u"status": -1,
                u"updated": u"None",
                u"title": "\u041e\u0442 \u043f\u0435\u0449\u0435\u0440\u043d\u044b\u0445 \u043b\u044e\u0434\u0435\u0439 \u0434\u043e \u043a\u043e\u0440\u043e\u043b\u0435\u0439",
                u"number": 1,
                u"time": 0,
                u"duration": 2635,
                u"id": 520081
            },
            {
                u"status": -1,
                u"updated": u"None",
                u"title": "\u042f\u0431\u043b\u043e\u043a\u043e \u0440\u0430\u0437\u0434\u043e\u0440\u0430",
                u"number": 2,
                u"time": 0,
                u"duration": 2615,
                u"id": 520078
            }
        ],
        u"title": u"NG: \u0414\u0440\u0435\u0432\u043d\u0438\u0435 \u0433\u0440\u0435\u043a\u0438 / The Greeks"
    }
}