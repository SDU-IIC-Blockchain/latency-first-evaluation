import json
import os
import time

import solcx
from web3 import Web3
from web3.middleware import geth_poa_middleware

HOST = os.environ.get('ETH_HOST', '127.0.0.1')
PORT = os.environ.get('ETH_PORT', '8545')
ETH_ENDPOINT = f'http://{HOST}:{PORT}'
ETH_CONSENSUS = os.environ.get('ETH_CONSENSUS', 'clique')
CONTRACT_FILE = os.environ.get('SOL_PATH', './contracts/transfer.sol')
account_num = int(os.environ.get('ACCOUNT_NUM', 1000))


def connect_eth() -> Web3:
    print('Connecting...')
    w3 = Web3(Web3.HTTPProvider(ETH_ENDPOINT))
    if not w3.isConnected():
        raise Exception(f'Can not connect to {ETH_ENDPOINT}')
    print(f'Connected to {ETH_ENDPOINT}.')

    if ETH_CONSENSUS == 'clique':
        # inject the poa compatibility middleware to the innermost layer
        # https://web3py.readthedocs.io/en/stable/middleware.html#geth-style-proof-of-authority
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    # set the sender account
    w3.eth.default_account = w3.eth.accounts[0]
    print(f'Use account {w3.eth.default_account}.')

    return w3


def load_solc():
    solcx.import_installed_solc()
    solcs = solcx.get_installed_solc_versions()
    if len(solcs) == 0:
        raise Exception('Can not find solc in $PATH. Please install solc first.')
    solcx.set_solc_version(solcs[0])
    print(f'solc {solcs[0]} is loaded.')


def compile_contract():
    print(f'Compiling {CONTRACT_FILE}')
    compiled_sol = solcx.compile_files(
        CONTRACT_FILE,
        output_values=["abi", "bin"],
        optimize=True,
    )

    # retrieve the contract interface
    contract_id, contract_interface = compiled_sol.popitem()

    bytecode = contract_interface['bin']
    abi = contract_interface['abi']

    return bytecode, abi


def wait_for_receipt(w3, tx_hash: bytes, mute: bool = False):
    if not mute:
        print(f'Waiting for transaction {tx_hash.hex()} to be mined...')
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if not mute:
        print(f'Transaction sealed.')
    return tx_receipt


def deploy_contract(w3, bytecode, abi):
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    print('Deploying the contract...')
    # Submit the transaction that deploys the contract
    tx_hash = contract.constructor().transact()
    # Wait for the transaction to be mined, and get the transaction receipt
    tx_receipt = wait_for_receipt(w3, tx_hash)

    instance = w3.eth.contract(
        address=tx_receipt.contractAddress,
        abi=abi,
    )

    return instance


# Yield successive n-sized chunks from l.
# https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
def divide_chunks(l: list, n: int):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]


if __name__ == '__main__':
    # compile and deploy the contract
    load_solc()
    bytecode, abi = compile_contract()

    # connect to ethereum
    w3 = connect_eth()

    # deploy the contract
    instance = deploy_contract(w3, bytecode, abi)

    # generate accounts
    accounts = []
    for i in range(account_num):
        acc = w3.eth.account.create()
        accounts.append(acc.address)

    print(f'Funding {len(accounts)} accounts...')
    tx_hashes = []
    for account_chunks in divide_chunks(accounts, 50):
        tx_hashes.append(instance.functions.FundAccounts(account_chunks).transact())

    for i in range(len(tx_hashes)):
        print(f'Wait-Fund({i, len(tx_hashes)})', end='\r')
        wait_for_receipt(w3, tx_hashes[i], mute=True)
    print()

    for i in range(len(accounts)):
        print(f'Check({i, len(accounts)})', end='\r')
        assert instance.functions.GetAccountBalance(accounts[i]).call() == 10000
    print()

    exp2_data = {
        'accounts': accounts,
        'contract-addr': instance.address,
        'contract-abi': abi,
    }

    with open('exp2-data.json', mode='w', encoding='utf-8') as f:
        json.dump(exp2_data, f)
         
    # if os.environ.get('MODE') == 'offline':
    #     print('Make an offline transaction...')
    #     assert len(accounts) % 2 == 0
    #     tx_hashes = []
    #     for i in range(0, len(accounts), 2):
    #         print(f'Commit({i, len(tx_hashes)})', end='\r')
    #         my_accounts = [accounts[i], accounts[i + 1]]
    #         # # Make sure there are no pending states
    #         # pending_state_nums = [instance.functions.__tx_pending_len_Transfer(addr).call() for addr in addresses]
    #         # assert not any(pending_state_nums)
    #
    #         # Fetch the latest states
    #         states = [instance.functions.__tx_state_latest_Transfer(addr).call() for addr in my_accounts]
    #         transfer_value = 1
    #         new_states, hashes = instance.functions.__tx_offline_Transfer(my_accounts, states, [transfer_value]).call()
    #         tx_hashes.append(instance.functions.__tx_commit_Transfer(my_accounts, hashes).transact())
    #     print()
    #     for i in range(len(tx_hashes)):
    #         print(f'Wait-Commit({i, len(tx_hashes)})', end='\r')
    #         wait_for_receipt(w3, tx_hashes[i], mute=True)
    #     print()
    #
    #     print('Proofing...')
    #     tx_hashes = []
    #     for i in range(0, len(accounts), 2):
    #         print(f'Proof({i, len(tx_hashes)})', end='\r')
    #         addresses = [accounts[i], accounts[i + 1]]
    #         transfer_value = 1
    #         tx_hashes.append(instance.functions.__tx_proof_Transfer(addresses, [transfer_value]).transact())
    #     print()
    #     for i in range(len(tx_hashes)):
    #         print(f'Wait-Proof({i, len(tx_hashes)})', end='\r')
    #         wait_for_receipt(w3, tx_hashes[i], mute=True)
    #     print()
    # elif os.environ.get('MODE') == 'online':
    #     print('Transferring...')
    #     tx_hashes = []
    #     for i in range(0, len(accounts), 2):
    #         print(f'Transfer({i, len(tx_hashes)})', end='\r')
    #         addresses = [accounts[i], accounts[i + 1]]
    #         transfer_value = 1
    #         tx_hashes.append(instance.functions.__tx_online_Transfer(addresses, [transfer_value]).transact())
    #     for i in range(len(tx_hashes)):
    #         print(f'Wait({i, len(tx_hashes)})', end='\r')
    #         wait_for_receipt(w3, tx_hashes[i], mute=True)
    #     print()
    # else:
    #     assert False