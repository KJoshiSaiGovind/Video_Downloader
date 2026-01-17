import yt_dlp
import os
import instaloader
import http.cookiejar
import re
import shutil

def get_download_options(output_path, progress_hook=None, use_cookies=False, browser="chrome"):
    """
    Returns default options for yt-dlp.
    """
    opts = {
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'restrictfilenames': True,  # Avoid special characters
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': False,
    }
    
    # Check for local ffmpeg.exe (Windows) or system ffmpeg (Linux/Web)
    if os.path.exists("ffmpeg.exe"):
        opts['ffmpeg_location'] = os.getcwd() # Explicit local path
    elif shutil.which("ffmpeg"):
        pass # It's in the PATH (Cloud/Linux), yt-dlp finds it automatically

    # Prioritize cookies.txt if it exists (avoids browser lock issues)
    if os.path.exists("cookies.txt"):
        opts['cookiefile'] = "cookies.txt"
    elif use_cookies:
        # Access cookies from the specified browser
        opts['cookiesfrombrowser'] = (browser,)

    if progress_hook:
        opts['progress_hooks'] = [progress_hook]
    return opts

def download_media(url, output_path, resolution="Best", progress_hook=None, use_cookies=False, browser="chrome"):
    """
    Downloads media from the provided URL using yt-dlp.
    """
    
    # Configure format selection
    # For images (Instagram/X posts), 'bestvideo' will fail. 
    # We use a broad selector that allows fallback.
    if resolution == "1080p":
        format_str = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
    elif resolution == "720p":
        format_str = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
    elif resolution == "Audio Only":
        format_str = 'bestaudio/best'
    else:
        # "Best" / Auto
        format_str = 'bestvideo+bestaudio/best'

    ydl_opts = get_download_options(output_path, progress_hook, use_cookies, browser)
    ydl_opts['format'] = format_str
    
    # Add post-processors if audio only
    if resolution == "Audio Only":
         ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First extract info to get title/thumbnail without downloading
            info = ydl.extract_info(url, download=False)
            
            # Now download
            ydl.download([url])
            
            # Construct the expected filename
            filename = ydl.prepare_filename(info)
            
            # Adjust extension for audio conversion if needed
            if resolution == "Audio Only":
                base, _ = os.path.splitext(filename)
                filename = base + ".mp3"
                
            return {
                "success": True,
                "title": info.get('title', 'Media'),
                "thumbnail": info.get('thumbnail'),
                "filepath": filename,
                "extractor": info.get('extractor_key')
            }
            
    except Exception as e:
        error_msg = str(e)
        
        # INSTAGRAM FALLBACK: If yt-dlp fails on images ("No video formats found"), use Instaloader
        if "instagram" in error_msg.lower() and "no video formats found" in error_msg.lower():
            print("Detected Instagram Image/Post (not video). Switching to Instaloader...")
            return download_instagram_fallback(url, output_path, use_cookies=use_cookies)

        # Check for FFmpeg error and retry with simpler format
        if "ffmpeg is not installed" in error_msg.lower() or "merging of multiple formats" in error_msg.lower() or "empty" in error_msg.lower() or "fragment" in error_msg.lower():
            print("FFmpeg not found or fragment error. Retrying with progressive (single file) formats...")
            try:
                # 18 = 360p MP4 (Progressive), 22 = 720p MP4 (Progressive - rare), 
                # best[ext=mp4] is generic fallback.
                ydl_opts['format'] = '18/22/best[ext=mp4]'
                ydl_opts['outtmpl'] = os.path.join(output_path, '%(id)s.%(ext)s')
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    ydl.download([url])
                    
                     # Recalculate filename
                    filename = ydl.prepare_filename(info)
                    
                    # Verify file exists
                    if not os.path.exists(filename):
                        base_name = os.path.join(output_path, info['id'])
                        # Add image extensions here to fix the "No such file" error for posts
                        for ext in ['mp4', 'webm', 'mkv', '3gp', 'jpg', 'jpeg', 'png', 'webp']:
                            if os.path.exists(f"{base_name}.{ext}"):
                                filename = f"{base_name}.{ext}"
                                break
                    
                    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                         raise Exception("File is empty after progressive download attempt.")

                    return {
                        "success": True,
                        "title": info.get('title', 'Media'),
                        "thumbnail": info.get('thumbnail'),
                        "filepath": filename,
                        "extractor": info.get('extractor_key'),
                        "warning": "Downloaded basic quality (Progressive MP4) due to missing FFmpeg"
                    }
            except Exception as retry_e:
                 print(f"Retry failed error: {retry_e}")
                 return {
                    "success": False,
                    "error": f"Retry failed: {str(retry_e)}"
                }
        
        return {
            "success": False,
            "error": error_msg
        }

