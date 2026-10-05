#!/usr/bin/env python3
"""
Module de Sidebar Commune
========================

Fournit une sidebar cohérente avec logo et navigation
pour toutes les pages de l'application.
"""

import streamlit as st
import streamlit.components.v1 as components
import json
# Remarque: aucune dépendance JSON nécessaire ici; import volontairement non utilisé retiré
from pathlib import Path
import sys
import os
import torch
import importlib.util

# Ajouter le répertoire parent au path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

def init_navigation_history():
    """Initialise l'historique de navigation."""
    if "navigation_history" not in st.session_state:
        st.session_state.navigation_history = ["app.py"]  # Toujours commencer par l'accueil

def clear_sidebar_cache():
    """Nettoie les caches de la sidebar pour éviter l'accumulation."""
    cache_keys = [
        "sidebar_css_loaded",
        "sidebar_logo_loaded", 
        "sidebar_scroll_script_loaded",
        "main_scroll_script_loaded",
        "system_status_expanded",
        "about_expanded"
    ]
    
    for key in cache_keys:
        if key in st.session_state:
            del st.session_state[key]

def add_to_navigation_history(current_page):
    """Ajoute la page actuelle à l'historique.
    Normalise la valeur stockée pour être compatible avec st.switch_page.
    """
    if "navigation_history" not in st.session_state:
        init_navigation_history()

    # Normaliser la cible de navigation: utiliser des chemins relatifs attendus par st.switch_page
    nav_token = current_page
    try:
        basename = Path(current_page).name
        if basename == "app.py":
            nav_token = "app.py"
        elif basename:
            nav_token = f"pages/{basename}"
    except Exception:
        # Si ce n'est pas un chemin, conserver tel quel (peut déjà être "app.py" ou "pages/...")
        pass

    # Ne pas ajouter la même page consécutivement
    if not st.session_state.navigation_history or st.session_state.navigation_history[-1] != nav_token:
        st.session_state.navigation_history.append(nav_token)

    # Limiter l'historique à 10 pages
    if len(st.session_state.navigation_history) > 10:
        st.session_state.navigation_history = st.session_state.navigation_history[-10:]

def get_previous_page():
    """Retourne la page précédente dans l'historique."""
    if "navigation_history" not in st.session_state or len(st.session_state.navigation_history) <= 1:
        return "app.py"  # Retour à l'accueil par défaut
    
    # Retourner la page précédente (avant-dernière)
    return st.session_state.navigation_history[-2]

def check_module_availability(module_name):
    """Vérifie si un module est disponible."""
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except ImportError:
        return False

@st.cache_data(ttl=300)  # Cache pour 5 minutes
def get_system_status_data():
    """Récupère les données d'état du système avec cache."""
    # Status des modules Python essentiels
    modules_status = {
        "🐍 Python Core": True,
        "🌐 Streamlit": check_module_availability("streamlit"),
        "🧠 PyTorch": check_module_availability("torch"),
        "📷 OpenCV": check_module_availability("cv2"),
        "🖼️ PIL/Pillow": check_module_availability("PIL"),
        "🔢 NumPy": check_module_availability("numpy"),
        "🤖 Groq API": check_module_availability("groq"),
    }
    
    # Status des modèles IA
    from config.config import AppConfig
    cls_path = AppConfig.CLASSIFICATION_MODEL_PATH
    seg_path = AppConfig.SEGMENTATION_MODEL_PATH
    
    models_status = {
        "classification": {
            "available": cls_path.exists(),
            "name": cls_path.name
        },
        "segmentation": {
            "available": seg_path.exists(),
            "name": seg_path.name
        }
    }
    
    # Status du système
    system_status = {}
    
    # GPU/CPU status
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        system_status["gpu"] = {
            "available": True,
            "name": gpu_name[:20] + "...",
            "vram": torch.cuda.get_device_properties(0).total_memory // 1024**3
        }
    else:
        system_status["gpu"] = {"available": False}
    
    # Mémoire disponible
    try:
        import psutil
        memory = psutil.virtual_memory()
        system_status["memory"] = {
            "percent": memory.percent,
            "available": True
        }
    except ImportError:
        system_status["memory"] = {"available": False}
    
    # Status des assets
    assets_path = current_dir / "assets"
    if assets_path.exists():
        images_path = assets_path / "images"
        system_status["assets"] = {
            "available": True,
            "images": images_path.exists() and bool(list(images_path.glob("*")))
        }
    else:
        system_status["assets"] = {"available": False}
    
    return modules_status, models_status, system_status

