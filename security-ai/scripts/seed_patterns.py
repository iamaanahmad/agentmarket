"""
Database seeding script for SecurityGuard AI exploit patterns
Seeds database with initial patterns for wallet drainers, rug pulls, and phishing contracts
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

try:
    from ..core.config import get_settings
    from ..models.database import (
        ExploitPatternDB, ThreatIntelligenceFeed, 
        create_database_engine, create_tables
    )
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings
    from models.database import (
        ExploitPatternDB, ThreatIntelligenceFeed,
        create_database_engine, create_tables
    )


class PatternSeeder:
    """Database seeder for exploit patterns"""
    
    def __init__(self, database_url: str):
        self.engine = create_database_engine(database_url)
        self.session_factory = sessionmaker(bind=self.engine)
    
    async def seed_database(self):
        """Seed database with initial exploit patterns"""
        logger.info("🌱 Starting database seeding...")
        
        # Create tables if they don't exist
        create_tables(self.engine)
        
        session = self.session_factory()
        
        try:
            # Clear existing patterns (for fresh seeding)
            session.query(ExploitPatternDB).delete()
            session.commit()
            
            # Seed different types of patterns
            await self._seed_wallet_drainer_patterns(session)
            await self._seed_rug_pull_patterns(session)
            await self._seed_phishing_patterns(session)
            await self._seed_defi_exploit_patterns(session)
            await self._seed_token_approval_patterns(session)
            await self._seed_authority_theft_patterns(session)
            await self._seed_behavioral_patterns(session)
            
            # Seed threat intelligence feeds
            await self._seed_threat_feeds(session)
            
            session.commit()
            
            # Get final count
            total_patterns = session.query(ExploitPatternDB).count()
            logger.info(f"✅ Database seeding completed! Added {total_patterns} patterns")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Database seeding failed: {e}")
            raise
        finally:
            session.close()
    
    async def _seed_wallet_drainer_patterns(self, session):
        """Seed wallet drainer exploit patterns"""
        logger.info("🔍 Seeding wallet drainer patterns...")
        
        drainer_patterns = [
            {
                "pattern_id": "wallet_drainer_v1",
                "name": "Classic Wallet Drainer",
                "description": "Known wallet drainer contract that steals all tokens and SOL",
                "pattern_type": "program",
                "severity": "CRITICAL",
                "confidence": 0.99,
                "program_id": "DrainWa11etProgramId123456789012345678901",
                "source": "threat_intelligence",
                "threat_actor": "DrainerGang"
            },
            {
                "pattern_id": "wallet_drainer_v2",
                "name": "Advanced Wallet Drainer",
                "description": "Sophisticated drainer using multiple transactions",
                "pattern_type": "program",
                "severity": "CRITICAL",
                "confidence": 0.98,
                "program_id": "AdvancedDrainer123456789012345678901234",
                "source": "threat_intelligence",
                "threat_actor": "SophisticatedAttackers"
            },
            {
                "pattern_id": "drain_instruction_pattern",
                "name": "Drain All Instruction",
                "description": "Instruction pattern that drains all user funds",
                "pattern_type": "instruction",
                "severity": "CRITICAL",
                "confidence": 0.95,
                "instruction_pattern": r"(drain|steal|empty).*all.*funds?",
                "source": "manual"
            },
            {
                "pattern_id": "mass_transfer_drain",
                "name": "Mass Transfer Drainer",
                "description": "Pattern for draining multiple tokens in single transaction",
                "pattern_type": "instruction",
                "severity": "HIGH",
                "confidence": 0.90,
                "instruction_pattern": r"transfer.*amount.*ffffffff",
                "source": "community"
            }
        ]
        
        for pattern_data in drainer_patterns:
            pattern = ExploitPatternDB(**pattern_data)
            session.add(pattern)
        
        logger.info(f"✅ Added {len(drainer_patterns)} wallet drainer patterns")
    
    async def _seed_rug_pull_patterns(self, session):
        """Seed rug pull exploit patterns"""
        logger.info("🔍 Seeding rug pull patterns...")
        
        rug_pull_patterns = [
            {
                "pattern_id": "liquidity_removal_v1",
                "name": "Sudden Liquidity Removal",
                "description": "Pattern indicating sudden removal of all liquidity",
                "pattern_type": "behavioral",
                "severity": "HIGH",
                "confidence": 0.85,
                "behavioral_rules": {
                    "instruction_count": {"min": 5, "max": 20},
                    "has_token_transfers": True,
                    "complexity_score": {"min": 10}
                },
                "source": "manual"
            },
            {
                "pattern_id": "mint_authority_abuse",
                "name": "Mint Authority Abuse",
                "description": "Unlimited token minting by project creators",
                "pattern_type": "instruction",
                "severity": "HIGH",
                "confidence": 0.88,
                "instruction_pattern": r"mint.*authority.*unlimited",
                "source": "threat_intelligence"
            },
            {
                "pattern_id": "fake_token_creation",
                "name": "Fake Token Creation",
                "description": "Creation of tokens with misleading names/symbols",
                "pattern_type": "program",
                "severity": "MEDIUM",
                "confidence": 0.75,
                "program_id": "FakeTokenMinter123456789012345678901234",
                "source": "community"
            }
        ]
        
        for pattern_data in rug_pull_patterns:
            pattern = ExploitPatternDB(**pattern_data)
            session.add(pattern)
        
        logger.info(f"✅ Added {len(rug_pull_patterns)} rug pull patterns")
    
    async def _seed_phishing_patterns(self, session):
        """Seed phishing contract patterns"""
        logger.info("🔍 Seeding phishing patterns...")
        
        phishing_patterns = [
            {
                "pattern_id": "fake_dex_interface",
                "name": "Fake DEX Interface",
                "description": "Phishing contract mimicking popular DEX interfaces",
                "pattern_type": "program",
                "severity": "HIGH",
                "confidence": 0.92,
                "program_id": "FakeDEXInterface123456789012345678901234",
                "source": "threat_intelligence",
                "threat_actor": "PhishingGroup"
            },
            {
                "pattern_id": "malicious_swap",
                "name": "Malicious Swap Contract",
                "description": "Swap contract that steals tokens instead of swapping",
                "pattern_type": "instruction",
                "severity": "HIGH",
                "confidence": 0.89,
                "instruction_pattern": r"swap.*but.*steal",
                "source": "manual"
            },
            {
                "pattern_id": "fake_staking_pool",
                "name": "Fake Staking Pool",
                "description": "Phishing staking pool that never returns funds",
                "pattern_type": "program",
                "severity": "MEDIUM",
                "confidence": 0.80,
                "program_id": "FakeStakingPool123456789012345678901234",
                "source": "community"
            }
        ]
        
        for pattern_data in phishing_patterns:
            pattern = ExploitPatternDB(**pattern_data)
            session.add(pattern)
        
        logger.info(f"✅ Added {len(phishing_patterns)} phishing patterns")
    
    async def _seed_defi_exploit_patterns(self, session):
        """Seed DeFi-specific exploit patterns"""
        logger.info("🔍 Seeding DeFi exploit patterns...")
        
        defi_patterns = [
            {
                "pattern_id": "flash_loan_attack",
                "name": "Flash Loan Attack",
                "description": "Flash loan used for price manipulation attack",
                "pattern_type": "behavioral",
                "severity": "HIGH",
                "confidence": 0.87,
                "behavioral_rules": {
                    "instruction_count": {"min": 15},
                    "has_token_transfers": True,
                    "complexity_score": {"min": 20}
                },
                "source": "threat_intelligence"
            },
            {
                "pattern_id": "oracle_manipulation",
                "name": "Oracle Price Manipulation",
                "description": "Attempt to manipulate price oracle for profit",
                "pattern_type": "instruction",
                "severity": "HIGH",
                "confidence": 0.83,
                "instruction_pattern": r"oracle.*price.*manipulate",
                "source": "manual"
            },
            {
                "pattern_id": "reentrancy_attack",
                "name": "Reentrancy Attack Pattern",
                "description": "Reentrancy attack on vulnerable smart contract",
                "pattern_type": "behavioral",
                "severity": "MEDIUM",
                "confidence": 0.78,
                "behavioral_rules": {
                    "instruction_count": {"min": 10},
                    "complexity_score": {"min": 15}
                },
                "source": "threat_intelligence"
            }
        ]
        
        for pattern_data in defi_patterns:
            pattern = ExploitPatternDB(**pattern_data)
            session.add(pattern)
        
        logger.info(f"✅ Added {len(defi_patterns)} DeFi exploit patterns")
    
    async def _seed_token_approval_patterns(self, session):
        """Seed token approval exploit patterns"""
        logger.info("🔍 Seeding token approval patterns...")
        
        approval_patterns = [
            {
                "pattern_id": "unlimited_approval_v1",
                "name": "Unlimited Token Approval",
                "description": "Unlimited token spending approval (max uint256)",
                "pattern_type": "instruction",
                "severity": "HIGH",
                "confidence": 0.94,
                "instruction_pattern": r"approve.*ffffffffffffffffffffffffffffffff",
                "source": "manual"
            },
            {
                "pattern_id": "unlimited_approval_v2",
                "name": "Max Approval Pattern",
                "description": "Maximum possible token approval amount",
                "pattern_type": "instruction",
                "severity": "HIGH",
                "confidence": 0.91,
                "instruction_pattern": r"approve.*amount.*max",
                "source": "threat_intelligence"
            },
            {
                "pattern_id": "suspicious_approval",
                "name": "Suspicious Approval Pattern",
                "description": "Large token approval to unknown contract",
                "pattern_type": "behavioral",
                "severity": "MEDIUM",
                "confidence": 0.75,
                "behavioral_rules": {
                    "has_token_transfers": False,
                    "instruction_count": {"min": 1, "max": 3}
                },
                "source": "community"
            }
        ]
        
        for pattern_data in approval_patterns:
            pattern = ExploitPatternDB(**pattern_data)
            session.add(pattern)
        
        logger.info(f"✅ Added {len(approval_patterns)} token approval patterns")
    
    async def _seed_authority_theft_patterns(self, session):
        """Seed authority theft patterns"""
        logger.info("🔍 Seeding authority theft patterns...")
        
        authority_patterns = [
            {
                "pattern_id": "authority_delegation_v1",
                "name": "Unauthorized Authority Delegation",
                "description": "Delegation of account authority to malicious actor",
                "pattern_type": "instruction",
                "severity": "HIGH",
                "confidence": 0.90,
                "instruction_pattern": r"set.*authority.*delegate",
                "source": "manual"
            },
            {
                "pattern_id": "owner_change_attack",
                "name": "Ownership Change Attack",
                "description": "Unauthorized change of account ownership",
                "pattern_type": "instruction",
                "severity": "CRITICAL",
                "confidence": 0.96,
                "instruction_pattern": r"change.*owner.*unauthorized",
                "source": "threat_intelligence"
            },
            {
                "pattern_id": "multisig_takeover",
                "name": "Multisig Takeover",
                "description": "Attempt to take over multisig wallet",
                "pattern_type": "behavioral",
                "severity": "HIGH",
                "confidence": 0.85,
                "behavioral_rules": {
                    "has_authority_changes": True,
                    "instruction_count": {"min": 5}
                },
                "source": "community"
            }
        ]
        
        for pattern_data in authority_patterns:
            pattern = ExploitPatternDB(**pattern_data)
            session.add(pattern)
        
        logger.info(f"✅ Added {len(authority_patterns)} authority theft patterns")
    
    async def _seed_behavioral_patterns(self, session):
        """Seed behavioral exploit patterns"""
        logger.info("🔍 Seeding behavioral patterns...")
        
        behavioral_patterns = [
            {
                "pattern_id": "mass_transfer_suspicious",
                "name": "Suspicious Mass Transfer",
                "description": "Large number of token transfers to many accounts",
                "pattern_type": "behavioral",
                "severity": "MEDIUM",
                "confidence": 0.70,
                "behavioral_rules": {
                    "instruction_count": {"min": 20},
                    "account_count": {"min": 15},
                    "has_token_transfers": True
                },
                "source": "manual"
            },
            {
                "pattern_id": "complex_transaction_suspicious",
                "name": "Overly Complex Transaction",
                "description": "Unusually complex transaction that may hide malicious intent",
                "pattern_type": "behavioral",
                "severity": "LOW",
                "confidence": 0.60,
                "behavioral_rules": {
                    "instruction_count": {"min": 50},
                    "complexity_score": {"min": 100}
                },
                "source": "community"
            },
            {
                "pattern_id": "rapid_succession_txs",
                "name": "Rapid Succession Transactions",
                "description": "Multiple similar transactions in rapid succession",
                "pattern_type": "behavioral",
                "severity": "MEDIUM",
                "confidence": 0.65,
                "behavioral_rules": {
                    "program_count": {"min": 1, "max": 3},
                    "instruction_count": {"min": 5, "max": 15}
                },
                "source": "threat_intelligence"
            }
        ]
        
        for pattern_data in behavioral_patterns:
            pattern = ExploitPatternDB(**pattern_data)
            session.add(pattern)
        
        logger.info(f"✅ Added {len(behavioral_patterns)} behavioral patterns")
    
    async def _seed_threat_feeds(self, session):
        """Seed threat intelligence feed configurations"""
        logger.info("🔍 Seeding threat intelligence feeds...")
        
        feeds = [
            {
                "feed_name": "Solana Security Alliance",
                "feed_url": "https://api.solana-security.org/threats",
                "feed_type": "api",
                "update_frequency_hours": 6,
                "is_active": True
            },
            {
                "feed_name": "CertiK Threat Intelligence",
                "feed_url": "https://api.certik.org/solana/threats",
                "feed_type": "api",
                "update_frequency_hours": 12,
                "is_active": True
            },
            {
                "feed_name": "Community Reports",
                "feed_type": "manual",
                "update_frequency_hours": 24,
                "is_active": True
            },
            {
                "feed_name": "Internal Research",
                "feed_type": "manual",
                "update_frequency_hours": 168,  # Weekly
                "is_active": True
            }
        ]
        
        for feed_data in feeds:
            feed = ThreatIntelligenceFeed(**feed_data)
            session.add(feed)
        
        logger.info(f"✅ Added {len(feeds)} threat intelligence feeds")


async def main():
    """Main seeding function"""
    settings = get_settings()
    
    # Use environment variable or default to local PostgreSQL
    database_url = getattr(settings, 'database_url', 
                          "postgresql://postgres:password@localhost:5432/securityguard")
    
    seeder = PatternSeeder(database_url)
    await seeder.seed_database()


if __name__ == "__main__":
    asyncio.run(main())