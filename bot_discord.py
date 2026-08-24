import json
import os
import re
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# TWÓJ WEBHOOK DISCORD:
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1541547769897156711/76BIq23soyJ0oeNbiwy7fH2_ZlOB805_BilRtLroMmwhr8RoA11Fa-I3-Kh1_Q31oIoh"

# TUTAJ MOŻESZ WKLEIĆ ADRES SWOJEJ STRONY W SIECI (np. https://twoja-nazwa.streamlit.app):
PAGE_URL = "https://share.streamlit.io/"

JSON_FILE = "mody_fs25.json"
BASE_URL = "https://www.farming-simulator.com/"
START_URL_PL = "https://www.farming-simulator.com/mods.php?lang=pl&country=pl&title=fs2025&filter=latest&page=0"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8",
}


def wyslij_powiadomienie_discord(mod, is_update=False):
    """Wysyła pojedynczą kartę moda na Discorda."""
    if not DISCORD_WEBHOOK_URL:
        return False

    embed_color = 0x8957E5 if is_update else 0x238636
    tag_tytul = "🔄 AKTUALIZACJA MODA!" if is_update else "🟢 NOWY MOD NA MODHUBIE!"

    embed = {
        "title": f"{tag_tytul}\n{mod.get('title', 'Nowa modyfikacja')}",
        "url": mod.get("url", BASE_URL),
        "color": embed_color,
        "fields": [
            {
                "name": "👤 Autor",
                "value": str(mod.get("author", "Nieznany")),
                "inline": True,
            },
            {
                "name": "📁 Kategoria",
                "value": str(mod.get("category", "Inne")),
                "inline": True,
            },
            {
                "name": "💾 Rozmiar pliku",
                "value": f"`{mod.get('size_raw', '0 MB')}`",
                "inline": True,
            },
            {
                "name": "⭐ Ocena graczy",
                "value": f"⭐ **{mod.get('rating', 0.0):.1f}** ({int(mod.get('votes', 0))} głosów)",
                "inline": True,
            },
            {
                "name": "🔢 Wersja",
                "value": f"`{mod.get('version', '1.0.0.0')}`",
                "inline": True,
            },
            {
                "name": "📅 Data publikacji",
                "value": str(mod.get("release_date", "Dzisiaj")),
                "inline": True,
            },
        ],
        "footer": {
            "text": "🚜 FS25 ModHub Watcher • Kliknij tytuł, aby zobaczyć mod",
            "icon_url": "https://www.farming-simulator.com/favicon.ico",
        },
    }

    payload = {
        "username": "FS25 ModHub Bot",
        "avatar_url": "https://www.farming-simulator.com/favicon.ico",
        "embeds": [embed],
    }

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        return r.status_code in [200, 204]
    except Exception as e:
        print(f"Błąd wysyłania na Discorda: {e}")
        return False


def wyslij_raport_statystyk(wszystkie_mody, nowo_dodane_mody):
    """Wysyła zbiorczą złotą kartę ze statystykami całej bazy i fali wydań."""
    if not DISCORD_WEBHOOK_URL or not nowo_dodane_mody:
        return False

    lacznie_modow = len(wszystkie_mody)
    laczna_waga_gb = (
        sum(float(m.get("size_mb", 0.0)) for m in wszystkie_mody) / 1024
    )

    nowosci_cnt = sum(
        1
        for m in nowo_dodane_mody
        if m.get("version", "1.0.0.0") in ["1.0.0.0", "1.0.0", "1.0"]
    )
    latki_cnt = len(nowo_dodane_mody) - nowosci_cnt
    waga_fali_mb = sum(
        float(m.get("size_mb", 0.0)) for m in nowo_dodane_mody
    )

    embed = {
        "title": "📊 RAPORT MODHUBA – PODSUMOWANIE FALI WYDAŃ",
        "url": PAGE_URL,
        "description": f"Właśnie zaktualizowano bazę modyfikacji FS25 o **{len(nowo_dodane_mody)} nowych pozycji**!",
        "color": 0xF1C40F,  # Złoty kolor
        "fields": [
            {
                "name": "🆕 W tej fali wydań",
                "value": f"🟢 Nowości: **{nowosci_cnt}** | 🔄 Łatki: **{latki_cnt}**\n💾 Waga fali: **{waga_fali_mb:.1f} MB**",
                "inline": False,
            },
            {
                "name": "📦 Łączny stan ModHuba",
                "value": f"Wszystkich modów: **{lacznie_modow:,}**\nCałkowita waga: **{laczna_waga_gb:.2f} GB**",
                "inline": True,
            },
            {
                "name": "🌐 Zobacz Statystyki Online",
                "value": f"[Otwórz pełny Dashboard WWW]({PAGE_URL})",
                "inline": True,
            },
        ],
        "footer": {
            "text": "🚜 FS25 Analytics & Watcher • Pełne statystyki w serwisie WWW",
            "icon_url": "https://www.farming-simulator.com/favicon.ico",
        },
    }

    payload = {
        "username": "FS25 ModHub Bot",
        "avatar_url": "https://www.farming-simulator.com/favicon.ico",
        "embeds": [embed],
    }

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        return r.status_code in [200, 204]
    except Exception as e:
        print(f"Błąd wysyłania raportu: {e}")
        return False


