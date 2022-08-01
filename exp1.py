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
CONTRACT_ACCOUNTS = [Web3.toChecksumAddress(addr) for addr in [
    'b3270be37a758e67a67fc6f2b62247cc58e0e61f',
    '203aa027380819d58897763131b1183048c08a90',
]]


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


def wait_for_receipt(w3, tx_hash: bytes):
    print(f'Waiting for transaction {tx_hash.hex()} to be mined...')
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
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


if __name__ == '__main__':
    # compile and deploy the contract
    load_solc()
    bytecode, abi = compile_contract()

    # connect to ethereum
    w3 = connect_eth()

    # deploy the contract
    instance = deploy_contract(w3, bytecode, abi)

    print('Funding accounts...')
    wait_for_receipt(w3, instance.functions.FundAccounts(CONTRACT_ACCOUNTS).transact())
    print('Make an online transaction...')
    transfer_value = 1
    wait_for_receipt(w3, instance.functions.__tx_online_Transfer(CONTRACT_ACCOUNTS, [transfer_value]).transact())

    print('Make an offline transaction...')
    time_start = time.time_ns()
    # Make sure there are no pending states
    pending_state_nums = [instance.functions.__tx_pending_len_Transfer(addr).call() for addr in CONTRACT_ACCOUNTS]
    assert not any(pending_state_nums)
    # Fetch the latest states
    states = [instance.functions.__tx_state_latest_Transfer(addr).call() for addr in CONTRACT_ACCOUNTS]
    transfer_value = 1
    new_states, hashes = instance.functions.__tx_offline_Transfer(CONTRACT_ACCOUNTS, states, [transfer_value]).call()

    print('Committing...')
    wait_for_receipt(w3, instance.functions.__tx_commit_Transfer(CONTRACT_ACCOUNTS, hashes).transact())
    time_end = time.time_ns()
    print(f'Latency: {time_end - time_start} ns')

    print('Proofing...')
    wait_for_receipt(w3, instance.functions.__tx_proof_Transfer(CONTRACT_ACCOUNTS, [transfer_value]).transact())
