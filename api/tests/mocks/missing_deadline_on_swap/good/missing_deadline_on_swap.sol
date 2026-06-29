pragma solidity ^0.8.0;

interface ISwapRouter {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint256 deadline;
    }

    function exactInputSingle(ExactInputSingleParams calldata params) external returns (uint256 amountOut);
}

contract MissingDeadlineOnSwapGood {
    ISwapRouter public router;

    constructor(ISwapRouter _router) {
        router = _router;
    }

    function swap(address tokenIn, address tokenOut, uint256 amountIn) external {
        router.exactInputSingle(
            ISwapRouter.ExactInputSingleParams({
                tokenIn: tokenIn,
                tokenOut: tokenOut,
                amountIn: amountIn,
                amountOutMinimum: 1,
                deadline: block.timestamp + 300
            })
        );
    }
}
