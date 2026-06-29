pragma solidity ^0.8.0;

contract GovernanceExecuteWithoutTimelockGood {
    struct Proposal {
        bool passed;
        uint256 eta;
        address target;
        bytes data;
    }

    mapping(uint256 => Proposal) public proposals;

    function execute(uint256 id) external {
        Proposal storage proposal = proposals[id];
        require(proposal.passed, "not passed");
        require(block.timestamp >= proposal.eta, "timelock not expired");
        (bool success, ) = proposal.target.call(proposal.data);
        require(success, "execution failed");
    }
}
