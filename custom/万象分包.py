import os

def process_rime_dicts(input_dir, output_dir, start_index=1, end_index=None):
    """
    处理 Rime 词典文件，提取拼音数据中指定索引范围的部分，确保不会超出索引范围，并去除末尾分号。

    :param input_dir: 输入目录路径
    :param output_dir: 输出目录路径
    :param start_index: 处理的开始分号索引
    :param end_index: 处理的结束分号索引（如果为 None，则表示直到末尾）
    """
    os.makedirs(output_dir, exist_ok=True)  # 确保输出目录存在

    for filename in os.listdir(input_dir):
        if filename.endswith('.yaml') or filename.endswith('.txt'):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename)

            with open(input_file, 'r', encoding='utf-8') as infile:
                lines = infile.readlines()

            processed_data = []
            processing = False  # 标志是否进入了处理区

            for line in lines:
                raw_line = line  # 记录原始行，保留换行符
                line = line.strip()

                # 检测到汉字部分，开始处理
                if not processing and any('\u4e00' <= char <= '\u9fff' for char in line):
                    processing = True

                if processing:
                    parts = line.split('\t')
                    if len(parts) < 3:
                        processed_data.append(raw_line.rstrip('\n'))  # 直接存原始行
                        continue

                    chinese_part = parts[0]
                    rime_data = parts[1]
                    other_parts = parts[2:]  # 其他列（频率或注释）

                    # 分割拼音数据，例如 "zhong;zong zhong;chong" → ["zhong;zong", "zhong;chong"]
                    rime_parts = rime_data.split(' ')
                    processed_rime_parts = []

                    for rime_part in rime_parts:
                        # 处理 `;`，保留空值但不删除它
                        segments = rime_part.split(';')

                        # 计算安全索引范围
                        max_index = len(segments) - 1
                        safe_start = min(start_index, max_index)
                        safe_end = len(segments) if end_index is None else min(end_index, len(segments))

                        # 取值逻辑
                        extracted_segments = [segments[0]]  # 先保留第一个拼音
                        if safe_start < len(segments):
                            extracted_segments.append(';'.join(segments[safe_start:safe_end]))

                        # 直接拼接，即使为空也保持 `;`
                        processed_rime_parts.append(';'.join(extracted_segments))

                    # 重新组合处理后的拼音数据
                    processed_rime_data = ' '.join(processed_rime_parts)

                    # 重新拼接完整的行
                    result_line = '\t'.join([
                        chinese_part,
                        processed_rime_data,
                        *other_parts
                    ])

                    processed_data.append(result_line)
                else:
                    processed_data.append(raw_line.rstrip('\n'))  # 保持未处理部分的原样

            # 写入新的文件
            with open(output_file, 'w', encoding='utf-8') as outfile:
                for item in processed_data:
                    outfile.write(item + '\n')


if __name__ == "__main__":
    # 定义索引区间，确保 `end_index` 可能超出时取到结尾
    index_mapping = [
        (1, 2, "moqi_cndicts"),
        (2, 3, "flypy_dicts"),
        (3, 4, "zrm_dicts"),
        (4, 5, "jdh_dicts"),
        (5, 6, "cj_dicts"),
        (6, 7, "tiger_dicts"),
        (7, 8, "wubi_dicts"),
        (8, None, "hanxin_dicts")  # 8 到结尾
    ]

    input_dir = 'cn_dicts'  # 输入目录

    for start_index, end_index, out_dir in index_mapping:
        process_rime_dicts(
            input_dir=input_dir,
            output_dir=out_dir,
            start_index=start_index,
            end_index=end_index
        )

    print("全部处理完成！")
