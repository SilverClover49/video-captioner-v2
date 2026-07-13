import os
import sys
import subprocess
import json
import time
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

# Provider config - auto-detect based on available keys
def get_config():
    fireworks_key = os.getenv("FIREWORKS_API_KEY")
    cerebras_key = os.getenv("CEREBRAS_API_KEY")
    
    if fireworks_key:
        return {
            "api_key": fireworks_key,
            "api_url": "https://api.fireworks.ai/inference/v1/chat/completions",
            "vision_model": "accounts/fireworks/models/gemma-4-31b-it",
            "text_model": "accounts/fireworks/models/gemma-4-31b-it",
            "name": "Fireworks (Gemma 4 31B)"
        }
    elif cerebras_key:
        return {
            "api_key": cerebras_key,
            "api_url": "https://api.cerebras.ai/v1/chat/completions",
            "vision_model": "gemma-4-31b",
            "text_model": "gemma-4-31b",
            "name": "Cerebras (Gemma 4 31B)"
        }
    else:
        print("ERROR: No API key found. Set FIREWORKS_API_KEY or CEREBRAS_API_KEY")
        sys.exit(1)

config = get_config()

def call_api(messages, model=None, max_tokens=300):
    if model is None:
        model = config["text_model"]
    headers = {"Authorization": f"Bearer {config['api_key']}", "Content-Type": "application/json"}
    data = {"model": model, "messages": messages, "max_tokens": max_tokens}
    for attempt in range(5):
        try:
            r = requests.post(config["api_url"], headers=headers, json=data, timeout=60)
            resp = r.json()
            if r.status_code == 429:
                wait = min(30, 2 ** attempt)
                print(f"    Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            if "choices" in resp and resp["choices"][0]["message"]["content"]:
                return resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"    Retry {attempt+1}: {e}")
        time.sleep(2)
    return ""

