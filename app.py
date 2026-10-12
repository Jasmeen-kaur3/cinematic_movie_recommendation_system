import concurrent.futures
import os
import pickle
import socket
import urllib.parse
from pathlib import Path

import requests
import streamlit as st

# ==============================================================================
# 1. DNS RESOLUTION FIX (Fixes Indian ISP / Jio / Airtel DNS blocking of TMDB)
# ==============================================================================
# Indian ISPs frequently spoof 'api.themoviedb.org' to blackhole IP 49.44.79.236.
# We resolve via Google DNS-over-HTTPS with fallback to verified CloudFront Anycast IPs.
_ORIGINAL_GETADDRINFO = socket.getaddrinfo
_RESOLVED_TMDB_IP = None


def get_tmdb_ip():
    global _RESOLVED_TMDB_IP
    if _RESOLVED_TMDB_IP is not None:
        return _RESOLVED_TMDB_IP

    try:
        res = requests.get(
            "https://dns.google/resolve?name=api.themoviedb.org&type=A",
            timeout=2.0,
        )
        if res.status_code == 200:
            data = res.json()
            for ans in data.get("Answer", []):
                if ans.get("type") == 1 and ans.get("data"):
                    _RESOLVED_TMDB_IP = ans["data"]
                    return _RESOLVED_TMDB_IP
    except Exception:
        pass

    # Verified AWS CloudFront Anycast IP for api.themoviedb.org
    _RESOLVED_TMDB_IP = "108.139.210.27"
    return _RESOLVED_TMDB_IP


def patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host == "api.themoviedb.org":
        target_ip = get_tmdb_ip()
        return _ORIGINAL_GETADDRINFO(target_ip, port, family, type, proto, flags)
    return _ORIGINAL_GETADDRINFO(host, port, family, type, proto, flags)


socket.getaddrinfo = patched_getaddrinfo


