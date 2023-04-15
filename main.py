"""
    Youtube player using mpv
"""
import curses
import threading
import json
import subprocess
import datetime
import textwrap
import types
import os


videos = None
daterange = None
refreshrate = 200


def get_videos(data):
    global videos
    videos = json.loads(
        data, object_hook=lambda d: types.SimpleNamespace(**d))


def set_date(**days):
    global daterange
    format = "%Y-%m-%d"
    range = datetime.datetime.today() - datetime.timedelta(days=days.get('days', 3))
    daterange = range.strftime(format)


class Menu:
    def __init__(self, title, videos):
        self.title = title
        self.videos = []
        self.selected = 0
        self.pos = 0
        self.count = 0

    def get_dimensions(self, stdscr):
        y, x = stdscr.getmaxyx()
        return y, x

    def set_colors(self, stdscr):
        curses.use_default_colors()
        for x, y in enumerate([curses.COLOR_RED,
                               curses.COLOR_GREEN,
                               curses.COLOR_YELLOW,
                               curses.COLOR_BLUE,
                               curses.COLOR_MAGENTA,
                               curses.COLOR_CYAN]):
            curses.init_pair(x, y, -1)

    def set_position(self, stdscr, y, x, *args, **kwargs):
        pass

    def list_options(self):
        for x in self.videos:
            print(x.title)

    def window(self, stdscr):
        global refreshrate
        curses.curs_set(0)
        stdscr.timeout(refreshrate)
        self.set_colors(stdscr)

        while True:
            y, x = self.get_dimensions(stdscr)
            stdscr.clear()
            stdscr.box()
            subwindow = self.create_subwindow(stdscr, y-5, x)
            thread = threading.Thread(self.display_videos(subwindow))
            thread.start()
            try:
                self.header(stdscr, x)
                self.footer(stdscr, y)
            except curses.error:
                pass
            thread.join()
            stdscr.refresh()
            try:
                c = stdscr.getch()
                if self.handle_input(c) == True:
                    break
            except KeyboardInterrupt:
                break
        curses.endwin()

    def create_subwindow(self, stdscr, y, x):
        try:
            subwin = stdscr.subwin(y-1, x-2, 4, 1)
            subwin.border(' ', ' ', 0, 0, ' ', ' ', ' ', ' ')
            subwin.refresh()
            return subwin
        except curses.error:
            pass

    def create_subpad(self, stdscr, y, x):
        try:
            subpad = stdscr.subpad(y-4, x-2, 2, 1)
            subpad.border(' ', ' ', 0, 0, ' ', ' ', ' ', ' ')
            subpad.refresh()
            return subpad
        except curses.error:
            pass

    def header(self, stdscr, x):
        stdscr.addstr(1, x//2-len(self.title)//2,
                      self.title, curses.color_pair(1))
        guide_text = "Use Up and Down arrow keys to navigate, Enter to select"
        stdscr.addstr(3, 3, guide_text, curses.color_pair(4))

    def footer(self, stdscr, y):
        text = "Press 'q' or Ctrl+C to exit"
        try:
            stdscr.addstr(y-2, 3, text)
        except curses.error:
            pass

    def display_videos(self, subwin):
        y, x = subwin.getmaxyx()
        global videos
        pos = self.pos
        count = 0
        for i, video in enumerate(videos):
            if i < y-3:
                try:
                    if self.selected == i:
                        ypos = i+1
                        subwin.addstr(ypos, 1, str(pos+i+1),
                                      curses.color_pair(1))
                        subwin.addstr(ypos, 5, video.title,
                                      curses.color_pair(2) | curses.A_BOLD)
                        pos += 1
                        subwin.addstr(ypos+1, 5, f"Channel:")
                        subwin.addstr(
                            ypos+1, 13, video.playlists[0].name, curses.color_pair(3) | curses.A_BOLD)
                        # pos += 1
                    else:
                        subwin.addstr(
                            i+1+pos, 1, f"{pos+i+1}. {video.title}", curses.color_pair(2))
                    self.videos.append(video.url)
                    count += 1
                except curses.error:
                    pass
        self.count = count
        subwin.refresh()

    def handle_input(self, key):
        selected = self.selected
        if selected > self.count-1:
            self.selected = self.count-1
        if key == ord('q'):
            return True
        elif key == curses.KEY_UP:
            if selected > 0:
                self.selected -= 1
                return False
        elif key == curses.KEY_DOWN:
            if selected <= self.count-1:
                self.selected += 1
                return False
            elif selected > self.count:
                self.selected = self.count+1
                return False
        elif key == curses.KEY_ENTER or key == 10 or key == 13:
            play_video(self.videos[self.selected])
        else:
            return False


def play_video(url):
    subprocess.run(['mpv',
                    '--hwdec=auto',
                    # '--no-audio-display',
                    # '--no-osc',
                    # '--no-input-default-bindings',
                    # '--no-input-cursor',
                    # '--no-keepaspect',
                    # '--no-border',
                    # '--no-keep-open',
                    # '--no-keep-open-pause',
                    # '--no-cache',
                    '--ytdl-format=bestvideo[height<=1080]+bestaudio/best[height<=1080]',
                    '--no-terminal',
                    '--no-msg-color',
                    # '--vo=gpu',
                    # '--vo=x11',
                    '--really-quiet',
                    '--start=1',
                    url],
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.STDOUT
                   )
    # print(url)


class Ytcc:
    def __init__(self):
        self.json_data = None
        self.date = ''

    def get_date(self):
        return self.date

    def get_subscriptions(self):
        pass

    def import_subscriptions(self):
        pass

    def update_subscriptions(self):
        subprocess.run(['ytcc', 'update'])

    def get_videos(self):
        global daterange
        command = subprocess.Popen(['ytcc',
                                    '--output',
                                   'json',
                                    'list',
                                    '-s',
                                    daterange,
                                    '--watched',
                                    '--unwatched',
                                    '-o',
                                    'publish_date',
                                    'desc'],
                                   stdout=subprocess.PIPE)
        data = command.stdout.read()
        return data


if __name__ == '__main__':
    os.system('clear')
    ytc = Ytcc()
    set_date(days=6)
    get_videos(ytc.get_videos())
    curses.wrapper(Menu('Youtube in MPV', videos).window)
