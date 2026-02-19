// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";

contract SimpleContract is Test {
    uint256 public value;
    
    function setValue(uint256 _value) public {
        value = _value;
    }
}
