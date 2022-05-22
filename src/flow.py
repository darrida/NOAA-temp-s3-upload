##############################################################################
# Author: Ben Hammond
# Last Changed: 5/7/21
#
# REQUIREMENTS
# - Detailed dependencies in requirements.txt
# - Directly referenced:
#   - prefect, boto3, tqdm
#
# - Infrastructure:
#   - Prefect: Script is registered as a Prefect flow with api.prefect.io
#     - Source: https://prefect.io
#   - AWS S3: Script retrieves and creates files stored in a S3 bucket
#     - Credentials: Stored localled in default user folder created by AWS CLI
#
# DESCRIPTION
# - Uploads local NOAA temperature csv files to AWS S3 storage
# - Includes the following features (to assist with handling the download of 538,000 [34gb] csv files):
#   - Continue Downloading: If the download is interrupted, the script can pick up where it left off
#   - Find Gaps: If an indidivual file is added to the source for any year, or removed from the server
#     for any year, the script can quickly scan all data in both locations, find the differences
#     and download the missing file(s)
# - Map: Uses map over a list of folders to upload files from each folder in a distributed/parallel fashion
##############################################################################
from functools import partial
from pathlib import Path
from prefect import flow
from prefect.task_runners import DaskTaskRunner
from src.tasks import load_year_files, aws_local_folder_difference, s3_list_folders, local_list_folders


@flow(name="NOAA files: AWS Upload", task_runner=DaskTaskRunner())
def main():
    working_dir = str(Path("/home/ben/github/NOAA-file-download/local_data/global-summary-of-the-day-archive/"))
    region_name = "us-east-1"
    bucket_name = "noaa-temperature-data"
    chunks = 10
    all_folders = True
    t1_local_folders = local_list_folders(working_dir)
    t2_aws_folders = s3_list_folders(region_name, bucket_name)
    t3_years = aws_local_folder_difference(t2_aws_folders, t1_local_folders, all_folders)
    for year in t3_years.result():
        partial_year = [year[i:i + chunks] for i in range(0, len(year), chunks)]
        for y in partial_year:
            load_year_files(y, region_name, bucket_name, working_dir)


if __name__ == "__main__":
    main()
