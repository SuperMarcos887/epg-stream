import gzip
import os
import shutil
import tempfile
import requests
import xml.etree.ElementTree as ET

# ==============================================================================
# 1. LE 18 SORGENTI EPG COMPLETE (Tutti i campionati e canali di canali.m3u)
# ==============================================================================
EPG_URLS = [
    # Nazionali e Sky Sport Italia / Cinema / DAZN
    "http://epg-guide.com/wltv.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_IT1.xml.gz",
    # Sky Sport Germania & Austria 1-8
    "https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz",
    # Canal+ Sport 1-8 CZ & Sport 1-2 CZ
    "https://epgshare01.online/epgshare01/epg_ripper_CZ1.xml.gz",
    # Eleven Sports 1-4 PL & Canal+ Sport PL
    "https://epgshare01.online/epgshare01/epg_ripper_PL1.xml.gz",
    # Setanta Sports 1 & 2 HD (Lettonia / Baltici Telia & cgates)
    "https://epgshare01.online/epgshare01/epg_ripper_LV1.xml.gz",
    # Arena Sport Premium 1 e Arena Sport 2-5 (Bosnia BHTelecom / Serbia)
    "https://epgshare01.online/epgshare01/epg_ripper_RS1.xml.gz",
    # Abu Dhabi Sports 1 & 2 HD (Starzplay Arabia / UAE)
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
	# Nova Sport 1-6 HD & Canal+ Sport SK (Slovacchia)
    "https://epgshare01.online/epgshare01/epg_ripper_SK1.xml.gz",
    # Match! Canali Sport Russia (Match TV, Futbol 1-3, Arena, Premier, Fight)
    "https://epgshare01.online/epgshare01/epg_ripper_UA1.xml.gz",
]

