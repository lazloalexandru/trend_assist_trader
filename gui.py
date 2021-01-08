import curses
import datetime
from watchlist import quotes
import numpy as np
import common as cu
import pandas as pd

__TEXT_COLOR = 8
__VARIABLE_COLOR = 3
__HIGHLIGHT_COLOR = 4


def print_quote_name(sym):
    qw = curses.newwin(2, 7, 0, 0)
    qw.clear()

    qw.addstr(0, 0, 'Quote', curses.color_pair(__TEXT_COLOR))
    qw.addstr(1, 0, sym, curses.color_pair(__VARIABLE_COLOR))

    qw.refresh()


def print_quote_info(df, p):
    price = df.iloc[-1]['Close']
    vol = df.iloc[-1]['Volume']
    _v = np.array(df['Volume'].tolist())
    _p = np.array(df['Close'].tolist())
    pxv = np.dot(_p, _v)
    cur_vol = sum(_v)

    w = curses.newwin(2, curses.COLS - 7, 0, 7)

    color_id = 3 if price > p['__min_close_price'] else 1
    w.addstr(0, 0, 'Price', curses.color_pair(__TEXT_COLOR))
    w.addstr(1, 0, '%.2f$' % price, curses.color_pair(color_id))

    w.addstr(0, 7, '1MinVol', curses.color_pair(__TEXT_COLOR))
    w.addstr(1, 8, '%sk' % round(vol / 1000), curses.color_pair(__VARIABLE_COLOR))

    w.addstr(0, 16, 'Volume', curses.color_pair(__TEXT_COLOR))
    w.addstr(1, 17, '%1.fM' % (cur_vol / 1000000), curses.color_pair(__VARIABLE_COLOR))

    color_id = 3 if pxv > p['min_volume_x_price'] else 1
    w.addstr(0, 24, 'PxV', curses.color_pair(__TEXT_COLOR))
    w.addstr(1, 24, '%.0fM' % (pxv / 1000000), curses.color_pair(color_id))

    w.refresh()


def select_quote(scr):
    idx = None
    n = len(quotes)

    scr.clear()
    scr.refresh()

    if n > 0:
        scr.addstr(1, 5, "Select Quote")
        scr.addstr(2, 5, "(press a key between  1 .. " + str(n) + ")")

        for i in range(0, n):
            scr.addstr(4 + i, 5, str(i+1) + " -> " + quotes[i][0])

        while idx not in range(0, n):
            key_pressed = scr.getch()
            idx = key_pressed - ord('1')
            scr.refresh()

    scr.clear()
    scr.refresh()

    return idx


def show_trading_info(command, pivots, p):
    pw = curses.newwin(11, curses.COLS, 3, 0)

    pw.clear()

    if p['position_size'] > 0:
        c = __HIGHLIGHT_COLOR
    else:
        c = __TEXT_COLOR

    r = 0
    pw.addstr(r, 0, 'POS:', curses.color_pair(__TEXT_COLOR))
    pw.addstr(r, 5, str(p['position_size']), curses.color_pair(c))
    text = str(p['mavs_sell']) + "," + str(p['mavl_sell']) + " " + str(p['mavs_p']) + "," + str(p['mavl_p'])
    pw.addstr(r, 25, text, curses.color_pair(c))
    r += 2

    ########################################################################

    pw.addstr(r, 0, 'Signal', curses.color_pair(__TEXT_COLOR))
    pw.addstr(r, 7, '=>', curses.color_pair(__TEXT_COLOR))
    pw.addstr(r, 10, command, curses.color_pair(get_command_color(command)))
    r += 2

    ########################################################################
    if pivots[-1][1]:
        pw.addstr(r, 0, "DOWN TREND", curses.color_pair(__TEXT_COLOR))
    else:
        if p['position_size'] == 0:
            if p['valid_pattern']:
                text = "UP TREND    Buy @ " + str(pivots[-2][0])
            else:
                text = "UP TREND    Entry Below " + str(pivots[-2][0])
        else:
            text = "UP TREND"
        pw.addstr(r, 0, text, curses.color_pair(__TEXT_COLOR))
    r += 1

    ########################################################################
    t_1 = pivots[-1][2][10:15]
    t_2 = pivots[-2][2][10:15]

    print(pivots)

    pw.addstr(r, 0, cu.get_pivot_name(pivots[-2][1]), curses.color_pair(__TEXT_COLOR))
    pw.addstr(r+1, 0, str(t_2), curses.color_pair(__TEXT_COLOR))
    pw.addstr(r+2, 0, str(pivots[-2][0]), curses.color_pair(__VARIABLE_COLOR))

    pw.addstr(r, 12, cu.get_pivot_name(pivots[-1][1]), curses.color_pair(__TEXT_COLOR))
    pw.addstr(r+1, 12, str(t_1), curses.color_pair(__TEXT_COLOR))
    pw.addstr(r+2, 12, str(pivots[-1][0]), curses.color_pair(__VARIABLE_COLOR))

    r += 4

    ########################################################################

    # pw.addstr(r, 0, 'NPvt/LPvt:', curses.color_pair(__TEXT_COLOR))
    # text = str(len(pivots)) + ", " + str(p['last_pivot_idx'])
    # pw.addstr(r, 12, text, curses.color_pair(__TEXT_COLOR))

    pw.refresh()


def get_command_color(command):
    c = None
    if command == cu.__BUY_COMMAND:
        c = 7
    elif command == cu.__SELL_COMMAND:
        c = 1
    elif command == cu.__IDLE_COMMAND:
        c = __TEXT_COLOR

    return c


def show_system_status(unix_time):
    if unix_time is not None:
        w = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)

        current_time = datetime.datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')
        w.addstr(0, 0, current_time, curses.color_pair(__TEXT_COLOR))
        w.addstr(0, 25, "Quit [Ctrl+Q]", curses.color_pair(__TEXT_COLOR))
        w.refresh()


def init_colors():
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_RED)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_YELLOW)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_WHITE)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_GREEN)
    curses.init_pair(8, curses.COLOR_WHITE, curses.COLOR_BLACK)


def init_curses(scr):
    curses.curs_set(0)
    curses.cbreak()
    curses.resize_term(20, 40)

    scr.nodelay(1)
    scr.timeout(1)

    w1 = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
    w2 = curses.newwin(1, curses.COLS, curses.LINES - 2, 0)
    w3 = curses.newwin(3, curses.COLS, curses.LINES - 5, 0)

    return w1, w2, w3


def clear_window(w):
    w.clear()
    w.refresh()
