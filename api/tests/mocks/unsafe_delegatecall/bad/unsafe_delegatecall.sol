// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

// The target address and the payload both come straight from the caller, so any
// account can make this contract execute arbitrary code against its own storage.
contract Executor {
    function execute(address target, bytes calldata data) external returns (bytes memory) {
        (bool ok, bytes memory ret) = target.delegatecall(data);
        require(ok, "delegatecall failed");
        return ret;
    }
}
