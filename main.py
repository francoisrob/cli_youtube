"""
############################################################################################################
                                Youtube player using mpv amd ytcc


############################################################################################################
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
updated = False
refreshrate = 750


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
    def __init__(self, title):
        self.title = title
        self.videos = []
        self.entered = False
        self.selected = 0
        self.pos = 0
        self.count = 0

    def get_dimensions(self, stdscr):
        y, x = stdscr.getmaxyx()
        return y, x

    def set_colors(self, stdscr):
        curses.use_default_colors()
        for x, y in enumerate([curses.COLOR_BLACK,
                               curses.COLOR_RED,
                               curses.COLOR_GREEN,
                               curses.COLOR_YELLOW,
                               curses.COLOR_BLUE,
                               curses.COLOR_MAGENTA,
                               curses.COLOR_CYAN,
                               curses.COLOR_WHITE]):
            curses.init_pair(x, y, -1)

    def list_options(self):
        for x in self.videos:
            print(x.title)

    def window(self, stdscr):
        global refreshrate, updated
        curses.curs_set(0)
        stdscr.timeout(refreshrate)
        self.set_colors(stdscr)
        y, x = self.get_dimensions(stdscr)

        while True:
            stdscr.clear()
            y, x = self.get_dimensions(stdscr)
            try:
                self.header(stdscr, x)
                self.footer(stdscr, y, x)
            except curses.error:
                pass
            stdscr.box()
            subwindow = self.create_subwindow(stdscr, y-5, x)
            thread = threading.Thread(self.display_videos(subwindow))
            thread.start()
            stdscr.refresh()
            try:
                curses.flushinp()
                c = stdscr.getch()
                if self.handle_input(c) == True:
                    break
                elif updated == True:
                    thread.join()
            except KeyboardInterrupt:
                break

    def create_subwindow(self, stdscr, y, x):
        try:
            subwin = stdscr.subwin(y-1, x-2, 4, 1)
            subwin.border(' ', ' ', 0, 0, ' ', ' ', ' ', ' ')
            subwin.refresh()
            return subwin
        except curses.error:
            pass

    def header(self, stdscr, x):
        stdscr.addstr(1, x//2-len(self.title)//2,
                      self.title, curses.color_pair(2) | curses.A_BOLD)
        guide_text = textwrap.wrap(
            "Use arrow keys to navigate and enter to select", width=(x-4))[0]
        stdscr.addstr(3, 2, guide_text, curses.color_pair(4) | curses.A_BOLD)

    def footer(self, stdscr, y, x):
        text = "Press 'q' or Ctrl+C to exit"
        updating_text = "Updating..."
        updated_text =  "Updated"
        if updated:
            stdscr.addstr(y-2, (x-len(updating_text)-2), "              ")
            stdscr.addstr(y-2, (x-len(updated_text)-3), updated_text, curses.color_pair(2))
        else:
            stdscr.addstr(y-2, (x-len(updating_text)-2), updating_text, curses.color_pair(0))
        try:
            stdscr.addstr(y-2, 2, text, curses.color_pair(4) | curses.A_BOLD)
        except curses.error:
            pass

    def display_videos(self, subwin):
        try:
            y, x = subwin.getmaxyx()
            global videos
            pos = self.pos
            count = 0
            for i, video in enumerate(videos):
                if i < y-2:
                    ypos = i + 1 + pos
                    try:
                        title = textwrap.wrap(video.title, width=(x//2-8))[0]
                        if self.selected == i:
                            if x > 100 and y > 20:
                                self.show_details(subwin, video, y, x)
                                subwin.addstr(ypos, 1, f"{pos+i+1}. {title}", curses.color_pair(2) | curses.A_BOLD)
                            else:
                                subwin.addstr(ypos, 1, f"{pos+i+1}. {textwrap.wrap(video.title, width=(x-8))[0]}", curses.color_pair(2) | curses.A_BOLD)
                        else:
                            if x > 100 and y > 20:
                                subwin.addstr(
                                    ypos, 1, f"{pos+i+1}. {title}", curses.color_pair(0))
                            else:
                                subwin.addstr(
                                    ypos, 1, f"{pos+i+1}. {textwrap.wrap(video.title, width=(x-6))[0]}", curses.color_pair(0))
                        self.videos.append(video.url)
                        count += 1
                    except curses.error:
                        pass
            self.count = count
            subwin.refresh()
        except AttributeError:
            pass

    def show_details(self, subwin, video, y, x):
        try:
            title = textwrap.wrap(video.title, width=(x//2-4))
            channel = video.playlists[0].name
            published = video.publish_date
            description = video.description
            watched = video.watch_date
            duration = video.duration
            details_text = ("Channel", "Published",
                            "Description", "Watched", "Duration")
            details = (channel, published, description, watched, duration)
            subdetails = subwin.subwin(y-2, (x//2 + x % 2), 5, x//2)
            subdetails.border()
            subdetails.refresh()
            count = 0
            for i, title in enumerate(title):
                if i >= 2:
                    break
                subdetails.addstr(
                    i+1, 2, title, curses.color_pair(3) | curses.A_BOLD)
                count += 1
            subdetails.addstr(2+count, 2, f"{details_text[0]}:")
            subdetails.addstr(3+count, 2, f"{details_text[4]}:")
            subdetails.addstr(
                10, 2, f"{details_text[2]}:", curses.color_pair(3) | curses.A_BOLD)
            subdetails.addstr(4+count, 2, f"{details_text[3]}:")
            subdetails.addstr(5+count, 2, f"{details_text[1]}:")
            subdetails.addstr(
                2+count, 14, f"{details[0]}", curses.color_pair(4) | curses.A_BOLD)
            subdetails.addstr(3+count, 12, f"{details[4]}")
            if details[3] != None:
                subdetails.addstr(
                    4+count, 14, f"YES", curses.color_pair(2) | curses.A_BOLD)
            else:
                subdetails.addstr(
                    4+count, 14, f"NO", curses.color_pair(1) | curses.A_BOLD)
            year, month, day = details[1].split('-')
            date = datetime.date.strftime(datetime.date(
                int(year), int(month), int(day)), '%d/%m/%Y')
            subdetails.addstr(5+count, 14, f"{date}")
            lines = textwrap.wrap(details[2], width=(x//2-6))
            for i, line in enumerate(lines):
                if i < y-14:
                    subdetails.addstr(11+i, 3, line)
            return subdetails
        except curses.error:
            pass

    def handle_input(self, key):
        selected = self.selected
        if key == ord('q'):
            return True
        elif key == curses.KEY_UP:
            if selected > 0:
                self.selected -= 1
            else:
                self.selected = self.count-1
        elif key == curses.KEY_DOWN:
            if self.count > selected+1:
                self.selected += 1
            else:
                self.selected = 0
        elif key == curses.KEY_ENTER or key == 10 or key == 13:
            play_video(self.videos[self.selected])

        else:
            return False


def play_video(url):
    subprocess.run(['mpv',
                    '--hwdec=auto',
                    # '--no-audio-display',
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


class Ytcc:
    def __init__(self):
        self.json_data = None

    def update_subscriptions(self):
        global updated
        subprocess.run(['ytcc', 'update'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        updated = True

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
    update_videos = threading.Thread(target=ytc.update_subscriptions)
    update_videos.start()
    set_date(days=6)
    get_videos(ytc.get_videos())
    curses.wrapper(Menu('Youtube in MPV').window)
