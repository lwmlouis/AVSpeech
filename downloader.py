import os
from pathlib import Path
from typing import Optional

import yt_dlp
from humanize import naturalsize
from pandas import read_csv


def get_size(start_path='.'):
    root_dir = Path(start_path)

    return sum(f.stat().st_size for f in root_dir.glob('**/*.mp4'))


class Downloader:
    def __init__(self, csv_pth, download_dir, proxy='http://127.0.0.1:10809',
                 limit_size: Optional[int] = None, slice: Optional[list[int, int]] = None):
        '''
        Args:
            csv_pth:
            download_dir:
            proxy:
            limit_size: 下载大小限制，单位GB
            slice: csv视频数量区间
        '''
        self.download_dir = download_dir
        self.current_size = get_size(download_dir)
        self.limit_size = limit_size  # GB

        self.df = read_csv(csv_pth, header=None, names=['id', 'start_time', 'end_time', 'x', 'y'],
                           index_col='id')
        if slice is not None:
            self.df = self.df[slice[0]:slice[1]]

        self.ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': f'{download_dir}/%(id)s/%(section_start)d_%(section_end)d.%(ext)s',
            'ignoreerrors': True,
            'download_ranges': lambda info, _: self.df.loc[[info['id']], ['start_time', 'end_time']].to_dict('records'),
            'proxy': proxy
        }

    def download(self):
        grouped = self.df.groupby('id')
        # 每次下载同一个视频不同片段
        for vid, group in grouped:
            if os.path.exists(f'{self.download_dir}/{vid}'):
                continue

            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([f'https://www.youtube.com/watch?v={vid}'])

            self.current_size += get_size(f'{self.download_dir}/{vid}')

            if self.limit_size is not None and self.current_size > self.limit_size * 1024 ** 3:
                break


def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')


def get_ydl_opts_vid(path):
    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]',
        'outtmpl': u'{}.%(ext)s'.format(path),
        'noplaylist': True,
        'progress_hooks': [my_hook],
        '--proxy': 'socks5://127.0.0.1:19180'
    }
    return ydl_opts


def get_ydl_opts_aud(path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': u'{}.%(ext)s'.format(path),
        'noplaylist': True,
        'progress_hooks': [my_hook],
        '--proxy': 'socks5://127.0.0.1:19180',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192'}]
    }
    return ydl_opts


def download(video_id, video_result_path, audio_result_path):
    print('donwloader..')
    with yt_dlp.YoutubeDL(get_ydl_opts_vid(video_result_path)) as ydl:
        ydl.download(['https://www.youtube.com/watch?v=' + video_id])

    with yt_dlp.YoutubeDL(get_ydl_opts_aud(audio_result_path)) as ydl:
        ydl.download(['https://www.youtube.com/watch?v=' + video_id])


if __name__ == '__main__':
    downloader = Downloader('./test/test.csv', './test',
                            proxy='http://127.0.0.1:13957')

    downloader.download()

    print(naturalsize(downloader.current_size))
