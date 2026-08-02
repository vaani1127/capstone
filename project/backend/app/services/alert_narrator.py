"""
Deterministic, template-based Alert Narrator.

Generates plain-English narratives for anomaly alerts without LLM calls.
One sentence per alert, keyed by (trigger_type, dominant_feature) pairs.
"""
from typing import List, Dict, Any, Optional, Tuple


TEMPLATE_REGISTRY: Dict[Tuple[str, str], str] = {
    # single_event: Access volume spikes
    ("single_event", "actions_per_hour"): (
        "{user_name} ({role}) performed {multiple} baseline access volume "
        "({actual:.1f} actions/hour vs {baseline:.1f} baseline) on {timestamp}."
    ),
    # single_event: Patient access spike
    ("single_event", "unique_patients_accessed"): (
        "{user_name} ({role}) accessed {multiple}x baseline unique patients "
        "({actual} vs {baseline} baseline) in a single session."
    ),
    # single_event: Off-hours access
    ("single_event", "off_hours_flag"): (
        "{user_name} ({role}) accessed records during off-hours when not normally active."
    ),
    # single_event: Rapid edits
    ("single_event", "rapid_edit_flag"): (
        "{user_name} ({role}) made edits at rapid pace, flagged as potential bulk modification."
    ),
    # single_event: Record entropy spike
    ("single_event", "record_type_entropy"): (
        "{user_name} ({role}) accessed diverse record types ({actual:.2f} entropy) "
        "significantly higher than baseline ({baseline:.2f})."
    ),
    # single_event: Untreated patient ratio
    ("single_event", "untreated_patient_ratio"): (
        "{user_name} ({role}) accessed untreated/non-affiliated patients "
        "at {ratio:.1%} ratio, anomalous for this role."
    ),
    # single_event: Cross-role action
    ("single_event", "cross_role_action_flag"): (
        "{user_name} ({role}) performed actions outside their normal role scope."
    ),
    # sustained_trend: Behavioral drift over multiple events
    ("sustained_trend", "generic"): (
        "{user_name} ({role}) has shown 7 consecutive anomalous behavioral scores "
        "(all > 0.35), sustained trend escalated at {timestamp}."
    ),
    # identity_drift: User drifting toward higher-privilege role
    ("identity_drift", "generic"): (
        "{user_name} ({role}) behavioral patterns trending toward {target_role} "
        "(privilege gap: {privilege_gap}). Distance trending down from {initial_distance:.1f} to {current_distance:.1f}. "
        "Importance: {importance:.2f}."
    ),
}


def _extract_top_feature(top_features: List[Dict[str, Any]]) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Extract the highest-importance feature from top_features.

    Args:
        top_features: List of {feature, value, shap} dicts from IsolationForest

    Returns:
        Tuple of (feature_name, feature_dict) or None if list is empty
    """
    if not top_features or len(top_features) == 0:
        return None

    # Return the first feature (already sorted by importance in anomaly_service)
    if isinstance(top_features[0], dict) and "feature" in top_features[0]:
        return (top_features[0]["feature"], top_features[0])

    return None


def _get_template(trigger_type: str, top_feature: Optional[str]) -> str:
    """
    Look up template by (trigger_type, feature) pair, fall back to generic.

    Args:
        trigger_type: "single_event", "sustained_trend", or "identity_drift"
        top_feature: Feature name or None

    Returns:
        Template string with placeholders ({key} format)
    """
    if top_feature:
        key = (trigger_type, top_feature)
        if key in TEMPLATE_REGISTRY:
            return TEMPLATE_REGISTRY[key]

    # Fallback to generic template for this trigger_type
    generic_key = (trigger_type, "generic")
    if generic_key in TEMPLATE_REGISTRY:
        return TEMPLATE_REGISTRY[generic_key]

    # Ultimate fallback (should never reach here if registry is complete)
    return (
        "{user_name} ({role}) triggered a {trigger_type} anomaly alert "
        "with score {score:.3f}."
    )


def narrate_alert(
    trigger_type: str,
    top_features: List[Dict[str, Any]],
    user_name: str,
    user_role: str,
    extra_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a deterministic, template-based narrative for an anomaly alert.

    Args:
        trigger_type: "single_event", "sustained_trend", or "identity_drift"
        top_features: List of {feature, value, shap} dicts (from IsolationForest scoring)
        user_name: Display name of the user
        user_role: Role of the user (e.g., "Nurse", "Doctor", "Admin")
        extra_context: Optional dict with {
            "score": float,
            "timestamp": str,
            "target_role": str (for identity_drift),
            "privilege_gap": int (for identity_drift),
            "initial_distance": float (for identity_drift),
            "current_distance": float (for identity_drift),
            "importance": float (for identity_drift),
        }

    Returns:
        Plain-English narrative string (one sentence)
    """
    if extra_context is None:
        extra_context = {}

    # Extract dominant feature
    top_feature_tuple = _extract_top_feature(top_features)
    top_feature_name = top_feature_tuple[0] if top_feature_tuple else None
    top_feature_dict = top_feature_tuple[1] if top_feature_tuple else {}

    # Get appropriate template
    template = _get_template(trigger_type, top_feature_name)

    # Build context for template interpolation
    context = {
        "user_name": user_name,
        "role": user_role,
        "trigger_type": trigger_type,
        "timestamp": extra_context.get("timestamp", "now"),
    }

    # Add feature-specific context
    if trigger_type == "single_event":
        context["actual"] = top_feature_dict.get("value", 0)
        context["baseline"] = extra_context.get("baseline", 0)
        if context["baseline"] > 0:
            context["multiple"] = f"{context['actual'] / context['baseline']:.1f}x"
        else:
            context["multiple"] = "N/A"
        context["score"] = extra_context.get("score", 0)
        context["ratio"] = top_feature_dict.get("value", 0)

    elif trigger_type == "sustained_trend":
        context["score_count"] = extra_context.get("score_count", 7)

    elif trigger_type == "identity_drift":
        context["target_role"] = extra_context.get("target_role", "higher-privilege role")
        context["privilege_gap"] = extra_context.get("privilege_gap", 0)
        context["initial_distance"] = extra_context.get("initial_distance", 0)
        context["current_distance"] = extra_context.get("current_distance", 0)
        context["importance"] = extra_context.get("importance", 0)

    # Format template with context, handling missing keys gracefully
    try:
        narrative = template.format(**context)
    except KeyError as e:
        # If a key is missing, return a safe fallback
        missing_key = str(e)
        narrative = f"{user_name} ({user_role}) triggered a {trigger_type} anomaly alert."

    return narrative.strip()
