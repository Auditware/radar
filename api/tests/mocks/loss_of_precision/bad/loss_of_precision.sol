pragma solidity ^0.8.20;

/// @notice Vault that charges a protocol fee on every deposit.
contract FeeVault {
    /// @dev Fee expressed as a divisor: 200 means "one two-hundredth", 0.5%.
    uint256 public feeDivisor = 200;

    mapping(address => uint256) public balanceOf;

    function deposit() external payable {
        uint256 fee = feeOf(msg.value);
        balanceOf[msg.sender] += msg.value - fee;
    }

    /// @dev Divides the raw amount by a large storage divisor, so the integer
    ///      division truncates and any deposit below `feeDivisor` wei pays no
    ///      fee at all.
    function feeOf(uint256 amount) public view returns (uint256) {
        return amount / feeDivisor;
    }
}
