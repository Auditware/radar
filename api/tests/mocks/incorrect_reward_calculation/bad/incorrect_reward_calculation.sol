pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract IncorrectRewardCalculationBad {
    struct UserInfo {
        uint256 amount;
        uint256 rewardDebt;
    }

    mapping(address => UserInfo) public userInfo;
    uint256 public accRewardPerShare;
    IERC20 public stakingToken;

    function deposit(uint256 amount) external {
        UserInfo storage user = userInfo[msg.sender];
        user.amount += amount;
        stakingToken.transferFrom(msg.sender, address(this), amount);
    }
}
