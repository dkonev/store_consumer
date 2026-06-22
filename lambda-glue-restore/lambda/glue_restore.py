
### modules/lambda-glue-restore/lambda/glue_restore.py

import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError

glue_client = boto3.client('glue')
s3_client = boto3.client('s3')

BACKUP_BUCKET = os.environ['BACKUP_BUCKET']
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'production')

def lambda_handler(event, context):
    """
    Main Lambda handler to restore Glue Data Catalog from backup
    
    Event format:
    {
        "backup_timestamp": "2024-01-15-22-00-00",  # Optional, uses latest if not provided
        "restore_components": ["databases", "crawlers", "jobs"],  # Optional, restores all if not provided
        "overwrite": false  # Optional, default false
    }
    """
    
    backup_timestamp = event.get('backup_timestamp')
    restore_components = event.get('restore_components', ['all'])
    overwrite = event.get('overwrite', False)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'backup_timestamp': backup_timestamp,
        'restore_components': restore_components,
        'status': 'success',
        'components': {}
    }
    
    try:
        # If no backup timestamp provided, find the latest
        if not backup_timestamp:
            backup_timestamp = find_latest_backup()
            results['backup_timestamp'] = backup_timestamp
        
        backup_prefix = f"glue-backup/{ENVIRONMENT}/{backup_timestamp}"
        
        # Verify backup exists
        if not verify_backup_exists(backup_prefix):
            raise Exception(f"Backup not found at {backup_prefix}")
        
        # Restore components
        if 'all' in restore_components or 'databases' in restore_components:
            databases_restore = restore_databases(backup_prefix, overwrite)
            results['components']['databases'] = databases_restore
        
        if 'all' in restore_components or 'crawlers' in restore_components:
            crawlers_restore = restore_crawlers(backup_prefix, overwrite)
            results['components']['crawlers'] = crawlers_restore
        
        if 'all' in restore_components or 'jobs' in restore_components:
            jobs_restore = restore_jobs(backup_prefix, overwrite)
            results['components']['jobs'] = jobs_restore
        
        if 'all' in restore_components or 'classifiers' in restore_components:
            classifiers_restore = restore_classifiers(backup_prefix, overwrite)
            results['components']['classifiers'] = classifiers_restore
        
        if 'all' in restore_components or 'connections' in restore_components:
            connections_restore = restore_connections(backup_prefix, overwrite)
            results['components']['connections'] = connections_restore
        
        if 'all' in restore_components or 'triggers' in restore_components:
            triggers_restore = restore_triggers(backup_prefix, overwrite)
            results['components']['triggers'] = triggers_restore
        
        if 'all' in restore_components or 'workflows' in restore_components:
            workflows_restore = restore_workflows(backup_prefix, overwrite)
            results['components']['workflows'] = workflows_restore
        
        if 'all' in restore_components or 'security_configurations' in restore_components:
            security_configs_restore = restore_security_configurations(backup_prefix, overwrite)
            results['components']['security_configurations'] = security_configs_restore
        
        print(f"Restore completed successfully: {json.dumps(results, indent=2, default=str)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(results, default=str)
        }
        
    except Exception as e:
        error_msg = f"Restore failed: {str(e)}"
        print(error_msg)
        results['status'] = 'failed'
        results['error'] = str(e)
        
        return {
            'statusCode': 500,
            'body': json.dumps(results, default=str)
        }

def find_latest_backup():
    """
    Find the latest backup timestamp
    """
    try:
        prefix = f"glue-backup/{ENVIRONMENT}/"
        response = s3_client.list_objects_v2(
            Bucket=BACKUP_BUCKET,
            Prefix=prefix,
            Delimiter='/'
        )
        
        if 'CommonPrefixes' not in response:
            raise Exception("No backups found")
        
        # Get all backup timestamps
        timestamps = []
        for prefix_obj in response['CommonPrefixes']:
            timestamp = prefix_obj['Prefix'].split('/')[-2]
            timestamps.append(timestamp)
        
        # Return the latest timestamp
        latest = sorted(timestamps, reverse=True)[0]
        print(f"Latest backup found: {latest}")
        return latest
        
    except Exception as e:
        raise Exception(f"Error finding latest backup: {str(e)}")

