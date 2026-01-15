"""
Simple Fixed Window Rate Limiter

A very simple rate limiter that tracks:
- Last consumption time (window start)
- Request counter

No support for multiple keys - just one simple counter.
"""

import time
from typing import Optional, Tuple


class FixedWindowRateLimiter:
    """
    Simple rate limiter using fixed time windows.
    
    Example:
        limiter = FixedWindowRateLimiter(max_requests=100, window_seconds=60)
        allowed, retry_after = await limiter.is_allowed()
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """Initialize rate limiter with max requests per window."""
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.count = 0
        self.window_start = int(time.time() // window_seconds) * window_seconds
    
    def is_allowed(self) -> Tuple[bool, Optional[float]]:
        """
        Check if request is allowed.
        
        Returns:
            (is_allowed, retry_after) - retry_after is seconds until next window
        """
        current_time = time.time()
        current_window = int(current_time // self.window_seconds) * self.window_seconds
        
        # Reset if window expired
        if self.window_start != current_window:
            self.count = 0
            self.window_start = current_window
        
        # Check limit
        if self.count >= self.max_requests:
            # Calculate time until next window
            next_window_start = (current_window + self.window_seconds)
            retry_after = next_window_start - current_time
            return False, retry_after
        
        # Allow request and increment counter
        self.count += 1
        return True, None
    
    def get_remaining_requests(self) -> int:
        """Get remaining requests allowed in current window."""
        current_time = time.time()
        current_window = int(current_time // self.window_seconds) * self.window_seconds
        
        # Reset if window expired
        if self.window_start != current_window:
            return self.max_requests
        
        return max(0, self.max_requests - self.count)
