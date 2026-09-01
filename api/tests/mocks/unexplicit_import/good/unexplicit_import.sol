// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

// The vendored dependency is imported from a version-pinned path, so a new
// major release of the library cannot silently change what this contract compiles against.
import "lib/erc20@4.9.3/IERC20.sol";

contract Payments {
    IERC20 public immutable token;

    constructor(IERC20 _token) {
        token = _token;
    }

    function pay(address to, uint256 amount) external {
        token.transfer(to, amount);
    }
}