def verify_backup_exists(backup_prefix):
    """
    Verify that backup exists
    """
    try:
        response = s3_client.list_objects_v2(
            Bucket=BACKUP_BUCKET,
            Prefix=backup_prefix,
            MaxKeys=1
        )
        return 'Contents' in response
    except Exception as e:
        print(f"Error verifying backup: {str(e)}")
        return False

def get_backup_data(key):
    """
    Get backup data from S3
    """
    try:
        response = s3_client.get_object(Bucket=BACKUP_BUCKET, Key=key)
        data = json.loads(response['Body'].read().decode('utf-8'))
        return data
    except Exception as e:
        print(f"Error getting backup data from {key}: {str(e)}")
        return None

def restore_databases(backup_prefix, overwrite):
    """
    Restore databases, tables, and partitions
    """
    restored_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        # Get databases backup
        databases_data = get_backup_data(f"{backup_prefix}/databases/all_databases.json")
        
        if not databases_data:
            return {
                'restored_count': 0,
                'skipped_count': 0,
                'error_count': 0,
                'status': 'no_backup_found'
            }
        
        for database_info in databases_data:
            database = database_info['database']
            database_name = database['Name']
            
            try:
                # Check if database exists
                try:
                    glue_client.get_database(Name=database_name)
                    database_exists = True
                except ClientError as e:
                    if e.response['Error']['Code'] == 'EntityNotFoundException':
                        database_exists = False
                    else:
                        raise
                
                # Create or update database
                database_input = {
                    'Name': database['Name'],
                    'Description': database.get('Description', ''),
                }
                
                if 'LocationUri' in database:
                    database_input['LocationUri'] = database['LocationUri']
                
                if 'Parameters' in database:
                    database_input['Parameters'] = database['Parameters']
                
                if database_exists:
                    if overwrite:
                        glue_client.update_database(
                            Name=database_name,
                            DatabaseInput=database_input
                        )
                        print(f"Updated database: {database_name}")
                        restored_count += 1
                    else:
                        print(f"Skipped existing database: {database_name}")
                        skipped_count += 1
                else:
                    glue_client.create_database(DatabaseInput=database_input)
                    print(f"Created database: {database_name}")
                    restored_count += 1
                
                # Restore tables
                for table_info in database_info.get('tables', []):
                    table = table_info['table']
                    table_name = table['Name']
                    
                    try:
                        # Check if table exists
                        try:
                            glue_client.get_table(DatabaseName=database_name, Name=table_name)
                            table_exists = True
                        except ClientError as e:
                            if e.response['Error']['Code'] == 'EntityNotFoundException':
                                table_exists = False
                            else:
                                raise
                        
                        # Prepare table input
                        table_input = {
                            'Name': table['Name'],
                            'StorageDescriptor': table['StorageDescriptor'],
                        }
                        
                        if 'Description' in table:
                            table_input['Description'] = table['Description']
                        
                        if 'Owner' in table:
                            table_input['Owner'] = table['Owner']
                        
                        if 'Parameters' in table:
                            table_input['Parameters'] = table['Parameters']
                        
                        if 'PartitionKeys' in table:
                            table_input['PartitionKeys'] = table['PartitionKeys']
                        
                        if 'ViewOriginalText' in table:
                            table_input['ViewOriginalText'] = table['ViewOriginalText']
                        
                        if 'ViewExpandedText' in table:
                            table_input['ViewExpandedText'] = table['ViewExpandedText']
                        
                        if 'TableType' in table:
                            table_input['TableType'] = table['TableType']
                        
                        # Create or update table
                        if table_exists:
                            if overwrite:
                                glue_client.update_table(
                                    DatabaseName=database_name,
                                    TableInput=table_input
                                )
                                print(f"Updated table: {database_name}.{table_name}")
                            else:
                                print(f"Skipped existing table: {database_name}.{table_name}")
                                skipped_count += 1
                                continue
                        else:
                            glue_client.create_table(
                                DatabaseName=database_name,
                                TableInput=table_input
                            )
                            print(f"Created table: {database_name}.{table_name}")
                        
                        # Restore partitions
                        partitions = table_info.get('partitions', [])
                        if partitions:
                            # Batch create partitions (max 100 per batch)
                            batch_size = 100
                            for i in range(0, len(partitions), batch_size):
                                batch = partitions[i:i + batch_size]
                                partition_inputs = []
                                
                                for partition in batch:
                                    partition_input = {
                                        'Values': partition['Values'],
                                        'StorageDescriptor': partition['StorageDescriptor'],
                                    }
                                    
                                    if 'Parameters' in partition:
                                        partition_input['Parameters'] = partition['Parameters']
                                    
                                    partition_inputs.append(partition_input)
                                
                                try:
                                    glue_client.batch_create_partition(
                                        DatabaseName=database_name,
                                        TableName=table_name,
                                        PartitionInputList=partition_inputs
                                    )
                                    print(f"Created {len(partition_inputs)} partitions for {database_name}.{table_name}")
                                except ClientError as e:
                                    if e.response['Error']['Code'] == 'AlreadyExistsException':
                                        print(f"Some partitions already exist for {database_name}.{table_name}")
                                    else:
                                        raise
                        
                    except Exception as e:
                        print(f"Error restoring table {database_name}.{table_name}: {str(e)}")
                        error_count += 1
                
            except Exception as e:
                print(f"Error restoring database {database_name}: {str(e)}")
                error_count += 1
        
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'success'
        }
        
    except Exception as e:
        print(f"Error restoring databases: {str(e)}")
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'failed',
            'error': str(e)
        }

