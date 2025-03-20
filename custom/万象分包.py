import os

def process_rime_dicts(input_dir, output_dir, start_index=1, end_index=2, remove_trailing_semicolon=False):
    """
    处理词典文件，将拼音数据中的指定范围内的内容提取并处理。

    :param input_dir: 输入目录路径
    :param output_dir: 输出目录路径
    :param start_index: 处理的开始分号索引
    :param end_index: 处理的结束分号索引（如果为 None 则表示直到末尾）
    :param remove_trailing_semicolon: 是否去掉末尾的分号（仅当处理到最后一段时需要）
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 遍历输入目录中的所有文件
    for filename in os.listdir(input_dir):
        if filename.endswith('.yaml') or filename.endswith('.txt'):
            input_file = os.path.join(input_dir, filename)
            output_file = os.path.join(output_dir, filename)

            with open(input_file, 'r', encoding='utf-8') as infile:
                lines = infile.readlines()

            processed_data = []
            processing = False

            for line in lines:
                raw_line = line  # 保留原始行（包含换行符）
                line = line.strip()

                # 如果检测到以汉字开头的部分，开始正式处理
                if not processing and any('\u4e00' <= char <= '\u9fff' for char in line):
                    processing = True

                if processing:
                    parts = line.split('\t')
                    if len(parts) < 3:
                        # 如果行的格式无法满足 “汉字\t拼音\t频度/注释...” 的结构
                        processed_data.append(raw_line.rstrip('\n'))
                        continue

                    chinese_part = parts[0]
                    rime_data = parts[1]
                    other_parts = parts[2:]  # 可能有多个注释列之类的

                    # 分割每个拼音数据，例如 "zhong;zong zhong;chong" 会被切成 ["zhong;zong", "zhong;chong"]
                    rime_parts = rime_data.split(' ')
                    processed_rime_parts = []

                    for rime_part in rime_parts:
                        # 对于每个单独的“拼音;拼音;...”段，split出来
                        segments = rime_part.split(';')

                        if end_index is None:
                            # 表示从 start_index 到末尾
                            if len(segments) > start_index:
                                wanted_segments = segments[0:1]  # 先保留第一个分号前面
                                if len(segments) > start_index:
                                    # 取 start_index 之后直到末尾
                                    wanted_segments.append(';'.join(segments[start_index:]))
                                processed_rime_parts.append(';'.join(wanted_segments))
                            else:
                                # 如果本身没有那么多分号，就用第一个
                                processed_rime_parts.append(segments[0])
                        else:
                            # 有 end_index 的情况
                            if len(segments) > end_index:
                                first_segment = segments[0]  # 分号前面的部分
                                middle_segment = segments[start_index] if len(segments) > start_index else ''
                                # 以分号形式拼接
                                processed_rime_parts.append(f"{first_segment};{middle_segment}")
                            else:
                                # 不够分号数，就只用第一个
                                processed_rime_parts.append(segments[0])

                    # 将处理后的拼音合并
                    processed_rime_data = ' '.join(processed_rime_parts)

                    # 如果需要去掉末尾分号
                    if remove_trailing_semicolon and processed_rime_data.endswith(';'):
                        processed_rime_data = processed_rime_data.rstrip(';')

                    # 拼装回去
                    result_line = '\t'.join([
                        chinese_part,
                        processed_rime_data,
                        *other_parts
                    ])

                    processed_data.append(result_line)
                else:
                    # 还没到汉字列表内容部分的行，原样保持
                    processed_data.append(raw_line.rstrip('\n'))

            # 写入新的文件
            with open(output_file, 'w', encoding='utf-8') as outfile:
                for item in processed_data:
                    outfile.write(item + '\n')


if __name__ == "__main__":
    # 这里定义每个索引区间对应的输出目录
    index_mapping = [
        (1, 2, "moqi_cndicts"),
        (2, 3, "flypy_dicts"),
        (3, 4, "zrm_dicts"),
        (4, 5, "jdh_dicts"),
        (5, 6, "cj_dicts"),
        (6, 7, "tiger_dicts"),
        (7, 8, "wubi_dicts"),
        (8, None, "hanxin_dicts")  # 表示从 8 一直到末尾
    ]

    # 输入目录
    input_dir = 'cn_dicts'

    for start_index, end_index, out_dir in index_mapping:
        # 对于最后一个区间(8到末尾)，你想要去掉末尾分号，所以:
        remove_semicolon = (start_index == 8 and end_index is None)

        process_rime_dicts(
            input_dir=input_dir,
            output_dir=out_dir,
            start_index=start_index,
            end_index=end_index,
            remove_trailing_semicolon=remove_semicolon
        )

    print("全部处理完成！")
