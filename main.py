"""
    Youtube player using mpv

#TODO: Import user subscriptions from csv file
#TODO: Generate the latest videos from the subscriptions and display them in a menu. Demo classes have been made but probs need modifying
#TODO: Play the videos
#TODO: Probably use a database to store the videos
#TODO: GUI Tweaks. I've thought about giving up since theres a pip module that makes things easier:https://github.com/pmbarrett314/curses-menu


Neat code:
def my_print(*args, **kwargs):
    prefix = kwargs.pop('prefix', '')
    print(prefix, *args, **kwargs)
>>> my_print('eggs')
 eggs
>>> my_print('eggs', prefix='spam')
spam eggs

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
refreshrate = 50


def get_videos(data):
    global videos
    videos = json.loads(
        data, object_hook=lambda d: types.SimpleNamespace(**d))


def set_date(**days):
    global daterange
    format = "%Y-%m-%d"
    range = datetime.datetime.today() - datetime.timedelta(days=days.get('days', 3))
    daterange = range.strftime(format)

# class YoutubeClient:
#     def __init__(self):
#         # self.subscriptions = []
#         self.latest_videos = []

#     def get_subscriptions(self, data):
#         self.latest_videos = json.loads(
#             data, object_hook=lambda d: types.SimpleNamespace(**d))
#         return self.latest_videos

#     def view_subscriptions(self):
#         return self.latest_videos


# class MenuOption:
#     def __init__(self, record, title, id, function):
#         self.record = record
#         self.title = title
#         self.id = id
#         self.function = function

#     def execute(self):
#         self.function(self.id)

class Menu:
    def __init__(self, title, videos):
        self.title = title
        self.videos = videos
        self.selected = 0
        self.pos = 0

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
            subwindow = self.create_subwindow(stdscr, y, x)
            thread = threading.Thread(self.display_videos(subwindow))
            thread.start()
            # self.create_subpad(stdscr, y, x)
            self.header(stdscr, x)
            self.footer(stdscr, y)
            thread.join()
            stdscr.refresh()
            try:
                c = stdscr.getch()
                if c == ord('q'):
                    break
            except KeyboardInterrupt:
                break
        curses.endwin()

    def create_subwindow(self, stdscr, y, x):
        try:
            subwin = stdscr.subwin(y-4, x-2, 2, 1)
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
        for i, video in enumerate(videos):
            if i < y-2:
                try:
                    if self.selected == i:
                        ypos = i+1
                        subwin.addstr(
                            ypos, 1, f"{pos+i+1}. {video.title}", curses.color_pair(2) | curses.A_BOLD)
                        pos += 1
                        subwin.addstr(ypos+1, 1, f"{video.playlists[0]}")
                        pos += 1
                    else:
                        subwin.addstr(
                            i+1+pos, 1, f"{pos+i+1}. {video.title}", curses.color_pair(2))
                except curses.error:
                    pass
        subwin.refresh()

    def add_record(self, record):
        pass


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

    def play_video(self, video_id):
        url = ''
        subprocess.run(['mpv',
                        '--hwdec=auto',
                        '--no-audio-display',
                        '--no-osc',
                        # '--no-input-default-bindings',
                        # '--no-input-cursor',
                        # '--no-keepaspect',
                        '--no-border',
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
        print(url)

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

    def handle_input(self, stdscr):
        selected = self.selected
        key_actions = {
            curses.KEY_UP: lambda: self.move_up(selected, num_options),
            curses.KEY_DOWN: lambda: self.move_down(selected, num_options),
            ord('q'): lambda: True}
        # curses.KEY_ENTER: lambda: ytc.play_video(self.options[selected].id),
        # 10: lambda: ytc.play_video(self.options[selected].id),
        # 13: lambda: ytc.play_video(self.options[selected].id)
        # }
        pass


if __name__ == '__main__':
    # os.system('clear')
    ytc = Ytcc()
    # ytc.generate_date()
    set_date(days=6)
    # ytc.update_subscriptions()
    get_videos(ytc.get_videos())
    curses.wrapper(Menu('Youtube in MPV', videos).window)
    # curses.wrapper(Menu('Youtube in MPV', ytc.get_videos()).display)
#
#
#
