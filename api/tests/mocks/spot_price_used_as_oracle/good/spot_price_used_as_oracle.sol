pragma solidity ^0.8.0;

interface ITwapOracle {
    function consult(address token, uint256 amountIn) external view returns (uint256);
}

contract SpotPriceUsedAsOracleGood {
    ITwapOracle public twapOracle;
    address public token;

    constructor(ITwapOracle _twapOracle, address _token) {
        twapOracle = _twapOracle;
        token = _token;
    }

    function getPrice() external view returns (uint256) {
        return twapOracle.consult(token, 1e18);
    }
}
