'''
    magma 并行重放统计crash工具, 针对并行实验
'''

import argparse
import concurrent.futures
import glob
import itertools
import os
import subprocess
from collections import defaultdict


# 根据采样间时间隔将 seed_dir 下的种子进行分组
def generate_seed_group(seed_dir):
    global start_time

    files = glob.glob(os.path.join(seed_dir, 'id:*'))
    orig_files = [file for file in files if ',orig:' in file]
    files = [file for file in files if ',orig:' not in file]
    print(f"{len(orig_files)} origin + {len(files)} seeds")

    sample_gap = 5  # second, default poll in magma
    if start_time == -1:
        cmdline_file = os.path.normpath(os.path.join(seed_dir, "../cmdline"))
        start_time = os.stat(cmdline_file).st_mtime

    if not files:  # crash 和 hangs 可能没有种子
        return [[] for _ in range(int(24 * 60 * 60 / sample_gap))]

    file_info = []
    for file in files:
        # ctime = os.stat(file).st_ctime  # 获取创建时间
        ctime = os.stat(file).st_mtime  # 获取修改时间
        file_info.append((ctime, file))
    file_info_sorted = sorted(file_info, key=lambda x: x[0])

    current_time = start_time
    arr_off = 0
    end_time = current_time + sample_gap

    file_group = [[]]

    # 初始种子不要
    group_id = 0
    file_group.append([])
    while arr_off < len(file_info_sorted):
        ctime, file = file_info_sorted[arr_off]

        if ctime <= end_time:
            file_group[group_id].append(file)
            arr_off += 1
        else:
            end_time += sample_gap
            group_id += 1
            file_group.append([])

    # 少补齐，多截断
    target_len = int(24 * 60 * 60 / sample_gap)
    if len(file_group) < target_len:
        while len(file_group) < target_len:
            file_group.append([])
    else:
        file_group = file_group[:target_len]

    return file_group


