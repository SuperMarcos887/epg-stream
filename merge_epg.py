import gzip
import os
import re
import shutil
import tempfile
import requests
import xml.etree.ElementTree as ET

# ==============================================================================
# 1. LE 20 SORGENTI EPG COMPLETE
# ==============================================================================
EPG_URLS = [
    # Nazionali e Sky Sport Italia / Cinema / DAZN
    "http://epg-guide.com/wltv.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_IT1.xml.gz",
    # Sky Sport Germania & Austria 1-8
    "https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz",
    # Canal+ Sport 1-8 CZ & Sport 1-2 CZ
    "https://epgshare01.online/epgshare01/epg_ripper_CZ1.xml.gz",
    # Nova Sport 1-6 HD & Canal+ Sport SK (Slovacchia)
    "https://epgshare01.online/epgshare01/epg_ripper_SK1.xml.gz",
    # Match! Canali Sport Russia
    "https://epgshare01.online/epgshare01/epg_ripper_UA1.xml.gz",
    # Eleven Sports 1-4 PL & Canal+ Sport PL
    "https://epgshare01.online/epgshare01/epg_ripper_PL1.xml.gz",
    # Setanta Sports 1 & 2 HD (Lettonia / Baltici)
    "https://epgshare01.online/epgshare01/epg_ripper_LV1.xml.gz",
    # Arena Sport Premium 1 e Arena Sport 2-5 (Bosnia / Serbia)
    "https://epgshare01.online/epgshare01/epg_ripper_RS1.xml.gz",
    # Abu Dhabi Sports 1 & 2 HD
    "https://epgshare01.online/epgshare01/epg_ripper_AE1.xml.gz",
    # Arena Sport 1-10 HR (Croazia)
    "https://epgshare01.online/epgshare01/epg_ripper_HR1.xml.gz",
    # Svizzera RSI LA 1-2
    "https://epgshare01.online/epgshare01/epg_ripper_CH1.xml.gz",
    # ESPN 1-6 Brasile
    "https://epgshare01.online/epgshare01/epg_ripper_BR1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_BR2.xml.gz",
    # ESPN 1-4 Messico
    "https://epgshare01.online/epgshare01/epg_ripper_MX1.xml.gz",
    # TNT Sports 1-4 UK/Irlanda
    "https://epgshare01.online/epgshare01/epg_ripper_IE1.xml.gz",
    # Sport TV 1-7 Portogallo & Eleven Sports PT
    "https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz",
    # USA: CBS Golazo Network, Fox Deportes HD, Fox Sports 4K
    "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz",
    # beIN Sports 1-3 Australia
    "https://epgshare01.online/epgshare01/epg_ripper_AU1.xml.gz",
    # SPOTV 1-2 Filippine
    "https://epgshare01.online/epgshare01/epg_ripper_PH1.xml.gz",
]

