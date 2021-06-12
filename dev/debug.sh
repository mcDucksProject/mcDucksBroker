#!/usr/bin/env bash
#encoding=utf8
CONFIGS="-c user_data/config.base.json 
         -c user_data/config.strategyKlinger.json 
         -c user_data/config.currencyUSDT.json 
         -c user_data/config.exchangeBinance.json"
BACKTESTING_TIMERANGE="--timerange 20210510-20210530"
BACKTESTING_STRATEGY="--strategy StrategyKlinger"
DEBUGPY_SETTINGS="--listen 5678 --wait-for-client"

case $* in
--backtest|-b)
source .env/bin/activate
python -m debugpy ${DEBUGPY_SETTINGS} -m freqtrade backtesting  --export=trades --timeframe 5m ${BACKTESTING_STRATEGY} ${CONFIGS} ${BACKTESTING_TIMERANGE}
;;
--trade|-t)
python -m debugpy ${DEBUGPY_SETTINGS} -m freqtrade trade ${CONFIGS}
;;
esac

exit 0