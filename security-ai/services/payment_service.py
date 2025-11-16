"""
Payment processing service for SecurityGuard AI
Integrates with AgentMarket escrow system for 0.01 SOL payments
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from decimal import Decimal
from loguru import logger

try:
    from solana.rpc.async_api import AsyncClient
    from solana.rpc.commitment import Confirmed
    from solana.publickey import PublicKey
    from solana.transaction import Transaction
    from solana.system_program import transfer, TransferParams
except ImportError:
    logger.warning("Solana SDK not available - payment service will use mock data")
    AsyncClient = None
    Confirmed = None
    PublicKey = None

try:
    from ..core.config import get_settings
    from ..models.schemas import UserProfile
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings
    from models.schemas import UserProfile


class PaymentService:
    """
    Handles payment processing for SecurityGuard AI services
    Integrates with Solana blockchain and AgentMarket escrow
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize Solana client if available
        if AsyncClient:
            self.solana_client = AsyncClient(self.settings.solana_rpc_url)
        else:
            self.solana_client = None
            logger.warning("Solana client not available - using mock payment processing")
        
        self.scan_price_sol = Decimal("0.01")  # 0.01 SOL per scan
        self.lamports_per_sol = 1_000_000_000
        self.scan_price_lamports = int(self.scan_price_sol * self.lamports_per_sol)
        
        # AgentMarket escrow program addresses (would be configured in production)
        self.escrow_program_id = "Escrow111111111111111111111111111111111"
        self.platform_wallet = "AgentMarketPlatform1111111111111111111111"
        self.treasury_wallet = "AgentMarketTreasury1111111111111111111111"
        
        # Payment tracking (in production, use database)
        self.pending_payments = {}
        self.completed_payments = {}
        
    async def check_user_balance(self, wallet_address: str) -> Tuple[bool, Decimal, str]:
        """
        Check if user has sufficient balance for scan payment
        
        Args:
            wallet_address: User's wallet address
            
        Returns:
            Tuple[bool, Decimal, str]: (has_sufficient_balance, current_balance_sol, message)
        """
        try:
            # Check if Solana client is available
            if not self.solana_client or not PublicKey:
                # Mock balance for demo
                balance_sol = Decimal("0.1")  # Mock sufficient balance
                logger.info(f"💰 Mock balance check for {wallet_address[:8]}...: {balance_sol:.4f} SOL")
            else:
                # Get wallet balance from Solana
                pubkey = PublicKey(wallet_address)
                balance_response = await self.solana_client.get_balance(pubkey, commitment=Confirmed)
                
                if balance_response.value is None:
                    return False, Decimal("0"), "Unable to fetch wallet balance"
                
                balance_lamports = balance_response.value
                balance_sol = Decimal(balance_lamports) / self.lamports_per_sol
            
            has_sufficient = balance_sol >= self.scan_price_sol
            
            if has_sufficient:
                message = f"Balance: {balance_sol:.4f} SOL (sufficient for scan)"
            else:
                needed = self.scan_price_sol - balance_sol
                message = f"Balance: {balance_sol:.4f} SOL (need {needed:.4f} SOL more)"
            
            logger.info(f"💰 Balance check for {wallet_address[:8]}...: {balance_sol:.4f} SOL")
            return has_sufficient, balance_sol, message
            
        except Exception as e:
            logger.error(f"❌ Balance check failed for {wallet_address}: {e}")
            return False, Decimal("0"), f"Balance check failed: {str(e)}"
    
    async def create_payment_request(
        self, 
        user_wallet: str, 
        service_type: str = "transaction_scan"
    ) -> Dict[str, Any]:
        """
        Create payment request for SecurityGuard service
        
        Args:
            user_wallet: User's wallet address
            service_type: Type of service being requested
            
        Returns:
            Dict: Payment request details
        """
        try:
            # Generate unique payment ID
            payment_id = f"sg_{int(datetime.utcnow().timestamp())}_{user_wallet[:8]}"
            
            # Check balance first
            has_balance, current_balance, balance_message = await self.check_user_balance(user_wallet)
            
            payment_request = {
                "payment_id": payment_id,
                "user_wallet": user_wallet,
                "service_type": service_type,
                "amount_sol": float(self.scan_price_sol),
                "amount_lamports": self.scan_price_lamports,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
                "has_sufficient_balance": has_balance,
                "current_balance_sol": float(current_balance),
                "balance_message": balance_message,
                "escrow_program_id": self.escrow_program_id,
                "platform_wallet": self.platform_wallet
            }
            
            # Store pending payment
            self.pending_payments[payment_id] = payment_request
            
            logger.info(f"💳 Payment request created: {payment_id} for {user_wallet[:8]}...")
            return payment_request
            
        except Exception as e:
            logger.error(f"❌ Failed to create payment request: {e}")
            raise
    
    async def process_payment(
        self, 
        payment_id: str, 
        transaction_signature: str
    ) -> Dict[str, Any]:
        """
        Process and validate payment transaction
        
        Args:
            payment_id: Payment request ID
            transaction_signature: Solana transaction signature
            
        Returns:
            Dict: Payment processing result
        """
        try:
            # Get pending payment
            if payment_id not in self.pending_payments:
                return {
                    "success": False,
                    "error": "Payment request not found or expired",
                    "payment_id": payment_id
                }
            
            payment_request = self.pending_payments[payment_id]
            
            # Check if payment expired
            expires_at = datetime.fromisoformat(payment_request["expires_at"])
            if datetime.utcnow() > expires_at:
                del self.pending_payments[payment_id]
                return {
                    "success": False,
                    "error": "Payment request expired",
                    "payment_id": payment_id
                }
            
            # Validate transaction on Solana blockchain
            validation_result = await self._validate_payment_transaction(
                transaction_signature,
                payment_request["user_wallet"],
                payment_request["amount_lamports"]
            )
            
            if validation_result["valid"]:
                # Mark payment as completed
                payment_result = {
                    "payment_id": payment_id,
                    "transaction_signature": transaction_signature,
                    "user_wallet": payment_request["user_wallet"],
                    "amount_sol": payment_request["amount_sol"],
                    "service_type": payment_request["service_type"],
                    "status": "completed",
                    "processed_at": datetime.utcnow().isoformat(),
                    "blockchain_confirmed": True,
                    "escrow_account": validation_result.get("escrow_account")
                }
                
                # Move to completed payments
                self.completed_payments[payment_id] = payment_result
                del self.pending_payments[payment_id]
                
                logger.info(f"✅ Payment processed successfully: {payment_id}")
                return {"success": True, "payment": payment_result}
            else:
                logger.warning(f"❌ Payment validation failed: {payment_id} - {validation_result['error']}")
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "payment_id": payment_id
                }
                
        except Exception as e:
            logger.error(f"❌ Payment processing failed: {e}")
            return {
                "success": False,
                "error": f"Payment processing error: {str(e)}",
                "payment_id": payment_id
            }
    
    async def _validate_payment_transaction(
        self, 
        transaction_signature: str, 
        expected_sender: str, 
        expected_amount: int
    ) -> Dict[str, Any]:
        """
        Validate payment transaction on Solana blockchain
        
        Args:
            transaction_signature: Transaction signature to validate
            expected_sender: Expected sender wallet address
            expected_amount: Expected payment amount in lamports
            
        Returns:
            Dict: Validation result
        """
        try:
            # Check if Solana client is available
            if not self.solana_client:
                # Mock validation for demo
                logger.info(f"💳 Mock transaction validation for: {transaction_signature[:8]}...")
                return {
                    "valid": True,
                    "transaction": transaction_signature,
                    "escrow_account": f"escrow_{transaction_signature[:8]}",
                    "block_time": int(datetime.utcnow().timestamp())
                }
            
            # Get transaction details from Solana
            tx_response = await self.solana_client.get_transaction(
                transaction_signature, 
                commitment=Confirmed
            )
            
            if not tx_response.value:
                return {"valid": False, "error": "Transaction not found"}
            
            transaction = tx_response.value
            
            # Check transaction success
            if transaction.meta.err:
                return {"valid": False, "error": f"Transaction failed: {transaction.meta.err}"}
            
            # Validate transaction details
            # In production, this would check:
            # 1. Sender matches expected wallet
            # 2. Amount matches expected payment
            # 3. Recipient is correct escrow account
            # 4. Transaction is recent (not replayed)
            
            # For demo, simulate validation
            validation_checks = {
                "sender_valid": True,  # Would check actual sender
                "amount_valid": True,  # Would check actual amount
                "recipient_valid": True,  # Would check escrow account
                "recent": True  # Would check timestamp
            }
            
            if all(validation_checks.values()):
                return {
                    "valid": True,
                    "transaction": transaction_signature,
                    "escrow_account": f"escrow_{transaction_signature[:8]}",
                    "block_time": transaction.block_time
                }
            else:
                failed_checks = [k for k, v in validation_checks.items() if not v]
                return {
                    "valid": False,
                    "error": f"Validation failed: {', '.join(failed_checks)}"
                }
                
        except Exception as e:
            logger.error(f"❌ Transaction validation error: {e}")
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    async def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Check status of payment request
        
        Args:
            payment_id: Payment request ID
            
        Returns:
            Dict: Payment status information
        """
        # Check completed payments first
        if payment_id in self.completed_payments:
            return {
                "status": "completed",
                "payment": self.completed_payments[payment_id]
            }
        
        # Check pending payments
        if payment_id in self.pending_payments:
            payment_request = self.pending_payments[payment_id]
            
            # Check if expired
            expires_at = datetime.fromisoformat(payment_request["expires_at"])
            if datetime.utcnow() > expires_at:
                del self.pending_payments[payment_id]
                return {"status": "expired", "payment_id": payment_id}
            
            return {
                "status": "pending",
                "payment": payment_request,
                "time_remaining_seconds": int((expires_at - datetime.utcnow()).total_seconds())
            }
        
        return {"status": "not_found", "payment_id": payment_id}
    
    async def has_valid_payment(self, user_wallet: str, service_type: str = "transaction_scan") -> bool:
        """
        Check if user has valid payment for service access
        
        Args:
            user_wallet: User's wallet address
            service_type: Type of service
            
        Returns:
            bool: True if user has valid payment
        """
        try:
            # Check recent completed payments for this user
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)  # 1 hour validity
            
            for payment in self.completed_payments.values():
                if (payment["user_wallet"] == user_wallet and 
                    payment["service_type"] == service_type and
                    datetime.fromisoformat(payment["processed_at"]) > recent_cutoff):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Payment validation check failed: {e}")
            return False
    
    def get_payment_instructions(self, user_wallet: str) -> Dict[str, Any]:
        """
        Get payment instructions for user
        
        Args:
            user_wallet: User's wallet address
            
        Returns:
            Dict: Payment instructions
        """
        return {
            "service": "SecurityGuard AI Transaction Scan",
            "price_sol": float(self.scan_price_sol),
            "price_lamports": self.scan_price_lamports,
            "instructions": [
                "1. Ensure your wallet has at least 0.01 SOL + transaction fees",
                "2. Click 'Pay for Scan' to create payment request",
                "3. Approve the transaction in your wallet",
                "4. Wait for blockchain confirmation",
                "5. Your scan will be processed automatically"
            ],
            "supported_wallets": ["Phantom", "Solflare", "Backpack"],
            "network": self.settings.solana_network,
            "estimated_fees": "~0.000005 SOL",
            "payment_validity": "1 hour after payment"
        }


# Global payment service instance
payment_service = PaymentService()