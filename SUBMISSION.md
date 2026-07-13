# Lablab.ai Submission Text

## Short Description (255 chars max)
Vision-based video captioning pipeline using Gemma 4 31B. Analyzes video frames, builds scene understanding, generates 4 caption styles with automatic quality scoring and re-generation.

## Long Description (1000+ words)

Video Captioner V2 is a 5-stage AI pipeline that generates accurate, multi-style captions for silent videos by analyzing visual content with Gemma 4 31B vision model.

**The Problem:**
Most video captioning tools rely on audio transcription, which fails for silent videos. The AMD Hackathon Track 2 requires describing what's IN the video visually, not what's said.

**Our Solution:**
A vision-first pipeline that extracts key frames, analyzes them with Gemma 4 31B vision capabilities, and generates 4 distinct caption styles with automatic quality verification.

**How It Works:**

Stage 1: Adaptive Frame Extraction
- Analyzes video duration (6s to 2min)
- Extracts 9-15 key frames at strategic intervals
- Covers opening, middle, and closing scenes

Stage 2: Vision Analysis
- Each frame analyzed with Gemma 4 31B vision model
- Describes objects, colors, setting, people, actions, mood
- Builds comprehensive scene understanding

Stage 3: Frame Comparison
- Compares adjacent frames for scene changes
- Identifies similar vs different moments
- Creates temporal flow understanding

Stage 4: Thinking Board
- Creates detailed scene analysis document
- Records all frame descriptions and comparisons
- Serves as context for caption generation

Stage 5: Caption Generation + Verification
- Generates 4 caption styles from thinking board
- Scores each caption 1-10
- Rewrites captions scoring below 8
- Ensures quality output

**Caption Styles:**
- Formal: Professional, descriptive, factual
- Sarcastic: Witty, dry humor, ironic
- Humorous-Tech: Developer metaphors, coding humor
- Humorous-NonTech: Everyday humor, relatable

**Results:**
- 9 frames extracted for 30-second videos
- 97 seconds average processing time
- 4 high-quality captions per video
- Automatic quality scoring and re-generation

**Tech Stack:**
- Gemma 4 31B (Cerebras API) - Vision and captioning
- FFmpeg - Frame extraction
- Python - Pipeline orchestration
- Docker - Containerized deployment
