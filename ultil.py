from PIL import Image, ImageDraw, ImageFont
import os

AVATAR_FOLDER = 'D:/com.backend.do.an.tot.nghiep/avatar'

def create_avatar(name, size=300, background_color=(255, 255, 255), text_color=(0, 0, 0)):
    # Tạo ảnh mới với kích thước và màu nền chỉ định
    img = Image.new('RGB', (size, size), background_color)
    
    # Sử dụng font có sẵn
    try:
        font = ImageFont.truetype("arial.ttf", size=int(size*0.4))
    except IOError:
        font = ImageFont.load_default()
    
    # Tạo đối tượng vẽ
    draw = ImageDraw.Draw(img)
    
    # Tính toán kích thước văn bản và vị trí để canh giữa
    text_width, text_height = draw.textsize(name[0], font=font)
    x = (size - text_width) / 2
    y = (size - text_height) / 2
    
    # Vẽ văn bản lên ảnh
    draw.text((x, y), name[0], fill=text_color, font=font)
    
    # Lưu ảnh
    img.save(os.path.join(AVATAR_FOLDER, f"{name}_avatar.png"))

# Tạo avatar với ký tự "G" như Gmail
create_avatar("Gmail", size=300)
