pragma solidity ^0.8.20;

/// @notice Vault that charges a protocol fee on every deposit.
contract FeeVault {
    /// @dev Fee expressed in basis points: 50 means 0.5%.
    uint256 public feeBps = 50;

    mapping(address => uint256) public balanceOf;

    function deposit() external payable {
        uint256 fee = feeOf(msg.value);
        balanceOf[msg.sender] += msg.value - fee;
    }

    /// @dev Scales the numerator up before dividing, and divides by a fixed
    ///      constant instead of an unbounded storage value, so the result keeps
    ///      full basis-point resolution.
    function feeOf(uint256 amount) public view returns (uint256) {
        return (amount * feeBps) / 10000;
    }
}
