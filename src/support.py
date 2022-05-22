from datetime import datetime
from pathlib import Path
from prefect import get_run_logger
import boto3
from botocore.exceptions import ClientError
from tqdm import tqdm


def initialize_s3_client(region_name: str) -> boto3.client:
    return boto3.client("s3", region_name=region_name)


def aws_load_files_year(s3_client: boto3.client, bucket: str, year: str, local_dir: str, files_l: list) -> int:
    """Loads set of csv files into aws

    Args:
        s3_client: initated boto3 s3_client object
        bucket (str): target AWS bucket
        year (str): year to check difference for
        local_dir (str): local directory with year folders
        files (list): filenames to upload

    Return (tuple): Number of upload success (index 0) and failures (index 1)
    """
    upload_count, failed_count = 0, 0
    for csv_file in tqdm(files_l, desc=f"{year} | Total: {len(files_l)}"):
        result = s3_upload_file(
            s3_client=s3_client,
            file_name=str(Path(local_dir) / year / 'data' / csv_file),
            bucket=bucket,
            object_name=f"{year}/{csv_file}",
        )
        if not result:
            with open("failed.txt", "a") as f:
                f.write(f"{year} | {csv_file} | {datetime.now()}")
                f.write("\n")
            failed_count += 1
            continue
        upload_count += 1
    return upload_count, failed_count



def s3_upload_file(s3_client: boto3.client, file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    Args:
        s3_client: initated boto3 s3_client object
        file_name (str): File to upload
        bucket (str): target AWS bucket
        object_name (str): S3 object name. If not specified then file_name is used [Optional]

    Return (bool): True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    logger = get_run_logger()
    if object_name is None:
        object_name = file_name

    # Upload the file
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logger.error(e)
        # logging.error(e)
        return False
    return True
