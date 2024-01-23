import os
import csv
import cv2
import glob
import argparse
import subprocess
from downloader import download
from cutter import cut
from cropper import crop_face


parser = argparse.ArgumentParser()
parser.add_argument('--csv_dir', default='./data_csv')
parser.add_argument('--result_dir', default='./result')
parser.add_argument('--start', default=0, type=int)
parser.add_argument('--end', default=6, type=int)
parser.add_argument('--sr', default=16000)
parser.add_argument('--fourcc', default='avc1')  # In ubuntu, use mp4v for mp4.
parser.add_argument('--crop_ext', default='mp4')
parser.add_argument('--crop_size', default=224)
parser.add_argument('--fps', default=25.0, type=float)
args = parser.parse_args()

all_csv = sorted(glob.glob(os.path.join(args.csv_dir, '*.csv')))
'''这段代码是用来找到指定目录下的所有CSV文件，并按照文件名排序的。它使用了`glob`模块和`os`模块，具体解释如下：

- `glob.glob(pattern)`是一个函数，它返回一个列表，包含了所有符合`pattern`参数的文件路径。`pattern`参数是一个字符串，可以使用通配符`*`和`?`来匹配任意字符或单个字符。例如，`*.csv`表示匹配所有以`.csv`结尾的文件。
- `os.path.join(path, *paths)`是一个函数，它返回一个字符串，表示将多个路径拼接在一起。它会根据操作系统的不同，自动添加合适的分隔符。例如，`os.path.join('a', 'b', 'c')`在Windows系统下返回`'a\\b\\c'`，在Linux系统下返回`'a/b/c'`。
- `args.csv_dir`是一个变量，它的值是一个字符串，表示CSV文件所在的目录。它是通过`argparse`模块从命令行参数获取的。
- `sorted(iterable)`是一个函数，它返回一个列表，表示将`iterable`参数中的元素按照一定的顺序排序。`iterable`参数可以是任何可迭代的对象，如列表，元组，字符串等。如果没有指定排序的规则，它会按照默认的升序排序。例如，`sorted([3, 1, 4, 2])`返回`[1, 2, 3, 4]`。

综上，这段代码的作用是，首先使用`os.path.join(args.csv_dir, '*.csv')`构造一个字符串，表示匹配`args.csv_dir`目录下的所有CSV文件。然后使用`glob.glob`函数根据这个字符串，找到所有符合条件的文件路径，并返回一个列表。最后使用`sorted`函数对这个列表进行排序，并赋值给`all_csv`变量。
'''
cut_video_dir = os.path.join(args.result_dir, 'original', 'video_cut')
full_video_dir = os.path.join(args.result_dir, 'original', 'video_full')
cut_audio_dir = os.path.join(args.result_dir, 'original', 'audio_cut')
full_audio_dir = os.path.join(args.result_dir, 'original', 'audio_full')
cropped_dir = os.path.join(args.result_dir, 'original', 'cropped')
audio_np_dir = os.path.join(args.result_dir, 'numpy', 'audio')
dummy_dir = os.path.join(args.result_dir, 'dummy')

os.makedirs(args.result_dir, exist_ok=True)
os.makedirs(cut_video_dir, exist_ok=True)
os.makedirs(full_video_dir, exist_ok=True)
os.makedirs(cut_audio_dir, exist_ok=True)
os.makedirs(full_audio_dir, exist_ok=True)
os.makedirs(cropped_dir, exist_ok=True)
os.makedirs(audio_np_dir, exist_ok=True)
os.makedirs(dummy_dir, exist_ok=True)

all_id = []
all_start = []
all_end = []
all_x = []
all_y = []

fail_cnt = 0
done_cnt = 0
skipped_cnt = 0