def get_video_duration(video_path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def extract_frames(video_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    duration = get_video_duration(video_path)
    print(f"  Duration: {duration:.1f}s")
    
    if duration <= 30:
        count = 9
    elif duration <= 60:
        count = 12
    else:
        count = 15
    
    frames = []
    for i in range(count):
        pos = i / (count - 1) if count > 1 else 0
        timestamp = min(pos * duration, duration - 0.1)
        name = f"F{i+1:02d}"
        output_file = os.path.join(output_dir, f"{name}.jpg")
        cmd = ["ffmpeg", "-ss", str(timestamp), "-i", video_path, "-frames:v", "1", "-q:v", "2", output_file, "-y"]
        subprocess.run(cmd, capture_output=True)
        frames.append({"name": name, "path": output_file, "timestamp": timestamp})
    
    print(f"  Extracted {len(frames)} frames")
    return frames

def analyze_frame(frame_path, frame_name):
    with open(frame_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    
    response = call_api([{
        "role": "user",
        "content": [
            {"type": "text", "text": f"Describe this video frame in detail. What objects, colors, setting, people, actions, and mood do you see? Be specific. Frame: {frame_name}"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}}
        ]
    }, {"role": "assistant", "content": ""}], model=config["vision_model"], max_tokens=200)
    return response

def compare_frames(desc1, desc2):
    response = call_api([{
        "role": "user",
        "content": f"Are these descriptions of the same or very similar scenes? Answer YES or NO only.\n\nDesc 1: {desc1}\n\nDesc 2: {desc2}"
    }], max_tokens=10)
    return "YES" in response.upper()

def create_thinking_board(frames, descriptions, comparisons):
    board = "VIDEO SCENE ANALYSIS\n" + "=" * 50 + "\n\n"
    board += "FRAME DESCRIPTIONS:\n" + "-" * 50 + "\n"
    for frame in frames:
        name = frame["name"]
        desc = descriptions.get(name, "No description")
        board += f"\n[{name}] ({frame['timestamp']:.1f}s):\n{desc}\n"
    board += "\nFRAME COMPARISONS:\n" + "-" * 50 + "\n"
    for comp in comparisons:
        status = "SIMILAR" if comp["similar"] else "DIFFERENT"
        board += f"{comp['from']} -> {comp['to']}: {status}\n"
    board += "\nSCENE SUMMARY:\n" + "-" * 50 + "\n"
    for frame in frames:
        desc = descriptions.get(frame["name"], "")
        board += f"[{frame['name']}]: {desc[:200]}\n"
    return board

STYLE_PROMPTS = {
    "formal": "Write a formal, professional 2-sentence caption describing this scene.",
    "sarcastic": "Write a sarcastic 2-sentence caption about this scene with dry humor.",
    "humorous_tech": "Write a funny 2-sentence caption using developer/tech metaphors.",
    "humorous_nontech": "Write a funny 2-sentence caption for anyone using everyday humor.",
}

def generate_captions(thinking_board):
    captions = {}
    for style, prompt in STYLE_PROMPTS.items():
        print(f"  {style}...")
        for attempt in range(3):
            response = call_api([{
                "role": "user",
                "content": f"{prompt}\n\nScene description:\n{thinking_board[:1500]}"
            }], max_tokens=200)
            if response and len(response) > 20:
                captions[style] = response
                print(f"    {response[:80]}...")
                break
            time.sleep(1)
        else:
            # Fallback: use simpler prompt
            response = call_api([{
                "role": "user",
                "content": f"Write a {style} caption about: {thinking_board[:500]}"
            }], max_tokens=200)
            captions[style] = response if response else f"[{style}] Scene analysis available in thinking board."
            print(f"    Fallback: {captions[style][:80]}...")
    return captions

def score_caption(caption, style, thinking_board):
    response = call_api([{
        "role": "user",
        "content": f"Rate this caption 1-10 for {style} style quality. Output ONLY a number.\n\nCaption: {caption[:300]}"
    }], max_tokens=5)
    try:
        return int(''.join(filter(str.isdigit, response[:3])))
    except:
        return 5

def rewrite_caption(caption, style, thinking_board):
    prompt = STYLE_PROMPTS[style]
    response = call_api([{
        "role": "user",
        "content": f"Rewrite this caption to be better.\n\nOriginal: {caption}\n\nScene: {thinking_board[:500]}\n\n{prompt}"
    }], max_tokens=200)
    return response if response and len(response) > 20 else caption

def process_video(video_path):
    print(f"\n{'='*60}")
    print(f"Processing: {os.path.basename(video_path)}")
    print(f"Provider: {config['name']}")
    print(f"{'='*60}")
    
    start = time.time()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    frames_dir = os.path.join(base_dir, "frames", video_name)
    thinking_file = os.path.join(base_dir, f"thinking_board_{video_name}.md")
    
    print("\n[STAGE 1] Extracting frames...")
    frames = extract_frames(video_path, frames_dir)
    
    print("\n[STAGE 2] Analyzing frames...")
    descriptions = {}
    for frame in frames:
        print(f"  {frame['name']}...")
        desc = analyze_frame(frame["path"], frame["name"])
        descriptions[frame["name"]] = desc
        print(f"    {desc[:80]}...")
    
    print("\n[STAGE 3] Comparing frames...")
    comparisons = []
    for i in range(len(frames) - 1):
        n1, n2 = frames[i]["name"], frames[i+1]["name"]
        similar = compare_frames(descriptions[n1], descriptions[n2])
        comparisons.append({"from": n1, "to": n2, "similar": similar})
        print(f"  {n1} -> {n2}: {'SIMILAR' if similar else 'DIFFERENT'}")
    
    thinking_board = create_thinking_board(frames, descriptions, comparisons)
    with open(thinking_file, "w", encoding="utf-8") as f:
        f.write(thinking_board)
    
    print("\n[STAGE 4] Generating captions...")
    captions = generate_captions(thinking_board)
    
    print("\n[STAGE 5] Scoring and verifying...")
    for style in list(captions.keys()):
        score = score_caption(captions[style], style, thinking_board)
        print(f"  {style}: {score}/10")
        if score < 8:
            print(f"  Rewriting {style}...")
            captions[style] = rewrite_caption(captions[style], style, thinking_board)
            new_score = score_caption(captions[style], style, thinking_board)
            print(f"  {style} improved: {new_score}/10")
    
    elapsed = round(time.time() - start, 1)
    print(f"\n  Done in {elapsed}s")
    
    return {
        "video": os.path.basename(video_path),
        "duration": get_video_duration(video_path),
        "frames": len(frames),
        "captions": captions,
        "thinking_board": thinking_file,
        "processing_time": elapsed
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python captioner.py <video_file>")
        sys.exit(1)
    video_file = sys.argv[1]
    if not os.path.exists(video_file):
        print(f"File not found: {video_file}")
        sys.exit(1)
    
    result = process_video(video_file)
    
    output_dir = "/app/output" if os.path.exists("/app") else os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "output.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("DONE")
    print(f"{'='*60}")
