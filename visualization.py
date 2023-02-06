from multiprocessing import Pipe

import matplotlib.pyplot as plt


class ScanPlotter:
    font_sizes = {
        'axis': 22,
        'title': 26,
        'ticks': 15,
        'legend': 16
    }

    Y_MARGIN = 0.05

    @staticmethod
    def terminate():
        plt.close('all')

    def update_plot(self):
        while self.pipe.poll():
            df = self.pipe.recv()
            if df is None:
                self.terminate()
                return False
            else:
                self.axs[0].plot(df.index, df.iloc[:, 1], 'r-', label='Detector 2')

                if df.shape[0] == 1:
                    continue

                self.axs[0].set_xlim([df.index[0], df.index[-1]])
                # self.axs[0].set_ylim([0 - self.Y_MARGIN * max(df.iloc[1]), max(df.iloc[1]) * (1 + self.Y_MARGIN)])
                # self.axs[1].plot(df.index, df.iloc[:, 1], 'r-')
                # self.axs[1].set_xlim([df.index[0], df.index[-1]])
        self.figure.canvas.draw()
        return True

    def __call__(self, pipe: Pipe, scan_mode: str, scales: dict):
        self.pipe = pipe
        self.figure = plt.figure(figsize=(10, 8))
        self.axs = []
        self.axs.append(self.figure.add_subplot(1, 1, 1))

        self.axs[0].set_title(scan_mode, fontsize=self.font_sizes['title'])
        self.axs[0].set_ylabel(scales['y_scale'], fontsize=self.font_sizes['axis'])
        self.axs[0].set_xlabel(scales['x_scale'], fontsize=self.font_sizes['axis'])
        self.axs[0].grid(True, linestyle='--')

        self.axs[0].plot([], [], 'r-', label='Detector 2')
        self.axs[0].legend(fontsize=self.font_sizes['legend'])

        plt.xticks(fontsize=self.font_sizes['ticks'])
        plt.yticks(fontsize=self.font_sizes['ticks'])

        timer = self.figure.canvas.new_timer(interval=100)
        self.figure.canvas.set_window_title(f'RSM-controller: {scan_mode}')
        timer.add_callback(self.update_plot)
        timer.start()

        plt.show()
