pragma solidity ^0.8.0;

contract EcrecoverBad {
    function verify(bytes32 hash, uint8 v, bytes32 r, bytes32 s, address expected) external pure returns (bool) {
        address signer = ecrecover(hash, v, r, s);
        return signer == expected;
    }
}
