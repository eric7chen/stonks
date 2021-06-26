import pprint
from config import ACCOUNT_NUM, CONSUMER_KEY, REDIRECT_URI, JSON_PATH
from td.client import TDClient
import pandas as pd
import os.path
from os import path
import time
import datetime
import sys
import signal

# global df


class Stonks():
    def __init__(self, ticker):
        print("Watching:" + ticker)
        self.td_client = TDClient(
            client_id=CONSUMER_KEY, redirect_uri=REDIRECT_URI, credentials_path=JSON_PATH
        )
        self.td_client.login()

        self.ticker = ticker

        if not path.exists(ticker + '.csv'):
            print("Creating New File for " + ticker + "...")
            new = pd.DataFrame(columns=["Date/Time", "9", "21"])
            new.to_csv(ticker + '.csv', index=False)

        self.df = pd.read_csv(ticker + '.csv')

        self.buy()
        self.sell()
        while True:
            print("New Entry...")
            new_entry = {"Date/Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                         "9": self.get_moving_average(9),
                         "21": self.get_moving_average(21)}

            self.df = self.df.append(new_entry, ignore_index=True)
            print(self.df)
            self.df.to_csv(ticker + ".csv", index=False)

            if not len(self.df.index) < 3:
                self.check_cross()

            time.sleep(60)

    def get_moving_average(self, amt):
        total = 0
        self.past_prices = self.td_client.get_price_history(
            symbol=self.ticker, frequency_type="minute", frequency=1, period_type="day").get("candles")
        for i in self.past_prices[-amt:]:
            total += i.get('close')
        return round(total / amt, 3)

    def check_cross(self):
        lop = {"21": 0, "50": 0, "100": 0, "250": 0}
        # short now greater than long but was less
        if self.df.iloc[-1]["9"] > self.df.iloc[-1]["21"] and self.df.iloc[-2]["9"] < self.df.iloc[-2]["21"]:
            print("BUY")
        # short now less than long but was greater
        elif self.df.iloc[-1]["9"] < self.df.iloc[-1]["21"] and self.df.iloc[-2]["9"] > self.df.iloc[-2]["21"]:
            print("SELL")

    def buy(self):
        buy_order = {
            "orderType": "MARKET",
            "session": "NORMAL",
            "duration": "DAY",
            "price": self.td_client.get_price_history(
                symbol=self.ticker, frequency_type="minute", frequency=1, period_type="day").get("candles")[-1:][0].get('open'),
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "Buy",
                    "quantity": 1,
                    "instrument": {
                        "symbol": self.ticker,
                        "assetType": "EQUITY"
                    }
                }
            ]
        }
        self.td_client.place_order(account=ACCOUNT_NUM, order=buy_order)

    def sell(self):
        sell_order = {
            "orderType": "MARKET",
            "session": "NORMAL",
            "duration": "DAY",
            "price": self.td_client.get_price_history(
                symbol=self.ticker, frequency_type="minute", frequency=1, period_type="day").get("candles")[-1:][0].get('open'),
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "Sell",
                    "quantity": 1,
                    "instrument": {
                        "symbol": self.ticker,
                        "assetType": "EQUITY"
                    }
                }
            ]
        }
        self.td_client.place_order(account=ACCOUNT_NUM, order=sell_order)


def main():
    Stonks("FREQ")


def exit_func(signal, frame):
    print("Exiting...")
    sys.exit(0)


signal.signal(signal.SIGINT, exit_func)


if __name__ == "__main__":
    main()
