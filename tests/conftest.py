#!/usr/bin/python3

import pytest
from brownie import MockFTGToken, accounts
from brownie import FTGSale, NTT
from scripts.deploy_FTGStaking import deploy_FTGStaking


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module", autouse=True)
def ftgtoken(MockFTGToken, accounts):
    print("ftgtoken deployment by accounts[0]=", accounts[0])
    return MockFTGToken.deploy(400_000_000 * 10 ** 18, {"from": accounts[0]})


@pytest.fixture(scope="module", autouse=True)
def investtoken(MockFTGToken, accounts):
    print("investtoken deployment by accounts[0]=", accounts[0])
    return MockFTGToken.deploy(100_000_000 * 10 ** 18, {"from": accounts[0]})


@pytest.fixture(scope="module", autouse=True)
def distribute_tokens(ftgtoken, investtoken):
    for i in range(1, 50):
        ftgtoken.transfer(accounts[i], 5000000 * 10 ** 18, {"from": accounts[0]})
        investtoken.transfer(accounts[i], 1_000_000 * 10 ** 18, {"from": accounts[0]})