# ==============================================================================
# 2. TARGET IDS (Tutti i tvg-id usati in canali.m3u e nelle varianti ammesse)
# ==============================================================================
TARGET_IDS = {
    # Abu Dhabi Sports
    "AD.Sports.1.HD.ae", "AD.Sports.2.HD.ae",

    # Setanta Sports Baltici
    "Setanta.Sports.1.HD.lv", "Setanta.Sports.2.HD.lv",

    # Arena Sport Bosnia / Serbia
    "Arena.PREMIUM.1.rs", "Arena.Sport.2.rs", "Arena.Sport.3.rs", "Arena.Sport.4.rs", "Arena.Sport.5.rs",

    # Arena Sport Croazia
    "Arena.Sport.1.HD.hr", "Arena.Sport.2.HD.hr", "Arena.Sport.3.HD.hr", "Arena.Sport.4.HD.hr",
    "Arena.Sport.5.HD.hr", "Arena.Sport.6.HD.hr", "Arena.Sport.7.HD.hr", "Arena.Sport.8.HD.hr",
    "Arena.Sport.9.HD.hr", "Arena.Sport.10.HD.hr",

    # Canal+ Sport CZ & SK & Sport 1-2 CZ
    "Canal+.Sport.cz", "Canal+.Sport.2.cz", "Canal+.Sport.3.cz", "Canal+.Sport.4.cz",
    "Canal+.Sport.5.cz", "Canal+.Sport.6.cz", "Canal+.Sport.7.cz", "Canal+.Sport.8.cz",
    "CANAL+.Sport.HD.sk", "CANAL+.Sport.4.HD.sk", "CANAL+.Sport.5.HD.sk",
    "CANAL+.Sport.6.HD.sk", "CANAL+.Sport.7.HD.sk", "CANAL+.Sport.8.HD.sk",
    "Sport1.cz", "Sport2.cz",

    # Nova Sport 1-6 HD
    "Nova.Sport.1.HD.sk", "Nova.Sport.2.HD.sk", "Nova.Sport.3.HD.sk",
    "Nova.Sport.4.HD.sk", "Nova.Sport.5.HD.sk", "Nova.Sport.6.HD.sk",

    # Match! Sport Russia
    "Match.TV.ru", "Match.Futbol.1.ru", "Match.Futbol.2.ru", "Match.Futbol.3.ru",
    "Match.Arena.ru", "Match.Premier.ru", "Match.Fight.ru",

    # Eleven Sports PL
    "Eleven.Sports.1.HD.pl", "Eleven.Sports.2.HD.pl", "Eleven.Sports.3.HD.pl", "Eleven.Sports.4.HD.pl",

    # Sky Sport Austria
    "Sky.Sport.Austria.1.HD.de", "Sky.Sport.Austria.2.HD.de", "Sky.Sport.Austria.3.HD.de", "Sky.Sport.Austria.4.HD.de",
    "Sky.Sport.Austria.5.HD.de", "Sky.Sport.Austria.6.HD.de", "Sky.Sport.Austria.7.HD.de", "Sky.Sport.Austria.8.HD.de",

    # Sky Sport Germania (sia formato con HD che senza HD per canali.m3u)
    "Sky.Sport.1.de", "Sky.Sport.2.de", "Sky.Sport.3.de", "Sky.Sport.4.de", "Sky.Sport.5.de",
    "Sky.Sport.6.de", "Sky.Sport.7.de", "Sky.Sport.8.de", "Sky.Sport.9.de", "Sky.Sport.10.de",
    "Sky.Sport.Top.Event.de", "Sky.Sport.Bundesliga.HD.de", "Sky.Sport.Bundesliga.1.HD.de",
    "Sky.Sport.Bundesliga.2.HD.de", "Sky.Sport.Bundesliga.3.HD.de", "Sky.Sport.Bundesliga.4.HD.de",
    "Sky.Sport.Bundesliga.5.HD.de",
    "Sky.Sport.Premier.League.HD.de", "Sky.Sport.Premier.League.de",
    "Sky.Sport.Mix.HD.de", "Sky.Sport.Mix.de",
    "Sky.Sport.Tennis.HD.de", "Sky.Sport.Tennis.de",
    "Sky.Sport.F1.HD.de", "Sky.Sport.F1.de",
    "Sky.Sport.News.de",

    # Portogallo Sport TV & DAZN PT (Eleven)
    "SPORT.TV1.HD.pt", "SPORT.TV2.HD.pt", "SPORT.TV3.HD.pt", "SPORT.TV4.HD.pt",
    "SPORT.TV5.HD.pt", "Sport.TV.6.HD.pt", "Sport.TV.7.HD.pt", "SPORT.TV+.HD.pt",
    "Sport.TV.1.pt", "Sport.TV.2.pt", "Sport.TV.3.pt", "Sport.TV.4.pt",
    "Sport.TV.5.pt", "Sport.TV.6.pt", "Sport.TV.7.pt",
    "DAZN.1.pt", "DAZN.2.pt", "DAZN.3.pt", "DAZN.4.pt", "DAZN.5.pt", "DAZN.6.pt",
    "eleven-sport1-pt", "eleven-sport2-pt", "eleven-sport3-pt", "eleven-sport4-pt", "eleven-sport5-pt", "eleven-sport6-pt",

    # Svizzera
    "RSI.La.1.ch", "RSI.La.2.ch", "RSI.LA.2.ch",

    # ESPN Brasile & Fox Sports
    "ESPN.br", "ESPN.2.br", "ESPN.3.br", "ESPN.4.br", "ESPN.5.br", "ESPN.6.br", "Fox.Sports.2.br",

    # ESPN Messico
    "ESPN.mx", "ESPN.MX.mx", "ESPN.2.mx", "ESPN.3.mx", "ESPN.4.mx",

    # TNT Sports UK / Irlanda
    "TNT.Sports.1.uk", "TNT.Sports.2.uk", "TNT.Sports.3.uk", "TNT.Sports.4.uk", "TNT.Sports.Ultimate.uk",
    "TNT.Sports.1.HD.ie", "TNT.Sports.2.HD.ie", "TNT.Sports.3.HD.ie", "TNT.Sports.4.HD.ie",

    # USA Sports
    "CBS.Sports.Golazo.Network.us", "CBS.Sports.Golazo.Network.us2",
    "Fox.Deportes.us", "Fox.Deportes.HD.us2",
    "Fox.Sports.1.us", "Fox.Sports.2.us", "Fox.Sports.4K.us2",

    # Australia beIN Sports
    "beIN.Sports.1.au", "beIN.Sports.2.au", "beIN.Sports.3.au",
    "beINSports1.au", "beINSports2.au", "beINSports3.au",

    # SPOTV Filippine
    "SPOTV.ph", "SPOTV.2.ph",

    # Sky Sport Italia & DAZN Italia (sia variante con singolo punto che doppio punto)
    "Sky.Sport.24.it", "Sky.Sport.Uno.it", "Sky.Sport.Calcio.it", "Sky.Sport.F1.it",
    "Sky.Sport.MotoGP.it", "Sky.Sport.Tennis.it", "Sky.Sport.Arena.it", "Sky.Sport.Max.it",
    "Sky.Sport.Golf.it", "Sky.Sport.Plus.it",
    "Sky.Sport.251.it", "Sky.Sport..251.it",
    "Sky.Sport.252.it", "Sky.Sport..252.it",
    "Sky.Sport.253.it", "Sky.Sport..253.it",
    "Sky.Sport.254.it", "Sky.Sport..254.it",
    "Sky.Sport.255.it", "Sky.Sport..255.it",
    "Sky.Sport.256.it", "Sky.Sport..256.it",
    "Sky.Sport.257.it", "Sky.Sport..257.it",
    "Sky.Sport.258.it", "Sky.Sport..258.it",
    "Sky.Sport.259.it", "Sky.Sport..259.it",
    "Sky.Sport.260.it", "Sky.Sport..260.it",
    "Sky.Sport.261.it", "Sky.Sport..261.it",
    "DAZN.1.it.it", "DAZN.2.it.it",
    "Milan.TV.it", "Inter.TV.it", "inter-it",

    # Sky Intrattenimento & Cinema Italia
    "Sky.Uno.it", "Sky.Atlantic.it", "Sky.Serie.it", "Sky.Investigation.it",
    "Sky.Arte.it", "Sky.Documentaries.it", "Sky.Nature.it",
    "Sky.Cinema.Uno.it", "Sky.Cinema.Uno.24.it", "Sky.Cinema.Uno.+24.it",
    "Sky.Cinema.Due.it", "Sky.Cinema.Collection.it", "Sky.Cinema.Family.it",
    "Sky.Cinema.Action.it", "Sky.Cinema.Suspense.it", "Sky.Cinema.Romance.it",
    "Sky.Cinema.Drama.it", "Sky.Cinema.Comedy.it",

    # Canali Nazionali Italia
    "Rai1.it", "Rai2.it", "Rai3.it", "Rete4.it", "Canale5.it", "Italia1.it",
    "la7", "Tv8.it", "Nove.it", "20Mediaset.it", "Rai4.it", "Iris.it",
    "RaiMovie.it", "RaiPremium.it", "Cielo.it", "TwentySeven.it", "La5.it",
    "RealTime.it", "QVC.it", "Rai5.it", "MediasetItalia2.it", "MediasetExtra.it",
    "DMAX.it", "RaiStoria.it", "RaiScuola.it", "RaiSport.it", "Supertennis.it",
    "Focus.it", "TopCrime.it", "Giallo.it", "Boing.it", "K2.it", "RaiGulp.it",
    "RaiYoyo.it", "Frisbee.it", "Cartoonito.it", "Super.it", "TgCom24.it",
    "RaiNews24.it", "SkyTG24.it", "Cine34.it", "MotorTrend.it",
}