def show_system_status():
    """Affiche l'état du système dans la sidebar."""
    # Récupérer les données avec cache
    modules_status, models_status, system_status = get_system_status_data()
    
    st.markdown("**🔧 Composants du Système**")
    
    # Affichage du statut des modules
    for module, status in modules_status.items():
        if status:
            st.markdown(f"✅ {module}")
        else:
            st.markdown(f"❌ {module}")
    
    st.markdown("---")
    
    # Status des modèles IA
    st.markdown("**🤖 Modèles IA**")
    
    if models_status["classification"]["available"]:
        st.markdown(f"✅ 🎯 Classification: {models_status['classification']['name']}")
    else:
        st.markdown(f"⚠️ 🎯 Classification: Non trouvé")
    
    if models_status["segmentation"]["available"]:
        st.markdown(f"✅ 📍 Segmentation: {models_status['segmentation']['name']}")
    else:
        st.markdown(f"⚠️ 📍 Segmentation: Non trouvé")
    
    # OpenCV (toujours disponible)
    st.markdown("✅ 🔧 OpenCV (Segmentation)")
    
    st.markdown("---")
    
    # Status du système
    st.markdown("**⚡ Performance Système**")
    
    # GPU/CPU status
    if system_status["gpu"]["available"]:
        st.markdown(f"🚀 GPU: {system_status['gpu']['name']}")
        st.markdown(f"💾 VRAM: {system_status['gpu']['vram']} GB")
    else:
        st.markdown("💻 Mode: CPU uniquement")
    
    # Mémoire disponible
    if system_status["memory"]["available"]:
        memory_percent = system_status["memory"]["percent"]
        if memory_percent < 80:
            st.markdown(f"✅ RAM: {memory_percent:.1f}% utilisée")
        else:
            st.markdown(f"⚠️ RAM: {memory_percent:.1f}% utilisée")
    else:
        st.markdown("ℹ️ RAM: Non disponible")
    
    # Status des assets
    st.markdown("---")
    st.markdown("**📁 Ressources**")
    
    if system_status["assets"]["available"]:
        st.markdown("✅ 📂 Dossier Assets")
        
        if system_status["assets"]["images"]:
            st.markdown("✅ 🖼️ Images")
        else:
            st.markdown("⚠️ 🖼️ Images manquantes")
    else:
        st.markdown("❌ 📂 Dossier Assets")

