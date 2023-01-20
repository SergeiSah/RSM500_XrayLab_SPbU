from multiprocessing import Pipe

import matplotlib.pyplot as plt


class Plotter:
    labels = {
        'en_scan': {'x_scale': 'Revs of the reel', 'y_scale': 'Counts'}
    }

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
                self.axs[0].plot(df.iloc[:, 0], df.iloc[:, 1], 'r-')
                self.axs[1].plot(df.iloc[:, 0], df.iloc[:, 2], 'r-')
        self.fig.canvas.draw()
        return True

    def __call__(self, pipe: Pipe, scan_mode: str):
        self.pipe = pipe
        # names = self.labels[scan_mode]

        self.fig, self.axs = plt.subplots(nrows=2, ncols=1)

        self.axs[0].set_title('Detector 1')
        # self.axs[0].set_ylabel(names['y_label'])
        self.axs[1].set_title('Detector 2')
        # self.axs[1].set_xlabel(names['x_label'])

        timer = self.fig.canvas.new_timer(interval=100)
        timer.add_callback(self.update_plot)
        timer.start()

        plt.show()