def parsuj_pojedynczy_mod(url):
    dane = {
        "url": url,
        "mod_id": (
            re.search(r"mod_id=(\d+)", url).group(1)
            if "mod_id=" in url
            else ""
        ),
        "title": "Nieznany",
        "author": "Nieznany",
        "category": "Inne",
        "size_raw": "0 MB",
        "size_mb": 0.0,
        "rating": 0.0,
        "votes": 0,
        "version": "1.0.0.0",
        "release_date": "",
        "download_url": "",
        "filename": "",
        "updates_count": 0,
        "version_history": [],
    }

    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            h2 = soup.find("h2")
            if h2:
                dane["title"] = h2.get_text(strip=True)

            for a in soup.find_all("a", href=True):
                if (
                    ".zip" in a["href"].lower()
                    or "downloadFile.php" in a["href"]
                ):
                    dane["download_url"] = urljoin(BASE_URL, a["href"])
                    break

            text_full = soup.get_text(separator="\n")
            lines = [
                line.strip() for line in text_full.split("\n") if line.strip()
            ]
            for i, line in enumerate(lines):
                l = line.rstrip(":.").lower()
                if l in ["autor", "author"] and i + 1 < len(lines):
                    dane["author"] = lines[i + 1]
                elif l in ["kategoria", "category"] and i + 1 < len(lines):
                    dane["category"] = lines[i + 1]
                elif l in ["rozmiar", "size"] and i + 1 < len(lines):
                    dane["size_raw"] = lines[i + 1]
                    m_sz = re.search(r"[\d.,]+", lines[i + 1])
                    dane["size_mb"] = (
                        float(m_sz.group(0).replace(",", ".")) if m_sz else 0.0
                    )
                elif l in ["wersja", "version"] and i + 1 < len(lines):
                    dane["version"] = lines[i + 1]
                elif l in ["data wydania", "released"] and i + 1 < len(lines):
                    dane["release_date"] = lines[i + 1]

            match_rating = re.search(
                r"(?:Ocena użytkowników|User Rating)[\s.:]+([\d.,]+)\s*\(([\d\s.,]+)\)",
                text_full,
                re.IGNORECASE,
            )
            if match_rating:
                dane["rating"] = float(match_rating.group(1).replace(",", "."))
                dane["votes"] = int(
                    re.sub(r"[^\d]", "", match_rating.group(2))
                )
    except Exception:
        pass

    return dane


def sprawdz_nowosci_i_powiadom():
    if not os.path.exists(JSON_FILE):
        print(f"❌ Brak pliku {JSON_FILE}!")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        istniejace = json.load(f)

    znane_id = {
        str(m.get("mod_id"))
        for m in istniejace
        if m.get("mod_id") is not None
    }

    print("🔍 Sprawdzanie najnowszych modów na ModHubie...")
    try:
        r = requests.get(START_URL_PL, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            print(f"Błąd HTTP {r.status_code}")
            return

        soup = BeautifulSoup(r.text, "html.parser")
        nowe_linki = []

        for a in soup.find_all("a", href=True):
            if "mod.php?" in a["href"] and "mod_id=" in a["href"]:
                full_url = urljoin(BASE_URL, a["href"])
                mod_id = re.search(r"mod_id=(\d+)", a["href"]).group(1)

                if mod_id not in znane_id and full_url not in nowe_linki:
                    nowe_linki.append(full_url)

        if not nowe_linki:
            print("✅ Brak nowych modów – Discord jest na bieżąco.")
            return

        print(
            f"🆕 Wykryto {len(nowe_linki)} nowych modów! Wysyłanie kart na Discord..."
        )

        nowo_dodane = []
        for url in reversed(nowe_linki):
            mod_data = parsuj_pojedynczy_mod(url)
            is_upd = mod_data.get("version", "1.0.0.0") not in [
                "1.0.0.0",
                "1.0.0",
                "1.0",
            ]

            wyslij_powiadomienie_discord(mod_data, is_update=is_upd)
            print(
                f"   📢 Wysłano mod: {mod_data['title']} ({mod_data['author']})"
            )
            nowo_dodane.append(mod_data)
            time.sleep(1)

        # Zapis do bazy
        calosc = nowo_dodane + istniejace
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(calosc, f, ensure_ascii=False, indent=2)

        # Na koniec wysyłamy ZŁOTY RAPORT ZE STATYSTYKAMI
        print("📊 Wysyłanie raportu podsumowującego...")
        wyslij_raport_statystyk(calosc, nowo_dodane)

        print(f"🎉 Sukces! Wysłano powiadomienia i raport ze statystykami.")

    except Exception as e:
        print(f"Błąd: {e}")


def wyslij_testowy_raport():
    """Wysyła testową kartę raportu podsumowującego."""
    if not os.path.exists(JSON_FILE):
        return
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        baza = json.load(f)

    testowe_nowosci = [
        {
            "title": "Bizon Z056",
            "author": "Modder",
            "version": "1.0.0.0",
            "size_mb": 45.0,
        },
        {
            "title": "Courseplay",
            "author": "CP Team",
            "version": "1.1.0.0",
            "size_mb": 12.0,
        },
    ]
    print("🚀 Wysyłanie testowego Raportu Statystyk na Discord...")
    wyslij_raport_statystyk(baza, testowe_nowosci)
    print("✅ Raport ze statystykami pojawił się na Discordzie!")


if __name__ == "__main__":
    # Sprawdzamy nowości i wysyłamy powiadomienia na Discord
    sprawdz_nowosci_i_powiadom()