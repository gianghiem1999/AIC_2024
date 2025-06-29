# import torch
# import numpy as np
# from PIL import Image
# from transformers import CLIPProcessor, CLIPModel
# import os
# from tqdm import tqdm

# # Tải mô hình CLIP và processor từ Hugging Face
# model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
# processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')

# def image_to_features(image_folder):
#     features = []
#     image_info = []

#     # Tìm tất cả các thư mục con và các file hình ảnh
#     subdirs = [os.path.join(root, d) for root, dirs, files in os.walk(image_folder) for d in dirs]
#     total_files = sum([len(files) for root, dirs, files in os.walk(image_folder) if any(file.lower().endswith(('.png', '.jpg', '.jpeg')) for file in files)])

#     # Khởi tạo thanh tiến trình tổng
#     total_progress = tqdm(total=total_files, desc="Total Progress", position=1)

#     # Duyệt qua tất cả các thư mục con và ảnh trong thư mục 'keyframes'
#     for subdir, dirs, files in os.walk(image_folder):
#         # Khởi tạo thanh tiến trình cho thư mục hiện tại
#         folder_progress = tqdm(total=len(files), desc=f"Processing {os.path.basename(subdir)}", position=0, leave=False)
        
#         for file in files:
#             if file.lower().endswith(('.png', '.jpg', '.jpeg')):
#                 img_path = os.path.join(subdir, file)
#                 img = Image.open(img_path)
                
#                 inputs = processor(images=img, return_tensors="pt")
#                 with torch.no_grad():
#                     image_features = model.get_image_features(**inputs)
                
#                 # Lưu đặc trưng hình ảnh
#                 features.append(image_features.squeeze().numpy())
                
#                 # Lưu thông tin thư mục và tên ảnh (không có phần đuôi mở rộng)
#                 folder_name = os.path.basename(subdir)
#                 image_name = os.path.splitext(file)[0]
#                 image_info.append((folder_name, image_name))
                
#                 # Cập nhật thanh tiến trình thư mục hiện tại
#                 folder_progress.update(1)
                
#                 # Cập nhật thanh tiến trình tổng
#                 total_progress.update(1)
        

#         folder_progress.close()
    
#     total_progress.close()
    
#     return np.array(features), np.array(image_info)

# # Đường dẫn đến thư mục 'keyframes'
# image_folder = 'keyframes'

# # Tạo đặc trưng cho tất cả các hình ảnh và lưu kèm thông tin thư mục và tên ảnh
# image_features, image_info = image_to_features(image_folder)

# # Lưu đặc trưng và thông tin ảnh vào file .npy
# np.save('result/keyframes_features.npy', image_features)
# np.save('result/keyframes_info.npy', image_info)



import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import os
from tqdm import tqdm
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# # Tải mô hình CLIP và processor từ Hugging Face
# model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
# processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')

# Tải mô hình CLIP và processor từ Hugging Face (Sử dụng CUDA nếu có GPU)
device = "cuda" if torch.cuda.is_available() else "cpu"
try:
    model = CLIPModel.from_pretrained('clip_model/').to(device)
    processor = CLIPProcessor.from_pretrained('clip_model/')
except Exception as e:
    logger.error(f"Error loading CLIP model: {e}")
    raise

def image_to_features(image_folder):
    features = []
    image_info = []

    # Tìm tất cả các thư mục con và các file hình ảnh
    subdirs = [os.path.join(root, d) for root, dirs, files in os.walk(image_folder) for d in dirs]
    total_files = sum([len(files) for root, dirs, files in os.walk(image_folder) if any(file.lower().endswith(('.png', '.jpg', '.jpeg')) for file in files)])

    # Khởi tạo thanh tiến trình tổng
    total_progress = tqdm(total=total_files, desc="Total Progress", position=1)

    # Duyệt qua tất cả các thư mục con và ảnh trong thư mục 'keyframes'
    for subdir, dirs, files in os.walk(image_folder):
        # Lọc chỉ các file hình ảnh
        image_files = [file for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg'))]
        total_images_in_folder = len(image_files)
        
        # Khởi tạo thanh tiến trình cho thư mục hiện tại
        folder_progress = tqdm(total=total_images_in_folder, desc=f"Processing {os.path.basename(subdir)}", position=0, leave=False)
        
        successful_images = 0
        
        for file in image_files:
            img_path = os.path.join(subdir, file)
            img = Image.open(img_path)
            
            inputs = processor(images=img, return_tensors="pt")
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
            
            # Lưu đặc trưng hình ảnh
            features.append(image_features.squeeze().numpy())
            
            # Lưu thông tin thư mục và tên ảnh (không có phần đuôi mở rộng)
            folder_name = os.path.basename(subdir)
            image_name = os.path.splitext(file)[0]
            image_info.append((folder_name, image_name))
            
            # Cập nhật thanh tiến trình thư mục hiện tại
            folder_progress.update(1)
            
            # Cập nhật thanh tiến trình tổng
            total_progress.update(1)
            
            # Tăng số lượng ảnh đã xử lý thành công
            successful_images += 1
        
        # Đóng thanh tiến trình thư mục và in ra số ảnh đã xử lý thành công
        folder_progress.close()
        print(f"Processed {successful_images}/{total_images_in_folder} images in folder {os.path.basename(subdir)}.")
    
    total_progress.close()
    
    return np.array(features), np.array(image_info)

# Đường dẫn đến thư mục 'keyframes'
image_folder = 'keyframes'

# Tạo đặc trưng cho tất cả các hình ảnh và lưu kèm thông tin thư mục và tên ảnh
image_features, image_info = image_to_features(image_folder)

# Lưu đặc trưng và thông tin ảnh vào file .npy
np.save('result/keyframes_features.npy', image_features)
np.save('result/keyframes_info.npy', image_info)
