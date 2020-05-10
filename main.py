import configparser
import json
import logging

from pydantic import BaseModel
from fastapi import FastAPI
from web3 import Web3
from web3.gas_strategies.time_based import slow_gas_price_strategy
from fastapi import HTTPException

CONFIG_FILE = "config.ini"
SECTION = "samaritan"


class Beg(BaseModel):
    recipient_address: str


config = configparser.ConfigParser()
config.read(CONFIG_FILE)

with open("erc20abi.json") as f:
    erc20_abi = json.load(f)

w3 = Web3(Web3.HTTPProvider(config.get(SECTION, "eth_api_url")))
w3.eth.setGasPriceStrategy(slow_gas_price_strategy)

app = FastAPI()


@app.post("/begs/")
async def send_coins(beg: Beg):

    logging.info("I hear a beg from " + beg.recipient_address)
    if w3.isAddress(beg.recipient_address) is not True:
        raise HTTPException(status_code=400, detail="Invalid address.")

    to_address = w3.toChecksumAddress(beg.recipient_address)
    bs = w3.eth.contract(
        address=w3.toChecksumAddress(config.get(SECTION, "contract_address")),
        abi=erc20_abi,
    )
    nonce = w3.eth.getTransactionCount(config.get(SECTION, "public_key"))
    gas_price = w3.eth.gasPrice
    bs_txn = bs.functions.transfer(to_address, 1000).buildTransaction(
        {"chainId": 1, "gas": 60000, "gasPrice": gas_price, "nonce": nonce,}
    )

    signed_txn = w3.eth.account.sign_transaction(
        bs_txn, private_key=config.get(SECTION, "private_key")
    )
    broadcasted_txn = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    logging.info("Transaction hex: " + repr(signed_txn.hash.hex()))
    logging.info("Gas price: " + str(gas_price))

    return {"recipient": to_address, "tx_hash": signed_txn.hash.hex()}
