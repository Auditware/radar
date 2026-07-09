pragma solidity ^0.8.0;

contract ArbitraryExternalCallGood {
    mapping(address => bool) public approved;

    function execute(address target, bytes calldata data) external payable {
        require(approved[target], "target not approved");
        (bool success,) = target.call{value: msg.value}(data);
        require(success, "call failed");
    }
}
