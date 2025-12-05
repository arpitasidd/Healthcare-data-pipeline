# Healthcare Pipeline Challenge - Stages 1 & 3

## Overview

This repository contains the implementation of Stage 1 (Data Extraction with Athena) and Stage 3 (Event-Driven Processing with Lambda) of the healthcare pipeline challenge. The solution implements a fully automated, serverless data processing pipeline for healthcare facility analytics.

**Key Achievement**: Zero manual intervention required from upload to results delivery.
## Stages Implemented

### Stage 1: Data Extraction with Athena
* Extract key facility metrics from nested JSON data in S3
* Handle complex nested structures (services, labs, accreditations)
* Create external tables with proper schema definitions
* Generate comprehensive facility metrics using UNNEST operations
* Save query results to S3 in JSON format

### Stage 3: Event-Driven Processing with Lambda
* Automatic triggering on JSON file uploads to S3
* Execute Athena queries to count accredited facilities by state
* Intelligent timeout and retry handling mechanisms
* Store results in multiple formats (JSON and CSV)
* Comprehensive error handling and CloudWatch logging
* Dead Letter Queue for failed invocations

## Tools Used
* **AWS Lambda**: Serverless compute for event-driven processing
* **Amazon Athena**: Serverless SQL analytics for querying S3 data
* **Amazon S3**: Data storage for input files and query results
* **AWS Glue Data Catalog**: Schema registry and metadata store
* **CloudWatch**: Monitoring, logging, and alerting
* **IAM**: Secure access control and permissions management

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Flow Pipeline                       │
└─────────────────────────────────────────────────────────────┘

JSON Upload → S3 (medlaunch-assignment)
                ↓
            S3 Event Notification
                ↓
            Lambda Function (Auto-triggered)
                ↓
        ┌───────┴────────┐
        ↓                ↓
  Athena Query      Store Results
  (Analytics)    (medlaunch-query-output)
        ↓
  Database/Table Creation
        ↓
  UNNEST & Aggregation
        ↓
  Results → JSON + CSV
