import os
import numpy as np
import torch
import pandas as pd
from transformers import CLIPModel, CLIPProcessor
from sklearn.metrics.pairwise import cosine_similarity
import socketio
import logging

#Khởi tạo kiểu dữ liệu để lưu thông tin gửi cho app
result_json = {}

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server SocketIO
sio = socketio.Server()
app = socketio.WSGIApp(sio)

# Load image features và thông tin từ file .npy
try:
    image_features = np.load('result/keyframes_features.npy')
    image_info = np.load('result/keyframes_info.npy', allow_pickle=True)
except Exception as e:
    logger.error(f"Error loading .npy files: {e}")
    raise

image_folder = "keyframes/"
map_folder = "map/"

# Tải mô hình CLIP và processor từ Hugging Face (Sử dụng CUDA nếu có GPU)
device = "cuda" if torch.cuda.is_available() else "cpu"
try:
    model = CLIPModel.from_pretrained('clip_model/').to(device)
    processor = CLIPProcessor.from_pretrained('clip_model/')
except Exception as e:
    logger.error(f"Error loading CLIP model: {e}")
    raise

def text_to_features(text_list):
    """Chuyển đổi danh sách văn bản thành đặc trưng văn bản."""
    inputs = processor(text=text_list, return_tensors="pt", padding=True, truncation=True).to(device)
    with torch.no_grad():
        text_features = model.get_text_features(**inputs)
    return text_features.cpu().numpy()

def format_image_name(number, width=3):
    """Định dạng tên ảnh để có đủ chữ số cần thiết."""
    return str(number).zfill(width)

def get_neighbor_image_details(image_name, num_neighbors=3):
    """Tìm các tên ảnh lân cận dựa trên tên ảnh hiện tại."""
    try:
        # Chuyển đổi tên ảnh sang số nguyên
        current_number = int(image_name)
    except ValueError:
        print(f"Cannot convert image name '{image_name}' to an integer.")
        return []

    # Tạo danh sách các tên ảnh lân cận
    neighbors = []
    for i in range(-num_neighbors, num_neighbors + 1):
        if i == 0:
            continue  # Bỏ qua ảnh hiện tại
        neighbor_number = current_number + i
        # Chuyển đổi lại sang tên ảnh và thêm vào danh sách
        neighbor_name = format_image_name(neighbor_number)
        neighbors.append(neighbor_name)

    return neighbors

def load_frame_id_map(folder_name):
    """Tải các frame ID từ file CSV tương ứng với tên thư mục."""
    csv_path = os.path.join(map_folder, f'{folder_name}.csv')
    if not os.path.exists(csv_path):
        print(f"File CSV '{csv_path}' không tồn tại.")
        return {}
    
    # Đọc file CSV
    df = pd.read_csv(csv_path, header=None)

    # Xử lý giá trị không hợp lệ và tạo từ điển frame ID
    frame_id_dict = {}
    for _, row in df.iterrows():
        try:
            # Chuyển đổi các giá trị thành số nguyên
            image_name = str(int(row.iloc[0]))
            frame_id = int(row.iloc[3])
            frame_id_dict[image_name] = frame_id
        except (ValueError, TypeError):
            # print(f"Giá trị không hợp lệ trong hàng: {row.tolist()}")
            continue  # Bỏ qua hàng có giá trị không hợp lệ

    return frame_id_dict

@sio.event
def connect(sid, environ):
    logger.info(f"Client {sid} connected")

@sio.event
def disconnect(sid):
    logger.info(f"Client {sid} disconnected")

