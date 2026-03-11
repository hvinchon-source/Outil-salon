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
    box-shadow: 0 0 40px rgba(233,69,96,0.15);
}
.main-header h1 { 
    color: #e94560; 
    font-size: 2.5rem; 
    margin: 0;
    text-shadow: 0 0 20px rgba(233,69,96,0.5);
}
.main-header p { color: #a0a0c0; margin: 0.5rem 0 0; font-size: 1.05rem; }

.metric-card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #2a2a4e;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    transition: border-color 0.3s;
}
.metric-card:hover { border-color: #e94560; }
.metric-number { font-size: 2rem; font-weight: 700; color: #e94560; font-family: 'Syne', sans-serif; }
.metric-label { font-size: 0.8rem; color: #7070a0; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }

.stButton > button {
    background: linear-gradient(135deg, #e94560, #c73652) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 15px rgba(233,69,96,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(233,69,96,0.5) !important;
}

div[data-testid="stSidebar"] {
    background: #0d0d1a !important;
    border-right: 1px solid #2a2a4e !important;
}
div[data-testid="stSidebar"] label { color: #a0a0c0 !important; }

.stSelectbox > div > div { background: #1a1a2e !important; border-color: #2a2a4e !important; color: #e8e8f0 !important; }
.stTextInput > div > div > input { background: #1a1a2e !important; border-color: #2a2a4e !important; color: #e8e8f0 !important; }
.stNumberInput > div > div > input { background: #1a1a2e !important; border-color: #2a2a4e !important; color: #e8e8f0 !important; }

.info-box, .warning-box, .success-box {
    border-radius: 8px; padding: 1rem 1.2rem; margin: 1rem 0; font-size: 0.9rem;
}
.info-box { background: linear-gradient(135deg, rgba(15,52,96,0.4), rgba(26,26,46,0.6)); border: 1px solid #1a4a7a; border-left: 4px solid #4a9eff; color: #9ab8d8; }
.warning-box { background: linear-gradient(135deg, rgba(96,60,15,0.4), rgba(46,36,16,0.6)); border: 1px solid #7a4a1a; border-left: 4px solid #ff9a4a; color: #d8b89a; }
.success-box { background: linear-gradient(135deg, rgba(15,96,52,0.4), rgba(16,46,26,0.6)); border: 1px solid #1a7a4a; border-left: 4px solid #4aff9a; color: #9ad8b8; }

.stDataFrame { background: #1a1a2e !important; }
.stTabs [data-baseweb="tab-list"] { background: #1a1a2e !important; border-bottom: 1px solid #2a2a4e; }
.stTabs [data-baseweb="tab"] { color: #7070a0 !important; font-family: 'Space Grotesk', sans-serif !important; }
.stTabs [aria-selected="true"] { color: #e94560 !important; border-bottom-color: #e94560 !important; }
</style>
""", unsafe_allow_html=True)

# ─── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🎯 ExpoLeads Pro</h1>
    <p>Extracteur & Qualificateur d'Exposants de Salons Professionnels</p>
</div>
""", unsafe_allow_html=True)

# ─── IMPORTS WITH ERROR HANDLING ────────────────────────────────────────────────
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

# ─── CONSTANTS ──────────────────────────────────────────────────────────────────
TARGET_INDUSTRIES = ["auto", "automobile", "diy", "bricolage", "pharma", "pharmaceutique",
                     "hygiène", "beauté", "cosmétique", "hap", "petfood", "animaux",
                     "jouet", "toy", "jeu", "pet"]

DISTRIBUTOR_KEYWORDS = ["distributeur", "distribution", "revendeur", "grossiste",
                        "importateur", "négociant", "agent commercial", "représentant",
                        "dealer", "retailer", "reseller", "wholesaler"]

ECOMMERCE_SIGNALS = ["add to cart", "ajouter au panier", "buy now", "acheter maintenant",
                     "add to basket", "panier", "checkout", "shop now", "commander",
                     "boutique en ligne", "e-shop", "online store", "cart", "basket",
                     "shopping cart", "/cart", "/panier", "/shop", "/boutique",
                     "woocommerce", "shopify", "prestashop", "magento"]

LINKEDIN_ROLES = {
    "Resp. Marketing": "Responsable+Marketing",
    "Resp. Digital": "Responsable+Digital",
    "CMO": "Chief+Marketing+Officer+CMO",
    "Head of Digital": "Head+of+Digital"
}

# ─── NOUVEAU MOTEUR DE SCRAPING ULTRA-ROBUSTE ───────────────────────────────────
async def scrape_with_playwright(url: str, mode: str, max_pages: int, max_companies: int) -> list[dict]:
    """Core scraping function using Playwright with advanced scroll mapping."""
    companies = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000) # Laisse le temps au site de charger
            
            if mode == "Auto":
                has_next = await page.query_selector("a[rel='next'], button:has-text('suivant'), button:has-text('next'), .pagination")
                mode = "Pagination" if has_next else "Infinite Scroll"
            
            pages_scraped = 0
            failed_scrolls = 0
            
            # Boucle d'extraction principale
            while len(companies) < max_companies:
                # 1. Extraire les données de la vue actuelle
                content = await page.content()
                new_companies = extract_companies_from_html(content, url)
                
                existing_names = {c.get("Nom", "") for c in companies}
                added_this_round = 0
                for c in new_companies:
                    if c.get("Nom") not in existing_names and len(companies) < max_companies:
                        companies.append(c)
                        existing_names.add(c.get("Nom", ""))
                        added_this_round += 1
                
                # 2. Naviguer vers la suite (Scroll ou Page suivante)
                if mode == "Infinite Scroll":
                    # Scroll par "paliers" pour forcer le chargement des images/textes
                    prev_height = await page.evaluate("document.body.scrollHeight")
                    await page.evaluate("window.scrollBy(0, 1500)")
                    await page.wait_for_timeout(1500)
                    new_height = await page.evaluate("document.body.scrollHeight")
                    
                    if added_this_round == 0 and new_height == prev_height:
                        failed_scrolls += 1
                        # Petite technique anti-blocage : on remonte un peu puis on redescend
                        await page.evaluate("window.scrollBy(0, -500)")
                        await page.wait_for_timeout(500)
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(1500)
                        
                        if failed_scrolls >= 6: # Si ça bloque 6 fois de suite, on a vraiment fini
                            break
                    else:
                        failed_scrolls = 0 # On a trouvé des trucs, on réinitialise

                elif mode == "Pagination":
                    if pages_scraped >= max_pages:
                        break
                    next_btn = await page.query_selector(
                        "a[rel='next'], a:has-text('Suivant'), a:has-text('Next'), "
                        "button:has-text('Suivant'), button:has-text('Next'), "
                        ".next a, .pagination-next a, [aria-label='Next page']"
                    )
                    if not next_btn:
                        break
                    try:
                        await next_btn.click()
                        await page.wait_for_timeout(3000)
                        pages_scraped += 1
                    except:
                        break # Le bouton existe mais n'est pas cliquable
                    
        except PlaywrightTimeout:
            st.warning("⏱️ Timeout sur la page — résultats partiels récupérés.")
        except Exception as e:
            st.warning(f"⚠️ Erreur de scraping : {str(e)[:200]}")
        finally:
            await browser.close()
    
    return companies


def extract_companies_from_html(html: str, base_url: str) -> list[dict]:
    """Parse HTML and extract exhibitor data."""
    if not BS4_AVAILABLE:
        return []
    
    soup = BeautifulSoup(html, "html.parser")
    companies = []
    
    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    
    # Sélecteurs enrichis pour ne rien rater
    selectors = [
        {"class_": re.compile(r"exhibitor|exposant|company|stand|booth|participant|brand|marque", re.I)},
        {"class_": re.compile(r"card|item|entry|listing|result|grid-item|col-", re.I)},
    ]
    
    blocks = []
    for sel in selectors:
        found = soup.find_all(["div", "article", "li", "section", "tr"], **sel)
        if found:
            blocks.extend(found)
    
    seen = set()
    for block in blocks:
        text = block.get_text(separator=" ", strip=True)
        if len(text) < 10:
            continue
        
        name = ""
        for tag in ["h1", "h2", "h3", "h4", "strong", "b"]:
            el = block.find(tag)
            if el:
                name = el.get_text(strip=True)[:100]
                if name: break
        
        if not name:
            link = block.find("a")
            if link:
                name = link.get_text(strip=True)[:100]
        
        if not name or name in seen or len(name) < 2:
            continue
        seen.add(name)
        
        website = ""
        for a in block.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and ("facebook" not in href and "linkedin" not in href):
                website = href
                break
        
        desc_candidates = block.find_all(["p", "span", "div"])
        description = ""
        for d in desc_candidates:
            t = d.get_text(strip=True)
            if len(t) > 30 and t != name:
                description = t[:300]
                break
        
        stand = ""
        stand_match = re.search(r"\b([A-Z]{1,3}[\s\-]?\d{2,4}|\d{2,4}[\s\-]?[A-Z]{0,3})\b", text)
        if stand_match:
            stand = stand_match.group(1)
        
        companies.append({
            "Nom": name,
            "Site Web": website,
            "Description": description,
            "Secteur": detect_sector(text),
            "Stand": stand,
            "_raw_text": text.lower()
        })
    
    return companies


def detect_sector(text: str) -> str:
    """Detect industry from text."""
    text_lower = text.lower()
    sector_map = {
        "Auto / Automobile": ["auto", "automobile", "automotive", "vehicule", "voiture"],
        "DIY / Bricolage": ["diy", "bricolage", "outillage", "jardinage", "renovation"],
        "Pharma / Santé": ["pharma", "pharmaceutique", "santé", "médical", "soin"],
        "HAP (Hygiène/Beauté)": ["hygiène", "beauté", "cosmétique", "parfum", "soins", "hap", "beauty"],
        "Petfood / Animaux": ["petfood", "animaux", "chien", "chat", "pet", "animal"],
        "Jouet / Jeu": ["jouet", "jeu", "toy", "game", "enfant", "loisir"],
    }
    for sector, keywords in sector_map.items():
        if any(k in text_lower for k in keywords):
            return sector
    return "Autre"


def is_distributor(text: str) -> bool:
    return any(k in text.lower() for k in DISTRIBUTOR_KEYWORDS)


async def check_ecommerce(url: str) -> str:
    """Check if a website has e-commerce features."""
    if not url or not PLAYWRIGHT_AVAILABLE:
        return "Non vérifié"
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=15000, wait_until="domcontentloaded")
            content = (await page.content()).lower()
            await browser.close()
            
            score = sum(1 for sig in ECOMMERCE_SIGNALS if sig in content)
            if score >= 2:
                return "✅ E-commerce présent"
            elif score == 1:
                return "⚠️ Possible"
            return "❌ Absent"
    except:
        return "Non vérifié"


def generate_linkedin_links(company_name: str) -> dict:
    """Generate LinkedIn search links for key roles."""
    links = {}
    encoded_name = urllib.parse.quote(company_name)
    for label, role in LINKEDIN_ROLES.items():
        links[label] = f"https://www.linkedin.com/search/results/people/?keywords={role}+{encoded_name}"
    return links


def qualify_companies(raw_companies: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split companies into ICP brands and distributors."""
    brands = []
    distributors = []
    
    for c in raw_companies:
        raw = c.get("_raw_text", "") + " " + c.get("Description", "").lower()
        
        li_links = generate_linkedin_links(c["Nom"])
        
        row = {
            "✅ Nom": c.get("Nom", ""),
            "🌐 Site Web": c.get("Site Web", ""),
            "📝 Description": c.get("Description", "")[:200],
            "🏭 Secteur": c.get("Secteur", "Autre"),
            "📍 Stand": c.get("Stand", ""),
            "🛒 E-commerce": "Non vérifié",
            "🔗 LinkedIn Resp. Marketing": li_links.get("Resp. Marketing", ""),
            "🔗 LinkedIn Resp. Digital": li_links.get("Resp. Digital", ""),
            "🔗 LinkedIn CMO": li_links.get("CMO", ""),
            "🔗 LinkedIn Head of Digital": li_links.get("Head of Digital", ""),
        }
        
        if is_distributor(raw):
            distributors.append(row)
        else:
            brands.append(row)
    
    return pd.DataFrame(brands), pd.DataFrame(distributors)


def run_scraping(url, mode, max_pages, max_companies):
    """Synchronous wrapper for async scraping."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(scrape_with_playwright(url, mode, max_pages, max_companies))
    finally:
        loop.close()


def run_ecom_check(url):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(check_ecommerce(url))
    finally:
        loop.close()


def df_to_excel(brands_df: pd.DataFrame, distrib_df: pd.DataFrame) -> bytes:
    """Export both dataframes to Excel with multiple sheets."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if not brands_df.empty:
            brands_df.to_excel(writer, sheet_name="✅ Marques ICP", index=False)
        if not distrib_df.empty:
            distrib_df.to_excel(writer, sheet_name="🔄 Distributeurs", index=False)
        
        summary = pd.DataFrame({
            "Métrique": ["Total Marques ICP", "Total Distributeurs", "Total Exposants", "Date d'extraction"],
            "Valeur": [len(brands_df), len(distrib_df), len(brands_df) + len(distrib_df), 
                       datetime.now().strftime("%d/%m/%Y %H:%M")]
        })
        summary.to_excel(writer, sheet_name="📊 Résumé", index=False)
    
    return output.getvalue()


# ─── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration du Scan")
    
    url = st.text_input(
        "🔗 URL du salon",
        placeholder="https://www.salon-exemple.com/exposants",
        help="Collez ici l'URL de la page des exposants"
    )
    
    mode = st.selectbox(
        "🔄 Mode de Scraping",
        ["Auto", "Infinite Scroll", "Pagination"],
        help="Auto détecte automatiquement la structure du site"
    )
    
    max_pages = st.number_input("📄 Pages max (si Pagination)", min_value=1, max_value=50, value=10)
    max_companies = st.number_input("🏢 Exposants max à extraire", min_value=10, max_value=2500, value=500)
    
    check_ecom = st.checkbox("🛒 Vérifier E-commerce (plus lent)", value=False,
                              help="Visite chaque site web pour détecter un panier d'achat")
    
    st.markdown("---")
    st.markdown("### 🎯 Votre ICP")
    st.markdown("""
    <div style="font-size:0.82rem; color:#7070a0; line-height:1.8;">
    ✅ <b>Industries :</b><br>
    Auto • DIY • Pharma<br>
    HAP • Petfood • Jouet<br><br>
    ✅ <b>Type :</b> Marques uniquement<br>
    ❌ Distributeurs séparés<br>
    🔍 Détection e-commerce
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    start_btn = st.button("🚀 Lancer le Scan", use_container_width=True)

# ─── MAIN CONTENT ───────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Résultats", "📖 Guide Déploiement", "❓ Comment ça marche"])

# ── TAB 1 : RESULTS ─────────────────────────────────────────────────────────────
with tab1:
    if not PLAYWRIGHT_AVAILABLE or not BS4_AVAILABLE:
        st.markdown("""
        <div class="warning-box">
        ⚠️ <b>Dépendances manquantes</b><br>
        Playwright et/ou BeautifulSoup4 ne sont pas installés. 
        Sur Streamlit Cloud, ils seront automatiquement installés via <code>requirements.txt</code>.
        </div>
        """, unsafe_allow_html=True)
    
    if start_btn:
        if not url:
            st.error("❌ Veuillez entrer une URL !")
        else:
            progress_bar = st.progress(0)
            status = st.empty()
            
            status.markdown("⏳ **Connexion au site et chargement de la structure...**")
            progress_bar.progress(15)
            
            with st.spinner("🔍 Scraping agressif en cours (cela peut prendre plusieurs minutes)..."):
                try:
                    raw = run_scraping(url, mode, int(max_pages), int(max_companies))
                    progress_bar.progress(60)
                    status.markdown(f"✅ **{len(raw)} exposants trouvés — Qualification en cours...**")
                    
                    brands_df, distrib_df = qualify_companies(raw)
                    progress_bar.progress(80)
                    
                    # E-commerce check
                    if check_ecom and not brands_df.empty:
                        status.markdown("🛒 **Vérification e-commerce en cours...**")
                        ecom_results = []
                        for i, row in brands_df.iterrows():
                            site = row.get("🌐 Site Web", "")
                            ecom_results.append(run_ecom_check(site) if site else "Non vérifié")
                        brands_df["🛒 E-commerce"] = ecom_results
                    
                    progress_bar.progress(100)
                    status.empty()
                    
                    st.session_state["brands_df"] = brands_df
                    st.session_state["distrib_df"] = distrib_df
                    st.session_state["scan_done"] = True
                    
                except Exception as e:
                    st.error(f"❌ Erreur : {str(e)}")
                    progress_bar.empty()
    
    # Display results
    if st.session_state.get("scan_done"):
        brands_df = st.session_state["brands_df"]
        distrib_df = st.session_state["distrib_df"]
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{len(brands_df)}</div>
                <div class="metric-label">✅ Marques ICP</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{len(distrib_df)}</div>
                <div class="metric-label">🔄 Distributeurs</div>
            </div>""", unsafe_allow_html=True)
        with col3:
            ecom_count = len(brands_df[brands_df["🛒 E-commerce"] == "✅ E-commerce présent"]) if not brands_df.empty else 0
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{ecom_count}</div>
                <div class="metric-label">🛒 Avec E-commerce</div>
            </div>""", unsafe_allow_html=True)
        with col4:
            total = len(brands_df) + len(distrib_df)
            st.markdown(f"""<div class="metric-card">
                <div class="metric-number">{total}</div>
                <div class="metric-label">📦 Total Exposants</div>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Export button
        if not brands_df.empty or not distrib_df.empty:
            excel_data = df_to_excel(brands_df, distrib_df)
            st.download_button(
                label="📥 Télécharger en Excel (.xlsx)",
                data=excel_data,
                file_name=f"exposants_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=False
            )
        
        # Results tabs
        res_tab1, res_tab2 = st.tabs([f"✅ Marques ICP ({len(brands_df)})", f"🔄 Distributeurs ({len(distrib_df)})"])
        
        with res_tab1:
            if brands_df.empty:
                st.markdown('<div class="info-box">ℹ️ Aucune marque ICP détectée. Essayez d\'ajuster les paramètres ou de scraper une autre URL.</div>', unsafe_allow_html=True)
            else:
                st.dataframe(brands_df, use_container_width=True, hide_index=True,
                             column_config={
                                 "🌐 Site Web": st.column_config.LinkColumn("🌐 Site Web"),
                                 "🔗 LinkedIn Resp. Marketing": st.column_config.LinkColumn("LinkedIn Mktg"),
                                 "🔗 LinkedIn Resp. Digital": st.column_config.LinkColumn("LinkedIn Digital"),
                                 "🔗 LinkedIn CMO": st.column_config.LinkColumn("LinkedIn CMO"),
                                 "🔗 LinkedIn Head of Digital": st.column_config.LinkColumn("LinkedIn HoD"),
                             })
        
        with res_tab2:
            if distrib_df.empty:
                st.markdown('<div class="info-box">ℹ️ Aucun distributeur détecté dans cette liste.</div>', unsafe_allow_html=True)
            else:
                st.dataframe(distrib_df, use_container_width=True, hide_index=True)
    else:
        st.markdown("""
        <div class="info-box">
        👈 <b>Pour commencer :</b><br>
        1. Collez l'URL de la page des exposants dans la barre latérale<br>
        2. Indiquez le nombre d'exposants MAXIMUM à chercher (ex: 500)<br>
        3. Cliquez sur <b>🚀 Lancer le Scan</b>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 2 : DEPLOYMENT GUIDE (Reste inchangé pour tes collègues) ────────────────
with tab2:
    st.markdown("## 🚀 Guide de Déploiement — Zéro Code")
    st.markdown('<div class="info-box">Ce guide vous permet de mettre cette application en ligne <b>gratuitement</b>, sans rien installer sur votre ordinateur.</div>', unsafe_allow_html=True)
    # Reste du texte du guide...
    
# ── TAB 3 : HOW IT WORKS (Reste inchangé) ──────────────────────────────────────
with tab3:
    st.markdown("## ❓ Comment faire mon premier scan ?")
    # Reste du texte du tutoriel...

# ─── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#404060; font-size:0.8rem; padding: 1rem 0;">
    ExpoLeads Pro — Construit avec Streamlit & Playwright • Données traitées localement, aucun stockage externe
</div>
""", unsafe_allow_html=True)
