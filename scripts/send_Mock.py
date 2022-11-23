#!/usr/bin/python3

from brownie import accounts, network
from brownie import FTGStaking, MockFTGToken, MockStable

testaddresses = [
        "0x6FcB6f4EDA59076B5673c909EF60227eFd90FBf7",
        "0xE6E86D543D3B6Bc43D9a480038CeFc6b1b2Bd4Fc",
        "0x99cBe0b7C39Edd6d892b7021199Ac9eaC4af83B1",
        "0xce87196D37A99c8a49a9811a2d9AeEE321D551B4",
        "0x9b28F08F28Bd465361BD1Bb0C848e3e39F52bcAb",
        "0x33b6FAE2F6e31f57FB15768A25E4B0733680eBE2",
        "0xD9F97D76e2193BE8b8b5f95A7840a5a656F65d71",
        "0x48dF73d1AaAb29241DDeC590B68FaFfb365Ec68E",
]

def send_ftg(mainaccount):
    ftgmockAddress = "0xC54Aee27538ae906034e9f2f1A784778ab55d861"
    ftgmock = MockFTGToken.at(ftgmockAddress)
    print("ftgmock ", ftgmock)
    print("ftgmock ", ftgmock.decimals())
    print("mainaccount ", mainaccount)
    print("main FTG balance ", ftgmock.balanceOf(mainaccount) / 10**18)
    print("main ETH balance ", mainaccount.balance())

    for addr in testaddresses[-1:]:
        a = 5 * 10**6 * 10**18
        ftgmock.transfer(addr, a, {"from": mainaccount})

def send_stable(mainaccount):
    
    mockstable = MockStable.at("0xEC5082A73242613a7d8C27515B10B77aB3E6e530")
    print("mockstable ", mockstable)
    print("ftgmock ", mockstable.decimals())
    print("mainaccount ", mainaccount)
    print("main FTG balance ", mockstable.balanceOf(mainaccount) / 10**18)
    print("main ETH balance ", mainaccount.balance())

    

    for addr in testaddresses[-1:]:
        a = 1 * 10**6 * 10**18
        mockstable.transfer(addr, a, {"from": mainaccount})

        

def main():
    # Fetch the account
    # account = accounts[0]
    # pk1 = "b5f58344a9513b68d2f20435107de17d865b01d603f4558fef27c1fed071d8e2"
    pk2 = "c43766a57a118e09e3b4dcda38685d2b1bc6e0872af1f9e51dd4bd704d77abde"
    mainaccount = accounts.add(pk2)

    #mockstable = MockStable.deploy(100 * 10**6 * 10**18, {"from": mainaccount})
    mockstable = MockStable.at("0xEC5082A73242613a7d8C27515B10B77aB3E6e530")
    print("mockstable ", mockstable)

    send_stable(mainaccount)
    send_ftg(mainaccount)
    