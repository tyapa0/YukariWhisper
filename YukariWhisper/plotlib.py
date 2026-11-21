#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider


class _CloseSafeFuncAnimation(FuncAnimation):
    def _step(self, *args):
        if not hasattr(self._fig.canvas, "restore_region"):
            return False
        return super()._step(*args)
class WaveformPlot:
    """Real-time microphone waveform with an amplitude slider.

    ``on_amp_changed`` is called with the slider value (1.0 - amp_max) whenever
    the user moves the Amp slider; the caller decides what to do with it.
    ``amp_max`` / ``amp_default`` come from yukariwhisper.ini ([RECOGNIZER]
    amp_max / amp_default); the slider starts at ``amp_default``.
    """

    def __init__(self, sample_rate=16000, downsample=10, on_amp_changed=None,
                 amp_max=5.0, amp_default=1.0):
        self.sample_rate = sample_rate
        self.downsample = downsample
        # settings 側でも補正済みだが、直接生成された場合でも
        # Slider の範囲 (下限 1.0 ～ amp_max) と初期値が矛盾しないようここでも丸める。
        self.amp_max = max(1.0, float(amp_max))
        self.amp_default = min(max(1.0, float(amp_default)), self.amp_max)

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
            slider_amp_pos, 'Amp', 1.0, self.amp_max,
            valstep=0.1, valinit=self.amp_default, orientation="vertical",
        )
        if on_amp_changed is not None:
            self.amp_slider.on_changed(on_amp_changed)

        self._animation = None
        self._is_speech = None  # set_speech の前回値 (色の変更要否の判定用)

    # マイク入力1チャンク分を波形バッファへ追加する
    # indata.shape = (n_samples, n_channels)
    def push(self, indata):
        data = indata[::self.downsample, 0]
        shift = len(data)
        self.plotdata = np.roll(self.plotdata, -shift, axis=0)
        self.plotdata[-shift:] = data

    # 発話中はマゼンタ、無音時はグレーに線の色を変える
    # 色が変わるときだけ set_color する 
    def set_speech(self, is_speech):
        is_speech = bool(is_speech)
        if is_speech != self._is_speech:
            self._is_speech = is_speech
            self.line.set_color("m" if is_speech else "gray")

    def update_plot(self, frame):
        """This is called by matplotlib for each plot update."""
        self.line.set_ydata(self.plotdata)
        return self.line,

    # 描画アニメーションを開始
    # interval(更新間隔) は ms単位
    def start_animation(self, interval=50):
        self._animation = _CloseSafeFuncAnimation(
            self.fig, self.update_plot,
            interval=interval, blit=True, cache_frame_data=False,
        )
        return self._animation

    # ウインドウを表示して閉じられるまでブロックする
    def show(self):
        plt.show()
