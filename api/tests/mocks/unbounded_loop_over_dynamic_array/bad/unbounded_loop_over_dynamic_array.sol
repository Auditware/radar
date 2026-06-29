pragma solidity ^0.8.0;

contract UnboundedLoopOverDynamicArrayBad {
    address[] public users;

    function processUsers() external view returns (uint256 total) {
        for (uint256 i = 0; i < users.length; i++) {
            total += i;
        }
    }
}
