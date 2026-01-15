"""
Token Bucket Rate Limiter Implementation

This module provides a token bucket algorithm-based rate limiter for controlling
the rate of requests. The token bucket algorithm allows bursts of traffic up to
the bucket capacity while maintaining a steady average rate.

Algorithm Overview:
- Each bucket has a maximum capacity (max_tokens)
- Tokens are added to the bucket at a constant rate (refill_rate per second)
- When a request arrives, it consumes tokens (default: 1 token per request)
- If sufficient tokens are available, the request is allowed
- If insufficient tokens are available, the request is rate limited

This implementation is designed to be thread-safe and suitable for async operations.
"""

import asyncio
import time
from typing import Dict, Optional, Tuple
from collections import defaultdict


class TokenBucket:
    """
    Represents a single token bucket for rate limiting.
    
    Each bucket maintains:
    - tokens: Current number of tokens available
    - last_refill: Timestamp of the last token refill
    - max_tokens: Maximum capacity of the bucket
    - refill_rate: Number of tokens added per second
    """
    
    def __init__(self, max_tokens: float, refill_rate: float):
        """
        Initialize a token bucket.
        
        Args:
            max_tokens: Maximum number of tokens the bucket can hold
            refill_rate: Number of tokens to add per second
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = max_tokens  # Start with a full bucket
        self.last_refill = time.time()
        self._lock = asyncio.Lock()  # Lock for thread-safe operations
    
    async def _refill_tokens(self) -> None:
        """
        Refill tokens based on elapsed time since last refill.
        
        This method calculates how many tokens should be added based on
        the time elapsed and the refill rate, then updates the bucket.
        
        Note: elapsed time is in seconds (as a float), which means we can
        add fractional tokens (e.g., 0.5 tokens). This is intentional and
        provides smooth, continuous refill rather than discrete jumps.
        """
        current_time = time.time()
        elapsed = current_time - self.last_refill  # Float in seconds
        
        # Calculate tokens to add based on elapsed time
        # This can result in fractional tokens (e.g., 0.5 tokens), which is correct
        tokens_to_add = elapsed * self.refill_rate
        
        # Add tokens, but don't exceed max capacity
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = current_time
    
    async def consume(self, tokens: float = 1.0) -> Tuple[bool, Optional[float]]:
        """
        Attempt to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume (default: 1.0)
            
        Returns:
            Tuple of (is_allowed, retry_after):
            - is_allowed: True if tokens were consumed, False if rate limited
            - retry_after: Seconds until enough tokens will be available (None if allowed)
        """
        async with self._lock:
            # Refill tokens based on elapsed time
            await self._refill_tokens()
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                # Consume tokens and allow the request
                self.tokens -= tokens
                return True, None
            else:
                # Calculate when enough tokens will be available
                tokens_needed = tokens - self.tokens
                retry_after = tokens_needed / self.refill_rate if self.refill_rate > 0 else None
                return False, retry_after
    
    async def get_available_tokens(self) -> float:
        """
        Get the current number of available tokens (after refill).
        
        Returns:
            Current number of tokens in the bucket
        """
        async with self._lock:
            await self._refill_tokens()
            return self.tokens


class TokenBucketRateLimiter:
    """
    Rate limiter that manages multiple token buckets (one per key).
    
    This class provides a simple interface for rate limiting requests
    based on keys (e.g., IP address, user ID, API key).
    
    Example usage:
        limiter = TokenBucketRateLimiter(max_tokens=100, refill_rate=10)
        allowed, retry_after = await limiter.is_allowed("user_123")
        if allowed:
            # Process request
        else:
            # Rate limited, wait retry_after seconds
    """
    
    def __init__(self, max_tokens: float = 100.0, refill_rate: float = 10.0):
        """
        Initialize the rate limiter.
        
        Args:
            max_tokens: Maximum tokens per bucket (default: 100)
            refill_rate: Tokens added per second (default: 10)
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        # Dictionary to store buckets per key
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()  # Lock for bucket creation
    
    async def _get_bucket(self, key: str) -> TokenBucket:
        """
        Get or create a token bucket for the given key.
        
        Args:
            key: Unique identifier for the rate limit (e.g., IP, user ID)
            
        Returns:
            TokenBucket instance for the key
        """
        # Check if bucket exists (fast path without lock)
        if key in self._buckets:
            return self._buckets[key]
        
        # Create bucket if it doesn't exist (with lock for thread safety)
        async with self._lock:
            # Double-check after acquiring lock (prevent race condition)
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(self.max_tokens, self.refill_rate)
            return self._buckets[key]
    
    async def is_allowed(self, key: str, tokens: float = 1.0) -> Tuple[bool, Optional[float]]:
        """
        Check if a request is allowed for the given key.
        
        Args:
            key: Unique identifier for the rate limit
            tokens: Number of tokens to consume (default: 1.0)
            
        Returns:
            Tuple of (is_allowed, retry_after):
            - is_allowed: True if request is allowed, False if rate limited
            - retry_after: Seconds until request will be allowed (None if allowed)
        """
        bucket = await self._get_bucket(key)
        return await bucket.consume(tokens)
    
    async def get_available_tokens(self, key: str) -> float:
        """
        Get the number of available tokens for a given key.
        
        Args:
            key: Unique identifier for the rate limit
            
        Returns:
            Current number of available tokens
        """
        bucket = await self._get_bucket(key)
        return await bucket.get_available_tokens()
    
    async def reset_bucket(self, key: str) -> None:
        """
        Reset a bucket to full capacity (useful for testing or manual resets).
        
        Args:
            key: Unique identifier for the rate limit
        """
        async with self._lock:
            if key in self._buckets:
                bucket = self._buckets[key]
                async with bucket._lock:
                    bucket.tokens = bucket.max_tokens
                    bucket.last_refill = time.time()
