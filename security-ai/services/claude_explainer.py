"""
High-performance AI explainer service using Google Gemini
Optimized for <1 second explanation generation
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List

import redis.asyncio as redis
from loguru import logger
import google.generativeai as genai

from core.config import get_settings
from models.schemas import SecurityChatMessage


class ClaudeExplainer:
    """High-performance AI explainer with caching and fallbacks using Google Gemini"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self.gemini_model: Optional[genai.GenerativeModel] = None
        
        # Performance tracking
        self.explanation_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Conversation context tracking
        self.conversation_contexts: Dict[str, List[Dict[str, Any]]] = {}
        self.context_max_length = 10  # Maximum messages to keep in context
        
        # Fallback explanations for common scenarios
        self.fallback_explanations = {
            "SAFE": {
                "explanation": "This transaction appears safe. All programs are verified and no suspicious patterns detected.",
                "recommendation": "You can proceed with this transaction with confidence."
            },
            "CAUTION": {
                "explanation": "This transaction has some risk factors that require attention. Review the details carefully.",
                "recommendation": "Proceed with caution and verify all transaction details before signing."
            },
            "DANGER": {
                "explanation": "This transaction contains high-risk patterns that could result in loss of funds.",
                "recommendation": "DO NOT SIGN this transaction. It appears to be malicious or highly suspicious."
            }
        }
        
        # Prompt templates for different query types
        self.prompt_templates = {
            "transaction_analysis": """You are SecurityGuard AI, an expert blockchain security analyst. Analyze this Solana transaction security report and provide a clear, actionable explanation.

Analysis Results:
Risk Level: {risk_level}
Risk Score: {risk_score}/100
Details: {details}

Provide a response with:
1. A clear explanation of what was found (2-3 sentences)
2. Specific actionable recommendations

Keep the language accessible to both technical and non-technical users. Focus on actionable insights.""",

            "general_security": """You are SecurityGuard AI, a Web3 security expert. Answer this security question clearly and helpfully.

User Question: {message}
Context: {context}

Provide practical, actionable security advice. Keep explanations clear and include specific steps users can take to stay safe.""",

            "educational_content": """You are SecurityGuard AI, a Web3 security educator. Explain this security concept in an educational way.

Topic: {message}
Context: {context}

Provide:
1. Clear explanation of the concept
2. Why it matters for security
3. Practical examples
4. How users can protect themselves

Make it educational but not overwhelming.""",

            "threat_explanation": """You are SecurityGuard AI, a threat intelligence expert. Explain this security threat clearly.

Threat/Question: {message}
Analysis Context: {context}

Explain:
1. What this threat is
2. How it works
3. How to recognize it
4. How to protect against it

Be specific and actionable."""
        }
    
    async def initialize(self):
        """Initialize Redis connection and Anthropic client"""
        # Initialize Redis
        try:
            self.redis_client = redis.from_url(
                self.settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            await self.redis_client.ping()
            logger.info("✅ Redis connected for Claude explainer")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}")
            self.redis_client = None
        
        # Initialize Google Gemini
        if self.settings.gemini_api_key:
            try:
                genai.configure(api_key=self.settings.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✅ Google Gemini initialized")
            except Exception as e:
                logger.warning(f"⚠️ Gemini initialization failed: {e}")
                self.gemini_model = None
        else:
            logger.warning("⚠️ No Gemini API key provided, using fallback responses")
    
    async def generate_explanation(
        self, 
        analysis_results: Dict[str, Any], 
        user_wallet: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate human-readable explanation of security analysis
        Target: <1 second generation time with caching
        """
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_explanation_cache_key(analysis_results)
            
            # Check cache first
            if self.redis_client:
                cached_result = await self.redis_client.get(f"explanation:{cache_key}")
                if cached_result:
                    self.cache_hits += 1
                    explanation_data = json.loads(cached_result)
                    cache_time = (time.time() - start_time) * 1000
                    logger.debug(f"⚡ Explanation cache hit in {cache_time:.1f}ms")
                    return explanation_data
            
            self.cache_misses += 1
            
            # Generate explanation with timeout
            try:
                explanation = await asyncio.wait_for(
                    self._generate_explanation_async(analysis_results, user_wallet),
                    timeout=0.8  # 800ms timeout
                )
            except asyncio.TimeoutError:
                logger.warning("⚠️ Explanation generation timeout, using fallback")
                explanation = self._get_fallback_explanation(analysis_results)
            
            # Cache the result
            await self._cache_explanation(cache_key, explanation)
            
            generation_time = (time.time() - start_time) * 1000
            self.explanation_times.append(generation_time)
            
            logger.debug(f"⚡ Explanation generated in {generation_time:.1f}ms")
            
            return explanation
            
        except Exception as e:
            logger.error(f"❌ Explanation generation failed: {e}")
            return self._get_fallback_explanation(analysis_results)
    
    async def process_security_query(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: List[SecurityChatMessage] = None
    ) -> Dict[str, Any]:
        """
        Process natural language security query
        Target: <3 second response time
        """
        start_time = time.time()
        
        try:
            # Generate cache key for query
            cache_key = self._generate_query_cache_key(message, context)
            
            # Check cache first
            if self.redis_client:
                cached_result = await self.redis_client.get(f"query:{cache_key}")
                if cached_result:
                    query_data = json.loads(cached_result)
                    cache_time = (time.time() - start_time) * 1000
                    logger.debug(f"⚡ Query cache hit in {cache_time:.1f}ms")
                    return query_data
            
            # Process query with timeout
            try:
                response = await asyncio.wait_for(
                    self._process_query_async(message, context, conversation_history),
                    timeout=2.5  # 2.5s timeout
                )
            except asyncio.TimeoutError:
                logger.warning("⚠️ Query processing timeout, using fallback")
                response = self._get_fallback_query_response(message)
            
            # Cache the response
            await self._cache_query_response(cache_key, response)
            
            query_time = (time.time() - start_time) * 1000
            logger.debug(f"⚡ Query processed in {query_time:.1f}ms")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Query processing failed: {e}")
            return self._get_fallback_query_response(message)
    
    async def _generate_explanation_async(
        self, 
        analysis_results: Dict[str, Any], 
        user_wallet: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate explanation asynchronously using Gemini API"""
        
        # If Gemini API is available, use it for enhanced explanations
        if self.gemini_model:
            try:
                return await self._generate_gemini_explanation(analysis_results, user_wallet)
            except Exception as e:
                logger.warning(f"Gemini API failed, using fallback: {e}")
        
        # Fallback to rule-based explanation
        return self._generate_fallback_explanation(analysis_results)
    
    async def _generate_gemini_explanation(
        self, 
        analysis_results: Dict[str, Any], 
        user_wallet: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate explanation using Google Gemini API"""
        
        risk_level = analysis_results.get("risk_level", "UNKNOWN")
        risk_score = analysis_results.get("risk_score", 0)
        details = analysis_results.get("details", {})
        
        # Format details for Gemini
        details_summary = self._format_analysis_details(details)
        
        prompt = self.prompt_templates["transaction_analysis"].format(
            risk_level=risk_level,
            risk_score=risk_score,
            details=details_summary
        )
        
        try:
            # Generate content with Gemini
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.3,
                )
            )
            
            # Parse Gemini's response
            content = response.text
            return self._parse_ai_explanation(content)
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _generate_fallback_explanation(self, analysis_results: Dict[str, Any]) -> Dict[str, str]:
        """Generate rule-based explanation as fallback"""
        
        # Extract key information
        risk_level = analysis_results.get("risk_level", "UNKNOWN")
        risk_score = analysis_results.get("risk_score", 0)
        details = analysis_results.get("details", {})
        
        # Build explanation based on analysis
        explanation_parts = []
        recommendation_parts = []
        
        # Risk level assessment
        if risk_level == "DANGER":
            explanation_parts.append(f"🚨 HIGH RISK DETECTED (Score: {risk_score}/100)")
            recommendation_parts.append("DO NOT SIGN this transaction")
        elif risk_level == "CAUTION":
            explanation_parts.append(f"⚠️ MODERATE RISK (Score: {risk_score}/100)")
            recommendation_parts.append("Proceed with caution")
        else:
            explanation_parts.append(f"✅ LOW RISK (Score: {risk_score}/100)")
            recommendation_parts.append("Transaction appears safe to proceed")
        
        # Program analysis
        program_analysis = details.get("program_analysis", {})
        if program_analysis.get("blacklisted_programs", 0) > 0:
            explanation_parts.append("Contains blacklisted malicious programs")
            recommendation_parts.append("This transaction interacts with known malicious contracts")
        elif program_analysis.get("unknown_programs", 0) > 0:
            explanation_parts.append(f"Interacts with {program_analysis['unknown_programs']} unverified programs")
            recommendation_parts.append("Verify the legitimacy of unknown programs before proceeding")
        
        # Pattern matches
        pattern_matches = details.get("pattern_matches", [])
        if pattern_matches:
            explanation_parts.append(f"Matches {len(pattern_matches)} known exploit patterns")
            recommendation_parts.append("Review the specific patterns detected")
        
        # ML analysis
        ml_analysis = details.get("ml_analysis", {})
        anomaly_score = ml_analysis.get("anomaly_score", 0)
        if anomaly_score > 0.7:
            explanation_parts.append("AI detected highly unusual transaction patterns")
            recommendation_parts.append("The transaction structure is atypical and potentially suspicious")
        elif anomaly_score > 0.4:
            explanation_parts.append("AI detected some unusual patterns")
            recommendation_parts.append("Review transaction details for any unexpected behavior")
        
        # Account analysis
        account_analysis = details.get("account_analysis", {})
        if account_analysis.get("unlimited_approvals", False):
            explanation_parts.append("Contains unlimited token spending approvals")
            recommendation_parts.append("Limit token approvals to specific amounts when possible")
        
        red_flags = account_analysis.get("red_flags", [])
        if red_flags:
            explanation_parts.append(f"Detected {len(red_flags)} account-related red flags")
            recommendation_parts.append("Review account permissions and authority changes")
        
        # Combine explanations
        explanation = ". ".join(explanation_parts) if explanation_parts else "Transaction analysis completed."
        recommendation = ". ".join(recommendation_parts) if recommendation_parts else "Review transaction details before proceeding."
        
        return {
            "explanation": explanation,
            "recommendation": recommendation
        }
    
    async def _process_query_async(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: List[SecurityChatMessage] = None
    ) -> Dict[str, Any]:
        """Process security query asynchronously using Gemini API"""
        
        # If Gemini API is available, use it for enhanced responses
        if self.gemini_model:
            try:
                return await self._process_gemini_query(message, context, conversation_history)
            except Exception as e:
                logger.warning(f"Gemini API failed for query, using fallback: {e}")
        
        # Fallback to rule-based responses
        return self._process_fallback_query(message, context)
    
    async def _process_gemini_query(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: List[SecurityChatMessage] = None
    ) -> Dict[str, Any]:
        """Process query using Gemini API with intent classification"""
        
        # Classify intent and select appropriate template
        intent = self._classify_intent(message)
        template = self.prompt_templates.get(intent, self.prompt_templates["general_security"])
        
        # Format context for Gemini
        context_str = json.dumps(context, indent=2) if context else "No additional context"
        
        prompt = template.format(
            message=message,
            context=context_str
        )
        
        # Add conversation history if available
        if conversation_history:
            history_context = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-5:]:
                history_context += f"{msg.role}: {msg.content}\n"
            prompt = history_context + "\n" + prompt
        
        try:
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=800,
                    temperature=0.4,
                )
            )
            
            content = response.text
            return self._parse_ai_query_response(content, intent)
            
        except Exception as e:
            logger.error(f"Gemini API error in query processing: {e}")
            raise
    
    def _process_fallback_query(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process query using rule-based fallback"""
        
        # Simple intent classification
        message_lower = message.lower()
        
        # Transaction analysis queries
        if any(word in message_lower for word in ["scan", "analyze", "check", "transaction"]):
            return {
                "message": "I can help you analyze Solana transactions for security threats. Please provide a transaction signature or paste the transaction data to get started.",
                "recommendations": [
                    "Always verify transaction details before signing",
                    "Check for unlimited token approvals",
                    "Verify program legitimacy"
                ],
                "confidence": 0.9
            }
        
        # Security best practices
        elif any(word in message_lower for word in ["safe", "secure", "protect", "best practice"]):
            return {
                "message": "Here are key Web3 security practices: 1) Never share your private keys, 2) Verify transaction details before signing, 3) Use hardware wallets for large amounts, 4) Check program legitimacy, 5) Be cautious with unlimited approvals.",
                "recommendations": [
                    "Use hardware wallets for significant amounts",
                    "Verify all transaction details",
                    "Keep private keys secure and never share them",
                    "Use reputable dApps and programs"
                ],
                "confidence": 0.95
            }
        
        # Threat explanation
        elif any(word in message_lower for word in ["threat", "attack", "exploit", "malicious"]):
            return {
                "message": "Common Web3 threats include wallet drainers, unlimited token approvals, authority theft, rug pulls, and phishing contracts. I can help identify these patterns in transactions.",
                "recommendations": [
                    "Learn to recognize common attack patterns",
                    "Use transaction analysis tools",
                    "Stay updated on latest threats",
                    "Verify contract legitimacy"
                ],
                "confidence": 0.9
            }
        
        # General help
        else:
            return {
                "message": "I'm SecurityGuard AI, your Web3 security assistant. I can analyze Solana transactions, explain security threats, and provide safety recommendations. How can I help protect you today?",
                "recommendations": [
                    "Ask about transaction analysis",
                    "Learn about security best practices",
                    "Get threat explanations",
                    "Understand risk assessments"
                ],
                "confidence": 0.8
            }
    
    def _get_fallback_explanation(self, analysis_results: Dict[str, Any]) -> Dict[str, str]:
        """Get fallback explanation when Claude API fails"""
        risk_level = analysis_results.get("risk_level", "CAUTION")
        return self.fallback_explanations.get(risk_level, self.fallback_explanations["CAUTION"])
    
    def _get_fallback_query_response(self, message: str) -> Dict[str, Any]:
        """Get fallback response for queries"""
        return {
            "message": "I'm here to help with Web3 security. I can analyze transactions, explain threats, and provide safety recommendations. Please try rephrasing your question or ask about specific security topics.",
            "recommendations": [
                "Ask about transaction analysis",
                "Learn about security best practices",
                "Get threat explanations"
            ],
            "confidence": 0.6
        }
    
    def _generate_explanation_cache_key(self, analysis_results: Dict[str, Any]) -> str:
        """Generate cache key for explanation"""
        risk_level = analysis_results.get("risk_level", "")
        risk_score = analysis_results.get("risk_score", 0)
        
        # Create hash from key analysis components
        details = analysis_results.get("details", {})
        program_count = details.get("program_analysis", {}).get("total_programs", 0)
        pattern_count = len(details.get("pattern_matches", []))
        
        return str(hash((risk_level, risk_score, program_count, pattern_count)))
    
    def _generate_query_cache_key(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for query"""
        # Normalize message for caching
        normalized_message = message.lower().strip()[:100]  # First 100 chars
        context_hash = str(hash(str(context))) if context else "no_context"
        return str(hash((normalized_message, context_hash)))
    
    async def _cache_explanation(self, cache_key: str, explanation: Dict[str, str]):
        """Cache explanation result"""
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    f"explanation:{cache_key}",
                    self.settings.cache_ttl,
                    json.dumps(explanation)
                )
            except Exception as e:
                logger.warning(f"Failed to cache explanation: {e}")
    
    async def _cache_query_response(self, cache_key: str, response: Dict[str, Any]):
        """Cache query response"""
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    f"query:{cache_key}",
                    self.settings.cache_ttl,
                    json.dumps(response)
                )
            except Exception as e:
                logger.warning(f"Failed to cache query response: {e}")
    
    def _classify_intent(self, message: str) -> str:
        """Classify user intent for appropriate prompt template selection"""
        message_lower = message.lower()
        
        # Transaction analysis queries
        if any(word in message_lower for word in ["scan", "analyze", "check", "transaction", "signature"]):
            return "transaction_analysis"
        
        # Threat explanation queries
        elif any(word in message_lower for word in ["threat", "attack", "exploit", "malicious", "scam", "phishing"]):
            return "threat_explanation"
        
        # Educational queries
        elif any(word in message_lower for word in ["learn", "explain", "what is", "how does", "tutorial"]):
            return "educational_content"
        
        # Default to general security
        else:
            return "general_security"
    
    def _build_conversation_context(self, conversation_history: List[SecurityChatMessage]) -> List[Dict[str, str]]:
        """Build conversation context for Claude API"""
        if not conversation_history:
            return []
        
        # Limit context to recent messages to avoid token limits
        recent_messages = conversation_history[-self.context_max_length:]
        
        context_messages = []
        for msg in recent_messages:
            context_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return context_messages
    
    def _format_analysis_details(self, details: Dict[str, Any]) -> str:
        """Format analysis details for Claude prompt"""
        formatted_parts = []
        
        # Program analysis
        program_analysis = details.get("program_analysis", {})
        if program_analysis:
            formatted_parts.append(f"Programs: {program_analysis}")
        
        # Pattern matches
        pattern_matches = details.get("pattern_matches", [])
        if pattern_matches:
            formatted_parts.append(f"Pattern Matches: {len(pattern_matches)} patterns detected")
        
        # ML analysis
        ml_analysis = details.get("ml_analysis", {})
        if ml_analysis:
            anomaly_score = ml_analysis.get("anomaly_score", 0)
            formatted_parts.append(f"ML Analysis: Anomaly score {anomaly_score:.2f}")
        
        # Account analysis
        account_analysis = details.get("account_analysis", {})
        if account_analysis:
            formatted_parts.append(f"Account Analysis: {account_analysis}")
        
        return "\n".join(formatted_parts) if formatted_parts else "No detailed analysis available"
    
    def _parse_ai_explanation(self, content: str) -> Dict[str, str]:
        """Parse AI explanation response"""
        try:
            # Try to extract structured explanation and recommendation
            lines = content.strip().split('\n')
            
            explanation = ""
            recommendation = ""
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for section headers
                if any(header in line.lower() for header in ["explanation:", "analysis:", "findings:"]):
                    current_section = "explanation"
                    # Extract content after the header
                    if ":" in line:
                        explanation += line.split(":", 1)[1].strip() + " "
                elif any(header in line.lower() for header in ["recommendation:", "advice:", "action:"]):
                    current_section = "recommendation"
                    # Extract content after the header
                    if ":" in line:
                        recommendation += line.split(":", 1)[1].strip() + " "
                else:
                    # Add to current section
                    if current_section == "explanation":
                        explanation += line + " "
                    elif current_section == "recommendation":
                        recommendation += line + " "
                    elif not current_section:
                        # If no section identified yet, assume it's explanation
                        explanation += line + " "
            
            # Clean up
            explanation = explanation.strip()
            recommendation = recommendation.strip()
            
            # If we couldn't parse properly, use the full content as explanation
            if not explanation:
                explanation = content.strip()
            
            if not recommendation:
                recommendation = "Review the analysis carefully and proceed with appropriate caution."
            
            return {
                "explanation": explanation,
                "recommendation": recommendation
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse Claude explanation: {e}")
            return {
                "explanation": content.strip(),
                "recommendation": "Review the analysis carefully and proceed with appropriate caution."
            }
    
    def _parse_ai_query_response(self, content: str, intent: str) -> Dict[str, Any]:
        """Parse AI query response"""
        try:
            # Extract recommendations if present
            recommendations = []
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                # Look for numbered lists or bullet points
                if line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•')):
                    # Clean up the recommendation
                    rec = line.lstrip('12345.-• ').strip()
                    if rec:
                        recommendations.append(rec)
            
            # If no structured recommendations found, create generic ones based on intent
            if not recommendations:
                if intent == "transaction_analysis":
                    recommendations = [
                        "Verify transaction details before signing",
                        "Check program legitimacy",
                        "Review token approvals carefully"
                    ]
                elif intent == "threat_explanation":
                    recommendations = [
                        "Stay informed about latest threats",
                        "Use security analysis tools",
                        "Verify contract authenticity"
                    ]
                else:
                    recommendations = [
                        "Follow security best practices",
                        "Stay vigilant with transactions",
                        "Use trusted security tools"
                    ]
            
            return {
                "message": content.strip(),
                "recommendations": recommendations[:5],  # Limit to 5 recommendations
                "confidence": 0.9  # High confidence for Gemini responses
            }
            
        except Exception as e:
            logger.warning(f"Failed to parse Gemini query response: {e}")
            return {
                "message": content.strip(),
                "recommendations": ["Follow security best practices"],
                "confidence": 0.7
            }
    
    def update_conversation_context(self, user_id: str, message: SecurityChatMessage):
        """Update conversation context for multi-turn conversations"""
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = []
        
        self.conversation_contexts[user_id].append({
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat()
        })
        
        # Limit context length
        if len(self.conversation_contexts[user_id]) > self.context_max_length:
            self.conversation_contexts[user_id] = self.conversation_contexts[user_id][-self.context_max_length:]
    
    def get_conversation_context(self, user_id: str) -> List[Dict[str, Any]]:
        """Get conversation context for a user"""
        return self.conversation_contexts.get(user_id, [])
    
    def clear_conversation_context(self, user_id: str):
        """Clear conversation context for a user"""
        if user_id in self.conversation_contexts:
            del self.conversation_contexts[user_id]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        avg_explanation_time = sum(self.explanation_times) / len(self.explanation_times) if self.explanation_times else 0
        total_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "avg_explanation_time_ms": avg_explanation_time,
            "total_explanations": len(self.explanation_times),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "active_conversations": len(self.conversation_contexts),
            "gemini_available": self.gemini_model is not None
        }