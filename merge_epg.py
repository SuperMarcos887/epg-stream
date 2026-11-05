import gzip
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
import requests

# 1. Sorgenti EPG complete (incluse DE1 per Sky Sport Germania/Austria e BR1/BR2 per ESPN Brasile)
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
    "https://epgshare01.online/epgshare01/epg_ripper_HR1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz",  # Sport TV PT & DAZN PT
    "https://epgshare01.online/epgshare01/epg_ripper_IE1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_MX1.xml.gz",  # ESPN MX
    "https://epgshare01.online/epgshare01/epg_ripper_PH1.xml.gz",
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

    # DAZN / ZONA DAZN
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

    # CANAL+ Sport (CZ / PL)
    "Canal+.Sport.cz": ["Canal+.Sport.cz", "Canal+.Sport.HD.pl"],
    "Canal+.Sport.HD.pl": ["Canal+.Sport.cz", "Canal+.Sport.HD.pl"],
    "Canal+.Sport.2.cz": ["Canal+.Sport.2.cz", "Canal+.Sport.2.HD.pl"],
    "Canal+.Sport.2.HD.pl": ["Canal+.Sport.2.cz", "Canal+.Sport.2.HD.pl"],
    "Canal+.Sport.3.cz": ["Canal+.Sport.3.cz", "Canal+.Sport.3.HD.pl"],
    "Canal+.Sport.3.HD.pl": ["Canal+.Sport.3.cz", "Canal+.Sport.3.HD.pl"],
    "Canal+.Sport.4.cz": ["Canal+.Sport.4.cz", "Canal+.Sport.4.HD.pl"],
    "Canal+.Sport.4.HD.pl": ["Canal+.Sport.4.cz", "Canal+.Sport.4.HD.pl"],
    "Canal+.Sport.5.cz": ["Canal+.Sport.5.cz", "Canal+.Sport.5.HD.pl"],
    "Canal+.Sport.5.HD.pl": ["Canal+.Sport.5.cz", "Canal+.Sport.5.HD.pl"],
    "Canal+.Sport.6.cz": ["Canal+.Sport.6.cz"],
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
}

# Insieme univoco di tutti gli ID sorgente che ci interessano
SOURCE_IDS_TO_TRACK = set(ID_MAPPING.keys())

def download_and_extract(url, temp_dir):
    """Scarica il file EPG .gz e lo decomprime in locale restituendo il path del file XML."""
    filename = url.split("/")[-1]
    gz_path = os.path.join(temp_dir, filename)
    xml_path = os.path.join(temp_dir, filename.replace(".gz", ""))

    print(f"📥 Download in corso: {url} ...")
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()

    with open(gz_path, "wb") as f_out:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f_out.write(chunk)

    print(f"📦 Decompressione {filename} ...")
    with gzip.open(gz_path, "rb") as f_in, open(xml_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    return xml_path

def build_merged_epg(output_path="epg.xml"):
    """Estrae e mappa solo i canali e programmi di interesse da tutte le sorgenti."""
    temp_dir = tempfile.mkdtemp(prefix="epg_build_")
    
    # Root del nuovo XMLTV unificato
    root_out = ET.Element("tv", {
        "generator-info-name": "SuperTeo EPG Merger",
        "generator-info-url": "https://github.com/superteo"
    })

    written_channels = set()
    total_programmes = 0

    try:
        for url in EPG_URLS:
            try:
                xml_path = download_and_extract(url, temp_dir)
            except Exception as e:
                print(f"⚠️ Errore durante il download da {url}: {e}")
                continue

            print(f"🔍 Parsing di {os.path.basename(xml_path)} ...")
            context = ET.iterparse(xml_path, events=("end",))

            for event, elem in context:
                # 1. Parsing nodi <channel>
                if elem.tag == "channel":
                    chan_id = elem.attrib.get("id")
                    if chan_id in SOURCE_IDS_TO_TRACK:
                        target_ids = ID_MAPPING.get(chan_id, [chan_id])
                        for t_id in target_ids:
                            if t_id not in written_channels:
                                new_chan = ET.SubElement(root_out, "channel", {"id": t_id})
                                for child in elem:
                                    new_chan.append(child)
                                written_channels.add(t_id)
                    elem.clear()

                # 2. Parsing nodi <programme>
                elif elem.tag == "programme":
                    chan_id = elem.attrib.get("channel")
                    if chan_id in SOURCE_IDS_TO_TRACK:
                        target_ids = ID_MAPPING.get(chan_id, [chan_id])
                        for t_id in target_ids:
                            new_prog = ET.SubElement(root_out, "programme", {
                                "start": elem.attrib.get("start", ""),
                                "stop": elem.attrib.get("stop", ""),
                                "channel": t_id
                            })
                            for child in elem:
                                new_prog.append(child)
                            total_programmes += 1
                    elem.clear()

            # Rimozione XML temporaneo per non saturare il disco
            if os.path.exists(xml_path):
                os.remove(xml_path)

        # Salvataggio del file finale compresso con gzip
        out_gz = output_path if output_path.endswith(".gz") else f"{output_path}.gz"
        print(f"💾 Scrittura file finale compresso: {out_gz} ...")
        xml_bytes = ET.tostring(root_out, encoding="utf-8", method="xml")
        with gzip.open(out_gz, "wb") as f_gz:
            f_gz.write(xml_bytes)

        print(f"✅ EPG Generata con Successo! Canali unici: {len(written_channels)}, Programmi: {total_programmes}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    build_merged_epg("epg.xml.gz")
