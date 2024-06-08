from tkinter import Image
from flask import app
from pdf2image import convert_from_path
import numpy as np
import cv2
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch
import pytesseract
import os
import db_manager as db
import time
import re
from backend import *


BASE_FOLDER = 'D:/com.backend.do.an.tot.nghiep/'

model = None
tokenizer = None

totalTime = 0

device = torch.device("cpu")

# def file_execute_task(onExecuteDone, onDone):
# @celery.task
def file_execute_task():
    print('on task')
    while True:
        file = db.get_file_to_execute()

        if not file: 
            onDoneAll()
            break
        else:
            print('start execute')
            filePath = BASE_FOLDER + "file_folder/" + file['fileName']
            # print(filePath)
            images = convert_from_path(filePath)

            summary_text = ""
            with open("result/origin_text.txt", "w", encoding="utf-8") as f:
                file_content = f.write("")
            with open("result/summary_text.txt", "w", encoding="utf-8") as f:
                file_content = f.write("")

            file_path = BASE_FOLDER + "modelT5"

            # load model T5
            global model
            global tokenizer
            
            try:
                if model is None:
                    model = T5ForConditionalGeneration.from_pretrained(file_path)
                if tokenizer is None:
                    tokenizer = T5Tokenizer.from_pretrained(file_path)
            except:
                model = T5ForConditionalGeneration.from_pretrained("NlpHUST/t5-small-vi-summarization")
                tokenizer = T5Tokenizer.from_pretrained("NlpHUST/t5-small-vi-summarization")

                model.save_pretrained(file_path)
                tokenizer.save_pretrained(file_path)

            model.eval()
            model.no_repeat_ngram_size = 0


            print('convert to img')

            for i, image in enumerate(images):
                img_array = np.array(image)

                gray_img = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
                gray_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                # gray_img = cv2.medianBlur(gray_img, 3)

                text = ""
                text = pytesseract.image_to_string(gray_img,lang='vie')
                with open("result/origin_text.txt", "a", encoding="utf-8") as f:
                    f.write(text)
                with open("result/recognize_text.txt", "a", encoding="utf-8") as f:
                    f.write(text)

            with open("result/origin_text.txt", "r", encoding="utf-8") as f:
                file_content = f.read()
                
            cleaned_content = ' '.join(file_content.split())
                # print(cleaned_content)
            with open("result/origin_text.txt", "w", encoding="utf-8") as f:
                f.write(cleaned_content)

                # phan doan
            segments = split_text_by_word_count(cleaned_content)
                # print(segments)

            print('summary')
            for segment in segments:
                # print(segment.count("."))
                summary_fun(segment, model, tokenizer)
            
            with open("result/summary_text.txt", "r", encoding="utf-8") as f:
                summary_text = f.read()
            recognize_text = ""
            with open("result/recognize_text.txt", "r", encoding="utf-8") as f:
                recognize_text = f.read()
            recognize_text = trimStr(recognize_text)

            db.update_file_after_execute(file['_id'], recognize_text, summary_text)
            notify_file_executed_done(file)

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
        global model
        global tokenizer
        
        try:
            if model is None:
                model = T5ForConditionalGeneration.from_pretrained(file_path)
            if tokenizer is None:
                tokenizer = T5Tokenizer.from_pretrained(file_path)
        except:
            model = T5ForConditionalGeneration.from_pretrained("NlpHUST/t5-small-vi-summarization")
            tokenizer = T5Tokenizer.from_pretrained("NlpHUST/t5-small-vi-summarization")

            model.save_pretrained(file_path)
            tokenizer.save_pretrained(file_path)

        model.eval()
        model.no_repeat_ngram_size = 0

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

            # phan doan
        segments = split_text_by_word_count(cleaned_content)
            # print(segments)

        for segment in segments:
            # print(segment.count("."))
            summary_fun(segment, model, tokenizer)


def summary_fun(segment, model, tokenizer):
    global totalTime
    print('tom tat', segment)
    start_time_ms = int(time.time() * 1000)

    tokenized_text = tokenizer.encode(segment, return_tensors="pt").to(device)
    
    summary_ids = model.generate(
        tokenized_text,
        max_length=756, 
        num_beams=4,
        repetition_penalty=2.5,
        early_stopping=False
    )
    summary_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    with open("result/summary_text.txt", "a", encoding="utf-8") as f:
        f.write(summary_text + "\n")
    end_time_ms = int(time.time() * 1000)
    totalTime = totalTime + (end_time_ms - start_time_ms)
    print('current total time to summary: ', totalTime)
    

def split_text_by_word_count(text, max_words=305):
    words = text.split()
    size = len(words)
    cur_segment = []
    segments = []
    cur_index = 0

    while True:
         next_index = cur_index + max_words
         if next_index > size:
              cur_segment = words[cur_index:]
              segments.append(" ".join(cur_segment))
              break
         
         cur_segment = words[cur_index:next_index]
         cur_index = next_index
         segments.append(" ".join(cur_segment))    

    return segments


def trimStr(str):
    str = re.sub(r'\s+', ' ', str)
    str = re.sub(r'[\r\n]+', '\n', str)
    return str.strip()


file_execute_task()

# execute_test()