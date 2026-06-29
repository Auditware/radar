pragma solidity ^0.8.0;

contract ERC4626ShareInflationGood {
    uint256 public totalAssetsStored = 1_000 ether;
    uint256 public supply;

    function totalSupply() public view returns (uint256) {
        return supply;
    }

    function totalAssets() public view returns (uint256) {
        return totalAssetsStored;
    }

    function decimalsOffset() public pure returns (uint256) {
        return 1;
    }

    function previewDeposit(uint256 assets) public view returns (uint256) {
        uint256 currentSupply = totalSupply();
        uint256 virtualOffset = 10 ** decimalsOffset();
        return (assets * (currentSupply + virtualOffset)) / (totalAssets() + virtualOffset);
    }
}
