"""
Safe wrapper for Keystroke Dynamics integration
This file is called from the main exam system
"""

def verify_keystroke_session(session_id: str) -> dict:
    """
    Wrapper function to verify a keystroke session
    """
    try:
        # Import inside function to avoid circular imports
        from modules.Keystroke_dynamics.backend import main

        # Temporary safe fallback
        if hasattr(main, "evaluate_session"):
            score = main.evaluate_session(session_id)
        else:
            # Fallback score (until we wire exact function)
            score = 0.5

        return {
            "status": "success",
            "score": score,
            "module": "keystroke_dynamics"
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "module": "keystroke_dynamics"
        }
