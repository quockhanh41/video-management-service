from moviepy.editor import ImageClip, VideoFileClip, concatenate_videoclips
import os
import random
from service.vid_transition_func import create_transition

def create_video_from_image(image_path, output_path, duration=5, fps=30):
    """
    Tạo video đơn giản từ một tấm ảnh
    
    Args:
        image_path (str): Đường dẫn đến file ảnh
        output_path (str): Đường dẫn để lưu video
        duration (int): Thời lượng video (giây)
        fps (int): Số khung hình trên giây
    """
    try:
        # Tạo clip từ ảnh
        clip = ImageClip(image_path)
        
        # Đặt thời lượng cho clip
        clip = clip.set_duration(duration)
        
        # Đặt FPS
        clip = clip.set_fps(fps)
        
        # Xuất video
        clip.write_videofile(
            output_path,
            fps=fps,
            codec='libx264',
            audio=False
        )
        
        print(f"Đã tạo video thành công: {output_path}")
        return clip
        
    except Exception as e:
        print(f"Lỗi khi tạo video: {str(e)}")
        return None
    finally:
        if 'clip' in locals():
            clip.close()

def get_random_transition():
    """
    Lấy ngẫu nhiên một loại transition
    """
    transitions = [
        "rotation", "rotation_inv", "zoom_in", "zoom_out",
        "translation", "translation_inv", "long_translation", "long_translation_inv"
    ]
    return random.choice(transitions)

def main():
    # Tạo thư mục output nếu chưa tồn tại
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Đường dẫn đến ảnh (thay đổi theo đường dẫn thực tế của bạn)
    image_paths = [
        "E:\\TKPM\\Video\\tests\\image1.png",
        "E:\\TKPM\\Video\\tests\\image2.png",
        "E:\\TKPM\\Video\\tests\\image3.png",
        "E:\\TKPM\\Video\\tests\\image4.png",
        "E:\\TKPM\\Video\\tests\\image5.png"
    ]
    
    # Tạo video từ các ảnh
    clips = []
    for i, image_path in enumerate(image_paths):
        output_path = os.path.join(output_dir, f"video{i+1}.mp4")
        print(f"Đang tạo video {i+1}...")
        clip = create_video_from_image(image_path, output_path)
        if clip:
            clips.append(clip)
    
    if len(clips) < 2:
        print("Không đủ video để tạo transition")
        return
    
    # Tạo transition giữa các video
    final_clips = []
    for i in range(len(clips)):
        if i > 0:  # Thêm transition cho tất cả các clip trừ clip đầu tiên
            try:
                # Lấy ngẫu nhiên một loại transition
                transition_type = get_random_transition()
                print(f"Đang tạo transition {transition_type} giữa video {i} và {i+1}...")
                
                # Tạo transition video
                transition_video = create_transition(
                    input_videos=[clips[i-1], clips[i]],
                    temp_path=output_dir,
                    animation=transition_type,
                    num_frames=30,
                    max_brightness=1.5
                )
                
                # Tạo clip transition
                transition_clip = VideoFileClip(transition_video)
                final_clips.append(transition_clip)
                
            except Exception as e:
                print(f"Lỗi khi tạo transition: {str(e)}")
                # Nếu có lỗi, bỏ qua transition và tiếp tục với clip tiếp theo
                continue
        
        # Thêm clip hiện tại vào danh sách
        final_clips.append(clips[i])
    
    # Kết hợp tất cả các clip
    print("Đang ghép các video...")
    final_clip = concatenate_videoclips(final_clips, method="compose")
    
    # Xuất video cuối cùng
    final_output = os.path.join(output_dir, "final_video.mp4")
    final_clip.write_videofile(
        final_output,
        fps=30,
        codec='libx264',
        audio=False
    )
    
    print(f"Đã tạo video cuối cùng thành công: {final_output}")
    
    # Giải phóng tài nguyên
    final_clip.close()
    for clip in clips:
        clip.close()

if __name__ == "__main__":
    main() 