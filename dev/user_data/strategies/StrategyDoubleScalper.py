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
    main_timeframe = '15m'
    support_timeframe = '12h'
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
    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True
    buy_params = {
        "main_overbought" : 47,
        "main_oversold" : 52,
        "main_rsi_timeperiod" : 14,
        "support_overbought" : 60,
        "support_oversold" : 40,
        "support_rsi_timeperiod" : 14
    }



    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, self.main_timeframe) for pair in pairs] + \
                            [(pair, self.support_timeframe) for pair in pairs]
        return informative_pairs

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        if self.config['runmode'].value in ('backtest', 'hyperopt'):
            assert (timeframe_to_minutes(self.timeframe) <= 5), "Backtest this strategy in 5m or 1m timeframe."

        if not self.dp:
            return dataframe

        main_dataframe = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=self.main_timeframe)
        support_dataframe = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=self.support_timeframe)
        # RSI MAIN

        main_dataframe['main_rsi'] = ta.RSI(main_dataframe['close'],timeperiod=self.buy_params['main_rsi_timeperiod'])
        support_dataframe['support_rsi'] = ta.RSI(support_dataframe['close'],timeperiod=self.buy_params['support_rsi_timeperiod'])

        dataframe = merge_dataframes(
            source=support_dataframe,
            sourceTimeframe=self.support_timeframe,
            destination=dataframe,
            destinationTimeFrame=self.timeframe
        )

        dataframe = merge_dataframes(
            source=main_dataframe,
            sourceTimeframe=self.main_timeframe,
            destination=dataframe,
            destinationTimeFrame=self.timeframe
        )
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        minimum_coin_price = 0.0000015

        conditions.append(dataframe["volume"] > 0)
        conditions.append(dataframe["close"] > minimum_coin_price)
        conditions.append(dataframe["main_rsi"] > self.buy_params["main_oversold"])
        conditions.append(dataframe["support_rsi"] > self.buy_params["support_overbought"])

        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), "buy"] = 1
        return dataframe
    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe