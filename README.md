# s3info

Usage:\
\
\
$ ./s3info.py -h\
usage: s3info.py [-h] [-t STORAGE_TYPE] [-b BUCKET_NAME] [-r REGIONS]\
                 [-p PREFIX] [-d DISPLAY_SIZE] -o OUTFILE\
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
        