# ==============================================================================
# 3. ID MAPPING (Mappa gli ID delle 20 fonti verso i target di canali.m3u)
# ==============================================================================
ID_MAPPING = {
    # --- CANALI NAZIONALI ITALIA (da wltv.gz e IT1) ---
    "rete4": ["Rete4.it"],
    "canale5": ["Canale5.it"],
    "italia1": ["Italia1.it"],
    "tv8": ["Tv8.it"],
    "TV8.HD.it": ["Tv8.it"],
    "cielo": ["Cielo.it"],
    "nove": ["Nove.it"],
    "italia2": ["MediasetItalia2.it"],
    "rai1": ["Rai1.it"],
    "rai2": ["Rai2.it"],
    "rai3": ["Rai3.it"],
    "rai4": ["Rai4.it"],
    "rai5": ["Rai5.it"],
    "raigulp": ["RaiGulp.it"],
    "raimovie": ["RaiMovie.it"],
    "rainews24": ["RaiNews24.it"],
    "raipremium": ["RaiPremium.it"],
    "raiscuola": ["RaiScuola.it"],
    "raisport": ["RaiSport.it"],
    "raistoria": ["RaiStoria.it"],
    "raiyoyo": ["RaiYoyo.it"],
    "skytg24": ["SkyTG24.it"],
    "la7": ["la7"],
    "LA7.it": ["la7"],

    # --- SVIZZERA RSI LA 1-2 (da CH1) ---
    "RSI.LA.2.ch": ["RSI.LA.2.ch", "RSI.La.2.ch"],
    "RSI.La.2.ch": ["RSI.LA.2.ch", "RSI.La.2.ch"],
    "RSI.La.1.ch": ["RSI.La.1.ch"],

    # --- SKY SPORT CALCIO / CANALI 251-261 (da IT1 con doppio punto) ---
    "Sky.Sport..251.it": ["Sky.Sport..251.it", "Sky.Sport.251.it"],
    "Sky.Sport.251.it": ["Sky.Sport..251.it", "Sky.Sport.251.it"],
    "Sky.Sport..252.it": ["Sky.Sport..252.it", "Sky.Sport.252.it"],
    "Sky.Sport.252.it": ["Sky.Sport..252.it", "Sky.Sport.252.it"],
    "Sky.Sport..253.it": ["Sky.Sport..253.it", "Sky.Sport.253.it"],
    "Sky.Sport.253.it": ["Sky.Sport..253.it", "Sky.Sport.253.it"],
    "Sky.Sport..254.it": ["Sky.Sport..254.it", "Sky.Sport.254.it"],
    "Sky.Sport.254.it": ["Sky.Sport..254.it", "Sky.Sport.254.it"],
    "Sky.Sport..255.it": ["Sky.Sport..255.it", "Sky.Sport.255.it"],
    "Sky.Sport.255.it": ["Sky.Sport..255.it", "Sky.Sport.255.it"],
    "Sky.Sport..256.it": ["Sky.Sport..256.it", "Sky.Sport.256.it"],
    "Sky.Sport.256.it": ["Sky.Sport..256.it", "Sky.Sport.256.it"],
    "Sky.Sport..257.it": ["Sky.Sport..257.it", "Sky.Sport.257.it"],
    "Sky.Sport.257.it": ["Sky.Sport..257.it", "Sky.Sport.257.it"],
    "Sky.Sport..258.it": ["Sky.Sport..258.it", "Sky.Sport.258.it"],
    "Sky.Sport.258.it": ["Sky.Sport..258.it", "Sky.Sport.258.it"],
    "Sky.Sport..259.it": ["Sky.Sport..259.it", "Sky.Sport.259.it"],
    "Sky.Sport.259.it": ["Sky.Sport..259.it", "Sky.Sport.259.it"],
    "Sky.Calcio.10..260.it": ["Sky.Sport..260.it", "Sky.Sport.260.it"],
    "Sky.Calcio.11..261.it": ["Sky.Sport..261.it", "Sky.Sport.261.it"],

    # --- MILAN TV, INTER TV & SKY CINEMA UNO +24 ---
    "Inter.TV.it": ["Inter.TV.it", "inter-it"],
    "inter-it": ["inter-it", "Inter.TV.it"],
    "Milan.TV.it": ["Milan.TV.it"],
    "Sky.Cinema.Uno.+24.it": ["Sky.Cinema.Uno.+24.it", "Sky.Cinema.Uno.24.it"],

    # --- BEIN SPORTS AUSTRALIA (da AU1) ---
    "beINSports1.au": ["beINSports1.au", "beIN.Sports.1.au"],
    "beINSports2.au": ["beINSports2.au", "beIN.Sports.2.au"],
    "beINSports3.au": ["beINSports3.au", "beIN.Sports.3.au"],
    "beIN.Sports.1.au": ["beINSports1.au", "beIN.Sports.1.au"],
    "beIN.Sports.2.au": ["beINSports2.au", "beIN.Sports.2.au"],
    "beIN.Sports.3.au": ["beINSports3.au", "beIN.Sports.3.au"],

    # --- USA: GOLAZO & FOX DEPORTES & 4K (da US2) ---
    "CBS.Sports.Golazo.Network.us2": ["CBS.Sports.Golazo.Network.us2", "CBS.Sports.Golazo.Network.us"],
    "CBS.Sports.Golazo.Network.us": ["CBS.Sports.Golazo.Network.us2", "CBS.Sports.Golazo.Network.us"],
    "Fox.Deportes.HD.us2": ["Fox.Deportes.HD.us2", "Fox.Deportes.us"],
    "Fox.Deportes.us": ["Fox.Deportes.HD.us2", "Fox.Deportes.us"],
    "Fox.Sports.4K.us2": ["Fox.Sports.4K.us2"],

    # --- PORTOGALLO SPORT TV & DAZN (ELEVEN) PT (da PT1) ---
    "SPORT.TV1.HD.pt": ["SPORT.TV1.HD.pt", "Sport.TV.1.pt"],
    "SPORT.TV2.HD.pt": ["SPORT.TV2.HD.pt", "Sport.TV.2.pt"],
    "SPORT.TV3.HD.pt": ["SPORT.TV3.HD.pt", "Sport.TV.3.pt"],
    "SPORT.TV4.HD.pt": ["SPORT.TV4.HD.pt", "Sport.TV.4.pt"],
    "SPORT.TV5.HD.pt": ["SPORT.TV5.HD.pt", "Sport.TV.5.pt"],
    "Sport.TV.6.HD.pt": ["Sport.TV.6.HD.pt", "Sport.TV.6.pt"],
    "Sport.TV.7.HD.pt": ["Sport.TV.7.HD.pt", "Sport.TV.7.pt"],
    "SPORT.TV+.HD.pt": ["SPORT.TV+.HD.pt"],
    "DAZN.1.pt": ["DAZN.1.pt", "eleven-sport1-pt"],
    "DAZN.2.pt": ["DAZN.2.pt", "eleven-sport2-pt"],
    "DAZN.3.pt": ["DAZN.3.pt", "eleven-sport3-pt"],
    "DAZN.4.pt": ["DAZN.4.pt", "eleven-sport4-pt"],
    "DAZN.5.pt": ["DAZN.5.pt", "eleven-sport5-pt"],
    "DAZN.6.pt": ["DAZN.6.pt", "eleven-sport6-pt"],

    # --- TNT SPORTS IRLANDA / UK (da IE1) ---
    "TNT.Sports.1.HD.ie": ["TNT.Sports.1.HD.ie", "TNT.Sports.1.uk"],
    "TNT.Sports.2.HD.ie": ["TNT.Sports.2.HD.ie", "TNT.Sports.2.uk"],
    "TNT.Sports.3.HD.ie": ["TNT.Sports.3.HD.ie", "TNT.Sports.3.uk"],
    "TNT.Sports.4.HD.ie": ["TNT.Sports.4.HD.ie", "TNT.Sports.4.uk"],
    "TNT.Sports.1.ie": ["TNT.Sports.1.HD.ie", "TNT.Sports.1.uk"],
    "TNT.Sports.2.ie": ["TNT.Sports.2.HD.ie", "TNT.Sports.2.uk"],
    "TNT.Sports.3.ie": ["TNT.Sports.3.HD.ie", "TNT.Sports.3.uk"],
    "TNT.Sports.4.ie": ["TNT.Sports.4.HD.ie", "TNT.Sports.4.uk"],

    # --- SKY SPORT GERMANIA (da DE1 senza HD) ---
    "Sky.Sport.F1.de": ["Sky.Sport.F1.de", "Sky.Sport.F1.HD.de"],
    "Sky.Sport.Premier.League.de": ["Sky.Sport.Premier.League.de", "Sky.Sport.Premier.League.HD.de"],
    "Sky.Sport.Mix.de": ["Sky.Sport.Mix.de", "Sky.Sport.Mix.HD.de"],
    "Sky.Sport.Tennis.de": ["Sky.Sport.Tennis.de", "Sky.Sport.Tennis.HD.de"],
    "Sky.Sport.News.de": ["Sky.Sport.News.de"],

    # --- CANAL+ SPORT CZ / SK ---
    "CANAL+.Sport.HD.sk": ["CANAL+.Sport.HD.sk", "Canal+.Sport.cz"],
    "CANAL+.Sport.4.HD.sk": ["CANAL+.Sport.4.HD.sk", "Canal+.Sport.4.cz"],
    "CANAL+.Sport.5.HD.sk": ["CANAL+.Sport.5.HD.sk", "Canal+.Sport.5.cz"],
    "CANAL+.Sport.6.HD.sk": ["CANAL+.Sport.6.HD.sk", "Canal+.Sport.6.cz"],
    "CANAL+.Sport.7.HD.sk": ["CANAL+.Sport.7.HD.sk", "Canal+.Sport.7.cz"],
    "CANAL+.Sport.8.HD.sk": ["CANAL+.Sport.8.HD.sk", "Canal+.Sport.8.cz"],
    "Canal+.Sport.cz": ["CANAL+.Sport.HD.sk", "Canal+.Sport.cz"],
    "Canal+.Sport.4.cz": ["CANAL+.Sport.4.HD.sk", "Canal+.Sport.4.cz"],
    "Canal+.Sport.5.cz": ["CANAL+.Sport.5.HD.sk", "Canal+.Sport.5.cz"],
    "Canal+.Sport.6.cz": ["CANAL+.Sport.6.HD.sk", "Canal+.Sport.6.cz"],
    "Canal+.Sport.7.cz": ["CANAL+.Sport.7.HD.sk", "Canal+.Sport.7.cz"],
    "Canal+.Sport.8.cz": ["CANAL+.Sport.8.HD.sk", "Canal+.Sport.8.cz"],

    # --- ESPN MESSICO (da MX1) ---
    "ESPN.MX.mx": ["ESPN.MX.mx", "ESPN.mx"],
    "ESPN.mx": ["ESPN.MX.mx", "ESPN.mx"],

    # --- MATCH TV RUSSIA (da UA1) ---
    "Матч.ТВ.HD.[RU].ua": ["Match.TV.ru"],
    "Матч.ТВ.[RU].ua": ["Match.TV.ru"],
    "Матч!.Футбол.1.HD.[RU].ua": ["Match.Futbol.1.ru"],
    "Матч!.Футбол.1.[RU].ua": ["Match.Futbol.1.ru"],
    "Матч!.Футбол.2.HD.[RU].ua": ["Match.Futbol.2.ru"],
    "Матч!.Футбол.2.[RU].ua": ["Match.Futbol.2.ru"],
    "Матч!.Футбол.3.HD.[RU].ua": ["Match.Futbol.3.ru"],
    "Матч!.Футбол.3.[RU].ua": ["Match.Futbol.3.ru"],
    "Матч!.Арена.HD.[RU].ua": ["Match.Arena.ru"],
    "Матч!.Арена.[RU].ua": ["Match.Arena.ru"],
    "Матч.Премьер.HD.[RU].ua": ["Match.Premier.ru"],
    "Матч.Премьер.[RU].ua": ["Match.Premier.ru"],
    "Матч!.Боец.[RU].ua": ["Match.Fight.ru"],

    # Abu Dhabi Sports
    "en:.Abu.Dhabi.Sports.1.ae": ["AD.Sports.1.HD.ae"],
    "en:.Abu.Dhabi.Sports.2.ae": ["AD.Sports.2.HD.ae"],
    "Abu.Dhabi.Sports.1.ae": ["AD.Sports.1.HD.ae"],
    "Abu.Dhabi.Sports.2.ae": ["AD.Sports.2.HD.ae"],

    # Arena Sport RS
    "Arena.Sport.Premium.1.rs": ["Arena.PREMIUM.1.rs"],
}

