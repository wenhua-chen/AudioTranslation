# -*- coding:utf-8 -*- 
# Author: 陈文华(Steven)
# Website: https://wenhua-chen.github.io/
# Github: https://github.com/wenhua-chen
# Date: 2022-08-11 10:35:45
# LastEditTime: 2023-01-13 15:51:09
# Description: 字幕重构, 第三版, 根据词语的起止时间进行截断

import pickle
import os
from glob import glob
from tqdm import tqdm

def time_to_time_str(time):
    m, s = divmod(int(time), 60)
    h, m = divmod(m, 60)
    return f'{h:02d}:{m:02d}:{s:02d},{int(time%1*1000):03d}'

#检验是否含有中文字符
def is_contains_chinese(strs):
    for _char in strs:
        if '\u4e00' <= _char <= '\u9fa5':
            return True
    return False

def write_srt_with_timestamps(srt_lst, output_path):
    # 整理
    for i in range(len(srt_lst)):
        srt = srt_lst[i]
        start_time = time_to_time_str(srt['s_times'][0])
        end_time = time_to_time_str(srt['e_times'][-1])
        time = f'{start_time} --> {end_time}'
        if is_contains_chinese(srt['words']):
            sentence = srt['words']
        else:
            sentence = ' '.join(srt['words'])
        srt_lst[i] = [str(i+1), time, sentence, '']
    # 输出
    with open(output_path,'w') as f:
        for srt in srt_lst:
            for j, line in enumerate(srt):
                if j == 2:
                    if not line[-1].isalpha(): # 去掉结尾的标点
                        line = line[:-1]
                # f.write(line.lower()+'\n') # 转小写
                f.write(line+'\n') # 转小写

# 截断逻辑
def cut_off(srt_lst):
    new_srt_lst = []

    # 循环直到不能再次截断
    while True:
        loop_again = False
        # 向前截断
        if len(new_srt_lst) != 0:
            srt_lst = new_srt_lst
            new_srt_lst = []
        for srt in srt_lst:
            words = srt['words']
            break_flag = False
            for i in range(1,len(words)):
                if words[i] in break_words: # 遇到'xxx and'就在'and'前面截断
                    first_srt = {'s_times':srt['s_times'][:i], 'e_times':srt['s_times'][:i], 'words':words[:i]}
                    second_srt = {'s_times':srt['s_times'][i:], 'e_times':srt['s_times'][i:], 'words':words[i:]}
                    new_srt_lst.append(first_srt)
                    new_srt_lst.append(second_srt)
                    break_flag = True
                    loop_again = True
                    break
            if not break_flag:
                new_srt_lst.append(srt)
        
        # 向后截断
        if len(new_srt_lst) != 0:
            srt_lst = new_srt_lst
            new_srt_lst = []
        for srt in srt_lst:
            words = srt['words']
            break_flag = False
            for i in range(len(words)-1):
                if words[i][-1] in break_symbols: # 遇到'xxx. ' 就在'.'后面截断
                    i += 1
                    first_srt = {'s_times':srt['s_times'][:i], 'e_times':srt['s_times'][:i], 'words':words[:i]}
                    second_srt = {'s_times':srt['s_times'][i:], 'e_times':srt['s_times'][i:], 'words':words[i:]}
                    new_srt_lst.append(first_srt)
                    new_srt_lst.append(second_srt)
                    break_flag = True
                    loop_again = True
                    break
            if not break_flag:
                new_srt_lst.append(srt)

        # 循环退出条件
        if not loop_again:
            break
    return new_srt_lst

# 拼接逻辑
def concat(srt_lst):
    # 拼接到前面
    new_srt_lst = []
    prev_srt = None
    for srt in srt_lst:
        words = srt['words']
        if prev_srt is None:
            prev_srt = srt
            new_srt_lst.append(prev_srt)
        elif words[0] in break_words and prev_srt['words'][-1][-1]==',': # ', and'处应该保持断开(不合并)
            prev_srt = srt
            new_srt_lst.append(prev_srt)
        else: # 其他地方都拼接到前面
            prev_srt['s_times'] += srt['s_times']
            prev_srt['e_times'] += srt['e_times']
            prev_srt['words'] += srt['words']
        
        if words[-1][-1] in break_symbols: # '. '处应该保持断开(不合并)
            prev_srt = None
    return new_srt_lst

# 二次截断, 目的是给长句子做截断
def cut_off_again(srt_lst):
    new_srt_lst = []

    # 循环直到不能再次截断
    while True:
        loop_again = False

        # 向后截断
        if len(new_srt_lst) != 0:
            srt_lst = new_srt_lst
            new_srt_lst = []
        for srt in srt_lst:
            words = srt['words']
            break_flag = False
            if len(' '.join(words)) > 100: # 对于>100的长句子
                stop_index_lst = [index for index,word in enumerate(words[:-1]) if word[-1]==',']
                if len(stop_index_lst) > 0: # 如果有', '逗号, 在最靠近中间的','逗号处向后截断
                    stop_dist_lst = [abs(index-len(words)/2) for index in stop_index_lst]
                    stop_index = stop_index_lst[stop_dist_lst.index(min(stop_dist_lst))]+1
                    first_srt = {'s_times':srt['s_times'][:stop_index], 'e_times':srt['s_times'][:stop_index], 'words':words[:stop_index]}
                    second_srt = {'s_times':srt['s_times'][stop_index:], 'e_times':srt['s_times'][stop_index:], 'words':words[stop_index:]}
                    new_srt_lst.append(first_srt)
                    new_srt_lst.append(second_srt)
                    break_flag = True
                    loop_again = True
            if not break_flag:
                new_srt_lst.append(srt)
        
        # 循环退出条件
        if not loop_again:
            break
    return new_srt_lst

def load_yd_result(result_path):
    with open(result_path,'rb') as f:
        yd_result = pickle.load(f)
    srt_lst_with_timestamps = []
    for sentence_dict in yd_result['result']:
        srt = dict()
        srt['words'] = sentence_dict['words']
        srt['s_times'] = [float(timestamp)/1000 for timestamp in sentence_dict['word_timestamps']]
        srt['e_times'] = [float(timestamp)/1000 for timestamp in sentence_dict['word_timestamps_eds']]
        srt_lst_with_timestamps.append(srt)
    return srt_lst_with_timestamps

if __name__ == '__main__':
    break_words = set(['that','which','but','and','or','while'])
    break_symbols = set(['?', '.'])
    
    results = sorted(glob('yd_results/*.pkl'))
    for result_path in tqdm(results):
        output_path = f'{result_path[:-4]}_rearranged.srt'
        if os.path.exists(output_path):
            continue

        srt_lst_with_timestamps = load_yd_result(result_path) # 读取有道结果

        # 截断逻辑
        # 1. 遇到'xxx and'就在'and'前面截断
        # 2. 遇到'xxx. ' 就在'.'后面截断
        srt_lst_with_timestamps = cut_off(srt_lst_with_timestamps)

        # 拼接逻辑
        # 1. ', and'处应该保持断开(不合并)
        # 2. '. '处应该保持断开(不合并)
        # 3. 其他地方都拼接到前面
        srt_lst_with_timestamps = concat(srt_lst_with_timestamps) # 拼接

        # 二次截断逻辑: 目的是给长句子做截断
        # 对于>100的长句子, 如果有', '逗号, 在最靠近中间的','逗号处向后截断
        srt_lst_with_timestamps = cut_off_again(srt_lst_with_timestamps)
        
        # 输出
        write_srt_with_timestamps(srt_lst_with_timestamps, output_path)
                
                

    

    