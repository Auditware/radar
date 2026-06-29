pragma solidity ^0.8.0;

contract UnboundedLoopOverDynamicArrayGood {
    address[] public users;

    function processUsers(uint256 fromIndex, uint256 toIndex) external view returns (uint256 total) {
        require(toIndex <= users.length, "range too large");
        for (uint256 i = fromIndex; i < toIndex; i++) {
            total += i;
        }
    }
}
