import os
# Cette ligne installe le navigateur manquant sur le serveur Streamlit
os.system("playwright install chromium")import os
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

.info-box {
    background: linear-gradient(135deg, rgba(15,52,96,0.4), rgba(26,26,46,0.6));
    border: 1px solid #1a4a7a;
    border-left: 4px solid #4a9eff;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.9rem;
    color: #9ab8d8;
}
.warning-box {
    background: linear-gradient(135deg, rgba(96,60,15,0.4), rgba(46,36,16,0.6));
    border: 1px solid #7a4a1a;
    border-left: 4px solid #ff9a4a;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.9rem;
    color: #d8b89a;
}
.success-box {
    background: linear-gradient(135deg, rgba(15,96,52,0.4), rgba(16,46,26,0.6));
    border: 1px solid #1a7a4a;
    border-left: 4px solid #4aff9a;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.9rem;
    color: #9ad8b8;
}

.tag-icp { background: #1a3a1a; color: #4aff4a; border: 1px solid #2a5a2a; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.tag-distributor { background: #3a1a1a; color: #ff4a4a; border: 1px solid #5a2a2a; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.tag-ecom { background: #1a2a3a; color: #4a9aff; border: 1px solid #2a4a6a; padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }

.guide-step {
    background: #1a1a2e;
    border: 1px solid #2a2a4e;
    border-radius: 10px;
    padding: 1.2rem;
    margin: 0.8rem 0;
    position: relative;
    padding-left: 3.5rem;
}
.guide-step-number {
    position: absolute;
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
    background: #e94560;
    color: white;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85rem;
}

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

# ─── SCRAPING FUNCTIONS ──────────────────────────────────────────────────────────
async def scrape_with_playwright(url: str, mode: str, max_pages: int, max_companies: int) -> list[dict]:
    """Core scraping function using Playwright."""
    companies = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            if mode == "Auto":
                # Detect mode
                has_next = await page.query_selector("a[rel='next'], button:has-text('suivant'), button:has-text('next'), .pagination")
                mode = "Pagination" if has_next else "Infinite Scroll"
            
            pages_scraped = 0
            
            while pages_scraped < max_pages and len(companies) < max_companies:
                content = await page.content()
                new_companies = extract_companies_from_html(content, url)
                
                # Avoid duplicates
                existing_names = {c.get("Nom", "") for c in companies}
                for c in new_companies:
                    if c.get("Nom") not in existing_names and len(companies) < max_companies:
                        companies.append(c)
                        existing_names.add(c.get("Nom", ""))
                
                pages_scraped += 1
                
                if mode == "Infinite Scroll":
                    prev_height = await page.evaluate("document.body.scrollHeight")
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2500)
                    new_height = await page.evaluate("document.body.scrollHeight")
                    if new_height == prev_height:
                        break
                        
                elif mode == "Pagination":
                    next_btn = await page.query_selector(
                        "a[rel='next'], a:has-text('Suivant'), a:has-text('Next'), "
                        "button:has-text('Suivant'), button:has-text('Next'), "
                        ".next a, .pagination-next a, [aria-label='Next page']"
                    )
                    if not next_btn:
                        break
                    await next_btn.click()
                    await page.wait_for_timeout(2500)
                    
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
    
    # Remove noise
    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    
    # Find exhibitor cards/blocks
    selectors = [
        {"class_": re.compile(r"exhibitor|exposant|company|stand|booth|participant|brand|marque", re.I)},
        {"class_": re.compile(r"card|item|entry|listing|result", re.I)},
    ]
    
    blocks = []
    for sel in selectors:
        found = soup.find_all(["div", "article", "li", "section"], **sel)
        if found:
            blocks.extend(found)
            break
    
    # Fallback: look for repeated link patterns
    if not blocks:
        links = soup.find_all("a", href=True)
        link_texts = [l.get_text(strip=True) for l in links if len(l.get_text(strip=True)) > 3]
        if link_texts:
            # Try to find containers
            containers = soup.find_all(["div", "article", "li"], limit=200)
            blocks = [c for c in containers if c.find("a") and len(c.get_text(strip=True)) > 20][:100]
    
    seen = set()
    for block in blocks[:500]:
        text = block.get_text(separator=" ", strip=True)
        if len(text) < 10:
            continue
        
        # Extract name
        name = ""
        for tag in ["h1", "h2", "h3", "h4", "strong", "b"]:
            el = block.find(tag)
            if el:
                name = el.get_text(strip=True)[:100]
                if name:
                    break
        
        if not name:
            link = block.find("a")
            if link:
                name = link.get_text(strip=True)[:100]
        
        if not name or name in seen or len(name) < 2:
            continue
        seen.add(name)
        
        # Extract website
        website = ""
        for a in block.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and base_url.split("/")[2] not in href:
                website = href
                break
        
        # Extract description
        desc_candidates = block.find_all(["p", "span", "div"])
        description = ""
        for d in desc_candidates:
            t = d.get_text(strip=True)
            if len(t) > 30 and t != name:
                description = t[:300]
                break
        
        # Extract stand number
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
        
        # Summary sheet
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
    
    max_pages = st.number_input("📄 Pages max à explorer", min_value=1, max_value=50, value=10)
    max_companies = st.number_input("🏢 Exposants max à extraire", min_value=10, max_value=1000, value=200)
    
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
            # Progress
            progress_bar = st.progress(0)
            status = st.empty()
            
            status.markdown("⏳ **Connexion au site...**")
            progress_bar.progress(15)
            
            with st.spinner("🔍 Scraping en cours..."):
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
        2. Choisissez le mode de scraping (Auto recommandé)<br>
        3. Cliquez sur <b>🚀 Lancer le Scan</b>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 2 : DEPLOYMENT GUIDE ────────────────────────────────────────────────────
