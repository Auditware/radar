// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// The same vendored dependency is pulled in twice.
import "lib/erc20/IERC20.sol";
import "lib/erc20/IERC20.sol";

contract Payments {
    IERC20 public immutable token;

    constructor(IERC20 _token) {
        token = _token;
    }

    function pay(address to, uint256 amount) external {
        token.transfer(to, amount);
    }
}