def restore_crawlers(backup_prefix, overwrite):
    """
    Restore crawlers
    """
    restored_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        crawlers_data = get_backup_data(f"{backup_prefix}/crawlers/all_crawlers.json")
        
        if not crawlers_data:
            return {
                'restored_count': 0,
                'skipped_count': 0,
                'error_count': 0,
                'status': 'no_backup_found'
            }
        
        for crawler in crawlers_data:
            crawler_name = crawler['Name']
            
            try:
                # Check if crawler exists
                try:
                    glue_client.get_crawler(Name=crawler_name)
                    crawler_exists = True
                except ClientError as e:
                    if e.response['Error']['Code'] == 'EntityNotFoundException':
                        crawler_exists = False
                    else:
                        raise
                
                # Prepare crawler configuration
                crawler_config = {
                    'Name': crawler['Name'],
                    'Role': crawler['Role'],
                    'Targets': crawler['Targets'],
                }
                
                if 'DatabaseName' in crawler:
                    crawler_config['DatabaseName'] = crawler['DatabaseName']
                
                if 'Description' in crawler:
                    crawler_config['Description'] = crawler['Description']
                
                if 'Schedule' in crawler:
                    crawler_config['Schedule'] = crawler['Schedule']
                
                if 'Classifiers' in crawler:
                    crawler_config['Classifiers'] = crawler['Classifiers']
                
                if 'TablePrefix' in crawler:
                    crawler_config['TablePrefix'] = crawler['TablePrefix']
                
                if 'SchemaChangePolicy' in crawler:
                    crawler_config['SchemaChangePolicy'] = crawler['SchemaChangePolicy']
                
                if 'Configuration' in crawler:
                    crawler_config['Configuration'] = crawler['Configuration']
                
                # Create or update crawler
                if crawler_exists:
                    if overwrite:
                        glue_client.update_crawler(**crawler_config)
                        print(f"Updated crawler: {crawler_name}")
                        restored_count += 1
                    else:
                        print(f"Skipped existing crawler: {crawler_name}")
                        skipped_count += 1
                else:
                    glue_client.create_crawler(**crawler_config)
                    print(f"Created crawler: {crawler_name}")
                    restored_count += 1
                
            except Exception as e:
                print(f"Error restoring crawler {crawler_name}: {str(e)}")
                error_count += 1
        
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'success'
        }
        
    except Exception as e:
        print(f"Error restoring crawlers: {str(e)}")
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'failed',
            'error': str(e)
        }

