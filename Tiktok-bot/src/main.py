import os
import time
import pickle
import json
import openai
import nltk
import random
from collections import Counter
from gtts import gTTS
import moviepy.editor as mp
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.fx import fadein, resize
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import tkinter as tk
from tkinter import messagebox, simpledialog

# Handle stopwords correctly
try:
    from nltk.corpus import stopwords
    _ = stopwords.words('english')  # trigger check
except LookupError:
    nltk.download('stopwords')
    from nltk.corpus import stopwords

# -----------------------------
# CONFIGURATION
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_FOLDER = os.path.join(BASE_DIR, "backgrounds")
COOKIES_FILE = os.path.join(BASE_DIR, "tiktok_cookies.pkl")
TIKTOK_UPLOAD_URL = "https://www.tiktok.com/upload?lang=en"
VIDEO_OUTPUT = os.path.join(BASE_DIR, "tiktok_video.mp4")
AUDIO_OUTPUT = os.path.join(BASE_DIR, "voice.mp3")
LOG_FILE = os.path.join(BASE_DIR, "tiktok_bot.jsonl")

# Integrate your GPT API key here
openai.api_key = "your-real-openai-api-key"

# -----------------------------
# LOGGER SETUP
# -----------------------------
def log(msg):
    entry = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "message": msg}
    print(msg)
    with open(LOG_FILE, 'a') as f:
        json.dump(entry, f)
        f.write('\n')

# -----------------------------
# AI CONTENT GENERATION
# -----------------------------
def generate_ai_caption(script_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generate a short, engaging TikTok caption for the given script."},
                {"role": "user", "content": script_text}
            ]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log(f"[!] AI Caption Error: {e}")
        return "🔥 Watch till the end! #funny"

def generate_hashtags(script_text):
    words = [word.lower() for word in script_text.split() if word.isalpha()]
    filtered_words = [w for w in words if w not in stopwords.words('english')]
    common = Counter(filtered_words).most_common(3)
    return [f"#{word}" for word, _ in common]

def analyze_tiktok_trends(script_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Suggest a viral TikTok trend related to the given script."},
                {"role": "user", "content": script_text}
            ]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log(f"[!] Trend Analysis Error: {e}")
        return "Try using a funny reaction or duet!"

def generate_ai_background():
    colors = [(255, 255, 0), (0, 255, 255), (255, 0, 255), (0, 0, 0), (128, 0, 128)]
    return mp.ColorClip(size=(720, 1280), color=random.choice(colors), duration=5)

def generate_ai_music():
    return None  # Placeholder for AI-generated music logic

# -----------------------------
# VIDEO CREATOR
# -----------------------------
def generate_video(script_text):
    ai_caption = generate_ai_caption(script_text)
    hashtags = generate_hashtags(script_text)
    trend_suggestion = analyze_tiktok_trends(script_text)

    try:
        tts = gTTS(text=script_text, lang='en')
        tts.save(AUDIO_OUTPUT)
    except Exception as e:
        log(f"[!] Text-to-speech error: {e}")
        return

    clip = generate_ai_background()

    try:
        audio_clip = mp.AudioFileClip(AUDIO_OUTPUT)
    except Exception as e:
        log(f"[!] Error loading audio: {e}")
        return

    clip = clip.set_audio(audio_clip).set_duration(audio_clip.duration)

    caption_clip = mp.TextClip(ai_caption, font="Arial-Bold", fontsize=40, color="yellow").set_position(("center", "top")).set_duration(5)
    hashtag_clip = mp.TextClip(" ".join(hashtags), font="Arial-Bold", fontsize=35, color="blue").set_position(("center", "bottom")).set_duration(5)
    trend_clip = mp.TextClip(trend_suggestion, font="Arial-Bold", fontsize=30, color="green").set_position(("center", "middle")).set_duration(5)

    final = mp.CompositeVideoClip([clip, caption_clip, hashtag_clip, trend_clip])

    try:
        final.write_videofile(VIDEO_OUTPUT, fps=24, codec="libx264", audio_codec="aac")
        log("[+] Video created successfully!")
    except Exception as e:
        log(f"[!] Video export error: {e}")

# -----------------------------
# TIKTOK AUTO-UPLOAD
# -----------------------------
def setup_browser():
    options = Options()
    options.add_argument("--user-data-dir=selenium")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    try:
        return webdriver.Chrome(options=options)
    except Exception as e:
        log(f"[!] Chrome WebDriver error: {e}")
        raise

def save_cookies(driver):
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)

def load_cookies(driver):
    with open(COOKIES_FILE, 'rb') as f:
        for cookie in pickle.load(f):
            driver.add_cookie(cookie)

def upload_to_tiktok():
    try:
        driver = setup_browser()
    except:
        return

    driver.get(TIKTOK_UPLOAD_URL)
    time.sleep(5)

    if os.path.exists(COOKIES_FILE):
        log("[+] Loading saved cookies...")
        driver.delete_all_cookies()
        load_cookies(driver)
        driver.get(TIKTOK_UPLOAD_URL)
        time.sleep(5)
    else:
        log("[!] No cookies found. Please log in manually.")
        input("Press ENTER after login is complete in the browser...")
        save_cookies(driver)
        log("[+] Login session saved.")

    try:
        upload_input = driver.find_element(By.XPATH, '//input[@type="file"]')
        upload_input.send_keys(os.path.abspath(VIDEO_OUTPUT))
        log("[+] Uploading video...")
        time.sleep(15)

        post_button = driver.find_element(By.XPATH, '//button[contains(., "Post")]')
        driver.execute_script("arguments[0].click();", post_button)
        log("[+] Video successfully posted!")
    except Exception as e:
        log(f"[!] Upload failed: {e}")
    finally:
        driver.quit()

# -----------------------------
# GUI MENU
# -----------------------------
def run_gui():
    def on_select(choice):
        nonlocal script_text
        if choice == "Generate script":
            script_text = simpledialog.askstring("Script", "Enter your script text:")
            log(f"[+] Script input: {script_text}")
        elif choice == "Create video":
            if script_text:
                generate_video(script_text)
            else:
                messagebox.showwarning("Warning", "No script provided.")
        elif choice == "Upload video":
            upload_to_tiktok()
        elif choice == "Full process":
            if not script_text:
                script_text = simpledialog.askstring("Script", "Enter your script text:")
            generate_video(script_text)
            upload_to_tiktok()
        elif choice == "Exit":
            root.quit()

    script_text = ""
    root = tk.Tk()
    root.title("TikTok AI Video Bot")
    root.geometry("300x300")

    options = ["Generate script", "Create video", "Upload video", "Full process", "Exit"]
    for opt in options:
        btn = tk.Button(root, text=opt, width=25, height=2, command=lambda c=opt: on_select(c))
        btn.pack(pady=5)

    root.mainloop()

# -----------------------------
# MAIN EXECUTION
# -----------------------------
if __name__ == "__main__":
    run_gui()
