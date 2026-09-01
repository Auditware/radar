pragma solidity ^0.8.20;

/// @notice Escrow that announces every release to off-chain indexers.
contract EscrowNotifier {
    event Released(address indexed to, uint256 amount);

    mapping(address => uint256) public escrowed;
    mapping(address => uint256) public claimable;

    function deposit(address to) external payable {
        escrowed[to] += msg.value;
    }

    /// @dev Credits the recipient and announces the release without making an
    ///      external call, so nothing can re-enter between the state change and
    ///      the event. The recipient pulls the funds with `claim`.
    function emitRelease(address to) external {
        uint256 amount = escrowed[to];
        escrowed[to] = 0;
        claimable[to] += amount;
        emit Released(to, amount);
    }

    function claim() external {
        uint256 amount = claimable[msg.sender];
        claimable[msg.sender] = 0;
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "claim failed");
    }
}
