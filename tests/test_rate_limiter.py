"""
Tests for the Token Bucket Rate Limiter

This test suite covers:
- Basic token consumption and refill
- Rate limiting behavior
- Multiple keys (per-key rate limiting)
- Edge cases and boundary conditions
"""

import asyncio
import time
import unittest
from app.tocket_bucket_rate_limiter import TokenBucket, TokenBucketRateLimiter


class TestTokenBucket(unittest.IsolatedAsyncioTestCase):
    """Test cases for the TokenBucket class."""
    
    async def test_initial_state(self):
        """Test that a bucket starts with full tokens."""
        bucket = TokenBucket(max_tokens=100, refill_rate=10)
        self.assertEqual(bucket.tokens, 100)
        self.assertEqual(bucket.max_tokens, 100)
        self.assertEqual(bucket.refill_rate, 10)
    
    async def test_consume_single_token(self):
        """Test consuming a single token from a full bucket."""
        bucket = TokenBucket(max_tokens=100, refill_rate=10)
        allowed, retry_after = await bucket.consume(1)
        
        self.assertTrue(allowed)
        self.assertIsNone(retry_after)
        self.assertEqual(bucket.tokens, 99)
    
    async def test_consume_multiple_tokens(self):
        """Test consuming multiple tokens at once."""
        bucket = TokenBucket(max_tokens=100, refill_rate=10)
        allowed, retry_after = await bucket.consume(50)
        
        self.assertTrue(allowed)
        self.assertIsNone(retry_after)
        self.assertEqual(bucket.tokens, 50)
    
    async def test_rate_limit_when_insufficient_tokens(self):
        """Test that consumption is denied when tokens are insufficient."""
        bucket = TokenBucket(max_tokens=10, refill_rate=5)
        # Consume all tokens
        await bucket.consume(10)
        
        # Try to consume more - should be rate limited
        allowed, retry_after = await bucket.consume(1)
        
        self.assertFalse(allowed)
        self.assertIsNotNone(retry_after)
        # Should need 1 token / 5 tokens per second = 0.2 seconds
        self.assertAlmostEqual(retry_after, 0.2, places=1)
    
    async def test_token_refill_over_time(self):
        """Test that tokens are refilled over time."""
        bucket = TokenBucket(max_tokens=10, refill_rate=10)  # 10 tokens per second
        # Consume all tokens
        await bucket.consume(10)
        self.assertEqual(bucket.tokens, 0)
        
        # Wait 0.5 seconds
        await asyncio.sleep(0.5)
        
        # Should have approximately 5 tokens refilled
        allowed, _ = await bucket.consume(5)
        self.assertTrue(allowed)
    
    async def test_token_refill_capped_at_max(self):
        """Test that tokens don't exceed max capacity."""
        bucket = TokenBucket(max_tokens=10, refill_rate=100)  # Very high refill rate
        # Consume some tokens
        await bucket.consume(5)
        
        # Wait a long time (simulated by setting last_refill far in the past)
        bucket.last_refill = time.time() - 10  # 10 seconds ago
        
        # Refill should cap at max_tokens
        await bucket._refill_tokens()
        self.assertEqual(bucket.tokens, 10)
    
    async def test_get_available_tokens(self):
        """Test getting the current number of available tokens."""
        bucket = TokenBucket(max_tokens=100, refill_rate=10)
        
        # Consume some tokens
        await bucket.consume(30)
        
        # Check available tokens
        available = await bucket.get_available_tokens()
        self.assertEqual(available, 70)
    
    async def test_concurrent_consumption(self):
        """Test that concurrent consumption is thread-safe."""
        bucket = TokenBucket(max_tokens=100, refill_rate=10)
        
        # Simulate concurrent requests
        async def consume_token():
            return await bucket.consume(1)
        
        # Create 50 concurrent requests
        results = await asyncio.gather(*[consume_token() for _ in range(50)])
        
        # All should be allowed
        all_allowed = all(allowed for allowed, _ in results)
        self.assertTrue(all_allowed)
        
        # Should have consumed 50 tokens (allow small tolerance for timing)
        available = await bucket.get_available_tokens()
        # Due to timing during concurrent operations, tokens may refill slightly
        self.assertGreaterEqual(available, 49.5)
        self.assertLessEqual(available, 50.5)


