from freqtrade import data
from numpy import array, where
from pandas.core.frame import DataFrame
from pandas import Timestamp
from freqtrade.strategy import merge_informative_pair
import talib.abstract as ta

MAIN_DATAFRAME_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume']

def klinger_oscilator(dataframe: DataFrame) -> array:
    previous_dataframe = dataframe.shift(1)
    previous_typical_price = ta.TYPPRICE(previous_dataframe)
    typical_price = ta.TYPPRICE(dataframe)
    signal_volume = where((typical_price - previous_typical_price) >= 0,
                          dataframe["volume"], dataframe["volume"] * -1)
    klinger_volume_indicator = ta.EMA(signal_volume, timeperiod=34) - \
        ta.EMA(signal_volume, timeperiod=55)
    signal = ta.EMA(klinger_volume_indicator, 13)

    return [klinger_volume_indicator, signal]


def populate_incomplete_candle(dataframe: DataFrame, ticker: dict) -> DataFrame:
    return dataframe.copy().iloc[1:].append({
        "date": Timestamp(ticker["timestamp"], unit='ms', tz='UTC', freq='240T'),
        "open": ticker["open"],
        "high": ticker["high"],
        "low": ticker["low"],
        "close": ticker["close"],
        "volume": ticker["baseVolume"]
    }, ignore_index=True)


"""
Merge two dataframes into one
"""
def merge_dataframes(source: DataFrame, 
                    sourceTimeframe: str, 
                    destination: DataFrame, 
                    destinationTimeFrame: str) -> DataFrame:
    destination = merge_informative_pair(destination, source, destinationTimeFrame, sourceTimeframe, ffill=True)
    skip_columns = [(s + "_" + sourceTimeframe) for s in MAIN_DATAFRAME_COLUMNS]
    destination.drop(inplace=True,columns=skip_columns)
    destination.rename(inplace=True,columns=lambda s: s.replace("_{}".format(sourceTimeframe), "") if (not s in skip_columns) else s)
    return destination