def get_media_info(url, use_cookies=False, browser="chrome"):
    """
    Fetches metadata for the URL without downloading.
    """
    # Reuse get_download_options to ensure consistent config (cookies, ffmpeg, etc.)
    # We create a dummy path "." since we aren't downloading yet
    ydl_opts = get_download_options(".", None, use_cookies, browser)
    
    # Force quiet mode for metadata fetch
    ydl_opts.update({
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True
    })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "success": True,
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "platform": info.get('extractor_key')
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

def download_instagram_fallback(url, output_path, use_cookies=False):
    """
    Fallback for Instagram Images using Instaloader.
    """
    try:
        # Extract shortcode from URL
        # Format: instagram.com/p/SHORTCODE/ or /reels/SHORTCODE/
        match = re.search(r'instagram\.com/(?:p|reel|tv)/([^/?#&]+)', url)
        if not match:
            return {"success": False, "error": "Could not parse Instagram shortcode."}
        
        shortcode = match.group(1)
        
        # Initialize Instaloader
        L = instaloader.Instaloader(download_video_thumbnails=False,
                                    save_metadata=False,
                                    compress_json=False,
                                    dirname_pattern=output_path,
                                    filename_pattern='{date:%Y-%m-%d}_{shortcode}')

        # Load cookies if available
        # We prioritize cookies.txt in the current directory
        if os.path.exists("cookies.txt"):
            cookie_jar = http.cookiejar.MozillaCookieJar("cookies.txt")
            cookie_jar.load()
            L.context._session.cookies = cookie_jar
        
        # Load Post
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        # Download
        # Instaloader downloads to a folder named by 'target' (dirname_pattern)
        # We want to download into output_path directly or a subfolder. 
        # Instaloader logic: if target is specified, it creates that folder.
        # But we passed `output_path` as `dirname_pattern`? No, `dirname_pattern` is for --dirname-pattern.
        # Actually, L.download_post(post, target=...) uses 'target' as a directory name.
        # We want to flatten it or move it.
        
        # Let's use a temporary target name to find the file easily
        temp_target = "insta_temp"
        L.download_post(post, target=temp_target)
        
        # Find the downloaded file in temp_target
        downloaded_file = None
        temp_dir = os.path.join(os.getcwd(), temp_target)
        
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                if file.endswith(('.jpg', '.png', '.mp4', '.webp')):
                    downloaded_file = os.path.join(temp_dir, file)
                    break 
                    
            # Move to output_path
            if downloaded_file:
                final_filename = os.path.join(output_path, os.path.basename(downloaded_file))
                # Ensure output_path exists
                if not os.path.exists(output_path):
                    os.makedirs(output_path)
                    
                if os.path.exists(final_filename):
                    os.remove(final_filename)
                    
                os.rename(downloaded_file, final_filename)
                
                # Cleanup temp dir
                try:
                    for f in os.listdir(temp_dir):
                        os.remove(os.path.join(temp_dir, f))
                    os.rmdir(temp_dir)
                except:
                    pass
                    
                return {
                    "success": True,
                    "title": f"Instagram Post {shortcode}",
                    "thumbnail": None, # Local file
                    "filepath": final_filename,
                    "extractor": "instaloader",
                    "warning": "Downloaded using Instaloader (Image Fallback)"
                }
        
        return {"success": False, "error": "Instaloader finished but no file found."}

    except Exception as e:
        return {"success": False, "error": f"Instaloader Fallback failed: {str(e)}"}
