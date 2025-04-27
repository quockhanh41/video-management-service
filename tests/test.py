import os
import subprocess
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, VideoFileClip

# Input parameters
# 
TEXT_FOR_SPEECH = """Thank you for joining us on this floral journey. May these beautiful blooms bring joy to your day!"""
IMAGES = [r"E:\TKPM\Video\image1.jpg", r"E:\TKPM\Video\image2.jpg", r"E:\TKPM\Video\image3.jpg"]  # List of image paths
OUTPUT_VIDEO = "output_video.mp4"
TTS_AUDIO = "audio5.mp3"
TEMP_VIDEO = "temp_video.mp4"

# Step 1: Generate TTS audio
def generate_tts_audio(text, output_file):
    tts = gTTS(text=text, lang="en", slow=False)
    tts.save(output_file)
    return output_file

# Step 2: Get audio duration
def get_audio_duration(audio_file):
    audio = AudioFileClip(audio_file)
    duration = audio.duration
    audio.close()
    return duration

# Step 3: Create video from images with MoviePy
def create_image_video(images, audio_duration, output_file):
    duration_per_image = audio_duration / len(images)
    clips = []
    for i, img in enumerate(images):
        clip = ImageClip(img).set_duration(duration_per_image).resize(height=1080).on_color(
            size=(1920, 1080), color=(0,0,0), pos='center'
        )
        # Thêm hiệu ứng crossfade nếu không phải ảnh đầu tiên
        if i > 0:
            clip = clip.crossfadein(0.5)
        clips.append(clip)
    # Nối các clip lại với nhau
    video = concatenate_videoclips(clips, method="compose")
    video.write_videofile(output_file, fps=24, codec="libx264", audio=False)
    for clip in clips:
        clip.close()
    video.close()

# Step 4: Combine video and audio with MoviePy
def combine_video_audio(video_file, audio_file, output_file):
    video = VideoFileClip(video_file)
    audio = AudioFileClip(audio_file)
    final = video.set_audio(audio).set_duration(min(video.duration, audio.duration))
    final.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")
    video.close()
    audio.close()
    final.close()

# Main execution
def main():
    # Generate TTS audio
    generate_tts_audio(TEXT_FOR_SPEECH, TTS_AUDIO)
    
    # Get audio duration
    audio_duration = get_audio_duration(TTS_AUDIO)
    
    # # Create video from images
    # create_image_video(IMAGES, audio_duration, TEMP_VIDEO)
    
    # # Combine video and audio
    # combine_video_audio(TEMP_VIDEO, TTS_AUDIO, OUTPUT_VIDEO)
    
    # print(f"Video created successfully at: {OUTPUT_VIDEO}")
    
    # # Clean up temporary files
    # os.remove(TTS_AUDIO)
    # os.remove(TEMP_VIDEO)

if __name__ == "__main__":
    main()