DISPLAY_NAMES = {
    "Match.TV.ru": "Match!",
    "Match.Futbol.1.ru": "Match! Futbol 1",
    "Match.Futbol.2.ru": "Match! Futbol 2",
    "Match.Futbol.3.ru": "Match! Futbol 3",
    "Match.Arena.ru": "Match! Arena",
    "Match.Premier.ru": "Match! Premier",
    "Match.Fight.ru": "Match! Fight",
    "Nova.Sport.1.HD.sk": "Nova Sport 1 HD",
    "Nova.Sport.2.HD.sk": "Nova Sport 2 HD",
    "Nova.Sport.3.HD.sk": "Nova Sport 3 HD",
    "Nova.Sport.4.HD.sk": "Nova Sport 4 HD",
    "Nova.Sport.5.HD.sk": "Nova Sport 5 HD",
    "Nova.Sport.6.HD.sk": "Nova Sport 6 HD",
}

# ==============================================================================
# 4. MODULO DI TRADUZIONE RUSSO
# ==============================================================================
RU_TOURNAMENTS = {
    'Альфа-Банк Российская Премьер-Лига': 'Russian Premier League',
    'Российская Премьер-Лига': 'Russian Premier League',
    'Премьер-Лига': 'Premier League',
    'Премьер-лига': 'Premier League',
    'Чемпионат Италии': 'Serie A',
    'Чемпионат Испании': 'LaLiga',
    'Чемпионат Германии': 'Bundesliga',
    'Чемпионат Франции': 'Ligue 1',
    'Чемпионат Португалии': 'Primeira Liga',
    'Чемпионат Бразилии': 'Brasileirão',
    'Чемпионат Турции': 'Süper Lig',
    'Чемпионат России': 'Campionato Russo',
    'Чемпионат Европы': 'Campionati Europei',
    'Чемпионат мира': 'Campionati Mondiali',
    'Лига чемпионов УЕФА': 'UEFA Champions League',
    'Лига чемпионов': 'UEFA Champions League',
    'Лига Европы УЕФА': 'UEFA Europa League',
    'Лига Европы': 'UEFA Europa League',
    'Лига конференций': 'UEFA Conference League',
    'Единая лига ВТБ': 'VTB United League',
    'Кубок России': 'Coppa di Russia',
    'Кубок Италии': 'Coppa Italia',
    'Кубок Испании': 'Copa del Rey',
    'Кубок Сильнейших': 'Coppa dei Campioni',
    'Суперлига': 'Super League',
    'Журнал Серии А': 'Magazine Serie A',
    'Формула-1. Гаснут огни': 'Formula 1: Luci Spente',
}

