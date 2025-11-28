# Healthcare Facility Data Processing Pipeline

> Event-driven serverless data processing solution using AWS Lambda, S3, and Athena

[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20S3%20%7C%20Athena-orange)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.9-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Stages Implemented](#stages-implemented)
- [Monitoring](#monitoring)
- [Cost Estimation](#cost-estimation)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This project implements an automated, event-driven pipeline for processing healthcare facility data. When JSON files containing facility information are uploaded to S3, the system automatically:

1. Triggers a Lambda function
2. Executes analytical queries using Amazon Athena
3. Stores processed results in structured formats
4. Handles errors with automatic retries

**Key Achievement**: Zero manual intervention required from upload to results delivery.

## 🏗️ Architecture

![Architecture Diagram](docs/architecture/architecture-diagram.png)

### Data Flow

```
JSON Upload → S3 (medlaunch-assignment)
                ↓ (S3 Event Notification)
             Lambda Function
                ↓
        ┌───────┴────────┐
        ↓                ↓
    Athena Query    Store Results
    (Analytics)     (S3 Output Bucket)
        ↓
   JSON + CSV Results
```

See [Architecture Documentation](docs/ARCHITECTURE.md) for detailed technical design.

## ✨ Features

### Stage 2: S3 and Athena Setup
- ✅ Dual S3 bucket architecture (source and output)
- ✅ Server-side encryption enabled
- ✅ Versioning for data protection
- ✅ Event notifications configured
- ✅ Athena external table with JSON SerDe
- ✅ Automated schema management

### Stage 3: Event-Driven Lambda Processing
- ✅ Automatic S3 event triggering
- ✅ Intelligent timeout handling
- ✅ Automatic retry mechanism (up to 2 retries)
- ✅ Dead Letter Queue for failed events
- ✅ Dual-format output (JSON + CSV)
- ✅ Comprehensive error handling
- ✅ CloudWatch logging and monitoring
- ✅ Production-ready configuration

## 📁 Project Structure

```
├── README.md                          # Main documentation
├── lambda/
│   ├── lambda_function.py            # Main Lambda handler
│   ├── requirements.txt              # Python dependencies
│   └── tests/
│       └── test_lambda.py            # Unit tests
├── infrastructure/
│   ├── cloudformation-template.yaml  # IaC deployment
│   └── iam-policy.json              # IAM permissions
├── docs/
│   ├── ARCHITECTURE.md              # Architecture details
│   ├── DEPLOYMENT.md                # Deployment guide
│   ├── TESTING.md                   # Testing guide
│   └── architecture/
│       ├── architecture-diagram.png
│       ├── data-flow-diagram.png
│       └── sequence-diagram.png
├── sample-data/
│   └── sample_data.jsonl            # Test data
└── scripts/
    ├── setup.sh                     # Automated setup
    └── deploy.sh                    # Deployment script
```

## 🔧 Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured (`aws configure`)
- Python 3.9 or higher
- Basic understanding of AWS services (S3, Lambda, Athena)

## 📦 Installation

### Option 1: Quick Deploy with CloudFormation (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/healthcare-data-pipeline.git
cd healthcare-data-pipeline

# Deploy using CloudFormation
aws cloudformation create-stack \
  --stack-name medlaunch-processor \
  --template-body file://infrastructure/cloudformation-template.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for deployment to complete (3-5 minutes)
aws cloudformation wait stack-create-complete \
  --stack-name medlaunch-processor
```

### Option 2: Manual Setup

Follow the detailed steps in [DEPLOYMENT.md](docs/DEPLOYMENT.md)

## 🚀 Usage

### Upload Data for Processing

```bash
# Upload a JSON file
aws s3 cp sample-data/sample_data.jsonl s3://medlaunch-assignment/

# Monitor Lambda execution
aws logs tail /aws/lambda/MedLaunchProcessor --follow

# Check results
aws s3 ls s3://medlaunch-query-output/processed-results/
```

### Expected Output

Results are stored in two formats:

**JSON Format** (`processed-results/`):
```json
{
  "query_execution_id": "abc123-def456",
  "source_file": "sample_data.jsonl",
  "execution_time": "2024-11-20T10:30:00",
  "result_count": 3,
  "results": [
    {
      "state": "TX",
      "facility_count": "1",
      "total_employees": "250",
      "total_accreditations": "2"
    }
  ]
}
```

**CSV Format** (`csv-results/`):
Raw Athena query results in CSV format.

## 📊 Stages Implemented

### Stage 2: Infrastructure Setup

**Deliverables:**
- S3 bucket configuration with event notifications
- Athena database and external table creation
- Security configurations (encryption, IAM)

**Key Files:**
- `infrastructure/cloudformation-template.yaml`
- `docs/ARCHITECTURE.md`

### Stage 3: Event-Driven Processing

**Deliverables:**
- Lambda function with timeout handling
- Automatic retry mechanisms
- Query execution and result storage
- Comprehensive error handling

**Key Files:**
- `lambda/lambda_function.py`
- `infrastructure/iam-policy.json`
- `docs/DEPLOYMENT.md`

## 📈 Monitoring

### CloudWatch Metrics

Monitor these key metrics in AWS Console:

- **Invocations**: Total processing requests
- **Duration**: Average execution time
- **Errors**: Failed invocations
- **Throttles**: Rate limiting occurrences

### Alarms Configured

- Error rate > 5 in 5 minutes
- Average duration > 4 minutes (approaching timeout)
- Dead Letter Queue messages received

### View Logs

```bash
# Real-time logs
aws logs tail /aws/lambda/MedLaunchProcessor --follow

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/MedLaunchProcessor \
  --filter-pattern "ERROR"
```

## 💰 Cost Estimation

Estimated monthly costs for 1,000 file uploads:

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 1,000 invocations × 30s | $0.01 |
| Athena | 1GB scanned | $0.01 |
| S3 Storage | 10GB | $0.23 |
| S3 Requests | 2,000 PUT/GET | $0.01 |
| **Total** | | **~$0.26/month** |

*Costs vary by region and actual usage*

## 🧪 Testing

Run the test suite:

```bash
cd lambda
python -m pytest tests/
```

For detailed testing procedures, see [TESTING.md](docs/TESTING.md)

## 🔒 Security

- S3 bucket encryption enabled (AES-256)
- IAM roles follow least privilege principle
- No hardcoded credentials
- VPC support ready (optional)
- CloudTrail logging enabled

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Your Name**
- GitHub: [@arpitasidd](https://github.com/arpitasidd)
- LinkedIn: [Arpita Siddhabhatti](https://www.linkedin.com/in/arpita-siddhabhatti-17893b312/)

## 🙏 Acknowledgments

- AWS Documentation
- Healthcare data standards (HL7, FHIR)
- Open source community

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Documentation](docs/)
2. Search [Issues](https://github.com/yourusername/healthcare-data-pipeline/issues)
3. Create a new issue with detailed information

---

**Project Status**: ✅ Production Ready

**Last Updated**: November 2024# Healthcare-data-pipeline
Event-driven serverless data processing pipeline for healthcare facility data using AWS Lambda, S3, and Athena with automatic retry and timeout handling.
