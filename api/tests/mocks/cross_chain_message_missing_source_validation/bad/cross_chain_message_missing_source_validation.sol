pragma solidity ^0.8.0;

library Client {
    struct Any2EVMMessage {
        bytes32 messageId;
        uint64 sourceChainSelector;
        bytes sender;
        bytes data;
    }
}

contract CrossChainReceiverBad {
    mapping(address => uint256) public balances;

    // BUG: acts on an inbound cross-chain message without validating the source
    // chain or the sending contract, so a message from any chain/contract is trusted.
    function _ccipReceive(Client.Any2EVMMessage memory message) internal {
        (address to, uint256 amount) = abi.decode(message.data, (address, uint256));
        balances[to] += amount;
    }
}
