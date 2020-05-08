from web3 import Web3
from web3.gas_strategies.time_based import slow_gas_price_strategy
import json
import sched
import time
import threading
import logging
import os

WAIT_TIME_SECONDS = 300

def fetch_gas_price():
    logging.info("Fetching new gas price")
    with open("env.json") as f:
        environment = json.load(f)

    eth_api_url = environment["eth_api_url"]
    w3 = Web3(Web3.HTTPProvider(eth_api_url))
    w3.eth.setGasPriceStrategy(slow_gas_price_strategy)
    api_gas_price = w3.eth.generateGasPrice()
    data = {}
    data["gas_price"] = api_gas_price
    data["timestamp"] = time.time()
    
    with open("gas_price.json", "w") as outfile:
        json.dump(data, outfile)

    logging.info("Got a price of " + str(api_gas_price))


def fetch_gas_price_forever():
    logging.info("Gas price thread start")
    fetch_gas_price()
    ticker = threading.Event()
    while not ticker.wait(WAIT_TIME_SECONDS):
        fetch_gas_price()
