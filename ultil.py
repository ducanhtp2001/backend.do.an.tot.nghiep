# from PIL import Image, ImageDraw, ImageFont
# import os

# AVATAR_FOLDER = 'D:/com.backend.do.an.tot.nghiep/avatar'

# def create_avatar(name, size=300, background_color=(255, 255, 255), text_color=(0, 0, 0)):
#     # Tạo ảnh mới với kích thước và màu nền chỉ định
#     img = Image.new('RGB', (size, size), background_color)
    
#     # Sử dụng font có sẵn
#     try:
#         font = ImageFont.truetype("arial.ttf", size=int(size*0.4))
#     except IOError:
#         font = ImageFont.load_default()
    
#     # Tạo đối tượng vẽ
#     draw = ImageDraw.Draw(img)
    
#     # Tính toán kích thước văn bản và vị trí để canh giữa
#     text_width, text_height = draw.textsize(name[0], font=font)
#     x = (size - text_width) / 2
#     y = (size - text_height) / 2
    
#     # Vẽ văn bản lên ảnh
#     draw.text((x, y), name[0], fill=text_color, font=font)
    
#     # Lưu ảnh
#     img.save(os.path.join(AVATAR_FOLDER, f"{name}_avatar.png"))

# # Tạo avatar với ký tự "G" như Gmail
# create_avatar("Gmail", size=300)

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random

def send_email(receiver_email, subject, body):
    sender_email = "xyza09346@gmail.com"
    app_password = "zddn kntr fgcl bhzd"
    try:
        # Thiết lập máy chủ SMTP cho Gmail
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Tạo phiên SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Bắt đầu kết nối TLS (bảo mật)

        # Đăng nhập vào tài khoản Gmail bằng mật khẩu ứng dụng
        server.login(sender_email, app_password)
        
        # Tạo đối tượng email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # Thêm nội dung email
        msg.attach(MIMEText(body, 'plain'))
        
        # Gửi email
        server.sendmail(sender_email, receiver_email, msg.as_string())

        # Đóng phiên SMTP
        server.quit()

        return True
    except Exception as e:
        return False

def generate_random_otp():
    return "{:04}".format(random.randint(0, 9999))

# print(generate_random_otp())

# Thông tin tài khoản Gmail và nội dung email

# receiver_email = "ducanh123.com@gmail.com"
# subject = "Đây là chủ đề email"
# body = "Đây là nội dung email"

# Gửi email
# send_email(sender_email, sender_password, receiver_email, subject, body)
