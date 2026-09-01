// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

// The multi-dimensional array is handed to abi.encode as-is, so the digest
// depends on how the compiler in use lays nested arrays out in memory.
contract MatrixCommitment {
    function commit(uint256[2][3] calldata matrix) external pure returns (bytes32) {
        return keccak256(abi.encode(matrix));
    }
}
