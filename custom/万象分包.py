import os

def process_rime_dicts(input_dir, output_dir, start_index=1, end_index=None):
    """
    处理 Rime 词典文件，
    1) 用\t分列，保证分成 3 列（不足补空，多余合并）；
    2) 针对第二列（拼音/编码），根据分号拆分并截取 [start_index, end_index)；
    3) 若分号不足，自动补空字符串；
    4) 写回新文件。

    :param input_dir: 输入目录路径
    :param output_dir: 输出目录路径
    :param start_index: 处理的开始分号索引（从 0 或 1 均可，需和你的需求对应）
    :param end_index: 处理的结束分号索引（如果为 None，则表示直到末尾）
    """
    os.makedirs(output_dir, exist_ok=True)  # 确保输出目录存在

    for filename in os.listdir(input_dir):
        if not (filename.endswith('.yaml') or filename.endswith('.txt')):
            continue

        input_file = os.path.join(input_dir, filename)
        output_file = os.path.join(output_dir, filename)

        with open(input_file, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()

        processed_data = []
        processing = False  # 标志是否进入了『正文区』（包含中文）

        for raw_line in lines:
            line = raw_line.rstrip('\n')  # 去掉行尾换行，不去空格是怕有些词典在行尾故意留空

            # 若尚未进入正文区，检查是否含中文。有则标记处理区开始。
            if not processing and any('\u4e00' <= ch <= '\u9fff' for ch in line):
                processing = True

            # 如果尚未进入正文区或该行内容不足以分成 2 列以上，原样输出
            # （比如开头注释、yaml 配置段等）
            if not processing:
                processed_data.append(line)
                continue

            # 进入正文区，先尝试分割为 3 列：字（或词）、拼音/编码、频率/注释
            parts = line.split('\t')

            # 若分割后不足 2 列，说明格式也不符合字、拼音的基本格式，直接原样保留
            if len(parts) < 2:
                processed_data.append(line)
                continue

            # 如果只有 2 列，则补上一个空字符串当第三列
            if len(parts) == 2:
                parts.append("")
            # 如果超过 3 列，则将第 3 列起的内容都合并到第三列（也可做别的更细致的处理）
            elif len(parts) > 3:
                parts = [parts[0], parts[1], "\t".join(parts[2:])]

            # parts 现一定有 3 列
            chinese_part = parts[0]
            rime_data = parts[1]  # 拼音或编码列
            other_parts = parts[2]  # 第三列（频率或注释）

            # 以「空格」拆分多个编码组，如 "zhong;zong zhong;chong"
            rime_groups = rime_data.split(' ')

            new_rime_groups = []
            for group in rime_groups:
                # 按分号切分该组
                segments = group.split(';')

                # 如果希望多余的索引也能用空字符串补足，那么：
                needed_end_index = end_index if end_index is not None else len(segments)
                # 取「比较大的值」，否则当 end_index 大于实际段数时会越界
                max_needed = max(needed_end_index, start_index+1)  # 确保至少能取到 start_index

                if len(segments) < max_needed:
                    # 不足就用空字符串补齐
                    segments += [''] * (max_needed - len(segments))

                # 现在 segments 至少有 max_needed 个元素
                # 截取 [start_index, end_index)
                if end_index is None:
                    # 若 end_index=None，就直接切到结尾
                    extracted = segments[start_index:]
                else:
                    extracted = segments[start_index:end_index]

                # 这时 extracted 可能全是空字符，也可能部分有值
                # 再拼回
                new_group = ';'.join(extracted)

                # 如果你想「保留 segments[0] 并将截取的追加到后面」，可改为：
                #   new_group = segments[0]
                #   if extracted:
                #       new_group += ';' + ';'.join(extracted)
                #
                # 这里示范：直接使用 [start_index,end_index) 那几段当结果
                new_rime_groups.append(new_group)

            # 将处理完成的各组，用空格拼回
            new_rime_data = ' '.join(new_rime_groups)

            # 最终三列合成一行
            result_line = '\t'.join([chinese_part, new_rime_data, other_parts])
            processed_data.append(result_line)

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as outfile:
            for item in processed_data:
                outfile.write(item + '\n')


if __name__ == "__main__":
    # 假设有多组 [start_index, end_index)，分别输出到不同目录演示
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

    input_dir = 'cn_dicts'  # 你的输入目录

    for start_idx, end_idx, out_dir in index_mapping:
        process_rime_dicts(
            input_dir=input_dir,
            output_dir=out_dir,
            start_index=start_idx,
            end_index=end_idx
        )

    print("全部处理完成！")
