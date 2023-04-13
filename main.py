"""
    Youtube player using mpv

#TODO: Import user subscriptions from csv file
#TODO: Generate the latest videos from the subscriptions and display them in a menu. Demo classes have been made but probs need modifying
#TODO: Play the videos
#TODO: Probably use a database to store the videos
#TODO: GUI Tweaks. I've thought about giving up since theres a pip module that makes things easier:https://github.com/pmbarrett314/curses-menu
"""
import curses
import json
import subprocess
import datetime


color_pairs = {
    "default": (curses.COLOR_WHITE, curses.COLOR_BLACK),
    "highlighted": (curses.COLOR_BLACK, curses.COLOR_WHITE),
    "header1": (curses.COLOR_BLACK, curses.COLOR_GREEN),
    "header2": (curses.COLOR_BLACK, curses.COLOR_BLUE),
    "header3": (curses.COLOR_BLACK, curses.COLOR_CYAN),
    "header4": (curses.COLOR_BLACK, curses.COLOR_MAGENTA),
}

styles = {
    'BRIGHT': curses.A_BOLD,
    'DIM': curses.A_DIM,
    'NORMAL': curses.A_NORMAL
}


class MenuOption:
    def __init__(self, title, id, function):
        self.title = title
        self.id = id
        self.function = function

    def execute(self):
        self.function(self.id)


# DEMO Option: Plays a game
class PlayGameOption(MenuOption):
    def __init__(self):
        super().__init__("Play", self.play_game)

    def play_game(self):
        print("Playing game...")


class Menu:
    def __init__(self, title, options):
        self.title = title
        self.options = options

    def display(self, stdscr):
        current_option = 0
        key_actions = {
            curses.KEY_UP: lambda: current_option > 0 and current_option - 1,
            curses.KEY_DOWN: lambda: current_option < num_options - 1 and current_option + 1,
            ord('q'): lambda: True,
            # curses.KEY_ENTER: lambda: self.options[current_option].execute(),
            # 10: lambda: self.options[current_option].execute(),
            # 13: lambda: self.options[current_option].execute()
            # TODO: Fix this
            curses.KEY_ENTER: lambda: ytc.play_video(self.options[current_option].id),
            10: lambda: ytc.play_video(self.options[current_option].id),
            13: lambda: ytc.play_video(self.options[current_option].id)
        }
        heading = [
            (f'{self.title}', curses.color_pair(3)),
            ('Use arrow keys to navigate\tq to quit'.expandtabs(
                5), curses.color_pair(4)),
        ]

        curses.curs_set(0)
        for i, (x, (fg, bg)) in enumerate(color_pairs.items()):
            curses.init_pair(i+1, fg, bg)
        for x, y in styles.items():
            setattr(curses, x, y)

        num_options = len(self.options)
        while True:
            stdscr.clear()
            line = 0
            try:
                for text, style in heading:
                    stdscr.addstr(line, 0, text, style)
                    line += 1
            except curses.error:
                pass

            for i, option in enumerate(self.options):
                if i == current_option:
                    stdscr.attron(curses.color_pair(2))
                else:
                    stdscr.attron(curses.color_pair(1))
                try:
                    stdscr.addstr(line, 0, option.title)
                except curses.error:
                    pass
                line += 1
            stdscr.refresh()

            try:
                key = stdscr.getch()
            except KeyboardInterrupt:
                break

            action = key_actions.get(key)
            if action:
                result = action()
                if result is True:
                    break
                elif result is not None:
                    current_option = result

        curses.endwin()


class Ytcc:
    def __init__(self):
        self.subscriptions = []
        self.json_data = None
        self.date = ''

    def generate_date(self):
        date_format = "%Y-%m-%d"
        three_days_ago = datetime.datetime.today() - datetime.timedelta(days=3)
        self.date = three_days_ago.strftime(date_format)

    def get_date(self):
        return self.date

    def get_subscriptions(self):
        pass

    def import_subscriptions(self):
        pass

    def play_video(self, video_id):
        subprocess.run(['ytcc', 'play', str(video_id)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    def update_subscriptions(self):
        subprocess.run(['ytcc', 'update'])

    def get_videos(self):
        command = subprocess.Popen(['ytcc', '--output', 'json', 'list', '-s', self.date, '--watched', '--unwatched',
                                    '-o', 'publish_date', 'desc'], stdout=subprocess.PIPE)
        json_data = command.stdout.read()
        self.json_data = json.loads(json_data)
        data = []
        for x in self.json_data:
            title = x['title']
            video_id = x['id']
            def sfunction(): return self.play_video(id)
            option = MenuOption(title, video_id, sfunction)
            data.append(option)
        return data


if __name__ == '__main__':
    ytc = Ytcc()
    ytc.generate_date()
    # ytc.update_subscriptions()
    curses.wrapper(Menu('\tYoutube in MPV', ytc.get_videos()).display)
    # print(ytc.get_videos())
