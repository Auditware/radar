pragma solidity ^0.8.0;

contract UnprotectedConfigurationSettersBad {
    uint256 public fee;

    function setFee(uint256 _fee) public {
        fee = _fee;
    }
}
