pragma solidity ^0.8.0;

contract PayoutGood {
    mapping(address => uint256) public owed;
    address[] public recipients;

    function accrue() external {
        for (uint256 i = 0; i < recipients.length; i++) {
            owed[recipients[i]] += 1 ether;
        }
    }

    function withdraw() external {
        uint256 amount = owed[msg.sender];
        owed[msg.sender] = 0;
        payable(msg.sender).transfer(amount);
    }
}
