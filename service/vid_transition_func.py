import pathlib
import tempfile
import os
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from service.vid_transition import (
    Animations, AnimationActions, AnimationImages, DataHandler,
    NUM_FRAMES, MAX_ROTATION, MAX_DISTORTION, MAX_BLUR, 
    MAX_BRIGHTNESS, MAX_ZOOM
)
from moviepy.editor import VideoFileClip, concatenate_videoclips
def create_transition(
    input_videos: list,
    temp_path: str,
    output: str = "",
    animation: str = "rotation",
    num_frames: int = NUM_FRAMES,
    max_rotation: float = MAX_ROTATION,
    max_distortion: float = MAX_DISTORTION,
    max_blur: float = MAX_BLUR,
    max_brightness: float = MAX_BRIGHTNESS,
    max_zoom: float = MAX_ZOOM,
    debug: bool = False,
    art: bool = True,
    remove_original: bool = False,
    merge_phases: bool = True
):
    """
    Tạo hiệu ứng chuyển cảnh giữa các video
    
    Args:
        input_videos (list): Danh sách đường dẫn đến các video đầu vào
        temp_path (str): Đường dẫn đến thư mục tạm để lưu video kết quả
        output (str): Đường dẫn đến video đầu ra (nếu không có sẽ tạo tự động)
        animation (str): Loại hiệu ứng chuyển cảnh
        num_frames (int): Số khung hình cho mỗi pha chuyển cảnh
        max_rotation (float): Góc xoay tối đa
        max_distortion (float): Độ biến dạng tối đa
        max_blur (float): Độ mờ tối đa
        max_brightness (float): Độ sáng tối đa
        max_zoom (float): Độ phóng to tối đa
        debug (bool): Chế độ debug
        art (bool): Hiển thị ASCII art
        remove_original (bool): Xóa file gốc sau khi xử lý
        merge_phases (bool): Gộp các pha lại với nhau
        
    Returns:
        tuple: (str, list) - Đường dẫn đến video đã được tạo và danh sách các file transition
    """
    # Kiểm tra số lượng video đầu vào
    if len(input_videos) < 2:
        raise ValueError("Cần ít nhất 2 video đầu vào")
    
    # Chuyển đổi đường dẫn thành Path objects
    input_videos = [pathlib.Path(video) for video in input_videos]
    output = pathlib.Path(output) if output else None
    
    # Danh sách các file transition được tạo ra
    transition_files = []
    
    # Tạo thư mục tạm cho quá trình xử lý
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = pathlib.Path(tmp_dir)
        
        # Khởi tạo DataHandler
        data_handler = DataHandler()
        
        # Tạo một đối tượng args giả để truyền vào verify_arguments
        class Args:
            def __init__(self):
                self.input = input_videos
                self.output = str(output) if output else ""
                self.temp_path = temp_path  # Thêm temp_path vào args
                self.num_frames = num_frames
                self.animation = animation
                self.max_rotation = max_rotation
                self.max_distortion = max_distortion
                self.max_blur = max_blur
                self.max_brightness = max_brightness
                self.max_zoom = max_zoom
                self.debug = debug
                self.art = art
                self.remove = remove_original
                self.merge = merge_phases
        
        args = Args()
        
        # Xác minh các tham số
        if not data_handler.verify_arguments(args, tmp_path):
            raise ValueError("Không thể xác minh các tham số đầu vào")
        
        # Trích xuất khung hình từ video đầu tiên
        if not data_handler._extract_phase1_images(num_frames):
            raise ValueError("Không thể trích xuất khung hình từ video đầu tiên")
        
        # Trích xuất khung hình từ video thứ hai
        if not data_handler._extract_phase2_images(num_frames):
            raise ValueError("Không thể trích xuất khung hình từ video thứ hai")
        
        # Tạo hiệu ứng chuyển cảnh
        animation_actions = AnimationActions(
            max_zoom, max_brightness, max_rotation, max_blur, 
            max_distortion, num_frames
        )
        
        actions1, actions2 = animation_actions.get_actions_values(
            getattr(Animations, animation)
        )
        
        # Tạo các khung hình chuyển cảnh
        final_phase_folder = AnimationImages.make_transition(
            tmp_path,
            data_handler.phase1_images,
            data_handler.phase2_images,
            actions1,
            actions2,
            debug
        )
        
        # Chuyển đổi khung hình thành video
        if not data_handler.final_images_to_video(final_phase_folder):
            raise ValueError("Không thể tạo video từ các khung hình")
            
        if merge_phases:
            if not data_handler.merge_video_chunks():
                raise ValueError("Không thể gộp các pha video")
            # Thêm các file transition vào danh sách
            transition_files.extend([
                str(data_handler.phase1_vid),
                str(data_handler.phase2_vid),
                str(data_handler.merged_vid)
            ])
            return str(data_handler.merged_vid), transition_files
        else:
            # Thêm các file transition vào danh sách
            transition_files.extend([
                str(data_handler.phase1_vid),
                str(data_handler.phase2_vid)
            ])
            return str(data_handler.phase1_vid), str(data_handler.phase2_vid), transition_files

# Ví dụ sử dụng
if __name__ == "__main__":
    # Ví dụ sử dụng hàm
    try:
        output, transition_files = create_transition(
            input_videos=["E:/TKPM/video-editing-py-script/Input/video1.mp4", "E:/TKPM/video-editing-py-script/Input/video2.mp4"],
            animation="zoom_out",
            temp_path="temp",
            num_frames=30,
            max_brightness=1.5
        )
        
        # output = concatenate_videoclips([VideoFileClip("E:/TKPM/video-editing-py-script/Input/video1.mp4"), VideoFileClip("E:/TKPM/video-editing-py-script/Output/output_merged.mp4"), VideoFileClip("E:/TKPM/video-editing-py-script/Input/video2.mp4")])
        # output.write_videofile("E:/TKPM/video-editing-py-script/Output/output_merged_final.mp4")
        print(f"Video đã được tạo: {output}")
        print(f"Các file transition được tạo: {transition_files}")
    except Exception as e:
        print(f"Lỗi: {e}") 