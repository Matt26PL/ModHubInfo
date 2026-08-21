from datetime import datetime
import json
import math
import os
import re
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(
    page_title="FS25 ModHub Manager",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")
except Exception:
    ADMIN_PASSWORD = "admin123"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8",
}
BASE_URL = "https://www.farming-simulator.com/"
START_URL_PL = "https://www.farming-simulator.com/mods.php?lang=pl&country=pl&title=fs2025&filter=latest&page="
JSON_FILE = "mody_fs25.json"
DOMYSLNA_SCIEZKA_MODS = os.path.expanduser(
    r"~\Documents\My Games\FarmingSimulator2025\mods"
)

# SŁOWNIK TŁUMACZEŃ KATEGORII
MAPA_KATEGORII = {
    "small tractors": "🚜 Ciągniki (małe)",
    "medium tractors": "🚜 Ciągniki (średnie)",
    "large tractors": "🚜 Ciągniki (duże)",
    "tractors": "🚜 Ciągniki rolnicze",
    "harvesters": "🌾 Kombajny",
    "harvester headers": "🌾 Hedery do kombajnów",
    "forage harvesters": "🌾 Sieczkarnie samojezdne",
    "forage harvester headers": "🌾 Hedery do sieczkarni",
    "trailers": "🚛 Przyczepy",
    "auger wagons": "🚛 Przyczepy przeładowcze",
    "trucks": "🚚 Ciężarówki",
    "cars": "🚗 Samochody i pojazdy",
    "cultivators": "⚙️ Kultywatory",
    "discs": "⚙️ Brony talerzowe",
    "disc harrows": "⚙️ Brony talerzowe",
    "power harrows": "⚙️ Brony wirnikowe",
    "plows": "⚙️ Pługi",
    "subsoilers": "⚙️ Głębosze",
    "seeders": "🌱 Siewniki",
    "planters": "🌱 Sadzarki",
    "fertilizer spreaders": "🧪 Rozsiewacze nawozów",
    "slurry tanks": "🧪 Beczkowozy gnojowicy",
    "manure spreaders": "🧪 Rozrzutniki obornika",
    "sprayers": "🧪 Opryskiwacze",
    "mowers": "🌿 Kosiarki",
    "tedders": "🌿 Przetrząsacze",
    "windrowers": "🌿 Zgrabiarki",
    "balers": "📦 Prasy do bel",
    "bale loaders": "📦 Przyczepy do bel",
    "bale wrappers": "📦 Owijarki do bel",
    "forestry": "🌲 Maszyny leśne",
    "forestry equipment": "🌲 Osprzęt leśny",
    "forestry trailers": "🌲 Przyczepy leśne",
    "animals": "🐄 Zwierzęta i hodowla",
    "animal pens": "🐄 Zagrody i obory",
    "farmhouses": "🏡 Domy gospodarcze",
    "sheds": "🏚️ Wiaty i garaże",
    "silos": "🏗️ Silosy i magazyny",
    "silo extensions": "🏗️ Rozbudowa silosów",
    "containers": "📦 Kontenery",
    "production sites": "🏭 Fabryki i produkcja",
    "selling points": "💰 Punkty skupu i sprzedaży",
    "greenhouses": "🍅 Szklarnie",
    "generators": "⚡ Generatory i energia",
    "decoration": "🪴 Dekoracje i otoczenie",
    "fences": "🪵 Płoty i ogrodzenia",
    "lights": "💡 Oświetlenie",
    "maps": "🗺️ Mapy",
    "prefabs": "🧱 Prefaby",
    "gameplay": "🎮 Rozgrywka i Skrypty",
    "miscellaneous": "📦 Różne akcesoria",
    "weights": "🏋️ Obciążniki",
    "front loaders": "🚜 Ładowacze czołowe",
    "front loader tools": "🚜 Osprzęt do ładowaczy",
    "telehandlers": "🚜 Ładowarki teleskopowe",
    "telehandler tools": "🚜 Osprzęt teleskopowy",
    "wheel loaders": "🚜 Ładowarki kołowe",
    "wheel loader tools": "🚜 Osprzęt kołowy",
    "skid steers": "🚜 Miniładowarki",
    "skid steer tools": "🚜 Osprzęt miniładowarek",
    "forklifts": "🚜 Wózki widłowe",
    "rollers": "🚜 Wały uprawowe",
    "weeders": "🌱 Chwastowniki i pielniki",
    "mulchers": "🌿 Mulczery i kosiarki",
    "grape technology": "🍇 Uprawa winogron",
    "olive technology": "🫒 Uprawa oliwek",
    "beet technology": "🥔 Maszyny do buraków",
    "potato technology": "🥔 Maszyny do ziemniaków",
    "cotton technology": "☁️ Maszyny do bawełny",
    "sugarcane technology": "🎋 Maszyny do trzciny",
    "inne": "📦 Inne modyfikacje",
}

