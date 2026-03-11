import os
import streamlit as st
import pandas as pd
import asyncio
import re
import urllib.parse
from datetime import datetime
import io
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

# --- INSTALLATION AUTO DES NAVIGATEURS ---
@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")

install_playwright()

# --- CONFIGURATION PRO ---
st.set_page_config(page_title="ExpoLeads Pro v2", page_icon="🎯", layout="wide")

# STYLE CYBER-PRO (Identique à ta demande initiale)
st.markdown("""
<style>
    .stApp { background: #0a0a0f; color: #e8e8f0; }
    .main-header { background: linear-gradient(135deg, #1a1a2e, #0f3460); border: 1px solid #e94560; border-radius: 15px; padding: 20px; margin-bottom: 20px; }
    .metric-card { background: #16213e; border: 1px solid #2a2a4e; border-radius: 10px; padding: 15px; text-align: center; }
    .stButton > button { background: #e94560 !important; color: white !important; width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- LOGIQUE DE FILTRAGE ICP ---
DISTRIBUTOR_KEYWORDS = ["distributeur", "revendeur", "grossiste", "importateur", "trading", "dealer", "wholesaler", "négociant"]
TARGET_INDUSTRIES = ["auto", "automobile", "diy", "bricolage", "pharma", "pharmaceutique", "hygiène", "beauté", "petfood", "jouet"]

def qualify_lead(name, description):
    text = (name + " " + description).lower()
    # 1. Détection Distributeur
    is_distrib = any(k in text for k in DISTRIBUTOR_KEYWORDS)
    # 2. Détection Secteur
    sector = "Autre"
    for s in TARGET_INDUSTRIES:
        if s in text: sector = s.upper()
    return is_distrib, sector

# --- LE SCRAPER PUISSANT ---
async def deep_scrape(url, max_exposants):
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            st.toast("✅ Connexion réussie, début du scan...")
            
            last_count = 0
            retries = 0
            
            # Boucle intelligente de scroll / récupération
            while len(results) < max_exposants and retries < 15:
                # Scroll progressif
                await page.evaluate("window.scrollBy(0, 2000)")
                await asyncio.sleep(2) # Attente chargement
                
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                # On cherche TOUS les liens et blocs de texte qui ressemblent à une fiche
                blocks = soup.find_all(["div", "li", "article", "tr"])
                
                for b in blocks:
                    # On cherche un nom (souvent dans un titre ou un lien gras)
                    name_tag = b.find(["h2", "h3", "h4", "strong", "b"])
                    if name_tag:
                        name = name_tag.get_text(strip=True)
                        if len(name) > 2 and not any(r['Nom'] == name for r in results):
                            desc = b.get_text(" ", strip=True).replace(name, "")[:400]
                            is_distrib, sector = qualify_lead(name, desc)
                            
                            results.append({
                                "Nom": name,
                                "Secteur": sector,
                                "Distributeur": "OUI" if is_distrib else "NON",
                                "Description": desc,
                                "LinkedIn": f"https://www.linkedin.com/search/results/people/?keywords=CMO+{urllib.parse.quote(name)}"
                            })
                
                # Si on n'a rien trouvé de plus après 2 scrolls, on insiste un peu puis on arrête
                if len(results) == last_count:
                    retries += 1
                else:
                    retries = 0
                    last_count = len(results)
                
                status_text.write(f"🔍 Analyse en cours : **{len(results)}** exposants détectés...")

        finally:
            await browser.close()
    return results

# --- INTERFACE ---
st.markdown('<div class="main-header"><h1>🎯 ExpoLeads Pro v2</h1></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuration")
    url = st.text_input("URL du salon")
    target_count = st.number_input("Nombre d'exposants à trouver", value=300)
    start = st.button("🚀 LANCER LE SCAN")

status_text = st.empty()

if start and url:
    raw_data = asyncio.run(deep_scrape(url, target_count))
    
    if raw_data:
        df = pd.DataFrame(raw_data)
        
        # Séparation Marques vs Distributeurs
        marques = df[df['Distributeur'] == "NON"]
        distribs = df[df['Distributeur'] == "OUI"]
        
        # Dashboard
        c1, c2, c3 = st.columns(3)
        c1.metric("Total trouvé", len(df))
        c2.metric("✅ Marques Cibles", len(marques))
        c3.metric("🔄 Distributeurs", len(distribs))
        
        t1, t2 = st.tabs(["💎 Marques ICP", "📦 Distributeurs"])
        
        with t1:
            st.dataframe(marques, use_container_width=True, column_config={"LinkedIn": st.column_config.LinkColumn()})
        with t2:
            st.dataframe(distribs, use_container_width=True)
            
        # Export Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            marques.to_excel(writer, sheet_name="Marques", index=False)
            distribs.to_excel(writer, sheet_name="Distributeurs", index=False)
        
        st.download_button("📥 TÉLÉCHARGER LE FICHIER EXCEL COMPLET", output.getvalue(), "leads_salon.xlsx")
    else:
        st.error("Aucune donnée n'a pu être extraite. Le site est peut-être protégé.")
