import gzip
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
import requests

# 1. Le 15 sorgenti EPG complete
EPG_URLS = [
    "http://epg-guide.com/wltv.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_IT1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz",  # Sky Sport DE & Austria
    "https://epgshare01.online/epgshare01/epg_ripper_BR1.xml.gz",  # ESPN 1-6 Brasil
    "https://epgshare01.online/epgshare01/epg_ripper_BR2.xml.gz",  # ESPN Brasil Backup
    "https://epgshare01.online/epgshare01/epg_ripper_PL1.xml.gz",  # Eleven / Canal+ PL
    "https://epgshare01.online/epgshare01/epg_ripper_CZ1.xml.gz",  # Canal+ Sport CZ / Sport1-2
    "https://epgshare01.online/epgshare01/epg_ripper_CH1.xml.gz",  # Svizzera (RSI)
    "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz",  # FOX Sport 4K, CBS Golazo
    "https://epgshare01.online/epgshare01/epg_ripper_AU1.xml.gz",  # beIN Sports AU
    "https://epgshare01.online/epgshare01/epg_ripper_HR1.xml.gz",  # Arena Sport 1-10 HR
    "https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz",  # Sport TV PT & DAZN PT
    "https://epgshare01.online/epgshare01/epg_ripper_IE1.xml.gz",  # TNT Sports 1-4 IE
    "https://epgshare01.online/epgshare01/epg_ripper_MX1.xml.gz",  # ESPN MX
    "https://epgshare01.online/epgshare01/epg_ripper_PH1.xml.gz",  # SPOTV PH
    "https://epgshare01.online/epgshare01/epg_ripper_LV1.xml.gz",  # Setanta Sports 1-2 (Baltici Telia / Cgates)
    "https://epgshare01.online/epgshare01/epg_ripper_LT1.xml.gz",  # Setanta LT
    "https://epgshare01.online/epgshare01/epg_ripper_RS1.xml.gz",  # Arena Sport Premium 1 e Arena Sport 2-5 (Serbia / Bosnia BHTelecom)
    "https://epgshare01.online/epgshare01/epg_ripper_AE1.xml.gz",  # Abu Dhabi Sports 1-2 (Starzplay Arabia / UAE)
]
]

