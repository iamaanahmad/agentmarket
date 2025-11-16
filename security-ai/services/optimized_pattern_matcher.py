"""
Optimized pattern matcher with database connection pooling and caching
Enhanced for <100ms lookup time requirement
"""

import asyncio
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from loguru import logger

try:
    from ..core.config import get_settings
    from ..models.schemas import ExploitPattern
    from .cache_service import cache_service
    from .database_pool import database_pool
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings
    from models.schemas import ExploitPattern


@dataclass
class PatternMatchStats:
    """Pattern matching performance statistics"""
    total_lookups: int = 0
    cache_hits: int = 0
    database_hits: int = 0
    avg_lookup_time_ms: float = 0.0
    slow_lookups: int = 0


class OptimizedPatternMatcher:
    """
    High-performance pattern matcher with optimized database queries,
    intelligent caching, and sub-100ms lookup times
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.stats = PatternMatchStats()
        self.lookup_times: List[float] = []
        
        # Performance targets
        self.target_lookup_time_ms = 100
        self.cache_ttl_seconds = 1800  # 30 minutes
        
        # Pattern matching algorithms
        self.matchers = {
            'exact': self._exact_match,
            'fuzzy': self._fuzzy_match,
            'behavioral': self._behavioral_match,
            'account_pattern': self._account_pattern_match
        }
    
    async def initialize(self):
        """Initialize optimized pattern matcher"""
        try:
            # Ensure database pool is initialized
            if not database_pool.asyncpg_pool:
                await database_pool.initialize()
            
            # Pre-warm cache with most common patterns
            await self._preload_common_patterns()
            
            logger.info("✅ Optimized pattern matcher initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pattern matcher initialization failed: {e}")
            return False
    
    async def match_patterns(self, parsed_tx: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Match transaction patterns with optimized lookup and caching
        Target: <100ms for 95% of lookups
        """
        lookup_start = time.time()
        
        try:
            # Generate transaction fingerprint for caching
            tx_fingerprint = self._generate_transaction_fingerprint(parsed_tx)
            
            # Check cache first
            cached_matches = await cache_service.get('pattern_matches', tx_fingerprint, timeout=0.01)
            
            if cached_matches:
                self.stats.cache_hits += 1
                self.stats.total_lookups += 1
                lookup_time = (time.time() - lookup_start) * 1000
                self._record_lookup_time(lookup_time)
                
                logger.debug(f"⚡ Pattern cache hit: {lookup_time:.1f}ms")
                return cached_matches['matches'], cached_matches['stats']
            
            # Perform optimized pattern matching
            matches = []
            match_stats = {
                'patterns_checked': 0,
                'exact_matches': 0,
                'fuzzy_matches': 0,
                'behavioral_matches': 0,
                'lookup_time_ms': 0
            }
            
            # Extract key transaction features for efficient matching
            tx_features = self._extract_transaction_features(parsed_tx)
            
            # Run parallel pattern matching algorithms
            tasks = []
            for matcher_name, matcher_func in self.matchers.items():
                task = asyncio.create_task(
                    self._safe_pattern_match(matcher_func, tx_features, matcher_name)
                )
                tasks.append(task)
            
            # Wait for all matchers with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=0.08  # 80ms timeout for pattern matching
                )
                
                # Process results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.warning(f"Pattern matcher {list(self.matchers.keys())[i]} failed: {result}")
                        continue
                    
                    if result:
                        matches.extend(result)
                        match_stats['patterns_checked'] += len(result)
                        
                        # Count match types
                        matcher_name = list(self.matchers.keys())[i]
                        if matcher_name == 'exact':
                            match_stats['exact_matches'] += len(result)
                        elif matcher_name == 'fuzzy':
                            match_stats['fuzzy_matches'] += len(result)
                        elif matcher_name == 'behavioral':
                            match_stats['behavioral_matches'] += len(result)
            
            except asyncio.TimeoutError:
                logger.warning("⚠️ Pattern matching timeout, returning partial results")
            
            # Remove duplicates and sort by severity
            matches = self._deduplicate_and_sort_matches(matches)
            
            lookup_time = (time.time() - lookup_start) * 1000
            match_stats['lookup_time_ms'] = lookup_time
            
            # Cache results for future lookups
            cache_data = {
                'matches': matches,
                'stats': match_stats
            }
            await cache_service.set('pattern_matches', tx_fingerprint, cache_data, self.cache_ttl_seconds)
            
            # Update statistics
            self.stats.database_hits += 1
            self.stats.total_lookups += 1
            self._record_lookup_time(lookup_time)
            
            # Performance logging
            if lookup_time > self.target_lookup_time_ms:
                self.stats.slow_lookups += 1
                logger.warning(f"⚠️ Slow pattern lookup: {lookup_time:.1f}ms (target: {self.target_lookup_time_ms}ms)")
            else:
                logger.debug(f"⚡ Fast pattern lookup: {lookup_time:.1f}ms")
            
            return matches, match_stats
            
        except Exception as e:
            lookup_time = (time.time() - lookup_start) * 1000
            self.stats.total_lookups += 1
            self._record_lookup_time(lookup_time)
            
            logger.error(f"❌ Pattern matching failed after {lookup_time:.1f}ms: {e}")
            return [], {'error': str(e), 'lookup_time_ms': lookup_time}
    
    def _generate_transaction_fingerprint(self, parsed_tx: Dict[str, Any]) -> str:
        """Generate unique fingerprint for transaction caching"""
        # Create fingerprint from key transaction elements
        fingerprint_data = {
            'programs': sorted(parsed_tx.get('programs', [])),
            'instruction_count': len(parsed_tx.get('instructions', [])),
            'account_count': len(parsed_tx.get('accounts', [])),
            'signatures_required': parsed_tx.get('signatures_required', 0)
        }
        
        fingerprint_str = str(fingerprint_data)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()
    
    def _extract_transaction_features(self, parsed_tx: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key features for efficient pattern matching"""
        return {
            'programs': set(parsed_tx.get('programs', [])),
            'instructions': parsed_tx.get('instructions', []),
            'accounts': parsed_tx.get('accounts', []),
            'signatures_required': parsed_tx.get('signatures_required', 0),
            'program_count': len(parsed_tx.get('programs', [])),
            'instruction_count': len(parsed_tx.get('instructions', [])),
            'account_count': len(parsed_tx.get('accounts', []))
        }
    
    async def _safe_pattern_match(self, matcher_func, tx_features: Dict[str, Any], matcher_name: str) -> List[Dict[str, Any]]:
        """Safely execute pattern matcher with error handling"""
        try:
            return await matcher_func(tx_features)
        except Exception as e:
            logger.warning(f"Pattern matcher {matcher_name} failed: {e}")
            return []
    
    async def _exact_match(self, tx_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Exact program ID and instruction matching"""
        matches = []
        
        try:
            # Build optimized query for exact program matches
            program_list = list(tx_features['programs'])
            if not program_list:
                return matches
            
            # Use database pool for optimized query
            query = """
                SELECT pattern_id, pattern_type, program_id, severity, description, confidence
                FROM exploit_patterns 
                WHERE program_id = ANY($1) AND pattern_type = 'exact'
                ORDER BY severity DESC
                LIMIT 50
            """
            
            results = await database_pool.execute_query(query, program_list, timeout=0.05)
            
            for row in results:
                matches.append({
                    'pattern_id': row['pattern_id'],
                    'type': row['pattern_type'],
                    'severity': row['severity'],
                    'description': row['description'],
                    'confidence': row['confidence'],
                    'evidence': {'matched_program': row['program_id']},
                    'matcher': 'exact'
                })
            
        except Exception as e:
            logger.warning(f"Exact matching failed: {e}")
        
        return matches
    
    async def _fuzzy_match(self, tx_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fuzzy pattern matching for similar exploits"""
        matches = []
        
        try:
            # Fuzzy matching based on transaction characteristics
            query = """
                SELECT pattern_id, pattern_type, severity, description, confidence,
                       program_count, instruction_count, account_count
                FROM exploit_patterns 
                WHERE pattern_type = 'fuzzy'
                  AND ABS(program_count - $1) <= 2
                  AND ABS(instruction_count - $2) <= 3
                  AND ABS(account_count - $3) <= 5
                ORDER BY severity DESC
                LIMIT 20
            """
            
            results = await database_pool.execute_query(
                query,
                tx_features['program_count'],
                tx_features['instruction_count'],
                tx_features['account_count'],
                timeout=0.03
            )
            
            for row in results:
                # Calculate similarity score
                similarity = self._calculate_similarity(tx_features, row)
                
                if similarity > 0.7:  # 70% similarity threshold
                    matches.append({
                        'pattern_id': row['pattern_id'],
                        'type': row['pattern_type'],
                        'severity': row['severity'],
                        'description': row['description'],
                        'confidence': row['confidence'] * similarity,
                        'evidence': {'similarity_score': similarity},
                        'matcher': 'fuzzy'
                    })
            
        except Exception as e:
            logger.warning(f"Fuzzy matching failed: {e}")
        
        return matches
    
    async def _behavioral_match(self, tx_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Behavioral pattern matching for complex exploit sequences"""
        matches = []
        
        try:
            # Look for behavioral patterns (simplified implementation)
            if tx_features['instruction_count'] > 10 and tx_features['program_count'] > 5:
                # Potential complex exploit pattern
                query = """
                    SELECT pattern_id, pattern_type, severity, description, confidence
                    FROM exploit_patterns 
                    WHERE pattern_type = 'behavioral'
                      AND instruction_count > $1
                      AND program_count > $2
                    ORDER BY severity DESC
                    LIMIT 10
                """
                
                results = await database_pool.execute_query(
                    query,
                    tx_features['instruction_count'] - 2,
                    tx_features['program_count'] - 1,
                    timeout=0.02
                )
                
                for row in results:
                    matches.append({
                        'pattern_id': row['pattern_id'],
                        'type': row['pattern_type'],
                        'severity': row['severity'],
                        'description': row['description'],
                        'confidence': row['confidence'],
                        'evidence': {
                            'instruction_count': tx_features['instruction_count'],
                            'program_count': tx_features['program_count']
                        },
                        'matcher': 'behavioral'
                    })
            
        except Exception as e:
            logger.warning(f"Behavioral matching failed: {e}")
        
        return matches
    
    async def _account_pattern_match(self, tx_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Account interaction pattern matching"""
        matches = []
        
        try:
            # Check for suspicious account patterns
            if tx_features['account_count'] > 20:  # Many accounts involved
                query = """
                    SELECT pattern_id, pattern_type, severity, description, confidence
                    FROM exploit_patterns 
                    WHERE pattern_type = 'account_pattern'
                      AND account_count > $1
                    ORDER BY severity DESC
                    LIMIT 5
                """
                
                results = await database_pool.execute_query(
                    query,
                    tx_features['account_count'] - 5,
                    timeout=0.02
                )
                
                for row in results:
                    matches.append({
                        'pattern_id': row['pattern_id'],
                        'type': row['pattern_type'],
                        'severity': row['severity'],
                        'description': row['description'],
                        'confidence': row['confidence'],
                        'evidence': {'account_count': tx_features['account_count']},
                        'matcher': 'account_pattern'
                    })
            
        except Exception as e:
            logger.warning(f"Account pattern matching failed: {e}")
        
        return matches
    
    def _calculate_similarity(self, tx_features: Dict[str, Any], pattern_row: Dict[str, Any]) -> float:
        """Calculate similarity score between transaction and pattern"""
        try:
            # Simple similarity calculation based on feature differences
            program_diff = abs(tx_features['program_count'] - pattern_row.get('program_count', 0))
            instruction_diff = abs(tx_features['instruction_count'] - pattern_row.get('instruction_count', 0))
            account_diff = abs(tx_features['account_count'] - pattern_row.get('account_count', 0))
            
            # Normalize differences
            max_diff = max(program_diff, instruction_diff, account_diff)
            if max_diff == 0:
                return 1.0
            
            similarity = 1.0 - (max_diff / (max_diff + 10))  # Normalize to 0-1 range
            return max(0.0, min(1.0, similarity))
            
        except Exception:
            return 0.5  # Default similarity
    
    def _deduplicate_and_sort_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate matches and sort by severity"""
        # Remove duplicates based on pattern_id
        seen_patterns = set()
        unique_matches = []
        
        for match in matches:
            pattern_id = match.get('pattern_id')
            if pattern_id not in seen_patterns:
                seen_patterns.add(pattern_id)
                unique_matches.append(match)
        
        # Sort by severity (descending) and confidence (descending)
        unique_matches.sort(
            key=lambda x: (x.get('severity', 0), x.get('confidence', 0)),
            reverse=True
        )
        
        return unique_matches[:20]  # Limit to top 20 matches
    
    async def _preload_common_patterns(self):
        """Pre-load most common patterns into cache"""
        try:
            # Get most frequently matched patterns
            query = """
                SELECT pattern_id, pattern_type, program_id, severity, description, confidence
                FROM exploit_patterns 
                WHERE match_count > 100  -- Frequently matched patterns
                ORDER BY match_count DESC
                LIMIT 100
            """
            
            results = await database_pool.execute_query(query, timeout=1.0)
            
            # Cache common patterns
            for row in results:
                cache_key = f"common_pattern_{row['pattern_id']}"
                await cache_service.set('pattern_matches', cache_key, row, self.cache_ttl_seconds * 2)
            
            logger.info(f"✅ Pre-loaded {len(results)} common patterns into cache")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to preload common patterns: {e}")
    
    def _record_lookup_time(self, lookup_time_ms: float):
        """Record lookup time for performance monitoring"""
        self.lookup_times.append(lookup_time_ms)
        
        # Keep only recent lookup times
        if len(self.lookup_times) > 1000:
            self.lookup_times = self.lookup_times[-500:]
        
        # Update average
        if self.lookup_times:
            self.stats.avg_lookup_time_ms = sum(self.lookup_times) / len(self.lookup_times)
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get pattern matcher performance statistics"""
        return {
            'total_lookups': self.stats.total_lookups,
            'cache_hits': self.stats.cache_hits,
            'database_hits': self.stats.database_hits,
            'cache_hit_rate': self.stats.cache_hits / max(1, self.stats.total_lookups),
            'avg_lookup_time_ms': self.stats.avg_lookup_time_ms,
            'slow_lookups': self.stats.slow_lookups,
            'slow_lookup_rate': self.stats.slow_lookups / max(1, self.stats.total_lookups),
            'target_lookup_time_ms': self.target_lookup_time_ms,
            'performance_target_met': self.stats.avg_lookup_time_ms < self.target_lookup_time_ms
        }


# Global optimized pattern matcher instance
optimized_pattern_matcher = OptimizedPatternMatcher()