RU_SPORTS_TERMS = {
    'Прямая трансляция': '🔴 LIVE',
    'Прямой эфир': '🔴 LIVE',
    'Трансляция': 'Diretta',
    'Баскетбол': 'Basket',
    'Волейбол': 'Volley',
    'Велокросс': 'Ciclocross',
    'Бокс голыми кулаками': 'Bare Knuckle Boxing',
    'Бокс': 'Boxe',
    'Художественная гимнастика': 'Ginnastica Ritmica',
    'Смешанные единоборства': 'MMA',
    'Футбол': 'Calcio',
    'Хоккей': 'Hockey',
    'Теннис': 'Tennis',
    'Автоспорт': 'Motorsport',
    'Женщины': 'Donne',
    'Мужчины': 'Uomini',
    'Финальный этап': 'Fase Finale',
    'Группы': 'Gironi',
    'Перед туром': 'Pre-partita',
    'Все на Матч!': 'Tutti su Match!',
    'Д/ф': 'Doc.',
    'Студия': 'Studio',
    'Обзор': 'Highlights',
    'Новости': 'News',
    'против': 'vs',
    'тур': 'Giornata',
    'в Москве': 'a Mosca',
    'в Нидерландах': 'in Olanda',
    'в Ливерпуле, Великобритания': 'a Liverpool (UK)',
    'в Миртл-Бич, США': 'a Myrtle Beach (USA)',
    'в Глазго, Великобритания': 'a Glasgow (UK)',
}

