pragma solidity ^0.8.0;

contract SignatureMissingNonceOrChainidGood {
    mapping(address => uint256) public nonces;

    function claim(address user, uint256 amount, uint8 v, bytes32 r, bytes32 s) external returns (address) {
        bytes32 hash = keccak256(abi.encodePacked(user, amount, nonces[user]++, block.chainid));
        return ecrecover(hash, v, r, s);
    }
}