# 2. Mappatura completa e bidirezionale (qualsiasi variante -> lista target da generare)
ID_MAPPING = {
    # Nazionali Italia
    "rai1": ["Rai1.it", "rai1"],
    "Rai1.it": ["Rai1.it", "rai1"],
    "rai2": ["Rai2.it", "rai2"],
    "Rai2.it": ["Rai2.it", "rai2"],
    "rai3": ["Rai3.it", "rai3"],
    "Rai3.it": ["Rai3.it", "rai3"],
    "rete4": ["Rete4.it", "rete4"],
    "Rete4.it": ["Rete4.it", "rete4"],
    "canale5": ["Canale5.it", "canale5"],
    "Canale5.it": ["Canale5.it", "canale5"],
    "italia1": ["Italia1.it", "italia1"],
    "Italia1.it": ["Italia1.it", "italia1"],
    "la7": ["la7", "La7.it"],
    "La7.it": ["la7", "La7.it"],
    "tv8": ["Tv8.it", "tv8"],
    "Tv8.it": ["Tv8.it", "tv8"],
    "nove": ["Nove.it", "nove"],
    "Nove.it": ["Nove.it", "nove"],

    # Sport Italia - Sky
    "Sky.Sport.Uno.it": ["Sky.Sport.Uno.it", "SkySportUno.it"],
    "SkySportUno.it": ["Sky.Sport.Uno.it", "SkySportUno.it"],
    "Sky.Sport.Calcio.it": ["Sky.Sport.Calcio.it", "SkySportCalcio.it"],
    "SkySportCalcio.it": ["Sky.Sport.Calcio.it", "SkySportCalcio.it"],
    "Sky.Sport.Tennis.it": ["Sky.Sport.Tennis.it", "SkySportTennis.it"],
    "SkySportTennis.it": ["Sky.Sport.Tennis.it", "SkySportTennis.it"],
    "Sky.Sport.Arena.it": ["Sky.Sport.Arena.it", "SkySportArena.it"],
    "SkySportArena.it": ["Sky.Sport.Arena.it", "SkySportArena.it"],
    "Sky.Sport.F1.it": ["Sky.Sport.F1.it", "SkySportF1.it"],
    "SkySportF1.it": ["Sky.Sport.F1.it", "SkySportF1.it"],
    "Sky.Sport.MotoGP.it": ["Sky.Sport.MotoGP.it", "SkySportMotoGP.it"],
    "SkySportMotoGP.it": ["Sky.Sport.MotoGP.it", "SkySportMotoGP.it"],

    # DAZN / ZONA DAZN (con gestione del doppio suffisso DAZN.1.it.it di IT1)
    "DAZN.1.it.it": ["DAZN.1.it.it", "DAZN.1.it", "Zona.DAZN.it", "zonadazn.it"],
    "DAZN.1.it":    ["DAZN.1.it.it", "DAZN.1.it", "Zona.DAZN.it", "zonadazn.it"],
    "Zona.DAZN.it": ["DAZN.1.it.it", "DAZN.1.it", "Zona.DAZN.it", "zonadazn.it"],
    "zonadazn.it":  ["DAZN.1.it.it", "DAZN.1.it", "Zona.DAZN.it", "zonadazn.it"],

    # Sky Calcio / Canali Multi-Evento
    "Sky.Sport..251.it": ["Sky.Sport..251.it", "Sky.Sport.251.it", "SkyCalcio1.it"],
    "Sky.Sport.251.it":  ["Sky.Sport..251.it", "Sky.Sport.251.it", "SkyCalcio1.it"],
    "SkyCalcio1.it":     ["Sky.Sport..251.it", "Sky.Sport.251.it", "SkyCalcio1.it"],

    "Sky.Sport..252.it": ["Sky.Sport..252.it", "Sky.Sport.252.it", "SkyCalcio2.it"],
    "Sky.Sport.252.it":  ["Sky.Sport..252.it", "Sky.Sport.252.it", "SkyCalcio2.it"],
    "SkyCalcio2.it":     ["Sky.Sport..252.it", "Sky.Sport.252.it", "SkyCalcio2.it"],

    "Sky.Sport..253.it": ["Sky.Sport..253.it", "Sky.Sport.253.it", "SkyCalcio3.it"],
    "Sky.Sport.253.it":  ["Sky.Sport..253.it", "Sky.Sport.253.it", "SkyCalcio3.it"],
    "SkyCalcio3.it":     ["Sky.Sport..253.it", "Sky.Sport.253.it", "SkyCalcio3.it"],

    "Sky.Sport..254.it": ["Sky.Sport..254.it", "Sky.Sport.254.it", "SkyCalcio4.it"],
    "Sky.Sport.254.it":  ["Sky.Sport..254.it", "Sky.Sport.254.it", "SkyCalcio4.it"],
    "SkyCalcio4.it":     ["Sky.Sport..254.it", "Sky.Sport.254.it", "SkyCalcio4.it"],

    "Sky.Sport..255.it": ["Sky.Sport..255.it", "Sky.Sport.255.it"],
    "Sky.Sport.255.it":  ["Sky.Sport..255.it", "Sky.Sport.255.it"],

    "Sky.Sport..256.it": ["Sky.Sport..256.it", "Sky.Sport.256.it"],
    "Sky.Sport.256.it":  ["Sky.Sport..256.it", "Sky.Sport.256.it"],

    "Sky.Sport..257.it": ["Sky.Sport..257.it", "Sky.Sport.257.it"],
    "Sky.Sport.257.it":  ["Sky.Sport..257.it", "Sky.Sport.257.it"],

    "Sky.Sport..258.it": ["Sky.Sport..258.it", "Sky.Sport.258.it"],
    "Sky.Sport.258.it":  ["Sky.Sport..258.it", "Sky.Sport.258.it"],

    "Sky.Sport..259.it": ["Sky.Sport..259.it", "Sky.Sport.259.it"],
    "Sky.Sport.259.it":  ["Sky.Sport..259.it", "Sky.Sport.259.it"],

    # Canali Club & DTT Sport
    "inter-it": ["inter-it", "Inter.TV.it"],
    "Inter.TV.it": ["inter-it", "Inter.TV.it"],
    "Milan.TV.it": ["Milan.TV.it", "milan-it"],
    "milan-it": ["Milan.TV.it", "milan-it"],
    "sportitalia": ["Sportitalia.HD.it", "sportitalia"],
    "Sportitalia.HD.it": ["Sportitalia.HD.it", "sportitalia"],

    # Svizzera
    "RSI.LA.2.ch": ["RSI.LA.2.ch"],
    "rsila2": ["RSI.LA.2.ch", "rsila2"],

    # Repubblica Ceca
    "Sport1.cz": ["Sport1.cz"],
    "Sport2.cz": ["Sport2.cz"],

    # Australia (beIN Sports)
    "beINSports1.au": ["beINSports1.au"],
    "beINSports2.au": ["beINSports2.au"],
    "beINSports3.au": ["beINSports3.au"],

    # USA & Messico
    "CBS.Sports.Golazo.Network.us2": ["CBS.Sports.Golazo.Network.us2"],
    "Fox.Deportes.HD.us2": ["Fox.Deportes.HD.us2"],
    "Fox.Sports.4K.us2": ["Fox.Sports.4K.us2", "FoxSports4K.us2"],
    "FoxSports4K.us2":   ["Fox.Sports.4K.us2", "FoxSports4K.us2"],
    "ESPN.MX.mx": ["ESPN.MX.mx"],
    "ESPN.2.mx": ["ESPN.2.mx"],
    "ESPN.3.mx": ["ESPN.3.mx"],
    "ESPN.4.mx": ["ESPN.4.mx"],
    "ESPN.5.mx": ["ESPN.4.mx", "ESPN.5.mx"],

    # ESPN Brasil (1-6)
    "ESPN.br": ["ESPN.br", "ESPN.HD.br"],
    "ESPN.HD.br": ["ESPN.br", "ESPN.HD.br"],
    "ESPN.2.br": ["ESPN.2.br", "ESPN2.HD.br"],
    "ESPN2.HD.br": ["ESPN.2.br", "ESPN2.HD.br"],
    "ESPN.3.br": ["ESPN.3.br", "São.Paulo/SP..ESPN.3.HD.br"],
    "São.Paulo/SP..ESPN.3.HD.br": ["ESPN.3.br", "São.Paulo/SP..ESPN.3.HD.br"],
    "ESPN.4.br": ["ESPN.4.br", "São.Paulo/SP..ESPN.4.HD.br"],
    "São.Paulo/SP..ESPN.4.HD.br": ["ESPN.4.br", "São.Paulo/SP..ESPN.4.HD.br"],
    "ESPN.5.br": ["ESPN.5.br"],
    "ESPN.6.br": ["ESPN.6.br"],

    # Germania - Sky Sport (1-10)
    "Sky.Sport.1.de": ["Sky.Sport.1.de"],
    "Sky.Sport.2.de": ["Sky.Sport.2.de"],
    "Sky.Sport.3.de": ["Sky.Sport.3.de"],
    "Sky.Sport.4.de": ["Sky.Sport.4.de"],
    "Sky.Sport.5.de": ["Sky.Sport.5.de"],
    "Sky.Sport.6.de": ["Sky.Sport.6.de"],
    "Sky.Sport.7.de": ["Sky.Sport.7.de"],
    "Sky.Sport.8.de": ["Sky.Sport.8.de"],
    "Sky.Sport.9.de": ["Sky.Sport.9.de"],
    "Sky.Sport.10.de": ["Sky.Sport.10.de"],

    # Germania - Sky Sport Austria (1-8)
    "Sky.Sport.Austria.1.HD.de": ["Sky.Sport.Austria.1.HD.de", "Sky.Sport.Austria.1.de"],
    "Sky.Sport.Austria.2.HD.de": ["Sky.Sport.Austria.2.HD.de", "Sky.Sport.Austria.2.de"],
    "Sky.Sport.Austria.3.HD.de": ["Sky.Sport.Austria.3.HD.de", "Sky.Sport.Austria.3.de"],
    "Sky.Sport.Austria.4.HD.de": ["Sky.Sport.Austria.4.HD.de", "Sky.Sport.Austria.4.de"],
    "Sky.Sport.Austria.5.HD.de": ["Sky.Sport.Austria.5.HD.de", "Sky.Sport.Austria.5.de"],
    "Sky.Sport.Austria.6.HD.de": ["Sky.Sport.Austria.6.HD.de", "Sky.Sport.Austria.6.de"],
    "Sky.Sport.Austria.7.HD.de": ["Sky.Sport.Austria.7.HD.de", "Sky.Sport.Austria.7.de"],
    "Sky.Sport.Austria.8.HD.de": ["Sky.Sport.Austria.8.HD.de", "Sky.Sport.Austria.8.de"],

    # Germania - Sky Sport Tematici
    "Sky.Sport.News.de": ["Sky.Sport.News.de"],
    "Sky.Sport.F1.de": ["Sky.Sport.F1.de"],
    "Sky.Sport.Premier.League.de": ["Sky.Sport.Premier.League.de"],
    "Sky.Sport.Mix.de": ["Sky.Sport.Mix.de"],
    "Sky.Sport.Tennis.de": ["Sky.Sport.Tennis.de"],

    # CANAL+ Sport (1-8) - Con mapping incrociato CZ e PL
    "Canal+.Sport.cz": ["Canal+.Sport.cz", "CANAL+.Sport.HD.pl"],
    "CANAL+.Sport.HD.pl": ["Canal+.Sport.cz", "CANAL+.Sport.HD.pl"],
    "CANAL+.Sport.pl": ["Canal+.Sport.cz", "CANAL+.Sport.HD.pl"],
    "Canal.plus.Sport.CZ.cz": ["Canal+.Sport.cz"],

    "Canal+.Sport.2.cz": ["Canal+.Sport.2.cz", "CANAL+.Sport.2.HD.pl"],
    "CANAL+.Sport.2.HD.pl": ["Canal+.Sport.2.cz", "CANAL+.Sport.2.HD.pl"],
    "CANAL+.Sport.2.pl": ["Canal+.Sport.2.cz", "CANAL+.Sport.2.HD.pl"],
    "Canal.plus.Sport.2.cz": ["Canal+.Sport.2.cz"],

    "Canal+.Sport.3.cz": ["Canal+.Sport.3.cz", "CANAL+.Sport.3.HD.pl"],
    "CANAL+.Sport.3.HD.pl": ["Canal+.Sport.3.cz", "CANAL+.Sport.3.HD.pl"],
    "CANAL+.Sport.3.pl": ["Canal+.Sport.3.cz", "CANAL+.Sport.3.HD.pl"],
    "Canal.plus.Sport.3.cz": ["Canal+.Sport.3.cz"],

    "Canal+.Sport.4.cz": ["Canal+.Sport.4.cz", "CANAL+.Sport.4.HD.pl"],
    "CANAL+.Sport.4.HD.pl": ["Canal+.Sport.4.cz", "CANAL+.Sport.4.HD.pl"],
    "CANAL+.Sport.4.pl": ["Canal+.Sport.4.cz", "CANAL+.Sport.4.HD.pl"],
    "Canal.plus.Sport.4.cz": ["Canal+.Sport.4.cz"],

    "Canal+.Sport.5.cz": ["Canal+.Sport.5.cz", "CANAL+.Sport.5.HD.pl"],
    "CANAL+.Sport.5.HD.pl": ["Canal+.Sport.5.cz", "CANAL+.Sport.5.HD.pl"],
    "CANAL+.Sport.5.pl": ["Canal+.Sport.5.cz", "CANAL+.Sport.5.HD.pl"],
    "Canal.plus.Sport.5.cz": ["Canal+.Sport.5.cz"],

    "Canal+.Sport.6.cz": ["Canal+.Sport.6.cz"],
    "Canal.plus.Sport.6.cz": ["Canal+.Sport.6.cz"],
    "Canal+.Sport.7.cz": ["Canal+.Sport.7.cz"],
    "Canal+.Sport.8.cz": ["Canal+.Sport.8.cz"],

    # Polonia (Eleven Sports)
    "Eleven.Sports.1.HD.pl": ["Eleven.Sports.1.HD.pl"],
    "Eleven.Sports.2.HD.pl": ["Eleven.Sports.2.HD.pl"],
    "Eleven.Sports.3.HD.pl": ["Eleven.Sports.3.HD.pl"],
    "Eleven.Sports.4.HD.pl": ["Eleven.Sports.4.HD.pl"],

    # Portogallo (Sport TV & DAZN/Eleven)
    "SPORT.TV1.HD.pt": ["SPORT.TV1.HD.pt"],
    "SPORT.TV2.HD.pt": ["SPORT.TV2.HD.pt"],
    "SPORT.TV3.HD.pt": ["SPORT.TV3.HD.pt"],
    "SPORT.TV4.HD.pt": ["SPORT.TV4.HD.pt"],
    "SPORT.TV5.HD.pt": ["SPORT.TV5.HD.pt"],
    "Sport.TV.6.HD.pt": ["Sport.TV.6.HD.pt"],
    "Sport.TV.7.HD.pt": ["Sport.TV.7.HD.pt"],
    "SPORT.TV+.HD.pt": ["SPORT.TV+.HD.pt"],
    "DAZN.1.pt": ["eleven-sport1-pt", "DAZN.1.pt"],
    "eleven-sport1-pt": ["eleven-sport1-pt", "DAZN.1.pt"],
    "DAZN.2.pt": ["eleven-sport2-pt", "DAZN.2.pt"],
    "eleven-sport2-pt": ["eleven-sport2-pt", "DAZN.2.pt"],
    "DAZN.3.pt": ["eleven-sport3-pt", "DAZN.3.pt"],
    "eleven-sport3-pt": ["eleven-sport3-pt", "DAZN.3.pt"],
    "DAZN.4.pt": ["eleven-sport4-pt", "DAZN.4.pt"],
    "eleven-sport4-pt": ["eleven-sport4-pt", "DAZN.4.pt"],
    "DAZN.5.pt": ["eleven-sport5-pt", "DAZN.5.pt"],
    "eleven-sport5-pt": ["eleven-sport5-pt", "DAZN.5.pt"],
    "DAZN.6.pt": ["eleven-sport6-pt", "DAZN.6.pt"],
    "eleven-sport6-pt": ["eleven-sport6-pt", "DAZN.6.pt"],

    # Croazia (Arena Sport)
    "Arena.Sport.1.HD.hr": ["Arena.Sport.1.HD.hr"],
    "Arena.Sport.2.HD.hr": ["Arena.Sport.2.HD.hr"],
    "Arena.Sport.3.HD.hr": ["Arena.Sport.3.HD.hr"],
    "Arena.Sport.4.HD.hr": ["Arena.Sport.4.HD.hr"],
    "Arena.Sport.5.HD.hr": ["Arena.Sport.5.HD.hr"],
    "Arena.Sport.6.HD.hr": ["Arena.Sport.6.HD.hr"],
    "Arena.Sport.7.HD.hr": ["Arena.Sport.7.HD.hr"],
    "Arena.Sport.8.HD.hr": ["Arena.Sport.8.HD.hr"],
    "Arena.Sport.9.HD.hr": ["Arena.Sport.9.HD.hr"],
    "Arena.Sport.10.HD.hr": ["Arena.Sport.10.HD.hr"],

    # Filippine (SPOTV)
    "SPOTV.HD.ph": ["Spotv Hd.ph", "SPOTV.HD.ph"],
    "SPOTV.ph": ["Spotv Hd.ph", "SPOTV.ph"],
    "Spotv Hd.ph": ["Spotv Hd.ph", "SPOTV.HD.ph"],
    "SPOTV.2.HD.ph": ["Spotv Hd2.ph", "SPOTV.2.HD.ph"],
    "SPOTV..2.ph": ["Spotv Hd2.ph", "SPOTV..2.ph"],
    "Spotv Hd2.ph": ["Spotv Hd2.ph", "SPOTV.2.HD.ph"],

    # UK / Irlanda (TNT Sports)
    "TNT.Sports.1.HD.ie": ["TNT.Sports.1.HD.ie"],
    "TNT.Sports.1.ie": ["TNT.Sports.1.HD.ie"],
    "TNT.Sports.2.HD.ie": ["TNT.Sports.2.HD.ie"],
    "TNT.Sports.2.ie": ["TNT.Sports.2.HD.ie"],
    "TNT.Sports.3.HD.ie": ["TNT.Sports.3.HD.ie"],
    "TNT.Sports.3.ie": ["TNT.Sports.3.HD.ie"],
    "TNT.Sports.4.HD.ie": ["TNT.Sports.4.HD.ie"],
    "TNT.Sports.4.ie": ["TNT.Sports.4.HD.ie"],
     # Setanta Sports 1
    "Setanta.Sports.1.HD.lv": ["Setanta.Sports.1.HD.lv", "Setanta.Sports.1.HD", "SetantaSports1.lt", "SetantaSports1"],
    "Setanta.LT.lt": ["Setanta.Sports.1.HD.lv", "Setanta.Sports.1.HD", "SetantaSports1.lt", "SetantaSports1"],
    "SetantaSports1.lt": ["Setanta.Sports.1.HD.lv", "Setanta.Sports.1.HD", "SetantaSports1.lt", "SetantaSports1"],
    # Setanta Sports 2
    "Setanta.Sports.2.HD.lv": ["Setanta.Sports.2.HD.lv", "Setanta.Sports.2.HD", "SetantaSports2.lt", "SetantaSports2"],
    "SetantaSports2.lt": ["Setanta.Sports.2.HD.lv", "Setanta.Sports.2.HD", "SetantaSports2.lt", "SetantaSports2"],
    # Arena Sport Premium 1 Bosnia (RS1 / Balcani)
    "Arena.PREMIUM.1.rs": ["Arena.PREMIUM.1.rs", "Arena.Sport.Premium.1.ba", "ArenaSportPremium1.ba", "ArenaSportPremium1"],
    "Arena.Premium.1.HD.(RS).rs": ["Arena.PREMIUM.1.rs", "Arena.Sport.Premium.1.ba", "ArenaSportPremium1.ba", "ArenaSportPremium1"],
    "Arena.Sport.Premium.1.ba": ["Arena.PREMIUM.1.rs", "Arena.Sport.Premium.1.ba", "ArenaSportPremium1.ba", "ArenaSportPremium1"],
    # Arena Sport 2 Bosnia
    "Arena.Sport.2.rs": ["Arena.Sport.2.rs", "Arena.Sport.2.ba", "ArenaSport2.ba", "ArenaSport2"],
    "Arena.Sport.2.HD.(RS).rs": ["Arena.Sport.2.rs", "Arena.Sport.2.ba", "ArenaSport2.ba", "ArenaSport2"],
    "Arena.Sport.2.HD.hr": ["Arena.Sport.2.rs", "Arena.Sport.2.ba", "ArenaSport2.ba", "ArenaSport2"],
    "Arena.Sport.2.ba": ["Arena.Sport.2.rs", "Arena.Sport.2.ba", "ArenaSport2.ba", "ArenaSport2"],
    # Arena Sport 3 Bosnia
    "Arena.Sport.3.rs": ["Arena.Sport.3.rs", "Arena.Sport.3.ba", "ArenaSport3.ba", "ArenaSport3"],
    "Arena.Sport.3.HD.(RS).rs": ["Arena.Sport.3.rs", "Arena.Sport.3.ba", "ArenaSport3.ba", "ArenaSport3"],
    "Arena.Sport.3.HD.hr": ["Arena.Sport.3.rs", "Arena.Sport.3.ba", "ArenaSport3.ba", "ArenaSport3"],
    "Arena.Sport.3.ba": ["Arena.Sport.3.rs", "Arena.Sport.3.ba", "ArenaSport3.ba", "ArenaSport3"],
    # Arena Sport 4 Bosnia
    "Arena.Sport.4.rs": ["Arena.Sport.4.rs", "Arena.Sport.4.ba", "ArenaSport4.ba", "ArenaSport4"],
    "Arena.Sport.4.HD.(RS).rs": ["Arena.Sport.4.rs", "Arena.Sport.4.ba", "ArenaSport4.ba", "ArenaSport4"],
    "Arena.Sport.4.HD.hr": ["Arena.Sport.4.rs", "Arena.Sport.4.ba", "ArenaSport4.ba", "ArenaSport4"],
    "Arena.Sport.4.ba": ["Arena.Sport.4.rs", "Arena.Sport.4.ba", "ArenaSport4.ba", "ArenaSport4"],
    # Arena Sport 5 Bosnia
    "Arena.Sport.5.rs": ["Arena.Sport.5.rs", "Arena.Sport.5.ba", "ArenaSport5.ba", "ArenaSport5"],
    "Arena.Sport.5.HD.(RS).rs": ["Arena.Sport.5.rs", "Arena.Sport.5.ba", "ArenaSport5.ba", "ArenaSport5"],
    "Arena.Sport.5.HD.hr": ["Arena.Sport.5.rs", "Arena.Sport.5.ba", "ArenaSport5.ba", "ArenaSport5"],
    "Arena.Sport.5.ba": ["Arena.Sport.5.rs", "Arena.Sport.5.ba", "ArenaSport5.ba", "ArenaSport5"],
    # Abu Dhabi Sports 1
    "en:.Abu.Dhabi.Sports.1.ae": ["en:.Abu.Dhabi.Sports.1.ae", "Abu.Dhabi.Sports.1.ae", "AbuDhabiSports1.ae", "AbuDhabiSports1"],
    "Abu.Dhabi.Sports.1.ae": ["en:.Abu.Dhabi.Sports.1.ae", "Abu.Dhabi.Sports.1.ae", "AbuDhabiSports1.ae", "AbuDhabiSports1"],
    # Abu Dhabi Sports 2
    "en:.Abu.Dhabi.Sports.2.ae": ["en:.Abu.Dhabi.Sports.2.ae", "Abu.Dhabi.Sports.2.ae", "AbuDhabiSports2.ae", "AbuDhabiSports2"],
    "Abu.Dhabi.Sports.2.ae": ["en:.Abu.Dhabi.Sports.2.ae", "Abu.Dhabi.Sports.2.ae", "AbuDhabiSports2.ae", "AbuDhabiSports2"],
}

