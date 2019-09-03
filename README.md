# s3info

Usage:\
\
\
$ ./s3info.py -h\
usage: s3info.py [-h] [-t STORAGE_TYPE] [-b BUCKET_NAME] [-r REGIONS]\
                 [-p PREFIX] [-d DISPLAY_SIZE] -o OUTFILE\
\
optional arguments:\
  -h, --help            show this help message and exit\
  -t STORAGE_TYPE, --storage_type STORAGE_TYPE\
                        Filter by storage type (STANDARD, STANDARD_IA,\
                        INTELLIGENT_TIERING, ONEZONE_IA, GLACIER,\
                        DEEP_ARCHIVE)\
  -b BUCKET_NAME, --bucket_name BUCKET_NAME\
                        Filter by bucket name\
  -r REGIONS, --regions REGIONS\
                        Filter by region, separated by comma\
  -p PREFIX, --prefix PREFIX\
                        Filter by prefix, ex:\
                        s3://mybucket/Folder/SubFolder/log\
  -d DISPLAY_SIZE, --display_size DISPLAY_SIZE\
                        Display size: B, KB, MB, TB. Default: Bytes\
  -o OUTFILE, --outfile OUTFILE\
                        Output results to file\
\
\
\
\
$ ./s3info.py -o s3_results\
\
cat s3_results\
Region: eu-west-1\
    Bucket: anotherbucketlfs\
        Creation Date: Tue Sep  3 03:29:38 2019\
        Encryption: AES256\
        Most Recent File: new_file - 2019-09-03 03:30:56+00:00\
        Number of Files: 1\
            STANDARD: 100.0% (1 file)\
        Total Size: 4194347\
\
\
$ ./s3info.py -o s3_results -d MB\
Region: eu-west-1\
    Bucket: anotherbucketlfs\
        Creation Date: Tue Sep  3 03:29:38 2019\
        Encryption: AES256\
        Most Recent File: new_file - 2019-09-03 03:30:56+00:00\
        Number of Files: 1\
            STANDARD: 100.0% (1 file)\
        Total Size: 4.0MB\
        


