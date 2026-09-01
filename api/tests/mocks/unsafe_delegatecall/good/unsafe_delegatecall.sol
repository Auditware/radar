// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

// The delegatecall target is fixed at construction and the payload is built by
// the contract itself, so the caller controls neither the code nor the calldata.
contract Executor {
    address private immutable implementation;

    constructor(address implementation_) {
        implementation = implementation_;
    }

    function execute(uint256 amount) external returns (bytes memory) {
        (bool ok, bytes memory ret) = implementation.delegatecall(
            abi.encodeWithSignature("run(uint256)", amount)
        );
        require(ok, "delegatecall failed");
        return ret;
    }
}
