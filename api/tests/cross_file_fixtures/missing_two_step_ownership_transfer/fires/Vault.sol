// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// A second file that has nothing to do with ownership. Its only job is to make
// this a multi-file project, so the rule's first pass has more than one source
// to walk before its second pass decides.
contract Vault {
    uint256 public total;

    function deposit(uint256 amount) public {
        total += amount;
    }
}
