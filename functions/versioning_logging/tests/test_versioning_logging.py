#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import unittest
from moto import mock_s3
from main import get_s3_client, get_s3_resource, get_region_name, \
    bucket_generator, enable_versioning, enable_logging


class TestS3(unittest.TestCase):

    @mock_s3
    def test_get_region_name(self):
        bucket_name = 'dummy-bucket-for-test'
        bucket_region = 'us-east-1'
        resource = get_s3_resource()
        bucket = resource.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': bucket_region
            }
        )
        self.assertEqual(get_region_name(bucket_name), bucket_region)

    @mock_s3
    def test_bucket_generator(self):
        test_data = [
            {
                'buckets': ['b1', 'b2', 'b3'],
            },
            {
                'buckets': []
            }
        ]
        resource = get_s3_resource()
        for data in test_data:
            # Create buckets
            for name in data['buckets']:
                bucket = resource.create_bucket(Bucket=name)
            bg = bucket_generator()
            all_buckets = []
            # Get buckets one by one
            while True:
                current_bucket = next(bg, None)
                if current_bucket is not None:
                    all_buckets.append(current_bucket.name)
                else:
                    break
            # Verify all the buckets are fetched
            self.assertEqual(data['buckets'], all_buckets)
            # Delete the buckets
            for name in data['buckets']:
                bucket = resource.Bucket(name)
                bucket.delete()

    @mock_s3
    def test_enable_versioning(self):
        test_data = [
            {
                'buckets': [
                    {
                        'name': 'bkt1',
                        'versioning_enabled': True
                    },
                    {
                        'name': 'bkt2',
                        'versioning_enabled': False
                    }
                ]
            },
            {
                'buckets': [
                    {
                        'name': 'bk1',
                        'versioning_enabled': False
                    },
                    {
                        'name': 'bk2',
                        'versioning_enabled': False
                    }
                ]
            },
            {
                'buckets': [
                    {
                        'name': 'bkt1',
                        'versioning_enabled': True
                    },
                    {
                        'name': 'bk2',
                        'versioning_enabled': True
                    }
                ]
            }
        ]
        resource = get_s3_resource()
        client = get_s3_client()
        for data in test_data:
            # Create buckets with required config
            for bkt in data['buckets']:
                bucket = resource.create_bucket(Bucket=bkt['name'])
                if bkt['versioning_enabled']:
                    resource.BucketVersioning(bkt['name']).enable()

            # Enable versioning
            for bkt in data['buckets']:
                enable_versioning(bkt['name'])

            # Check if versioning is enabled
            for bkt in data['buckets']:
                bkt_ver = client.get_bucket_versioning(Bucket=bkt['name'])
                self.assertEqual(bkt_ver['Status'], 'Enabled')