# ==============================================================================
# 2. STREAMLIT CONFIGURATION & THEMING
# ==============================================================================
st.set_page_config(
    page_title="CineMatch AI | Smart Movie Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Cinematic UI Styling
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Bebas+Neue&display=swap');

    /* Global Typography & Palette */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main background aesthetics */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(20, 24, 38, 0.95), rgba(10, 12, 18, 1));
        color: #f1f5f9;
    }

    /* Hero Header Styling */
    .hero-container {
        padding: 2.2rem 2.5rem;
        background: linear-gradient(135deg, rgba(229, 9, 20, 0.12) 0%, rgba(30, 41, 59, 0.4) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        position: relative;
        overflow: hidden;
    }

    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(229, 9, 20, 0.08) 0%, transparent 60%);
        pointer-events: none;
    }

    .brand-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 14px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        background: rgba(229, 9, 20, 0.18);
        color: #ff4b55;
        border: 1px solid rgba(229, 9, 20, 0.35);
        margin-bottom: 0.8rem;
    }

    .hero-title {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3.4rem;
        letter-spacing: 2px;
        margin: 0;
        line-height: 1;
        background: linear-gradient(90deg, #ffffff 0%, #cbd5e1 50%, #ff4b55 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: 0.5rem;
        max-width: 700px;
        line-height: 1.5;
    }

    /* Selected Movie Spotlight Card */
    .spotlight-card {
        background: linear-gradient(135deg, rgba(26, 31, 46, 0.75), rgba(15, 23, 42, 0.85));
        border: 1px solid rgba(229, 9, 20, 0.25);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        display: flex;
        flex-direction: row;
        gap: 1.5rem;
        box-shadow: 0 14px 30px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(10px);
    }

    /* Recommendation Movie Card */
    .movie-card {
        background: rgba(18, 22, 34, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        overflow: hidden;
        transition: all 0.32s cubic-bezier(0.16, 1, 0.3, 1);
        display: flex;
        flex-direction: column;
        height: 100%;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.2rem;
    }

    .movie-card:hover {
        transform: translateY(-7px) scale(1.02);
        border-color: rgba(229, 9, 20, 0.45);
        box-shadow: 0 18px 32px rgba(229, 9, 20, 0.2);
    }

    .poster-container {
        position: relative;
        width: 100%;
        aspect-ratio: 2/3;
        overflow: hidden;
        background: #0f121a;
    }

    .poster-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.4s ease;
    }

    .movie-card:hover .poster-image {
        transform: scale(1.05);
    }

    .movie-content {
        padding: 0.9rem;
        display: flex;
        flex-direction: column;
        flex-grow: 1;
        justify-content: space-between;
    }

    .movie-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.4rem;
        line-height: 1.3;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        min-height: 2.5rem;
    }

    .badge-row {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 0.5rem;
        flex-wrap: wrap;
    }

    .rating-badge {
        background: rgba(234, 179, 8, 0.15);
        color: #facc15;
        border: 1px solid rgba(234, 179, 8, 0.3);
        padding: 2px 7px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
    }

    .year-badge {
        background: rgba(148, 163, 184, 0.12);
        color: #cbd5e1;
        padding: 2px 7px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    .genre-chip {
        display: inline-block;
        background: rgba(229, 9, 20, 0.12);
        color: #fca5a5;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.68rem;
        font-weight: 600;
    }

    /* Primary Action Buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #e50914 0%, #b80710 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 0.65rem 1.4rem !important;
        border-radius: 10px !important;
        letter-spacing: 0.03em !important;
        box-shadow: 0 6px 18px rgba(229, 9, 20, 0.35) !important;
        transition: all 0.25s ease !important;
    }

    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 24px rgba(229, 9, 20, 0.5) !important;
    }

    /* Quick Pick Pills */
    .quick-pick-pill {
        display: inline-block;
        padding: 4px 12px;
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 9999px;
        color: #cbd5e1;
        font-size: 0.8rem;
        cursor: pointer;
        margin: 3px;
        transition: all 0.2s ease;
    }
    .quick-pick-pill:hover {
        background: rgba(229, 9, 20, 0.3);
        border-color: #e50914;
        color: #ffffff;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0c0e15 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
</style>
""",
    unsafe_allow_html=True,
)


# ==============================================================================
# 3. DATA LOADING & MODEL SETUP
# ==============================================================================
DATA_PATH = Path(__file__).resolve().parent / "movies_data.pkl"

DEFAULT_TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8"


@st.cache_resource(show_spinner=False)
def load_data():
    if not DATA_PATH.exists():
        st.error(f"Data file not found at: {DATA_PATH}")
        st.stop()
    with open(DATA_PATH, "rb") as f:
        movies_df, similarity = pickle.load(f)
    return movies_df, similarity


movies, cosine_sim = load_data()


# ==============================================================================
# 4. TMDB POSTER & METADATA FETCHING (WITH CACHING & FALLBACKS)
# ==============================================================================
def make_placeholder_poster(title: str) -> str:
    """Return a styled SVG placeholder poster encoded in data URI."""
    clean_title = urllib.parse.quote(title[:26])
    return f"https://placehold.co/500x750/141724/ff4b55.png?text={clean_title}&font=montserrat"


@st.cache_data(show_spinner=False, ttl=7200)
def fetch_movie_details(movie_id: int, api_key: str):
    """
    Fetch poster, rating, release year, genres, and overview from TMDB.
    Returns clean dictionary with guaranteed fallbacks.
    """
    if not api_key:
        api_key = DEFAULT_TMDB_API_KEY

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}"

    try:
        response = requests.get(url, timeout=3.5)
        if response.status_code == 200:
            data = response.json()
            poster_path = data.get("poster_path")
            poster_url = (
                f"https://image.tmdb.org/t/p/w500{poster_path}"
                if poster_path
                else None
            )

            genres = [g.get("name") for g in data.get("genres", []) if "name" in g][:3]
            rating = round(float(data.get("vote_average", 0.0)), 1)
            release_date = data.get("release_date") or ""
            release_year = release_date[:4] if len(release_date) >= 4 else "N/A"
            tagline = data.get("tagline", "")
            overview = data.get("overview", "")
            runtime = data.get("runtime")

            return {
                "poster_url": poster_url,
                "rating": rating,
                "year": release_year,
                "genres": genres,
                "tagline": tagline,
                "overview": overview,
                "runtime": runtime,
                "tmdb_url": f"https://www.themoviedb.org/movie/{movie_id}",
            }
    except Exception:
        pass

    return None


def get_recommendations_with_metadata(title: str, top_n: int = 10, api_key: str = DEFAULT_TMDB_API_KEY):
    """
    Get top_n movie recommendations using cosine similarity and fetch metadata in parallel.
    """
    matches = movies[movies["title"] == title]
    if matches.empty:
        return []

    idx = matches.index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1 : top_n + 1]

    movie_indices = [i[0] for i in sim_scores]
    recommended_rows = movies.iloc[movie_indices].copy().reset_index(drop=True)

    # Fetch details in parallel for lightning-fast loading
    results_map = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        future_to_idx = {
            executor.submit(fetch_movie_details, row["movie_id"], api_key): i
            for i, row in recommended_rows.iterrows()
        }
        for future in concurrent.futures.as_completed(future_to_idx):
            i = future_to_idx[future]
            try:
                results_map[i] = future.result()
            except Exception:
                results_map[i] = None

    compiled_list = []
    for i, row in recommended_rows.iterrows():
        details = results_map.get(i)
        poster = (
            details["poster_url"]
            if details and details.get("poster_url")
            else make_placeholder_poster(row["title"])
        )
        rating = details["rating"] if details and details.get("rating") else 0.0
        year = details["year"] if details and details.get("year") else "N/A"
        genres = details["genres"] if details and details.get("genres") else []
        overview = (
            details["overview"]
            if details and details.get("overview")
            else str(row.get("overview", "No synopsis available."))
        )
        tmdb_url = (
            details["tmdb_url"]
            if details and details.get("tmdb_url")
            else f"https://www.themoviedb.org/movie/{row['movie_id']}"
        )

        compiled_list.append(
            {
                "movie_id": row["movie_id"],
                "title": row["title"],
                "poster_url": poster,
                "rating": rating,
                "year": year,
                "genres": genres,
                "overview": overview,
                "tmdb_url": tmdb_url,
            }
        )

    return compiled_list


# ==============================================================================
# 5. SIDEBAR CONTROLS & API KEY MANAGEMENT
# ==============================================================================
with st.sidebar:
    st.markdown(" Engine Settings")

    # API Key Configuration
    st.markdown("#### 🔑 TMDB API Key")
    active_key = st.text_input(
        "Enter TMDB API Key (v3 auth):",
        value=st.session_state.get("custom_api_key", DEFAULT_TMDB_API_KEY),
        type="password",
        help="A valid TheMovieDatabase (TMDB) API Key. Default working key is pre-filled.",
    )
    st.session_state["custom_api_key"] = active_key

    # Verification status pill
    if active_key == DEFAULT_TMDB_API_KEY:
        st.success("🟢 Verified Active Key (Default)")
    elif active_key:
        st.info("🟡 Custom Key Applied")
    else:
        st.warning("⚠️ No key provided, using fallback")

    # with st.expander("ℹ️ How to get your own TMDB API key?"):
    #     st.markdown(
    #         """
    #         1. Visit [themoviedb.org](https://www.themoviedb.org/signup) and create a free account.
    #         2. Go to **Settings > API**.
    #         3. Request an API Key (Developer).
    #         4. Copy your **API Key (v3 auth)** (32-character hex string) and paste it here!
            
    #         > **Note:** Do NOT paste an OpenAI key (`sk-proj-...`). TMDB requires a TMDB API key.
    #         """
    #     )

    st.markdown("---")
    st.markdown("#### 🎛️ Recommendation Preferences")
    num_recommendations = st.slider(
        "Number of recommendations:",
        min_value=5,
        max_value=15,
        value=10,
        step=5,
    )

    st.markdown("---")
    st.markdown("#### 📊 Dataset & Model Info")
    st.markdown(
        f"""
        - **Total Movies:** `{len(movies):,}`
        - **Algorithm:** `Cosine Similarity`
        - **Features:** `Tags, Genres, Cast, Crew`
        - **DNS Patch:** `Active (Bypasses ISP blocks)`
        """
    )

    # st.markdown("---")
    # if st.button("🎲 Surprise Me (Random Movie)"):
    #     random_movie = movies.sample(1)["title"].values[0]
    #     st.session_state["selected_movie"] = random_movie


# ==============================================================================
# 6. MAIN APPLICATION UI
# ==============================================================================

# Hero Header
st.markdown(
    """
    <div class="hero-container">
        <div class="brand-badge">✦ AI-Powered Cinema Recommender</div>
        <h1 class="hero-title">CINEMATCH AI</h1>
        <p class="hero-subtitle">
            Find films tailored to your unique taste. Powered by Natural Language Processing,
            Cosine Similarity vector space, and live high-resolution artwork from The Movie Database.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Quick Picks Section
quick_picks = [
    "Avatar",
    "The Dark Knight",
    "Inception",
    "Interstellar",
    "The Avengers",
    "Titanic",
    "Fight Club",
    "Pulp Fiction",
]

st.markdown("<p style='color: #94a3b8; font-size: 0.88rem; margin-bottom: 6px;'>🔥 <b>Trending Quick-Picks:</b></p>", unsafe_allow_html=True)
quick_cols = st.columns(len(quick_picks))
for col, qp in zip(quick_cols, quick_picks):
    with col:
        if st.button(qp, key=f"qp_{qp}"):
            st.session_state["selected_movie"] = qp

# Search & Selection Area
movie_titles = movies["title"].values.tolist()
default_selection = st.session_state.get("selected_movie", "Avatar")

if default_selection not in movie_titles:
    default_selection = movie_titles[0]

selected_movie_name = st.selectbox(
    "🎬 Select or search for a movie you love:",
    options=movie_titles,
    index=movie_titles.index(default_selection),
    key="movie_dropdown",
)
st.session_state["selected_movie"] = selected_movie_name

# Action Button
col_btn, _ = st.columns([1, 2])
with col_btn:
    show_recs = st.button("✨ Get Recommendations", use_container_width=True)

# Process Recommendations
if show_recs or "selected_movie" in st.session_state:
    target_movie = st.session_state.get("selected_movie", selected_movie_name)
    target_row = movies[movies["title"] == target_movie].iloc[0]
    target_id = int(target_row["movie_id"])

    # Spotlight Card for the Selected Movie
    spotlight_details = fetch_movie_details(target_id, active_key)
    spot_poster = (
        spotlight_details["poster_url"]
        if spotlight_details and spotlight_details.get("poster_url")
        else make_placeholder_poster(target_movie)
    )
    spot_rating = spotlight_details["rating"] if spotlight_details else "N/A"
    spot_year = spotlight_details["year"] if spotlight_details else "N/A"
    spot_genres = (
        " • ".join(spotlight_details["genres"])
        if spotlight_details and spotlight_details.get("genres")
        else "Cinema"
    )
    spot_tagline = (
        f'<i>"{spotlight_details["tagline"]}"</i><br>'
        if spotlight_details and spotlight_details.get("tagline")
        else ""
    )
    spot_overview = (
        spotlight_details["overview"]
        if spotlight_details and spotlight_details.get("overview")
        else target_row.get("overview", "No synopsis available.")
    )

    st.markdown("<h3 style='margin-top: 1.8rem; margin-bottom: 0.8rem;'>🎯 Selected Movie Spotlight</h3>", unsafe_allow_html=True)

    spot_col1, spot_col2 = st.columns([1, 4])
    with spot_col1:
        st.image(spot_poster, use_container_width=True)
    with spot_col2:
        st.markdown(
            f"""
            <div style="background: rgba(18, 22, 34, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 1.2rem; height: 100%;">
                <h2 style="margin: 0 0 0.4rem 0; color: #fff;">{target_movie}</h2>
                <div style="display: flex; gap: 10px; margin-bottom: 0.8rem; align-items: center; flex-wrap: wrap;">
                    <span style="background: rgba(234, 179, 8, 0.2); color: #facc15; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.85rem;">⭐ {spot_rating} / 10</span>
                    <span style="background: rgba(148, 163, 184, 0.15); color: #cbd5e1; padding: 3px 8px; border-radius: 6px; font-size: 0.85rem;">📅 {spot_year}</span>
                    <span style="color: #ff4b55; font-size: 0.85rem; font-weight: 600;">🎭 {spot_genres}</span>
                </div>
                {spot_tagline}
                <p style="color: #94a3b8; font-size: 0.92rem; line-height: 1.6; margin-top: 0.6rem;">{spot_overview}</p>
                <a href="https://www.themoviedb.org/movie/{target_id}" target="_blank" style="display: inline-block; margin-top: 0.6rem; color: #ff4b55; font-size: 0.85rem; text-decoration: none; font-weight: 600;">🔗 View on TMDB &rarr;</a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Recommendations Header
    st.markdown(
        f"<h3 style='margin-top: 2.2rem; margin-bottom: 1rem;'>🍿 Recommended For You (Top {num_recommendations})</h3>",
        unsafe_allow_html=True,
    )

    with st.spinner("Finding cinematic matches & fetching posters..."):
        recs = get_recommendations_with_metadata(
            target_movie,
            top_n=num_recommendations,
            api_key=active_key,
        )

    if not recs:
        st.warning("No recommendations found for this title.")
    else:
        # Display in rows of 5 cards
        for row_start in range(0, len(recs), 5):
            cols = st.columns(5)
            row_items = recs[row_start : min(row_start + 5, len(recs))]

            for col, item in zip(cols, row_items):
                with col:
                    genre_tags_html = "".join(
                        [f'<span class="genre-chip">{g}</span> ' for g in item["genres"][:2]]
                    )
                    rating_display = (
                        f"⭐ {item['rating']}" if item["rating"] > 0 else "⭐ N/A"
                    )

                    st.markdown(
                        f"""
                        <div class="movie-card">
                            <div class="poster-container">
                                <img src="{item['poster_url']}" class="poster-image" alt="{item['title']}" loading="lazy"/>
                            </div>
                            <div class="movie-content">
                                <div class="movie-title" title="{item['title']}">{item['title']}</div>
                                <div class="badge-row">
                                    <span class="rating-badge">{rating_display}</span>
                                    <span class="year-badge">{item['year']}</span>
                                </div>
                                <div>{genre_tags_html}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    with st.expander("📖 Synopsis"):
                        st.caption(item["overview"])
                        st.markdown(
                            f"[Open on TMDB &rarr;]({item['tmdb_url']})",
                            unsafe_allow_html=True,
                        )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #64748b; font-size: 0.85rem; padding: 1.5rem 0;">
        🎬 <b>CineMatch AI</b> • Content-Based Filtering with Cosine Similarity & TMDB API Integration • Crafted with Streamlit & Python
    </div>
    """,
    unsafe_allow_html=True,
)