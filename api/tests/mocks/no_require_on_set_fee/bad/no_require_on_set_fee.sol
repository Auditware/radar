pragma solidity ^0.8.20;

contract NoRequireOnSetFeeBad {
    uint256 public constant MAX_FEE_BPS = 1000;

    uint256 public feeBps;

    event FeeUpdated(uint256 newFeeBps);

    // Accepts any value, so the fee can be set to 100% (or more).
    function setFee(uint256 newFeeBps) external {
        feeBps = newFeeBps;
        emit FeeUpdated(newFeeBps);
    }
}
