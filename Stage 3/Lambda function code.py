import json
import boto3
import time
import os
from datetime import datetime
from urllib.parse import unquote_plus

# Initialize AWS clients
s3_client = boto3.client('s3')
athena_client = boto3.client('athena')

# Configuration from environment variables
SOURCE_BUCKET = os.environ.get('SOURCE_BUCKET', 'medlaunch-assignment')
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET', 'medlaunch-query-output')
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'healthcare_db')
TABLE_NAME = os.environ.get('TABLE_NAME', 'facilities')
ATHENA_OUTPUT_LOCATION = f's3://{OUTPUT_BUCKET}/athena-results/'

def lambda_handler(event, context):
    """
    Main Lambda handler triggered by S3 events
    """
    try:
        # Extract S3 event details
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])
            
            print(f"Processing file: {key} from bucket: {bucket}")
            print(f"Processing Event : {event}")
            
            # Validate JSON file
            if not key.endswith('.json') and not key.endswith('.jsonl'):
                print(f"Skipping non-JSON file: {key}")
                continue
            
            # Process the file
            process_facility_data(bucket, key, context)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Processing completed successfully')
        }
    
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        raise

def process_facility_data(bucket, key, context):
    """
    Process facility data and execute Athena query
    """
    try:
        # Ensure Athena table exists
        ensure_athena_table()
        
        # Execute Athena query to count facilities per state
        query_execution_id = execute_athena_query()
        
        # Wait for query completion with timeout handling
        query_result = wait_for_query_completion(
            query_execution_id, 
            context
        )
        
        # Store results in output bucket
        store_query_results(query_execution_id, key)
        
        print(f"Successfully processed {key}")
        
    except Exception as e:
        print(f"Error processing {bucket}/{key}: {str(e)}")
        raise

def ensure_athena_table():
    """
    Create Athena database and table if they don't exist
    """
    try:
        # Create database
        create_db_query = f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}"
        execute_query(create_db_query, wait=True)
        
        # Create external table pointing to S3
        create_table_query = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS {DATABASE_NAME}.{TABLE_NAME} (
            facility_id string,
            facility_name string,
            location struct<
                address:string,
                city:string,
                state:string,
                zip:string
            >,
            employee_count int,
            services array<string>,
            labs array<struct<
                lab_name:string,
                certifications:array<string>
            >>,
            accreditations array<struct<
                accreditation_body:string,
                accreditation_id:string,
                valid_until:string
            >>
        )
        ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
        LOCATION 's3://{SOURCE_BUCKET}/'
        """
        
        execute_query(create_table_query, wait=True)
        print("Athena table ensured")
        
    except Exception as e:
        print(f"Error ensuring Athena table: {str(e)}")
        raise

def execute_athena_query():
    """
    Execute query to count accredited facilities per state
    """
    query = f"""
    SELECT 
        location.state as state,
        COUNT(DISTINCT facility_id) as facility_count,
        SUM(employee_count) as total_employees,
        COUNT(accreditation) as total_accreditations
    FROM {DATABASE_NAME}.{TABLE_NAME}
    CROSS JOIN UNNEST(accreditations) AS t(accreditation)
    WHERE accreditation.valid_until >= CAST(current_date AS VARCHAR)
    GROUP BY location.state
    ORDER BY facility_count DESC
    """
    
    return execute_query(query, wait=False)

def execute_query(query, wait=False):
    """
    Execute an Athena query
    """
    try:
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': DATABASE_NAME},
            ResultConfiguration={
                'OutputLocation': ATHENA_OUTPUT_LOCATION,
                'EncryptionConfiguration': {
                    'EncryptionOption': 'SSE_S3'
                }
            }
        )
        
        query_execution_id = response['QueryExecutionId']
        print(f"Query execution started: {query_execution_id}")
        
        if wait:
            wait_for_query_completion(query_execution_id, None, timeout=30)
        
        return query_execution_id
        
    except Exception as e:
        print(f"Error executing query: {str(e)}")
        raise

def wait_for_query_completion(query_execution_id, context, timeout=240):
    """
    Wait for Athena query to complete with timeout and retry handling
    """
    start_time = time.time()
    max_wait_time = timeout  # Maximum wait time in seconds
    
    # Check remaining Lambda execution time if context is provided
    if context:
        remaining_time = context.get_remaining_time_in_millis() / 1000
        max_wait_time = min(max_wait_time, remaining_time - 10)  # Keep 10s buffer
    
    while True:
        elapsed_time = time.time() - start_time
        
        # Check timeout
        if elapsed_time > max_wait_time:
            print(f"Query timeout after {elapsed_time}s")
            raise TimeoutError(f"Query execution timeout: {query_execution_id}")
        
        try:
            response = athena_client.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            
            status = response['QueryExecution']['Status']['State']
            
            if status == 'SUCCEEDED':
                print(f"Query succeeded in {elapsed_time:.2f}s")
                return response
            
            elif status in ['FAILED', 'CANCELLED']:
                reason = response['QueryExecution']['Status'].get(
                    'StateChangeReason', 
                    'Unknown error'
                )
                raise Exception(f"Query {status}: {reason}")
            
            elif status in ['QUEUED', 'RUNNING']:
                print(f"Query {status}... ({elapsed_time:.1f}s)")
                time.sleep(2)  # Poll every 2 seconds
            
        except athena_client.exceptions.InvalidRequestException as e:
            print(f"Invalid request: {str(e)}")
            raise
        except Exception as e:
            print(f"Error checking query status: {str(e)}")
            raise

def store_query_results(query_execution_id, source_key):
    """
    Copy query results to a structured location in output bucket
    """
    try:
        # Get query results
        results = athena_client.get_query_results(
            QueryExecutionId=query_execution_id,
            MaxResults=1000
        )
        
        # Format results as JSON
        columns = [col['Label'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
        rows = results['ResultSet']['Rows'][1:]  # Skip header row
        
        formatted_results = []
        for row in rows:
            row_data = {}
            for i, col in enumerate(columns):
                value = row['Data'][i].get('VarCharValue', '')
                row_data[col] = value
            formatted_results.append(row_data)
        
        # Create output object
        output_data = {
            'query_execution_id': query_execution_id,
            'source_file': source_key,
            'execution_time': datetime.utcnow().isoformat(),
            'result_count': len(formatted_results),
            'results': formatted_results
        }
        
        # Store in output bucket with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        output_key = f"processed-results/{timestamp}-{source_key.split('/')[-1]}"
        
        s3_client.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=output_key,
            Body=json.dumps(output_data, indent=2),
            ContentType='application/json'
        )
        
        print(f"Results stored: s3://{OUTPUT_BUCKET}/{output_key}")
        
        # Also store raw CSV from Athena
        csv_key = f"{query_execution_id}.csv"
        copy_athena_csv(csv_key, source_key)
        
    except Exception as e:
        print(f"Error storing results: {str(e)}")
        raise

def copy_athena_csv(csv_key, source_key):
    """
    Copy Athena CSV results to organized location
    """
    try:
        # Athena stores results in athena-results/ folder
        source_csv_key = f"athena-results/{csv_key}"
        timestamp = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        dest_csv_key = f"csv-results/{timestamp}-results.csv"
        
        s3_client.copy_object(
            Bucket=OUTPUT_BUCKET,
            CopySource={'Bucket': OUTPUT_BUCKET, 'Key': source_csv_key},
            Key=dest_csv_key
        )
        
        print(f"CSV copied: s3://{OUTPUT_BUCKET}/{dest_csv_key}")
        
    except Exception as e:
        print(f"Warning: Could not copy CSV: {str(e)}")
        # Non-critical error, continue processing
