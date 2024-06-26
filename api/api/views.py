import json
import sys
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import GenerateASTSerializer

import logging

logger = logging.getLogger(__name__)


class GenerateASTView(APIView):
    def post(self, request, *args, **kwargs):
        source_type = request.data.get("source_type")
        source_path = request.data.get(f"{source_type}_path")

        # @todo sample content, needs to be loaded based on source_path
        rust_code = """
        use anchor_lang::prelude::*;
        use anchor_spl::token::{self, Token, TokenAccount};

        declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

        #[program]
        pub mod pda_sharing_insecure {
            use super::*;

            pub fn withdraw_tokens(ctx: Context<WithdrawTokens>) -> ProgramResult {
                let amount = ctx.accounts.vault.amount;
                let seeds = &[ctx.accounts.pool.mint.as_ref(), &[ctx.accounts.pool.bump]];
                token::transfer(ctx.accounts.transfer_ctx().with_signer(&[seeds]), amount)
            }
        }

        #[derive(Accounts)]
        pub struct WithdrawTokens<'info> {
            #[account(has_one = vault, has_one = withdraw_destination)]
            pool: Account<'info, TokenPool>,
            vault: Account<'info, TokenAccount>,
            withdraw_destination: Account<'info, TokenAccount>,
            authority: Signer<'info>,
            token_program: Program<'info, Token>,
        }

        impl<'info> WithdrawTokens<'info> {
            pub fn transfer_ctx(&self) -> CpiContext<'_, '_, '_, 'info, token::Transfer<'info>> {
                let program = self.token_program.to_account_info();
                let accounts = token::Transfer {
                    from: self.vault.to_account_info(),
                    to: self.withdraw_destination.to_account_info(),
                    authority: self.authority.to_account_info(),
                };
                CpiContext::new(program, accounts)
            }
        }

        #[account]
        pub struct TokenPool {
            vault: Pubkey,
            mint: Pubkey,
            withdraw_destination: Pubkey,
            bump: u8,
        }
        """

        if not source_type or not source_path:
            return Response(
                {"error": "Missing required fields: source_type and path"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if source_type not in ["file", "folder"]:
            return Response(
                {"error": 'source_type must be either "file" or "folder"'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Ensure proper import of rust_syn.so (copied at build time)
            path_to_rust_syn_so = "/api/api"
            if path_to_rust_syn_so not in sys.path:
                sys.path.append(path_to_rust_syn_so)
            import rust_syn  # type: ignore

            ast_data = rust_syn.parse_rust_to_ast(rust_code)
            ast_data = json.loads(ast_data)
        except json.JSONDecodeError:
            return Response(
                {"error": "Faild to decode AST JSON from provided source code"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(e)
            return Response(
                {"error": "Faild to parse AST from provided source code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer_data = {
            "ast": ast_data,
            "source_type": source_type,
            "file_path": source_path if source_type == "file" else None,
            "folder_path": source_path if source_type == "folder" else None,
        }
        serializer = GenerateASTSerializer(data=serializer_data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
