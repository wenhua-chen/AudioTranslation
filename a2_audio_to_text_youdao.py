# -*- coding:utf-8 -*- 
# Author: 陈文华(Steven)
# Website: https://wenhua-chen.github.io/
# Github: https://github.com/wenhua-chen
# Date: 2022-08-12 16:28:52
# LastEditTime: 2023-01-13 15:40:30
# Description: 语音识别

import hashlib
import json
import os
import time
import uuid
import requests
import pickle
from tqdm import tqdm
from glob import glob
from a3_subtitles_rearrange_2 import write_srt

# 请求路径
asr_host = 'https://openapi.youdao.com/api/audio'
api_prepare = '/prepare'
api_upload = '/upload'
api_merge = '/merge'
api_get_progress = '/get_progress'
api_get_result = '/get_result'
file_piece_sice = 10*1024*1024 # 文件分片大小10M

def encrypt(signStr):
    hash = hashlib.sha256()
    hash.update(signStr.encode('utf-8'))
    return hash.hexdigest()

def result_to_srt_list(result):
    srt_list = []
    for sentence_dict in result:
        srt = dict()
        srt['s_time'] = float(sentence_dict['word_timestamps'][0])/1000
        srt['e_time'] = float(sentence_dict['word_timestamps_eds'][-1])/1000
        srt['words'] = sentence_dict['words']
        srt_list.append(srt)
    return srt_list

class RequestApi(object):
    def __init__(self):
        self.app_key = '2390aff591342262'
        self.app_secret = 'GJjMuCSPxkpw2lWVpEjvnlGkT26Sjb8P'
        self.lang = 'en'

    def gene_params(self, apiname):
        app_key = self.app_key
        file_len = self.file_len
        nonce = str(uuid.uuid1())
        curtime = str(int(time.time()))
        sign = encrypt(app_key + nonce + curtime + self.app_secret)

        param_dict = {}
        if apiname == api_prepare:
            slice_num = int(file_len / file_piece_sice) + (0 if (file_len % file_piece_sice == 0) else 1)
            param_dict['appKey'] = app_key
            param_dict['sign'] = sign
            param_dict['curtime'] = curtime
            param_dict['salt'] = nonce
            param_dict['signType'] = "v4"
            param_dict['langType'] = self.lang
            param_dict['fileSize'] = str(file_len)
            param_dict['name'] = self.file_name
            param_dict['format'] = self.format
            param_dict['sliceNum'] = str(slice_num)
        elif apiname == api_upload:
            param_dict['appKey'] = app_key
            param_dict['sign'] = sign
            param_dict['curtime'] = curtime
            param_dict['salt'] = nonce
            param_dict['signType'] = "v4"
            param_dict['q'] = self.taskid
            param_dict['sliceId'] = self.slice_id
        elif apiname == api_merge:
            param_dict['appKey'] = app_key
            param_dict['sign'] = sign
            param_dict['curtime'] = curtime
            param_dict['salt'] = nonce
            param_dict['signType'] = "v4"
            param_dict['q'] = self.taskid
        elif apiname == api_get_progress or apiname == api_get_result:
            param_dict['appKey'] = app_key
            param_dict['sign'] = sign
            param_dict['curtime'] = curtime
            param_dict['salt'] = nonce
            param_dict['signType'] = "v4"
            param_dict['q'] = self.taskid
        return param_dict

    def gene_request(self, apiname, files=None, headers=None):
        data = self.gene_params(apiname)
        response = requests.post(asr_host + apiname, data=data, files=files, headers=headers)
        result = json.loads(response.text)
        if result["errorCode"] == "0":
            return result
        else:
            assert 1>2, f"[{apiname} error]: {str(result)}"

    # 获取分析结果
    def get_result(self, audio_path):
        # 准备参数
        self.slice_id = 1
        self.start_time = time.time()
        self.upload_audio_path = audio_path
        self.file_len = os.path.getsize(audio_path)
        self.file_name = os.path.basename(audio_path)
        self.format = os.path.splitext(audio_path)[-1][1:]
        self.taskid = self.gene_request(api_prepare)['result']

        # 分段上传
        file_object = open(self.upload_audio_path, 'rb')
        try:
            while True:
                print(f'[数据上传] {int(time.time()-self.start_time)}s...')
                content = file_object.read(file_piece_sice)
                if not content or len(content) == 0:
                    break
                self.gene_request(api_upload, files={"file": content})
                self.slice_id += 1
        finally:
            file_object.close()
        self.gene_request(api_merge) # 合并

        # 等待云端处理
        while True:
            process = self.gene_request(api_get_progress)['result'][0]
            if process['status'] == '9':
                break
            print(f'[云端分析] {int(time.time()-self.start_time)}s...')
            time.sleep(10) # 每次获取进度间隔10s
        
        # 获取结果
        result = self.gene_request(api_get_result)
        return result

if __name__ == '__main__':
    # 准备
    audios = sorted(glob('audios/*.aac'))
    api = RequestApi()

    for audio_path in tqdm(audios):
        # 分析结果
        result_path = f'{audio_path[:-4].replace("audios/","yd_results/")}.pkl'
        if os.path.exists(result_path): # 从本地读取
            with open(result_path,'rb') as f:
                result = pickle.load(f)
        else: # 保存到本地
            print('='*50)
            print(audio_path+'\n')
            result = api.get_result(audio_path)
            with open(result_path, 'wb') as f:
                pickle.dump(result, f)

        # 制作字幕
        subtitle_path = f'{result_path[:-4]}_yd.srt'
        if not os.path.exists(subtitle_path):
            srt_list = result_to_srt_list(result['result'])
            write_srt(srt_list, subtitle_path)

