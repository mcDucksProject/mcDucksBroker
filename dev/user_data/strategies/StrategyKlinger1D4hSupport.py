import freqtrade.vendor.qtpylib.indicators as qtpylib
from numpy import ceil
import talib.abstract as ta
from freqtrade import data
from freqtrade.exchange import timeframe_to_minutes
from freqtrade.strategy import IStrategy
from pandas.core.frame import DataFrame
from user_data.strategies.custom_indicators import merge_dataframes

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from custom_indicators import klinger_oscilator, populate_incomplete_candle

"""
Buys when the 1D Klinger and de 4H Klinger crosses
"""
class StrategyKlinger1D4hSupport(IStrategy):
    INTERFACE_VERSION = 2

    # Optimal ticker interval for the strategy.
    timeframe = '5m'
    timeframe_main = '1d'
    timeframe_support = '4h'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = True
    sell_profit_only = True
    ignore_roi_if_buy_signal = False
    ignore_buying_expired_candle_after = 360
    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 55

    # ROI table:
    # minimal_roi = {
    #    "0": 0.545,
    #    "1564": 0.328,
    #    "4110": 0.121,
    #    "6891": 0
    # }
    minimal_roi = {
        "0": 100
    }

    # Stoploss:
    #stoploss = -0.045
    stoploss = -100
    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.24
    trailing_stop_positive_offset = 0.315
    trailing_only_offset_is_reached = False

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, self.timeframe_main) for pair in pairs] + \
                            [(pair, self.timeframe_support) for pair in pairs]
        return informative_pairs

    def do_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        [dataframe["kvo"], dataframe["ks"]] = klinger_oscilator(dataframe)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        if self.config['runmode'].value in ('backtest', 'hyperopt'):
            assert (timeframe_to_minutes(self.timeframe) <=
                    5), "Backtest this strategy in 5m or 1m timeframe."

        if not self.dp:
            return dataframe

        dataframe_main = self.dp.get_pair_dataframe(
                pair=metadata['pair'], 
                timeframe=self.timeframe_main
        )   
        dataframe_support = self.dp.get_pair_dataframe(
                pair=metadata['pair'], 
                timeframe=self.timeframe_support
        )         
        [dataframe_main["main_kvo"], dataframe_main["main_ks"]] = \
            klinger_oscilator(dataframe_main)
        [dataframe_support["support_kvo"], dataframe_support["support_ks"]] = \
            klinger_oscilator(dataframe_support)

        dataframe = merge_dataframes(
            source=dataframe_main,
            sourceTimeframe=self.timeframe_main,
            destination=dataframe,
            destinationTimeFrame=self.timeframe
        )
        dataframe = merge_dataframes(
            source=dataframe_support,
            sourceTimeframe=self.timeframe_support,
            destination=dataframe,
            destinationTimeFrame=self.timeframe
        )     

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        minimum_coin_price = 0.0000015
        last_day = dataframe.shift(self.shift_value())
        dataframe.loc[(
            (qtpylib.crossed_above(dataframe["support_kvo"], dataframe["support_ks"])) &
            ((last_day['main_kvo'] < last_day['main_ks']) &
            (dataframe['main_kvo'] > dataframe['main_ks'])) &
            (dataframe["volume"] > 0) &
            (dataframe["close"] > minimum_coin_price)
        ), "buy"] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        last_day = dataframe.shift(self.shift_value())
        dataframe.loc[(
            (qtpylib.crossed_below(dataframe["support_kvo"], dataframe["support_ks"])) &
            ((last_day['main_kvo'] > last_day['main_ks']) &
            (dataframe['main_kvo'] < dataframe['main_ks'])) &            
            (dataframe["volume"] > 0)
        ), "sell"] = 1
        return dataframe

    def shift_value(self) -> int:
        return int(ceil(timeframe_to_minutes(self.timeframe_main) / timeframe_to_minutes(self.timeframe)))