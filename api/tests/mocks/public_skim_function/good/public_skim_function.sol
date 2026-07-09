pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract PublicSkimFunctionGood {
    IERC20 public token0;
    IERC20 public token1;
    uint256 public reserve0;
    uint256 public reserve1;
    address public owner;

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor(IERC20 _token0, IERC20 _token1) {
        token0 = _token0;
        token1 = _token1;
        owner = msg.sender;
    }

    function skim(address to) external onlyOwner {
        token0.transfer(to, token0.balanceOf(address(this)) - reserve0);
        token1.transfer(to, token1.balanceOf(address(this)) - reserve1);
    }
}
