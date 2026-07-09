pragma solidity ^0.8.0;

interface ICurvePool {
    function get_virtual_price() external view returns (uint256);
}

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
}

contract ReadOnlyReentrancyGood {
    ICurvePool public curvePool;
    IERC20 public token;
    mapping(address => uint256) public collateral;
    bool private locked;

    modifier nonReentrant() {
        require(!locked, "reentrant");
        locked = true;
        _;
        locked = false;
    }

    constructor(ICurvePool _pool, IERC20 _token) {
        curvePool = _pool;
        token = _token;
    }

    function liquidate(address user) external nonReentrant {
        uint256 price = curvePool.get_virtual_price();
        uint256 value = collateral[user] * price / 1e18;
        collateral[user] = 0;
        token.transfer(user, value);
    }
}