# ==============================================================================
# 2. TARGET IDS DIRETTI (Tutti i tvg-id usati nella lista canali.m3u)
# ==============================================================================
TARGET_IDS = {
    # Abu Dhabi Sports
    "AD.Sports.1.HD.ae",
    "AD.Sports.2.HD.ae",

    # Setanta Sports Baltici
    "Setanta.Sports.1.HD.lv",
    "Setanta.Sports.2.HD.lv",

    # Arena Sport Bosnia / Serbia (bhtelecom)
    "Arena.PREMIUM.1.rs",
    "Arena.Sport.2.rs",
    "Arena.Sport.3.rs",
    "Arena.Sport.4.rs",
    "Arena.Sport.5.rs",

    # Arena Sport Croazia
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

    # Canal+ Sport CZ & Sport 1-2 CZ
    "Canal+.Sport.cz",
    "Canal+.Sport.2.cz",
    "Canal+.Sport.3.cz",
    "Canal+.Sport.4.cz",
    "Canal+.Sport.5.cz",
    "Canal+.Sport.6.cz",
    "Canal+.Sport.7.cz",
    "Canal+.Sport.8.cz",
    "Sport1.cz",
    "Sport2.cz",

    # Eleven Sports PL
    "Eleven.Sports.1.HD.pl",
    "Eleven.Sports.2.HD.pl",
    "Eleven.Sports.3.HD.pl",
    "Eleven.Sports.4.HD.pl",

    # Sky Sport Austria
    "Sky.Sport.Austria.1.HD.de",
    "Sky.Sport.Austria.2.HD.de",
    "Sky.Sport.Austria.3.HD.de",
    "Sky.Sport.Austria.4.HD.de",
    "Sky.Sport.Austria.5.HD.de",
    "Sky.Sport.Austria.6.HD.de",
    "Sky.Sport.Austria.7.HD.de",
    "Sky.Sport.Austria.8.HD.de",

    # Sky Sport Germania
    "Sky.Sport.1.de",
    "Sky.Sport.2.de",
    "Sky.Sport.3.de",
    "Sky.Sport.4.de",
    "Sky.Sport.5.de",
    "Sky.Sport.6.de",
    "Sky.Sport.7.de",
    "Sky.Sport.8.de",
    "Sky.Sport.9.de",
    "Sky.Sport.10.de",
    "Sky.Sport.F1.de",
    "Sky.Sport.Mix.de",
    "Sky.Sport.News.de",
    "Sky.Sport.Premier.League.de",
    "Sky.Sport.Tennis.de",

    # Sky Sport Italia & DAZN & Club
    "Sky.Sport.Uno.it",
    "Sky.Sport.Calcio.it",
    "Sky.Sport.Tennis.it",
    "Sky.Sport.Arena.it",
    "Sky.Sport.F1.it",
    "Sky.Sport.MotoGP.it",
    "Sky.Sport..251.it",
    "Sky.Sport..252.it",
    "Sky.Sport..253.it",
    "Sky.Sport..254.it",
    "DAZN.1.it.it",
    "Milan.TV.it",
    "inter-it",

    # Sky Cinema & Sky Uno Italia
    "Sky.Uno.it",
    "Sky.Cinema.Uno.it",
    "Sky.Cinema.Uno.24.it",
    "Sky.Cinema.Collection.it",
    "Sky.Cinema.Family.it",
    "Sky.Cinema.Action.it",
    "Sky.Cinema.Suspense.it",
    "Sky.Cinema.Romance.it",
    "Sky.Cinema.Drama.it",
    "Sky.Cinema.Comedy.it",

    # Canali Nazionali Italia
    "Rai1.it",
    "Rai2.it",
    "Rai3.it",
    "Rete4.it",
    "Canale5.it",
    "Italia1.it",
    "la7",
    "Tv8.it",
    "Nove.it",

    # RSI Svizzera
    "RSI.LA.2.ch",

    # TNT Sports UK/IE
    "TNT.Sports.1.HD.ie",
    "TNT.Sports.2.HD.ie",
    "TNT.Sports.3.HD.ie",
    "TNT.Sports.4.HD.ie",

    # Sport TV Portogallo & Eleven PT
    "SPORT.TV+.HD.pt",
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

    # ESPN Brasile
    "ESPN.br",
    "ESPN.2.br",
    "ESPN.3.br",
    "ESPN.4.br",
    "ESPN.5.br",
    "ESPN.6.br",

    # ESPN Messico
    "ESPN.MX.mx",
    "ESPN.2.mx",
    "ESPN.3.mx",
    "ESPN.4.mx",

    # USA
    "CBS.Sports.Golazo.Network.us2",
    "Fox.Deportes.HD.us2",
    "Fox.Sports.4K.us2",

    # Australia & Filippine
    "beINSports1.au",
    "beINSports2.au",
    "beINSports3.au",
    "Spotv Hd.ph",
    "Spotv Hd2.ph",
	
	# Nova Sport 1-6 HD (Slovacchia / Repubblica Ceca)
    "Nova.Sport.1.HD.sk",
    "Nova.Sport.2.HD.sk",
    "Nova.Sport.3.HD.sk",
    "Nova.Sport.4.HD.sk",
    "Nova.Sport.5.HD.sk",
    "Nova.Sport.6.HD.sk",
	
    # Match! Sport Russia
    "Match.TV.ru",
    "Match.Futbol.1.ru",
    "Match.Futbol.2.ru",
    "Match.Futbol.3.ru",
    "Match.Arena.ru",
    "Match.Premier.ru",
    "Match.Fight.ru",
	
	# CANAL+.Sport Slovacchia
	"CANAL+.Sport.4.HD.sk",
	"CANAL+.Sport.5.HD.sk",
	"CANAL+.Sport.6.HD.sk",
	"CANAL+.Sport.7.HD.sk",
	"CANAL+.Sport.8.HD.sk",
	"CANAL+.Sport.HD.sk",
}

