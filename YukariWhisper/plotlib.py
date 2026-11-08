#!/usr/bin/env python3
"""Waveform window for YukariWhisper (matplotlib).

This module was split out of recognizer.py: it owns everything that draws -
the rolling waveform buffer, the line colour that shows whether the VAD
heard speech, the amplitude slider and the FuncAnimation.

recognizer.py only has to
    * call ``push(indata)`` for every microphone callback,
    * call ``set_speech(bool)`` with the VAD result,
    * call ``start_animation()`` once and ``show()`` to run the window.

Nothing in here knows about speech recognition.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider


class WaveformPlot:
    """Real-time microphone waveform with an amplitude slider.

    ``on_amp_changed`` is called with the slider value (1.0 - 5.0) whenever
    the user moves the Amp slider; the caller decides what to do with it.
    """

    def __init__(self, sample_rate=16000, downsample=10, on_amp_changed=None):
        self.sample_rate = sample_rate
        self.downsample = downsample

        # 表示する波形データ (1秒分をダウンサンプルして保持する)
        length = int(1000 * self.sample_rate / (1000 * self.downsample))
        self.plotdata = np.zeros((length))

        # plots_set
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot(self.plotdata)
        self.ax.set_ylim([-1.0, 1.0])
        self.ax.set_xlim([0, length])
        self.ax.yaxis.grid(True)
        self.fig.tight_layout()

        # sliderの作成
        plt.subplots_adjust(right=0.9)
        slider_amp_pos = self.fig.add_axes([0.91, 0.12, 0.05, 0.81])
        self.amp_slider = Slider(
            slider_amp_pos, 'Amp', 1.0, 5.0,
            valstep=0.1, valinit=1.0, orientation="vertical",
        )
        if on_amp_changed is not None:
            self.amp_slider.on_changed(on_amp_changed)

        self._animation = None

    # マイク入力1チャンク分を波形バッファへ追加する
    # indata.shape = (n_samples, n_channels)
    def push(self, indata):
        data = indata[::self.downsample, 0]
        shift = len(data)
        self.plotdata = np.roll(self.plotdata, -shift, axis=0)
        self.plotdata[-shift:] = data

    # 発話中はマゼンタ、無音時はグレーに線の色を変える
    def set_speech(self, is_speech):
        self.line.set_color("m" if is_speech else "gray")

    def update_plot(self, frame):
        """This is called by matplotlib for each plot update."""
        self.line.set_ydata(self.plotdata)
        return self.line,

    # 描画アニメーションを開始する (show() の前に呼ぶ)
    def start_animation(self, interval=30):
        self._animation = FuncAnimation(
            self.fig, self.update_plot,
            interval=interval, blit=True, cache_frame_data=False,
        )
        return self._animation

    # ウインドウを表示して閉じられるまでブロックする
    def show(self):
        plt.show()
