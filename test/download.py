from pandas import read_csv
from os.path import basename, splitext

import yt_dlp


# 记录下载成功视频id
def download_callback(d):
    if d['status'] == 'finished':
        with open('../data/train.txt', 'a') as f:
            f.write(splitext(basename(d['filename']))[0] + '\n')


if __name__ == '__main__':
    df = read_csv('../avspeech_train.csv', header=None, names=['id', 'start_time', 'end_time', 'x', 'y'],
                  index_col='id')


    def download_ranges_callback(info, ydl):
        vid = info['id']

        # [vid]避免单行数据被转换为Series
        return df.loc[[vid]].apply(lambda row: {
            'start_time': row['start_time'],
            'end_time': row['end_time']
        }, axis=1).tolist()


    data_dir = '../data/train'

    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': f'{data_dir}/%(id)s/%(autonumber)d.%(ext)s',
        # 'simulate': True,
        'ignoreerrors': True,
        'download_ranges': download_ranges_callback,
        'proxy': 'http://127.0.0.1:10809'
    }

    grouped = df.groupby('id')
    for vid, group in grouped:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'https://www.youtube.com/watch?v={vid}'])
