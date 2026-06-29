pragma solidity ^0.8.0;

contract ERC4626ShareInflationBad {
    uint256 public totalAssetsStored = 1_000 ether;
    uint256 public supply;

    function totalSupply() public view returns (uint256) {
        return supply;
    }

    function totalAssets() public view returns (uint256) {
        return totalAssetsStored;
    }

    function previewDeposit(uint256 assets) public view returns (uint256) {
        uint256 currentSupply = totalSupply();
        return currentSupply == 0 ? assets : assets * currentSupply / totalAssets();
    }
}
