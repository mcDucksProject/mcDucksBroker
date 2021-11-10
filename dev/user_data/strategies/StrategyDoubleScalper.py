# --- Do not remove these libs ---
import talib

from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy import timeframe_to_minutes
from pandas import DataFrame
import technical.indicators as technical
from technical.util import resample_to_interval, resampled_merge
from functools import reduce
import numpy  # noqa
from mcDuck.custom_indicators import merge_dataframes
# --------------------------------
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class StrategyDoubleScalper(IStrategy):
    INTERFACE_VERSION = 2

    # Optimal ticker interval for the strategy.
    timeframe = '5m'
    timeframe_main = '15m'
    timeframe_support = '12h'
    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = False
    sell_profit_only = False
    ignore_roi_if_buy_signal = False
    ignore_buying_expired_candle_after = 30
    # Number of candles the strategy requires before producing valid signals
    startup_candle_count:  14

    minimal_roi = {
        "0" : 0.044
    }
    stoploss = -0.03

    buy_params = {
        "main_overbought" : 47,
        "main_oversold" : 52,
        "main_timeperiod" : 14,
        "support_overbought" : 60,
        "support_oversold" : 40,
        "support_timeperiod" : 14
    }



    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, self.timeframe_main) for pair in pairs] + \
                            [(pair, self.timeframe_support) for pair in pairs]
        return informative_pairs

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        if self.config['runmode'].value in ('backtest', 'hyperopt'):
            assert (timeframe_to_minutes(self.timeframe) <= 5), "Backtest this strategy in 5m or 1m timeframe."

        if not self.dp:
            return dataframe

        dataframe_main = self.dp.get_pair_dataframe(pair=metadata['pair'],timeframe=self.timeframe_main)
        dataframe_support = self.dp.get_pair_dataframe(pair=metadata['pair'],timeframe=self.timeframe_support)
        # RSI MAIN

        timeperiod_main = 14
        timeperiod_support = 14
        dataframe_main['main_rsi'] = ta.RSI(dataframe_main['close'],timeperiod=timeperiod_main)
        dataframe_support['support_rsi'] = ta.RSI(dataframe_support['close'],timeperiod=timeperiod_support)

        dataframe = merge_dataframes(
            source=dataframe_support,
            sourceTimeframe=self.timeframe_support,
            destination=dataframe,
            destinationTimeFrame=self.timeframe
        )

        dataframe = merge_dataframes(
            source=dataframe_main,
            sourceTimeframe=self.timeframe_main,
            destination=dataframe,
            destinationTimeFrame=self.timeframe
        )
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        minimum_coin_price = 0.0000015

        conditions.append(dataframe["volume"] > 0)
        conditions.append(dataframe["close"] > minimum_coin_price)
        conditions.append(dataframe["rsi_main"] > self.buy_params["main_oversold"])
        conditions.append(dataframe["rsi_support"] > self.buy_params["support_overbought"])

        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), "buy"] = 1
        return dataframe