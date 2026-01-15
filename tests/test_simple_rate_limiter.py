"""
Tests for the Simple Rate Limiters
"""

import time
import unittest
from app.simple_rate_limiter import FixedWindowRateLimiter, SimpleTokenBucketRateLimiter


class TestFixedWindowRateLimiter(unittest.TestCase):
    """Test cases for the FixedWindowRateLimiter class."""
    
    def test_initial_state(self):
        """Test that rate limiter initializes correctly."""
        limiter = FixedWindowRateLimiter(max_requests=100, window_seconds=60)
        self.assertEqual(limiter.max_requests, 100)
        self.assertEqual(limiter.window_seconds, 60)
        self.assertEqual(limiter.count, 0)
    
    def test_allows_requests_within_limit(self):
        """Test that requests are allowed when under the limit."""
        limiter = FixedWindowRateLimiter(max_requests=5, window_seconds=60)
        
        # Make 5 requests - all should be allowed
        for i in range(5):
            allowed, retry_after = limiter.is_allowed()
            self.assertTrue(allowed)
            self.assertIsNone(retry_after)
            self.assertEqual(limiter.count, i + 1)
    
    def test_rate_limits_when_exceeded(self):
        """Test that requests are rate limited when limit is exceeded."""
        limiter = FixedWindowRateLimiter(max_requests=5, window_seconds=60)
        
        # Make 5 requests - all should be allowed
        for _ in range(5):
            limiter.is_allowed()
        
        # 6th request should be rate limited
        allowed, retry_after = limiter.is_allowed()
        self.assertFalse(allowed)
        self.assertIsNotNone(retry_after)
        self.assertGreater(retry_after, 0)
        self.assertLessEqual(retry_after, 60)
    
    def test_starts_at_zero(self):
        """Test that counter starts at 0."""
        limiter = FixedWindowRateLimiter(max_requests=5, window_seconds=60)
        
        # First request should be allowed (starts at 0)
        allowed, _ = limiter.is_allowed()
        self.assertTrue(allowed)
        self.assertEqual(limiter.count, 1)
        
        # Check remaining requests
        remaining = limiter.get_remaining_requests()
        self.assertEqual(remaining, 4)  # 5 max - 1 used = 4 remaining
    
    def test_window_reset(self):
        """Test that counter resets when window expires."""
        limiter = FixedWindowRateLimiter(max_requests=5, window_seconds=1)
        
        # Exhaust limit
        for _ in range(5):
            limiter.is_allowed()
        
        self.assertEqual(limiter.count, 5)
        
        # Should be rate limited
        allowed, _ = limiter.is_allowed()
        self.assertFalse(allowed)
        
        # Wait for window to expire
        import time
        time.sleep(1.1)
        
        # Should be allowed again (new window)
        allowed, _ = limiter.is_allowed()
        self.assertTrue(allowed)
        self.assertEqual(limiter.count, 1)  # Reset to 1 (just incremented)
    
    def test_get_remaining_requests(self):
        """Test getting remaining requests in current window."""
        limiter = FixedWindowRateLimiter(max_requests=10, window_seconds=60)
        
        # Initially should have 10 remaining
        remaining = limiter.get_remaining_requests()
        self.assertEqual(remaining, 10)
        
        # Make 3 requests
        for _ in range(3):
            limiter.is_allowed()
        
        # Should have 7 remaining
        remaining = limiter.get_remaining_requests()
        self.assertEqual(remaining, 7)
    
    def test_window_boundary_behavior(self):
        """Test behavior at window boundaries."""
        limiter = FixedWindowRateLimiter(max_requests=5, window_seconds=1)
        
        # Make requests in first window
        for _ in range(5):
            limiter.is_allowed()
        
        # Should be rate limited
        allowed, _ = limiter.is_allowed()
        self.assertFalse(allowed)
        
        # Wait until next window
        time.sleep(1.1)
        
        # Should be allowed in new window
        allowed, _ = limiter.is_allowed()
        self.assertTrue(allowed)
        
        # Counter should have reset
        remaining = limiter.get_remaining_requests()
        self.assertEqual(remaining, 4)  # 5 max - 1 used in new window
    
    def test_zero_max_requests(self):
        """Test behavior with zero max requests (all requests blocked)."""
        limiter = FixedWindowRateLimiter(max_requests=0, window_seconds=60)
        
        # Should always be rate limited
        allowed, retry_after = limiter.is_allowed()
        self.assertFalse(allowed)
        self.assertIsNotNone(retry_after)
    
    def test_single_request_limit(self):
        """Test with limit of 1 request per window."""
        limiter = FixedWindowRateLimiter(max_requests=1, window_seconds=60)
        
        # First request should be allowed
        allowed, _ = limiter.is_allowed()
        self.assertTrue(allowed)
        self.assertEqual(limiter.count, 1)
        
        # Second request should be rate limited
        allowed, _ = limiter.is_allowed()
        self.assertFalse(allowed)
        self.assertEqual(limiter.count, 1)  # Count didn't increment


