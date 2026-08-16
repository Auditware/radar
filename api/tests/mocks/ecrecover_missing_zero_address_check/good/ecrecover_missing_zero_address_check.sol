pragma solidity ^0.8.0;

contract EcrecoverGood {
    function verify(bytes32 hash, uint8 v, bytes32 r, bytes32 s, address expected) external pure returns (bool) {
        address signer = ecrecover(hash, v, r, s);
        require(signer != address(0), "invalid signature");
        return signer == expected;
    }
}
