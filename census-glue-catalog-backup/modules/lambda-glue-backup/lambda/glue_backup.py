### modules/lambda-glue-backup/lambda/glue_backup.py

import json
import boto3
import os
from datetime import datetime
from typing import Dict, List, Any

glue_client = boto3.client('glue')
s3_client = boto3.client('s3')

BACKUP_BUCKET = os.environ['BACKUP_BUCKET']
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'prod')


def lambda_handler(event, context):
    """
    Main Lambda handler to backup AWS Glue Data Catalog
    """
    try:
        timestamp = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
        backup_prefix = f"glue-backup/{ENVIRONMENT}/{timestamp}"
        
        print(f"Starting Glue backup to s3://{BACKUP_BUCKET}/{backup_prefix}")
        
        # Backup databases and tables
        backup_databases(backup_prefix)
        
        # Backup crawlers
        backup_crawlers(backup_prefix)
        
        # Backup jobs
        backup_jobs(backup_prefix)
        
        # Backup classifiers
        backup_classifiers(backup_prefix)
        
        # Backup connections
        backup_connections(backup_prefix)
        
        # Backup triggers
        backup_triggers(backup_prefix)
        
        # Backup workflows
        backup_workflows(backup_prefix)
        
        print(f"Glue backup completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Glue backup completed successfully',
                'backup_location': f"s3://{BACKUP_BUCKET}/{backup_prefix}",
                'timestamp': timestamp
            })
        }
    
    except Exception as e:
        print(f"Error during backup: {str(e)}")
        raise


def backup_databases(backup_prefix: str):
    """Backup all Glue databases, tables, and partitions"""
    print("Backing up databases...")
    
    databases = []
    paginator = glue_client.get_paginator('get_databases')
    
    for page in paginator.paginate():
        for database in page['DatabaseList']:
            db_name = database['Name']
            print(f"  Backing up database: {db_name}")
            
            # Get database details
            db_detail = {
                'database': database,
                'tables': []
            }
            
            # Get all tables in the database
            table_paginator = glue_client.get_paginator('get_tables')
            for table_page in table_paginator.paginate(DatabaseName=db_name):
                for table in table_page['TableList']:
                    table_name = table['Name']
                    print(f"    Backing up table: {table_name}")
                    
                    # Get partitions for the table
                    partitions = []
                    try:
                        partition_paginator = glue_client.get_paginator('get_partitions')
                        for partition_page in partition_paginator.paginate(
                            DatabaseName=db_name,
                            TableName=table_name
                        ):
                            partitions.extend(partition_page['Partitions'])
                    except glue_client.exceptions.EntityNotFoundException:
                        # Table has no partitions
                        pass
                    
                    table_detail = {
                        'table': table,
                        'partitions': partitions
                    }
                    db_detail['tables'].append(table_detail)
            
            databases.append(db_detail)
    
    # Save to S3
    save_to_s3(
        data=databases,
        key=f"{backup_prefix}/databases.json"
    )
    print(f"Backed up {len(databases)} databases")


def backup_crawlers(backup_prefix: str):
    """Backup all Glue crawlers"""
    print("Backing up crawlers...")
    
    crawlers = []
    paginator = glue_client.get_paginator('get_crawlers')
    
    for page in paginator.paginate():
        crawlers.extend(page['Crawlers'])
    
    save_to_s3(
        data=crawlers,
        key=f"{backup_prefix}/crawlers.json"
    )
    print(f"Backed up {len(crawlers)} crawlers")


def backup_jobs(backup_prefix: str):
    """Backup all Glue jobs"""
    print("Backing up jobs...")
    
    jobs = []
    paginator = glue_client.get_paginator('get_jobs')
    
    for page in paginator.paginate():
        jobs.extend(page['Jobs'])
    
    save_to_s3(
        data=jobs,
        key=f"{backup_prefix}/jobs.json"
    )
    print(f"Backed up {len(jobs)} jobs")


def backup_classifiers(backup_prefix: str):
    """Backup all Glue classifiers"""
    print("Backing up classifiers...")
    
    classifiers = []
    paginator = glue_client.get_paginator('get_classifiers')
    
    for page in paginator.paginate():
        classifiers.extend(page['Classifiers'])
    
    save_to_s3(
        data=classifiers,
        key=f"{backup_prefix}/classifiers.json"
    )
    print(f"Backed up {len(classifiers)} classifiers")


def backup_connections(backup_prefix: str):
    """Backup all Glue connections"""
    print("Backing up connections...")
    
    try:
        connections = []
        paginator = glue_client.get_paginator('get_connections')
        
        for page in paginator.paginate():
            connections.extend(page['ConnectionList'])
        
        save_to_s3(
            data=connections,
            key=f"{backup_prefix}/connections.json"
        )
        print(f"Backed up {len(connections)} connections")
    except Exception as e:
        print(f"Warning: Could not backup connections: {str(e)}")


def backup_triggers(backup_prefix: str):
    """Backup all Glue triggers"""
    print("Backing up triggers...")
    
    try:
        triggers = []
        paginator = glue_client.get_paginator('get_triggers')
        
        for page in paginator.paginate():
            triggers.extend(page['Triggers'])
        
        save_to_s3(
            data=triggers,
            key=f"{backup_prefix}/triggers.json"
        )
        print(f"Backed up {len(triggers)} triggers")
    except Exception as e:
        print(f"Warning: Could not backup triggers: {str(e)}")


def backup_workflows(backup_prefix: str):
    """Backup all Glue workflows"""
    print("Backing up workflows...")
    
    try:
        workflows = []
        paginator = glue_client.get_paginator('list_workflows')
        
        for page in paginator.paginate():
            workflow_names = page['Workflows']
            
            for workflow_name in workflow_names:
                response = glue_client.get_workflow(Name=workflow_name)
                workflows.append(response['Workflow'])
        
        save_to_s3(
            data=workflows,
            key=f"{backup_prefix}/workflows.json"
        )
        print(f"Backed up {len(workflows)} workflows")
    except Exception as e:
        print(f"Warning: Could not backup workflows: {str(e)}")


def save_to_s3(data: Any, key: str):
    """Save data to S3 bucket"""
    try:
        s3_client.put_object(
            Bucket=BACKUP_BUCKET,
            Key=key,
            Body=json.dumps(data, default=str, indent=2),
            ServerSideEncryption='AES256',
            ContentType='application/json'
        )
        print(f"  Saved to s3://{BACKUP_BUCKET}/{key}")
    except Exception as e:
        print(f"Error saving to S3: {str(e)}")
        raise
