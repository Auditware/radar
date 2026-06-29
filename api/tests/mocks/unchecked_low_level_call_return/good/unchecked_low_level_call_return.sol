pragma solidity ^0.8.0;

contract UncheckedLowLevelCallReturnGood {
    function execute(address target, bytes calldata data, uint256 amount) external {
        (bool success, ) = target.call{value: amount}(data);
        require(success, "call failed");
    }
}
