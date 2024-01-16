import random
from loguru import logger
from web3 import Web3
from utils.wallet import Wallet
from settings import VALUE_TUNNEL
from utils.retry import exception_handler

chain_id = {
    'Zora': 7777777,
    'Arbitrum': 42161,
    'Optimism': 10,
    'Nova': 42170,
    'Base': 8453
}

url = {
    'Zora'    : 'https://api-zora.reservoir.tools/execute/call/v1',
    'Arbitrum': 'https://api-arbitrum.reservoir.tools/execute/call/v1',
    'Optimism': 'https://api-optimism.reservoir.tools/execute/call/v1',
    'Nova'    : 'https://api-arbitrum-nova.reservoir.tools/execute/call/v1',
    'Base'    : 'https://api-base.reservoir.tools/execute/call/v1'
}


class TunnelBridge(Wallet):

    def __init__(self, private_key, chain_from, chain_to, number, proxy):
        super().__init__(private_key, chain_from, number, proxy)
        self.chain_to = chain_to

    @exception_handler
    def bridge(self):
        logger.info(f'Tunnel bridge || {self.chain} -> {self.chain_to}')
        value = Web3.to_wei(round(random.uniform(VALUE_TUNNEL[0], VALUE_TUNNEL[1]), VALUE_TUNNEL[2]), 'ether')
        balance = self.get_native_balance()

        json = {
            'originChainId': chain_id[self.chain],
            'user': self.address_wallet,
            'txs': [{
                'data': '0x',
                'to': self.address_wallet,
                'value': str(value)
            }]
        }

        data = self.get_api_call_data_post(url[self.chain_to], json)

        value = int(data['steps'][0]['items'][0]['data']['value'])

        if balance < value:
            value = balance

        if value <= 0:
            logger.error(f'Value bridge ETH - {value}\n')
            return

        dick = {
            'chainId': self.web3.eth.chain_id,
            'from': self.address_wallet,
            'data': data['steps'][0]['items'][0]['data']['data'],
            'to': Web3.to_checksum_address(data['steps'][0]['items'][0]['data']['to']),
            'value': value,
            'nonce': self.web3.eth.get_transaction_count(self.address_wallet),
            **self.get_gas_price()
        }

        gas = int(self.web3.eth.estimate_gas(dick) * 1.3)
        dick.update({'gas': gas})

        self.send_transaction_and_wait(dick, f'Tunnel bridge {round(Web3.from_wei(value, "ether"), 5)} ETH || {self.chain} -> {self.chain_to}')

