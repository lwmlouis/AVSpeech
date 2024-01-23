import csv
import yt_dlp


class VidInfo:
    def __init__(self, id: str, start: float, end: float, face_x: float, face_y: float):
        self.id = id
        self.start = float(start)
        self.end = float(end)
        self.face_x = float(face_x)
        self.face_y = float(face_y)

    def __str__(self):
        return f'{self.id},{self.start},{self.end}, {self.face_x},{self.face_y}'


if __name__ == '__main__':
    vidInfos = {}
    with open('../data/avspeech_train.csv', 'r') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if i > 2:
                break
            vi = VidInfo(*row)
            vidInfos[vi.id] = vi

    URLS = [f'https://www.youtube.com/watch?v={vi.id}' for vi in vidInfos.values()]

    data_dir = '../data/avspeech/train'


    def download_range_callback(info, ydl):
        print(info['id'])

        return [{
            'start_time': vidInfos[info['id']].start,
            'end_time': vidInfos[info['id']].end
        }]


    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': f'{data_dir}/%(id)s.%(ext)s',
        # 'simulate': True,
        'ignoreerrors': True,
        'download_ranges': download_range_callback,
        'proxy': 'http://127.0.0.1:10809'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        er = ydl.download(URLS)
