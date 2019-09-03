#!/usr/bin/env python3

import boto3
import re
import multiprocessing as mp
import argparse
import collections


class S3:
    def __init__(self, storage_type, bucket_name, regions, prefix, display_size, outfile):
        self.s3_resource = boto3.resource('s3')
        self.s3_client = boto3.client('s3')
        self.paginator = self.s3_client.get_paginator('list_objects')
        self.buckets_all = self.s3_resource.buckets.all()

        self.storage_type = storage_type
        self.filter_bucket_name = bucket_name
        self.regions = self._regions_to_list(regions)
        self.prefix = prefix
        self.display = display_size.upper() if display_size else 'B'
        self.size_options = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        self.stats_size_total = 0
        self.stats_size_per_bucket = collections.defaultdict(int)
        self.outfile = outfile

    @staticmethod
    def _regions_to_list(regions):
        """
        This method converts comma separated string into list to be used to filter by region.
        :param regions:
        :return: list with regions
        """
        if regions:
            return {reg.strip() for reg in regions.split(',')}
        else:
            return None

    @staticmethod
    def _convert_filter_pattern(filter_pattern):
        """
        This method removes s3:// from prefix, if it exists.
        :param filter_pattern:
        :return: compiled regex pattern
        """
        # s3://
        fp = filter_pattern.replace('s3://', '')
        fp = fp.replace('*', '.*')
        return re.compile(fp)

    def _get_bucket_encryption(self, bucket):
        """
        Extracts encryption type from get_bucket_encryption
        :param bucket: name of bucket
        :return: encryption type
        """
        try:
            bucket_info = self.s3_client.get_bucket_encryption(Bucket=bucket)
            encrypt = bucket_info['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm']
            return encrypt
        except:
            return 'Disabled'

    def process(self):
        """
        This method scans all buckets, which are grouped by region and then it will write the results to files
        :return: None
        """
        buckets_list = self._get_buckets_list()
        stats_total_size = 0
        stats_per_bucket_size = collections.defaultdict(list)

        with open(self.outfile, 'w') as f_out:
            for region, buckets in buckets_list.items():
                manager = mp.Manager()
                output = manager.list()
                proc = [mp.Process(target=self._get_buckets_info, args=(bucket, output)) for bucket in buckets]
                for p in proc:
                    p.start()
                for p in proc:
                    p.join()

                if len(output) == 0:
                    continue

                f_out.write('\nRegion: {}\n'.format(region))
                for output_buckets in output:
                    for bucket_name, values in output_buckets.items():
                        f_out.write('    Bucket: {}\n'.format(bucket_name))
                        f_out.write('        Creation Date: {}\n'.format(values['Creation Date']))
                        f_out.write('        Encryption: {}\n'.format(values['Encryption']))
                        f_out.write('        Most Recent File: {}\n'.format(values['Most Recent File']))
                        f_out.write('        Number of Files: {}\n'.format(values['Number of Files']))
                        for storage_type, storage_value in values['Storage by Type'].items():
                            f_out.write('            {}: {}\n'.format(storage_type, storage_value))

                        f_out.write('        Total Size: {}\n'.format(self._display_size(values['Total Size'],
                                                                      self.display)))
                    stats_total_size += values['Total Size']
                    stats_per_bucket_size[values['Total Size']].append(bucket_name)

        self._output_stats(stats_per_bucket_size, stats_total_size)

        print('All results are saved in "{0}" and "{0}.stats"'.format(self.outfile))

    def _get_buckets_list(self):
        """
        Creates a dict with region as key and a list with all buckets as value
        :return: dict
        """
        buckets_dict = collections.defaultdict(list)

        for bucket in self.s3_resource.buckets.all():
            # us-east-1 is the default region
            region = self.s3_client.get_bucket_location(Bucket=bucket.name)['LocationConstraint'] or 'us-east-1'

            if self.regions and region not in self.regions:
                continue
            else:
                buckets_dict[region].append(bucket)

        return buckets_dict

    def _get_buckets_info(self, bucket, output):
        """
        This method gets all keys (files) from a bucket and extracts information about each one of them
        :param bucket: bucket name
        :param bucket_output: list with all outputs from multiprocess
        :return: output list or None if self.filter_bucket_name is True and Bucket name is not the same as
        self.filter_bucket_name
        """

        # Filter by bucket name:
        if self.filter_bucket_name and bucket.name != self.filter_bucket_name:
            return None

        keys_output = []
        most_recent_key = {'date': None, 'name': None}
        number_of_files = 0
        total_size = 0
        storage_counter_by_type = collections.defaultdict(int)
        storage_counter_total = 0

        if self.prefix:
            operation_parameters = {'Bucket': bucket.name, 'Prefix': self.prefix}
        else:
            operation_parameters = {'Bucket': bucket.name}

        page_iterator = self.paginator.paginate(**operation_parameters)
        for page in page_iterator:

            if 'Contents' not in page:
                continue

            for key in page['Contents']:
                key_dict = {'key_name': key['Key'],  'key_size': key['Size'],
                            'key_lastmod': key['LastModified'], 'key_storage': key['StorageClass']}

                if self.storage_type and self.storage_type != key['StorageClass']:
                    continue

                keys_output.append(key_dict)

        for item in keys_output:
            if most_recent_key['date'] is None or item['key_lastmod'] > most_recent_key['date']:
                most_recent_key.update({'date': item['key_lastmod'], 'name': item['key_name']})
            if item['key_size'] > 0:
                # directories have key_size == 0
                total_size += item['key_size']
                number_of_files += 1
                storage_counter_by_type[item['key_storage']] += 1
                storage_counter_total += 1

        output.append(
            {
                bucket.name: {
                    'Creation Date': self.s3_resource.Bucket(bucket.name).creation_date.ctime(),
                    'Encryption': self._get_bucket_encryption(bucket.name),
                    'Total Size': total_size,
                    'Number of Files': number_of_files,
                    'Storage by Type': self._stotage_by_type(storage_counter_by_type, storage_counter_total),
                    'Most Recent File': '{} - {}'.format(most_recent_key['name'], most_recent_key['date']),
                }
            }
        )

    @staticmethod
    def _stotage_by_type(storage_counter_by_type, storage_counter_total):
        """
        This method provides stats regarding files / storage type
        :param storage_counter_by_type:
        :param storage_counter_total:
        :return: dict
        """
        storage_tmp_dict = {}
        for storage_key, storage_value in sorted(storage_counter_by_type.items()):
            value = '{}% ({} {})'.format(
                round(100 * storage_value / storage_counter_total, 2),
                storage_value,
                'files' if storage_value > 1 else 'file'
            )
            storage_tmp_dict[storage_key] = value

        return storage_tmp_dict

    def _display_size(self, key_size, display_size):
        """
        Converts bytes into selected display format
        :param key_size: bytes
        :return: string with formatted size
        """

        if display_size == 'B':
            return key_size

        power = 10 * self.size_options.index(display_size)
        denominator = 2 ** power

        return '{}{}'.format(round(key_size / float(denominator), 1), display_size)

    def _output_stats(self, stats_per_bucket_size, stats_total_size):
        """
        This method writes stats to file
        :param stats_per_bucket_size:
        :param stats_total_size:
        :return: None
        """
        with open(self.outfile + '.stats', 'w') as f_out:
            for size in sorted(stats_per_bucket_size.keys(), reverse=True):
                for bucket_name in stats_per_bucket_size[size]:
                    if stats_total_size > 0:
                        f_out.write('{} - {}% {}\n'.format(bucket_name, round(100*size/stats_total_size, 2), size))


def parse_arguments():
    """

    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t', '--storage_type',
        help='Filter by storage type (STANDARD, STANDARD_IA, INTELLIGENT_TIERING, ONEZONE_IA, GLACIER, DEEP_ARCHIVE)')
    parser.add_argument(
        '-b', '--bucket_name',
        help='Filter by bucket name')
    parser.add_argument(
        '-r', '--regions',
        help='Filter by region, separated by comma')
    parser.add_argument(
        '-p', '--prefix',
        help='Filter by prefix, ex: s3://mybucket/Folder/SubFolder/log')
    parser.add_argument(
        '-d', '--display_size',
        help='Display size: B, KB, MB, TB. Default: Bytes')
    parser.add_argument(
        '-o', '--outfile',
        help='Output results to file', required=True)
    return parser.parse_args()
    

def main(args):
    """

    :param args:
    :return:
    """
    p1 = S3(args.storage_type, args.bucket_name, args.regions, args.prefix, args.display_size, args.outfile)
    p1.process()


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
