"""
High-performance Solana transaction analyzer
Optimized for <2 second response times
"""

import asyncio
import base64
import json
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from loguru import logger
import redis.asyncio as redis
from solders.transaction import VersionedTransaction
from solders.message import Message

try:
    from ..core.config import get_settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings


@dataclass
class ParsedTransaction:
    """Parsed transaction data structure"""
    programs: List[str]
    instructions: List[Dict[str, Any]]
    accounts: List[str]
    signatures_required: int
    recent_blockhash: str
    fee_payer: str
    raw_data: Dict[str, Any]


class TransactionAnalyzer:
    """High-performance transaction analyzer with caching and async processing"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Known program classifications for fast lookup
        self.verified_programs = {
            "11111111111111111111111111111112",  # System Program
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",  # Token Program
            "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",  # Associated Token
            "So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo",  # Solend
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",  # Serum DEX
        }
        
        self.blacklisted_programs = {
            # Known malicious programs would be loaded from database
        }
    
    async def initialize(self):
        """Initialize Redis connection and cache"""
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            await self.redis_client.ping()
            logger.info("✅ Redis connected for transaction analyzer")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self.redis_client = None
    
    async def parse_transaction(self, transaction_data: Any) -> ParsedTransaction:
        """
        Parse Solana transaction with performance optimization
        Target: <150ms parsing time with aggressive caching
        """
        start_time = time.time()
        
        try:
            # Generate cache key for parsed transaction (optimized hashing)
            if isinstance(transaction_data, str):
                cache_key = f"parsed_tx:{hash(transaction_data[:100])}"  # Hash first 100 chars for speed
            else:
                cache_key = f"parsed_tx:{hash(str(transaction_data)[:100])}"
            
            # Check cache first with timeout
            if self.redis_client:
                try:
                    cached_result = await asyncio.wait_for(
                        self.redis_client.get(cache_key),
                        timeout=0.05  # 50ms cache timeout
                    )
                    if cached_result:
                        cached_data = json.loads(cached_result)
                        parsed = ParsedTransaction(**cached_data)
                        cache_time = (time.time() - start_time) * 1000
                        logger.debug(f"⚡ Transaction cache hit in {cache_time:.1f}ms")
                        return parsed
                except (asyncio.TimeoutError, Exception) as cache_error:
                    logger.debug(f"Cache lookup failed/timeout: {cache_error}")
            
            # Handle different input formats with optimized parsing
            if isinstance(transaction_data, str):
                # Base64 encoded transaction - parse in thread pool for CPU work
                transaction = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    self._parse_base64_transaction,
                    transaction_data
                )
            elif isinstance(transaction_data, dict):
                # JSON transaction object
                transaction = self._parse_json_transaction(transaction_data)
            else:
                raise ValueError("Unsupported transaction format")
            
            # Extract transaction components with aggressive timeout
            try:
                # Run extraction tasks with very short timeout for speed
                extraction_timeout = 0.08  # 80ms timeout for extraction
                
                programs_task = asyncio.create_task(self._extract_programs_fast(transaction))
                instructions_task = asyncio.create_task(self._extract_instructions_fast(transaction))
                accounts_task = asyncio.create_task(self._extract_accounts_fast(transaction))
                
                programs, instructions, accounts = await asyncio.wait_for(
                    asyncio.gather(programs_task, instructions_task, accounts_task),
                    timeout=extraction_timeout
                )
            except asyncio.TimeoutError:
                logger.warning("⚠️ Fast extraction timeout, using fallback")
                # Ultra-fast fallback extraction
                programs = self._extract_programs_sync(transaction)
                instructions = self._extract_instructions_sync(transaction)
                accounts = self._extract_accounts_sync(transaction)
            
            parsed = ParsedTransaction(
                programs=programs,
                instructions=instructions,
                accounts=accounts,
                signatures_required=len(transaction.signatures) if hasattr(transaction, 'signatures') else 1,
                recent_blockhash=str(transaction.message.recent_blockhash) if hasattr(transaction, 'message') else "",
                fee_payer=str(transaction.message.account_keys[0]) if (hasattr(transaction, 'message') and transaction.message.account_keys) else "",
                raw_data=self._serialize_transaction_data_fast(transaction)
            )
            
            # Cache the parsed result asynchronously (don't wait)
            if self.redis_client:
                asyncio.create_task(self._cache_parsed_transaction(cache_key, parsed))
            
            parse_time = (time.time() - start_time) * 1000
            
            # Log performance warnings
            if parse_time > 150:
                logger.warning(f"⚠️ Slow transaction parsing: {parse_time:.1f}ms (target: <150ms)")
            else:
                logger.debug(f"⚡ Transaction parsed in {parse_time:.1f}ms")
            
            return parsed
            
        except Exception as e:
            logger.error(f"❌ Transaction parsing failed: {e}")
            # Return minimal parsed transaction for graceful degradation
            return ParsedTransaction(
                programs=[],
                instructions=[],
                accounts=[],
                signatures_required=1,
                recent_blockhash="",
                fee_payer="",
                raw_data={"error": str(e)}
            )
    
    async def analyze_programs(self, parsed_tx) -> Dict[str, Any]:
        """
        Analyze programs involved in transaction
        Target: <100ms analysis time
        """
        start_time = time.time()
        
        # Handle both ParsedTransaction objects and dicts
        if isinstance(parsed_tx, dict):
            programs = parsed_tx.get("programs", [])
        else:
            programs = parsed_tx.programs
        
        # Check cache first
        cache_key = f"program_analysis:{hash(tuple(programs))}"
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as cache_error:
                logger.debug(f"Cache lookup failed: {cache_error}")
        
        # Parallel program analysis
        analysis_tasks = [
            self._analyze_single_program(program_id) 
            for program_id in programs
        ]
        
        program_analyses = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Aggregate results
        verified_count = 0
        unknown_count = 0
        blacklisted_count = 0
        risk_programs = []
        
        for i, analysis in enumerate(program_analyses):
            if isinstance(analysis, Exception):
                logger.warning(f"Program analysis failed for {programs[i]}: {analysis}")
                unknown_count += 1
                continue
                
            if analysis["is_verified"]:
                verified_count += 1
            elif analysis["is_blacklisted"]:
                blacklisted_count += 1
                risk_programs.append(programs[i])
            else:
                unknown_count += 1
        
        result = {
            "total_programs": len(programs),
            "verified_programs": verified_count,
            "unknown_programs": unknown_count,
            "blacklisted_programs": blacklisted_count,
            "risk_programs": risk_programs,
            "program_details": [
                analysis for analysis in program_analyses 
                if not isinstance(analysis, Exception)
            ]
        }
        
        # Cache result
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    cache_key, 
                    self.settings.cache_ttl, 
                    json.dumps(result)
                )
            except Exception as cache_error:
                logger.debug(f"Failed to cache program analysis: {cache_error}")
        
        analysis_time = (time.time() - start_time) * 1000
        logger.debug(f"⚡ Program analysis completed in {analysis_time:.1f}ms")
        
        return result
    
    async def analyze_accounts(self, parsed_tx, user_wallet: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze account relationships and permissions
        Target: <150ms analysis time
        """
        start_time = time.time()
        
        # Handle both ParsedTransaction objects and dicts
        if isinstance(parsed_tx, dict):
            accounts = parsed_tx.get("accounts", [])
            instructions = parsed_tx.get("instructions", [])
        else:
            accounts = parsed_tx.accounts
            instructions = parsed_tx.instructions
        
        # Quick account risk assessment
        red_flags = []
        suspicious_patterns = []
        
        # Check for new accounts (simplified - would query blockchain in production)
        new_accounts = [
            acc for acc in accounts 
            if len(acc) == 44 and acc.startswith("1")  # Heuristic for new accounts
        ]
        
        # Check for authority changes
        authority_changes = self._detect_authority_changes(instructions)
        if authority_changes:
            red_flags.append("authority_delegation_detected")
            suspicious_patterns.extend(authority_changes)
        
        # Check for unlimited approvals
        unlimited_approvals = self._detect_unlimited_approvals(instructions)
        if unlimited_approvals:
            red_flags.append("unlimited_token_approval")
            suspicious_patterns.extend(unlimited_approvals)
        
        # Check user wallet involvement
        user_at_risk = False
        if user_wallet and user_wallet in accounts:
            user_at_risk = len(red_flags) > 0
        
        result = {
            "total_accounts": len(accounts),
            "new_accounts": len(new_accounts),
            "red_flags": red_flags,
            "suspicious_patterns": suspicious_patterns,
            "user_at_risk": user_at_risk,
            "unlimited_approvals": len(unlimited_approvals) > 0,
            "authority_changes": len(authority_changes) > 0
        }
        
        analysis_time = (time.time() - start_time) * 1000
        logger.debug(f"⚡ Account analysis completed in {analysis_time:.1f}ms")
        
        return result
    
    def _parse_base64_transaction(self, transaction_data: str):
        """Parse base64 transaction in thread pool (CPU intensive)"""
        tx_bytes = base64.b64decode(transaction_data)
        return VersionedTransaction.from_bytes(tx_bytes)
    
    async def _cache_parsed_transaction(self, cache_key: str, parsed: ParsedTransaction):
        """Cache parsed transaction asynchronously"""
        try:
            cache_data = {
                "programs": parsed.programs,
                "instructions": parsed.instructions,
                "accounts": parsed.accounts,
                "signatures_required": parsed.signatures_required,
                "recent_blockhash": parsed.recent_blockhash,
                "fee_payer": parsed.fee_payer,
                "raw_data": parsed.raw_data
            }
            await self.redis_client.setex(
                cache_key,
                self.settings.cache_ttl,
                json.dumps(cache_data)
            )
        except Exception as cache_error:
            logger.debug(f"Failed to cache parsed transaction: {cache_error}")
    
    async def _extract_programs_fast(self, transaction) -> List[str]:
        """Fast program extraction with error handling"""
        return await asyncio.get_event_loop().run_in_executor(
            self.thread_pool,
            self._extract_programs_sync,
            transaction
        )
    
    def _extract_programs_sync(self, transaction) -> List[str]:
        """Synchronous program extraction for speed"""
        programs = set()
        
        try:
            # Extract from instructions
            if hasattr(transaction, 'message') and hasattr(transaction.message, 'instructions'):
                for instruction in transaction.message.instructions:
                    program_index = instruction.program_id_index
                    if program_index < len(transaction.message.account_keys):
                        program_id = str(transaction.message.account_keys[program_index])
                        programs.add(program_id)
        except Exception as e:
            logger.debug(f"Failed to extract programs: {e}")
        
        return list(programs)
    
    async def _extract_programs(self, transaction) -> List[str]:
        """Extract program IDs from transaction"""
        return self._extract_programs_sync(transaction)
    
    async def _extract_instructions_fast(self, transaction) -> List[Dict[str, Any]]:
        """Fast instruction extraction with error handling"""
        return await asyncio.get_event_loop().run_in_executor(
            self.thread_pool,
            self._extract_instructions_sync,
            transaction
        )
    
    def _extract_instructions_sync(self, transaction) -> List[Dict[str, Any]]:
        """Synchronous instruction extraction for speed"""
        instructions = []
        
        try:
            if hasattr(transaction, 'message') and hasattr(transaction.message, 'instructions'):
                for i, instruction in enumerate(transaction.message.instructions):
                    # Limit data processing for speed
                    data_hex = ""
                    data_length = 0
                    
                    if hasattr(instruction, 'data') and instruction.data:
                        data_length = len(instruction.data)
                        # Only convert first 64 bytes to hex for speed
                        data_hex = instruction.data[:64].hex() if data_length > 0 else ""
                    
                    instructions.append({
                        "index": i,
                        "program_id_index": getattr(instruction, 'program_id_index', 0),
                        "accounts": list(getattr(instruction, 'accounts', [])),
                        "data": data_hex,
                        "data_length": data_length
                    })
        except Exception as e:
            logger.debug(f"Failed to extract instructions: {e}")
        
        return instructions
    
    async def _extract_instructions(self, transaction) -> List[Dict[str, Any]]:
        """Extract instruction data from transaction"""
        return self._extract_instructions_sync(transaction)
    
    async def _extract_accounts_fast(self, transaction) -> List[str]:
        """Fast account extraction with error handling"""
        return await asyncio.get_event_loop().run_in_executor(
            self.thread_pool,
            self._extract_accounts_sync,
            transaction
        )
    
    def _extract_accounts_sync(self, transaction) -> List[str]:
        """Synchronous account extraction for speed"""
        try:
            if hasattr(transaction, 'message') and hasattr(transaction.message, 'account_keys'):
                return [str(account) for account in transaction.message.account_keys]
        except Exception as e:
            logger.debug(f"Failed to extract accounts: {e}")
        
        return []
    
    async def _extract_accounts(self, transaction) -> List[str]:
        """Extract account addresses from transaction"""
        return self._extract_accounts_sync(transaction)
    
    async def _analyze_single_program(self, program_id: str) -> Dict[str, Any]:
        """Analyze a single program for risk factors"""
        return {
            "program_id": program_id,
            "is_verified": program_id in self.verified_programs,
            "is_blacklisted": program_id in self.blacklisted_programs,
            "risk_score": 0 if program_id in self.verified_programs else 
                         100 if program_id in self.blacklisted_programs else 30,
            "reputation_score": 1.0 if program_id in self.verified_programs else 0.5
        }
    
    def _parse_json_transaction(self, tx_data: dict) -> VersionedTransaction:
        """Parse transaction from JSON format"""
        # Simplified implementation - would handle full JSON parsing
        if "transaction" in tx_data:
            tx_bytes = base64.b64decode(tx_data["transaction"])
            return VersionedTransaction.from_bytes(tx_bytes)
        raise ValueError("Invalid JSON transaction format")
    
    def _serialize_transaction_data_fast(self, transaction) -> Dict[str, Any]:
        """Fast transaction data serialization"""
        try:
            return {
                "signature_count": len(getattr(transaction, 'signatures', [])),
                "account_count": len(getattr(transaction.message, 'account_keys', [])) if hasattr(transaction, 'message') else 0,
                "instruction_count": len(getattr(transaction.message, 'instructions', [])) if hasattr(transaction, 'message') else 0,
                "recent_blockhash": str(getattr(transaction.message, 'recent_blockhash', '')) if hasattr(transaction, 'message') else ""
            }
        except Exception as e:
            logger.debug(f"Failed to serialize transaction data: {e}")
            return {"error": str(e)}
    
    def _serialize_transaction_data(self, transaction) -> Dict[str, Any]:
        """Serialize transaction data for storage/caching"""
        return self._serialize_transaction_data_fast(transaction)
    
    def _detect_authority_changes(self, instructions: List[Dict[str, Any]]) -> List[str]:
        """Detect authority delegation patterns in instructions"""
        authority_changes = []
        
        for instruction in instructions:
            # Simplified pattern detection
            if instruction.get("data_length", 0) > 32:  # Potential authority change
                authority_changes.append(f"instruction_{instruction['index']}")
        
        return authority_changes
    
    def _detect_unlimited_approvals(self, instructions: List[Dict[str, Any]]) -> List[str]:
        """Detect unlimited token approval patterns"""
        unlimited_approvals = []
        
        for instruction in instructions:
            # Simplified pattern detection for token approvals
            data = instruction.get("data", "")
            if len(data) > 16 and "ffffff" in data.lower():  # Max approval pattern
                unlimited_approvals.append(f"instruction_{instruction['index']}")
        
        return unlimited_approvals