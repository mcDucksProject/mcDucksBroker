from numpy import array, where
from pandas.core.frame import DataFrame
from pandas import Timestamp
import talib.abstract as ta


def klinger_oscilator(dataframe: DataFrame) -> array:
    previous_dataframe = dataframe.shift(1)
    previous_typical_price = ta.TYPPRICE(previous_dataframe)
    typical_price = ta.TYPPRICE(dataframe)
    signal_volume = where((typical_price - previous_typical_price) >= 0,
                          dataframe["volume"], dataframe["volume"] * -1)
    klinger_volume_indicator = ta.EMA(signal_volume, timeperiod=34) - ta.EMA(signal_volume, timeperiod=55)
    signal = ta.EMA(klinger_volume_indicator, 13)

    return [klinger_volume_indicator, signal]


def populate_incomplete_candle(dataframe: DataFrame, ticker: dict) -> DataFrame:
    return dataframe.copy().iloc[1:].append({
        "date" : Timestamp(ticker["timestamp"],unit='ms',tz='UTC', freq='240T'),
        "open" : ticker["open"],
        "high" : ticker["high"],
        "low" : ticker["low"],
        "close" : ticker["close"],
        "volume" : ticker["baseVolume"]
    }, ignore_index=True)
