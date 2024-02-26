# -*- coding:utf-8 -*- 
# Author: 陈文华(Steven)
# Website: https://wenhua-chen.github.io/
# Github: https://github.com/wenhua-chen
# Date: 2022-08-12 21:59:32
# LastEditTime: 2023-01-13 15:33:37
# Description: 提取音频

import subprocess
import os
from glob import glob
from tqdm import tqdm

if __name__ == '__main__':
    videos = glob('videos/*.mp4')
    for video_path in tqdm(videos):
        audio_path = f'{video_path.replace("videos/","audios/")[:-4]}.aac'
        if not os.path.exists(audio_path):
            print('='*50)
            print(audio_path)
            # 执行外部ffmpeg命令, 提取音频
            ffmpeg_path = '/Users/Steven/anaconda3/envs/py36/bin/ffmpeg'
            command = f'{ffmpeg_path} -i \"{video_path}\" -vn -y -acodec copy \"{audio_path}\"'
            subprocess.call(command, shell=True) # 外部命令结束后继续

