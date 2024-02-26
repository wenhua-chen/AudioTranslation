# -*- coding:utf-8 -*- 
# Author: 陈文华(Steven)
# Website: https://wenhua-chen.github.io/
# Github: https://github.com/wenhua-chen
# Date: 2023-01-16 22:34:50
# LastEditTime: 2023-01-16 22:50:41
# Description: 修改字幕文件的顺序

# 读取原始srt文件
def read_srt(input_path):
    # 读取数据
    with open(input_path,'r') as f:
        lines = f.readlines()
    
    # 初步整理成list
    srt_lst = []
    srt = []
    for i, line in enumerate(lines):
        if len(line.strip()) == 0:
            assert len(srt)==3, f'len(srt)!=3, {i}, {line}'
            srt_lst.append(srt)
            srt = []
        else:
            srt.append(line)
    if len(srt) == 3: # 补充最后一个
        srt_lst.append(srt)
    return srt_lst

def write_srt(srt_lst, output_path):
    with open(output_path,'w') as f:
        for i, srt in enumerate(srt_lst):
            f.write(str(i+1)+'\n')
            f.write(srt[1])
            f.write(srt[2])
            f.write('\n')

if __name__ == '__main__':
    input_path = "subtitles/ZH_a5_Why France is Secretly the World's 5th Biggest Country_rearranged.srt"
    output_path = input_path.replace('/ZH_a','/ZH_test_a')

    srt_lst = read_srt(input_path)
    write_srt(srt_lst, output_path)