#!/usr/bin/python3

import pytest
from brownie import MockFTGToken, accounts


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module", autouse=True)
def ftgtoken(MockFTGToken, accounts):
    print("Reinitialize FTGToken by accounts[0]=", accounts[0])
    return MockFTGToken.deploy(30000000 * 10**18, {"from": accounts[0]})


@pytest.fixture(scope="module", autouse=True)
def investtoken(MockFTGToken, accounts):
    print("Reinitialize FTGToken by accounts[0]=", accounts[0])
    return MockFTGToken.deploy(30000000 * 10**18, {"from": accounts[0]})

@pytest.fixture(scope="module", autouse=True)
def distribute_tokens(ftgtoken):
    for i in range(1, 3):
        ftgtoken.transfer(accounts[i], 10000, {"from": accounts[0]})
