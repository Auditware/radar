pragma solidity ^0.8.0;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

contract VaultShareInflationGood {
    IERC20 public token;
    uint256 public totalSupply;
    uint256 public totalAssets;
    mapping(address => uint256) public balanceOf;

    constructor(IERC20 _token) {
        token = _token;
    }

    function deposit(uint256 amount) external returns (uint256 shares) {
        shares = totalSupply == 0 ? amount : amount * totalSupply / totalAssets;
        totalSupply += shares;
        totalAssets += amount;
        balanceOf[msg.sender] += shares;
        token.transferFrom(msg.sender, address(this), amount);
    }
}
