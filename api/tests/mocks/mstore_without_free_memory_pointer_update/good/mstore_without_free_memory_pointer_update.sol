pragma solidity ^0.8.20;

contract MstoreWithoutFreeMemoryPointerUpdateGood {
    // Packs two words into memory and returns the offset they start at.
    function pack(uint256 a, uint256 b) internal pure returns (uint256 offset) {
        assembly {
            // 0x80 is where Solidity's allocator starts handing out memory.
            mstore(0x80, a)
            mstore(0xa0, b)
            // Advance the free memory pointer past the two words so the next
            // allocation cannot overlap them.
            mstore(0x40, 0xc0)
        }
        offset = 0x80;
    }

    function packed(uint256 a, uint256 b) external pure returns (uint256) {
        return pack(a, b);
    }
}
