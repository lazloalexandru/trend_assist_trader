import queue
import curses
import pandas as pd
import utils_tws as tws
import numpy as np

import pivots as pvt
from watchlist import quotes
import common as cu
import gui
from gui import __TEXT_COLOR


def init_tws_connection(w, ibkr_message_window, connection_id):
    w.addstr(0, 0, "Connecting to TWS ...", curses.color_pair(__TEXT_COLOR))
    w.refresh()

    app = tws.init_tws(ibkr_message_window, connection_id)

    app.data = []

    time_queue = app.init_time()
    req_store = app.init_req_queue()

    w.clear()
    w.addstr(0, 0, "Connected!", curses.color_pair(__TEXT_COLOR))
    w.refresh()

    return app, time_queue, req_store


def trade(df, command, p):
    app = p['app']
    close = df.iloc[-1]["Close"]

    ######################## DEBUG #################################################
    p['status_bar'].clear()
    text = str(p['position_size']) + " " + str(command)
    p['status_bar'].addstr(0, 0, text, curses.color_pair(__TEXT_COLOR))
    p['status_bar'].refresh()
    ################################################################################

    if p['position_size'] > 0:
        if command == cu.__SELL_COMMAND:
            sellPrice = cu.to_tick_price(close * 1.2)
            p['bracket_order'][1].auxPrice = sellPrice
            app.placeOrder(p['bracket_order'][1].orderId, p['contract'], p['bracket_order'][1])

            cu.save_trade_log(p['bracket_order'][1].orderId, p['symbol'], "SELL", df.iloc[-1]["Time"], close, p['position_size'])
            p['position_size'] = 0
    else:
        if command == cu.__BUY_COMMAND:
            order_id = tws.get_next_order_id(app)

            buyPrice = cu.to_tick_price(close * (1 + p['buy_above'] / 100))
            stopPrice = cu.to_tick_price(close * (1 + p['stop'] / 100))
            pos = int(p['buy_amount'] / close)

            p['position_size'] = pos

            print("Buy:", buyPrice, "STOP:", stopPrice)

            p['bracket_order'] = cu.BracketOrder2(
                parentOrderId=order_id,
                quantity=pos,
                limitPrice=buyPrice,
                stopLossPrice=stopPrice)

            app.placeOrder(p['bracket_order'][0].orderId, p['contract'], p['bracket_order'][0])
            app.placeOrder(p['bracket_order'][1].orderId, p['contract'], p['bracket_order'][1])

            cu.save_trade_log(order_id, p['symbol'], "BUY", df.iloc[-1]["Time"], buyPrice, p['position_size'])


def trade_chart(req_store, p):
    sw = curses.newwin(1, curses.COLS, curses.LINES - 2, 0)

    mavs = "mav" + str(p["mavs_sell"])
    mavl = "mav" + str(p["mavl_sell"])

    xxx = None
    while not p['app'].wrapper.is_error() and xxx is None:
        try:
            xxx = req_store.get(timeout=1)
        except queue.Empty:
            xxx = None

    if len(p['app'].data) == 0:
        sw.addstr(0, 0, "No data", curses.color_pair(2))
        sw.refresh()
    else:
        data = p['app'].data
        df = pd.DataFrame(data, columns=["Time", "Open", "Close", "High", "Low", "Volume"])
        _t = pd.to_datetime(df.iloc[-1]["Time"], format="%Y%m%d  %H:%M:%S")
        df = cu.add_indicators(df, p)

        pivots = pvt.get_pivots(df, p)
        num_pivots = len(pivots)

        command = cu.__IDLE_COMMAND

        if df.iloc[-1][mavs] < df.iloc[-1][mavl]:
            command = cu.__SELL_COMMAND

        if num_pivots >= 2:
            if not pivots[-1][1]:  # last pivot was a low
                close = df.iloc[-1]["Close"]

                if df.iloc[-1]["Close"] < pivots[-2][0]:
                    p['valid_pattern'] = True

                if p['valid_pattern']:
                    if close >= pivots[-2][0]:
                        p['valid_pattern'] = False
                        if df.iloc[-1][mavs] > df.iloc[-1][mavl]:
                            command = cu.__BUY_COMMAND

        trade(df, command, p)

        gui.print_quote_info(df, p)

        gui.show_trading_info(command, pivots, p)


def main(scr):
    main_window, status_bar, tws_message_window = gui.init_curses(scr)
    gui.init_colors()

    if quotes is None or len(quotes) == 0:
        main_window.addstr(0, 0, "No quotes in watchlist. See \'watchilist.py\' file.", curses.color_pair(3))
        main_window.refresh()
    else:
        p = get_params()

        selected_id = gui.select_quote(scr)

        p['symbol'] = quotes[selected_id][0]
        p['fast_moving_stock'] = quotes[selected_id][1]

        p['contract'] = cu.contract(p['symbol'])
        p['position_size'] = 0
        p['status_bar'] = status_bar
        p['valid_pattern'] = False

        app, time_queue, req_store = init_tws_connection(main_window, tws_message_window, selected_id)
        gui.print_quote_name(p['symbol'])
        app.reqHistoricalData(2001, p['contract'], "", '1 D', '1 min', 'TRADES', 0, 1, True, [])
        gui.clear_window(status_bar)

        p['app'] = app

        key_pressed = None
        while key_pressed != 17:
            gui.show_system_status(tws.server_clock(app, time_queue))
            trade_chart(req_store, p)
            key_pressed = scr.getch()


def get_params():
    params = {
            '__chart_begin_hh': 9,
            '__chart_begin_mm': 30,
            '__chart_end_hh': 15,
            '__chart_end_mm': 59,

            '__min_close_price': 1.5,
            '__max_close_price': 20,

            'trading_begin_hh': 9,
            'trading_begin_mm': 40,
            'last_entry_hh': 15,
            'last_entry_mm': 55,

            'mavs_sell': 3,
            'mavl_sell': 5,
            'mavs_p': 3,
            'mavl_p': 8,

            'min_volume_x_price': 5000000,
            'pivot_calc_start_index': 10,

            'buy_amount': 250,


            'buy_above': 3,
            'stop': -5,
            'model_params_path': 'model_params\\checkpoint_10'
    }

    return params


curses.wrapper(main)