# ==============================================================================
# 3. MAPPATURA ALIAS E VARIANTI (ID Sorgente XML -> ID Target M3U SuperTeo)
# ==============================================================================
ID_MAPPING = {
    # Abu Dhabi Sports
    "AD.Sports.1.HD.ae": ["AD.Sports.1.HD.ae"],
    "AD.Sports.2.HD.ae": ["AD.Sports.2.HD.ae"],
    "en:.Abu.Dhabi.Sports.1.ae": ["AD.Sports.1.HD.ae"],
    "en:.Abu.Dhabi.Sports.2.ae": ["AD.Sports.2.HD.ae"],
    "Abu.Dhabi.Sports.1.ae": ["AD.Sports.1.HD.ae"],
    "Abu.Dhabi.Sports.2.ae": ["AD.Sports.2.HD.ae"],

    # Setanta Sports (Baltici)
    "Setanta.Sports.1.HD.lv": ["Setanta.Sports.1.HD.lv"],
    "Setanta.Sports.2.HD.lv": ["Setanta.Sports.2.HD.lv"],
    "Setanta.Sports.1.lv": ["Setanta.Sports.1.HD.lv"],
    "Setanta.Sports.2.lv": ["Setanta.Sports.2.HD.lv"],
    "Setanta.LT.lt": ["Setanta.Sports.1.HD.lv"],

    # Arena Sport Bosnia / Serbia
    "Arena.PREMIUM.1.rs": ["Arena.PREMIUM.1.rs"],
    "Arena.Sport.Premium.1.rs": ["Arena.PREMIUM.1.rs"],
    "Arena.Sport.2.rs": ["Arena.Sport.2.rs"],
    "Arena.Sport.3.rs": ["Arena.Sport.3.rs"],
    "Arena.Sport.4.rs": ["Arena.Sport.4.rs"],
    "Arena.Sport.5.rs": ["Arena.Sport.5.rs"],

    # Arena Sport Croazia
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

    # Nazionali Italia e wltv
    "rai1": ["Rai1.it"],
    "Rai1.it": ["Rai1.it"],
    "rai2": ["Rai2.it"],
    "Rai2.it": ["Rai2.it"],
    "rai3": ["Rai3.it"],
    "Rai3.it": ["Rai3.it"],
    "rete4": ["Rete4.it"],
    "Rete4.it": ["Rete4.it"],
    "canale5": ["Canale5.it"],
    "Canale5.it": ["Canale5.it"],
    "italia1": ["Italia1.it"],
    "Italia1.it": ["Italia1.it"],
    "la7": ["la7"],
    "La7.it": ["la7"],
    "tv8": ["Tv8.it"],
    "Tv8.it": ["Tv8.it"],
    "nove": ["Nove.it"],
    "Nove.it": ["Nove.it"],

    # Sky Sport Italia
    "SkySportUno.it": ["Sky.Sport.Uno.it"],
    "Sky.Sport.Uno.it": ["Sky.Sport.Uno.it"],
    "SkySportCalcio.it": ["Sky.Sport.Calcio.it"],
    "Sky.Sport.Calcio.it": ["Sky.Sport.Calcio.it"],
    "SkySportTennis.it": ["Sky.Sport.Tennis.it"],
    "Sky.Sport.Tennis.it": ["Sky.Sport.Tennis.it"],
    "SkySportArena.it": ["Sky.Sport.Arena.it"],
    "Sky.Sport.Arena.it": ["Sky.Sport.Arena.it"],
    "SkySportF1.it": ["Sky.Sport.F1.it"],
    "Sky.Sport.F1.it": ["Sky.Sport.F1.it"],
    "SkySportMotoGP.it": ["Sky.Sport.MotoGP.it"],
    "Sky.Sport.MotoGP.it": ["Sky.Sport.MotoGP.it"],
    "Sky.Sport.251.it": ["Sky.Sport..251.it"],
    "Sky.Sport..251.it": ["Sky.Sport..251.it"],
    "Sky.Sport.252.it": ["Sky.Sport..252.it"],
    "Sky.Sport..252.it": ["Sky.Sport..252.it"],
    "Sky.Sport.253.it": ["Sky.Sport..253.it"],
    "Sky.Sport..253.it": ["Sky.Sport..253.it"],
    "Sky.Sport.254.it": ["Sky.Sport..254.it"],
    "Sky.Sport..254.it": ["Sky.Sport..254.it"],

    # Sky Uno
    "SkyUno.it": ["Sky.Uno.it"],
    "Sky.Uno.it": ["Sky.Uno.it"],
    "skyuno": ["Sky.Uno.it"],
    "Sky Uno": ["Sky.Uno.it"],

    # Sky Cinema Uno
    "SkyCinemaUno.it": ["Sky.Cinema.Uno.it"],
    "Sky.Cinema.Uno.it": ["Sky.Cinema.Uno.it"],
    "skycinemauno": ["Sky.Cinema.Uno.it"],
    "Sky Cinema Uno": ["Sky.Cinema.Uno.it"],

    # Sky Cinema Uno +24
    "SkyCinemaUno+24.it": ["Sky.Cinema.Uno.24.it"],
    "SkyCinemaUno24.it": ["Sky.Cinema.Uno.24.it"],
    "Sky.Cinema.Uno.+24.it": ["Sky.Cinema.Uno.24.it"],
    "Sky.Cinema.Uno.24.it": ["Sky.Cinema.Uno.24.it"],
    "skycinemauno24": ["Sky.Cinema.Uno.24.it"],
    "Sky Cinema Uno +24": ["Sky.Cinema.Uno.24.it"],

    # Sky Cinema Collection
    "SkyCinemaCollection.it": ["Sky.Cinema.Collection.it"],
    "Sky.Cinema.Collection.it": ["Sky.Cinema.Collection.it"],
    "skycinemacollection": ["Sky.Cinema.Collection.it"],
    "Sky Cinema Collection": ["Sky.Cinema.Collection.it"],

    # Sky Cinema Family
    "SkyCinemaFamily.it": ["Sky.Cinema.Family.it"],
    "Sky.Cinema.Family.it": ["Sky.Cinema.Family.it"],
    "skycinemafamily": ["Sky.Cinema.Family.it"],
    "Sky Cinema Family": ["Sky.Cinema.Family.it"],

    # Sky Cinema Action
    "SkyCinemaAction.it": ["Sky.Cinema.Action.it"],
    "Sky.Cinema.Action.it": ["Sky.Cinema.Action.it"],
    "skycinemaaction": ["Sky.Cinema.Action.it"],
    "Sky Cinema Action": ["Sky.Cinema.Action.it"],

    # Sky Cinema Suspense
    "SkyCinemaSuspense.it": ["Sky.Cinema.Suspense.it"],
    "Sky.Cinema.Suspense.it": ["Sky.Cinema.Suspense.it"],
    "skycinemasuspense": ["Sky.Cinema.Suspense.it"],
    "Sky Cinema Suspense": ["Sky.Cinema.Suspense.it"],

    # Sky Cinema Romance
    "SkyCinemaRomance.it": ["Sky.Cinema.Romance.it"],
    "Sky.Cinema.Romance.it": ["Sky.Cinema.Romance.it"],
    "skycinemaromance": ["Sky.Cinema.Romance.it"],
    "Sky Cinema Romance": ["Sky.Cinema.Romance.it"],

    # Sky Cinema Drama
    "SkyCinemaDrama.it": ["Sky.Cinema.Drama.it"],
    "Sky.Cinema.Drama.it": ["Sky.Cinema.Drama.it"],
    "skycinemadrama": ["Sky.Cinema.Drama.it"],
    "Sky Cinema Drama": ["Sky.Cinema.Drama.it"],

    # Sky Cinema Comedy
    "SkyCinemaComedy.it": ["Sky.Cinema.Comedy.it"],
    "Sky.Cinema.Comedy.it": ["Sky.Cinema.Comedy.it"],
    "skycinemacomedy": ["Sky.Cinema.Comedy.it"],
    "Sky Cinema Comedy": ["Sky.Cinema.Comedy.it"],

    # DAZN
    "DAZN.1.it.it": ["DAZN.1.it.it"],
    "DAZN.1.it": ["DAZN.1.it.it"],
    "Zona.DAZN.it": ["DAZN.1.it.it"],
    "zonadazn.it": ["DAZN.1.it.it"],

    # Club
    "Milan TV": ["Milan.TV.it"],
    "Milan.TV.it": ["Milan.TV.it"],
    "Inter TV": ["inter-it"],
    "inter-it": ["inter-it"],
    "Inter.it": ["inter-it"],

    # RSI Svizzera
    "RSI.La.2.ch": ["RSI.LA.2.ch"],
    "RSI.LA.2.ch": ["RSI.LA.2.ch"],
    "RSI.La2.ch": ["RSI.LA.2.ch"],

    # Eleven Sports PL
    "Eleven.Sports.1.pl": ["Eleven.Sports.1.HD.pl"],
    "Eleven.Sports.2.pl": ["Eleven.Sports.2.HD.pl"],
    "Eleven.Sports.3.pl": ["Eleven.Sports.3.HD.pl"],
    "Eleven.Sports.4.pl": ["Eleven.Sports.4.HD.pl"],
    "Eleven.Sports.1.HD.pl": ["Eleven.Sports.1.HD.pl"],
    "Eleven.Sports.2.HD.pl": ["Eleven.Sports.2.HD.pl"],
    "Eleven.Sports.3.HD.pl": ["Eleven.Sports.3.HD.pl"],
    "Eleven.Sports.4.HD.pl": ["Eleven.Sports.4.HD.pl"],
}

