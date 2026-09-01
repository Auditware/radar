// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

// The vendored dependency is imported by bare name, so the contract silently
// picks up whatever version happens to sit in lib/ at build time.
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
