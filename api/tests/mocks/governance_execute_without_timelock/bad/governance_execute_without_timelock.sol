pragma solidity ^0.8.0;

contract GovernanceExecuteWithoutTimelockBad {
    struct Proposal {
        bool passed;
        address target;
        bytes data;
    }

    mapping(uint256 => Proposal) public proposals;

    function execute(uint256 id) external {
        Proposal storage proposal = proposals[id];
        require(proposal.passed, "not passed");
        (bool success, ) = proposal.target.call(proposal.data);
        require(success, "execution failed");
    }
}
