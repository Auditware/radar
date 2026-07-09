pragma solidity ^0.8.0;

interface IVault {
    function deposit(uint256 tokenId) external;
}

contract CallbackTokenReentrancyGood {
    IVault public vault;

    modifier nonReentrant() {
        _;
    }

    constructor(IVault _vault) {
        vault = _vault;
    }

    function onERC721Received(address, address, uint256 tokenId, bytes calldata) external nonReentrant returns (bytes4) {
        vault.deposit(tokenId);
        return this.onERC721Received.selector;
    }
}