def restore_jobs(backup_prefix, overwrite):
    """
    Restore Glue jobs
    """
    restored_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        jobs_data = get_backup_data(f"{backup_prefix}/jobs/all_jobs.json")
        
        if not jobs_data:
            return {
                'restored_count': 0,
                'skipped_count': 0,
                'error_count': 0,
                'status': 'no_backup_found'
            }
        
        for job in jobs_data:
            job_name = job['Name']
            
            try:
                # Check if job exists
                try:
                    glue_client.get_job(JobName=job_name)
                    job_exists = True
                except ClientError as e:
                    if e.response['Error']['Code'] == 'EntityNotFoundException':
                        job_exists = False
                    else:
                        raise
                
                # Prepare job configuration
                job_config = {
                    'Name': job['Name'],
                    'Role': job['Role'],
                    'Command': job['Command'],
                }
                
                if 'Description' in job:
                    job_config['Description'] = job['Description']
                
                if 'LogUri' in job:
                    job_config['LogUri'] = job['LogUri']
                
                if 'ExecutionProperty' in job:
                    job_config['ExecutionProperty'] = job['ExecutionProperty']
                
                if 'DefaultArguments' in job:
                    job_config['DefaultArguments'] = job['DefaultArguments']
                
                if 'Connections' in job:
                    job_config['Connections'] = job['Connections']
                
                if 'MaxRetries' in job:
                    job_config['MaxRetries'] = job['MaxRetries']
                
                if 'Timeout' in job:
                    job_config['Timeout'] = job['Timeout']
                
                if 'MaxCapacity' in job:
                    job_config['MaxCapacity'] = job['MaxCapacity']
                
                if 'WorkerType' in job:
                    job_config['WorkerType'] = job['WorkerType']
                
                if 'NumberOfWorkers' in job:
                    job_config['NumberOfWorkers'] = job['NumberOfWorkers']
                
                if 'SecurityConfiguration' in job:
                    job_config['SecurityConfiguration'] = job['SecurityConfiguration']
                
                if 'GlueVersion' in job:
                    job_config['GlueVersion'] = job['GlueVersion']
                
                # Create or update job
                if job_exists:
                    if overwrite:
                        job_update = {k: v for k, v in job_config.items() if k != 'Name'}
                        glue_client.update_job(JobName=job_name, JobUpdate=job_update)
                        print(f"Updated job: {job_name}")
                        restored_count += 1
                    else:
                        print(f"Skipped existing job: {job_name}")
                        skipped_count += 1
                else:
                    glue_client.create_job(**job_config)
                    print(f"Created job: {job_name}")
                    restored_count += 1
                
            except Exception as e:
                print(f"Error restoring job {job_name}: {str(e)}")
                error_count += 1
        
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'success'
        }
        
    except Exception as e:
        print(f"Error restoring jobs: {str(e)}")
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'failed',
            'error': str(e)
        }

def restore_classifiers(backup_prefix, overwrite):
    """
    Restore classifiers
    """
    restored_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        classifiers_data = get_backup_data(f"{backup_prefix}/classifiers/all_classifiers.json")
        
        if not classifiers_data:
            return {
                'restored_count': 0,
                'skipped_count': 0,
                'error_count': 0,
                'status': 'no_backup_found'
            }
        
        for classifier in classifiers_data:
            # Determine classifier type and name
            classifier_name = None
            classifier_type = None
            
            if 'GrokClassifier' in classifier:
                classifier_name = classifier['GrokClassifier']['Name']
                classifier_type = 'Grok'
            elif 'XMLClassifier' in classifier:
                classifier_name = classifier['XMLClassifier']['Name']
                classifier_type = 'XML'
            elif 'JsonClassifier' in classifier:
                classifier_name = classifier['JsonClassifier']['Name']
                classifier_type = 'Json'
            elif 'CsvClassifier' in classifier:
                classifier_name = classifier['CsvClassifier']['Name']
                classifier_type = 'Csv'
            
            if not classifier_name:
                continue
            
            try:
                # Check if classifier exists
                try:
                    glue_client.get_classifier(Name=classifier_name)
                    classifier_exists = True
                except ClientError as e:
                    if e.response['Error']['Code'] == 'EntityNotFoundException':
                        classifier_exists = False
                    else:
                        raise
                
                # Create or update classifier
                if classifier_exists:
                    if overwrite:
                        if classifier_type == 'Grok':
                            glue_client.update_classifier(GrokClassifier=classifier['GrokClassifier'])
                        elif classifier_type == 'XML':
                            glue_client.update_classifier(XMLClassifier=classifier['XMLClassifier'])
                        elif classifier_type == 'Json':
                            glue_client.update_classifier(JsonClassifier=classifier['JsonClassifier'])
                        elif classifier_type == 'Csv':
                            glue_client.update_classifier(CsvClassifier=classifier['CsvClassifier'])
                        
                        print(f"Updated classifier: {classifier_name}")
                        restored_count += 1
                    else:
                        print(f"Skipped existing classifier: {classifier_name}")
                        skipped_count += 1
                else:
                    if classifier_type == 'Grok':
                        glue_client.create_classifier(GrokClassifier=classifier['GrokClassifier'])
                    elif classifier_type == 'XML':
                        glue_client.create_classifier(XMLClassifier=classifier['XMLClassifier'])
                    elif classifier_type == 'Json':
                        glue_client.create_classifier(JsonClassifier=classifier['JsonClassifier'])
                    elif classifier_type == 'Csv':
                        glue_client.create_classifier(CsvClassifier=classifier['CsvClassifier'])
                    
                    print(f"Created classifier: {classifier_name}")
                    restored_count += 1
                
            except Exception as e:
                print(f"Error restoring classifier {classifier_name}: {str(e)}")
                error_count += 1
        
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'success'
        }
        
    except Exception as e:
        print(f"Error restoring classifiers: {str(e)}")
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'failed',
            'error': str(e)
        }

