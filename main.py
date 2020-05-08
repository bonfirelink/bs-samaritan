import json
import uvicorn
import threading
import logging

from pydantic import BaseModel
from fastapi import FastAPI
from web3 import Web3
from web3.gas_strategies.time_based import medium_gas_price_strategy
from gas_price import fetch_gas_price_forever

environment = None
erc20_abi = None

gas_thread = threading.Thread(target=fetch_gas_price_forever, daemon=True)
gas_thread.start()


class Beg(BaseModel):
    recipient_address: str


app = FastAPI()

with open("erc20abi.json") as f:
    erc20_abi = json.load(f)

with open("env.json") as f:
    environment = json.load(f)

contract_address = environment["contract_address"]
private_key = environment["private_key"]
from_address = environment["public_key"]
eth_api_url = environment["eth_api_url"]


@app.post("/begs/")
async def send_coins(beg: Beg):
    logging.info("I hear a beg")
    w3 = Web3(Web3.HTTPProvider(eth_api_url))
    if w3.isAddress(beg.recipient_address) is not True:
        return {"bad address"}

    gas_price = w3.toWei("6", "gwei")
    try:
        with open("gas_price.json") as f:
            gas_price = json.load(f)["gas_price"]
    except OSError as e:
        logging.warning("Could not read gas price! " + e)

    to_address = w3.toChecksumAddress(beg.recipient_address)
    bs = w3.eth.contract(address=w3.toChecksumAddress(contract_address), abi=erc20_abi)
    nonce = w3.eth.getTransactionCount(from_address)

    bs_txn = bs.functions.transfer(to_address, 1).buildTransaction(
        {"chainId": 1, "gas": 50000, "gasPrice": gas_price, "nonce": nonce,}
    )

    signed_txn = w3.eth.account.sign_transaction(bs_txn, private_key=private_key)
    broadcasted_txn = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    logging.info("Transaction hex: " + repr(signed_txn.hash.hex()))
    return {"recipient": to_address, "tx_hash": signed_txn.hash.hex()}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
