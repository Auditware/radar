pragma solidity ^0.8.0;

contract SignatureMissingNonceOrChainidBad {
    function claim(address user, uint256 amount, uint8 v, bytes32 r, bytes32 s) external pure returns (address) {
        bytes32 hash = keccak256(abi.encodePacked(user, amount));
        return ecrecover(hash, v, r, s);
    }
}
