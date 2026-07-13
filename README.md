# Video Captioner V2 - Vision-Based

5-stage AI pipeline that generates captions for SILENT videos by analyzing visual content with Gemma 4 31B vision model.

## How It Works

1. Extract 9 key frames from video
2. Analyze each frame with Gemma 4 vision
3. Compare adjacent frames for scene changes
4. Build thinking board with scene analysis
5. Generate 4 caption styles (formal, sarcastic, tech, nontech)

## Quick Start

```bash
pip install -r requirements.txt
python captioner.py video.mp4
```

## Docker

```bash
docker build -t video-captioner .
docker run --env-file .env video-captioner video.mp4
```

## Tech Stack

- **Vision**: Gemma 4 31B via Cerebras API
- **Captioning**: Gemma 4 31B via Cerebras API
- **Frame Extraction**: FFmpeg
- **Container**: Docker

## Output

- `frames/` - Extracted video frames
- `thinking_board.md` - Scene analysis
- `output/output.json` - Final captions in 4 styles