def resolve_target_ids(source_id: str) -> list[str]:
    """Risolve un channel ID sorgente verso i canali target di SuperTeo."""
    if source_id in ID_MAPPING:
        return ID_MAPPING[source_id]
    if source_id in TARGET_IDS:
        return [source_id]
    return []

def download_file(url: str, dest_path: str) -> bool:
    print(f"[*] Download sorgente: {url}")
    try:
        r = requests.get(url, stream=True, timeout=40, headers={"User-Agent": "SuperTeo/2.0 EPG Downloader"})
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
                                    for child in list(elem):
                                        new_child = ET.SubElement(new_prog, child.tag, child.attrib)
                                        new_child.text = child.text
                                    programmes_collected.append(new_prog)
                            root.clear()

            except Exception as e:
                print(f"[!] Errore durante il parsing di {url}: {e}")

        print(f"\n[+] Canali totali unificati: {len(channels_collected)}")
        print(f"[+] Programmi totali indicizzati: {len(programmes_collected)}")

        # Verifica rapida canali chiave (inclusi Cinema & Sky Uno)
        canali_chiave = [
            "AD.Sports.1.HD.ae", "AD.Sports.2.HD.ae",
            "Setanta.Sports.1.HD.lv", "Setanta.Sports.2.HD.lv",
            "Arena.PREMIUM.1.rs", "Arena.Sport.2.rs",
            "Arena.Sport.1.HD.hr", "Sky.Sport.Uno.it", "DAZN.1.it.it",
            "Sky.Uno.it", "Sky.Cinema.Uno.it", "Sky.Cinema.Collection.it"
        ]
        print("\n--- STATO CANALI CHIAVE ---")
        for ck in canali_chiave:
            presente = "SI" if ck in channels_collected else "NO"
            progs = sum(1 for p in programmes_collected if p.attrib.get("channel") == ck)
            print(f" - {ck:<26}: Canale presente = {presente} | Programmi = {progs}")

        # Creazione del documento XML unificato
        root_out = ET.Element("tv", {"generator-info-name": "SuperTeo EPG Generator 2.0"})
        for ch_elem in channels_collected.values():
            root_out.append(ch_elem)
        for pr_elem in programmes_collected:
            root_out.append(pr_elem)

        tree = ET.ElementTree(root_out)
        tree.write(merged_xml_path, encoding="utf-8", xml_declaration=True)

        # Compressione GZIP livello 9
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
