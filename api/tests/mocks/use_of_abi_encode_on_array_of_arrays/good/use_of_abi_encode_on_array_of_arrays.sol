// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

// Same public API, but the matrix is flattened explicitly before encoding, so
// the digest no longer depends on the encoder's nested-array layout.
contract MatrixCommitment {
    function commit(uint256[2][3] calldata matrix) external pure returns (bytes32) {
        uint256[6] memory flattened;
        for (uint256 i = 0; i < 3; i++) {
            for (uint256 j = 0; j < 2; j++) {
                flattened[i * 2 + j] = matrix[i][j];
            }
        }
        return keccak256(abi.encode(flattened));
    }
}
