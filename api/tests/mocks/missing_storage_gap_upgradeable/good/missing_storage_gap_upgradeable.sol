pragma solidity ^0.8.0;

contract MissingStorageGapUpgradeableGoodUpgradeable {
    uint256 public value;
    uint256[49] private __gap;
}
