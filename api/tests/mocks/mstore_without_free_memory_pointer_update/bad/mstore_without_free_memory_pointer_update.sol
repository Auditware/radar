pragma solidity ^0.8.20;

contract MstoreWithoutFreeMemoryPointerUpdateBad {
    // Packs two words into memory and returns the offset they start at.
    function pack(uint256 a, uint256 b) internal pure returns (uint256 offset) {
        assembly {
            // 0x80 is where Solidity's allocator starts handing out memory.
            mstore(0x80, a)
            mstore(0xa0, b)
        }
        // The free memory pointer is never advanced past the two words, so the
        // next allocation is handed 0x80 again and overwrites them.
        offset = 0x80;
    }

    function packed(uint256 a, uint256 b) external pure returns (uint256) {
        return pack(a, b);
    }
}
