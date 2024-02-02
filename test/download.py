import yt_dlp
from pandas import read_csv

if __name__ == '__main__':
    df = read_csv('./test.csv', header=None, names=['id', 'start_time', 'end_time', 'x', 'y'],
                  index_col='id')

    data_dir = '.'

    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': f'{data_dir}/%(id)s/%(section_start)d_%(section_end)d.%(ext)s',
        # 'simulate': True,
        'ignoreerrors': True,
        'download_ranges': lambda info, _: df.loc[[info['id']], ['start_time', 'end_time']].to_dict('records'),
        'proxy': 'http://127.0.0.1:13957'
    }

    grouped = df.groupby('id')
    for vid, group in grouped:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'https://www.youtube.com/watch?v={vid}'])
