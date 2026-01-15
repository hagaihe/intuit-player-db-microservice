import time
from typing import Tuple, Optional


class SimpleTokenBucketRateLimiter:
    """
    Simple Token Bucket Rate Limiter

    A very simple rate limiter that tracks:
    - Current tokens (starts full)
    - Last refill time

    Tokens refill continuously at a constant rate.
    No support for multiple keys - just one simple bucket.

    Example:
        limiter = SimpleTokenBucketRateLimiter(max_tokens=100, refill_rate=10)
        allowed, retry_after = limiter.is_allowed()
    """

    def __init__(self, max_tokens: float = 100.0, refill_rate: float = 10.0):
        """
        Initialize token bucket rate limiter.

        Args:
            max_tokens: Maximum tokens the bucket can hold (starts full)
            refill_rate: Tokens added per second
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = max_tokens  # Start with full bucket
        self.last_refill = time.time()

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time since last refill."""
        current_time = time.time()
        elapsed = current_time - self.last_refill

        # Calculate tokens to add (can be fractional)
        tokens_to_add = elapsed * self.refill_rate

        # Add tokens, but don't exceed max capacity
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = current_time

    def is_allowed(self, tokens: float = 1.0) -> Tuple[bool, Optional[float]]:
        """
        Check if request is allowed (consumes tokens if allowed).

        Args:
            tokens: Number of tokens to consume (default: 1.0)

        Returns:
            (is_allowed, retry_after) - retry_after is seconds until enough tokens available
        """
        # Refill tokens first
        self._refill_tokens()

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

    def get_available_tokens(self) -> float:
        """Get current number of available tokens (after refill)."""
        self._refill_tokens()
        return self.tokens
