pragma solidity ^0.8.0;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
}

contract NoEmergencyPauseMechanismGood {
    IERC20 public token;
    mapping(address => uint256) public deposits;
    bool public paused;

    modifier whenNotPaused() {
        require(!paused, "paused");
        _;
    }

    constructor(IERC20 _token) {
        token = _token;
    }

    function deposit(uint256 amount) external whenNotPaused {
        token.transferFrom(msg.sender, address(this), amount);
        deposits[msg.sender] += amount;
    }

    function withdraw(uint256 amount) external whenNotPaused {
        deposits[msg.sender] -= amount;
        token.transfer(msg.sender, amount);
    }
}
