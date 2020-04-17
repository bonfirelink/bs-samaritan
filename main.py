from pydantic import BaseModel
from fastapi import FastAPI
from web3 import Web3
import json
import uvicorn

environment = None
erc20_abi = None


class Beg(BaseModel):
    recipient_address: str

app = FastAPI()

with open("erc20abi.json") as f:
    erc20_abi = json.load(f)

with open("env.json") as f:
    environment = json.load(f)

contract_address = environment['contract_address']
private_key = environment['private_key']
from_address = environment['public_key']
eth_api_url = environment['eth_api_url']

@app.post("/begs/")
async def send_coins(beg: Beg):    
    
    w3 = Web3(
        Web3.HTTPProvider(eth_api_url)
    )
    if w3.isAddress(beg.recipient_address) is not True:
        return {"bad address"}
    
    to_address = w3.toChecksumAddress(beg.recipient_address)
    bs = w3.eth.contract(address=w3.toChecksumAddress(contract_address), abi=erc20_abi)
    nonce = w3.eth.getTransactionCount(from_address) + 1

    bs_txn = bs.functions.transfer(to_address, 1).buildTransaction(
        {"chainId": 1, "gas": 70000, "gasPrice": w3.toWei("1", "gwei"), "nonce": nonce,}
    )

    signed_txn = w3.eth.account.sign_transaction(bs_txn, private_key=private_key)
    broadcasted_txn = w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    return {"recipient": to_address, "tx_hash": signed_txn.hash.hex()}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