# Lookup insensibile al maiuscolo/minuscolo per matching infallibile
LOWER_ID_MAP = {k.lower(): v for k, v in ID_MAPPING.items()}
OUTPUT_FILE = "epg.xml.gz"
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def download_to_temp(url: str, dest_path: str) -> bool:
    try:
        with requests.get(url, headers=HTTP_HEADERS, stream=True, timeout=90) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        print(f"  [WARN] Errore scaricamento da {url}: {e}")
        return False

def open_epg_stream(file_path: str):
    with open(file_path, "rb") as f:
        magic = f.read(2)
    if magic == b"\x1f\x8b":
        return gzip.open(file_path, "rb")
    return open(file_path, "rb")

def resolve_target_ids(channel_id: str):
    if not channel_id:
        return []
    if channel_id in ID_MAPPING:
        return ID_MAPPING[channel_id]
    low = channel_id.lower()
    return LOWER_ID_MAP.get(low, [])

def main():
    temp_dir = tempfile.mkdtemp(prefix="epg_merge_")
    merged_channels = {}
    seen_programmes = set()  # Deduplicazione: (channel_id, start_time)
    total_programmes = 0

    try:
        temp_prog_path = os.path.join(temp_dir, "programmes.tmp")
        print("=== INIZIO ELABORAZIONE SORGENTI EPG ===")

        with open(temp_prog_path, "wb") as prog_out:
            for idx, url in enumerate(EPG_URLS, 1):
                print(f"[{idx}/{len(EPG_URLS)}] Download {url} ...")
                local_archive = os.path.join(temp_dir, f"source_{idx}.tmp")

                if not download_to_temp(url, local_archive):
                    continue

                try:
                    with open_epg_stream(local_archive) as stream:
                        context = ET.iterparse(stream, events=("start", "end"))
                        _, root = next(context)

                        for event, elem in context:
                            if event == "end" and elem.tag == "channel":
                                c_id = elem.get("id")
                                target_ids = resolve_target_ids(c_id)
                                if target_ids:
                                    for tid in target_ids:
                                        if tid not in merged_channels:
                                            new_ch = ET.Element("channel", id=tid)
                                            for child in elem:
                                                new_ch.append(child)
                                            merged_channels[tid] = ET.tostring(new_ch, encoding="utf-8")
                                elem.clear()
                                root.clear()

                            elif event == "end" and elem.tag == "programme":
                                p_chan = elem.get("channel")
                                p_start = elem.get("start")
                                target_ids = resolve_target_ids(p_chan)

                                if target_ids and p_start:
                                    for tid in target_ids:
                                        dedup_key = (tid, p_start)
                                        # Scrive il programma solo se non è già stato inserito da un'altra sorgente
                                        if dedup_key not in seen_programmes:
                                            seen_programmes.add(dedup_key)
                                            elem.set("channel", tid)
                                            prog_out.write(b"  " + ET.tostring(elem, encoding="utf-8") + b"\n")
                                            total_programmes += 1
                                elem.clear()
                                root.clear()

                except Exception as e:
                    print(f"  [ERROR] Parsing fallito per {url}: {e}")

                if os.path.exists(local_archive):
                    os.remove(local_archive)

        print(f"\nCanali unici configurati: {len(merged_channels)} | Programmi estratti: {total_programmes}")

        # Generazione archivio XML compresso
        print(f"Compressione in {OUTPUT_FILE} (livello 9)...")
        with gzip.open(OUTPUT_FILE, "wb", compresslevel=9) as gz_out:
            gz_out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            gz_out.write(b'<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
            gz_out.write(b'<tv generator-info-name="Custom EPG Merger">\n')

            for ch_bytes in merged_channels.values():
                gz_out.write(b"  " + ch_bytes + b"\n")

            with open(temp_prog_path, "rb") as prog_in:
                shutil.copyfileobj(prog_in, gz_out)

            gz_out.write(b"</tv>\n")

        size_kb = os.path.getsize(OUTPUT_FILE) / 1024
        print(f"[OK] {OUTPUT_FILE} completato con successo ({size_kb:.1f} KB)!")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
