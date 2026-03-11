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

st.set_page_config(page_title="ExpoLeads Pro MAX", page_icon="🎯", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
* { font-family: 'Space Grotesk', sans-serif; }
.stApp { background: #0f111a; color: #e8e8f0; }
.main-header { background: #161824; border: 1px solid #2d3042; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; }
.main-header h1 { color: #4ade80; font-size: 2.2rem; margin: 0; }
.stButton > button { background: #4ade80 !important; color: #0f111a !important; border-radius: 6px !important; font-weight: 700 !important; width: 100%; }
.stDataFrame { background: #161824 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🎯 ExpoLeads Pro MAX</h1><p>Scraping de Précision Extrême & Moteur ICP</p></div>', unsafe_allow_html=True)

try:
    from playwright.async_api import async_playwright
    from bs4 import BeautifulSoup
except ImportError:
    pass

ECOMMERCE_SIGNALS = ["add to cart", "ajouter au panier", "buy now", "panier", "checkout", "shop now", "commander", "e-shop", "/cart"]

ANTI_NOISE_WORDS = [
    "accueil", "contact", "mentions", "recherche", "login", 
    "connexion", "menu", "exposants", "home", "en savoir plus", 
    "lire la suite", "voir la fiche", "page", "filtrer", 
    "catégories", "mot de passe", "s'inscrire", "newsletter",
    "tous les", "trouver", "résultats", "précédent", "suivant",
    "sélectionner", "afficher", "rechercher"
]

def contains_exact_keyword(text: str, keywords_list: list) -> bool:
    text_lower = text.lower()
    for kw in keywords_list:
        clean_kw = kw.strip().lower()
        if not clean_kw: continue
        if re.search(r'\b' + re.escape(clean_kw) + r'\b', text_lower):
            return True
    return False

def get_matched_keyword(text: str, keywords_list: list) -> str:
    text_lower = text.lower()
    for kw in keywords_list:
        clean_kw = kw.strip().lower()
        if not clean_kw: continue
        if re.search(r'\b' + re.escape(clean_kw) + r'\b', text_lower):
            return clean_kw.capitalize()
    return "Autre"

def fetch_web_insights(brand_name: str) -> tuple:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"}
    distrib_info, prix_info = "Introuvable", "Introuvable"
    if not brand_name or len(brand_name) < 2: return distrib_info, prix_info
    try:
        data_d = {"q": f'"{brand_name}" revendeur OR distributeur', "kl": "fr-fr"}
        r_d = requests.post("https://lite.duckduckgo.com/lite/", data=data_d, headers=headers, timeout=5)
        soup_d = BeautifulSoup(r_d.text, 'html.parser')
        snippets_d = [tr.text.strip() for tr in soup_d.find_all('td', class_='result-snippet')]
        if snippets_d: distrib_info = " | ".join(snippets_d)[:250]
        
        data_p = {"q": f'"{brand_name}" prix OR tarif', "kl": "fr-fr"}
        r_p = requests.post("https://lite.duckduckgo.com/lite/", data=data_p, headers=headers, timeout=5)
        soup_p = BeautifulSoup(r_p.text, 'html.parser')
        snippets_p = [tr.text.strip() for tr in soup_p.find_all('td', class_='result-snippet')]
        if snippets_p: prix_info = " | ".join(snippets_p)[:250]
    except: pass
    return distrib_info, prix_info

def calculate_score_with_details(text: str, website: str, ecom_status: str, distrib_web_info: str, weights: dict, positive_distrib: list) -> tuple:
    points = 0
    max_possible = sum(weights.values())
    details = []
    
    if max_possible == 0: return 0, "Aucun poids défini"

    if website: 
        points += weights['web']
        details.append(f"✅ Site Web (+{weights['web']})")
    
    if ecom_status == "❌ Absent": 
        points += weights['no_ecom']
        details.append(f"✅ Pas d'e-com (+{weights['no_ecom']})")
    elif ecom_status == "Non vérifié":
        points += (weights['no_ecom'] / 2)
        details.append(f"⚠️ E-com incertain (+{weights['no_ecom']/2})")
    else:
        details.append(f"❌ E-com détecté (0)")
    
    distrib_found = False
    if contains_exact_keyword(text, positive_distrib):
        distrib_found = True
        details.append("✅ Mots distribution (Fiche)")
    if distrib_web_info != "Introuvable" and distrib_web_info != "Non cherché":
        distrib_found = True
        details.append("✅ Distributeurs (Web)")
        
    if distrib_found:
        points += weights['distrib']
        details.append(f"➡️ Bonus Distrib (+{weights['distrib']})")
        if ecom_status == "❌ Absent":
            points += 5
            max_possible += 5
            details.append("🌟 COMBO B2B2C (+5)")
            
    if len(text) > 150: 
        points += weights['qualite']
        details.append(f"✅ Fiche détaillée (+{weights['qualite']})")
    
    score_100 = int((points / max_possible) * 100)
    return min(100, score_100), " | ".join(details)

def qualify_companies(raw_companies: list[dict], config: dict, do_web_search: bool) -> tuple:
    brands, exclus = [], []
    grossistes_kw = ["grossiste", "importateur", "négociant", "centrale d'achat"]
    
    for c in raw_companies:
        raw_text = c.get("_raw_text", "") + " " + c.get("Description", "").lower()
        website = c.get("Site Web", "")
        ecom_status = c.get("E-commerce", "Non vérifié")
        
        sector = get_matched_keyword(raw_text, config['sectors'])
                
        distrib_info, prix_info = "Non cherché", "Non cherché"
        if do_web_search:
            distrib_info, prix_info = fetch_web_insights(c.get("Nom", ""))
            
        score, explications = calculate_score_with_details(raw_text, website, ecom_status, distrib_info, config['weights'], config['positive_distrib'])
        
        row = {
            "🔥 Score": score,
            "🔍 Détail": explications,
            "✅ Nom": c.get("Nom", ""),
            "🏭 Secteur": sector,
            "🌐 Site Web": website,
            "🛒 E-commerce": ecom_status,
            "🔍 Distributeurs (Web)": distrib_info,
            "🏷️ Prix (Web)": prix_info,
            "📝 Description": c.get("Description", "")[:200]
        }
        
        is_exclu = contains_exact_keyword(raw_text, config['exclusions'])
        is_grossiste = contains_exact_keyword(raw_text, grossistes_kw)
        
        if is_exclu or is_grossiste:
            row["Raison exclusion"] = "Mot d'exclusion" if is_exclu else "Grossiste/Importateur"
            exclus.append(row)
        else:
            brands.append(row)
            
    brands_df = pd.DataFrame(brands).sort_values(by="🔥 Score", ascending=False) if brands else pd.DataFrame()
    exclus_df = pd.DataFrame(exclus) if exclus else pd.DataFrame()
    return brands_df, exclus_df

# --- MOTEUR DE SCRAPING ULTRA ROBUSTE ---
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
                has_next = await page.query_selector("a[rel='next'], button:has-text('suivant')")
                mode = "Pagination" if has_next else "Infinite Scroll"
            
            pages_scraped, failed_scrolls = 0, 0
            while len(companies) < max_companies:
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                blocks = soup.find_all(["div", "article", "li"], class_=re.compile(r"exhibitor|exposant|company|booth|stand|brand|participant", re.I))
                
                added_this_round = 0
                existing_names = {c.get("Nom", "").lower() for c in companies}
                
                for block in blocks:
                    text = block.get_text(" ", strip=True)
                    if len(text) < 40: continue
                    
                    name_tag = block.find(["h2", "h3", "h4", "strong"])
                    if not name_tag:
                        a_tags = block.find_all("a")
                        if a_tags: name_tag = a_tags[0]
                    
                    name = name_tag.get_text(strip=True) if name_tag else ""
                    
                    if not name or len(name) < 2 or len(name) > 60: continue
                    if name.lower() in existing_names: continue
                    if any(bad_word in name.lower() for bad_word in ANTI_NOISE_WORDS): continue
                    
                    website = ""
                    for a in block.find_all("a", href=True):
                        if a["href"].startswith("http") and "facebook" not in a["href"] and "linkedin" not in a["href"]:
                            website = a["href"]; break
                    
                    # MÉTHODE BLINDÉE POUR LA DESCRIPTION
                    desc = text.replace(name, "").strip()[:300]
                        
                    if len(desc) < 20: continue 

                    companies.append({"Nom": name, "Site Web": website, "Description": desc, "_raw_text": text.lower(), "Stand": "", "E-commerce": "Non vérifié"})
                    existing_names.add(name.lower())
                    added_this_round += 1
                
                if mode == "Infinite Scroll":
                    prev_h = await page.evaluate("document.body.scrollHeight")
                    await page.evaluate("window.scrollBy(0, 1500)")
                    await page.wait_for_timeout(2000)
                    new_h = await page.evaluate("document.body.scrollHeight")
                    if added_this_round == 0 and new_h == prev_h:
                        failed_scrolls += 1
                        if failed_scrolls >= 4: break
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
    with col2: w_noecom = st.slider("PAS D'E-COMMERCE", 0, 5, 5)
    with col3: w_distrib = st.slider("RÉSEAU DISTRIBUTION", 0, 5, 5)
    with col4: w_qual = st.slider("QUALITÉ DU SITE", 0, 5, 2)
    
    st.markdown("### 🎯 PARAMÈTRES ICP")
    c1, c2 = st.columns(2)
    with c1:
        secteurs_input = st.text_input("SECTEURS ICP CIBLES", "Pharma, Cosmétique, DIY, HAP, Auto, Animaux")
    with c2:
        exclusions_input = st.text_input("CRITÈRES D'EXCLUSION EXACTS", "Pure player, Marketplace, Startup, Agence")
        
    instructions = st.text_area("Mots-clés de distribution (Dans la description) :", "GMS, pharmacies, GSB, animaleries, réseau de distribution, revendeurs agréés")

with tab_main:
    col_url, col_btn = st.columns([3, 1])
    with col_url:
        url = st.text_input("🔗 URL de la liste des exposants", placeholder="https://www.salon-exemple.com/exposants")
    with col_btn:
        st.write("") 
        start_btn = st.button("🚀 LANCER LE SCAN")
        
    with st.expander("⚙️ Options techniques"):
        mode = st.selectbox("Mode", ["Auto", "Infinite Scroll", "Pagination"])
        max_comp = st.number_input("Exposants max", 10, 2500, 500)
        check_ecom = st.checkbox("🛒 Activer la vérification E-commerce (Indispensable pour l'ICP)", value=True)
        check_web = st.checkbox("🔍 Rechercher distributeurs sur le Web", value=True)

    if start_btn and url:
        config = {
            'weights': {'web': w_web, 'no_ecom': w_noecom, 'distrib': w_distrib, 'qualite': w_qual},
            'sectors': [x.strip() for x in secteurs_input.split(',')],
            'exclusions': [x.strip() for x in exclusions_input.split(',')],
            'positive_distrib': [x.strip() for x in instructions.split(',')]
        }
        
        status = st.empty()
        status.info("⏳ Étape 1/3 : Scraping de Précision des fiches...")
        raw_data = run_sync(scrape_with_playwright, url, mode, 20, int(max_comp))
        
        if raw_data:
            if check_ecom:
                status.info("🛒 Étape 2/3 : Analyse des paniers e-commerce...")
                for r in raw_data:
                    if r["Site Web"]: r["E-commerce"] = run_sync(check_ecommerce, r["Site Web"])
            
            status.info("🔍 Étape 3/3 : Qualification et Recherche Web...")
            brands_df, exclus_df = qualify_companies(raw_data, config, check_web)
            
            status.empty()
            
            t1, t2 = st.tabs(["💎 Prospects Qualifiés", "🗑️ Exclus"])
            with t1:
                st.dataframe(brands_df, use_container_width=True)
            with t2:
                st.dataframe(exclus_df, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if not brands_df.empty: brands_df.to_excel(writer, sheet_name="Marques Qualifiées", index=False)
                if not exclus_df.empty: exclus_df.to_excel(writer, sheet_name="Exclus", index=False)
            st.download_button("📥 TÉLÉCHARGER L'EXCEL ENRICHIT", output.getvalue(), "Leads_ICP_Scores.xlsx")
        else:
            st.error("Aucune donnée trouvée. L'algorithme a filtré tout le bruit mais n'a pas trouvé les fiches.")
