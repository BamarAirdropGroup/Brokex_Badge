

import os
from web3 import Web3
from colorama import init, Fore, Style
import sys


init(autoreset=True)


PHAROS_TESTNET_RPC = "https://testnet.dplabs-internal.com"  

CONTRACT_ADDRESS = Web3.to_checksum_address("0x9979b7fedf761c2989642f63ba6ed580dbdfc46f")

CONTRACT_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_receiver", "type": "address"},
            {"name": "_quantity", "type": "uint256"},
            {"name": "_currency", "type": "address"},
            {"name": "_pricePerToken", "type": "uint256"},
            {
                "name": "_allowlistProof",
                "type": "tuple",
                "components": [
                    {"name": "proof", "type": "bytes32[]"},
                    {"name": "quantityLimitPerWallet", "type": "uint256"},
                    {"name": "pricePerToken", "type": "uint256"},
                    {"name": "currency", "type": "address"}
                ]
            },
            {"name": "_data", "type": "bytes"}
        ],
        "name": "claim",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    }
]

def load_private_keys(file_path):
    """Load private keys from accounts.txt."""
    try:
        with open(file_path, 'r') as file:
            keys = [line.strip() for line in file if line.strip()]
            if not keys:
                print(f"{Fore.RED}No private keys found in {file_path}")
                sys.exit(1)
            return keys
    except Exception as e:
        print(f"{Fore.RED}Error reading {file_path}: {e}")
        sys.exit(1)

def mint_nft(w3, contract, private_key, key_index, total_keys):
    try:
        account = w3.eth.account.from_key(private_key)
        public_key = account.address
        print(f"{Fore.CYAN}Processing key {key_index + 1}/{total_keys} for address {public_key}...")

        balance = w3.eth.get_balance(public_key)
        min_balance = w3.to_wei(1, "ether") + 200000 * w3.to_wei(10, "gwei")
        if balance < min_balance:
            print(f"{Fore.YELLOW}Insufficient balance for {public_key}: {w3.from_wei(balance, 'ether')} PHRS")
            return False

        nonce = w3.eth.get_transaction_count(public_key)

        contract_instance = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

        receiver = public_key
        quantity = 1
        currency = w3.to_checksum_address("0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
        price_per_token = w3.to_wei(1, "ether")
        allowlist_proof = (
            [],
            0,
            0,
            w3.to_checksum_address("0x0000000000000000000000000000000000000000")
        )
        data = b""

        print(f"{Fore.BLUE}Attempting claim for {public_key}...")

        func = contract_instance.functions.claim(
            receiver,
            quantity,
            currency,
            price_per_token,
            allowlist_proof,
            data
        )

        try:
            gas_estimate = func.estimate_gas({
                "from": public_key,
                "value": w3.to_wei(1, "ether")
            })
        except Exception as e:
            print(f"{Fore.RED}Gas estimation failed for {public_key}: {str(e)}")
            return False

        tx = func.build_transaction({
            "chainId": 688688,
            "gas": gas_estimate + 10000,
            "gasPrice": w3.to_wei(10, "gwei"),
            "nonce": nonce,
            "value": w3.to_wei(1, "ether")
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)  # Fixed here
        print(f"{Fore.GREEN}Minting NFT for {public_key}, Tx Hash: {w3.to_hex(tx_hash)}")

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(f"{Fore.GREEN}{Style.BRIGHT}Successfully minted NFT for {public_key}")
            return True
        else:
            print(f"{Fore.RED}Transaction failed for {public_key}: {receipt}")
            return False

    except Exception as e:
        print(f"{Fore.RED}Error minting NFT for {public_key}: {str(e)}")
        return False

def main():

    w3 = Web3(Web3.HTTPProvider(PHAROS_TESTNET_RPC))
    
    if not w3.is_connected():
        print(f"{Fore.RED}Failed to connect to Pharos Testnet. Please check the RPC URL.")
        sys.exit(1)

       


    private_keys = load_private_keys("accounts.txt")
    total_keys = len(private_keys)
    print(f"{Fore.MAGENTA}########## BROKEX Badge Mint Bot##########")
    
    print(f"{Fore.MAGENTA}Found {total_keys} private keys in accounts.txt")
    
    
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)


    for i, private_key in enumerate(private_keys):
        success = mint_nft(w3, contract, private_key, i, total_keys)
        if not success:
            print(f"{Fore.YELLOW}Skipping to next key due to failure...")
        else:
            print(f"{Fore.GREEN}Completed minting for key {i + 1}")

    print(f"{Fore.MAGENTA}{Style.BRIGHT}All {total_keys} private keys processed. Exiting.")
    sys.exit(0)

if __name__ == "__main__":
    main()
