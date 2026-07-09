pragma solidity ^0.8.0;

interface IToken {
    function getPastVotes(address account, uint256 blockNumber) external view returns (uint256);
}

contract SnapshotlessGovernanceVotingGood {
    IToken public token;
    mapping(uint256 => uint256) public proposalSnapshots;
    mapping(uint256 => mapping(address => bool)) public hasVoted;
    mapping(uint256 => uint256) public forVotes;

    constructor(IToken _token) {
        token = _token;
    }

    function castVote(uint256 proposalId, bool support) external {
        require(!hasVoted[proposalId][msg.sender], "already voted");
        uint256 weight = token.getPastVotes(msg.sender, proposalSnapshots[proposalId]);
        hasVoted[proposalId][msg.sender] = true;
        if (support) forVotes[proposalId] += weight;
    }
}
