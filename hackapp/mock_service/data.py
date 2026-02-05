"""
Mock Data for External Service
Keyword-based logic for realistic responses
"""

import re


# Diagnosis patterns based on keywords
DIAGNOSES = {
    'pneumonia': {
        'keywords': ['cough', 'fever', 'chest', 'infiltrate', 'pneumonia', 'respiratory', 'lung'],
        'summary': 'Pneumonia with respiratory symptoms and radiological findings consistent with lower respiratory tract infection',
        'icd10': {'code': 'J18.9', 'label': 'Pneumonia, unspecified organism'},
        'confidence': 0.92
    },
    'hypertension': {
        'keywords': ['blood pressure', 'hypertension', 'BP', 'elevated pressure', 'HTN', 'systolic', 'diastolic'],
        'summary': 'Essential hypertension without complications',
        'icd10': {'code': 'I10', 'label': 'Essential (primary) hypertension'},
        'confidence': 0.88
    },
    'diabetes': {
        'keywords': ['diabetes', 'glucose', 'blood sugar', 'glycemia', 'A1C', 'hyperglycemia'],
        'summary': 'Type 2 diabetes mellitus without complications',
        'icd10': {'code': 'E11.9', 'label': 'Type 2 diabetes mellitus without complications'},
        'confidence': 0.90
    },
    'uri': {
        'keywords': ['cold', 'runny nose', 'sore throat', 'URI', 'upper respiratory', 'congestion'],
        'summary': 'Acute upper respiratory infection, likely viral etiology',
        'icd10': {'code': 'J06.9', 'label': 'Acute upper respiratory infection, unspecified'},
        'confidence': 0.85
    },
    'copd': {
        'keywords': ['COPD', 'emphysema', 'chronic bronchitis', 'shortness of breath', 'dyspnea', 'wheezing'],
        'summary': 'Chronic obstructive pulmonary disease with acute exacerbation',
        'icd10': {'code': 'J44.0', 'label': 'COPD with acute lower respiratory infection'},
        'confidence': 0.87
    },
    'sepsis': {
        'keywords': ['sepsis', 'infection', 'septic', 'bacteremia', 'systemic infection'],
        'summary': 'Sepsis, unspecified organism, requires immediate intervention',
        'icd10': {'code': 'A41.9', 'label': 'Sepsis, unspecified organism'},
        'confidence': 0.91
    },
    'reflux': {
        'keywords': ['heartburn', 'reflux', 'GERD', 'acid', 'esophagus', 'regurgitation'],
        'summary': 'Gastro-esophageal reflux disease without esophagitis',
        'icd10': {'code': 'K21.9', 'label': 'Gastro-esophageal reflux disease without esophagitis'},
        'confidence': 0.83
    },
    'back_pain': {
        'keywords': ['back pain', 'lumbar', 'spine', 'lower back', 'LBP'],
        'summary': 'Low back pain, likely musculoskeletal origin',
        'icd10': {'code': 'M54.5', 'label': 'Low back pain'},
        'confidence': 0.79
    },
    'anxiety': {
        'keywords': ['anxiety', 'panic', 'worry', 'stress', 'nervous', 'GAD'],
        'summary': 'Generalized anxiety disorder',
        'icd10': {'code': 'F41.1', 'label': 'Generalized anxiety disorder'},
        'confidence': 0.82
    },
    'depression': {
        'keywords': ['depression', 'depressed', 'sad', 'MDD', 'major depressive'],
        'summary': 'Major depressive disorder, single episode',
        'icd10': {'code': 'F32.9', 'label': 'Major depressive disorder, single episode, unspecified'},
        'confidence': 0.84
    },
    'fever': {
        'keywords': ['fever', 'febrile', 'temperature', 'pyrexia'],
        'summary': 'Fever of unknown origin, requires further evaluation',
        'icd10': {'code': 'R50.9', 'label': 'Fever, unspecified'},
        'confidence': 0.75
    }
}


def get_mock_summary(text: str) -> dict:
    """
    Generate mock clinical summary based on keyword matching

    Args:
        text: Clinical note text

    Returns:
        Dictionary with summary, ICD-10 code, and confidence
    """
    text_lower = text.lower()

    # Try to match diagnoses based on keywords
    best_match = None
    best_score = 0

    for diagnosis_key, diagnosis_data in DIAGNOSES.items():
        # Count keyword matches
        matches = sum(1 for keyword in diagnosis_data['keywords'] if keyword in text_lower)

        # Calculate score (number of matches + bonus for multiple matches)
        score = matches + (0.1 * matches if matches > 2 else 0)

        if score > best_score:
            best_score = score
            best_match = diagnosis_data

    # If good match found (at least 2 keywords)
    if best_match and best_score >= 2:
        return {
            'summary': best_match['summary'],
            'icd10': best_match['icd10'],
            'confidence': min(0.95, best_match['confidence'] + (best_score * 0.02)),
            'processing_time_ms': 234
        }

    # No clear match - return generic response
    return {
        'summary': 'Clinical presentation documented. Further evaluation and assessment recommended to establish definitive diagnosis.',
        'icd10': {
            'code': 'R69',
            'label': 'Illness, unspecified'
        },
        'confidence': 0.50,
        'processing_time_ms': 156
    }


def extract_vital_signs(text: str) -> dict:
    """
    Extract vital signs from clinical text (bonus feature)

    Args:
        text: Clinical note

    Returns:
        Dictionary of extracted vitals
    """
    vitals = {}

    # Temperature (°F or °C)
    temp_match = re.search(r'(\d{2,3}(?:\.\d)?)\s*°?[FC]', text, re.IGNORECASE)
    if temp_match:
        vitals['temperature'] = temp_match.group(1)

    # Blood Pressure
    bp_match = re.search(r'(\d{2,3})/(\d{2,3})', text)
    if bp_match:
        vitals['blood_pressure'] = f"{bp_match.group(1)}/{bp_match.group(2)}"

    # Heart Rate
    hr_match = re.search(r'(\d{2,3})\s*bpm', text, re.IGNORECASE)
    if hr_match:
        vitals['heart_rate'] = hr_match.group(1)

    return vitals


# ============================================================================
# Test code
# ============================================================================

if __name__ == "__main__":
    print("Testing mock data logic...")
    print("=" * 60)

    test_cases = [
        "Patient presents with persistent cough, fever 102F, and chest pain. Chest X-ray shows infiltrates.",
        "Elevated blood pressure readings: 160/95. Patient has history of HTN.",
        "Patient complains of heartburn and acid reflux after meals.",
        "Chronic back pain in lumbar region, worsens with movement."
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"\n{i}. Test Case:")
        print(f"   Input: {text[:70]}...")
        result = get_mock_summary(text)
        print(f"   Summary: {result['summary'][:70]}...")
        print(f"   ICD-10: {result['icd10']['code']} - {result['icd10']['label']}")
        print(f"   Confidence: {result['confidence']:.2f}")

    print("\n✅ Mock data tests complete!")
