from pydantic import BaseModel
from fastapi import FastAPI
from web3 import Web3
import json
import uvicorn


class Beg(BaseModel):
    recipient_address: str


app = FastAPI()
with open("erc20abi.json") as f:
    erc20_abi = json.load(f)


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/begs/")
async def send_coins(beg: Beg):

    w3 = Web3(
        Web3.HTTPProvider(
            "https://mainnet.infura.io/v3/5e7c6e7f901840d28faa64699c1e02de"
        )
    )
    if w3.isAddress(beg.recipient_address) is not True:
        return {"bad address"}

    bs_address = w3.toChecksumAddress("0x91bc206f0a1ffbc399b4a20a41324ed1dad2b718")
    from_address = w3.toChecksumAddress("0x0a437f83726520767fca1936544d779b5d384a04")
    to_adress = w3.toChecksumAddress(beg.recipient_address)
    private_key = b"\xb2\\}\xb3\x1f\xee\xd9\x12''\xbf\t9\xdcv\x9a\x96VK-\xe4\xc4rm\x03[6\xec\xf1\xe5\xb3d"

    bs = w3.eth.contract(address=bs_address, abi=erc20_abi)
    nonce = w3.eth.getTransactionCount(from_address)

    bs_txn = bs.functions.transfer(to_adress, 1).buildTransaction(
        {"chainId": 1, "gas": 70000, "gasPrice": w3.toWei("1", "gwei"), "nonce": nonce,}
    )

    signed_txn = w3.eth.account.sign_transaction(bs_txn, private_key=private_key)
    #w3.eth.sendRawTransaction(signed_txn.raw_transaction)
    return {"recipient": to_adress, "tx_hash": signed_txn.hash.hex()}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
