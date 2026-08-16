pragma solidity ^0.8.0;

abstract contract ERC721 {
    mapping(uint256 => address) public ownerOf;
    function _mint(address to, uint256 id) internal virtual {
        ownerOf[id] = to;
    }
    function _safeMint(address to, uint256 id) internal virtual {
        ownerOf[id] = to;
    }
}

contract NftBad is ERC721 {
    function mint(address to, uint256 id) external {
        _mint(to, id);
    }
}