# NOWOCZESNA STYLIZACJA KAFELKÓW
st.markdown(
    """
<style>
    .mod-card-box {
        background: linear-gradient(145deg, #1e222d, #161922);
        border: 1px solid #2d3343;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 14px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .mod-card-box:hover {
        border-color: #58a6ff;
        transform: translateY(-2px);
    }
    .mod-img-wrapper {
        width: 100%;
        height: 130px;
        border-radius: 8px;
        overflow: hidden;
        background: #11141a;
        margin-bottom: 8px;
    }
    .mod-img-wrapper img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .mod-title-text {
        font-weight: 700;
        font-size: 0.98rem;
        color: #ffffff;
        margin-bottom: 3px;
        line-height: 1.3;
        height: 2.6em;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    .mod-author-text {
        font-size: 0.82rem;
        color: #8b949e;
        margin-bottom: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .badge-pill {
        display: inline-block;
        padding: 3px 7px;
        border-radius: 5px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 4px;
    }
    .badge-size { background-color: #1f6feb; color: #fff; }
    .badge-rating { background-color: #238636; color: #fff; }
    div[data-testid="stButton"] > button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)


def formatuj_czas(sekundy):
    if sekundy < 0 or math.isinf(sekundy) or math.isnan(sekundy):
        return "obliczanie..."
    s = int(sekundy)
    godziny = s // 3600
    minuty = (s % 3600) // 60
    sek = s % 60
    if godziny > 0:
        return f"{godziny} godz. {minuty} min {sek} s"
    elif minuty > 0:
        return f"{minuty} min {sek} s"
    else:
        return f"{sek} s"


def tlumacz_kategorie(tekst):
    t = str(tekst).strip().lower()
    return MAPA_KATEGORII.get(t, f"📦 {str(tekst).title() if tekst else 'Inne'}")


def size_to_mb(size_str):
    match = re.search(r"([\d.,]+)\s*(KB|MB|GB|TB)", size_str, re.IGNORECASE)
    if not match:
        return 0.0
    val = float(match.group(1).replace(",", "."))
    unit = match.group(2).upper()
    if unit == "KB":
        return val / 1024
    elif unit == "MB":
        return val
    elif unit == "GB":
        return val * 1024
    elif unit == "TB":
        return val * 1024 * 1024
    return 0.0


@st.cache_data
def load_data():
    if not os.path.exists(JSON_FILE):
        return pd.DataFrame()

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    kolumny_domyslne = {
        "title": "Brak tytułu",
        "author": "Nieznany",
        "category": "Inne",
        "size_mb": 0.0,
        "size_raw": "0 MB",
        "rating": 0.0,
        "votes": 0,
        "image_url": "",
        "download_url": "",
        "filename": "",
        "url": "",
        "release_date": "",
    }
    for col, val in kolumny_domyslne.items():
        if col not in df.columns:
            df[col] = val
        else:
            df[col] = df[col].fillna(val)

    df["author"] = df["author"].astype(str).str.strip()
    df["category"] = df["category"].apply(tlumacz_kategorie)

    df["size_mb"] = pd.to_numeric(df["size_mb"], errors="coerce").fillna(0.0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0)

    df["mod_id"] = df["url"].apply(
        lambda x: (
            re.search(r"mod_id=(\d+)", str(x)).group(1)
            if re.search(r"mod_id=(\d+)", str(x))
            else ""
        )
    )

    df["date"] = pd.to_datetime(
        df["release_date"], format="%d.%m.%Y", errors="coerce"
    )
    return df.drop_duplicates(subset=["url"])


df = load_data()

# STAN SESJI
if "basket" not in st.session_state:
    st.session_state["basket"] = {}
if "selected_category" not in st.session_state:
    st.session_state["selected_category"] = None
if "selected_page_num" not in st.session_state:
    st.session_state["selected_page_num"] = 1


def pobierz_plik_moda(row, folder_docelowy, on_chunk=None):
    try:
        download_url = row.get("download_url", "")
        mod_url = row.get("url", "")
        filename = row.get("filename", "")

        if not download_url:
            r = requests.get(
                mod_url,
                headers={**HEADERS, "Referer": BASE_URL},
                timeout=12,
            )
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    if (
                        ".zip" in a["href"].lower()
                        or "downloadFile.php" in a["href"]
                    ):
                        download_url = urljoin(BASE_URL, a["href"])
                        break

        if not download_url:
            return False, "Brak linku pobierania na serwerze"

        req_headers = HEADERS.copy()
        req_headers["Referer"] = mod_url

        with requests.get(
            download_url,
            headers=req_headers,
            stream=True,
            timeout=120,
            allow_redirects=True,
        ) as file_req:
            if file_req.status_code != 200:
                return False, f"Błąd HTTP {file_req.status_code}"

            if not filename or not filename.endswith(".zip"):
                content_disp = file_req.headers.get("content-disposition", "")
                fn_m = re.search(r'filename="?([^";]+)"?', content_disp)
                if fn_m:
                    filename = fn_m.group(1)
                else:
                    filename = f"FS25_mod_{row.get('mod_id', 'mod')}.zip"

            target_path = os.path.join(folder_docelowy, filename)

            with open(target_path, "wb") as f:
                for chunk in file_req.iter_content(chunk_size=131072):
                    if chunk:
                        f.write(chunk)
                        if on_chunk:
                            on_chunk(len(chunk))

            if os.path.getsize(target_path) < 2048:
                return False, "Pobrany plik był pusty lub zablokowany"

        return True, filename
    except Exception as e:
        return False, str(e)


# FUNKCJA PARSUJĄCA DLA PANELU ADMINA
def parsuj_pojedynczy_mod_online(url):
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
        "image_url": "",
        "download_url": "",
        "filename": "",
    }
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            h2 = soup.find("h2")
            if h2:
                dane["title"] = h2.get_text(strip=True)

            for img in soup.find_all("img", src=True):
                src = img["src"]
                if any(
                    b in src.lower()
                    for b in ["flag", "logo", "icon", "lang", "social"]
                ):
                    continue
                if (
                    "modhub" in src.lower()
                    or "mods" in src.lower()
                    or "imgs" in src.lower()
                    or "storage" in src.lower()
                ):
                    dane["image_url"] = urljoin(BASE_URL, src).replace(
                        "http://", "https://"
                    )
                    break

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
                    dane["size_mb"] = size_to_mb(lines[i + 1])
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

            fn_match = re.search(
                r"(?:Nazwa pliku|Filename)[\s.:]+([a-zA-Z0-9_\-\.]+\.zip)",
                text_full,
                re.IGNORECASE,
            )
            if fn_match:
                dane["filename"] = fn_match.group(1).strip()
    except Exception:
        pass
    return dane


# NAGŁÓWEK GŁÓWNY
st.title("🚜 Farming Simulator 25 – ModHub Manager")
st.caption(
    "Centrum analityki, automatyczny menedżer paczek i wizualny eksplorator ModHuba"
)
st.markdown("---")

# METRYKI
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📦 Wszystkich modów", f"{len(df):,}")
c2.metric(
    "💾 Całkowita waga",
    f"{df['size_mb'].sum() / 1024:.2f} GB" if not df.empty else "0 GB",
)
c3.metric(
    "⭐ Średnia ocen",
    (
        f"{df[df['rating'] > 0]['rating'].mean():.2f} / 5.0"
        if not df.empty and len(df[df["rating"] > 0]) > 0
        else "N/A"
    ),
)
c4.metric(
    "🗳️ Oddanych głosów",
    f"{df['votes'].sum():,}" if not df.empty and "votes" in df else "N/A",
)
c5.metric(
    "👨‍🌾 Liczba autorów", f"{df['author'].nunique():,}" if not df.empty else "0"
)

st.markdown("---")

# 7 GŁÓWNYCH ZAKŁADEK
(
    tab_modhub,
    tab_koszyk,
    tab_statystyki,
    tab_top,
    tab_giants,
    tab_szukaj,
    tab_admin,
) = st.tabs(
    [
        "🎮 ModHub Visual Hub",
        "🛒 Twoja Paczka & Pobieranie",
        "📊 Statystyki & Wykresy",
        "🏆 TOP Rankingi",
        "🕒 Harmonogram GIANTS",
        "🔍 Wyszukiwarka & Tabela",
        "⚙️ Panel Administratora",
    ]
)

# ==========================================
# ZAKŁADKA 1: WIZUALNY MODHUB ZE ZDJĘCIAMI (PROXIED)
# ==========================================
with tab_modhub:
    basket_count = len(st.session_state["basket"])
    basket_mb = sum(
        m.get("size_mb", 0.0) for m in st.session_state["basket"].values()
    )
    basket_gb = basket_mb / 1024

    top_c1, top_c2 = st.columns([3, 1])
    with top_c1:
        st.subheader("Wybierz kategorię i skomponuj paczkę modów:")
    with top_c2:
        if basket_count > 0:
            st.success(
                f"🛒 W paczce: **{basket_count} modów** ({basket_gb:.2f} GB)"
            )
        else:
            st.info("🛒 Paczka jest pusta")

    kategorie_lista = sorted(df["category"].unique()) if not df.empty else []

    st.markdown("##### ⚡ Szybki wybór kategorii z listy:")
    wybrana_z_listy = st.selectbox(
        "Wybierz kategorię:",
        options=["-- Wybierz kategorię z listy --"] + kategorie_lista,
        index=(
            kategorie_lista.index(st.session_state["selected_category"]) + 1
            if st.session_state["selected_category"] in kategorie_lista
            else 0
        ),
        label_visibility="collapsed",
    )

    if wybrana_z_listy != "-- Wybierz kategorię z listy --":
        if st.session_state["selected_category"] != wybrana_z_listy:
            st.session_state["selected_category"] = wybrana_z_listy
            st.session_state["selected_page_num"] = 1
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state["selected_category"] is None:
        st.markdown("### 📁 Lub kliknij w kafelek poniżej:")
        cols_per_row = 3
        for i in range(0, len(kategorie_lista), cols_per_row):
            row_cats = kategorie_lista[i : i + cols_per_row]
            cols = st.columns(cols_per_row)
            for j, cat in enumerate(row_cats):
                mod_cnt = len(df[df["category"] == cat])
                total_c_gb = df[df["category"] == cat]["size_mb"].sum() / 1024
                label = f"**{cat}**\n\n📦 {mod_cnt} modów &nbsp;|&nbsp; 💾 {total_c_gb:.1f} GB"
                if cols[j].button(
                    label, key=f"c_btn_{cat}", use_container_width=True
                ):
                    st.session_state["selected_category"] = cat
                    st.session_state["selected_page_num"] = 1
                    st.rerun()

    else:
        current_cat = st.session_state["selected_category"]
        col_back, col_cat_title = st.columns([1.2, 4])
        with col_back:
            if st.button(
                "⬅ Wróć do kafelków",
                type="secondary",
                use_container_width=True,
            ):
                st.session_state["selected_category"] = None
                st.rerun()
        with col_cat_title:
            st.markdown(f"### Kategoria: **{current_cat}**")

        cat_df = df[df["category"] == current_cat].copy()
        search_in_cat = st.text_input(
            f"🔎 Szukaj w {current_cat}:",
            "",
            placeholder="Wpisz nazwę szukanego moda...",
        )
        if search_in_cat:
            cat_df = cat_df[
                cat_df["title"].str.contains(search_in_cat, case=False, na=False)
            ]

        total_mods_cat = len(cat_df)
        PAGE_SIZE = 24
        total_pages = max(1, math.ceil(total_mods_cat / PAGE_SIZE))

        p_col1, p_col2 = st.columns([2, 2])
        with p_col1:
            page_selected = st.selectbox(
                f"📄 Przejdź do strony (łącznie {total_mods_cat} modów):",
                options=list(range(1, total_pages + 1)),
                index=min(
                    st.session_state["selected_page_num"] - 1, total_pages - 1
                ),
                format_func=lambda x: f"Strona {x} z {total_pages}",
            )
            st.session_state["selected_page_num"] = page_selected

        start_idx = (page_selected - 1) * PAGE_SIZE
        page_df = cat_df.iloc[start_idx : start_idx + PAGE_SIZE]

        st.markdown("---")

        cols_grid = 4
        rows = [
            page_df.iloc[i : i + cols_grid]
            for i in range(0, len(page_df), cols_grid)
        ]

        for row_items in rows:
            grid_cols = st.columns(cols_grid)
            for idx, (_, mod) in enumerate(row_items.iterrows()):
                with grid_cols[idx]:
                    mod_id = mod["mod_id"]
                    is_in_basket = mod_id in st.session_state["basket"]

                    # Ustalenie linku do zdjęcia
                    raw_img = mod.get("image_url", "")
                    if not raw_img or "flag" in str(raw_img).lower():
                        raw_img = f"https://www.farming-simulator.com/img/mods/imgs/512x288/mod_{mod_id}.jpg"

                    # UŻYCIE BEZPIECZNEGO PROXY OMIJAJĄCEGO BŁĄD 403
                    proxied_img_url = f"https://wsrv.nl/?url={raw_img}&w=380&output=webp"

                    st.markdown(
                        f"""
                        <div class="mod-card-box">
                            <div>
                                <div class="mod-img-wrapper">
                                    <img src="{proxied_img_url}" loading="lazy" onerror="this.parentElement.style.display='none';" />
                                </div>
                                <div class="mod-title-text" title="{mod['title']}">{mod['title']}</div>
                                <div class="mod-author-text">👤 {mod['author']}</div>
                            </div>
                            <div>
                                <span class="badge-pill badge-size">💾 {mod['size_raw']}</span>
                                <span class="badge-pill badge-rating">⭐ {mod['rating']:.1f} ({int(mod['votes'])})</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if is_in_basket:
                        if st.button(
                            "✅ W paczce (Usuń)",
                            key=f"btn_rem_{mod_id}",
                            type="secondary",
                            use_container_width=True,
                        ):
                            del st.session_state["basket"][mod_id]
                            st.rerun()
                    else:
                        if st.button(
                            "➕ Dodaj do paczki",
                            key=f"btn_add_{mod_id}",
                            type="primary",
                            use_container_width=True,
                        ):
                            st.session_state["basket"][mod_id] = mod.to_dict()
                            st.rerun()

                    st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# ZAKŁADKA 2: PACZKA & POBIERANIE
# ==========================================
with tab_koszyk:
    st.subheader("🛒 Skomponowana paczka modyfikacji")

    if not st.session_state["basket"]:
        st.info(
            "Twoja paczka jest pusta. Przejdź do zakładki '🎮 ModHub Visual Hub' i wybierz mody!"
        )
    else:
        basket_list = list(st.session_state["basket"].values())
        b_df = pd.DataFrame(basket_list)

        total_b_mb = b_df["size_mb"].sum()
        total_b_gb = total_b_mb / 1024

        st.markdown("#### 🌐 Ustaw prędkość swojego łącza internetowego:")
        net_col1, net_col2 = st.columns([3, 1])
        with net_col1:
            user_speed_mbps = st.slider(
                "Prędkość pobierania (Mb/s):",
                min_value=5,
                max_value=1000,
                value=50,
                step=5,
            )
        with net_col2:
            st.metric(
                "Transfer teoretyczny", f"{user_speed_mbps / 8:.1f} MB/s"
            )

        czas_szacowany_sekundy = total_b_mb / (user_speed_mbps / 8)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📦 Wybranych modów", len(b_df))
        m2.metric(
            "💾 Całkowity rozmiar",
            f"{total_b_mb:.1f} MB" if total_b_gb < 1 else f"{total_b_gb:.2f} GB",
        )
        m3.metric(
            f"⏳ Szacowany czas ({user_speed_mbps} Mb/s)",
            formatuj_czas(czas_szacowany_sekundy),
        )

        with m4:
            if st.button(
                "🗑️ Wyczyść cały koszyk", type="secondary", use_container_width=True
            ):
                st.session_state["basket"] = {}
                st.rerun()

        st.markdown("---")
        st.markdown("### 📋 Mody w Twojej paczce (usuwanie pojedynczo):")

        for mod_id, mod_item in list(st.session_state["basket"].items()):
            row_c1, row_c2, row_c3, row_c4 = st.columns([5, 3, 2, 1.5])
            with row_c1:
                st.markdown(f"**{mod_item.get('title', 'Mod')}**")
                st.caption(f"Autor: {mod_item.get('author', 'Nieznany')}")
            with row_c2:
                st.markdown(f"📁 {mod_item.get('category', 'Inne')}")
            with row_c3:
                st.markdown(f"💾 `{mod_item.get('size_raw', '0 MB')}`")
            with row_c4:
                if st.button(
                    "❌ Usuń", key=f"del_mod_{mod_id}", use_container_width=True
                ):
                    del st.session_state["basket"][mod_id]
                    st.rerun()
            st.markdown(
                "<hr style='margin: 4px 0; border-color: #262730;'>",
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### 🚀 Pobierz paczkę bezpośrednio do gry:")

        target_folder = st.text_input(
            "Folder instalacyjny modów FS25 (przy uruchomieniu lokalnym):",
            value=DOMYSLNA_SCIEZKA_MODS,
        )

        b_col1, b_col2 = st.columns(2)
        with b_col1:
            start_btn = st.button(
                f"📥 Rozpocznij pobieranie {len(b_df)} modów (.zip)",
                type="primary",
                use_container_width=True,
            )

        with b_col2:
            pack_json = b_df[
                ["title", "url", "size_raw", "category"]
            ].to_json(orient="records", indent=2, force_ascii=False)
            st.download_button(
                "💾 Eksportuj paczkę do pliku (.json)",
                data=pack_json,
                file_name="paczka_fs25.json",
                mime="application/json",
                use_container_width=True,
            )

        if start_btn:
            if not os.path.exists(target_folder):
                try:
                    os.makedirs(target_folder, exist_ok=True)
                except Exception as e:
                    st.error(f"Nie udało się utworzyć folderu: {e}")
                    st.stop()

            progress_bar = st.progress(0.0)
            status_mod = st.empty()

            live_c1, live_c2, live_c3 = st.columns(3)
            metric_transferred = live_c1.empty()
            metric_speed = live_c2.empty()
            metric_eta = live_c3.empty()

            total_bytes_target = int(total_b_mb * 1024 * 1024)
            tracker = {
                "bytes": 0,
                "last_update": time.time(),
                "start_time": time.time(),
            }

            sukces = 0
            bledy = []

            def on_chunk_downloaded(chunk_len):
                tracker["bytes"] += chunk_len
                now = time.time()
                if now - tracker["last_update"] > 0.2:
                    tracker["last_update"] = now
                    elapsed = now - tracker["start_time"]
                    if elapsed > 0:
                        current_speed_MBps = (
                            tracker["bytes"] / (1024 * 1024)
                        ) / elapsed
                        remaining_bytes = max(
                            0, total_bytes_target - tracker["bytes"]
                        )
                        remaining_MB = remaining_bytes / (1024 * 1024)
                        eta_seconds = (
                            remaining_MB / current_speed_MBps
                            if current_speed_MBps > 0
                            else 0
                        )

                        pobrane_mb = tracker["bytes"] / (1024 * 1024)
                        procent = (
                            min(
                                1.0,
                                tracker["bytes"] / total_bytes_target,
                            )
                            if total_bytes_target > 0
                            else 0.0
                        )

                        progress_bar.progress(procent)
                        metric_transferred.metric(
                            "💾 Pobrany transfer",
                            f"{pobrane_mb:.1f} / {total_b_mb:.1f} MB ({int(procent*100)}%)",
                        )
                        metric_speed.metric(
                            "⚡ Prędkość na żywo",
                            f"{current_speed_MBps:.2f} MB/s ({current_speed_MBps*8:.1f} Mb/s)",
                        )
                        metric_eta.metric(
                            "⏳ Pozostały czas", formatuj_czas(eta_seconds)
                        )

            for idx, (_, row) in enumerate(b_df.iterrows(), start=1):
                status_mod.markdown(
                    f"⏳ **Pobieranie [{idx}/{len(b_df)}]:** `{row['title']}` ({row['size_raw']})"
                )
                ok, res = pobierz_plik_moda(
                    row, target_folder, on_chunk=on_chunk_downloaded
                )
                if ok:
                    sukces += 1
                else:
                    bledy.append(f"{row['title']}: {res}")

            progress_bar.progress(1.0)
            status_mod.empty()
            calkowity_czas = time.time() - tracker["start_time"]
            st.success(
                f"🎉 Pomyślnie pobrano **{sukces} modów** do `{target_folder}` w czasie: **{formatuj_czas(calkowity_czas)}**!"
            )
            if bledy:
                st.error("Błędy przy pobieraniu:")
                for b in bledy:
                    st.write(f"- {b}")

# ==========================================
# ZAKŁADKA 3: STATYSTYKI & WYKRESY
# ==========================================
with tab_statystyki:
    st.subheader("📊 Pełne Statystyki i Analityka ModHuba")
    if not df.empty:
        st_c1, st_c2 = st.columns(2)
        with st_c1:
            st.markdown("#### 💾 Rozkład wagi bazy wg kategorii (GB)")
            cat_w = (
                df.groupby("category")["size_mb"]
                .sum()
                .reset_index()
                .sort_values(by="size_mb", ascending=False)
            )
            cat_w["size_gb"] = cat_w["size_mb"] / 1024
            fig_cat_w = px.pie(
                cat_w.head(12),
                names="category",
                values="size_gb",
                hole=0.4,
                title="TOP 12 najcięższych kategorii (GB)",
            )
            st.plotly_chart(fig_cat_w, use_container_width=True)

        with st_c2:
            st.markdown("#### 📦 Liczba modyfikacji w kategoriach")
            cat_counts = (
                df["category"]
                .value_counts()
                .reset_index()
                .rename(columns={"index": "Kategoria", "count": "Liczba modów"})
            )
            fig_cat_c = px.bar(
                cat_counts.head(12),
                x="category",
                y="Liczba modów",
                title="TOP 12 kategorii z największą liczbą modów",
                color="Liczba modów",
                color_continuous_scale="Viridis",
            )
            st.plotly_chart(fig_cat_c, use_container_width=True)

        st.markdown("---")
        st_c3, st_c4 = st.columns(2)

        with st_c3:
            st.markdown("#### 👨‍🌾 TOP 15 Najaktywniejszych Modderów")
            top_auth = (
                df[df["author"] != "Nieznany"]["author"]
                .value_counts()
                .head(15)
                .reset_index()
            )
            top_auth.columns = ["Autor", "Liczba modów"]
            fig_auth = px.bar(
                top_auth,
                x="Liczba modów",
                y="Autor",
                orientation="h",
                color="Liczba modów",
                color_continuous_scale="Blues",
            )
            fig_auth.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_auth, use_container_width=True)

        with st_c4:
            st.markdown("#### ⚖️ Średnia waga pojedynczego moda (MB)")
            cat_avg = (
                df.groupby("category")["size_mb"]
                .mean()
                .reset_index()
                .sort_values(by="size_mb", ascending=False)
            )
            fig_avg = px.bar(
                cat_avg.head(12),
                x="category",
                y="size_mb",
                title="Średnia waga moda w kategorii (MB)",
                labels={"category": "Kategoria", "size_mb": "Średnia (MB)"},
                color="size_mb",
                color_continuous_scale="Reds",
            )
            st.plotly_chart(fig_avg, use_container_width=True)

# ==========================================
# ZAKŁADKA 4: TOP RANKINGI
# ==========================================
with tab_top:
    if not df.empty:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader("⭐ TOP 20 Najwyżej Ocenianych (min. 50 ocen)")
            st.dataframe(
                df[df["votes"] >= 50]
                .sort_values(by=["rating", "votes"], ascending=[False, False])
                .head(20)[
                    ["title", "author", "rating", "votes", "size_raw", "url"]
                ],
                column_config={
                    "url": st.column_config.LinkColumn("Link"),
                    "rating": st.column_config.NumberColumn(
                        "Ocena", format="%.2f ⭐"
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )
        with col_t2:
            st.subheader("🔥 TOP 20 Najpopularniejszych (liczba głosów)")
            st.dataframe(
                df.sort_values(by="votes", ascending=False).head(20)[
                    ["title", "author", "votes", "rating", "size_raw", "url"]
                ],
                column_config={
                    "url": st.column_config.LinkColumn("Link"),
                    "rating": st.column_config.NumberColumn(
                        "Ocena", format="%.1f ⭐"
                    ),
                    "votes": st.column_config.NumberColumn(
                        "Głosy", format="%d 🗳️"
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )

# ==========================================
# ZAKŁADKA 5: DNI TYGODNIA GIANTS
# ==========================================
with tab_giants:
    st.subheader("🕒 Kiedy moderatorzy GIANTS publikują mody?")
    if not df.empty:
        df_d = df.dropna(subset=["date"]).copy()
        if not df_d.empty:
            dni = {
                "Monday": "1. Poniedziałek",
                "Tuesday": "2. Wtorek",
                "Wednesday": "3. Środa",
                "Thursday": "4. Czwartek",
                "Friday": "5. Piątek",
                "Saturday": "6. Sobota",
                "Sunday": "7. Niedziela",
            }
            df_d["Dzień"] = df_d["date"].dt.day_name().map(dni)
            g1, g2 = st.columns(2)
            with g1:
                d_cnt = (
                    df_d["Dzień"]
                    .value_counts()
                    .reset_index()
                    .sort_values(by="Dzień")
                )
                d_cnt.columns = ["Dzień tygodnia", "Wydanych modów"]
                st.plotly_chart(
                    px.bar(
                        d_cnt,
                        x="Dzień tygodnia",
                        y="Wydanych modów",
                        color="Wydanych modów",
                        color_continuous_scale="Teal",
                    ),
                    use_container_width=True,
                )
            with g2:
                df_d["Miesiąc"] = df_d["date"].dt.to_period("M").astype(str)
                m_cnt = (
                    df_d["Miesiąc"]
                    .value_counts()
                    .reset_index()
                    .sort_values(by="Miesiąc")
                )
                m_cnt.columns = ["Miesiąc", "Liczba"]
                st.plotly_chart(
                    px.line(m_cnt, x="Miesiąc", y="Liczba", markers=True),
                    use_container_width=True,
                )

# ==========================================
# ZAKŁADKA 6: WYSZUKIWARKA & TABELA
# ==========================================
with tab_szukaj:
    st.subheader("🔍 Klasyczna wyszukiwarka i filtry")
    if not df.empty:
        s_f1, s_f2 = st.columns(2)
        with s_f1:
            s_title = st.text_input("Szukaj po nazwie:", key="s_tab_title")
        with s_f2:
            s_cat = st.multiselect(
                "Kategorie:",
                options=sorted(df["category"].unique()),
                key="s_tab_cat",
            )

        f_res = df.copy()
        if s_title:
            f_res = f_res[
                f_res["title"].str.contains(s_title, case=False, na=False)
            ]
        if s_cat:
            f_res = f_res[f_res["category"].isin(s_cat)]

        st.dataframe(
            f_res[
                [
                    "title",
                    "author",
                    "category",
                    "size_raw",
                    "rating",
                    "votes",
                    "url",
                ]
            ],
            column_config={"url": st.column_config.LinkColumn("Link")},
            hide_index=True,
            use_container_width=True,
        )

# ==========================================
# ZAKŁADKA 7: PANEL ADMINISTRATORA
# ==========================================
with tab_admin:
    st.subheader("⚙️ Panel Zarządzania Bazą ModHub Online")
    st.write("Z tego miejsca możesz zaktualizować bazę o nowości z poziomu przeglądarki.")

    haslo_input = st.text_input(
        "Podaj hasło administratora:", type="password", key="admin_pass_input"
    )

    if haslo_input == ADMIN_PASSWORD:
        st.success("🔓 Zalogowano do panelu administratora!")

        st.markdown("#### 🔄 Szybka aktualizacja bazy (Nowości z ModHuba)")
        st.caption(
            "Sprawdza najnowsze strony ModHuba i dopisuje tylko brakujące nowe mody."
        )
        if st.button(
            "🚀 Uruchom aktualizację nowości", type="primary", key="btn_adm_upd"
        ):
            with st.spinner("Sprawdzanie nowości na ModHubie..."):
                if os.path.exists(JSON_FILE):
                    with open(JSON_FILE, "r", encoding="utf-8") as f:
                        istniejace = json.load(f)
                else:
                    istniejace = []

                znane_id = {
                    str(m.get("mod_id"))
                    for m in istniejace
                    if m.get("mod_id") is not None
                }
                nowe_linki = []
                page = 0
                koniec = False

                while not koniec:
                    url = f"{START_URL_PL}{page}"
                    try:
                        r = requests.get(url, headers=HEADERS, timeout=10)
                        if r.status_code != 200:
                            break
                        soup = BeautifulSoup(r.text, "html.parser")
                        znalezione = 0
                        for a in soup.find_all("a", href=True):
                            if (
                                "mod.php?" in a["href"]
                                and "mod_id=" in a["href"]
                            ):
                                full_url = urljoin(BASE_URL, a["href"])
                                mod_id = re.search(
                                    r"mod_id=(\d+)", a["href"]
                                ).group(1)
                                if mod_id in znane_id:
                                    koniec = True
                                    break
                                if full_url not in nowe_linki:
                                    nowe_linki.append(full_url)
                                    znalezione += 1
                        if znalezione == 0:
                            break
                        page += 1
                    except Exception:
                        break

                if not nowe_linki:
                    st.info("Baza jest w 100% aktualna! Brak nowych modów.")
                else:
                    nowo_pobrane = []
                    prog_upd = st.progress(0.0)
                    for i, l in enumerate(nowe_linki, start=1):
                        nowo_pobrane.append(parsuj_pojedynczy_mod_online(l))
                        prog_upd.progress(i / len(nowe_linki))
                        time.sleep(0.1)

                    calosc = nowo_pobrane + istniejace
                    with open(JSON_FILE, "w", encoding="utf-8") as f:
                        json.dump(calosc, f, ensure_ascii=False, indent=2)

                    st.success(
                        f"🎉 Dodano {len(nowo_pobrane)} nowych modów do bazy!"
                    )
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()

        st.markdown("---")
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                json_str = f.read()
            st.download_button(
                "💾 Pobierz aktualny plik `mody_fs25.json` na swój komputer",
                data=json_str,
                file_name="mody_fs25.json",
                mime="application/json",
            )
    elif haslo_input:
        st.error("❌ Nieprawidłowe hasło administratora.")
