import json
import os

def write(fn, fo):    
    with open(fn, "r") as f:
        x =f.read()
        z = json.loads(x)["abi"]
        zd = {"abi": z}
        
        if len(z)==0: return

        with open(fo, "w") as o:
            o.write(json.dumps(zd))



l = os.listdir("./build/contracts")
for x in l:
    print("write ", x)
    fn = "./build/contracts/%s"%x
    fo = "./abi/%s"%x
    write(fn, fo)


#fns = ["BondDepository","StakingDistributor","StakingHelper","StakingWarmup","StandardBondingCalculator","MEME","Treasury","MagERC20","MockTreasury","sMAGToken","Staking"]

# for fn in fns:
#     fn = "./build/contracts/%s.json"%fn
#     fo = "%s.json"%fn
#     write(fn, fo)


# fn = "./artifacts/contracts/NRT.sol/NRT.json"

# with open(fn, "r") as f:
#     x =f.read()
#     z = json.loads(x)["abi"]

#     with open("NRT.abi", "w") as o:
#         o.write(json.dumps(z))        