RU_TEAMS = {
    'Аталанта': 'Atalanta', 'Парма': 'Parma', 'Венеция': 'Venezia', 'Удинезе': 'Udinese',
    'Дженоа': 'Genoa', 'Милан': 'Milan', 'Интер': 'Inter', 'Комо 1907': 'Como 1907', 'Комо': 'Como',
    'Наполи': 'Napoli', 'Лацио': 'Lazio', 'Болонья': 'Bologna', 'Рома': 'Roma',
    'Сассуоло': 'Sassuolo', 'Фиорентина': 'Fiorentina', 'Торино': 'Torino', 'Лечче': 'Lecce',
    'Ювентус': 'Juventus', 'Верона': 'Verona', 'Кальяри': 'Cagliari', 'Эмполи': 'Empoli',
    'Монца': 'Monza',
    'Атлетико Мадрид': 'Atlético Madrid', 'Атлетико': 'Atlético Madrid', 'Барселона': 'Barcellona',
    'Валенсия': 'Valencia', 'Реал Мадрид': 'Real Madrid', 'Вильярреал': 'Villarreal',
    'Хетафе': 'Getafe', 'Леванте': 'Levante', 'Малага': 'Málaga', 'Реал Расинг': 'Racing Santander',
    'Осасуна': 'Osasuna', 'Атлетик': 'Athletic Bilbao', 'Реал Сосьедад': 'Real Sociedad',
    'Райо Вальекано': 'Rayo Vallecano', 'Севилья': 'Siviglia', 'Депортиво Алавес': 'Alavés',
    'Алавес': 'Alavés', 'Эльче': 'Elche', 'Реал Бетис': 'Real Betis', 'Бетис': 'Real Betis',
    'Эспаньол': 'Espanyol', 'РК Депортиво Ла-Корунья': 'Deportivo La Coruña',
    'Депортиво': 'Deportivo La Coruña', 'Сельта': 'Celta Vigo', 'Жирона': 'Girona',
    'Мальорка': 'Mallorca', 'Лас-Пальмас': 'Las Palmas', 'Вальядолид': 'Valladolid',
    'Витория Гимарайнш': 'Vitória Guimarães', 'Порту': 'Porto', 'Спортинг': 'Sporting CP',
    'Морейренсе': 'Moreirense', 'Эштрела': 'Estrela Amadora', 'Бенфика': 'Benfica',
    'Брага': 'Braga',
    'Аланьяспор': 'Alanyaspor', 'Трабзонспор': 'Trabzonspor', 'Галатасарай': 'Galatasaray',
    'Амед': 'Amed SK', 'Чорум': 'Çorum FK', 'Фенербахче': 'Fenerbahçe', 'Бешикташ': 'Beşiktaş',
    'Атлетико Паранаэнсе': 'Athletico Paranaense', 'Васко да Гама': 'Vasco da Gama',
    'Витория': 'Vitória', 'Флуминенсе': 'Fluminense', 'Крузейро': 'Cruzeiro', 'Баия': 'Bahia',
    'Палмейрас': 'Palmeiras', 'Ремо': 'Remo', 'Сан-Паулу': 'São Paulo', 'Коринтианс': 'Corinthians',
    'Фламенго': 'Flamengo', 'Ботафого': 'Botafogo', 'Гремио': 'Grêmio', 'Интернасьонал': 'Internacional',
    'Атлетико Минейро': 'Atlético Mineiro', 'Сантос': 'Santos',
    'Ахмат': 'Akhmat', 'Родина': 'Rodina', 'Балтика': 'Baltika', 'Динамо': 'Dinamo',
    'Махачкала': 'Makhachkala', 'Зенит': 'Zenit', 'Ростов': 'Rostov', 'Краснодар': 'Krasnodar',
    'ЦСКА': 'CSKA Mosca', 'Крылья Советов': 'Krylya Sovetov', 'Оренбург': 'Orenburg',
    'Локомотив': 'Lokomotiv Mosca', 'Рубин': 'Rubin Kazan', 'Спартак': 'Spartak Mosca',
    'Акрон': 'Akron Tolyatti', 'Факел': 'Fakel', 'Москва': 'Mosca', 'Санкт-Петербург': 'San Pietroburgo',
    'Динамо-Урал': 'Dinamo-Ural', 'Уфа': 'Ufa',
    'Бавария': 'Bayern Monaco', 'Боруссия': 'Borussia', 'ПСЖ': 'Paris Saint-Germain',
}

