#!/usr/bin/python3

from brownie import accounts, network
from brownie import FTGStaking, MockFTGToken, FTGSale



def main(): 
    # Fetch the account 
    #account = accounts[0] 
    #pk1 = "b5f58344a9513b68d2f20435107de17d865b01d603f4558fef27c1fed071d8e2"
    pk2 = "c43766a57a118e09e3b4dcda38685d2b1bc6e0872af1f9e51dd4bd704d77abde"
    print(network.chain.id)
    mainaccount = accounts.add(pk2)
    print(mainaccount)
    print("balance ", mainaccount.balance()/10**18)

    #FTGToken deployed to  0xC54Aee27538ae906034e9f2f1A784778ab55d861
    #FTGStaking deployed to  0x7cba9dcC55C3493325db6EBbe7ffbe7AA9F9c4df
    #FTGSale deployed to  0x29Ad8d496E63641B35d1Ad12f11A6eAec15fE4D6

    #FTGToken = 0xC54Aee27538ae906034e9f2f1A784778ab55d861
    ftgstaking = "0x7cba9dcC55C3493325db6EBbe7ffbe7AA9F9c4df"
    
    #_amountGuaranteedPool = 1000000
    #_amountPublicPool = 1000000
    _tokenPriceInUSD = 100    
    #investtoken = MockFTGToken.deploy(1000000 * 10**18, {"from": accounts[0]})
    #saletoken = MockFTGToken.deploy(1000000 * 10**18, {"from": mainaccount})

    #investtoken = 0x7bEB5aD5e3869eE3DB48A2aCF334B180AA38c276
    investtoken = "0x901E7caE144726cB1F41Cc2861E912EeF0AC9E3a"
    saletoken = "0x61Ba43a2469a32801520160ca0e29b2726874CC5"

    #salectr = FTGSale.deploy("TestSale", investtoken , saletoken, ftgstaking, _tokenPriceInUSD, {"from": mainaccount})
    # salectr = FTGSale.at("0xEa958dADd3Fee6DFcf6F4545ABD3ed2c8c28D427")
    # print(salectr.nameSale())
    # #salectr.setMins(1000, 500, 200, 100, {"from": mainaccount})
    # salectr.setAllocs(40, 30, 20, 10, {"from": mainaccount})
    #print(salectr)
   