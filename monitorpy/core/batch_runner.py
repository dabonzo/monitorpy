"""
Batch processing module for executing multiple checks in parallel.

This module provides functionality to run multiple monitoring checks
concurrently using ThreadPoolExecutor.
"""

import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Tuple, Optional, Union

from monitorpy.core.registry import registry
from monitorpy.core.result import CheckResult

# Configure logging
logger = logging.getLogger(__name__)


def run_checks_in_parallel(
    check_configs: List[Dict[str, Any]],
    max_workers: Optional[int] = None,
    timeout: Optional[float] = None,
) -> List[Tuple[Dict[str, Any], CheckResult]]:
    """
    Run multiple monitoring checks in parallel.

    Args:
        check_configs: List of check configuration dictionaries.
            Each dictionary must contain:
                - 'plugin_type': The plugin type/name
                - 'id': Optional ID to identify the check (used in result)
                - 'config': The configuration for the plugin
        max_workers: Maximum number of worker threads to use.
            Default is min(32, os.cpu_count() + 4).
        timeout: Maximum time in seconds to wait for all checks to complete.
            Default is None (wait indefinitely).

    Returns:
        List of tuples containing the original check configuration and the result.
    """
    start_time = time.time()
    results = []

    logger.info(f"Starting parallel execution of {len(check_configs)} checks")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all checks to the executor
        future_to_check = {
            executor.submit(
                _run_single_check, check["plugin_type"], check.get("config", {})
            ): check
            for check in check_configs
        }

        # Process results as they complete
        for future in as_completed(future_to_check, timeout=timeout):
            check = future_to_check[future]
            try:
                check_result = future.result()
                results.append((check, check_result))
                logger.debug(
                    f"Completed check {check.get('id', 'unknown')}: {check_result.status}"
                )
            except Exception as e:
                # Handle exceptions in thread execution
                error_result = CheckResult(
                    status=CheckResult.STATUS_ERROR,
                    message=f"Error executing check: {str(e)}",
                    response_time=0.0,
                    raw_data={
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                results.append((check, error_result))
                logger.error(f"Error executing check {check.get('id', 'unknown')}: {e}")

    total_time = time.time() - start_time
    logger.info(f"Completed {len(results)} checks in {total_time:.2f} seconds")

    return results


def _run_single_check(plugin_type: str, config: Dict[str, Any]) -> CheckResult:
    """
    Execute a single check with error handling.

    Args:
        plugin_type: Type of plugin to use
        config: Configuration for the plugin

    Returns:
        CheckResult: Result of the check
    """
    try:
        # Get plugin instance
        plugin = registry.get_plugin(plugin_type, config)

        # Validate configuration
        if not plugin.validate_config():
            return CheckResult(
                CheckResult.STATUS_ERROR,
                f"Invalid configuration for plugin {plugin_type}",
                0.0,
                {"config": config},
            )

        # Run the check
        return plugin.run_check()
    except Exception as e:
        logger.exception(f"Error running check with plugin {plugin_type}")
        return CheckResult(
            CheckResult.STATUS_ERROR,
            f"Exception running check: {str(e)}",
            0.0,
            {"error": str(e), "error_type": type(e).__name__},
        )


def run_check_batch(
    check_configs: List[Dict[str, Any]],
    batch_size: int = 10,
    max_workers: Optional[int] = None,
    timeout: Optional[float] = None,
) -> List[Tuple[Dict[str, Any], CheckResult]]:
    """
    Run a large number of checks in multiple batches.

    This is useful for very large numbers of checks to prevent
    excessive resource consumption.

    Args:
        check_configs: List of check configurations
        batch_size: Number of checks to run in each batch
        max_workers: Maximum number of worker threads per batch
        timeout: Timeout per batch in seconds

    Returns:
        List of tuples containing check configurations and results
    """
    results = []
    total_checks = len(check_configs)
    batches = [
        check_configs[i : i + batch_size] for i in range(0, total_checks, batch_size)
    ]

    logger.info(f"Processing {total_checks} checks in {len(batches)} batches")

    for i, batch in enumerate(batches):
        logger.info(f"Processing batch {i+1}/{len(batches)} ({len(batch)} checks)")
        batch_results = run_checks_in_parallel(batch, max_workers, timeout)
        results.extend(batch_results)

    return results
