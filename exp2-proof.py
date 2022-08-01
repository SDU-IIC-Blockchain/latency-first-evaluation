import json
import os
import time

from web3 import Web3
from web3.middleware import geth_poa_middleware

HOST = os.environ.get('ETH_HOST', '127.0.0.1')
PORT = os.environ.get('ETH_PORT', '8545')
ETH_ENDPOINT = f'http://{HOST}:{PORT}'
ETH_CONSENSUS = os.environ.get('ETH_CONSENSUS', 'clique')


def connect_eth() -> Web3:
    print('Connecting...', flush=True)
    w3 = Web3(Web3.HTTPProvider(ETH_ENDPOINT))
    if not w3.isConnected():
        raise Exception(f'Can not connect to {ETH_ENDPOINT}')
    print(f'Connected to {ETH_ENDPOINT}.', flush=True)

    if ETH_CONSENSUS == 'clique':
        # inject the poa compatibility middleware to the innermost layer
        # https://web3py.readthedocs.io/en/stable/middleware.html#geth-style-proof-of-authority
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    # set the sender account
    w3.eth.default_account = w3.eth.accounts[0]
    print(f'Use account {w3.eth.default_account}.')

    return w3


def wait_for_receipt(w3, tx_hash: bytes, timeout: float = 120, poll_latency: float = 0.1):
    print(f'Waiting for transaction {tx_hash.hex()} to be mined...', flush=True)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout, poll_latency=poll_latency)
    print(f'Transaction sealed.', flush=True)
    return tx_receipt


if __name__ == '__main__':
    # connect to ethereum
    w3 = connect_eth()

    with open('exp2-data.json', mode='r', encoding='utf-8') as f:
        exp2_data = json.load(f)

    # deploy the contract
    instance = w3.eth.contract(
        address=exp2_data['contract-addr'],
        abi=exp2_data['contract-abi'],
    )

    instance_id = int(os.environ.get('MY_ID'))
    assert instance_id % 2 == 0
    addresses = [
        exp2_data['accounts'][instance_id],
        exp2_data['accounts'][instance_id + 1],
    ]

    print('Proofing...')
    transfer_value = 1
    # pending_state_nums = [instance.functions.__tx_pending_len_Transfer(addr).call() for addr in addresses]
    # assert pending_state_nums[0] == 1 and pending_state_nums[1] == 1
    # instance.functions.__tx_proof_Transfer(addresses, [transfer_value]).call()

    while True:
        try:
            wait_for_receipt(
                w3, instance.functions.__tx_proof_Transfer(addresses, [transfer_value]).transact(), 120, 1)
            break
        except Exception as e:
            print(e)
    time_end = time.time_ns()
    print(f'Timestamp: {time_end} ns')
