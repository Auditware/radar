pragma solidity ^0.8.0;

library Client {
    struct Any2EVMMessage {
        bytes32 messageId;
        uint64 sourceChainSelector;
        bytes sender;
        bytes data;
    }
}

contract CrossChainReceiverGood {
    mapping(address => uint256) public balances;
    mapping(uint64 => address) public trustedSenders;

    function _ccipReceive(Client.Any2EVMMessage memory message) internal {
        address sender = abi.decode(message.sender, (address));
        require(trustedSenders[message.sourceChainSelector] == sender, "untrusted source");
        (address to, uint256 amount) = abi.decode(message.data, (address, uint256));
        balances[to] += amount;
    }
}
