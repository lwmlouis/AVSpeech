import moviepy.editor as mpy
import numpy as np
import librosa

'''这段代码的功能是从一个视频文件和一个音频文件中截取一段指定的时间区间，并保存为新的视频文件，音频文件和numpy数组。代码的分析如下：
- 首先，导入了三个Python库：moviepy，numpy和librosa。这些库分别用于视频编辑，科学计算和音乐分析。
- 然后，定义了一个名为cut的函数，它有八个参数：
    - full_video_path: 原始视频文件的路径，例如"video.mp4"。
    - cut_video_path: 截取后的视频文件的路径，例如"video_cut.mp4"。
    - full_audio_path: 原始音频文件的路径，例如"audio.wav"。
    - cut_audio_path: 截取后的音频文件的路径，例如"audio_cut.wav"。
    - start_t: 截取的开始时间，以秒为单位，例如10。
    - end_t: 截取的结束时间，以秒为单位，例如20。
    - sr: 音频的采样率，以赫兹为单位，例如44100。
    - np_path: 保存音频数据的numpy数组的路径，例如"audio.npy"。
- 接下来，函数的主体部分分为三个步骤：
    - 第一步，使用moviepy的VideoFileClip类打开原始视频文件，并用subclip方法截取指定的时间区间，然后用write_videofile方法保存为新的视频文件。
    - 第二步，使用librosa的load函数加载原始音频文件，并指定采样率，偏移量和持续时间，得到一个一维的numpy数组y，表示音频的波形数据。然后用librosa的output.write_wav函数保存为新的音频文件。
    - 第三步，使用numpy的save函数将音频的波形数据y保存
'''
def cut(full_video_path, cut_video_path, full_audio_path, cut_audio_path, start_t, end_t, sr, np_path):
    # Cut video
    with mpy.VideoFileClip(full_video_path) as myclip:
        # myclip = mpy.VideoFileClip(full_video_path)
        subclip = myclip.subclip(start_t, end_t)
        subclip.write_videofile(cut_video_path)

    # Cut audio
    duration = end_t - start_t
    y, _ = librosa.load(full_audio_path, sr, offset=start_t, duration=duration)
    librosa.output.write_wav(cut_audio_path, y, sr)

    # Save audio as numpy
    np.save(np_path, y)

