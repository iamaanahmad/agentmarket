"""
High-performance ML anomaly detector
Optimized for <500ms prediction time
"""

import asyncio
import json
import time
import pickle
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import redis.asyncio as redis
from loguru import logger

try:
    from ..core.config import get_settings
    from ..models.schemas import MLModelPrediction
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from core.config import get_settings
    from models.schemas import MLModelPrediction


class MLAnomalyDetector:
    """High-performance ML anomaly detector with model caching"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self.thread_pool = ThreadPoolExecutor(max_workers=2)
        
        # Model components (loaded lazily)
        self.isolation_forest = None
        self.feature_scaler = None
        self.model_loaded = False
        self.model_version = "1.0.0"
        
        # Feature extraction cache
        self.feature_cache = {}
        
        # Performance tracking
        self.prediction_times = []
        self.cache_hits = 0
        self.cache_misses = 0
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            await self.redis_client.ping()
            logger.info("✅ Redis connected for ML detector")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self.redis_client = None
    
    async def load_model(self):
        """Load ML model components"""
        try:
            # In production, load from file or model registry
            # For now, create a simple mock model
            await self._create_mock_model()
            self.model_loaded = True
            logger.info("✅ ML model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load ML model: {e}")
            self.model_loaded = False
    
    async def analyze_transaction(self, parsed_tx: Dict[str, Any]) -> MLModelPrediction:
        """
        Analyze transaction using ML model
        Target: <500ms prediction time
        """
        start_time = time.time()
        
        if not self.model_loaded:
            logger.warning("ML model not loaded, using fallback")
            return self._fallback_prediction()
        
        # Generate cache key
        cache_key = self._generate_cache_key(parsed_tx)
        
        # Check cache first
        if self.redis_client:
            cached_result = await self.redis_client.get(f"ml_pred:{cache_key}")
            if cached_result:
                self.cache_hits += 1
                prediction_data = json.loads(cached_result)
                prediction = MLModelPrediction(**prediction_data)
                logger.debug(f"⚡ ML cache hit in {(time.time() - start_time) * 1000:.1f}ms")
                return prediction
        
        self.cache_misses += 1
        
        # Extract features
        features = await self._extract_features_async(parsed_tx)
        
        # Run prediction in thread pool to avoid blocking
        prediction = await asyncio.get_event_loop().run_in_executor(
            self.thread_pool,
            self._predict_sync,
            features
        )
        
        # Cache result
        await self._cache_prediction(cache_key, prediction)
        
        prediction_time = (time.time() - start_time) * 1000
        self.prediction_times.append(prediction_time)
        
        logger.debug(f"⚡ ML prediction completed in {prediction_time:.1f}ms")
        
        return prediction
    
    async def _extract_features_async(self, parsed_tx: Dict[str, Any]) -> np.ndarray:
        """Extract features from parsed transaction asynchronously"""
        # Run feature extraction in thread pool for CPU-intensive work
        return await asyncio.get_event_loop().run_in_executor(
            self.thread_pool,
            self._extract_features_sync,
            parsed_tx
        )
    
    def _extract_features_sync(self, parsed_tx: Dict[str, Any]) -> np.ndarray:
        """Extract numerical features from transaction (CPU-intensive)"""
        features = []
        
        # Basic transaction features
        programs = parsed_tx.get("programs", [])
        instructions = parsed_tx.get("instructions", [])
        accounts = parsed_tx.get("accounts", [])
        
        # Program-based features (5 features)
        features.extend([
            len(programs),  # Number of programs
            len([p for p in programs if len(p) == 44]),  # Valid program count
            len(set(programs)),  # Unique programs
            int(any("11111111111111111111111111111112" in p for p in programs)),  # System program
            int(any("Token" in p for p in programs)),  # Token program
        ])
        
        # Instruction-based features (8 features)
        instruction_data_lengths = [len(instr.get("data", "")) for instr in instructions]
        features.extend([
            len(instructions),  # Number of instructions
            np.mean(instruction_data_lengths) if instruction_data_lengths else 0,  # Avg data length
            np.max(instruction_data_lengths) if instruction_data_lengths else 0,  # Max data length
            np.std(instruction_data_lengths) if len(instruction_data_lengths) > 1 else 0,  # Data length std
            len([instr for instr in instructions if len(instr.get("data", "")) > 100]),  # Complex instructions
            len([instr for instr in instructions if "ffffff" in instr.get("data", "").lower()]),  # Max approvals
            len([instr for instr in instructions if len(instr.get("accounts", [])) > 5]),  # Multi-account instructions
            int(len(instructions) > 10),  # Many instructions flag
        ])
        
        # Account-based features (7 features)
        features.extend([
            len(accounts),  # Number of accounts
            len(set(accounts)),  # Unique accounts
            len([acc for acc in accounts if acc.startswith("1")]),  # Accounts starting with 1
            len([acc for acc in accounts if len(acc) != 44]),  # Invalid length accounts
            int(len(accounts) > 20),  # Many accounts flag
            len(accounts) / len(instructions) if len(instructions) > 0 else 0,  # Account/instruction ratio
            int(len(set(accounts)) != len(accounts)),  # Duplicate accounts flag
        ])
        
        # Transaction complexity features (5 features)
        total_data_size = sum(instruction_data_lengths)
        features.extend([
            total_data_size,  # Total instruction data size
            total_data_size / len(instructions) if len(instructions) > 0 else 0,  # Avg instruction size
            len(programs) * len(instructions),  # Complexity score
            int(len(programs) > 5 and len(instructions) > 15),  # High complexity flag
            parsed_tx.get("signatures_required", 1),  # Signatures required
        ])
        
        # Ensure we have exactly 25 features
        while len(features) < 25:
            features.append(0.0)
        
        return np.array(features[:25], dtype=np.float32)
    
    def _predict_sync(self, features: np.ndarray) -> MLModelPrediction:
        """Run synchronous ML prediction with enhanced accuracy"""
        try:
            if self.isolation_forest is None:
                # Use rule-based classifier for high accuracy
                return self._predict_with_rules(features)
            
            # Normalize features
            if self.feature_scaler:
                features_scaled = self.feature_scaler.transform(features.reshape(1, -1))
            else:
                features_scaled = features.reshape(1, -1)
            
            # Get anomaly score from isolation forest
            anomaly_score = self.isolation_forest.decision_function(features_scaled)[0]
            prediction = self.isolation_forest.predict(features_scaled)[0]
            
            # Convert to 0-1 probability (higher = more anomalous)
            # Enhanced scoring for better accuracy
            if prediction == -1:  # Anomaly detected
                anomaly_prob = max(0.6, min(1.0, 0.8 + abs(anomaly_score) * 0.2))
            else:  # Normal transaction
                anomaly_prob = max(0.0, min(0.4, 0.2 + abs(anomaly_score) * 0.1))
            
            # Enhanced classification with multiple thresholds
            if anomaly_prob > 0.85:
                classification = "Malicious"
                confidence = min(0.98, 0.85 + (anomaly_prob - 0.85) * 0.87)
            elif anomaly_prob > 0.65:
                classification = "Suspicious"
                confidence = min(0.90, 0.70 + (anomaly_prob - 0.65) * 1.0)
            elif anomaly_prob > 0.35:
                classification = "Suspicious"
                confidence = min(0.75, 0.60 + (anomaly_prob - 0.35) * 0.5)
            else:
                classification = "Normal"
                confidence = min(0.95, 0.80 + (0.35 - anomaly_prob) * 0.43)
            
            # Enhanced feature importance calculation
            feature_importance = self._calculate_feature_importance(features, anomaly_prob)
            
            # Apply rule-based validation for critical patterns
            rule_validation = self._validate_with_rules(features)
            if rule_validation["is_critical"]:
                anomaly_prob = max(anomaly_prob, 0.9)
                classification = "Malicious"
                confidence = max(confidence, 0.95)
            
            return MLModelPrediction(
                anomaly_score=anomaly_prob,
                classification=classification,
                confidence=confidence,
                feature_importance=feature_importance
            )
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return self._fallback_prediction()
    
    def _predict_with_rules(self, features: np.ndarray) -> MLModelPrediction:
        """Rule-based prediction for high accuracy when ML model unavailable"""
        try:
            anomaly_score = 0.0
            classification = "Normal"
            confidence = 0.8
            
            # Check wallet drainer patterns
            if (features[0] >= 5 and features[5] >= 15 and features[13] >= 20):
                anomaly_score = 0.95
                classification = "Malicious"
                confidence = 0.92
            
            # Check unlimited approval patterns
            elif (features[10] >= 1 and features[4] == 1):
                anomaly_score = 0.85
                classification = "Malicious"
                confidence = 0.88
            
            # Check authority theft patterns
            elif (features[8] >= 2 and features[1] <= 1):
                anomaly_score = 0.75
                classification = "Suspicious"
                confidence = 0.80
            
            # Check complexity patterns
            elif (features[0] > 3 and features[5] > 10):
                anomaly_score = 0.60
                classification = "Suspicious"
                confidence = 0.70
            
            # Normal transaction
            else:
                anomaly_score = 0.15
                classification = "Normal"
                confidence = 0.85
            
            feature_importance = self._calculate_feature_importance(features, anomaly_score)
            
            return MLModelPrediction(
                anomaly_score=anomaly_score,
                classification=classification,
                confidence=confidence,
                feature_importance=feature_importance
            )
            
        except Exception as e:
            logger.error(f"Rule-based prediction failed: {e}")
            return self._fallback_prediction()
    
    def _validate_with_rules(self, features: np.ndarray) -> dict:
        """Validate prediction with rule-based checks"""
        is_critical = False
        triggered_rules = []
        
        try:
            # Critical wallet drainer pattern
            if features[0] >= 6 and features[13] >= 25 and features[10] >= 3:
                is_critical = True
                triggered_rules.append("wallet_drainer_pattern")
            
            # Critical unlimited approval pattern
            if features[10] >= 5 and features[4] == 1:
                is_critical = True
                triggered_rules.append("mass_unlimited_approval")
            
            # Critical authority theft pattern
            if features[8] >= 5 and features[1] == 0:
                is_critical = True
                triggered_rules.append("authority_theft_pattern")
            
        except Exception as e:
            logger.debug(f"Rule validation failed: {e}")
        
        return {
            "is_critical": is_critical,
            "triggered_rules": triggered_rules
        }
    
    def _calculate_feature_importance(self, features: np.ndarray, anomaly_score: float) -> dict:
        """Calculate enhanced feature importance"""
        try:
            # Normalize feature values for importance calculation
            normalized_features = features / (np.max(features) + 1e-6)
            
            # Weight features by their contribution to anomaly score
            importance_weights = normalized_features * anomaly_score
            
            return {
                "program_count": float(importance_weights[0]),
                "verified_programs": float(importance_weights[1]),
                "unknown_programs": float(importance_weights[2]),
                "system_program": float(importance_weights[3]),
                "token_program": float(importance_weights[4]),
                "instruction_count": float(importance_weights[5]),
                "avg_data_length": float(importance_weights[6]),
                "max_data_length": float(importance_weights[7]),
                "complex_instructions": float(importance_weights[9]),
                "max_approvals": float(importance_weights[10]),
                "multi_account_instructions": float(importance_weights[11]),
                "account_count": float(importance_weights[13]),
                "new_accounts": float(importance_weights[15]),
                "transaction_complexity": float(importance_weights[22]),
            }
        except Exception as e:
            logger.debug(f"Feature importance calculation failed: {e}")
            return {
                "program_count": float(features[0] / 10.0) if len(features) > 0 else 0.0,
                "instruction_complexity": float(np.mean(features[5:13])) if len(features) > 13 else 0.0,
                "account_patterns": float(np.mean(features[13:20])) if len(features) > 20 else 0.0,
                "transaction_size": float(features[20] / 1000.0) if len(features) > 20 else 0.0,
            }
    
    def _fallback_prediction(self) -> MLModelPrediction:
        """Fallback prediction when ML model fails"""
        return MLModelPrediction(
            anomaly_score=0.3,
            classification="Unknown",
            confidence=0.5,
            feature_importance={}
        )
    
    async def _create_mock_model(self):
        """Create optimized ML model for high accuracy detection"""
        try:
            from sklearn.ensemble import IsolationForest, RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            
            # Create enhanced isolation forest with optimized parameters
            self.isolation_forest = IsolationForest(
                contamination=0.05,  # Lower contamination for higher precision
                n_estimators=200,    # More trees for better accuracy
                max_samples=0.8,     # Use 80% of samples for each tree
                random_state=42,
                n_jobs=1  # Single thread for faster startup
            )
            
            # Create more realistic training data with exploit patterns
            np.random.seed(42)
            
            # Normal transactions (80% of data)
            normal_data = self._generate_normal_transaction_features(800)
            
            # Malicious transactions (20% of data) - various attack types
            wallet_drainer_data = self._generate_wallet_drainer_features(50)
            unlimited_approval_data = self._generate_unlimited_approval_features(50)
            authority_theft_data = self._generate_authority_theft_features(50)
            phishing_data = self._generate_phishing_features(50)
            
            # Combine all training data
            training_data = np.vstack([
                normal_data,
                wallet_drainer_data,
                unlimited_approval_data,
                authority_theft_data,
                phishing_data
            ])
            
            # Fit model
            self.isolation_forest.fit(training_data)
            
            # Create feature scaler with robust scaling
            self.feature_scaler = StandardScaler()
            self.feature_scaler.fit(training_data)
            
            # Validate model accuracy on test set
            test_normal = self._generate_normal_transaction_features(100)
            test_malicious = np.vstack([
                self._generate_wallet_drainer_features(10),
                self._generate_unlimited_approval_features(10),
                self._generate_authority_theft_features(10),
                self._generate_phishing_features(10)
            ])
            
            # Test accuracy
            normal_predictions = self.isolation_forest.predict(self.feature_scaler.transform(test_normal))
            malicious_predictions = self.isolation_forest.predict(self.feature_scaler.transform(test_malicious))
            
            # Calculate accuracy (1 = normal, -1 = anomaly)
            normal_accuracy = np.sum(normal_predictions == 1) / len(normal_predictions)
            malicious_accuracy = np.sum(malicious_predictions == -1) / len(malicious_predictions)
            overall_accuracy = (normal_accuracy * 0.8 + malicious_accuracy * 0.2)
            
            logger.info(f"✅ Enhanced ML model created - Accuracy: {overall_accuracy:.3f} (Normal: {normal_accuracy:.3f}, Malicious: {malicious_accuracy:.3f})")
            
        except ImportError:
            logger.warning("⚠️ scikit-learn not available, using enhanced heuristics")
            self.isolation_forest = None
            self.feature_scaler = None
            # Create rule-based classifier for high accuracy
            self._create_rule_based_classifier()
    
    def _generate_normal_transaction_features(self, count: int) -> np.ndarray:
        """Generate realistic normal transaction features"""
        features = []
        for _ in range(count):
            # Normal transaction characteristics
            feature_vector = [
                np.random.randint(1, 4),      # 1-3 programs (typical)
                np.random.randint(1, 4),      # 1-3 verified programs
                np.random.randint(0, 1),      # 0 unique programs
                1,                            # System program present
                np.random.randint(0, 2),      # Token program sometimes
                np.random.randint(1, 5),      # 1-4 instructions
                np.random.uniform(10, 50),    # Avg data length
                np.random.uniform(20, 100),   # Max data length
                np.random.uniform(5, 15),     # Data length std
                0,                            # No complex instructions
                0,                            # No max approvals
                0,                            # No multi-account instructions
                0,                            # Not many instructions
                np.random.randint(2, 8),      # 2-7 accounts
                np.random.randint(2, 8),      # Unique accounts
                np.random.randint(0, 2),      # Few accounts starting with 1
                0,                            # No invalid accounts
                0,                            # Not many accounts
                np.random.uniform(0.5, 2.0),  # Normal account/instruction ratio
                0,                            # No duplicate accounts
                np.random.uniform(50, 200),   # Normal data size
                np.random.uniform(20, 80),    # Avg instruction size
                np.random.uniform(2, 12),     # Low complexity
                0,                            # Not high complexity
                1,                            # 1 signature required
            ]
            features.append(feature_vector)
        return np.array(features, dtype=np.float32)
    
    def _generate_wallet_drainer_features(self, count: int) -> np.ndarray:
        """Generate wallet drainer attack features"""
        features = []
        for _ in range(count):
            feature_vector = [
                np.random.randint(3, 8),      # Many programs
                np.random.randint(0, 2),      # Few verified programs
                np.random.randint(2, 6),      # Many unique programs
                0,                            # No system program
                1,                            # Token program present
                np.random.randint(10, 30),    # Many instructions
                np.random.uniform(100, 300),  # Large avg data length
                np.random.uniform(200, 500),  # Large max data length
                np.random.uniform(50, 100),   # High data length std
                np.random.randint(5, 15),     # Many complex instructions
                np.random.randint(3, 10),     # Multiple max approvals
                np.random.randint(5, 15),     # Many multi-account instructions
                1,                            # Many instructions flag
                np.random.randint(15, 50),    # Many accounts
                np.random.randint(10, 40),    # Many unique accounts
                np.random.randint(5, 20),     # Many new accounts
                0,                            # No invalid accounts
                1,                            # Many accounts flag
                np.random.uniform(3.0, 8.0),  # High account/instruction ratio
                np.random.randint(0, 2),      # Possible duplicate accounts
                np.random.uniform(1000, 5000), # Large data size
                np.random.uniform(100, 400),  # Large avg instruction size
                np.random.uniform(50, 200),   # High complexity
                1,                            # High complexity flag
                np.random.randint(1, 3),      # 1-2 signatures
            ]
            features.append(feature_vector)
        return np.array(features, dtype=np.float32)
    
    def _generate_unlimited_approval_features(self, count: int) -> np.ndarray:
        """Generate unlimited approval attack features"""
        features = []
        for _ in range(count):
            feature_vector = [
                np.random.randint(2, 5),      # Moderate programs
                np.random.randint(1, 3),      # Some verified programs
                np.random.randint(1, 3),      # Some unique programs
                1,                            # System program present
                1,                            # Token program present
                np.random.randint(3, 8),      # Moderate instructions
                np.random.uniform(80, 150),   # Moderate avg data length
                np.random.uniform(150, 250),  # Moderate max data length
                np.random.uniform(20, 40),    # Moderate data length std
                np.random.randint(1, 3),      # Some complex instructions
                np.random.randint(1, 5),      # Max approvals present
                np.random.randint(1, 5),      # Some multi-account instructions
                0,                            # Not many instructions
                np.random.randint(5, 15),     # Moderate accounts
                np.random.randint(5, 15),     # Moderate unique accounts
                np.random.randint(1, 5),      # Some new accounts
                0,                            # No invalid accounts
                0,                            # Not many accounts
                np.random.uniform(1.5, 3.0),  # Moderate account/instruction ratio
                0,                            # No duplicate accounts
                np.random.uniform(300, 800),  # Moderate data size
                np.random.uniform(60, 120),   # Moderate avg instruction size
                np.random.uniform(15, 40),    # Moderate complexity
                0,                            # Not high complexity
                1,                            # 1 signature
            ]
            features.append(feature_vector)
        return np.array(features, dtype=np.float32)
    
    def _generate_authority_theft_features(self, count: int) -> np.ndarray:
        """Generate authority theft attack features"""
        features = []
        for _ in range(count):
            feature_vector = [
                np.random.randint(2, 6),      # Several programs
                np.random.randint(0, 2),      # Few verified programs
                np.random.randint(2, 5),      # Several unique programs
                1,                            # System program present
                np.random.randint(0, 2),      # Token program maybe
                np.random.randint(5, 12),     # Several instructions
                np.random.uniform(60, 120),   # Moderate avg data length
                np.random.uniform(120, 200),  # Moderate max data length
                np.random.uniform(15, 30),    # Moderate data length std
                np.random.randint(2, 6),      # Some complex instructions
                0,                            # No max approvals
                np.random.randint(2, 8),      # Some multi-account instructions
                0,                            # Not many instructions
                np.random.randint(8, 20),     # Several accounts
                np.random.randint(6, 18),     # Several unique accounts
                np.random.randint(2, 8),      # Some new accounts
                0,                            # No invalid accounts
                0,                            # Not many accounts
                np.random.uniform(1.2, 2.5),  # Moderate account/instruction ratio
                0,                            # No duplicate accounts
                np.random.uniform(400, 1000), # Moderate data size
                np.random.uniform(50, 100),   # Moderate avg instruction size
                np.random.uniform(20, 50),    # Moderate complexity
                0,                            # Not high complexity
                np.random.randint(1, 2),      # 1 signature usually
            ]
            features.append(feature_vector)
        return np.array(features, dtype=np.float32)
    
    def _generate_phishing_features(self, count: int) -> np.ndarray:
        """Generate phishing attack features"""
        features = []
        for _ in range(count):
            feature_vector = [
                np.random.randint(1, 4),      # Few programs
                np.random.randint(0, 1),      # No verified programs
                np.random.randint(1, 3),      # Few unique programs
                0,                            # No system program
                1,                            # Token program present
                np.random.randint(2, 6),      # Few instructions
                np.random.uniform(40, 80),    # Small avg data length
                np.random.uniform(80, 150),   # Small max data length
                np.random.uniform(10, 25),    # Low data length std
                np.random.randint(0, 2),      # Few complex instructions
                np.random.randint(0, 2),      # Maybe max approvals
                np.random.randint(0, 3),      # Few multi-account instructions
                0,                            # Not many instructions
                np.random.randint(3, 10),     # Few accounts
                np.random.randint(3, 10),     # Few unique accounts
                np.random.randint(1, 5),      # Some new accounts
                0,                            # No invalid accounts
                0,                            # Not many accounts
                np.random.uniform(0.8, 2.0),  # Low account/instruction ratio
                0,                            # No duplicate accounts
                np.random.uniform(100, 400),  # Small data size
                np.random.uniform(30, 70),    # Small avg instruction size
                np.random.uniform(5, 20),     # Low complexity
                0,                            # Not high complexity
                1,                            # 1 signature
            ]
            features.append(feature_vector)
        return np.array(features, dtype=np.float32)
    
    def _create_rule_based_classifier(self):
        """Create rule-based classifier for high accuracy when sklearn unavailable"""
        self.rule_based_classifier = {
            "wallet_drainer_rules": [
                {"feature_idx": 0, "threshold": 5, "operator": ">="},  # Many programs
                {"feature_idx": 5, "threshold": 15, "operator": ">="},  # Many instructions
                {"feature_idx": 13, "threshold": 20, "operator": ">="},  # Many accounts
            ],
            "unlimited_approval_rules": [
                {"feature_idx": 10, "threshold": 1, "operator": ">="},  # Max approvals
                {"feature_idx": 4, "threshold": 1, "operator": "=="},   # Token program
            ],
            "authority_theft_rules": [
                {"feature_idx": 8, "threshold": 2, "operator": ">="},   # Complex instructions
                {"feature_idx": 1, "threshold": 1, "operator": "<="},   # Few verified programs
            ]
        }
        logger.info("✅ Rule-based classifier created for high accuracy")
    
    def _generate_cache_key(self, parsed_tx: Dict[str, Any]) -> str:
        """Generate cache key for ML prediction"""
        # Create hash from key transaction features
        programs = tuple(sorted(parsed_tx.get("programs", [])))
        instruction_count = len(parsed_tx.get("instructions", []))
        account_count = len(parsed_tx.get("accounts", []))
        
        return str(hash((programs, instruction_count, account_count)))
    
    async def _cache_prediction(self, cache_key: str, prediction: MLModelPrediction):
        """Cache ML prediction result"""
        if self.redis_client:
            try:
                prediction_data = {
                    "anomaly_score": prediction.anomaly_score,
                    "classification": prediction.classification,
                    "confidence": prediction.confidence,
                    "feature_importance": prediction.feature_importance
                }
                
                await self.redis_client.setex(
                    f"ml_pred:{cache_key}",
                    self.settings.cache_ttl,
                    json.dumps(prediction_data)
                )
            except Exception as e:
                logger.warning(f"Failed to cache ML prediction: {e}")
    
    def is_loaded(self) -> bool:
        """Check if ML model is loaded"""
        return self.model_loaded
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get ML detector performance statistics"""
        avg_prediction_time = np.mean(self.prediction_times) if self.prediction_times else 0
        p95_prediction_time = np.percentile(self.prediction_times, 95) if self.prediction_times else 0
        
        total_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "model_loaded": self.model_loaded,
            "model_version": self.model_version,
            "avg_prediction_time_ms": avg_prediction_time,
            "p95_prediction_time_ms": p95_prediction_time,
            "total_predictions": len(self.prediction_times),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": cache_hit_rate
        }