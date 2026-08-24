from datetime import datetime, date
import io
import json
import math
import os
import re
import time
from urllib.parse import urljoin
import zipfile
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit.components.v1 as components

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

# STYLIZACJA CSS
st.markdown(
    """
<style>
    .mod-card-box {
        background: linear-gradient(145deg, #1e222d, #161922);
        border: 1px solid #2d3343;
        border-radius: 12px;
        padding: 14px;
        margin-bottom: 14px;
        min-height: 185px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .mod-card-box:hover {
        border-color: #58a6ff;
        transform: translateY(-2px);
    }
    .mod-top-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .mod-icon {
        font-size: 1.8rem;
    }
    .mod-title-link {
        font-weight: 700;
        font-size: 1.05rem;
        color: #58a6ff !important;
        text-decoration: none;
        line-height: 1.3;
        height: 2.6em;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        margin-bottom: 4px;
    }
    .mod-title-link:hover {
        color: #79c0ff !important;
        text-decoration: underline;
    }
    .mod-author-text {
        font-size: 0.84rem;
        color: #8b949e;
        margin-bottom: 10px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .badge-pill {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 600;
        margin-right: 4px;
        margin-bottom: 3px;
    }
    .badge-size { background-color: #1f6feb; color: #fff; }
    .badge-rating { background-color: #238636; color: #fff; }
    .badge-patch { background-color: #8957e5; color: #fff; }
    .btn-dl-link {
        display: inline-block;
        background-color: #238636;
        color: white !important;
        text-decoration: none;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        text-align: center;
        border: 1px solid #2ea043;
    }
    .btn-dl-link:hover {
        background-color: #2ea043;
        text-decoration: none;
    }
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


def parsuj_elastyczna_date(val):
    if pd.isna(val) or not str(val).strip():
        return pd.NaT
    s = str(val).strip()

    m_dot = re.search(r"(\d{1,2})[\./\-](\d{1,2})[\./\-](\d{2,4})", s)
    if m_dot:
        d, m, y = int(m_dot.group(1)), int(m_dot.group(2)), int(m_dot.group(3))
        if y < 100:
            y += 2000
        try:
            return datetime(y, m, d)
        except Exception:
            pass

    m_iso = re.search(r"(\d{4})[\./\-](\d{1,2})[\./\-](\d{1,2})", s)
    if m_iso:
        y, m, d = int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3))
        try:
            return datetime(y, m, d)
        except Exception:
            pass

    try:
        return pd.to_datetime(s, dayfirst=True, errors="coerce")
    except Exception:
        return pd.NaT


def oblicz_prawdziwe_aktualizacje(row):
    wersja_glowna = str(row.get("version", "1.0.0.0")).strip()
    historia = row.get("version_history", [])

    unikalne_wersje = set()
    if isinstance(historia, list):
        for wpis in historia:
            m = re.search(r"(\d+\.\d+\.\d+\.\d+)", str(wpis))
            if m:
                unikalne_wersje.add(m.group(1))

    if len(unikalne_wersje) > 1:
        return len(unikalne_wersje) - 1

    if wersja_glowna not in ["1.0.0.0", "1.0.0", "1.0", "1.0.0.0.", ""]:
        m_v = re.search(r"\d+\.(\d+)\.", wersja_glowna)
        if m_v and int(m_v.group(1)) > 0:
            return int(m_v.group(1))
        return 1

    return 0


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
        "version": "1.0.0.0",
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

    if "version_history" not in df.columns:
        df["version_history"] = [[] for _ in range(len(df))]
    else:
        df["version_history"] = df["version_history"].apply(
            lambda x: x if isinstance(x, list) else []
        )

    df["author"] = df["author"].astype(str).str.strip()
    df["category"] = df["category"].apply(tlumacz_kategorie)

    df["size_mb"] = pd.to_numeric(df["size_mb"], errors="coerce").fillna(0.0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
    df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0)

    # Obliczanie aktualizacji
    df["updates_count"] = df.apply(oblicz_prawdziwe_aktualizacje, axis=1)
    df["typ_wydania"] = df["updates_count"].apply(
        lambda x: "🔄 Aktualizacja" if x > 0 else "🟢 Premiera (v1.0)"
    )

    df["mod_id"] = df["url"].apply(
        lambda x: (
            re.search(r"mod_id=(\d+)", str(x)).group(1)
            if re.search(r"mod_id=(\d+)", str(x))
            else ""
        )
    )

    df["date"] = df["release_date"].apply(parsuj_elastyczna_date)
    return df.drop_duplicates(subset=["url"])


df = load_data()

# STAN SESJI
if "basket" not in st.session_state:
    st.session_state["basket"] = {}
if "selected_category" not in st.session_state:
    st.session_state["selected_category"] = None
if "selected_page_num" not in st.session_state:
    st.session_state["selected_page_num"] = 1

# NAGŁÓWEK GŁÓWNY
st.title("🚜 Farming Simulator 25 – ModHub Manager & Analytics")
st.caption(
    "Centrum analityki ModHuba, menedżer paczek i pełna historia aktualizacji"
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
    "🔄 Zaktualizowanych modów",
    f"{len(df[df['updates_count'] > 0]):,} ({len(df[df['updates_count'] > 0])/max(1, len(df))*100:.1f}%)"
    if not df.empty
    else "N/A",
)
c5.metric(
    "👨‍🌾 Liczba autorów", f"{df['author'].nunique():,}" if not df.empty else "0"
)

st.markdown("---")

# 8 GŁÓWNYCH ZAKŁADEK (W TYM PROFILE TWÓRCÓW)
(
    tab_modhub,
    tab_koszyk,
    tab_tworcy,
    tab_statystyki,
    tab_top,
    tab_giants,
    tab_szukaj,
    tab_admin,
) = st.tabs(
    [
        "🎮 ModHub Visual Hub",
        "🛒 Twoja Paczka & Pobieranie",
        "👨‍🌾 Profile Twórców (Hall of Fame)",
        "📊 Statystyki & Wykresy",
        "🏆 TOP Rankingi",
        "🕒 Harmonogram GIANTS",
        "🔍 Wyszukiwarka & Tabela",
        "⚙️ Panel Administratora",
    ]
)

# ==========================================
# ZAKŁADKA 1: WIZUALNY MODHUB
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
                    upd_cnt = mod.get("updates_count", 0)

                    icon = (
                        mod["category"].split()[0]
                        if " " in mod["category"]
                        else "🚜"
                    )

                    patch_badge = (
                        f'<span class="badge-pill badge-patch" title="Liczba aktualizacji">🔄 {upd_cnt} łatki</span>'
                        if upd_cnt > 0
                        else ""
                    )

                    st.markdown(
                        f"""
                        <div class="mod-card-box">
                            <div>
                                <div class="mod-top-row">
                                    <span class="mod-icon">{icon}</span>
                                    <a href="{mod['url']}" target="_blank" style="text-decoration: none; font-size: 0.78rem; color: #58a6ff; background: #21262d; padding: 2px 7px; border-radius: 4px; border: 1px solid #30363d;">
                                        ID: {mod_id} ↗
                                    </a>
                                </div>
                                <a href="{mod['url']}" target="_blank" class="mod-title-link" title="Kliknij, aby otworzyć zdjęcia na ModHubie">
                                    {mod['title']}
                                </a>
                                <div class="mod-author-text">👤 {mod['author']}</div>
                            </div>
                            <div>
                                <span class="badge-pill badge-size">💾 {mod['size_raw']}</span>
                                <span class="badge-pill badge-rating">⭐ {mod['rating']:.1f} ({int(mod['votes'])})</span>
                                {patch_badge}
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
    st.subheader("🛒 Twoja Paczka Modów")

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
        st.markdown("### 🚀 Masowe pobieranie prosto z przeglądarki:")

        urls_do_pobrania = []
        for m in basket_list:
            u = m.get("download_url")
            if not u:
                u = f"https://www.farming-simulator.com/downloadFile.php?mod_id={m.get('mod_id')}"
            urls_do_pobrania.append(u)

        urls_json_str = json.dumps(urls_do_pobrania)

        down_col1, down_col2 = st.columns(2)

        with down_col1:
            st.markdown("#### Sposób 1: Wszystkie pliki naraz")
            st.caption(
                "Przeglądarka po kolei rozpocznie pobieranie każdego modu do folderu Pobrane:"
            )

            js_code = f"""
            <button onclick="pobierzWszystkie()" style="
                background-color: #238636;
                color: white;
                border: 1px solid #2ea043;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 15px;
                cursor: pointer;
                width: 100%;
            ">
                🚀 Pobierz {len(b_df)} plików modów naraz (.zip)
            </button>
            <script>
            function pobierzWszystkie() {{
                const urls = {urls_json_str};
                urls.forEach((url, i) => {{
                    setTimeout(() => {{
                        const a = document.createElement("a");
                        a.href = url;
                        a.target = "_blank";
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    }}, i * 450);
                }});
            }}
            </script>
            """
            components.html(js_code, height=60)

        with down_col2:
            st.markdown("#### Sposób 2: Spakuj do 1 pliku ZIP")
            st.caption("Pobierz jedno zbiorcze archiwum z wybranymi modami:")

            if st.button(
                f"📦 Przygotuj 1 dużą paczkę ZIP ({total_b_mb:.1f} MB)",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner("Pobieranie i pakowanie modów do 1 pliku ZIP..."):
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(
                        zip_buffer, "w", zipfile.ZIP_DEFLATED
                    ) as zip_file:
                        prog_z = st.progress(0.0)
                        for i, m in enumerate(basket_list, start=1):
                            dl_url = m.get("download_url") or f"https://www.farming-simulator.com/downloadFile.php?mod_id={m.get('mod_id')}"
                            fname = m.get("filename") or f"FS25_mod_{m.get('mod_id')}.zip"
                            try:
                                r = requests.get(
                                    dl_url,
                                    headers={
                                        **HEADERS,
                                        "Referer": m.get("url", BASE_URL),
                                    },
                                    timeout=60,
                                )
                                if r.status_code == 200:
                                    zip_file.writestr(fname, r.content)
                            except Exception:
                                pass
                            prog_z.progress(i / len(basket_list))

                    st.download_button(
                        label=f"💾 Zapisz plik `paczka_modow_fs25.zip` na dysku",
                        data=zip_buffer.getvalue(),
                        file_name="paczka_modow_fs25.zip",
                        mime="application/zip",
                        type="primary",
                        use_container_width=True,
                    )

        st.markdown("---")
        st.markdown("### 📋 Lista modów w koszyku (pobieranie pojedyncze):")

        for mod_id, mod_item in list(st.session_state["basket"].items()):
            row_c1, row_c2, row_c3, row_c4, row_c5 = st.columns(
                [4.5, 2.5, 1.8, 1.8, 1.2]
            )
            with row_c1:
                st.markdown(
                    f"**[{mod_item.get('title', 'Mod')}]({mod_item.get('url', '#')})**"
                )
                st.caption(f"Autor: {mod_item.get('author', 'Nieznany')}")
            with row_c2:
                st.markdown(f"📁 {mod_item.get('category', 'Inne')}")
            with row_c3:
                st.markdown(f"💾 `{mod_item.get('size_raw', '0 MB')}`")
            with row_c4:
                dl_url = mod_item.get("download_url", "")
                if not dl_url:
                    dl_url = f"https://www.farming-simulator.com/downloadFile.php?mod_id={mod_id}"
                st.markdown(
                    f'<a href="{dl_url}" class="btn-dl-link" target="_blank">📥 Pobierz</a>',
                    unsafe_allow_html=True,
                )
            with row_c5:
                if st.button(
                    "❌", key=f"del_mod_{mod_id}", help="Usuń z koszyka"
                ):
                    del st.session_state["basket"][mod_id]
                    st.rerun()

            st.markdown(
                "<hr style='margin: 4px 0; border-color: #262730;'>",
                unsafe_allow_html=True,
            )

# ==========================================
# ZAKŁADKA 3: PROFILE TWÓRCÓW (HALL OF FAME)
# ==========================================
with tab_tworcy:
    st.subheader("👨‍🌾 Modder Hall of Fame – Profile i Statystyki Twórców")
    st.write(
        "Wybierz twórcę, aby poznać jego statystyki, największe hity i specjalizację:"
    )

    if not df.empty:
        autorzy_lista = sorted(
            [a for a in df["author"].unique() if a and a != "Nieznany"]
        )

        top_5_popular = (
            df[df["author"] != "Nieznany"]["author"]
            .value_counts()
            .head(5)
            .index.tolist()
        )

        auth_sel_col1, auth_sel_col2 = st.columns([3, 2])

        with auth_sel_col1:
            wybrany_autor = st.selectbox(
                "Wybierz twórcę z listy lub wpisz jego nazwę:",
                options=autorzy_lista,
                index=0 if autorzy_lista else None,
            )

        with auth_sel_col2:
            st.caption("🔥 Szybki wybór najpopularniejszych twórców:")
            chip_cols = st.columns(len(top_5_popular))
            for idx, top_auth_name in enumerate(top_5_popular):
                if chip_cols[idx].button(
                    top_auth_name,
                    key=f"chip_auth_{top_auth_name}",
                    use_container_width=True,
                ):
                    wybrany_autor = top_auth_name
                    st.rerun()

        if wybrany_autor:
            df_auth = df[df["author"] == wybrany_autor].copy()
            mods_count = len(df_auth)
            total_mb_auth = df_auth["size_mb"].sum()
            avg_rating_auth = (
                df_auth[df_auth["rating"] > 0]["rating"].mean()
                if len(df_auth[df_auth["rating"] > 0]) > 0
                else 0.0
            )
            total_votes_auth = df_auth["votes"].sum()
            total_patches_auth = df_auth["updates_count"].sum()

            st.markdown("---")
            st.markdown(f"### 🚜 Profil Twórcy: **{wybrany_autor}**")

            am1, am2, am3, am4, am5 = st.columns(5)
            am1.metric("📦 Wydanych modów", mods_count)
            am2.metric(
                "⭐ Średnia ocena",
                (
                    f"{avg_rating_auth:.2f} / 5.0"
                    if avg_rating_auth > 0
                    else "Brak ocen"
                ),
            )
            am3.metric("🗳️ Łącznie głosów", f"{total_votes_auth:,}")
            am4.metric(
                "💾 Waga wszystkich modów",
                (
                    f"{total_mb_auth:.1f} MB"
                    if total_mb_auth < 1024
                    else f"{total_mb_auth/1024:.2f} GB"
                ),
            )
            am5.metric("🔄 Wydanych patchy", f"{total_patches_auth}")

            st.markdown("---")

            # HITY TWÓRCY
            hit_col1, hit_col2 = st.columns([1.5, 1.5])

            with hit_col1:
                st.markdown("#### 👑 Największe Hity Twórcy")

                # Najwyżej oceniany
                best_rated = df_auth.sort_values(
                    by=["rating", "votes"], ascending=[False, False]
                ).iloc[0]
                # Najpopularniejszy (głosy)
                most_voted_auth = df_auth.sort_values(
                    by="votes", ascending=False
                ).iloc[0]
                # Najcięższy projekt
                heaviest_auth = df_auth.sort_values(
                    by="size_mb", ascending=False
                ).iloc[0]

                st.markdown(
                    f"""
                    * 🥇 **Najwyżej oceniany mod:** [{best_rated['title']}]({best_rated['url']})  
                      ⭐ **{best_rated['rating']:.1f}** ({int(best_rated['votes'])} głosów) | 📁 `{best_rated['category']}`
                    * 🔥 **Najpopularniejszy mod:** [{most_voted_auth['title']}]({most_voted_auth['url']})  
                      🗳️ **{int(most_voted_auth['votes'])}** ocen społeczności | 💾 `{most_voted_auth['size_raw']}`
                    * 🐘 **Największy projekt:** [{heaviest_auth['title']}]({heaviest_auth['url']})  
                      💾 **{heaviest_auth['size_raw']}** | 🔄 {heaviest_auth['updates_count']} patchy
                    """
                )

            with hit_col2:
                st.markdown("#### 🥧 Specjalizacja Twórcy")
                auth_cat_counts = (
                    df_auth["category"]
                    .value_counts()
                    .reset_index()
                    .rename(
                        columns={"index": "Kategoria", "count": "Liczba modów"}
                    )
                )
                fig_spec = px.pie(
                    auth_cat_counts,
                    names="category",
                    values="Liczba modów",
                    hole=0.4,
                    title=f"Kategorie projektów ({wybrany_autor})",
                )
                st.plotly_chart(fig_spec, use_container_width=True)

            st.markdown("---")
            st.markdown(f"#### 📋 Wszystkie modyfikacje twórcy ({mods_count}):")

            st.dataframe(
                df_auth[
                    [
                        "title",
                        "category",
                        "updates_count",
                        "size_raw",
                        "rating",
                        "votes",
                        "url",
                    ]
                ].sort_values(by=["rating", "votes"], ascending=[False, False]),
                column_config={
                    "url": st.column_config.LinkColumn("Otwórz na ModHubie"),
                    "updates_count": st.column_config.NumberColumn(
                        "Łatki 🔄", format="%d"
                    ),
                    "rating": st.column_config.NumberColumn(
                        "Ocena ⭐", format="%.1f"
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )

        st.markdown("---")
        st.markdown("### 🏆 Liga Mistrzów Modderów (TOP 15 Najwyżej Ocenianych)")
        st.caption(
            "Ranking twórców z najwyższą średnią oceną społeczności (dla modderów z minimum 3 modami):"
        )

        hall_of_fame = (
            df[df["author"] != "Nieznany"]
            .groupby("author")
            .agg(
                Liczba_Modow=("title", "count"),
                Srednia_Ocena=(
                    "rating",
                    lambda x: x[x > 0].mean() if len(x[x > 0]) > 0 else 0.0,
                ),
                Lacznie_Glosow=("votes", "sum"),
                Laczna_Waga_MB=("size_mb", "sum"),
            )
            .reset_index()
        )

        hall_of_fame = (
            hall_of_fame[hall_of_fame["Liczba_Modow"] >= 3]
            .sort_values(
                by=["Srednia_Ocena", "Lacznie_Glosow"], ascending=[False, False]
            )
            .head(15)
        )

        hall_of_fame["Waga"] = hall_of_fame["Laczna_Waga_MB"].apply(
            lambda x: f"{x:.1f} MB" if x < 1024 else f"{x/1024:.2f} GB"
        )

        st.dataframe(
            hall_of_fame.drop(columns=["Laczna_Waga_MB"]).rename(
                columns={
                    "author": "Twórca / Grupa",
                    "Liczba_Modow": "Wydanych modów",
                    "Srednia_Ocena": "Średnia ocena ⭐",
                    "Lacznie_Glosow": "Oddanych głosów 🗳️",
                }
            ),
            column_config={
                "Średnia ocena ⭐": st.column_config.NumberColumn(
                    "Średnia ⭐", format="%.2f / 5.0"
                )
            },
            hide_index=True,
            use_container_width=True,
        )

# ==========================================
# ZAKŁADKA 4: STATYSTYKI & WYKRESY
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
# ZAKŁADKA 5: TOP RANKINGI
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
                    [
                        "title",
                        "author",
                        "rating",
                        "votes",
                        "updates_count",
                        "size_raw",
                        "url",
                    ]
                ],
                column_config={
                    "url": st.column_config.LinkColumn("Link"),
                    "rating": st.column_config.NumberColumn(
                        "Ocena", format="%.2f ⭐"
                    ),
                    "updates_count": st.column_config.NumberColumn(
                        "Łatki 🔄", format="%d"
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )
        with col_t2:
            st.subheader("🛠️ TOP 20 Najczęściej Aktualizowanych Modów")
            st.dataframe(
                df.sort_values(
                    by=["updates_count", "rating"], ascending=[False, False]
                ).head(20)[
                    [
                        "title",
                        "author",
                        "updates_count",
                        "rating",
                        "size_raw",
                        "url",
                    ]
                ],
                column_config={
                    "url": st.column_config.LinkColumn("Link"),
                    "updates_count": st.column_config.NumberColumn(
                        "Liczba patchy 🔄", format="%d"
                    ),
                    "rating": st.column_config.NumberColumn(
                        "Ocena", format="%.1f ⭐"
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )

# ==========================================
# ZAKŁADKA 6: HARMONOGRAM GIANTS
# ==========================================
with tab_giants:
    st.subheader(
        "🕒 Harmonogram Wydań GIANTS – Podział na Premiery i Aktualizacje"
    )
    st.caption(
        "Analiza dokładnych dat premier oraz patchy dzięki zarchiwizowanym danym historycznym."
    )

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
                d_grouped = (
                    df_d.groupby(["Dzień", "typ_wydania"])
                    .size()
                    .reset_index(name="Liczba wydań")
                    .sort_values(by="Dzień")
                )

                fig_days = px.bar(
                    d_grouped,
                    x="Dzień",
                    y="Liczba wydań",
                    color="typ_wydania",
                    title="Dni tygodnia: Premiery vs Aktualizacje",
                    color_discrete_map={
                        "🟢 Premiera (v1.0)": "#238636",
                        "🔄 Aktualizacja": "#8957e5",
                    },
                    barmode="stack",
                )
                st.plotly_chart(fig_days, use_container_width=True)

            with g2:
                type_counts = df_d["typ_wydania"].value_counts().reset_index()
                type_counts.columns = ["Typ", "Liczba"]

                fig_pie_type = px.pie(
                    type_counts,
                    names="Typ",
                    values="Liczba",
                    title="Stosunek Nowych Modów do Aktualizacji na ModHubie",
                    hole=0.4,
                    color="Typ",
                    color_discrete_map={
                        "🟢 Premiera (v1.0)": "#238636",
                        "🔄 Aktualizacja": "#8957e5",
                    },
                )
                st.plotly_chart(fig_pie_type, use_container_width=True)

            df_d["Miesiąc"] = df_d["date"].dt.to_period("M").astype(str)
            m_grouped = (
                df_d.groupby(["Miesiąc", "typ_wydania"])
                .size()
                .reset_index(name="Liczba wydań")
                .sort_values(by="Miesiąc")
            )

            fig_timeline = px.bar(
                m_grouped,
                x="Miesiąc",
                y="Liczba wydań",
                color="typ_wydania",
                title="Oś Czasu: Miesięczna liczba premier i patchy",
                color_discrete_map={
                    "🟢 Premiera (v1.0)": "#238636",
                    "🔄 Aktualizacja": "#8957e5",
                },
                barmode="group",
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

            st.markdown("---")

            # KLASYCZNY ODBLOKOWANY KALENDARZ
            st.subheader("📅 Kalendarium Dnia – Wybierz datę z kalendarza")
            st.write(
                "Wybierz dowolny dzień (z 2024, 2025, 2026 roku itp.), aby sprawdzić ile modów wydało GIANTS w te 24 godziny:"
            )

            df_d["dzien_czysty"] = df_d["date"].dt.date
            min_d = df_d["dzien_czysty"].min()
            max_d = df_d["dzien_czysty"].max()

            cal_c1, cal_c2 = st.columns([1.5, 3.5])

            with cal_c1:
                wybrana_data = st.date_input(
                    "📆 Wybierz datę z kalendarza:",
                    value=max_d if pd.notna(max_d) else date(2026, 8, 24),
                    min_value=date(2020, 1, 1),
                    max_value=date(2030, 12, 31),
                    format="DD.MM.YYYY",
                )

            df_day = df_d[df_d["dzien_czysty"] == wybrana_data].copy()

            with cal_c2:
                if not df_day.empty:
                    nowe_d = len(df_day[df_day["updates_count"] == 0])
                    latki_d = len(df_day[df_day["updates_count"] > 0])
                    waga_d = df_day["size_mb"].sum()

                    dc1, dc2, dc3, dc4 = st.columns(4)
                    dc1.metric("📦 Razem modów", len(df_day))
                    dc2.metric("🟢 Nowości (v1.0)", nowe_d)
                    dc3.metric("🔄 Łatki / Update", latki_d)
                    dc4.metric(
                        "💾 Waga wydań",
                        (
                            f"{waga_d:.1f} MB"
                            if waga_d < 1024
                            else f"{waga_d/1024:.2f} GB"
                        ),
                    )
                else:
                    st.info(
                        f"W dniu **{wybrana_data.strftime('%d.%m.%Y')}** GIANTS nie opublikowało żadnych modów."
                    )

            if not df_day.empty:
                st.markdown(
                    f"##### 📋 Mody wydane w dniu: `{wybrana_data.strftime('%d.%m.%Y')}` ({len(df_day)} pozycji)"
                )
                st.dataframe(
                    df_day[
                        [
                            "title",
                            "author",
                            "category",
                            "typ_wydania",
                            "updates_count",
                            "size_raw",
                            "rating",
                            "url",
                        ]
                    ],
                    column_config={
                        "url": st.column_config.LinkColumn("Link"),
                        "updates_count": st.column_config.NumberColumn(
                            "Łatki", format="%d"
                        ),
                    },
                    hide_index=True,
                    use_container_width=True,
                )

            st.markdown("---")
            st.markdown(
                "#### 🏆 Rekordowe dni GIANTS (Najwięcej wydań w 1 dzień):"
            )

            top_days = (
                df_d.groupby(df_d["date"].dt.strftime("%d.%m.%Y"))
                .agg(
                    Razem=("title", "count"),
                    Nowości=("typ_wydania", lambda x: (x == "🟢 Premiera (v1.0)").sum()),
                    Łatki=("typ_wydania", lambda x: (x == "🔄 Aktualizacja").sum()),
                    Łączna_Waga_MB=("size_mb", "sum"),
                )
                .reset_index()
                .rename(columns={"date": "Data"})
                .sort_values(by="Razem", ascending=False)
                .head(10)
            )

            top_days["Waga"] = top_days["Łączna_Waga_MB"].apply(
                lambda x: f"{x:.1f} MB" if x < 1024 else f"{x/1024:.2f} GB"
            )
            st.dataframe(
                top_days.drop(columns=["Łączna_Waga_MB"]),
                hide_index=True,
                use_container_width=True,
            )

# ==========================================
# ZAKŁADKA 7: WYSZUKIWARKA & TABELA
# ==========================================
with tab_szukaj:
    st.subheader("🔍 Klasyczna wyszukiwarka i filtry")
    if not df.empty:
        s_f1, s_f2, s_f3 = st.columns(3)
        with s_f1:
            s_title = st.text_input("Szukaj po nazwie:", key="s_tab_title")
        with s_f2:
            s_cat = st.multiselect(
                "Kategorie:",
                options=sorted(df["category"].unique()),
                key="s_tab_cat",
            )
        with s_f3:
            s_type = st.selectbox(
                "Typ wydania:",
                options=[
                    "Wszystkie",
                    "🟢 Tylko premiery (v1.0)",
                    "🔄 Tylko zaktualizowane",
                ],
            )

        f_res = df.copy()
        if s_title:
            f_res = f_res[
                f_res["title"].str.contains(s_title, case=False, na=False)
            ]
        if s_cat:
            f_res = f_res[f_res["category"].isin(s_cat)]
        if s_type == "🟢 Tylko premiery (v1.0)":
            f_res = f_res[f_res["updates_count"] == 0]
        elif s_type == "🔄 Tylko zaktualizowane":
            f_res = f_res[f_res["updates_count"] > 0]

        st.dataframe(
            f_res[
                [
                    "title",
                    "author",
                    "category",
                    "updates_count",
                    "size_raw",
                    "rating",
                    "votes",
                    "url",
                ]
            ],
            column_config={
                "url": st.column_config.LinkColumn("Link"),
                "updates_count": st.column_config.NumberColumn(
                    "Łatki 🔄", format="%d"
                ),
            },
            hide_index=True,
            use_container_width=True,
        )

# ==========================================
# ZAKŁADKA 8: PANEL ADMINISTRATORA
# ==========================================
with tab_admin:
    st.subheader("⚙️ Panel Zarządzania Bazą ModHub Online")
    st.write(
        "Z tego miejsca możesz zaktualizować bazę o nowości z poziomu przeglądarki."
    )

    haslo_input = st.text_input(
        "Podaj hasło administratora:", type="password", key="admin_pass_input"
    )

    if haslo_input == ADMIN_PASSWORD:
        st.success("🔓 Zalogowano do panelu administratora!")

        st.markdown("#### 🔄 Szybka aktualizacja bazy (Nowości z ModHuba)")
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
                        d = {
                            "url": l,
                            "mod_id": (
                                re.search(r"mod_id=(\d+)", l).group(1)
                                if "mod_id=" in l
                                else ""
                            ),
                            "title": "Nieznany",
                            "author": "Nieznany",
                            "category": "Inne",
                            "size_raw": "0 MB",
                            "size_mb": 0.0,
                            "rating": 0.0,
                            "votes": 0,
                            "updates_count": 0,
                            "version_history": [],
                            "version": "1.0.0.0",
                            "release_date": "",
                            "download_url": "",
                            "filename": "",
                        }
                        try:
                            rq = requests.get(l, headers=HEADERS, timeout=10)
                            if rq.status_code == 200:
                                sp = BeautifulSoup(rq.text, "html.parser")
                                h2 = sp.find("h2")
                                if h2:
                                    d["title"] = h2.get_text(strip=True)
                                for a in sp.find_all("a", href=True):
                                    if (
                                        ".zip" in a["href"].lower()
                                        or "downloadFile.php" in a["href"]
                                    ):
                                        d["download_url"] = urljoin(
                                            BASE_URL, a["href"]
                                        )
                                        break
                                tf = sp.get_text(separator="\n")
                                lines = [
                                    ln.strip()
                                    for ln in tf.split("\n")
                                    if ln.strip()
                                ]
                                for idx, ln in enumerate(lines):
                                    lc = ln.rstrip(":.").lower()
                                    if (
                                        lc in ["autor", "author"]
                                        and idx + 1 < len(lines)
                                    ):
                                        d["author"] = lines[idx + 1]
                                    elif (
                                        lc in ["kategoria", "category"]
                                        and idx + 1 < len(lines)
                                    ):
                                        d["category"] = lines[idx + 1]
                                    elif (
                                        lc in ["rozmiar", "size"]
                                        and idx + 1 < len(lines)
                                    ):
                                        d["size_raw"] = lines[idx + 1]
                                        d["size_mb"] = size_to_mb(lines[idx + 1])
                                mr = re.search(
                                    r"(?:Ocena użytkowników|User Rating)[\s.:]+([\d.,]+)\s*\(([\d\s.,]+)\)",
                                    tf,
                                    re.IGNORECASE,
                                )
                                if mr:
                                    d["rating"] = float(
                                        mr.group(1).replace(",", ".")
                                    )
                                    d["votes"] = int(
                                        re.sub(r"[^\d]", "", mr.group(2))
                                    )
                        except Exception:
                            pass
                        nowo_pobrane.append(d)
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
