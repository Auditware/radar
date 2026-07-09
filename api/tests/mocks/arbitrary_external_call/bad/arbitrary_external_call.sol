pragma solidity ^0.8.0;

contract ArbitraryExternalCallBad {
    function execute(address target, bytes calldata data) external payable {
        (bool success,) = target.call{value: msg.value}(data);
        require(success, "call failed");
    }
}