CYRILLIC_TO_LATIN = {
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh',
    'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O',
    'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts',
    'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu',
    'Я': 'Ya',
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh',
    'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
    'я': 'ya'
}


def translate_russian_text(text: str) -> str:
    if not text:
        return ""
    res = text
    for d in [RU_TOURNAMENTS, RU_SPORTS_TERMS, RU_TEAMS]:
        for k in sorted(d.keys(), key=len, reverse=True):
            v = d[k]
            pattern = re.compile(rf'(?<!\w){re.escape(k)}(?!\w)', re.IGNORECASE)
            res = pattern.sub(v, res)
    res = re.sub(r'(\d+)-[йяе]\s*Giornata', r'\1ª Giornata', res)
    out = [CYRILLIC_TO_LATIN.get(ch, ch) for ch in res]
    clean = "".join(out)
    return re.sub(r'\s+', ' ', clean).strip()


# ==============================================================================
# 5. LOGICA DI PARSING & GENERAZIONE EPG
# ==============================================================================
def resolve_target_ids(source_id: str) -> list[str]:
    """Risolve un channel ID sorgente verso i target ammessi."""
    if source_id in ID_MAPPING:
        return ID_MAPPING[source_id]
    if source_id in TARGET_IDS:
        return [source_id]
    return []


