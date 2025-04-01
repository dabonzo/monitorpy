"""
Batch operation endpoints for the MonitorPy API.

This module defines API endpoints for batch operations,
allowing multiple checks to be run in parallel.
"""

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy.exc import SQLAlchemyError

from monitorpy.api.extensions import db
from monitorpy.api.models import Check, Result
from monitorpy.core.batch_runner import run_checks_in_parallel

bp = Blueprint("batch", __name__)


@bp.route("/run", methods=["POST"])
def batch_run_checks():
    """
    Run multiple checks in parallel.

    Request body:
        checks: List of check IDs to run
        max_workers: Optional maximum number of worker threads
        timeout: Optional timeout in seconds

    Returns:
        JSON response with check results
    """
    data = request.get_json()

    if not data or "checks" not in data or not isinstance(data["checks"], list):
        return jsonify({"error": "Invalid request. Expected a list of check IDs."}), 400

    check_ids = data["checks"]
    max_workers = data.get("max_workers")
    timeout = data.get("timeout")

    # Get all checks from database
    checks = Check.query.filter(Check.id.in_(check_ids)).all()

    if not checks:
        return jsonify({"error": "No valid checks found for the provided IDs"}), 404

    # Convert checks to the format expected by run_checks_in_parallel
    check_configs = [
        {
            "id": check.id,
            "plugin_type": check.plugin_type,
            "config": check.get_config(),
        }
        for check in checks
    ]

    try:
        # Run the checks in parallel
        check_results = run_checks_in_parallel(check_configs, max_workers, timeout)

        # Store results in the database
        stored_results = []
        for check_config, result in check_results:
            try:
                check_id = check_config["id"]

                # Create and store result
                db_result = Result.from_check_result(check_id, result)
                db.session.add(db_result)

                # Update check's last run timestamp
                check = Check.query.get(check_id)
                if check:
                    check.last_run = db_result.executed_at

                stored_results.append(
                    {"check_id": check_id, "result": result.to_dict()}
                )
            except Exception as e:
                current_app.logger.error(
                    f"Error storing result for check {check_config.get('id')}: {e}"
                )

        db.session.commit()

        return jsonify({"results": stored_results})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error executing batch checks: {str(e)}"}), 500


@bp.route("/run-ad-hoc", methods=["POST"])
def batch_run_ad_hoc_checks():
    """
    Run multiple ad-hoc checks in parallel without storing results.

    Request body:
        checks: List of check configurations, each containing:
            - plugin_type: Type of plugin to use
            - config: Configuration for the plugin
        max_workers: Optional maximum number of worker threads
        timeout: Optional timeout in seconds

    Returns:
        JSON response with check results
    """
    data = request.get_json()

    if not data or "checks" not in data or not isinstance(data["checks"], list):
        return (
            jsonify(
                {"error": "Invalid request. Expected a list of check configurations."}
            ),
            400,
        )

    check_configs = data["checks"]
    max_workers = data.get("max_workers")
    timeout = data.get("timeout")

    # Validate each check configuration
    for i, check in enumerate(check_configs):
        if "plugin_type" not in check:
            return jsonify({"error": f"Missing plugin_type in check at index {i}"}), 400
        if "config" not in check:
            return jsonify({"error": f"Missing config in check at index {i}"}), 400

    try:
        # Run the checks in parallel
        check_results = run_checks_in_parallel(check_configs, max_workers, timeout)

        # Format results without storing in database
        results = [
            {
                "plugin_type": check_config.get("plugin_type"),
                "id": check_config.get("id", f"ad-hoc-{i}"),
                "result": result.to_dict(),
            }
            for i, (check_config, result) in enumerate(check_results)
        ]

        return jsonify({"results": results})

    except Exception as e:
        return jsonify({"error": f"Error executing batch checks: {str(e)}"}), 500