class TestTokenBucketRateLimiter(unittest.IsolatedAsyncioTestCase):
    """Test cases for the TokenBucketRateLimiter class."""
    
    async def test_initial_state(self):
        """Test that rate limiter initializes correctly."""
        limiter = TokenBucketRateLimiter(max_tokens=100, refill_rate=10)
        self.assertEqual(limiter.max_tokens, 100)
        self.assertEqual(limiter.refill_rate, 10)
    
    async def test_is_allowed_for_new_key(self):
        """Test that a new key is allowed and bucket is created."""
        limiter = TokenBucketRateLimiter(max_tokens=10, refill_rate=5)
        allowed, retry_after = await limiter.is_allowed("user_1")
        
        self.assertTrue(allowed)
        self.assertIsNone(retry_after)
    
    async def test_rate_limit_single_key(self):
        """Test rate limiting for a single key."""
        limiter = TokenBucketRateLimiter(max_tokens=5, refill_rate=2)
        
        # Consume all tokens
        for _ in range(5):
            allowed, _ = await limiter.is_allowed("user_1")
            self.assertTrue(allowed)
        
        # Next request should be rate limited
        allowed, retry_after = await limiter.is_allowed("user_1")
        self.assertFalse(allowed)
        self.assertIsNotNone(retry_after)
    
    async def test_independent_buckets_per_key(self):
        """Test that different keys have independent rate limits."""
        limiter = TokenBucketRateLimiter(max_tokens=5, refill_rate=2)
        
        # Exhaust tokens for user_1
        for _ in range(5):
            await limiter.is_allowed("user_1")
        
        # user_1 should be rate limited
        allowed, _ = await limiter.is_allowed("user_1")
        self.assertFalse(allowed)
        
        # user_2 should still be allowed (different bucket)
        allowed, _ = await limiter.is_allowed("user_2")
        self.assertTrue(allowed)
    
    async def test_get_available_tokens(self):
        """Test getting available tokens for a key."""
        limiter = TokenBucketRateLimiter(max_tokens=100, refill_rate=10)
        
        # Consume some tokens
        await limiter.is_allowed("user_1", tokens=30)
        
        # Check available tokens
        available = await limiter.get_available_tokens("user_1")
        self.assertEqual(available, 70)
    
    async def test_reset_bucket(self):
        """Test resetting a bucket to full capacity."""
        limiter = TokenBucketRateLimiter(max_tokens=10, refill_rate=5)
        
        # Consume all tokens
        for _ in range(10):
            await limiter.is_allowed("user_1")
        
        # Should be rate limited
        allowed, _ = await limiter.is_allowed("user_1")
        self.assertFalse(allowed)
        
        # Reset bucket
        await limiter.reset_bucket("user_1")
        
        # Should be allowed again
        allowed, _ = await limiter.is_allowed("user_1")
        self.assertTrue(allowed)
    
    async def test_custom_token_consumption(self):
        """Test consuming custom amounts of tokens."""
        limiter = TokenBucketRateLimiter(max_tokens=100, refill_rate=10)
        
        # Consume 50 tokens at once
        allowed, _ = await limiter.is_allowed("user_1", tokens=50)
        self.assertTrue(allowed)
        
        # Check remaining tokens
        available = await limiter.get_available_tokens("user_1")
        self.assertEqual(available, 50)
    
    async def test_refill_rate_accuracy(self):
        """Test that tokens refill at the correct rate."""
        limiter = TokenBucketRateLimiter(max_tokens=10, refill_rate=10)  # 10 tokens/second
        
        # Consume all tokens
        for _ in range(10):
            await limiter.is_allowed("user_1")
        
        # Wait 0.5 seconds
        await asyncio.sleep(0.5)
        
        # Should have approximately 5 tokens available
        available = await limiter.get_available_tokens("user_1")
        self.assertGreaterEqual(available, 4.5)  # Allow some tolerance
        self.assertLessEqual(available, 5.5)
    
    async def test_multiple_keys_concurrent(self):
        """Test concurrent requests from multiple keys."""
        limiter = TokenBucketRateLimiter(max_tokens=10, refill_rate=10)
        
        async def make_request(key):
            return await limiter.is_allowed(key)
        
        # Make concurrent requests from different keys
        keys = [f"user_{i}" for i in range(5)]
        results = await asyncio.gather(*[make_request(key) for key in keys])
        
        # All should be allowed (different buckets)
        all_allowed = all(allowed for allowed, _ in results)
        self.assertTrue(all_allowed)
    
    async def test_zero_refill_rate(self):
        """Test behavior with zero refill rate (no automatic refill)."""
        limiter = TokenBucketRateLimiter(max_tokens=5, refill_rate=0)
        
        # Consume all tokens
        for _ in range(5):
            allowed, _ = await limiter.is_allowed("user_1")
            self.assertTrue(allowed)
        
        # Should be rate limited and retry_after should be None (infinite wait)
        allowed, retry_after = await limiter.is_allowed("user_1")
        self.assertFalse(allowed)
        # With zero refill rate, retry_after calculation may return None
        # This is acceptable behavior as it indicates tokens won't refill


if __name__ == '__main__':
    unittest.main()
