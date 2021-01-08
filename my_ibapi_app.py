import queue

from ibapi.common import ListOfPriceIncrements
from ibapi.wrapper import OrderId
from ibapi.client import EClient
from ibapi.wrapper import EWrapper, BarData


class IBApi(EWrapper, EClient):
    def __init__(self, client_id, message_window=None):
        EClient.__init__(self, self)
        self.w = message_window

        self.client_id = client_id
        self.data = []
        self.my_time_queue = None
        self.my_errors_queue = None
        self.req_queue = None

    def init_time(self):
        time_queue = queue.Queue()
        self.my_time_queue = time_queue
        return time_queue

    def init_error(self):
        error_queue = queue.Queue()
        self.my_errors_queue = error_queue

    def get_error(self, timeout=6):
        if self.is_error():
            try:
                return self.my_errors_queue.get(timeout=timeout)
            except queue.Empty:
                return None
        return None

    def is_error(self):
        error_exist = not self.my_errors_queue.empty()
        return error_exist

    def init_req_queue(self):
        req_queue = queue.Queue()
        self.req_queue = req_queue
        return req_queue

    def currentTime(self, server_time):
        self.my_time_queue.put(server_time)

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId

    def error(self, id, errorCode, errorString):
        if errorCode != 2104 and errorCode != 2106 and errorCode != 2158:
            error_message = "[%d] %d:%s" % (id, errorCode, errorString)
            # self.w.addstr(1, 0, error_message)
            # self.w.refresh()

            self.my_errors_queue.put(error_message)

    def historicalData(self, reqId, bar):
        # date_time_obj = datetime.datetime.strptime(bar.date, '%Y%m%d')
        # print(date_time_obj.date())
        # print(f'Time: {bar.date} Open: {bar.open} Close: {bar.close}')
        # if bar.date == "20190329":
        #    print(bar)

        msg = str(bar.date)
        # self.sw.addstr(0, 40, msg)
        # self.sw.refresh()

        self.data.append([bar.date, bar.open, bar.close,  bar.high, bar.low, bar.volume * 100])

    def historicalDataUpdate(self, reqId: int, bar: BarData):
        if bar.date == self.data[-1][0]:
            self.data[-1] = [bar.date, bar.open, bar.close, bar.high, bar.low, bar.volume * 100]
        else:
            self.data.append([bar.date, bar.open, bar.close, bar.high, bar.low, bar.volume * 100])
        self.req_queue.put(reqId)

    def historicalDataEnd(self, reqId:int, start:str, end:str):
        msg = str(reqId)
        # self.sw.addstr(0, 70, msg)
        # self.sw.refresh()

        self.req_queue.put(reqId)

    def orderStatus(self, orderId: OrderId, status: str, filled: float, remaining: float, avgFillPrice: float, permId: int, parentId: int,
                    lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):

        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)

        if self.client_id == clientId:
            if status == "Filled":
                status = ""

            text = "[" + str(orderId) + "] " + status + " F: " + str(filled) + " R: " + str(remaining) + "AvgP:" + str(avgFillPrice)
            self.w.addstr(0, 0, text)
            self.w.refresh()

            print("OrderStatus. Id:", orderId, "Status:", status, "Filled:", int(filled), "Remaining:", int(remaining),
                  "AvgFillPrice:", avgFillPrice, "ClientId:", clientId)

    def openOrderEnd(self):
        super().openOrderEnd()
        print("OpenOrderEnd")

    def execDetails(self, reqId, contract, execution):
        print('Order Executed: ', reqId, contract.symbol, contract.secType, contract.currency, execution.execId, execution.orderId, execution.shares,
              execution.lastLiquidity)

    def marketRule(self, marketRuleId: int, priceIncrements: ListOfPriceIncrements):
        super().marketRule(marketRuleId, priceIncrements)
        print("Market Rule ID: ", marketRuleId)
        for priceIncrement in priceIncrements:
            print("Price Increment.", priceIncrement)