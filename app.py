import os
import streamlit as st
import pandas as pd
import asyncio
import re
import urllib.parse
from datetime import datetime
import io

# --- INSTALLATION DE PLAYWRIGHT (INDISPENSABLE SUR STREAMLIT CLOUD) ---
@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")

install_playwright()

# --- CONFIGURATION DE LA PAGE (DOIT ÊTRE AU DÉBUT) ---
st.set_page_config(
    page_title="ExpoLeads Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@700;800&display=swap');
* { font-family: 'Space Grotesk', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif; }
.stApp { background: #0a0a0f; color: #e8e8f0; }
.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border: 1px solid #e94560;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
}
.main-header h1 { color: #e94560; font-size: 2.5rem; margin: 0; }
.metric-card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #2a2a4e;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
}
.metric-number { font-size: 2rem; font-weight: 700; color: #e94560; }
.info-box { background: rgba(15,52,96,0.4); border-left: 4px solid #4a9eff; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
.stButton > button {
    background: linear-gradient(135deg, #e94560, #c73652) !important;
    color: white !important;
    border-radius: 10px !important;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ─── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🎯 ExpoLeads Pro</h1>
    <p>Extracteur & Qualificateur d'Exposants de Salons Professionnels</p>
</div>
""", unsafe_allow_html=True)

# ─── IMPORTS TECHNIQUES ────────────────────────────────────────────────────────
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

# ─── CONSTANTES & FILTRES ICP ──────────────────────────────────────────────────
DISTRIBUTOR_KEYWORDS = ["distributeur", "distribution", "revendeur", "grossiste", "importateur", "négociant"]
ECOMMERCE_SIGNALS = ["panier", "checkout", "ajouter au panier", "cart", "shop", "commander"]
LINKEDIN_ROLES = {
    "Resp. Marketing": "Responsable+Marketing",
    "Resp. Digital": "Responsable+Digital",
    "CMO": "Chief+Marketing+Officer+CMO",
    "Head of Digital": "Head+of+Digital"
}

# ─── FONCTIONS DE SCRAPING ─────────────────────────────────────────────────────
def detect_sector(text: str) -> str:
    text_lower = text.lower()
    sectors = {
        "Auto": ["auto", "automobile", "vehicule"],
        "DIY": ["diy", "bricolage", "outillage"],
        "Pharma": ["pharma", "pharmaceutique", "santé"],
        "HAP": ["hygiène", "beauté", "cosmétique"],
        "Petfood": ["petfood", "animaux", "pet"],
        "Jouet": ["jouet", "toy", "enfant"]
    }
    for sector, keywords in sectors.items():
        if any(k in text_lower for k in keywords): return sector
    return "Autre"

def is_distributor(text: str) -> bool:
    return any(k in text.lower() for k in DISTRIBUTOR_KEYWORDS)

async def scrape_exposants(url, mode, max_pages, max_companies):
    companies = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            for _ in range(max_pages):
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                # Extraction simplifiée (recherche de blocs type "exposant")
                blocks = soup.find_all(["div", "li", "article"], class_=re.compile(r"exhibitor|exposant|item|card", re.I))
                
                for block in blocks:
                    if len(companies) >= max_companies: break
                    text = block.get_text(separator=" ", strip=True)
                    name_el = block.find(["h3", "h4", "strong", "b", "a"])
                    name = name_el.get_text(strip=True) if name_el else "Inconnu"
                    
                    if name != "Inconnu" and not any(c['Nom'] == name for c in companies):
                        companies.append({
                            "Nom": name,
                            "Description": text[:300],
                            "Secteur": detect_sector(text),
                            "_raw": text
                        })

                if mode == "Infinite Scroll":
                    await page.evaluate("window.scrollBy(0, 1000)")
                    await asyncio.sleep(2)
                else:
                    break # Pour simplifier en version 1
        finally:
            await browser.close()
    return companies

# ─── INTERFACE ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Réglages")
    url_input = st.text_input("Lien du salon :", placeholder="https://...")
    mode_input = st.selectbox("Mode :", ["Pagination", "Infinite Scroll"])
    limit = st.number_input("Max exposants :", value=50)
    start_btn = st.button("🚀 Lancer le Scan")

if start_btn and url_input:
    status = st.empty()
    status.info("⏳ Scraping en cours... cela peut prendre 1 à 2 minutes.")
    
    # Exécution du scraping
    results = asyncio.run(scrape_exposants(url_input, mode_input, 5, limit))
    
    if results:
        brands = []
        distribs = []
        
        for r in results:
            # Qualification
            li_base = "https://www.linkedin.com/search/results/people/?keywords="
            encoded_name = urllib.parse.quote(r['Nom'])
            
            row = {
                "Entreprise": r['Nom'],
                "Secteur": r['Secteur'],
                "Description": r['Description'],
                "Lien LinkedIn CMO": f"{li_base}CMO+{encoded_name}"
            }
            
            if is_distributor(r['_raw']):
                distribs.append(row)
            else:
                brands.append(row)
        
        # Affichage
        st.success(f"Scan terminé ! {len(results)} trouvés.")
        
        col1, col2 = st.columns(2)
        col1.metric("Marques ICP", len(brands))
        col2.metric("Distributeurs", len(distribs))
        
        t1, t2 = st.tabs(["✅ Marques", "🔄 Distributeurs"])
        with t1: st.dataframe(pd.DataFrame(brands))
        with t2: st.dataframe(pd.DataFrame(distribs))
        
        # Export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(brands).to_excel(writer, index=False)
        st.download_button("📥 Télécharger Excel", output.getvalue(), "leads.xlsx")
    else:
        st.error("Aucun résultat trouvé. Vérifiez l'URL ou essayez un autre mode.")