@sio.event
def translated_text(sid, data):
    global result_json
    keywords_input = data.get('text', '').strip()
    print(f"Received message: {keywords_input}")

    keywords = [keyword.strip() for keyword in keywords_input.split(';') if keyword.strip()]

    # Chuyển đổi từ khóa thành đặc trưng văn bản
    text_features = text_to_features(keywords)

    # Tính toán độ tương đồng cosine giữa đặc trưng văn bản và đặc trưng hình ảnh
    similarities = cosine_similarity(text_features, image_features)

    # Lấy chỉ số của 10 ảnh phù hợp nhất
    top_indices = np.argsort(similarities[0])[::-1][:50]

    # Hiển thị danh sách ảnh phù hợp nhất và ảnh xung quanh chúng
    # total_images = len(image_info)
    for i, index in enumerate(top_indices):
        # Lấy thông tin của ảnh ưu tiên
        folder_name, image_name = image_info[index]

        # Tải bản đồ tên ảnh và frameID từ file CSV tương ứng
        frame_id_map = load_frame_id_map(folder_name)
        image_name_int = str(int(image_name))  # Chuyển tên ảnh sang integer dạng string

        # Lấy frameID của ảnh ưu tiên
        frame_id = frame_id_map.get(image_name_int, "N/A")

        # Tìm các tên ảnh lân cận
        neighbor_image_names = get_neighbor_image_details(image_name)

        # Hiển thị 2 ảnh lân cận trước
        for idx, neighbor_image_name in enumerate(neighbor_image_names[:3], start=1):
            img_path = os.path.join(image_folder, folder_name, neighbor_image_name + ".jpg")
            neighbor_image_name_int = str(int(neighbor_image_name))
            neighbor_frame_id = frame_id_map.get(neighbor_image_name_int, "N/A")
            neighbor_name = neighbor_image_name + ".jpg"
            # print(f"+ Nearby Image of rank {i+1}: Folder '{folder_name}', Name '{neighbor_name}', FrameID '{neighbor_frame_id}'")
            # Thêm thông tin ảnh tiệm cận trước vào đối tượng với định dạng "near1.1", "near1.2", ...
            result_json[f"near{i+1}.{idx}"] = {"keyframe": folder_name, "name": neighbor_name, "frameid": neighbor_frame_id}
            if os.path.exists(img_path):
                # display(IPyImage(img_path))
                pass
            else:
                print(f"Image file '{img_path}' does not exist.")

        # Hiển thị ảnh ưu tiên
        similarity_score = similarities[0][index]
        image_full_name = image_name + ".jpg"
        # print(f">> Rank {i+1}: Folder '{folder_name}', Name '{image_full_name}', FrameID '{frame_id}' with similarity score {similarity_score:.4f}")
        # Thêm thông tin ảnh top priority vào đối tượng.
        result_json[f"rank{i+1}"] = {"keyframe": folder_name, "name": image_full_name, "frameid": frame_id}
        img_path = os.path.join(image_folder, folder_name, image_name + ".jpg")
        if os.path.exists(img_path):
            # display(IPyImage(img_path))
            pass
        else:
            print(f"Image file '{img_path}' does not exist.")

        # Hiển thị 3 ảnh lân cận sau
        for idx, neighbor_image_name in enumerate(neighbor_image_names[3:], start=4):
            img_path = os.path.join(image_folder, folder_name, neighbor_image_name + ".jpg")
            neighbor_image_name_int = str(int(neighbor_image_name))
            neighbor_frame_id = frame_id_map.get(neighbor_image_name_int, "N/A")
            neighbor_name = neighbor_image_name + ".jpg"
            result_json[f"near{i+1}.{idx}"] = {"keyframe": folder_name, "name": neighbor_name, "frameid": neighbor_frame_id}
            if os.path.exists(img_path):
                pass
            else:
                print(f"Image file '{img_path}' does not exist.")

    #Hiển thị thông tin và gửi đối tượng đến app.
    sio.emit('result', result_json)
    # for json_key, json_value in result_json.items():
    #     print(f"{json_key}: {json_value}")
    result_json = {}

if __name__ == '__main__':
    import eventlet
    import eventlet.wsgi
    eventlet.wsgi.server(eventlet.listen(('localhost', 5000)), app)