def download_file(url: str, dest_path: str) -> bool:
    print(f"[*] Download sorgente: {url}")
    try:
        r = requests.get(url, stream=True, timeout=45, headers={"User-Agent": "SuperTeo/2.0 EPG Downloader"})
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=512 * 1024):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"[!] Errore durante il download da {url}: {e}")
        return False


def process_epg(output_gz_path: str = "epg.xml.gz"):
    temp_dir = tempfile.mkdtemp(prefix="superteo_epg_")
    merged_xml_path = os.path.join(temp_dir, "epg_merged.xml")

    channels_collected: dict[str, ET.Element] = {}
    programmes_collected: list[ET.Element] = []
    seen_programmes: set[tuple[str, str]] = set()

    try:
        for idx, url in enumerate(EPG_URLS):
            gz_path = os.path.join(temp_dir, f"source_{idx}.xml.gz")
            if not download_file(url, gz_path):
                continue

            try:
                with gzip.open(gz_path, "rb") as gz_in:
                    context = ET.iterparse(gz_in, events=("start", "end"))
                    _, root = next(context)

                    for event, elem in context:
                        if event == "end" and elem.tag == "channel":
                            raw_id = elem.attrib.get("id", "")
                            target_ids = resolve_target_ids(raw_id)
                            for tid in target_ids:
                                if tid not in channels_collected:
                                    new_ch = ET.Element("channel", {"id": tid})
                                    for child in list(elem):
                                        new_child = ET.SubElement(new_ch, child.tag, child.attrib)
                                        if child.tag == "display-name" and tid in DISPLAY_NAMES:
                                            new_child.text = DISPLAY_NAMES[tid]
                                        else:
                                            new_child.text = child.text
                                    channels_collected[tid] = new_ch
                            root.clear()

                        elif event == "end" and elem.tag == "programme":
                            raw_channel = elem.attrib.get("channel", "")
                            start_time = elem.attrib.get("start", "")
                            target_channels = resolve_target_ids(raw_channel)

                            for tch in target_channels:
                                prog_key = (tch, start_time)
                                if prog_key not in seen_programmes:
                                    seen_programmes.add(prog_key)
                                    new_prog = ET.Element("programme", elem.attrib)
                                    new_prog.attrib["channel"] = tch

                                    is_russian = tch.startswith("Match.")

                                    for child in list(elem):
                                        new_child = ET.SubElement(new_prog, child.tag, child.attrib)
                                        txt = child.text or ""
                                        if is_russian and child.tag in ("title", "desc") and txt:
                                            trans = translate_russian_text(txt)
                                            new_child.text = trans
                                        else:
                                            new_child.text = txt

                                    programmes_collected.append(new_prog)
                            root.clear()

            except Exception as e:
                print(f"[!] Errore durante il parsing di {url}: {e}")

        print(f"\n[+] Canali unificati estratti: {len(channels_collected)}")
        print(f"[+] Programmi totali indicizzati: {len(programmes_collected)}")

        # Verifica canali chiave
        canali_verifica = [
            "Rete4.it", "Canale5.it", "Italia1.it", "Tv8.it",
            "RSI.LA.2.ch", "Sky.Sport..251.it", "beINSports1.au",
            "CBS.Sports.Golazo.Network.us2", "SPORT.TV1.HD.pt",
            "TNT.Sports.1.HD.ie", "Sky.Sport.F1.de"
        ]
        print("\n--- STATO VERIFICA CANALI CHIAVE ---")
        for ck in canali_verifica:
            presente = "SI" if ck in channels_collected else "NO"
            progs = sum(1 for p in programmes_collected if p.attrib.get("channel") == ck)
            print(f" - {ck:<32}: Canale presente = {presente:<3} | Programmi = {progs}")

        # Generazione XML finale
        root_out = ET.Element("tv", {"generator-info-name": "SuperTeo EPG Generator 2.0"})
        for ch_elem in channels_collected.values():
            root_out.append(ch_elem)
        for pr_elem in programmes_collected:
            root_out.append(pr_elem)

        tree = ET.ElementTree(root_out)
        tree.write(merged_xml_path, encoding="utf-8", xml_declaration=True)

        print(f"\n[*] Compressione finale in {output_gz_path}...")
        with open(merged_xml_path, "rb") as f_in:
            with gzip.open(output_gz_path, "wb", compresslevel=9) as f_out:
                shutil.copyfileobj(f_in, f_out)

        out_size_mb = os.path.getsize(output_gz_path) / (1024 * 1024)
        print(f"[OK] File EPG generato con successo: {output_gz_path} ({out_size_mb:.2f} MB)")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    process_epg("epg.xml.gz")
