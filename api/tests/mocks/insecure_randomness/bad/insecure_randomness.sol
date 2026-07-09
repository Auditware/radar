pragma solidity ^0.8.0;

contract InsecureRandomnessBad {
    uint256 public nonce;

    function getRandomNumber() public returns (uint256) {
        nonce++;
        return uint256(keccak256(abi.encodePacked(block.timestamp, msg.sender, nonce)));
    }
}
