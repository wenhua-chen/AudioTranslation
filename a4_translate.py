# -*- coding:utf-8 -*- 
# Author: 陈文华(Steven)
# Website: https://wenhua-chen.github.io/
# Github: https://github.com/wenhua-chen
# Date: 2022-08-11 15:35:13
# LastEditTime: 2023-01-17 16:04:19
# Description: 翻译

from a3_subtitles_rearrange_2 import read_srt, write_srt
import subprocess
import json
import uuid
import os
import requests
import hashlib
import time
import traceback
from tqdm import tqdm

def encrypt(signStr):
    hash_algorithm = hashlib.sha256()
    hash_algorithm.update(signStr.encode('utf-8'))
    return hash_algorithm.hexdigest()

def truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

def do_request(data):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    return requests.post(YOUDAO_URL, data=data, headers=headers)

def english_to_chinese(sentence):
    # 去掉最后的标点
    if not sentence[-1].isalpha():
        sentence = sentence[:-1]

    data = {}
    data['from'] = 'EN'
    data['to'] = 'zh-CHS'
    data['signType'] = 'v3'
    curtime = str(int(time.time()))
    data['curtime'] = curtime
    salt = str(uuid.uuid1())
    signStr = APP_KEY + truncate(sentence) + salt + curtime + APP_SECRET
    sign = encrypt(signStr)
    data['appKey'] = APP_KEY
    data['q'] = sentence
    data['salt'] = salt
    data['sign'] = sign
    
    response = do_request(data)
    content = json.loads(response.content)
    assert 'translation' in content, content
    result = content['translation'][0]
    return result

def translate_srt(srt_lst):
    for srt in tqdm(srt_lst):
        request_count = 3
        while request_count > 0:
            try:
                srt['words'] = english_to_chinese(' '.join(srt['words']))
                break
            except Exception:
                print(f'[Exception] {request_count}')
                time.sleep(5)
                request_count -= 1
    return srt_lst

if __name__ == '__main__':
    # 参数
    input_path = "subtitles/EN_a7_How Las Vegas Exists in America's Driest Desert_rearranged.srt"
    output_path = input_path.replace('/EN_a','/ZH_a')
    YOUDAO_URL = 'https://openapi.youdao.com/api'
    APP_KEY = '77a704e43d9010d2'
    APP_SECRET = '0Lp24OXhGej9lqzZu36ao31WHbRGe4p2'

    # 翻译
    if not os.path.exists(output_path):
        srt_lst = read_srt(input_path) # 读取
        srt_lst = translate_srt(srt_lst) # 翻译
        write_srt(srt_lst, output_path) # 输出
