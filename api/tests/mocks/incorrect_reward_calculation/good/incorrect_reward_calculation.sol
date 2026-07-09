pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract IncorrectRewardCalculationGood {
    struct UserInfo {
        uint256 amount;
        uint256 rewardDebt;
    }

    mapping(address => UserInfo) public userInfo;
    uint256 public accRewardPerShare;
    IERC20 public stakingToken;
    IERC20 public rewardToken;

    function deposit(uint256 amount) external {
        UserInfo storage user = userInfo[msg.sender];
        if (user.amount > 0) {
            uint256 pending = user.amount * accRewardPerShare / 1e12 - user.rewardDebt;
            rewardToken.transfer(msg.sender, pending);
        }
        user.amount += amount;
        user.rewardDebt = user.amount * accRewardPerShare / 1e12;
        stakingToken.transferFrom(msg.sender, address(this), amount);
    }
}
