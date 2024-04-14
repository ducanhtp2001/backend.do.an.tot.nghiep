from tkinter import Image
from flask import app
from pdf2image import convert_from_path
# from PIL import Image
import numpy as np
import cv2
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch
import pytesseract
import os
from celery import Celery
import db_manager as db

BASE_FOLDER = 'D:/com.backend.do.an.tot.nghiep/'

max_width = 612
max_height = 792

model = None
tokenizer = None
  
# def make_celery(app):
#     celery = Celery(
#         app.import_name,
#         backend=app.config['CELERY_RESULT_BACKEND'],
#         broker=app.config['CELERY_BROKER_URL']
#     )
#     celery.conf.update(app.config)
#     return celery

# app.config.update(
#     CELERY_BROKER_URL='redis://localhost:6379/0',
#     CELERY_RESULT_BACKEND='redis://localhost:6379/0'
# )
# celery = make_celery(app)

device = torch.device("cpu")


# @app.task
# def file_execute_task(onExecuteDone, onDone):
#     file = db.get_file_to_execute()

#     if not file: onDone()
#     else:
#         # filePath = UPLOAD_FOLDER + 

#         onExecuteDone()
    
def execute_test():
    file = db.get_file_to_execute()

    if not file: print("no file")
    else:
        filePath = BASE_FOLDER + "file_folder/" + file['fileName']
        print(filePath)
        images = convert_from_path(filePath)

        summary_text = ""
        with open("result/origin_text.txt", "w", encoding="utf-8") as f:
            file_content = f.write("")
        with open("result/summary_text.txt", "w", encoding="utf-8") as f:
            file_content = f.write("")

        file_path = BASE_FOLDER + "modelT5"

        # load model T5
        try:
            if model:
                model = T5ForConditionalGeneration.from_pretrained(file_path)
            if tokenizer:
                tokenizer = T5Tokenizer.from_pretrained(file_path)
        except:
            model = T5ForConditionalGeneration.from_pretrained("NlpHUST/t5-small-vi-summarization")
            tokenizer = T5Tokenizer.from_pretrained("NlpHUST/t5-small-vi-summarization")

            model.save_pretrained(file_path)
            tokenizer.save_pretrained(file_path)

        for i, image in enumerate(images):
            img_array = np.array(image)

            gray_img = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            gray_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            # gray_img = cv2.medianBlur(gray_img, 3)

            text = ""
            text = pytesseract.image_to_string(gray_img,lang='vie')
            with open("result/origin_text.txt", "a", encoding="utf-8") as f:
                # Ghi nội dung văn bản vào cuối tệp tin
                f.write(text)
            with open("result/origin_text.txt", "r", encoding="utf-8") as f:
                file_content = f.read()
            
            cleaned_content = ' '.join(file_content.split())
            # print(cleaned_content)
            with open("result/origin_text.txt", "w", encoding="utf-8") as f:
                f.write(cleaned_content)


execute_test()