def magma_runonce(test_case):
    """get magma crash info on a single test case."""
    # /magma_out/monitor --fetch watch --dump human /path/runonce.sh /seed

    # 执行目标程序并生成漏洞信息。不能并行，没有加锁
    command_run_program = [
        "/magma_out/monitor",
        "--fetch",
        "watch",
        "--dump",
        "row",
        "/replay/runonce.sh", # dockerfile中指定
        test_case  # 测试用例文件
    ]

    # 捕获输出并解析
    try:
        # print(command_run_program)
        result = subprocess.run(command_run_program, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        output = result.stdout  # 获取标准输出内容

        # 假设输出是以特定格式返回的，例如：PNG003_R,PNG003_T,PNG001_R,PNG001_T,PNG005_R,PNG005_T,PNG007_R,PNG007_T
        # 1,0,1,0,1,0,1,1
        header_line = output.splitlines()[0]  # 第一行是列名
        value_line = output.splitlines()[1]  # 第二行是值

        keys = header_line.split(',')
        values = list(map(int, value_line.split(",")))

        return zip(keys, values)

    except subprocess.CalledProcessError as e:
        print(f"Error running program: {e}")
        return None
    except subprocess.TimeoutExpired as e:
        print(f"Timeout expired while running program for {test_case}")
        return None


def grouped_crash_info_by_time(seeds, thread=1):
    with concurrent.futures.ThreadPoolExecutor(max_workers=thread) as executor:
        futures = []
        for t_id, test_case in enumerate(seeds):
            futures.append(
                executor.submit(magma_runonce, test_case))
        # 进度
        total = len(futures)
        finished = 0
        for future in concurrent.futures.as_completed(futures):
            zip_ = future.result()  # 获取执行结果
            for k, v in zip_:  # 计数
                cur_crash_info[k] += v
            finished = finished + 1
            print(f"  Progress: {finished} / {total}", end='\r')


def get_all_instance_seeds(out_dir):
    result = []
    instance_list = []

    # 汇总所有实例
    for dir_name in os.listdir(out_dir):
        dir_path = os.path.join(out_dir, dir_name)
        # 排除当前目录
        if os.path.isdir(dir_path):
            instance_list.append(dir_path)

    for instance_out_dir in instance_list:
        print(f"  [*] {instance_out_dir}")
        queue_path = os.path.join(instance_out_dir, 'queue')
        hangs_path = os.path.join(instance_out_dir, 'hangs')
        crash_path = os.path.join(instance_out_dir, 'crashes')
        print(f"    [-] queue\t", end="")
        queue_group = generate_seed_group(queue_path)
        print(f"    [-] hangs\t", end="")
        hangs_group = generate_seed_group(hangs_path)
        print(f"    [-] crashes\t", end="")
        crash_group = generate_seed_group(crash_path)
        print(f'[group num] seeds:{len(queue_group)}, hangs:{len(hangs_group)}, crashes:{len(crash_group)}')

        # 对齐种子group数量
        len_h = len(hangs_group)
        len_c = len(crash_group)
        while len_h < len(queue_group):
            hangs_group.append([])  # 添加一个空列表
            len_h += 1
        while len_c < len(queue_group):
            crash_group.append([])  # 添加一个空列表
            len_c += 1

        # 合并列表
        merged_list = [list(itertools.chain(*pair)) for pair in zip(queue_group, hangs_group, crash_group)]

        # 将 results 和 merged_list 合并为一个新的二重列表
        if result == []:
            result = merged_list
        else:
            result = [list(itertools.chain(*pair)) for pair in zip(result, merged_list)]

    return result


work_dir = ''
cur_crash_info = {}
start_time = -1

program_to_harness = {
    "libpng": "libpng_read_fuzzer",
    "libtiff": "tiff_read_rgba_fuzzer",
    "lua": "lua",
    "libxml2": "xmllint",
    "libsndfile": "sndfile_fuzzer",
    "openssl": "server",
    "sqlite3": "sqlite3_fuzz",
    "poppler": "pdf_fuzzer",
    "php": "parser"
}



def main():
    global work_dir  # 声明全局变量
    global cur_crash_info

    """解析用户输入的命令行参数"""
    parser = argparse.ArgumentParser(description="Coverage Statistics Automation Tool")
    parser.add_argument('--threads', type=int, required=True,
                        help='执行并行数 (e.g. --threads=10)')
    parser.add_argument(
        '--workdir', type=str, required=True,
        help="path to magma worker dir (e.g., --experiment_out_dircabs ./workdir)"
    )
    parser.add_argument(
        '--experiment_out_dirs',
        type=str,
        nargs='+',
        required=True,
        help="List of absolute paths for experiment output directories (e.g., --experiment_out_dircabs /path1 /path2)"
    )

    args = parser.parse_args()

    threads = args.threads
    experiment_out_dirs = args.experiment_out_dirs
    workdir = args.workdir

    cur_crash_info = defaultdict(int)
    for out_dir in experiment_out_dirs:
        start_time = -1  # 每一轮实验

        print(f'[+] process {out_dir} ...')
        # 构建 monitor 路径  eg. /workdir/ar/aflplusplus/libpng/fuzzer_png/0/monitor/
        # 获取轮数id, 注意实验文件夹命名格式
        folder_name = os.path.basename(os.path.normpath(out_dir)).split('-')
        exp_cycle_id = folder_name[0]
        fuzzer = folder_name[1]
        target = folder_name[2]
        harness = program_to_harness[target]
        monitor_dir = os.path.join(workdir,"ar",fuzzer,target,harness,exp_cycle_id,"monitor")
        monitor_dir = os.path.normpath(monitor_dir)
        os.makedirs(monitor_dir, exist_ok=True)
        
        merged_list = get_all_instance_seeds(out_dir)

        for i in range(0, len(merged_list)):
            seeds = merged_list[i]
            if seeds:
                print(f'[*] process group {i}...')
                grouped_crash_info_by_time(seeds, thread=threads)
                time = (i + 1) * 5
                # print(f"   {dict(cur_crash_info)}")
                with open(os.path.join(monitor_dir, f"{time}"), "w") as f:
                    f.write(",".join(cur_crash_info.keys()) + "\n")
                    f.write(",".join(str(cur_crash_info[k]) for k in cur_crash_info.keys()) + "\n")
    print(dict(cur_crash_info))


if __name__ == '__main__':
    main()

# python3 /crash-replay.py --threads=1 --workdir /out/magma-wrokdir --experiment_out_dirs /out/aflplusplus/0-aflplusplus-libpng/

# {'PNG003_R': 64, 'PNG003_T': 0, 'PNG001_R': 65, 'PNG001_T': 1, 'PNG005_R': 64, 'PNG005_T': 0, 'PNG007_R': 64, 'PNG007_T': 64, 'PNG006_R': 3, 'PNG006_T': 0}