# Read all CSV
for c in all_csv:
    with open(c, 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        for col in csv_reader:
            all_id.append(col[0])
            all_start.append(float(col[1]))
            all_end.append(float(col[2]))
            all_x.append(float(col[3]))
            all_y.append(float(col[4]))

print('Sorting..')
zipped = zip(all_id, all_start, all_end, all_x, all_y)
zipped = sorted(zipped)
all_id, all_start, all_end, all_x, all_y = zip(*zipped)

'''这段代码是用来将几个列表（all_id, all_start, all_end, all_x, all_y）按照相同的顺序排序的。它使用了`zip`和`sorted`两个内置函数，具体解释如下：

- `zip(*iterables)`是一个函数，它接受任意个可迭代对象（如列表，元组，字符串等）作为参数，返回一个迭代器，每次生成一个元组，包含每个可迭代对象的对应位置的元素。例如，`zip([1, 2, 3], ['a', 'b', 'c'])`返回一个迭代器，每次生成`(1, 'a')`，`(2, 'b')`，`(3, 'c')`。
- `sorted(iterable)`是一个函数，它接受一个可迭代对象作为参数，返回一个列表，表示将可迭代对象中的元素按照一定的顺序排序。如果没有指定排序的规则，它会按照默认的升序排序。例如，`sorted([3, 1, 4, 2])`返回`[1, 2, 3, 4]`。

综上，这段代码的作用是，首先使用`zip(all_id, all_start, all_end, all_x, all_y)`将五个列表打包成一个迭代器，每次生成一个包含五个元素的元组。然后使用`sorted(zipped)`对这个迭代器进行排序，根据每个元组的第一个元素（即all_id中的元素）进行升序排序。最后使用`zip(*zipped)`将排序后的迭代器拆分成五个列表，并赋值给`all_id, all_start, all_end, all_x, all_y`变量。👍

'''

# Check already processed number of data
cnt_path = os.path.join(dummy_dir, 'processed_cnt.txt')
if os.path.exists(cnt_path):
    with open(cnt_path, 'r') as f:
        processed_cnt = int(f.readline())
else:
    with open(cnt_path, 'w') as f:
        f.write('0')
    processed_cnt = 0

all_id = all_id[args.start + processed_cnt:args.end]
all_start = all_start[args.start + processed_cnt:args.end]
all_end = all_end[args.start + processed_cnt:args.end]
all_x = all_x[args.start + processed_cnt:args.end]
all_y = all_y[args.start + processed_cnt:args.end]

prev_id = None
for i in range(len(all_id)):
    id, start, end, x, y = all_id[i], all_start[i], all_end[i], all_x[i], all_y[i]
    print('================== Progress: [{}/{}],  ID:{} =================='.format(i+1, len(all_id), id))
    id_dur = id + '_' + str(int(start)) + '_' + str(int(end))
    id_dur_crop_ext = id_dur + '.' + args.crop_ext
    id_dur_npy = id_dur + '.npy'
    cut_audio_path = os.path.join(cut_audio_dir, id_dur)
    cut_audio_path_ext = cut_audio_path + '.wav'
    full_audio_path = os.path.join(full_audio_dir, id)
    full_audio_path_ext = full_audio_path + '.wav'
    cut_video_path = os.path.join(cut_video_dir, id_dur)
    cut_video_path_ext = cut_video_path + '.mp4'
    full_video_path = os.path.join(full_video_dir, id)
    full_video_path_ext = full_video_path + '.mp4'
    cropped_path = os.path.join(cropped_dir, id_dur_crop_ext)
    audio_np_path = os.path.join(audio_np_dir, id_dur_npy)

    try:
        if id != prev_id and prev_id is not None:
            print('Delete full video, id:', prev_id)
            prev_id_wav = prev_id + '.wav'
            prev_id_mp4 = prev_id + '.mp4'
            prev_audio_full = os.path.join(full_audio_dir, prev_id_wav)
            prev_video_full = os.path.join(full_video_dir, prev_id_mp4)
            if os.path.exists(prev_audio_full):
                os.remove(prev_audio_full)
            if os.path.exists(prev_video_full):
                os.remove(prev_video_full)
        prev_id = id
        # Download full video and audio
        download(id, full_video_path, full_audio_path)

        # Cut out target portion of video and audio
        # Also, save audio as numpy
        cut(full_video_path_ext, cut_video_path_ext,
            full_audio_path_ext, cut_audio_path_ext,
            start, end, args.sr, audio_np_path)

        vc = cv2.VideoCapture(cut_video_path_ext)

        # If FPS is not 25, resample video.
        if vc.get(cv2.CAP_PROP_FPS) != args.fps:
            print('Resample video..')
            fps_int = int(args.fps)
            resample_command = 'ffmpeg -y -i ' + cut_video_path_ext + \
                               ' -r ' + str(fps_int) + \
                               ' -c:v libx264 -b:v 3M -strict -2 -movflags faststart ' \
                               + cut_video_path + '_resampled.mp4'
            subprocess.call(resample_command, shell=True)

            os.remove(cut_video_path_ext)
            os.rename(cut_video_path + '_resampled.mp4', cut_video_path_ext)
            vc.release()
            vc = cv2.VideoCapture(cut_video_path_ext)

        fourcc = cv2.VideoWriter_fourcc(*args.fourcc)
        vid_writer = cv2.VideoWriter(cropped_path,
                                     fourcc,
                                     args.fps,
                                     (args.crop_size, args.crop_size))
        # Crop target face
        is_cropped = crop_face(vc, x, y, vid_writer)
        vc.release()
        vid_writer.release()
        if is_cropped:
            done_cnt += 1
        else:
            print('Skipped:', cropped_path)
            print('REMOVE ALL RELAVANT FILE to', id_dur)
            skipped_cnt += 1
            all_relavant = glob.glob(os.path.join(args.result_dir, '*', '*', id_dur + '*'))
            for f in all_relavant:
                os.remove(f)
    except Exception as e:
        print('[!][!][!][!][!][!][!][!][!][!][!][!][!][!][!]')
        print('FAIL. SOMTHING WRONG. ex) Fail to download.')
        print(e)
        print('REMOVE ALL RELAVANT FILE to', id_dur)
        fail_cnt += 1
        all_relavant = glob.glob(os.path.join(args.result_dir, '*', '*', id_dur + '*'))
        for f in all_relavant:
            os.remove(f)

    # Add count
    with open(cnt_path, 'r') as f:
        cnt = int(f.readline())
    with open(cnt_path, 'w') as f:
        cnt += 1
        f.write(str(cnt))

with open(cnt_path, 'w') as f:
    f.write('0')

print('Done')
print('..')
print('..')
print('========= RESULT =========')
print('Total video:', len(all_id))
print('Preprocessed video:', done_cnt)
print('Failed video:', fail_cnt)
print('Skipped video:', skipped_cnt)
