"""
Threat Intelligence Service for SecurityGuard AI
Automated daily pattern updates from threat intelligence feeds
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import aiohttp
from dataclasses import dataclass

from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, or_
from loguru import logger

try:
    from ..core.config import get_settings
    from ..models.database import (
        ExploitPatternDB, ThreatIntelligenceFeed, 
        ScanHistoryDB, ScanPatternMatch
    )
    from ..services.pattern_matcher import PatternMatcher
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings
    from models.database import (
        ExploitPatternDB, ThreatIntelligenceFeed,
        ScanHistoryDB, ScanPatternMatch
    )
    from services.pattern_matcher import PatternMatcher


@dataclass
class ThreatUpdate:
    """Threat intelligence update result"""
    feed_name: str
    patterns_added: int
    patterns_updated: int
    patterns_deactivated: int
    errors: List[str]
    update_time_ms: float


class ThreatIntelligenceService:
    """
    Automated threat intelligence service
    Updates exploit patterns daily from multiple sources
    """
    
    def __init__(self, database_session_factory: sessionmaker, 
                 pattern_matcher: Optional[PatternMatcher] = None):
        self.settings = get_settings()
        self.db_session_factory = database_session_factory
        self.pattern_matcher = pattern_matcher
        
        # HTTP client for API feeds
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Update tracking
        self.last_update_check = datetime.utcnow()
        self.update_in_progress = False
        
    async def initialize(self):
        """Initialize threat intelligence service"""
        try:
            # Create HTTP session for API calls
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.http_session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'User-Agent': 'SecurityGuard-AI/1.0',
                    'Accept': 'application/json'
                }
            )
            
            logger.info("✅ Threat intelligence service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize threat intelligence service: {e}")
    
    async def run_daily_updates(self) -> List[ThreatUpdate]:
        """
        Run daily threat intelligence updates
        Updates patterns from all active feeds
        """
        if self.update_in_progress:
            logger.warning("⚠️ Update already in progress, skipping")
            return []
        
        self.update_in_progress = True
        start_time = time.time()
        
        try:
            logger.info("🔄 Starting daily threat intelligence updates...")
            
            session = self.db_session_factory()
            updates = []
            
            try:
                # Get active threat intelligence feeds
                feeds = session.query(ThreatIntelligenceFeed).filter(
                    ThreatIntelligenceFeed.is_active == True
                ).all()
                
                logger.info(f"📡 Processing {len(feeds)} threat intelligence feeds")
                
                # Process each feed
                for feed in feeds:
                    if self._should_update_feed(feed):
                        update_result = await self._update_from_feed(session, feed)
                        updates.append(update_result)
                        
                        # Update feed timestamp
                        feed.last_update = datetime.utcnow()
                        if update_result.errors:
                            feed.error_count += len(update_result.errors)
                            feed.last_error = "; ".join(update_result.errors)
                        else:
                            feed.last_successful_update = datetime.utcnow()
                            feed.error_count = 0
                            feed.last_error = None
                        
                        feed.patterns_added += update_result.patterns_added
                        feed.patterns_updated += update_result.patterns_updated
                
                session.commit()
                
                # Reload patterns in pattern matcher if available
                if self.pattern_matcher:
                    await self.pattern_matcher.reload_patterns()
                
                # Clean up old patterns and cache
                await self._cleanup_old_data(session)
                
                total_time = (time.time() - start_time) * 1000
                total_added = sum(u.patterns_added for u in updates)
                total_updated = sum(u.patterns_updated for u in updates)
                
                logger.info(f"✅ Daily updates completed in {total_time:.1f}ms: "
                           f"{total_added} added, {total_updated} updated")
                
                return updates
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"❌ Daily updates failed: {e}")
            return []
        finally:
            self.update_in_progress = False
    
    def _should_update_feed(self, feed: ThreatIntelligenceFeed) -> bool:
        """Check if feed should be updated based on frequency"""
        if not feed.last_update:
            return True
        
        hours_since_update = (datetime.utcnow() - feed.last_update).total_seconds() / 3600
        return hours_since_update >= feed.update_frequency_hours
    
    async def _update_from_feed(self, session, feed: ThreatIntelligenceFeed) -> ThreatUpdate:
        """Update patterns from a specific threat intelligence feed"""
        start_time = time.time()
        update_result = ThreatUpdate(
            feed_name=feed.feed_name,
            patterns_added=0,
            patterns_updated=0,
            patterns_deactivated=0,
            errors=[],
            update_time_ms=0
        )
        
        try:
            logger.info(f"📡 Updating from feed: {feed.feed_name}")
            
            if feed.feed_type == "api":
                patterns = await self._fetch_api_patterns(feed)
            elif feed.feed_type == "rss":
                patterns = await self._fetch_rss_patterns(feed)
            elif feed.feed_type == "manual":
                patterns = await self._fetch_manual_patterns(feed)
            else:
                update_result.errors.append(f"Unknown feed type: {feed.feed_type}")
                return update_result
            
            # Process fetched patterns
            for pattern_data in patterns:
                try:
                    result = await self._process_pattern_update(session, pattern_data, feed.feed_name)
                    if result == "added":
                        update_result.patterns_added += 1
                    elif result == "updated":
                        update_result.patterns_updated += 1
                    elif result == "deactivated":
                        update_result.patterns_deactivated += 1
                        
                except Exception as pattern_error:
                    update_result.errors.append(f"Pattern processing error: {pattern_error}")
                    logger.warning(f"Failed to process pattern: {pattern_error}")
            
            update_result.update_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Feed {feed.feed_name}: {update_result.patterns_added} added, "
                       f"{update_result.patterns_updated} updated in {update_result.update_time_ms:.1f}ms")
            
        except Exception as e:
            update_result.errors.append(str(e))
            logger.error(f"❌ Feed update failed for {feed.feed_name}: {e}")
        
        return update_result
    
    async def _fetch_api_patterns(self, feed: ThreatIntelligenceFeed) -> List[Dict[str, Any]]:
        """Fetch patterns from API endpoint"""
        if not self.http_session or not feed.feed_url:
            return []
        
        try:
            async with self.http_session.get(feed.feed_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Handle different API response formats
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        # Common formats: {"patterns": [...]} or {"threats": [...]}
                        return data.get("patterns", data.get("threats", data.get("data", [])))
                    
                else:
                    logger.warning(f"API returned status {response.status} for {feed.feed_name}")
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to fetch from API {feed.feed_url}: {e}")
            return []
    
    async def _fetch_rss_patterns(self, feed: ThreatIntelligenceFeed) -> List[Dict[str, Any]]:
        """Fetch patterns from RSS feed"""
        # RSS parsing would be implemented here
        # For now, return empty list
        logger.info(f"RSS feed processing not implemented for {feed.feed_name}")
        return []
    
    async def _fetch_manual_patterns(self, feed: ThreatIntelligenceFeed) -> List[Dict[str, Any]]:
        """Fetch manually curated patterns"""
        # Manual patterns could come from internal research, community reports, etc.
        # For now, return some sample patterns
        
        if feed.feed_name == "Community Reports":
            return await self._get_community_patterns()
        elif feed.feed_name == "Internal Research":
            return await self._get_internal_research_patterns()
        
        return []
    
    async def _get_community_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns from community reports"""
        # This would integrate with community reporting system
        return [
            {
                "pattern_id": f"community_{int(time.time())}",
                "name": "Community Reported Threat",
                "description": "Threat pattern reported by community",
                "pattern_type": "program",
                "severity": "MEDIUM",
                "confidence": 0.70,
                "program_id": "CommunityReported123456789012345678901",
                "source": "community"
            }
        ]
    
    async def _get_internal_research_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns from internal security research"""
        # This would integrate with internal research findings
        return [
            {
                "pattern_id": f"research_{int(time.time())}",
                "name": "Research-Based Pattern",
                "description": "Pattern identified through internal security research",
                "pattern_type": "behavioral",
                "severity": "HIGH",
                "confidence": 0.85,
                "behavioral_rules": {
                    "instruction_count": {"min": 10},
                    "complexity_score": {"min": 25}
                },
                "source": "internal_research"
            }
        ]
    
    async def _process_pattern_update(self, session, pattern_data: Dict[str, Any], 
                                    source: str) -> str:
        """Process a single pattern update"""
        pattern_id = pattern_data.get("pattern_id")
        if not pattern_id:
            raise ValueError("Pattern missing required pattern_id")
        
        # Check if pattern already exists
        existing_pattern = session.query(ExploitPatternDB).filter(
            ExploitPatternDB.pattern_id == pattern_id
        ).first()
        
        if existing_pattern:
            # Update existing pattern
            for key, value in pattern_data.items():
                if hasattr(existing_pattern, key) and key != "id":
                    setattr(existing_pattern, key, value)
            
            existing_pattern.updated_at = datetime.utcnow()
            existing_pattern.source = source
            
            return "updated"
        else:
            # Create new pattern
            pattern_data["source"] = source
            pattern_data["created_at"] = datetime.utcnow()
            pattern_data["updated_at"] = datetime.utcnow()
            
            new_pattern = ExploitPatternDB(**pattern_data)
            session.add(new_pattern)
            
            return "added"
    
    async def _cleanup_old_data(self, session):
        """Clean up old patterns and scan data"""
        try:
            # Deactivate patterns that haven't matched in 90 days
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            old_patterns = session.query(ExploitPatternDB).filter(
                and_(
                    ExploitPatternDB.updated_at < cutoff_date,
                    ExploitPatternDB.match_count == 0,
                    ExploitPatternDB.severity.in_(["LOW", "MEDIUM"])
                )
            ).all()
            
            for pattern in old_patterns:
                pattern.is_active = False
                logger.debug(f"Deactivated old pattern: {pattern.pattern_id}")
            
            # Clean up expired scan history (privacy compliance)
            expired_scans = session.query(ScanHistoryDB).filter(
                and_(
                    ScanHistoryDB.expires_at.isnot(None),
                    ScanHistoryDB.expires_at < datetime.utcnow()
                )
            ).all()
            
            for scan in expired_scans:
                session.delete(scan)
            
            session.commit()
            
            logger.info(f"🧹 Cleanup completed: {len(old_patterns)} patterns deactivated, "
                       f"{len(expired_scans)} expired scans removed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            session.rollback()
    
    async def get_pattern_effectiveness_stats(self) -> Dict[str, Any]:
        """Get statistics on pattern effectiveness"""
        session = self.db_session_factory()
        
        try:
            # Get pattern match statistics
            total_patterns = session.query(ExploitPatternDB).filter(
                ExploitPatternDB.is_active == True
            ).count()
            
            active_patterns = session.query(ExploitPatternDB).filter(
                and_(
                    ExploitPatternDB.is_active == True,
                    ExploitPatternDB.match_count > 0
                )
            ).count()
            
            # Get false positive rates
            false_positive_count = session.query(ScanPatternMatch).filter(
                ScanPatternMatch.is_false_positive == True
            ).count()
            
            total_matches = session.query(ScanPatternMatch).count()
            
            false_positive_rate = false_positive_count / max(1, total_matches)
            
            # Get top performing patterns
            top_patterns = session.query(ExploitPatternDB).filter(
                ExploitPatternDB.is_active == True
            ).order_by(
                ExploitPatternDB.match_count.desc()
            ).limit(10).all()
            
            return {
                "total_patterns": total_patterns,
                "active_patterns": active_patterns,
                "pattern_utilization_rate": active_patterns / max(1, total_patterns),
                "false_positive_rate": false_positive_rate,
                "total_matches": total_matches,
                "top_patterns": [
                    {
                        "pattern_id": p.pattern_id,
                        "name": p.name,
                        "match_count": p.match_count,
                        "severity": p.severity
                    }
                    for p in top_patterns
                ]
            }
            
        finally:
            session.close()
    
    async def close(self):
        """Close HTTP session and cleanup"""
        if self.http_session:
            await self.http_session.close()


# Background task runner for daily updates
class ThreatIntelligenceScheduler:
    """Scheduler for automated threat intelligence updates"""
    
    def __init__(self, threat_service: ThreatIntelligenceService):
        self.threat_service = threat_service
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the scheduler"""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info("🕐 Threat intelligence scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Threat intelligence scheduler stopped")
    
    async def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Run updates every 6 hours
                await asyncio.sleep(6 * 3600)  # 6 hours
                
                if self.running:
                    await self.threat_service.run_daily_updates()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                # Continue running despite errors
                await asyncio.sleep(300)  # Wait 5 minutes before retry