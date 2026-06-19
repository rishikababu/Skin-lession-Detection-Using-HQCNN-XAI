def severity_stage(confidence):

    # Convert to percentage if model outputs 0-1
    if confidence <= 1:
        confidence = confidence * 100

    if confidence >= 85:
        stage = "High Risk"
        advice = "Immediate dermatologist consultation recommended"

    elif confidence >= 60:
        stage = "Moderate Risk"
        advice = "Medical review advised within short period"

    else:
        stage = "Low Risk"
        advice = "Routine monitoring recommended"

    return {
        "stage": stage,
        "confidence_percent": round(confidence, 2),
        "advice": advice
    }
