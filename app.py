import os
# --- INSTALLATION AUTO DU NAVIGATEUR POUR STREAMLIT ---
os.system("playwright install chromium")

import streamlit as st
import pandas as pd
import asyncio
import re
import urllib.parse
from datetime import datetime
import io

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="ExpoLeads Pro", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

# ─── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@700;800&display=swap');
* { font-family: 'Space Grotesk', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif; }
.stApp { background: #0a0a0f; color: #e8e8f0; }
.main-header { background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460); border: 1px solid #e94560; border-radius: 16px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 0 40px rgba(233,69,96,0.15); }
.main-header h1 { color: #e94560; font-size: 2.5rem; margin: 0; text-shadow: 0 0 20px rgba(233,69,96,0.5); }
.metric-card { background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #2a2a4e; border-radius: 12px; padding: 1.2rem; text-align: center; }
.metric-number { font-size: 2rem; font-weight: 700; color: #e94560; }
.stButton > button { background: linear-gradient(135deg, #e94560, #c73652) !important; color: white !important; border-radius: 10px !important; font-weight: 600 !important; width: 100%; padding: 0.6rem !important; }
.info-box { background: rgba(15,52,96,0.4); border-left: 4px solid #4a9eff; padding: 1rem; border-radius: 8px; margin: 1rem 0; color: #9ab8d8; }
.stDataFrame { background: #1a1a2e !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🎯 ExpoLeads Pro</h1><p>Extracteur & Qualificateur d\'Exposants avec Scoring ICP</p></div>', unsafe_allow_html=True)

# ─── IMPORTS UTILES ─────────────────────────────────────────────────────────────
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

ECOMMERCE_SIGNALS = ["add to cart", "ajouter au panier", "buy now", "panier", "checkout", "shop now", "commander", "boutique en ligne", "e-shop", "/cart"]
LINKEDIN_ROLES = {"Resp. Marketing": "Responsable+Marketing", "Resp. Digital": "Responsable+Digital", "CMO": "Chief+Marketing+Officer+CMO", "Head of Digital": "Head+of+Digital"}

# ─── LOGIQUE DE SCORING ET QUALIFICATION ────────────────────────────────────────
def detect_sector_and_score(text: str, icp_keywords: list) -> tuple:
    text_lower = text.lower()
    score = 0
    sector = "Autre"
    
    # 1. Check if it matches ICP keywords
    for kw in icp_keywords:
        if kw.strip() and kw.strip().lower() in text_lower:
            sector = kw.strip().capitalize()
            score += 5  # Fort match ICP
            break
            
    # 2. Points pour la richesse de la description
    if len(text) > 100: score += 2
    if len(text) > 300: score += 1
    
    return sector, score

def is_distributor(text: str, distrib_keywords: list) -> bool:
    text_lower = text.lower()
    return any(k.strip().lower() in text_lower for k in distrib_keywords if k.strip())

def qualify_companies(raw_companies: list[dict], icp_keywords: list, distrib_keywords: list) -> tuple:
    brands = []
    distributors = []
    
    for c in raw_companies:
        raw_text = c.get("_raw_text", "") + " " + c.get("Description", "").lower()
        
        # Generer liens Linkedin
        encoded_name = urllib.parse.quote(c.get("Nom", ""))
        li_links = {label: f"https://www.linkedin.com/search/results/people/?keywords={role}+{encoded_name}" for label, role in LINKEDIN_ROLES.items()}
        
        # Scoring initial
        sector, score = detect_sector_and_score(raw_text, icp_keywords)
        if c.get("Site Web", ""): score += 2  # A un site internet = +2 pts
        
        row = {
            "⭐ Score ICP": f"{score}/10",
            "✅ Nom": c.get("Nom", ""),
            "🏭 Secteur": sector,
            "🌐 Site Web": c.get("Site Web", ""),
            "📝 Description": c.get("Description", "")[:250] + "...",
            "📍 Stand": c.get("Stand", ""),
            "🛒 E-commerce": "Non vérifié",
            "🔗 LinkedIn CMO": li_links.get("CMO", ""),
            "🔗 LinkedIn Head of Digital": li_links.get("Head of Digital", ""),
            "_score_num": score # hidden column for sorting
        }
        
        if is_distributor(raw_text, distrib_keywords):
            distributors.append(row)
        else:
            brands.append(row)
            
    # Sort brands by score descending
    brands_df = pd.DataFrame(brands)
    if not brands_df.empty:
        brands_df = brands_df.sort_values(by="_score_num", ascending=False).drop(columns=["_score_num"])
        
    distrib_df = pd.DataFrame(distributors)
    if not distrib_df.empty:
        distrib_df = distrib_df.drop(columns=["_score_num"])
        
    return brands_df, distrib_df

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
                        
                        companies.append({"Nom": name, "Site Web": website, "Description": desc, "_raw_text": text.lower(), "Stand": ""})
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
                    btn = await page.query_selector("a[rel='next'], button:has-text('Suivant'), button:has-text('Next'), .next a")
                    if not btn: break
                    try: await btn.click(); await page.wait_for_timeout(3000); pages_scraped += 1
                    except: break
        except Exception as e: st.warning(f"⚠️ Erreur de scraping : {str(e)[:100]}")
        finally: await browser.close()
    return companies

async def check_ecommerce(url):
    if not url: return "Non vérifié"
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=15000)
            content = (await page.content()).lower()
            await browser.close()
            score = sum(1 for sig in ECOMMERCE_SIGNALS if sig in content)
            if score >= 2: return "✅ E-commerce présent"
            elif score == 1: return "⚠️ Possible"
            return "❌ Absent (Idéal)"
    except: return "Non vérifié"

def run_sync(func, *args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(func(*args))

# ─── SIDEBAR & REGLAGES ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")
    url = st.text_input("🔗 URL du salon", placeholder="https://...")
    
    st.markdown("### 🎯 Critères ICP (Modifiables)")
    icp_input = st.text_area("Industries cibles (séparées par des virgules)", "auto, diy, pharma, hygiène, beauté, petfood, jouet")
    distrib_input = st.text_area("Mots-clés Distributeurs à exclure", "distributeur, revendeur, grossiste, importateur, négociant, trading")
    
    st.markdown("### 🤖 Technique")
    mode = st.selectbox("Mode", ["Auto", "Infinite Scroll", "Pagination"])
    max_companies = st.number_input("Exposants max", min_value=10, max_value=2500, value=500)
    check_ecom = st.checkbox("🛒 Vérifier E-commerce (plus lent)")
    
    start_btn = st.button("🚀 LANCER LE SCAN")

# ─── MAIN APP ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Résultats du Scan", "✉️ Email de Prospection", "❓ Guide"])

with tab1:
    if start_btn and url:
        icp_list = [x.strip() for x in icp_input.split(',')]
        distrib_list = [x.strip() for x in distrib_input.split(',')]
        
        status = st.empty()
        status.info("⏳ Navigation sur le site et extraction en cours...")
        
        raw_data = run_sync(scrape_with_playwright, url, mode, 20, int(max_companies))
        
        if raw_data:
            status.info(f"✅ {len(raw_data)} exposants extraits. Application de vos filtres ICP...")
            brands_df, distrib_df = qualify_companies(raw_data, icp_list, distrib_list)
            
            if check_ecom and not brands_df.empty:
                status.info("🛒 Vérification des paniers e-commerce sur les sites web...")
                ecom_res = []
                # On met à jour le score si e-commerce absent
                scores = list(brands_df["⭐ Score ICP"])
                
                for i, row in brands_df.iterrows():
                    site = row.get("🌐 Site Web", "")
                    res = run_sync(check_ecommerce, site)
                    ecom_res.append(res)
                    # Bonus score si e-commerce absent (car c'est ton ICP)
                    if "Absent" in res:
                        current_score = int(scores[i].split('/')[0])
                        scores[i] = f"{min(10, current_score + 3)}/10"
                        
                brands_df["🛒 E-commerce"] = ecom_res
                brands_df["⭐ Score ICP"] = scores
                # On retrie après le bonus e-commerce
                brands_df['_score_num'] = brands_df['⭐ Score ICP'].apply(lambda x: int(x.split('/')[0]))
                brands_df = brands_df.sort_values(by="_score_num", ascending=False).drop(columns=['_score_num'])

            status.empty()
            st.success("🎉 Scan et Qualification terminés !")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("✅ Marques Qualifiées", len(brands_df))
            c2.metric("🔄 Distributeurs Écartés", len(distrib_df))
            top_icp = len(brands_df[brands_df["⭐ Score ICP"].str.startswith(("8", "9", "10"))]) if not brands_df.empty else 0
            c3.metric("🔥 Prospects 'Chauds' (Score > 8)", top_icp)
            
            st.dataframe(brands_df, use_container_width=True, column_config={
                "🌐 Site Web": st.column_config.LinkColumn(),
                "🔗 LinkedIn CMO": st.column_config.LinkColumn(),
                "🔗 LinkedIn Head of Digital": st.column_config.LinkColumn()
            })
            
            # Export Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                brands_df.to_excel(writer, sheet_name="✅ Marques ICP", index=False)
                distrib_df.to_excel(writer, sheet_name="🔄 Distributeurs", index=False)
            st.download_button("📥 TÉLÉCHARGER LE FICHIER EXCEL", output.getvalue(), f"Leads_{datetime.now().strftime('%Y%m%d')}.xlsx")

        else:
            st.error("❌ Aucun exposant trouvé. Essayez de changer le Mode (Pagination / Scroll).")

with tab2:
    st.markdown("### ✍️ Générateur d'Email de Prospection (Cold Email)")
    st.markdown("Ce modèle est optimisé pour ton ICP (Marques vendant via distributeurs, ciblant le CMO/Head of Digital).")
    
    salon_name = st.text_input("Nom du salon (ex: Maison&Objet)", "ce salon")
    user_company = st.text_input("Le nom de ton entreprise", "Ma Société")
    user_value = st.text_input("Ta proposition de valeur courte (ex: digitaliser votre réseau de distribution)", "booster vos ventes via vos réseaux de distributeurs sans e-commerce direct")
    
    email_template = f"""**Objet :** Votre présence à {salon_name} / Stratégie Digitale

Bonjour [Prénom du CMO / Head of Digital],

J'ai vu que [Nom de l'entreprise] exposait à {salon_name} cette année. Bravo pour le stand !

En analysant votre modèle, j'ai remarqué que vous distribuez vos produits via un réseau de revendeurs plutôt qu'en vente directe sur votre site. C'est exactement le modèle que nous accompagnons chez {user_company}. 

Nous aidons les marques de votre secteur à {user_value}, ce qui permet généralement de débloquer de nouveaux relais de croissance sans concurrencer vos propres distributeurs.

Avez-vous 10 minutes la semaine prochaine pour que je vous montre comment nous avons fait cela pour d'autres marques industrielles ?

Bien à vous,

**[Ton Nom]**
*[{user_company}]*
"""
    st.info("💡 **Astuce :** Copie ce texte. Dans ton Excel généré, clique sur les liens LinkedIn pour trouver le prénom du décideur, et envoie-lui ce message en DM ou par email.")
    st.text_area("Modèle généré (Copier-Coller) :", value=email_template, height=350)

with tab3:
    st.markdown("### 💡 Comment utiliser le Scoring ?")
    st.write("- **5 points** si la description contient un de tes mots-clés de l'ICP (Auto, DIY, etc.)")
    st.write("- **3 points** si l'entreprise n'a PAS de e-commerce (Uniquement si tu coches la case de vérification !)")
    st.write("- **2 points** si elle a un site web et une description claire.")
    st.write("Le tableau Excel est automatiquement trié pour te mettre les scores 10/10 en premier. Tu n'as plus qu'à attaquer la liste de haut en bas !")
