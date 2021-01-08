import os
import pandas as pd
from ibapi.contract import Contract
from ibapi.order import Order
import matplotlib.pyplot as plt

__BUY_COMMAND = "BUY"
__SELL_COMMAND = "SELL"
__IDLE_COMMAND = "IDLE"


__log_path = "logs"


def get_pivot_name(is_top):
    return "High" if is_top else "Low"


def contract(symbol):
    c = Contract()
    c.symbol = symbol
    c.secType = 'STK'
    c.exchange = 'SMART'
    c.currency = 'USD'

    return c


def to_tick_price(x):
    x = int(100 * x) / 100.0
    return x


def BracketOrder(parentOrderId: int,
                 quantity: float,
                 limitPrice: float,
                 takeProfitLimitPrice: float,
                 stopLossPrice: float):
    parent = Order()
    parent.orderId = parentOrderId
    parent.action = "BUY"
    parent.orderType = "LMT"
    parent.totalQuantity = quantity
    parent.lmtPrice = to_tick_price(limitPrice)
    parent.transmit = False

    takeProfit = Order()
    takeProfit.orderId = parent.orderId + 1
    takeProfit.action = "SELL"
    takeProfit.orderType = "LMT"
    takeProfit.totalQuantity = quantity
    takeProfit.lmtPrice = to_tick_price(takeProfitLimitPrice)
    takeProfit.parentId = parentOrderId
    takeProfit.transmit = False

    stopLoss = Order()
    stopLoss.orderId = parent.orderId + 2
    stopLoss.action = "SELL"
    stopLoss.orderType = "STP"
    stopLoss.auxPrice = to_tick_price(stopLossPrice)
    stopLoss.totalQuantity = quantity
    stopLoss.parentId = parentOrderId
    stopLoss.transmit = True

    bracketOrder = [parent, takeProfit, stopLoss]
    return bracketOrder


def BracketOrder2(
        parentOrderId: int,
        quantity: float,
        limitPrice: float,
        stopLossPrice: float):
    parent = Order()
    parent.orderId = parentOrderId
    parent.action = "BUY"
    parent.orderType = "LMT"
    parent.totalQuantity = quantity
    parent.lmtPrice = to_tick_price(limitPrice)
    parent.transmit = False

    stopLoss = Order()
    stopLoss.orderId = parent.orderId + 1
    stopLoss.action = "SELL"
    stopLoss.orderType = "STP"
    stopLoss.auxPrice = to_tick_price(stopLossPrice)
    stopLoss.totalQuantity = quantity
    stopLoss.parentId = parentOrderId
    stopLoss.transmit = True

    bracketOrder = [parent, stopLoss]
    return bracketOrder


def save_trade_log(order_id, symbol, action, time_, price, size):
    path = __log_path + "\\" + "trades.csv"

    if os.path.isfile(path):
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(columns=['sym', 'time', 'action', 'price', 'size'])

    data = {
        'sym': symbol,
        'time': time_,
        'action': action,
        'price': price,
        'size': size,
        'orderid': order_id
    }

    df = df.append(data, ignore_index=True)
    print(df)

    df.to_csv(path, index=False)


def add_indicators(df, p):
    # df["mav" + str(p["mavs_sell"])] = df['Close'].rolling(window=p["mavs_sell"]).mean()
    # df["mav" + str(p["mavl_sell"])] = df['Close'].rolling(window=p["mavl_sell"]).mean()
    df["mav" + str(p["mavs_sell"])] = ema(df['Close'], p["mavs_sell"])
    df["mav" + str(p["mavl_sell"])] = ema(df['Close'], p["mavl_sell"])
    df["mav" + str(p["mavs_p"])] = ema(df['Close'], p["mavs_p"])
    df["mav" + str(p["mavl_p"])] = ema(df['Close'], p["mavl_p"])

    return df


def stats(gains, show_in_rows=False, show_header=True, show_chart_=False):
    plus = sum(x > 0 for x in gains)
    splus = sum(x for x in gains if x > 0)
    minus = sum(x < 0 for x in gains)
    sminus = sum(x for x in gains if x < 0)

    num_trades = len(gains)
    success_rate = None if (plus + minus) == 0 else plus / (plus + minus)
    rr = None if plus == 0 or minus == 0 else -(splus / plus) / (sminus / minus)

    avg_win = None if plus == 0 else splus / plus
    avg_loss = None if minus == 0 else sminus / minus

    if avg_win is None:
        win_value = 0
    else:
        win_value = num_trades * success_rate * avg_win

    if avg_loss is None:
        loss_value = 0
    else:
        loss_value = num_trades * (1 - success_rate) * avg_loss

    profit = win_value + loss_value

    if len(gains) > 0:
        if show_in_rows:
            if show_header:
                print("Nr.Trades    Success Rate    R/R     Winners    Avg. Win     Losers     Avg. Loss      Profit/Trade")

            print("    ", end="")
            print(num_trades, end="")
            print("           ", end="")
            print(round(100 * success_rate), "%", end="")
            print("        ", end="")
            print("N/A" if rr is None else "%.2f" % rr, end="")
            print("        ", end="")
            print(plus, end="")
            print("        ", end="")
            print("N/A" if avg_win is None else "%.2f" % avg_win + "%", end="")
            print("        ", end="")
            print(minus, end="")
            print("        ", end="")
            print("N/A" if avg_loss is None else "%.2f" % avg_loss + "%", end="")
            print("          ", end="")
            print("%.2f" % (profit / num_trades))
        else:
            print("")
            print("Nr Trades:", num_trades)
            print("Success Rate: %.2f" % (100 * success_rate), "%")
            print("R/R:", "N/A" if rr is None else "%.2f" % rr)
            print("Winners:", plus, " Avg. Win:", "N/A" if avg_win is None else "%.2f" % avg_win + "%")
            print("Losers:", minus, " Avg. Loss:", "N/A" if avg_loss is None else "%.2f" % avg_loss + "%")
            print("Profit/Trade: %.2f" % (profit / num_trades))
            print("")

    if show_chart_:
        x = list(range(0, len(gains)))
        plt.bar(x, gains)
        plt.show()
        plt.close("all")


def ema(x, length):
    multiplier = 2 / (length + 1)

    n = len(x)
    s = x.copy()

    print(n, length)
    if 0 < length < n:
        s[length] = sum(x[n-length:]) / length

        print(len(x[n-length:]), x[n-length:])

        for i in range(length, n):
            s[i] = x[i] * multiplier + s[i-1] * (1 - multiplier)
    return s
