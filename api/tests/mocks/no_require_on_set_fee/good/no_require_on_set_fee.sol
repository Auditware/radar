pragma solidity ^0.8.20;

contract NoRequireOnSetFeeGood {
    uint256 public constant MAX_FEE_BPS = 1000;

    uint256 public feeBps;

    event FeeUpdated(uint256 newFeeBps);

    // Bounds the fee before storing it.
    function setFee(uint256 newFeeBps) external {
        require(newFeeBps <= MAX_FEE_BPS, "fee too high");
        feeBps = newFeeBps;
        emit FeeUpdated(newFeeBps);
    }
}
