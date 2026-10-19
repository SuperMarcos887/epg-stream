import gzip
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
import requests

# 1. Le 9 sorgenti EPG indicate
EPG_URLS = [
    "http://epg-guide.com/wltv.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_PL1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_CZ1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_CH1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_AU1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_HR1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_PT1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_IE1.xml.gz",
]

# 2. I tvg-id estratti dalla tua playlist
WHITELIST_IDS = {
    # Nazionali Italia
    "Rai1.it",
    "Rai2.it",
    "Rai3.it",
    "Rete4.it",
    "Canale5.it",
    "Italia1.it",
    "la7",
    "Tv8.it",
    "Nove.it",

    # Svizzera & Italia Sport
    "RSI.LA.2.ch",
    "Sky.Sport.F1.it",
    "inter-it",

    # Repubblica Ceca
    "Sport1.cz",
    "Sport2.cz",

    # Australia (beIN Sports)
    "beINSports1.au",
    "beINSports2.au",
    "beINSports3.au",

    # USA & Messico
    "CBS.Sports.Golazo.Network.us2",
    "Fox.Deportes.HD.us2",
    "ESPN.MX.mx",
    "ESPN.2.mx",
    "ESPN.3.mx",
    "ESPN.4.mx",

    # Polonia (Eleven Sports)
    "Eleven.Sports.1.HD.pl",
    "Eleven.Sports.2.HD.pl",
    "Eleven.Sports.3.HD.pl",
    "Eleven.Sports.4.HD.pl",

    # Portogallo (Sport TV & DAZN/Eleven)
    "SPORT.TV1.HD.pt",
    "SPORT.TV2.HD.pt",
    "SPORT.TV3.HD.pt",
    "SPORT.TV4.HD.pt",
    "SPORT.TV5.HD.pt",
    "Sport.TV.6.HD.pt",
    "Sport.TV.7.HD.pt",
    "eleven-sport1-pt",
    "eleven-sport2-pt",
    "eleven-sport3-pt",
    "eleven-sport4-pt",
    "eleven-sport5-pt",
    "eleven-sport6-pt",

    # Croazia (Arena Sport)
    "Arena.Sport.1.HD.hr",
    "Arena.Sport.2.HD.hr",
    "Arena.Sport.3.HD.hr",
    "Arena.Sport.4.HD.hr",
    "Arena.Sport.5.HD.hr",
    "Arena.Sport.6.HD.hr",
    "Arena.Sport.7.HD.hr",
    "Arena.Sport.8.HD.hr",
    "Arena.Sport.9.HD.hr",
    "Arena.Sport.10.HD.hr",

    # Filippine (SPOTV)
    "Spotv Hd.ph",
    "Spotv Hd2.ph",

    # UK / Irlanda (TNT Sports)
    "TNT.Sports.1.HD.ie",
    "TNT.Sports.2.HD.ie",
    "TNT.Sports.3.HD.ie",
    "TNT.Sports.4.HD.ie",
}

OUTPUT_FILE = "epg.xml.gz"
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


def download_to_temp(url: str, dest_path: str) -> bool:
    """Scarica il file a blocchi per non saturare la memoria."""
    try:
        with requests.get(url, headers=HTTP_HEADERS, stream=True, timeout=90) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=128 * 1024):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        print(f"  [!] Errore download da {url}: {e}")
        return False


def main():
    print(f"Inizio elaborazione EPG per {len(WHITELIST_IDS)} canali target...")
    channels_dict = {}  # channel_id -> bytes XML
    seen_programmes_count = 0

    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_prog_file_path = os.path.join(tmp_dir, "programmes.tmp")
        temp_download_path = os.path.join(tmp_dir, "downloaded.gz")

        with open(temp_prog_file_path, "wb") as prog_out:
            for idx, url in enumerate(EPG_URLS, 1):
                print(f"[{idx}/{len(EPG_URLS)}] Download: {url}")
                if not download_to_temp(url, temp_download_path):
                    continue

                print("      Parsing e filtraggio...")
                try:
                    with gzip.open(temp_download_path, "rb") as gz_in:
                        context = ET.iterparse(gz_in, events=("start", "end"))
                        context = iter(context)
                        _, root = next(context)

                        for event, elem in context:
                            if event == "end":
                                if elem.tag == "channel":
                                    c_id = elem.get("id")
                                    if c_id in WHITELIST_IDS and c_id not in channels_dict:
                                        channels_dict[c_id] = ET.tostring(elem, encoding="utf-8")
                                    root.clear()

                                elif elem.tag == "programme":
                                    c_id = elem.get("channel")
                                    if c_id in WHITELIST_IDS:
                                        prog_out.write(ET.tostring(elem, encoding="utf-8") + b"\n")
                                        seen_programmes_count += 1
                                    root.clear()

                except Exception as e:
                    print(f"  [!] Errore parsing {url}: {e}")

                if os.path.exists(temp_download_path):
                    os.remove(temp_download_path)

        # Scrittura del file unificato finale compresso
        print(f"Generazione file finale '{OUTPUT_FILE}'...")
        with gzip.open(OUTPUT_FILE, "wb", compresslevel=9) as f_out:
            f_out.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
            f_out.write(b'<tv generator-info-name="CustomEPGMerger">\n')

            # 1. Prima tutti i canali
            for ch_bytes in channels_dict.values():
                f_out.write(ch_bytes)
                f_out.write(b"\n")

            # 2. Poi tutti i programmi dal file temporaneo
            with open(temp_prog_file_path, "rb") as prog_in:
                shutil.copyfileobj(prog_in, f_out)

            f_out.write(b"</tv>\n")

    file_size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print("Elaborazione completata!")
    print(f"- Canali agganciati: {len(channels_dict)}/{len(WHITELIST_IDS)}")
    print(f"- Eventi programma indicizzati: {seen_programmes_count}")
    print(f"- Dimensione file generato: {file_size_kb:.2f} KB")


if __name__ == "__main__":
    main()
