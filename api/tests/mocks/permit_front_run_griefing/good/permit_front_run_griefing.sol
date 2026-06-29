pragma solidity ^0.8.0;

interface IERC20Permit {
    function permit(address owner, address spender, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s) external;
    function transferFrom(address from, address to, uint256 value) external returns (bool);
}

contract PermitFrontRunGriefingGood {
    IERC20Permit public token;

    constructor(IERC20Permit _token) {
        token = _token;
    }

    function depositWithPermit(address owner, uint256 value, uint256 deadline, uint8 v, bytes32 r, bytes32 s) external {
        try token.permit(owner, address(this), value, deadline, v, r, s) {
        } catch {
        }
        token.transferFrom(owner, address(this), value);
    }
}
