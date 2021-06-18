import freqtrade.vendor.qtpylib.indicators as qtpylib
from numpy import ceil
import talib as ta
from talib.abstract import SMA, STOCH, RSI
from freqtrade import data
from freqtrade.exchange import timeframe_to_minutes
from freqtrade.strategy import IStrategy
from pandas.core.frame import DataFrame
from user_data.strategies.custom_indicators import merge_dataframes


import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from custom_indicators import klinger_oscilator, merge_dataframes

"""
Buys when the 1D Klinger and de 4H Klinger crosses
"""
class StrategyKlingerStoch(IStrategy):
    INTERFACE_VERSION = 2

    # Optimal ticker interval for the strategy.
    timeframe = '5m'
    timeframe_main = '4h'
    timeframe_support = '1d'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = False
    sell_profit_only = False
    ignore_roi_if_buy_signal = False
    ignore_buying_expired_candle_after = 60
    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 55

    # ROI table:
    minimal_roi = {
        "0": 0.593,
        "1469": 0.153,
        "2722": 0.098,
        "5246": 0
    }

    # Stoploss:
    stoploss = -0.023
    # Trailing stop:

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, self.timeframe_main) for pair in pairs] + \
                            [(pair, self.timeframe_support) for pair in pairs]
        return informative_pairs

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
        [dataframe_main["main_kvo"], dataframe_main["main_ks"]] = \
            klinger_oscilator(dataframe_main)
    
        rsi = RSI(dataframe_main["close"],14)
        stoch_k, stoch_d = STOCH(rsi,rsi,rsi,
                                    fastk_period=14,slowk_period=3,
                                    slowk_matype=ta.MA_Type.EMA,
                                    slowd_period=3,
                                    slowd_matype=ta.MA_Type.EMA)
        k = SMA(stoch_k,3)
        d = SMA(k,3)
        dataframe_main["stochk"] = k
        dataframe_main["stochd"] = d
        #dataframe_main["stochk"] = stoch["fastk"]
        #dataframe_main["stochd"] = stoch["fastd"]
        #dataframe_main["stochk"] = ta.SMA(stoch["fastk"],3)
        #dataframe_main["stochd"] = ta.SMA(dataframe_main["stochk"],3)
        dataframe = merge_dataframes(
            source=dataframe_main,
            sourceTimeframe=self.timeframe_main,
            destination=dataframe,
            destinationTimeFrame=self.timeframe
        )    

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        minimum_coin_price = 0.0000015
        last_candle_main = dataframe.shift(self.shift_value(self.timeframe_main))
        dataframe.loc[(
            (dataframe["stochk"] > last_candle_main["stochk"]) &
            ((last_candle_main['main_kvo'] < last_candle_main['main_ks']) &
            (dataframe['main_kvo'] > dataframe['main_ks'])) &
            (dataframe["volume"] > 0) &
            (dataframe["close"] > minimum_coin_price)
        ), "buy"] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        last_candle_main = dataframe.shift(self.shift_value(self.timeframe_main))      
        dataframe.loc[(
            (dataframe["stochk"] < last_candle_main["stochk"]) &
            ((last_candle_main['main_kvo'] > last_candle_main['main_ks']) &
            (dataframe['main_kvo'] < dataframe['main_ks'])) &            
            (dataframe["volume"] > 0)
        ), "sell"] = 0
        return dataframe

    def shift_value(self, timeframe: str) -> int:
        return int(ceil(timeframe_to_minutes(timeframe) / timeframe_to_minutes(self.timeframe)))