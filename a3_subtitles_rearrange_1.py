# -*- coding:utf-8 -*- 
# Author: 陈文华(Steven)
# Website: https://wenhua-chen.github.io/
# Github: https://github.com/wenhua-chen
# Date: 2022-08-10 17:17:21
# LastEditTime: 2022-08-17 13:48:03
# Description: 字幕重构, 第一版(废弃)

def time_to_time_str(time):
    m, s = divmod(int(time), 60)
    h, m = divmod(m, 60)
    return f'{h:02d}:{m:02d}:{s:02d},{int(time%1*1000):03d}'

def time_str_to_time(time_str):
    hms,ms = time_str.split(',')
    h,m,s = hms.split(':')
    time = int(h)*3600+int(m)*60+int(s) + float(ms)/1000
    return time

# 读取原始srt文件
def read_srt(input_path):
    # 读取数据
    with open(input_path,'r') as f:
        lines = f.readlines()
    
    # 初步整理成list
    srt_lst = []
    srt = []
    for line in lines:
        line = line.strip()
        if len(line) == 0:
            assert len(srt)==3, 'len(srt)!=3'
            srt_lst.append(srt)
            srt = []
        else:
            srt.append(line)
    if len(srt) == 3: # 补充最后一个
        srt_lst.append(srt)

    # 进一步整理
    for i in range(len(srt_lst)):
        srt = srt_lst[i]
        start_time, _, end_time = srt[1].split(' ')
        start_time = time_str_to_time(start_time)
        end_time = time_str_to_time(end_time)
        words = srt[2].split(' ')
        srt_lst[i] = {'s_time':start_time, 'e_time':end_time, 'words':words}
    return srt_lst

def write_srt(srt_lst, output_path):
    # 整理
    for i in range(len(srt_lst)):
        srt = srt_lst[i]
        start_time = time_to_time_str(srt['s_time'])
        end_time = time_to_time_str(srt['e_time'])
        time = f'{start_time} --> {end_time}'
        srt_lst[i] = [str(i+1), time, ' '.join(srt['words']), '']
    # 输出
    with open(output_path,'w') as f:
        for srt in srt_lst:
            for j, line in enumerate(srt):
                if j == 2:
                    if not line[-1].isalpha(): # 去掉结尾的标点
                        line = line[:-1]
                f.write(line.lower()+'\n')

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
                if words[i] in break_words:
                    duration = srt['e_time'] - srt['s_time']
                    break_time = i/len(words) * duration + srt['s_time']
                    first_srt = {'s_time':srt['s_time'], 'e_time':break_time, 'words':words[:i]}
                    second_srt = {'s_time':break_time, 'e_time':srt['e_time'], 'words':words[i:]}
                    new_srt_lst.append(first_srt)
                    new_srt_lst.append(second_srt)
                    break_flag = True
                    loop_again = True
                    break
            if not break_flag:
                new_srt_lst.append(srt)
        
        # 向后截断
        srt_lst = new_srt_lst
        new_srt_lst = []
        for srt in srt_lst:
            words = srt['words']
            break_flag = False
            for i in range(len(words)-1):
                if words[i][-1] in break_symbols:
                    i += 1
                    duration = srt['e_time'] - srt['s_time']
                    break_time = i/len(words) * duration + srt['s_time']
                    first_srt = {'s_time':srt['s_time'], 'e_time':break_time, 'words':words[:i]}
                    second_srt = {'s_time':break_time, 'e_time':srt['e_time'], 'words':words[i:]}
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
        if (words[0][0].islower()) and (prev_srt is not None) and ((len(words) <= 3 and words[-1][-1] in break_symbols) or (words[0] in concat_front_words)):
            prev_srt['e_time'] = srt['e_time']
            prev_srt['words'] += srt['words']
        else:
            prev_srt = srt
            new_srt_lst.append(prev_srt)
            
    
    # 拼接到后面
    srt_lst = new_srt_lst
    new_srt_lst = []
    prev_srt = None
    for srt in srt_lst:
        if prev_srt is not None:
            srt['words'] = prev_srt['words'] + srt['words']
            srt['s_time'] = prev_srt['s_time']
            prev_srt = None
        else:
            words = srt['words']
            if (len(words) <= 3 and words[0].lower() in break_words) or (words[-1] in concat_back_words):
                prev_srt = srt
                continue
        new_srt_lst.append(srt)
    return new_srt_lst

if __name__ == '__main__':
    input_path = 'VEED-subtitles_English_What If We Covered the Sahara With Solar Panels？_What If We Covered the Sahara With Solar Panels？.srt'
    output_path = f'{input_path[:-4]}_new.srt'
    break_words = set(['that','which','but','and','or'])
    break_symbols = set([',', '.'])
    concat_front_words = set(['of'])
    concat_back_words = set(['the'])

    # 读取
    srt_lst = read_srt(input_path)

    # 截断
    srt_lst = cut_off(srt_lst)
    
    # 拼接
    srt_lst = concat(srt_lst)
    
    # 输出
    write_srt(srt_lst, output_path)
                
                

    

    