def restore_connections(backup_prefix, overwrite):
    """
    Restore connections
    """
    restored_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        connections_data = get_backup_data(f"{backup_prefix}/connections/all_connections.json")
        
        if not connections_data:
            return {
                'restored_count': 0,
                'skipped_count': 0,
                'error_count': 0,
                'status': 'no_backup_found'
            }
        
        for connection in connections_data:
            connection_name = connection['Name']
            
            try:
                # Check if connection exists
                try:
                    glue_client.get_connection(Name=connection_name)
                    connection_exists = True
                except ClientError as e:
                    if e.response['Error']['Code'] == 'EntityNotFoundException':
                        connection_exists = False
                    else:
                        raise
                
                # Prepare connection input
                connection_input = {
                    'Name': connection['Name'],
                    'ConnectionType': connection['ConnectionType'],
                    'ConnectionProperties': connection['ConnectionProperties'],
                }
                
                if 'Description' in connection:
                    connection_input['Description'] = connection['Description']
                
                if 'PhysicalConnectionRequirements' in connection:
                    connection_input['PhysicalConnectionRequirements'] = connection['PhysicalConnectionRequirements']
                
                # Create or update connection
                if connection_exists:
                    if overwrite:
                        glue_client.update_connection(
                            Name=connection_name,
                            ConnectionInput=connection_input
                        )
                        print(f"Updated connection: {connection_name}")
                        restored_count += 1
                    else:
                        print(f"Skipped existing connection: {connection_name}")
                        skipped_count += 1
                else:
                    glue_client.create_connection(ConnectionInput=connection_input)
                    print(f"Created connection: {connection_name}")
                    restored_count += 1
                
            except Exception as e:
                print(f"Error restoring connection {connection_name}: {str(e)}")
                error_count += 1
        
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'success'
        }
        
    except Exception as e:
        print(f"Error restoring connections: {str(e)}")
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'failed',
            'error': str(e)
        }

def restore_triggers(backup_prefix, overwrite):
    """
    Restore triggers
    """
    restored_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        triggers_data = get_backup_data(f"{backup_prefix}/triggers/all_triggers.json")
        
        if not triggers_data:
            return {
                'restored_count': 0,
                'skipped_count': 0,
                'error_count': 0,
                'status': 'no_backup_found'
            }
        
        for trigger in triggers_data:
            trigger_name = trigger['Name']
            
            try:
                # Check if trigger exists
                try:
                    glue_client.get_trigger(Name=trigger_name)
                    trigger_exists = True
                except ClientError as e:
                    if e.response['Error']['Code'] == 'EntityNotFoundException':
                        trigger_exists = False
                    else:
                        raise
                
                # Prepare trigger configuration
                trigger_config = {
                    'Name': trigger['Name'],
                    'Type': trigger['Type'],
                    'Actions': trigger['Actions'],
                }
                
                if 'Description' in trigger:
                    trigger_config['Description'] = trigger['Description']
                
                if 'Schedule' in trigger:
                    trigger_config['Schedule'] = trigger['Schedule']
                
                if 'Predicate' in trigger:
                    trigger_config['Predicate'] = trigger['Predicate']
                
                if 'WorkflowName' in trigger:
                    trigger_config['WorkflowName'] = trigger['WorkflowName']
                
                # Create or update trigger
                if trigger_exists:
                    if overwrite:
                        trigger_update = {k: v for k, v in trigger_config.items() if k != 'Name'}
                        glue_client.update_trigger(Name=trigger_name, TriggerUpdate=trigger_update)
                        print(f"Updated trigger: {trigger_name}")
                        restored_count += 1
                    else:
                        print(f"Skipped existing trigger: {trigger_name}")
                        skipped_count += 1
                else:
                    glue_client.create_trigger(**trigger_config, StartOnCreation=False)
                    print(f"Created trigger: {trigger_name}")
                    restored_count += 1
                
            except Exception as e:
                print(f"Error restoring trigger {trigger_name}: {str(e)}")
                error_count += 1
        
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'success'
        }
        
    except Exception as e:
        print(f"Error restoring triggers: {str(e)}")
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'failed',
            'error': str(e)
        }

