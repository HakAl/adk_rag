"""
Circuit breaker pattern for handling provider failures.
"""
import time
from typing import Optional

from config import logger


class CircuitBreaker:
    """
    Circuit breaker to prevent repeated calls to failing services.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests blocked
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
            self,
            name: str,
            failure_threshold: int = 5,
            timeout: int = 60,
            half_open_attempts: int = 1
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Name of the service (for logging)
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery
            half_open_attempts: Number of successful attempts needed to close
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_attempts = half_open_attempts

        self.failures = 0
        self.successes = 0
        self.open_until: Optional[float] = None
        self.state = "CLOSED"

    def is_open(self) -> bool:
        """
        Check if circuit is open (service unavailable).

        Returns:
            True if circuit is open, False otherwise
        """
        if self.open_until is None:
            return False

        # Check if timeout has passed
        if time.time() >= self.open_until:
            # Transition to HALF_OPEN
            self.state = "HALF_OPEN"
            self.successes = 0
            logger.info(f"Circuit breaker [{self.name}] entering HALF_OPEN state")
            return False

        return True

    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        self.failures += 1

        if self.state == "HALF_OPEN":
            # Failure during recovery, go back to OPEN
            self._open_circuit()
            logger.warning(
                f"Circuit breaker [{self.name}] failed during recovery, "
                f"reopening for {self.timeout}s"
            )
        elif self.failures >= self.failure_threshold:
            # Too many failures, open circuit
            self._open_circuit()
            logger.warning(
                f"Circuit breaker [{self.name}] OPENED after {self.failures} failures, "
                f"blocking for {self.timeout}s"
            )

    def record_success(self):
        """Record a success and potentially close the circuit."""
        self.failures = 0

        if self.state == "HALF_OPEN":
            self.successes += 1

            if self.successes >= self.half_open_attempts:
                # Enough successes, close circuit
                self._close_circuit()
                logger.info(f"Circuit breaker [{self.name}] CLOSED, service recovered")
        elif self.state == "OPEN":
            # Shouldn't happen, but handle gracefully
            logger.warning(f"Circuit breaker [{self.name}] received success while OPEN")

    def _open_circuit(self):
        """Open the circuit."""
        self.state = "OPEN"
        self.open_until = time.time() + self.timeout
        self.failures = 0

    def _close_circuit(self):
        """Close the circuit."""
        self.state = "CLOSED"
        self.open_until = None
        self.successes = 0
        self.failures = 0

    def get_state(self) -> str:
        """Get current circuit state."""
        return self.state

    def reset(self):
        """Manually reset the circuit breaker."""
        self._close_circuit()
        logger.info(f"Circuit breaker [{self.name}] manually reset")