with tab2:
    st.markdown("## 🚀 Guide de Déploiement — Zéro Code")
    st.markdown('<div class="info-box">Ce guide vous permet de mettre cette application en ligne <b>gratuitement</b>, sans rien installer sur votre ordinateur.</div>', unsafe_allow_html=True)
    
    st.markdown("### Étape 1 — Créer un compte GitHub (5 min)")
    st.markdown("""
    <div class="guide-step">
        <div class="guide-step-number">1</div>
        Allez sur <a href="https://github.com" target="_blank" style="color:#4a9eff">github.com</a> et cliquez sur <b>Sign Up</b> (S'inscrire)
    </div>
    <div class="guide-step">
        <div class="guide-step-number">2</div>
        Créez votre compte avec votre e-mail (c'est gratuit). Confirmez votre adresse e-mail.
    </div>
    <div class="guide-step">
        <div class="guide-step-number">3</div>
        Une fois connecté, cliquez sur le bouton vert <b>"New"</b> (Nouveau dépôt). Nommez-le <code>expo-leads-pro</code>. Cochez <b>"Add a README file"</b>. Cliquez <b>"Create repository"</b>.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Étape 2 — Uploader les fichiers (5 min)")
    st.markdown("""
    <div class="guide-step">
        <div class="guide-step-number">1</div>
        Dans votre dépôt GitHub, cliquez sur <b>"Add file"</b> puis <b>"Upload files"</b>
    </div>
    <div class="guide-step">
        <div class="guide-step-number">2</div>
        Glissez-déposez les 3 fichiers téléchargés : <code>app.py</code>, <code>requirements.txt</code>, <code>packages.txt</code>
    </div>
    <div class="guide-step">
        <div class="guide-step-number">3</div>
        Cliquez sur <b>"Commit changes"</b> (bouton vert en bas). C'est sauvegardé !
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Étape 3 — Déployer sur Streamlit Cloud (5 min)")
    st.markdown("""
    <div class="guide-step">
        <div class="guide-step-number">1</div>
        Allez sur <a href="https://share.streamlit.io" target="_blank" style="color:#4a9eff">share.streamlit.io</a> et connectez-vous avec votre compte GitHub
    </div>
    <div class="guide-step">
        <div class="guide-step-number">2</div>
        Cliquez sur <b>"New app"</b>, sélectionnez votre dépôt <code>expo-leads-pro</code>
    </div>
    <div class="guide-step">
        <div class="guide-step-number">3</div>
        Dans "Main file path", écrivez <code>app.py</code>. Cliquez <b>"Deploy!"</b>
    </div>
    <div class="guide-step">
        <div class="guide-step-number">4</div>
        ☕ Attendez 3-5 minutes. Votre app sera accessible via une URL du type <code>votre-app.streamlit.app</code>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📋 Contenu des fichiers à uploader")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**`requirements.txt`** (copiez ce contenu)")
        st.code("""streamlit>=1.32.0
playwright>=1.42.0
beautifulsoup4>=4.12.0
pandas>=2.0.0
openpyxl>=3.1.0
lxml>=4.9.0""", language="text")
    
    with col2:
        st.markdown("**`packages.txt`** (copiez ce contenu)")
        st.code("""chromium
chromium-driver""", language="text")
    
    st.markdown("""
    <div class="success-box">
    ✅ <b>Félicitations !</b> Une fois déployée, partagez simplement l'URL avec vos collègues. 
    L'application tourne 24h/24 gratuitement sur les serveurs de Streamlit.
    </div>
    """, unsafe_allow_html=True)

# ── TAB 3 : HOW IT WORKS ────────────────────────────────────────────────────────
with tab3:
    st.markdown("## ❓ Comment faire mon premier scan ?")
    st.markdown("### C'est aussi simple que de faire une recherche Google !")
    
    st.markdown("""
    <div class="guide-step">
        <div class="guide-step-number">1</div>
        <b>Trouvez la page des exposants :</b> Allez sur le site d'un salon professionnel (ex: Maison&Objet, Cosmoprof...). 
        Cherchez un menu "Exposants" ou "Liste des exposants". Copiez l'URL de cette page.
    </div>
    <div class="guide-step">
        <div class="guide-step-number">2</div>
        <b>Collez l'URL dans l'app :</b> Dans la barre latérale gauche, collez votre URL dans le champ "URL du salon".
    </div>
    <div class="guide-step">
        <div class="guide-step-number">3</div>
        <b>Choisissez le mode Auto :</b> Laissez "Auto" sélectionné — l'app détectera seule si le site utilise des pages ou du défilement infini.
    </div>
    <div class="guide-step">
        <div class="guide-step-number">4</div>
        <b>Lancez le scan :</b> Cliquez sur 🚀 "Lancer le Scan". Attendez 1-3 minutes selon la taille du salon.
    </div>
    <div class="guide-step">
        <div class="guide-step-number">5</div>
        <b>Récupérez vos leads :</b> Les marques ICP apparaissent dans l'onglet "Marques ICP". 
        Cliquez "Télécharger en Excel" pour exporter votre liste propre avec tous les liens LinkedIn !
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 Comment est filtrée votre liste ?")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **🏭 Filtre Secteur**
        
        L'app cherche dans les descriptions des mots-clés liés à vos 6 industries cibles. Les entreprises hors secteur apparaissent quand même mais avec "Autre" comme secteur.
        """)
    with col2:
        st.markdown("""
        **🔄 Filtre Marque/Distrib**
        
        Si la description contient "distributeur", "grossiste", "importateur", etc. → l'entreprise va dans l'onglet **Distributeurs** automatiquement.
        """)
    with col3:
        st.markdown("""
        **🛒 Détection E-commerce**
        
        Activez l'option dans la barre latérale. L'app visite chaque site et cherche un panier d'achat, un bouton "Commander", etc.
        """)
    
    st.markdown("""
    <div class="warning-box">
    ⚠️ <b>Conseil important :</b> Certains sites de salons bloquent le scraping automatique. 
    Si vous obtenez 0 résultat, essayez de changer le mode (Pagination vs Infinite Scroll), 
    ou contactez directement l'organisateur du salon pour obtenir la liste en PDF.
    </div>
    """, unsafe_allow_html=True)

# ─── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#404060; font-size:0.8rem; padding: 1rem 0;">
    ExpoLeads Pro — Construit avec Streamlit & Playwright • Données traitées localement, aucun stockage externe
</div>
""", unsafe_allow_html=True)
