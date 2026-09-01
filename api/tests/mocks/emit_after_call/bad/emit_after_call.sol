pragma solidity ^0.8.20;

/// @notice Escrow that announces every release to off-chain indexers.
contract EscrowNotifier {
    event Released(address indexed to, uint256 amount);

    mapping(address => uint256) public escrowed;

    function deposit(address to) external payable {
        escrowed[to] += msg.value;
    }

    /// @dev Pushes the funds out and only then announces the release. A
    ///      re-entering recipient can call back in before `Released` is
    ///      emitted, so the events reach indexers out of order.
    function emitRelease(address to) external {
        uint256 amount = escrowed[to];
        escrowed[to] = 0;
        (bool ok, ) = to.call{value: amount}("");
        require(ok, "release failed");
        emit Released(to, amount);
    }
}
