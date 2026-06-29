pragma solidity ^0.8.0;

interface IVault {
    function deposit(address from, uint256 amount) external;
}

contract ReentrancyViaERC777HookGood {
    IVault public vault;

    modifier nonReentrant() {
        _;
    }

    constructor(IVault _vault) {
        vault = _vault;
    }

    function tokensReceived(address operator, address from, address to, uint256 amount, bytes calldata data, bytes calldata operatorData) external nonReentrant {
        operator;
        to;
        data;
        operatorData;
        vault.deposit(from, amount);
    }
}