class TestSimpleTokenBucketRateLimiter(unittest.TestCase):
    """Test cases for the SimpleTokenBucketRateLimiter class."""
    
    def test_initial_state(self):
        """Test that rate limiter initializes correctly."""
        limiter = SimpleTokenBucketRateLimiter(max_tokens=100, refill_rate=10)
        self.assertEqual(limiter.max_tokens, 100)
        self.assertEqual(limiter.refill_rate, 10)
        self.assertEqual(limiter.tokens, 100)  # Starts full
    
    def test_starts_with_full_capacity(self):
        """Test that bucket starts with full tokens."""
        limiter = SimpleTokenBucketRateLimiter(max_tokens=100, refill_rate=10)
        self.assertEqual(limiter.tokens, 100)
        available = limiter.get_available_tokens()
        self.assertEqual(available, 100)
    
    def test_consume_single_token(self):
        """Test consuming a single token from a full bucket."""
        limiter = SimpleTokenBucketRateLimiter(max_tokens=100, refill_rate=10)
        allowed, retry_after = limiter.is_allowed(1)
        
        self.assertTrue(allowed)
        self.assertIsNone(retry_after)
        self.assertEqual(limiter.tokens, 99)
    
    def test_consume_multiple_tokens(self):
        """Test consuming multiple tokens at once."""
        limiter = SimpleTokenBucketRateLimiter(max_tokens=100, refill_rate=10)
        allowed, retry_after = limiter.is_allowed(50)
        
        self.assertTrue(allowed)
        self.assertIsNone(retry_after)
        self.assertEqual(limiter.tokens, 50)
    
    def test_rate_limit_when_insufficient_tokens(self):
        """Test that consumption is denied when tokens are insufficient."""
        limiter = SimpleTokenBucketRateLimiter(max_tokens=10, refill_rate=5)
        # Consume all tokens
        limiter.is_allowed(10)
        
        # Try to consume more - should be rate limited
        allowed, retry_after = limiter.is_allowed(1)
        
        self.assertFalse(allowed)
        self.assertIsNotNone(retry_after)
        # Should need 1 token / 5 tokens per second = 0.2 seconds
        self.assertAlmostEqual(retry_after, 0.2, places=1)
    
    def test_token_refill_over_time(self):
        """Test that tokens are refilled over time."""
        limiter = SimpleTokenBucketRateLimiter(max_tokens=10, refill_rate=10)  # 10 tokens per second
        # Consume all tokens
        limiter.is_allowed(10)
        self.assertEqual(limiter.tokens, 0)
        
        # Wait 0.5 seconds
        time.sleep(0.5)
        
        # Should have approximately 5 tokens refilled
        allowed, _ = limiter.is_allowed(5)
        self.assertTrue(allowed)
    
    def test_token_refill_capped_at_max(self):
        """Test that tokens don't exceed max capacity."""
        limiter = SimpleTokenBucketRateLimiter(max_tokens=10, refill_rate=100)  # Very high refill rate
        # Consume some tokens
        limiter.is_allowed(5)
        
        # Wait a bit and check - should cap at max
        time.sleep(0.1)
        available = limiter.get_available_tokens()
        self.assertLessEqual(available, 10)
    
    def test_get_available_tokens(self):
        """Test getting the current number of available tokens."""
        limiter = SimpleTokenBucketRateLimiter(max_tokens=100, refill_rate=10)
        
        # Consume some tokens
        limiter.is_allowed(30)
        
        # Check available tokens
        available = limiter.get_available_tokens()
        self.assertEqual(available, 70)
    
    def test_fractional_tokens(self):
        """Test that fractional tokens work correctly."""
        limiter = SimpleTokenBucketRateLimiter(max_tokens=10, refill_rate=10)
        
        # Consume all tokens
        limiter.is_allowed(10)
        
        # Wait 0.1 seconds (should add 1.0 token)
        time.sleep(0.1)
        available = limiter.get_available_tokens()
        self.assertGreaterEqual(available, 0.9)  # Allow some tolerance
        self.assertLessEqual(available, 1.1)
    
    def test_zero_refill_rate(self):
        """Test behavior with zero refill rate (no automatic refill)."""
        limiter = SimpleTokenBucketRateLimiter(max_tokens=5, refill_rate=0)
        
        # Consume all tokens
        limiter.is_allowed(5)
        
        # Should be rate limited and retry_after should be None (infinite wait)
        allowed, retry_after = limiter.is_allowed(1)
        self.assertFalse(allowed)
        # With zero refill rate, retry_after calculation may return None
        # This is acceptable behavior as it indicates tokens won't refill


if __name__ == '__main__':
    unittest.main()
