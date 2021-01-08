import numpy as np
from termcolor import colored
import common as cu
import pandas as pd


def tws_metrics(trade_log_file_path):
    df = pd.read_csv(trade_log_file_path)
    df.time = pd.to_datetime(df.time, format="%H:%M:%S")

    print(df.head())

    n = len(df)

    x = []

    num_trades = 0

    print("Entries:", n)

    for i in range(n-1, 0, -1):
        sym = df['sym'][i]
        action = df['action'][i]
        buy_price = df['price'][i]
        pos = df['pos'][i]
        buy_fee = df['comission'][i]

        sold = False

        if action == 'BOT':
            num_trades += 1
            print("%s. " % num_trades, sym, df['time'][i].time(), action, pos, buy_price, " ", end="")

            j = i - 1
            while j >= 0 and not sold:
                if df['sym'][j] == sym:
                    if df['action'][j] == 'SLD':

                        sold = True
                        sell_price = df['price'][j]
                        action = df['action'][j]
                        sell_fee = df['comission'][i]

                        print(action, df['time'][j].time(), sell_price, end="")

                        buy_cost = buy_price * pos + buy_fee
                        sell_value = sell_price * pos - sell_fee
                        gain = 100 * (sell_price / buy_price - 1)
                        net_gain = 100 * (sell_value / buy_cost - 1)
                        c = 'red' if net_gain < 0 else 'green'
                        print(colored("   ->   Gain: %.2f" % net_gain + "%", color=c))

                        x.append(net_gain)
                j -= 1

            if not sold:
                print("")

    cu.stats(x, show_chart_=True)


tws_metrics("logs\\current.csv")