def show_common_sidebar(current_page=None):
    """
    Affiche la sidebar commune avec logo, bouton Accueil et bouton Retour.
    
    Args:
        current_page (str): Nom de la page actuelle pour l'historique de navigation
    """
    # Initialiser l'historique de navigation
    init_navigation_history()

    # Fallback sur la session si l'argument n'est pas fourni
    if current_page is None:
        current_page = st.session_state.get("active_nav_page")

    # Normaliser et réduire à un basename stable (indépendant de l'OS)
    page_basename = ""
    if current_page:
        page_basename = Path(current_page).name
        add_to_navigation_history(current_page)
        # Mettre à jour la page active pour la persistance (utile après Retour/Avancer)
        st.session_state.active_nav_page = current_page
        
        # Nettoyer les caches de navigation pour éviter l'accumulation
        clear_sidebar_cache()
    
    # CSS pour la sidebar avec séparateur et indicateurs de page active
    # Utiliser un cache pour éviter les rechargements répétés
    if "sidebar_css_loaded" not in st.session_state:
        st.session_state.sidebar_css_loaded = True
        st.markdown("""
        <style>
        /* Séparateur latéral (splitter) en bordeaux clair */
        section[data-testid="stSidebar"] {
            border-right: 2px solid #b56576 !important; /* bordeaux clair */
            box-shadow: 2px 0 4px rgba(181, 101, 118, 0.25);
        }
        
        /* Scrollbar en bordeaux clair (tous conteneurs) */
        section[data-testid="stSidebar"],
        div[data-testid="stAppViewContainer"] {
            scrollbar-width: thin; /* Firefox */
            scrollbar-color: rgba(181, 101, 118, 0.45) #111111; /* Firefox: thumb track */
        }
        
        /* WebKit (Chrome/Edge/Safari) - appliquer aux zones défilantes principales */
        section[data-testid="stSidebar"] ::-webkit-scrollbar,
        div[data-testid="stAppViewContainer"] ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        section[data-testid="stSidebar"] ::-webkit-scrollbar-track,
        div[data-testid="stAppViewContainer"] ::-webkit-scrollbar-track {
            background: #111111;
            border-radius: 4px;
        }
        section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb,
        div[data-testid="stAppViewContainer"] ::-webkit-scrollbar-thumb {
            background: rgba(181, 101, 118, 0.45);
            border-radius: 6px;
            border: 2px solid transparent; /* évite l'effet de superposition grise */
            background-clip: padding-box;  /* garde les bords nets sans overlay */
        }
        section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover,
        div[data-testid="stAppViewContainer"] ::-webkit-scrollbar-thumb:hover {
            background: rgba(181, 101, 118, 0.65);
        }
        
        /* Centrage + responsive du logo dans la sidebar */
        .sidebar-logo {
            text-align: center;
            margin-bottom: 0.75rem;
        }
        .sidebar-logo img {
            display: block;
            margin: 0 auto;
            width: clamp(140px, 80%, 240px);
            height: auto;
        }
        
        /* Liens de page (st.page_link) stylés comme des boutons */
        /* Encadrer et harmoniser TOUS les liens de page dans la sidebar */
        section[data-testid="stSidebar"] a[data-testid="stPageLink"],
        section[data-testid="stSidebar"] a[data-testid^="stPageLink"],
        section[data-testid="stSidebar"] a[href*="pages/"] {
            display: flex !important;
            align-items: center !important;
            gap: 0.5rem !important;
            text-decoration: none !important;
            color: #e5e7eb !important; /* gris clair lisible */
            margin: 0.28rem 0 !important; /* espace un peu plus généreux */
            padding: 0.55rem 0.95rem !important; /* soft */
            border-radius: 12px !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            background: #141414 !important;
            box-sizing: border-box !important;
            transition: background-color .15s ease, border-color .15s ease, box-shadow .15s ease, color .15s ease !important;
            position: relative !important; /* pour positionner le marqueur actif */
        }
        section[data-testid="stSidebar"] a[data-testid="stPageLink"]:hover,
        section[data-testid="stSidebar"] a[data-testid^="stPageLink"]:hover,
        section[data-testid="stSidebar"] a[href*="pages/"]:hover {
            background: #1a1a1a !important;
            border-color: rgba(255,154,102,0.45) !important;
            box-shadow: 0 0 0 2px rgba(255,154,102,0.25), 0 0 12px rgba(255,154,102,0.28) !important; /* lueur externe douce */
        }
        /* Page active via aria-current OU via marqueurs (classe/is-active ou data-nav-active) */
        section[data-testid="stSidebar"] a[data-testid="stPageLink"][aria-current="page"],
        section[data-testid="stSidebar"] a[data-testid^="stPageLink"][aria-current="page"],
        section[data-testid="stSidebar"] a[href*="pages/"][aria-current="page"],
        section[data-testid="stSidebar"] a.is-active,
        section[data-testid="stSidebar"] a[data-nav-active="true"] {
            box-shadow: inset 0 0 0 2px #ff9a66 !important; /* contour orange net */
            border-color: #ff9a66 !important;
            background: transparent !important; /* non opaque */
            color: #ff9a66 !important;
            font-weight: 600 !important;
        }
        /* Marqueur: point orange en extrémité droite pour la page active */
        section[data-testid="stSidebar"] a[data-testid="stPageLink"][aria-current="page"]::after,
        section[data-testid="stSidebar"] a[data-testid^="stPageLink"][aria-current="page"]::after,
        section[data-testid="stSidebar"] a[href*="pages/"][aria-current="page"]::after,
        section[data-testid="stSidebar"] a.is-active::after,
        section[data-testid="stSidebar"] a[data-nav-active="true"]::after {
            content: "";
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: #ff9a66;
            box-shadow: 0 0 0 2px rgba(255,154,102,0.25);
        }
        /* Lueur externe supplémentaire quand la page active est survolée */
        section[data-testid="stSidebar"] a[data-testid="stPageLink"][aria-current="page"]:hover,
        section[data-testid="stSidebar"] a[data-testid^="stPageLink"][aria-current="page"]:hover,
        section[data-testid="stSidebar"] a[href*="pages/"][aria-current="page"]:hover,
        section[data-testid="stSidebar"] a.is-active:hover,
        section[data-testid="stSidebar"] a[data-nav-active="true"]:hover {
            box-shadow: inset 0 0 0 2px #ff9a66, 0 0 12px rgba(255,154,102,0.32) !important;
        }
        
        /* Réduire l'espace vertical général dans la sidebar */
        section[data-testid="stSidebar"] > div { gap: 0.25rem !important; }
        </style>
        """, unsafe_allow_html=True)
    
    with st.sidebar:
        # Logo de l'application en haut de la sidebar - avec cache
        if "sidebar_logo_loaded" not in st.session_state:
            st.session_state.sidebar_logo_loaded = True
            
            logo_path = Path(current_dir / "assets" / "images")
            logo_files = []
            if logo_path.exists():
                for ext in ['png', 'jpg', 'jpeg', 'svg', 'ico']:
                    logo_files.extend(logo_path.glob(f"*.{ext}"))
            
            if logo_files:
                # Centrage + responsive via wrapper et largeur adaptative
                st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
                st.image(str(logo_files[0]), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                # Placeholder centré et responsive
                st.markdown("""
                <div class="sidebar-logo" style="padding: 1rem; background: #111111; border-radius: 8px;">
                    <h2 style="color: #ff6b35; margin: 0;">🏗️</h2>
                    <p style="color: white; margin: 0; font-size: 0.8rem;">Logo Application</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Boutons de navigation
        is_home_page = page_basename == "app.py"
        if is_home_page:
            # Centrer le bouton Accueil lorsque l'on est déjà sur l'accueil
            spacer_left, center_col, spacer_right = st.columns([1, 2, 1])
            with center_col:
                home_key = f"sidebar_home_btn_{current_page or 'default'}"
                if st.button("🏠 Accueil", use_container_width=True, key=home_key):
                    # Réinitialiser l'historique lors du retour à l'accueil
                    st.session_state.navigation_history = ["app.py"]
                    st.switch_page("app.py")
        else:
            # Disposition classique: Retour à gauche, Accueil à droite
            col1, col2 = st.columns(2)
            with col1:
                # Bouton Retour - seulement si pas sur l'accueil
                if current_page and current_page != "app.py" and len(st.session_state.navigation_history) > 1:
                    back_key = f"sidebar_back_btn_{current_page or 'default'}"
                    if st.button("⬅️ Retour", use_container_width=True, key=back_key):
                        previous_page = get_previous_page()
                        # Supprimer la page actuelle de l'historique avant de naviguer
                        if len(st.session_state.navigation_history) > 1:
                            st.session_state.navigation_history.pop()
                        st.switch_page(previous_page)
            with col2:
                # Bouton Accueil
                home_key = f"sidebar_home_btn_{current_page or 'default'}"
                if st.button("🏠 Accueil", use_container_width=True, key=home_key):
                    # Réinitialiser l'historique lors du retour à l'accueil
                    st.session_state.navigation_history = ["app.py"]
                    st.switch_page("app.py")
        
        st.markdown("---")
        
        # Navigation Rapide (liens natifs avec aria-current pour l'état actif)
        st.markdown("### 🚀 Navigation Rapide")
        st.markdown('<div class="quick-nav">', unsafe_allow_html=True)

        # Renforcement de l'état actif pour certains navigateurs qui n'appliquent pas aria-current
        # Utiliser un mapping par basename pour éviter la dépendance aux chemins/émoticônes
        page_to_sub = {
            "🔍_Detection_Simple.py": "Detection_Simple.py",
            "📊_Analyse_Batch.py": "Analyse_Batch.py",
            "📹_Detection_Temps_Reel.py": "Detection_Temps_Reel.py",
            "📈_Tableau_de_Bord.py": "Tableau_de_Bord.py",
            "💬_Chat_Assistant.py": "Chat_Assistant.py",
        }
        active_sub = page_to_sub.get(page_basename)
        if active_sub:
            st.markdown(f"""
            <style>
            section[data-testid='stSidebar'] a[href*='{active_sub}'] {{
                box-shadow: inset 0 0 0 2px #ff9a66 !important;
                border-color: #ff9a66 !important;
                background: transparent !important;
                color: #ff9a66 !important;
                font-weight: 600 !important;
            }}
            section[data-testid='stSidebar'] a[href*='{active_sub}']::after {{
                content: "";
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
                width: 9px;
                height: 9px;
                border-radius: 50%;
                background: #ff9a66;
                box-shadow: 0 0 0 2px rgba(255,154,102,0.25);
            }}
            section[data-testid='stSidebar'] a[href*='{active_sub}']:hover {{
                box-shadow: inset 0 0 0 2px #ff9a66, 0 0 12px rgba(255,154,102,0.32) !important;
            }}
            </style>
            """, unsafe_allow_html=True)

        st.page_link("pages/🔍_Detection_Simple.py", label="🔍 Détection Simple", use_container_width=True)
        st.markdown('<span id="nav-marker-simple" class="nav-marker" data-key="simple"></span>', unsafe_allow_html=True)
        st.page_link("pages/📊_Analyse_Batch.py", label="📊 Analyse Batch", use_container_width=True)
        st.markdown('<span id="nav-marker-batch" class="nav-marker" data-key="batch"></span>', unsafe_allow_html=True)
        st.page_link("pages/📹_Detection_Temps_Reel.py", label="📹 Détection en temps réel", use_container_width=True)
        st.markdown('<span id="nav-marker-realtime" class="nav-marker" data-key="realtime"></span>', unsafe_allow_html=True)
        st.page_link("pages/📈_Tableau_de_Bord.py", label="📈 Tableau de Bord", use_container_width=True)
        st.markdown('<span id="nav-marker-dashboard" class="nav-marker" data-key="dashboard"></span>', unsafe_allow_html=True)
        st.page_link("pages/💬_Chat_Assistant.py", label="💬 Chat Assistant", use_container_width=True)
        st.markdown('<span id="nav-marker-chat" class="nav-marker" data-key="chat"></span>', unsafe_allow_html=True)

        # Activer explicitement le lien de la page courante via substring d'URL (sans se fier à aria-current)
        # Utiliser un cache pour éviter les rechargements répétés
        if active_sub and f"nav_activation_script_{active_sub}" not in st.session_state:
            st.session_state[f"nav_activation_script_{active_sub}"] = True
            components.html(
                f"""
                <script>
                (function(){{
                    const sub = {json.dumps(active_sub)};
                    function activate(){{
                        const sidebar = parent.document.querySelector('section[data-testid="stSidebar"]');
                        if(!sidebar || !sub) return false;
                        const links = sidebar.querySelectorAll('a[href]');
                        let target = null;
                        for(const a of links){{
                            const href = a.getAttribute('href') || '';
                            if(href.indexOf(sub) !== -1){{ target = a; break; }}
                        }}
                        if(!target) return false;
                        target.setAttribute('aria-current','page');
                        target.classList.add('is-active');
                        target.setAttribute('data-nav-active','true');
                        return true;
                    }}
                    let tries=0; const t=setInterval(()=>{{ tries++; if(activate()||tries>20){{ clearInterval(t); }} }}, 80);
                }})();
                </script>
                """,
                height=0,
                width=0,
            )

        # Déterminer la clé active à partir du basename de la page courante
        active_key_map = {
            "🔍_Detection_Simple.py": "simple",
            "📊_Analyse_Batch.py": "batch",
            "📹_Detection_Temps_Reel.py": "realtime",
            "📈_Tableau_de_Bord.py": "dashboard",
            "💬_Chat_Assistant.py": "chat",
        }
        active_key = active_key_map.get(page_basename, "")

        # Script client: applique data-nav-active/aria-current via marqueurs
        # Utiliser un cache pour éviter les rechargements répétés
        if f"nav_marker_script_{active_key}" not in st.session_state:
            st.session_state[f"nav_marker_script_{active_key}"] = True
            _script = """
            <script>
            (function(){
                const activeKey = __ACTIVE_KEY__;
                function run(){
                    const sidebar = parent.document.querySelector('section[data-testid="stSidebar"]');
                    if(!sidebar) return false;
                    if(!activeKey) return true;
                    const marker = parent.document.querySelector('#nav-marker-' + activeKey);
                    if(!marker) return false;
                    // Trouver l'ancre la plus proche avant le marqueur
                    let container = marker.parentElement; // wrapper streamlit
                    if(!container) return false;
                    let probe = container.previousElementSibling;
                    let safety = 0;
                    let found = null;
                    while(probe && safety++ < 8){
                        const a = probe.querySelector('a[data-testid^="stPageLink"], a[href]');
                        if(a){ found = a; break; }
                        probe = probe.previousElementSibling;
                    }
                    // Fallback: chercher après le marqueur
                    if(!found){
                        probe = container.nextElementSibling; safety = 0;
                        while(probe && safety++ < 4){
                            const a = probe.querySelector('a[data-testid^="stPageLink"], a[href]');
                            if(a){ found = a; break; }
                            probe = probe.nextElementSibling;
                        }
                    }
                    if(!found) return false;
                    found.setAttribute('aria-current','page');
                    found.classList.add('is-active');
                    found.setAttribute('data-nav-active','true');
                    return true;
                }
                // Essayer plusieurs fois pour couvrir les rerenders
                let attempts = 0;
                const timer = setInterval(() => {
                    attempts += 1;
                    if(run() || attempts > 20) { clearInterval(timer); }
                }, 80);
            })();
            </script>
            """.replace("__ACTIVE_KEY__", json.dumps(active_key))
            components.html(_script, height=0, width=0)

        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")

        # Mémoriser la position de scroll de la sidebar entre les reruns/navigations
        # Utiliser un cache pour éviter les rechargements répétés
        if "sidebar_scroll_script_loaded" not in st.session_state:
            st.session_state.sidebar_scroll_script_loaded = True
            components.html(
                """
                <script>
                (function(){
                    const key = 'st_sidebar_scrollTop_v1';
                    function getSidebar(){ return parent.document.querySelector('section[data-testid="stSidebar"]'); }
                    function restore(){
                        const el = getSidebar();
                        if(!el) return;
                        const top = parseFloat(localStorage.getItem(key) || '0');
                        if (!isNaN(top)) { el.scrollTop = top; }
                    }
                    function listen(){
                        const el = getSidebar();
                        if(!el) return;
                        el.addEventListener('scroll', () => {
                            localStorage.setItem(key, el.scrollTop || 0);
                        }, {passive:true});
                    }
                    restore();
                    setTimeout(restore, 100);
                    setTimeout(restore, 400);
                    setTimeout(restore, 1000);
                    listen();
                })();
                </script>
                """,
                height=0,
                width=0,
            )

        # Préserver aussi la position de scroll de la zone principale (contenu)
        if "main_scroll_script_loaded" not in st.session_state:
            st.session_state.main_scroll_script_loaded = True
            components.html(
                """
                <script>
                (function(){
                    const key = 'st_main_scrollY_v1';
                    function restore(){
                        try{
                            const top = parseFloat(localStorage.getItem(key) || '0');
                            if(!isNaN(top)) { parent.window.scrollTo(0, top); }
                        }catch(e){}
                    }
                    function listen(){
                        try{
                            parent.window.addEventListener('scroll', () => {
                                try{ localStorage.setItem(key, parent.window.scrollY || 0); }catch(e){}
                            }, {passive:true});
                        }catch(e){}
                    }
                    restore();
                    setTimeout(restore, 120);
                    setTimeout(restore, 600);
                    setTimeout(restore, 1200);
                    listen();
                })();
                </script>
                """,
                height=0,
                width=0,
            )
        
        # Section État du Système - avec cache pour éviter les rechargements
        if "system_status_expanded" not in st.session_state:
            st.session_state.system_status_expanded = False
            
        with st.expander("🔧 État du Système", expanded=st.session_state.system_status_expanded):
            show_system_status()
            # Mémoriser l'état de l'expander
            st.session_state.system_status_expanded = st.session_state.get("system_status_expanded", False)
        
        # Section À propos - avec cache pour éviter les rechargements
        if "about_expanded" not in st.session_state:
            st.session_state.about_expanded = False
            
        with st.expander("ℹ️ À propos", expanded=st.session_state.about_expanded):
            st.markdown("""
            **🏗️ Détection de Fissures IA**
            
            Application professionnelle pour l'inspection 
            automatisée des structures en béton.
            
            **🤖 Technologies :**
            - ResNet50 (Classification)
            - U-Net (Segmentation)  
            - OpenCV (Traitement d'image)
            - Groq API (Assistant IA)
            
            **👥 Conçue pour :**
            - Ingénieurs en génie civil
            - Techniciens du bâtiment  
            - Inspecteurs de structures
            """)
            # Mémoriser l'état de l'expander
            st.session_state.about_expanded = st.session_state.get("about_expanded", False)
        
        st.markdown("---")



def apply_theme():
    """
    Applique le thème noir cohérent à la page.
    Doit être appelé sur chaque page pour la cohérence visuelle.
    """
    from config.config import StreamlitConfig
    st.markdown(StreamlitConfig.CUSTOM_CSS, unsafe_allow_html=True)

def setup_common_page_elements(current_page=None):
    """
    Configure tous les éléments communs d'une page :
    - Thème noir
    - Sidebar avec logo, bouton Accueil et bouton Retour
    
    Args:
        current_page (str): Nom de la page actuelle pour l'historique de navigation
    """
    apply_theme()
    show_common_sidebar(current_page)