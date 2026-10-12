# 🎬 CineMatch AI — Movie Recommendation System

An AI-powered content-based movie recommendation system built with **Python**, **Cosine Similarity / NLP**, and **Streamlit**, integrated with **The Movie Database (TMDB) API** for real-time high-resolution posters and movie metadata.

---

## 🚀 Key Improvements & Fixes

### 1. 🔑 API Key Problem Solved
- **Original Bug 1 (Wrong API Key Type):** The original code contained an OpenAI key (`sk-proj-...`) pasted into the TMDB endpoint (`api.themoviedb.org`). TMDB returned `401 Unauthorized`.
- **Original Bug 2 (Indian ISP DNS Blocking):** In India (Reliance Jio, Airtel, etc.), `api.themoviedb.org` is often DNS-spoofed to a dead IP (`49.44.79.236`), causing `ConnectTimeoutError` and freezing the application.
- **The Solution:**
  - Added a verified, working TMDB API key by default.
  - Implemented automatic **DNS-over-HTTPS (DoH)** and direct CloudFront Anycast IP fallback to bypass ISP blocking.
  - Added parallel asynchronous fetching with `@st.cache_data` and graceful placeholder fallback posters so the app **never hangs or shows broken images**.
  - Added a dynamic **API Key settings panel** in the sidebar where you can view status or plug in your own custom TMDB key anytime.

---

### 2. 🎨 Enhanced Modern Cinematic UI
- **Netflix-Inspired Theme:** Dark gradient theme, glowing accents, and glassmorphism cards.
- **Featured Spotlight Banner:** Highlights the currently selected movie with poster, synopsis, rating, release year, runtime, and genres.
- **Trending Quick-Picks:** One-click chips for popular movies (*Avatar, Inception, Interstellar, The Dark Knight*, etc.).
- **Interactive Controls:**
  - "🎲 Surprise Me!" random movie picker button.
  - Slider to customize number of recommendations (5 to 15 movies).
- **Rich Movie Cards:** Displaying poster artwork with smooth hover-zoom effects, star ratings (⭐), release years, genre chips, and expandable synopsis with TMDB links.

---

## 🛠️ How to Run the App

1. Open your terminal in this project directory:
   ```bash
   cd c:\Users\HP\Desktop\CODSOFT
   ```

2. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

3. The app will automatically open in your default browser at `http://localhost:8501`.
