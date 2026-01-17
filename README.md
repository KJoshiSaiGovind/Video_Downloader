Open your Terminal (VSCode).
Run: streamlit run app.py
Open http://localhost:8501

link:https://video-downloader143.streamlit.app/

# Universal Media Downloader 📥

A premium, user-friendly web application to download videos and images from **YouTube**, **Instagram** (Reels & Posts), and **X (Twitter)** in maximum quality (up to 4K). Built with **Python** and **Streamlit**.


## ✨ Features
*   **Universal Support**: Download from YouTube, Instagram, and X/Twitter with one search bar.
*   **High Quality**: Supports 1080p/4K YouTube videos (auto-merges video+audio).
*   **Smart Fallback**: Automatically handles Instagram Images vs. Videos.
*   **Private Content**: Supports downloading login-restricted content via `cookies.txt`.
*   **Premium UI**: Dark mode with "Glassmorphism" design.

---

## 🚀 How to Run Locally

### Prerequisites
*   **Python 3.8+** installed.
*   **FFmpeg** (Included in the repo or installed independently).

### Installation
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/KJoshiSaiGovind/Video_Downloader.git
    cd Video_Downloader
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the App**:
    ```bash
    streamlit run app.py
    ```
    The app will open in your browser at `http://localhost:8501`.

---

## 🛠 Troubleshooting: "Login Required" Errors

If you try to download a private Instagram post/story or age-restricted YouTube video and get an error, follow these steps:

### Option 1: Use Browser Cookies (Easy)
1.  Open the app sidebar (Left side).
2.  Check **"Use Browser Cookies"**.
3.  Select your logged-in browser (e.g., Chrome).
4.  **Close your browser** (important, as Chrome locks the database).
5.  Click Download.

### Option 2: Use `cookies.txt` (Reliable)
This is the best method if Option 1 fails.
1.  Install a **Get cookies.txt** extension (e.g., [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookies321txt-locally/cclelndahbckbenkjhflccfodgmokloh)).
2.  Go to Instagram.com and log in.
3.  Use the extension to download `cookies.txt`.
4.  **Save the file** as `cookies.txt` inside your project folder (next to `app.py`).
5.  The app will automatically detect it ("✅ 'cookies.txt' detected!") and use it.

---

## ☁️ Deploying to the Web (Streamlit Cloud)

You can host this for free on Streamlit Cloud using the button below or following the steps:

1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Click **New App**.
3.  Select this repository (`Video_Downloader`).
4.  Set **Main file path** to `app.py`.
5.  Click **Deploy**.

**Note for Web Deployment:**
For security reasons, `cookies.txt` is NOT uploaded to GitHub. The web version will work for Public links. For private links, stick to the Local version.

---

## 📜 License
This project is for personal use and educational purposes.
Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [Instaloader](https://instaloader.github.io/).
