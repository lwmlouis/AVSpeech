import yt_dlp
from pandas import read_csv


class Downloader:
    def __init__(self, csv_pth, download_dir, proxy='http://127.0.0.1:10809'):
        self.df = read_csv(csv_pth, header=None, names=['id', 'start_time', 'end_time', 'x', 'y'],
                           index_col='id')

        self.ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': f'{download_dir}/%(id)s/%(autonumber)d.%(ext)s',
            'ignoreerrors': True,
            'download_ranges': lambda info, _: self.df.loc[[info['id']], ['start_time', 'end_time']].to_dict('records'),
            'proxy': proxy
        }

    def download(self):
        grouped = self.df.groupby('id')
        for vid, group in grouped:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([f'https://www.youtube.com/watch?v={vid}'])


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
