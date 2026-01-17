import streamlit as st
import os
import time
from utils import download_media, get_media_info

# --- Page Configuration ---
st.set_page_config(
    page_title="Universal Media Downloader",
    page_icon="📥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for Premium/Glassmorphism Look ---
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Input Field */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #fff;
        border-radius: 12px;
        padding: 12px;
        backdrop-filter: blur(10px);
    }
    .stTextInput input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }

    /* Buttons */
    .stButton button {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }

    /* Cards/Containers */
    .media-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        margin-bottom: 24px;
    }

    /* Headers */
    h1, h2, h3 {
        color: #f8fafc;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    h1 {
        background: linear-gradient(to right, #60a5fa, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #3b82f6, #a855f7);
    }
</style>
""", unsafe_allow_html=True)

# --- State Management ---
if 'url' not in st.session_state:
    st.session_state.url = ""
if 'media_info' not in st.session_state:
    st.session_state.media_info = None

# --- Main UI ---

# Sidebar for Advanced Options
with st.sidebar:
    st.header("Settings")
    st.markdown("Use these options if downloads fail due to login requirements (e.g. private Instagram/X content).")
    
    if os.path.exists("cookies.txt"):
        st.success("✅ 'cookies.txt' detected! Using it automatically.")
        st.info("To use browser selection instead, delete or rename 'cookies.txt'.")
        use_cookies = False # Ignored in utils, but keeps UI clean
        browser = "chrome"
    else:
        use_cookies = st.checkbox("Use Browser Cookies", help="Enable this if you get 'Login Required' errors. It uses your local browser session.")
        browser = st.selectbox("Select Browser", ["chrome", "edge", "firefox", "brave", "opera"], index=0, disabled=not use_cookies)
        
        st.info("ℹ️ Tip: If you get 'Database' errors, close your browser completely or use a 'cookies.txt' file.")
        
    st.markdown("---")

# Header
col1, col2 = st.columns([1, 6])
with col2:
    st.title("Universal Downloader")
    st.markdown("Download videos from **YouTube**, **Instagram**, and **X (Twitter)** in high quality.")

# Input Section
url_input = st.text_input("Paste URL here...", placeholder="https://youtube.com/watch?v=...", help="Supports YouTube, Instagram Reels/Posts, Twitter Videos")

if url_input:
    # If the URL changed, clear old info
    if url_input != st.session_state.url:
        st.session_state.url = url_input
        st.session_state.media_info = None
        
    # Preview Logic
    if not st.session_state.media_info:
        with st.spinner("Fetching media info..."):
            # Pass cookie settings to metadata fetcher too!
            info = get_media_info(url_input, use_cookies, browser)
            if info['success']:
                st.session_state.media_info = info
            else:
                st.error(f"Could not fetch media info: {info.get('error')}")

# Result & Download Section
if st.session_state.media_info:
    info = st.session_state.media_info
    
    st.markdown('<div class="media-card">', unsafe_allow_html=True)
    
    # Preview Layout
    c1, c2 = st.columns([1, 1])
    
    with c1:
        if info.get('thumbnail'):
            st.image(info['thumbnail'], use_container_width=True, output_format="JPEG")
            
    with c2:
        st.subheader(info.get('title', 'Unknown Title'))
        st.caption(f"Platform: {info.get('platform', 'Unknown')}")
        
        # Options
        quality = st.selectbox("Select Quality", ["Best (Auto)", "1080p", "720p", "Audio Only"], index=0)
        
        # Download Button
        if st.button("Download Now"):
            
            # Progress Bar Placeholder
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Hook for yt-dlp to update Streamlit progress
            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        p = d.get('_percent_str', '0%').replace('%','')
                        progress_bar.progress(float(p)/100)
                        status_text.text(f"Downloading: {d.get('_percent_str')} of {d.get('_total_bytes_str', 'Unknown size')}")
                    except:
                        pass
                if d['status'] == 'finished':
                    progress_bar.progress(1.0)
                    status_text.text("Processing complete! Saving file...")

            # Start Download (to a temp/cache location to stream it back)
            with st.spinner("Processing media..."):
                # Use a temporary directory or just the current folder for staging
                temp_folder = "downloads_temp"
                if not os.path.exists(temp_folder):
                    os.makedirs(temp_folder)
                
                result = download_media(st.session_state.url, temp_folder, quality, progress_hook, use_cookies, browser)
                
            if result['success']:
                st.success("Processing complete! Click below to save to your device.")
                
                try:
                    with open(result['filepath'], "rb") as file:
                        btn = st.download_button(
                            label="📥 Save File to Device",
                            data=file,
                            file_name=os.path.basename(result['filepath']),
                            mime="video/mp4" if "mp4" in result['filepath'] else "audio/mp3"
                        )
                except Exception as e:
                     st.error(f"Error preparing download: {e}")
            else:
                st.error(f"Download failed: {result.get('error')}")

    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("<center style='color: #64748b; font-size: 0.8rem;'>Powered by yt-dlp & Streamlit. For personal use only.</center>", unsafe_allow_html=True)
