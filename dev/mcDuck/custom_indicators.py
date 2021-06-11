from numpy import array,where
from pandas.core.frame import DataFrame
import talib.abstract as ta

def klinger_oscilator(dataframe: DataFrame) -> array:
    previous_dataframe = dataframe.shift(1)
    previous_typical_price = ta.TYPPRICE(previous_dataframe)
    typical_price = ta.TYPPRICE(dataframe)
    signal_volume = where((typical_price - previous_typical_price) >= 0,dataframe["volume"],dataframe["volume"] * -1)
    klinger_volume_indicator = ta.EMA(signal_volume, timeperiod=34) - ta.EMA(signal_volume, timeperiod=55)
    signal = ta.EMA(klinger_volume_indicator,13)

    return [klinger_volume_indicator,signal]