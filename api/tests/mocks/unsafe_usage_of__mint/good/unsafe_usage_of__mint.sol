pragma solidity ^0.8.0;

abstract contract ERC20 {
    mapping(address => uint256) public balanceOf;
    uint256 public totalSupply;
    function _mint(address to, uint256 amount) internal virtual {
        balanceOf[to] += amount;
        totalSupply += amount;
    }
}

contract TokenGood is ERC20 {
    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
}