def restore_workflows(backup_prefix, overwrite):
    """
    Restore workflows
    """
    restored_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        workflows_data = get_backup_data(f"{backup_prefix}/workflows/all_workflows.json")
        
        if not workflows_data:
            return {
                'restored_count': 0,
                'skipped_count': 0,
                'error_count': 0,
                'status': 'no_backup_found'
            }
        
        for workflow in workflows_data:
            workflow_name = workflow['Name']
            
            try:
                # Check if workflow exists
                try:
                    glue_client.get_workflow(Name=workflow_name)
                    workflow_exists = True
                except ClientError as e:
                    if e.response['Error']['Code'] == 'EntityNotFoundException':
                        workflow_exists = False
                    else:
                        raise
                
                # Prepare workflow configuration
                workflow_config = {
                    'Name': workflow['Name'],
                }
                
                if 'Description' in workflow:
                    workflow_config['Description'] = workflow['Description']
                
                if 'DefaultRunProperties' in workflow:
                    workflow_config['DefaultRunProperties'] = workflow['DefaultRunProperties']
                
                # Create or update workflow
                if workflow_exists:
                    if overwrite:
                        workflow_update = {k: v for k, v in workflow_config.items() if k != 'Name'}
                        glue_client.update_workflow(Name=workflow_name, **workflow_update)
                        print(f"Updated workflow: {workflow_name}")
                        restored_count += 1
                    else:
                        print(f"Skipped existing workflow: {workflow_name}")
                        skipped_count += 1
                else:
                    glue_client.create_workflow(**workflow_config)
                    print(f"Created workflow: {workflow_name}")
                    restored_count += 1
                
            except Exception as e:
                print(f"Error restoring workflow {workflow_name}: {str(e)}")
                error_count += 1
        
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'success'
        }
        
    except Exception as e:
        print(f"Error restoring workflows: {str(e)}")
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'failed',
            'error': str(e)
        }

def restore_security_configurations(backup_prefix, overwrite):
    """
    Restore security configurations
    """
    restored_count = 0
    skipped_count = 0
    error_count = 0
    
    try:
        security_configs_data = get_backup_data(f"{backup_prefix}/security_configurations/all_security_configurations.json")
        
        if not security_configs_data:
            return {
                'restored_count': 0,
                'skipped_count': 0,
                'error_count': 0,
                'status': 'no_backup_found'
            }
        
        for config in security_configs_data:
            config_name = config['Name']
            
            try:
                # Check if security configuration exists
                try:
                    glue_client.get_security_configuration(Name=config_name)
                    config_exists = True
                except ClientError as e:
                    if e.response['Error']['Code'] == 'EntityNotFoundException':
                        config_exists = False
                    else:
                        raise
                
                # Security configurations cannot be updated, only created
                if config_exists:
                    print(f"Skipped existing security configuration: {config_name}")
                    skipped_count += 1
                else:
                    glue_client.create_security_configuration(
                        Name=config['Name'],
                        EncryptionConfiguration=config['EncryptionConfiguration']
                    )
                    print(f"Created security configuration: {config_name}")
                    restored_count += 1
                
            except Exception as e:
                print(f"Error restoring security configuration {config_name}: {str(e)}")
                error_count += 1
        
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'success'
        }
        
    except Exception as e:
        print(f"Error restoring security configurations: {str(e)}")
        return {
            'restored_count': restored_count,
            'skipped_count': skipped_count,
            'error_count': error_count,
            'status': 'failed',
            'error': str(e)
        }