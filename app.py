import os
os.system("playwright install chromium")

import streamlit as st
import pandas as pd
import asyncio
import re
import urllib.parse
from datetime import datetime
import io
import requests

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="ExpoLeads Pro MAX", page_icon="🎯", layout="wide")

# ─── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@700;800&display=swap');
* { font-family: 'Space Grotesk', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif; }
.stApp { background: #0f111a; color: #e8e8f0; }
.main-header { background: #161824; border: 1px solid #2d3042; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; }
.main-header h1 { color: #4ade80; font-size: 2.2rem; margin: 0; }
.score-card { background: #1e2130; border: 1px solid #2d3042; border-radius: 8px; padding: 1.5rem; }
.stSlider > div > div > div > div { background-color: #4ade80 !important; }
.stButton > button { background: #4ade80 !important; color: #0f111a !important; border-radius: 6px !important; font-weight: 700 !important; width: 100%; }
.metric-number { font-size: 2rem; font-weight: 700; color: #4ade80; }
.stDataFrame { background: #161824 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🎯 ExpoLeads Pro MAX</h1><p>Scraping, Scoring ICP & Enrichissement Web</p></div>', unsafe_allow_html=True)

# ─── IMPORTS UTILES ─────────────────────────────────────────────────────────────
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

ECOMMERCE_SIGNALS = ["add to cart", "ajouter au panier", "buy now", "panier", "checkout", "shop now", "commander", "e-shop", "/cart"]

# ─── MOTEUR DE RECHERCHE WEB FURTIF (DUCKDUCKGO) ──────────────────────────────
def fetch_web_insights(brand_name: str) -> tuple:
    """Cherche sur le web les distributeurs et les mentions de prix."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    distrib_info = "Introuvable"
    prix_info = "Introuvable"
    
    if not brand_name or len(brand_name) < 2:
        return distrib_info, prix_info
        
    try:
        # Recherche Distributeurs
        data_d = {"q": f'"{brand_name}" revendeur OR distributeur OR "en vente chez"', "kl": "fr-fr"}
        r_d = requests.post("https://lite.duckduckgo.com/lite/", data=data_d, headers=headers, timeout=5)
        soup_d = BeautifulSoup(r_d.text, 'html.parser')
        snippets_d = [tr.text.strip() for tr in soup_d.find_all('td', class_='result-snippet')]
        if snippets_d:
            distrib_info = " | ".join(snippets_d)[:250] + "..."
            
        # Recherche Prix
        data_p = {"q": f'"{brand_name}" prix OR tarif OR "€"', "kl": "fr-fr"}
        r_p = requests.post("https://lite.duckduckgo.com/lite/", data=data_p, headers=headers, timeout=5)
        soup_p = BeautifulSoup(r_p.text, 'html.parser')
        snippets_p = [tr.text.strip() for tr in soup_p.find_all('td', class_='result-snippet')]
        if snippets_p:
            prix_info = " | ".join(snippets_p)[:250] + "..."
    except Exception:
        pass # Ignore silencieusement les erreurs de connexion
        
    return distrib_info, prix_info

# ─── LOGIQUE DE SCORING AVANCÉE ─────────────────────────────────────────────────
def calculate_score(text: str, website: str, ecom_status: str, distrib_web_info: str, weights: dict, positive_distrib: list) -> int:
    text_lower = text.lower()
    distrib_web_lower = distrib_web_info.lower()
    points = 0
    max_possible = sum(weights.values())
    
    if max_possible == 0: return 0

    # 1. Présence Web
    if website: points += weights['web']
    
    # 2. Pas d'e-commerce (Le critère d'or !)
    if ecom_status == "❌ Absent": points += weights['no_ecom']
    
    # 3. Réseau de distribution (Le combo parfait : Pas d'ecom + Distributeurs trouvés)
    # On regarde si des distributeurs sont mentionnés sur leur fiche OU trouvés sur Google
    distrib_found = False
    if any(k.strip().lower() in text_lower for k in positive_distrib if k.strip()):
        distrib_found = True
    if distrib_web_info != "Introuvable" and distrib_web_info != "Non cherché":
        distrib_found = True
        
    if distrib_found:
        points += weights['distrib']
        # Bonus magique de l'ICP : Si Pas d'ecom + Vendu ailleurs = Jackpot
        if ecom_status == "❌ Absent":
            points += 5
            max_possible += 5
            
    # 4. Qualité du site/description
    if len(text) > 200: points += weights['qualite']
    
    score_100 = int((points / max_possible) * 100)
    return min(100, score_100) # Plafonne à 100

def qualifies_for_exclusion(text: str, exclusions: list) -> bool:
    return any(k.strip().lower() in text.lower() for k in exclusions if k.strip())

def qualify_companies(raw_companies: list[dict], config: dict, do_web_search: bool) -> tuple:
    brands, exclus = [], []
    grossistes_kw = ["grossiste", "importateur", "trading", "négociant", "centrale d'achat"]
    
    for c in raw_companies:
        raw_text = c.get("_raw_text", "") + " " + c.get("Description", "").lower()
        website = c.get("Site Web", "")
        ecom_status = c.get("E-commerce", "Non vérifié")
        
        # Détection secteur
        sector = "Autre"
        for kw in config['sectors']:
            if kw.strip() and kw.strip().lower() in raw_text:
                sector = kw.strip().capitalize()
                break
                
        # Enrichissement Web (Seulement si demandé)
        distrib_info, prix_info = "Non cherché", "Non cherché"
        if do_web_search:
            distrib_info, prix_info = fetch_web_insights(c.get("Nom", ""))
            
        score = calculate_score(raw_text, website, ecom_status, distrib_info, config['weights'], config['positive_distrib'])
        
        row = {
            "🔥 Score": score,
            "✅ Nom": c.get("Nom", ""),
            "🏭 Secteur": sector,
            "🌐 Site Web": website,
            "🛒 E-commerce": ecom_status,
            "🔍 Distributeurs (Recherche Web)": distrib_info,
            "🏷️ Infos Prix (Recherche Web)": prix_info,
            "📝 Description (Salon)": c.get("Description", "")[:200] + "...",
            "📍 Stand": c.get("Stand", ""),
            "💰 CA Min (Cible)": config['ca_min']
        }
        
        if qualifies_for_exclusion(raw_text, config['exclusions']) or qualifies_for_exclusion(raw_text, grossistes_kw):
            exclus.append(row)
        else:
            brands.append(row)
            
    brands_df = pd.DataFrame(brands).sort_values(by="🔥 Score", ascending=False) if brands else pd.DataFrame()
    exclus_df = pd.DataFrame(exclus) if exclus else pd.DataFrame()
    return brands_df, exclus_df

# ─── MOTEUR DE SCRAPING ─────────────────────────────────────────────────────────
async def scrape_with_playwright(url, mode, max_pages, max_companies):
    companies = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()
        try:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            if mode == "Auto":
                has_next = await page.query_selector("a[rel='next'], button:has-text('suivant'), button:has-text('next'), .pagination")
                mode = "Pagination" if has_next else "Infinite Scroll"
            
            pages_scraped, failed_scrolls = 0, 0
            while len(companies) < max_companies:
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                blocks = soup.find_all(["div", "article", "li", "tr"], class_=re.compile(r"exhibitor|exposant|company|card|item|grid", re.I))
                
                added_this_round = 0
                existing_names = {c.get("Nom", "") for c in companies}
                
                for block in blocks:
                    text = block.get_text(" ", strip=True)
                    if len(text) < 10: continue
                    name_tag = block.find(["h2", "h3", "h4", "strong", "b", "a"])
                    name = name_tag.get_text(strip=True)[:100] if name_tag else ""
                    
                    if name and name not in existing_names and len(companies) < max_companies:
                        website = ""
                        for a in block.find_all("a", href=True):
                            if a["href"].startswith("http") and "facebook" not in a["href"] and "linkedin" not in a["href"]:
                                website = a["href"]; break
                        
                        desc_tags = block.find_all(["p", "span"])
                        desc = desc_tags[0].get_text(strip=True)[:300] if desc_tags else text.replace(name, "")[:300]
                        companies.append({"Nom": name, "Site Web": website, "Description": desc, "_raw_text": text.lower(), "Stand": "", "E-commerce": "Non vérifié"})
                        existing_names.add(name)
                        added_this_round += 1
                
                if mode == "Infinite Scroll":
                    prev_h = await page.evaluate("document.body.scrollHeight")
                    await page.evaluate("window.scrollBy(0, 1500)")
                    await page.wait_for_timeout(2000)
                    new_h = await page.evaluate("document.body.scrollHeight")
                    if added_this_round == 0 and new_h == prev_h:
                        failed_scrolls += 1
                        if failed_scrolls >= 5: break
                    else: failed_scrolls = 0
                elif mode == "Pagination":
                    if pages_scraped >= max_pages: break
                    btn = await page.query_selector("a[rel='next'], button:has-text('Suivant')")
                    if not btn: break
                    try: await btn.click(); await page.wait_for_timeout(3000); pages_scraped += 1
                    except: break
        except Exception as e: st.warning(f"⚠️ Erreur: {str(e)[:100]}")
        finally: await browser.close()
    return companies

async def check_ecommerce(url):
    if not url: return "Non vérifié"
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=12000)
            content = (await page.content()).lower()
            await browser.close()
            score = sum(1 for sig in ECOMMERCE_SIGNALS if sig in content)
            if score >= 2: return "✅ Présent"
            elif score == 1: return "⚠️ Possible"
            return "❌ Absent"
    except: return "Non vérifié"

def run_sync(func, *args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(func(*args))

# ─── INTERFACE UTILISATEUR (UI) ─────────────────────────────────────────────────
tab_main, tab_settings = st.tabs(["🚀 Lancer le Scan", "⚖️ Pondérations & ICP"])

with tab_settings:
    st.markdown("### ⚖️ PONDÉRATIONS DU SCORING")
    col1, col2, col3, col4 = st.columns(4)
    with col1: w_web = st.slider("PRÉSENCE WEB", 0, 5, 3)
    with col2: w_noecom = st.slider("PAS D'E-COMMERCE", 0, 5, 5, help="Le critère le plus fort pour votre ICP.")
    with col3: w_distrib = st.slider("RÉSEAU DISTRIBUTION", 0, 5, 5, help="Distributeurs trouvés sur le web ou dans la description.")
    with col4: w_qual = st.slider("QUALITÉ DU SITE", 0, 5, 2)
    
    st.markdown("### 🎯 PARAMÈTRES ICP")
    c1, c2 = st.columns(2)
    with c1:
        ca_min = st.text_input("CA MINIMUM (€)", "20 000 000")
    with c2:
        secteurs_input = st.text_input("SECTEURS ICP CIBLES", "Pharma, Cosmétique, DIY, HAP, Auto, Animaux")
        exclusions_input = st.text_input("CRITÈRES D'EXCLUSION", "Pure player e-commerce, Marketplace, Startup, Agence")
        
    instructions = st.text_area("Mots-clés qui prouvent un bon réseau de distribution (dans la fiche) :", "GMS, pharmacies, GSB, animaleries, réseau de distribution, revendeurs agréés")

with tab_main:
    col_url, col_btn = st.columns([3, 1])
    with col_url:
        url = st.text_input("🔗 URL de la liste des exposants", placeholder="https://www.salon-exemple.com/exposants")
    with col_btn:
        st.write("") 
        start_btn = st.button("🚀 LANCER LE SCAN")
        
    st.markdown("---")
    
    with st.expander("⚙️ Options techniques d'enrichissement"):
        mode = st.selectbox("Mode", ["Auto", "Infinite Scroll", "Pagination"])
        max_comp = st.number_input("Exposants max", 10, 2500, 500)
        check_ecom = st.checkbox("🛒 Activer la vérification E-commerce (Indispensable pour l'ICP)", value=True)
        check_web = st.checkbox("🔍 Rechercher les distributeurs et prix sur Google/Web (Ajoute du temps de scan)", value=True)

    if start_btn and url:
        config = {
            'weights': {'web': w_web, 'no_ecom': w_noecom, 'distrib': w_distrib, 'qualite': w_qual},
            'ca_min': ca_min,
            'sectors': [x.strip() for x in secteurs_input.split(',')],
            'exclusions': [x.strip() for x in exclusions_input.split(',')],
            'positive_distrib': [x.strip() for x in instructions.split(',')]
        }
        
        status = st.empty()
        status.info("⏳ Étape 1/3 : Scraping des fiches du salon en cours...")
        raw_data = run_sync(scrape_with_playwright, url, mode, 20, int(max_comp))
        
        if raw_data:
            if check_ecom:
                status.info("🛒 Étape 2/3 : Analyse des sites web pour vérifier l'absence d'e-commerce...")
                for r in raw_data:
                    if r["Site Web"]: r["E-commerce"] = run_sync(check_ecommerce, r["Site Web"])
            
            if check_web:
                status.info("🔍 Étape 3/3 : Recherche Web des distributeurs et des prix... (Cela peut prendre quelques minutes)")
                # La recherche se fait dans la fonction qualify_companies
            else:
                status.info("⚙️ Étape 3/3 : Calcul des scores ICP en cours...")
                
            brands_df, exclus_df = qualify_companies(raw_data, config, check_web)
            
            status.empty()
            st.success("🎉 Analyse terminée ! Les marques sans E-commerce et avec des distributeurs ont obtenu les meilleurs scores.")
            
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='score-card'><div>MARQUES ICP</div><div class='metric-number'>{len(brands_df)}</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='score-card'><div>EXCLUS / DISTRIBUTEURS</div><div class='metric-number' style='color:#ef4444;'>{len(exclus_df)}</div></div>", unsafe_allow_html=True)
            top_tier = len(brands_df[brands_df["🔥 Score"] >= 85]) if not brands_df.empty else 0
            c3.markdown(f"<div class='score-card'><div>SCORE > 85% (Coeur de cible)</div><div class='metric-number' style='color:#eab308;'>{top_tier}</div></div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            t1, t2 = st.tabs(["💎 Prospects Qualifiés", "🗑️ Exclus"])
            with t1:
                st.dataframe(brands_df, use_container_width=True)
            with t2:
                st.dataframe(exclus_df, use_container_width=True)
            
            # Export
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if not brands_df.empty: brands_df.to_excel(writer, sheet_name="Marques Qualifiées", index=False)
                if not exclus_df.empty: exclus_df.to_excel(writer, sheet_name="Exclus", index=False)
            st.download_button("📥 TÉLÉCHARGER L'EXCEL ENRICHIT", output.getvalue(), "Leads_ICP_Enrichis.xlsx")
        else:
            st.error("Aucune donnée trouvée. Le site bloque peut-être le robot.")
