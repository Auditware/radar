pragma solidity ^0.8.0;

interface IVRFCoordinator {
    function requestRandomWords(bytes32 keyHash, uint64 subId, uint16 minimumRequestConfirmations, uint32 callbackGasLimit, uint32 numWords) external returns (uint256 requestId);
}

contract InsecureRandomnessGood {
    IVRFCoordinator public vrfCoordinator;

    constructor(IVRFCoordinator _vrf) {
        vrfCoordinator = _vrf;
    }

    function getRandomNumber(bytes32 keyHash, uint64 subId) external returns (uint256 requestId) {
        requestId = vrfCoordinator.requestRandomWords(keyHash, subId, 3, 200000, 1);
    }
}
