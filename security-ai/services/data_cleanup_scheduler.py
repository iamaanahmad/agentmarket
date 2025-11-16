"""
Data Cleanup Scheduler for SecurityGuard AI
Handles automated data retention and privacy compliance
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from .analytics_service import AnalyticsService


class DataCleanupScheduler:
    """
    Scheduler for automated data cleanup and retention compliance
    Runs background tasks for expired data removal
    """
    
    def __init__(self, analytics_service: AnalyticsService):
        self.analytics_service = analytics_service
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.cleanup_interval_hours = 6  # Run cleanup every 6 hours
        
    async def start(self):
        """Start the data cleanup scheduler"""
        if self.is_running:
            logger.warning("Data cleanup scheduler already running")
            return
        
        self.is_running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("🧹 Data cleanup scheduler started (runs every 6 hours)")
    
    async def stop(self):
        """Stop the data cleanup scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Data cleanup scheduler stopped")
    
    async def _cleanup_loop(self):
        """Main cleanup loop that runs periodically"""
        while self.is_running:
            try:
                # Wait for the cleanup interval
                await asyncio.sleep(self.cleanup_interval_hours * 3600)
                
                if not self.is_running:
                    break
                
                # Run cleanup
                await self._run_cleanup()
                
            except asyncio.CancelledError:
                logger.info("Data cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Data cleanup loop error: {e}")
                # Continue running even if cleanup fails
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def _run_cleanup(self):
        """Run the actual data cleanup process"""
        try:
            logger.info("🧹 Starting scheduled data cleanup...")
            
            # Clean up expired data
            cleanup_result = await self.analytics_service.cleanup_expired_data()
            
            if "error" in cleanup_result:
                logger.error(f"❌ Data cleanup failed: {cleanup_result['error']}")
            else:
                expired_scans = cleanup_result.get("expired_scans_deleted", 0)
                expired_cache = cleanup_result.get("expired_cache_deleted", 0)
                
                if expired_scans > 0 or expired_cache > 0:
                    logger.info(f"✅ Data cleanup completed: {expired_scans} scans, {expired_cache} cache entries removed")
                else:
                    logger.debug("✅ Data cleanup completed: no expired data found")
            
        except Exception as e:
            logger.error(f"❌ Data cleanup execution failed: {e}")
    
    async def run_manual_cleanup(self) -> dict:
        """Run manual cleanup (for admin endpoints)"""
        try:
            logger.info("🧹 Running manual data cleanup...")
            result = await self.analytics_service.cleanup_expired_data()
            
            if "error" not in result:
                logger.info("✅ Manual data cleanup completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Manual data cleanup failed: {e}")
            return {"error": f"Manual cleanup failed: {str(e)}"}