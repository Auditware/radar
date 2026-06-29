pragma solidity ^0.8.0;

contract UncheckedLowLevelCallReturnBad {
    function execute(address target, bytes calldata data, uint256 amount) external {
        target.call{value: amount}(data);
    }
}