```

## Demo Link
*[Insert your Loom demo link here]*

## Implementation Summary

### Technical Approach

My solution implements a production-ready, event-driven healthcare data pipeline using AWS serverless technologies with a focus on automation, scalability, and maintainability.

**Stage 1: Athena Data Extraction**

For the data extraction layer, I designed a robust Athena schema that handles the complex nested JSON structure of healthcare facility data. The implementation uses AWS Glue's JSON SerDe to parse nested structures including arrays of services, labs with certifications, and accreditations with expiration dates. The key innovation in my approach is the dynamic table creation within the Lambda function itself - rather than requiring manual Athena setup, the Lambda function automatically creates the database and external table on first run, pointing to the S3 data location.

The extraction query leverages SQL UNNEST operations to flatten nested arrays, specifically extracting the first accreditation's expiry date while counting total services offered. This approach efficiently handles one-to-many relationships in the data model without requiring table normalization, keeping the query simple while maintaining performance. The query extracts five critical metrics: `facility_id`, `facility_name`, `employee_count`, `number_of_offered_services`, and `expiry_date_of_first_accreditation`, providing a comprehensive view of each facility's operational status.

**Stage 3: Event-Driven Lambda Processing**

The Lambda implementation represents a sophisticated event-driven architecture that automatically processes new data uploads without manual intervention. When a JSON file is uploaded to the source S3 bucket, an S3 event notification immediately triggers the Lambda function, which then orchestrates the entire analytics pipeline. The function implements intelligent timeout management by monitoring the Lambda context's remaining execution time, ensuring queries complete before the function times out (default 5 minutes, configurable up to 15 minutes).

A critical feature is the retry and error handling mechanism. The solution implements a three-tier approach: immediate retry logic within the function, Lambda's built-in asynchronous retry (configured for 2 retries), and a Dead Letter Queue (DLQ) that captures permanently failed events for investigation. This ensures no data is lost due to transient failures. The Lambda function executes a production-ready Athena query that counts accredited facilities per state, including only currently valid accreditations by filtering on expiry dates, and aggregates employee counts and accreditation totals.

Results are stored in two formats: structured JSON with metadata (query execution ID, timestamp, source file) for programmatic access, and raw CSV from Athena for traditional analytics tools. This dual-format approach supports both automated downstream processing and manual analysis by data analysts.

### Challenges and Solutions

**Challenge 1: Handling Nested JSON in Athena**
The most significant technical challenge was designing an Athena schema that properly handles deeply nested JSON structures with arrays of objects. Healthcare facility data contains multiple levels of nesting: services as string arrays, labs as arrays of objects with nested certification arrays, and accreditations as arrays of objects. I resolved this by using the `org.openx.data.jsonserde.JsonSerDe` serializer with carefully defined struct and array types in the CREATE TABLE statement. This approach allows Athena to parse complex structures without requiring data transformation, while still enabling efficient querying through UNNEST operations.

**Challenge 2: Lambda Timeout Management**
Athena queries can take variable time to complete depending on data volume and query complexity. With Lambda's maximum execution time of 15 minutes, there was a risk of timeout before query completion. I implemented a sophisticated timeout handling mechanism that monitors the Lambda context's `get_remaining_time_in_millis()` method and adjusts the polling behavior accordingly. The function keeps a 10-second buffer before the Lambda timeout, allowing graceful failure and retry rather than abrupt termination. This ensures queries that need more time are retried in a new invocation rather than being abandoned mid-execution.

**Challenge 3: Ensuring Data Pipeline Reliability**
In a production environment, the pipeline must handle various failure scenarios: S3 notification delays, Athena service throttling, transient network issues, and malformed input data. I addressed this through multiple defensive programming strategies: comprehensive try-catch blocks with detailed logging, validation of file extensions before processing, the Dead Letter Queue for capturing failed events, and idempotent table creation (using IF NOT EXISTS clauses) so the function can safely run multiple times on the same data. Additionally, I implemented CloudWatch integration for real-time monitoring and alerting, enabling proactive issue detection.

**Challenge 4: Managing AWS Permissions**
Cross-service operations required careful IAM policy configuration. The Lambda function needs permissions across multiple AWS services: S3 read from the source bucket, S3 write to the output bucket, Athena query execution, Glue catalog operations for database/table creation, and CloudWatch Logs for monitoring. I designed a least-privilege IAM policy that grants only necessary permissions, following AWS security best practices. The CloudFormation template automates this policy creation, ensuring consistent and secure deployments across environments.

## Key Features

### Automation & Scalability
- **Zero manual intervention**: Entire pipeline runs automatically on file upload
- **Serverless architecture**: Scales automatically with data volume
- **Concurrent processing**: Handles multiple file uploads simultaneously
- **Cost-efficient**: Pay only for actual compute time (seconds)

### Reliability & Monitoring
- **Automatic retries**: Up to 2 retries on failures with exponential backoff
- **Dead Letter Queue**: Captures failed events for troubleshooting
- **CloudWatch integration**: Real-time logs and metrics
- **Timeout protection**: Intelligent query completion monitoring

### Data Quality
- **Schema validation**: Ensures JSON structure matches expected format
- **Null filtering**: Handles missing or malformed data gracefully
- **Date validation**: Filters expired accreditations automatically
- **Result verification**: Stores execution metadata with results



## Future Enhancements

1. **Data Partitioning**: Implement date-based partitions for large datasets
2. **SNS Notifications**: Alert on query completion or failures
3. **Step Functions**: Orchestrate complex multi-stage workflows
4. **Data Quality Checks**: Validate data before processing
5. **Real-time Dashboard**: Visualize metrics using QuickSight
6. **API Gateway**: Expose results via REST API

## Lessons Learned

1. **Serverless is Production-Ready**: AWS Lambda with proper error handling is reliable for production workloads
2. **Athena's Power**: Complex analytics on S3 data without managing infrastructure
3. **IaC is Essential**: CloudFormation enables reproducible, version-controlled deployments
4. **Monitoring from Day 1**: CloudWatch integration should be built-in, not added later
5. **Cost Optimization**: Proper query design and data format selection significantly impact costs

## Conclusion

This implementation demonstrates a production-grade, event-driven data processing pipeline that combines the power of AWS serverless technologies. The solution is cost-effective, scalable, reliable, and maintainable - suitable for real-world healthcare analytics workloads. The automated nature of the pipeline, coupled with robust error handling and monitoring, makes it a strong foundation for building more complex data processing workflows.

---

## 👤 Author

**Arpita Siddhabhatti**
- Email: siddarpita09@gmail.com
- GitHub: [@arpitasidd](https://github.com/arpitasidd)
- LinkedIn: [Arpita Siddhabhatti](https://www.linkedin.com/in/arpita-siddhabhatti-17893b312/)


**Project Status**: Production Ready

**Last Updated**: November 2024# Healthcare-data-pipeline
Event-driven serverless data processing pipeline for healthcare facility data using AWS Lambda, S3, and Athena with automatic retry and timeout handling.
