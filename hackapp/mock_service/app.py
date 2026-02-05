"""
Mock External Service
Simulates Voice AI and other external APIs for demo
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from data import get_mock_summary, extract_vital_signs
import time


app = Flask(__name__)
CORS(app)  # Allow requests from middleware


@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'HackApp Mock External Service',
        'version': '1.0.0',
        'endpoints': {
            'clinical_summary': '/api/clinical_summary (POST)',
            'health': '/health'
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'mock_external_service'
    })


@app.route('/api/clinical_summary', methods=['POST'])
def clinical_summary():
    """
    Mock Voice AI Clinical Summarization Endpoint

    Accepts clinical text and returns:
    - Summary
    - ICD-10 diagnosis code
    - Confidence score

    Request:
        {
            "text": "Clinical note text...",
            "language": "en" (optional),
            "include_icd10": true (optional)
        }

    Response:
        {
            "summary": "Clinical summary...",
            "icd10": {
                "code": "J18.9",
                "label": "Pneumonia, unspecified organism"
            },
            "confidence": 0.92,
            "processing_time_ms": 234
        }
    """
    try:
        data = request.json

        if not data or 'text' not in data:
            return jsonify({
                'error': 'Missing required field: text'
            }), 400

        clinical_text = data['text']

        # Validate text length
        if len(clinical_text) < 10:
            return jsonify({
                'error': 'Text too short (minimum 10 characters)'
            }), 400

        if len(clinical_text) > 10000:
            return jsonify({
                'error': 'Text too long (maximum 10000 characters)'
            }), 400

        # Simulate processing delay (realistic)
        time.sleep(0.2)  # 200ms delay

        # Generate mock summary
        result = get_mock_summary(clinical_text)

        print(f"✅ Processed clinical summary request:")
        print(f"   Input length: {len(clinical_text)} chars")
        print(f"   Diagnosis: {result['icd10']['code']}")
        print(f"   Confidence: {result['confidence']:.2f}")

        return jsonify(result)

    except Exception as e:
        print(f"❌ Error in clinical_summary: {e}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@app.route('/api/drug_interaction', methods=['POST'])
def drug_interaction():
    """
    Mock Drug Interaction Checker (bonus endpoint)

    Request:
        {
            "medications": "Aspirin, Warfarin"
        }

    Response:
        {
            "interactions": [
                {
                    "drug1": "Aspirin",
                    "drug2": "Warfarin",
                    "severity": "high",
                    "description": "Increased risk of bleeding"
                }
            ],
            "severity": "high"
        }
    """
    try:
        data = request.json
        medications = data.get('medications', '')

        # Simple mock logic
        interactions = []
        severity = "none"

        if 'warfarin' in medications.lower() and 'aspirin' in medications.lower():
            interactions.append({
                'drug1': 'Aspirin',
                'drug2': 'Warfarin',
                'severity': 'high',
                'description': 'Increased risk of bleeding due to combined antiplatelet and anticoagulant effects'
            })
            severity = "high"

        return jsonify({
            'interactions': interactions,
            'severity': severity,
            'recommendations': 'Monitor for signs of bleeding if both medications are necessary'
        })

    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            '/api/clinical_summary',
            '/api/drug_interaction',
            '/health'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error'
    }), 500


def main():
    """Start the mock service"""
    print("=" * 70)
    print("🤖 HackApp Mock External Service Starting...")
    print("=" * 70)
    print("\n📍 Endpoints:")
    print("   • http://localhost:5001/api/clinical_summary")
    print("   • http://localhost:5001/api/drug_interaction")
    print("   • http://localhost:5001/health")
    print("\n✅ Mock service ready for requests!")
    print("=" * 70 + "\n")

    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False  # Set to False to reduce console noise
    )


if __name__ == "__main__":
    main()
