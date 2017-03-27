#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import boto3
import logging
from botocore.exceptions import ClientError


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

s3_client = None
s3_resource = None
IGNORE_BUCKETS = []


def handle(event, context):
    """Lambda handler"""
    bucket_list, target_bucket = initialize()
    start_versioning_logging(bucket_list, target_bucket)

    return


def initialize():
    """Initializes source bucket and target bucket list from envionment
    and returns them.

    :return: Tuple of source and target buckets (source, target)
    :rtype: tuple

    """
    # Source bucket list
    if 'SOURCE_BUCKETS' in os.environ:
        source_bucket_list = os.getenv('SOURCE_BUCKETS')
        bucket_list = [x.strip() for x in source_bucket_list.split(',')]
    else:
        bucket_list = None

    # Target buckets
    if 'TARGET_BUCKET' in os.environ:
        target_bucket = os.getenv('TARGET_BUCKET')
    else:
        target_bucket = None

    # Ignore buckets
    global IGNORE_BUCKETS
    if 'IGNORE_BUCKETS' in os.environ:
        ignore_bucket_list = os.getenv('IGNORE_BUCKETS')
        IGNORE_BUCKETS = [x.strip() for x in ignore_bucket_list.split(',')]

    return (bucket_list, target_bucket)


def get_s3_client():
    global s3_client
    if s3_client is None:
        s3_client = boto3.client('s3')
    return s3_client


def get_s3_resource():
    global s3_resource
    if s3_resource is None:
        s3_resource = boto3.resource('s3')
    return s3_resource


def get_region_name(bucket_name):
    """Returns AWS region name, given a bucket name.

    :param bucket_name: Name of a S3 bucket.
    :type bucket_name: str

    :return: AWS region name. Example: 'us-east-1'.
    :rtype: str

    """
    response = get_s3_client().get_bucket_location(Bucket=bucket_name)
    # For default region, US Standard, LocationConstraint is empty.
    # Return 'us-east-1' when no data is available.
    return response['LocationConstraint'] or 'us-east-1'


def bucket_generator():
    """Returns a s3.Bucket object generator."""
    bucket_collection = get_s3_resource().buckets.all()
    for bucket in bucket_collection:
        yield bucket


def enable_versioning(bucket_name):
    """Enables versioning in a given bucket name.

    :param bucket_name: Name of a S3 bucket.
    :type bucket_name: str

    """
    get_s3_resource().BucketVersioning(bucket_name).enable()


def enable_logging(source_bucket_name, target_bucket_name, exc_handle=True):
    """Enable logging for a source bucket in a target bucket with prefix
    as the name of source bucket.

    :param source_bucket_name: Bucket in which logging has to be enabled.
    :type source_bucket_name: str

    :param target_bucket_name: Bucket in which logs would be stored.
    :type target_bucket_name: str

    :param exc_handle: Handle exception. Used to avoid handling exception on
                       consequent execution.
    :type exc_handle: bool

    :param target_bucket_name: Bucket where the logs would be stored.
    :type target_bucket_name: str

    """
    # For given target bucket, check if the source and target are in the same
    # regioin. If not, fetch the log bucket in assigned for the region.
    # If no target bucket is provided, fetch log bucket for source bucket
    # region.
    try:
        if target_bucket_name:
            if not buckets_in_same_region(source_bucket_name,
                                          target_bucket_name):
                target_bucket_name = get_log_bucket_for_region(
                    get_region_name(source_bucket_name)
                )
        else:
            target_bucket_name = get_log_bucket_for_region(
                get_region_name(source_bucket_name)
            )
        logger.info("%s %s" % (source_bucket_name, target_bucket_name))
        get_s3_client().put_bucket_logging(
            Bucket=source_bucket_name,
            BucketLoggingStatus={
                'LoggingEnabled': {
                    'TargetBucket': target_bucket_name,
                    'TargetPrefix': source_bucket_name + '/'
                }
            }
        )
    except ClientError:
        if exc_handle:
            # For exceptions due to lack of logging permission
            set_bucket_permissions(target_bucket_name)
            # Try enabling again
            enable_logging(source_bucket_name, target_bucket_name, False)
        else:
            # Raise error when exception handling is explicitly False
            # This is helpful in avoiding recursive calls to itself on multiple
            # exceptions.
            raise


def buckets_in_same_region(x_bucket_name, y_bucket_name):
    """Checks if x and y buckets are in the same region.
    This would be used if no region-wise log buckets are specified, to validate
    if x can have y as the target logging bucket.

    :param x_bucket_name: Name of bucket x.
    :type x_bucket_name: str

    :param y_bucket_name: Name of bucket y.
    :type y_bucket_name: str

    :return: True if both the buckets are in the same region. False otherwise.
    :rtype: bool

    """
    if get_region_name(x_bucket_name) == get_region_name(y_bucket_name):
        return True
    return False


def get_log_bucket_for_region(region):
    """Returns log bucket assigned for a particular region.
    This is required to add logging target bucket in the same region bucket.

    :param region: AWS region name.
    :type region: str

    :return: Name of bucket assigned for logs in the given region.
    :rtype: str or NoneType

    """
    # Replace '-' with '_' and append to get variable name.
    env_var_name = "TARGET_" + region.replace('-', '_')
    return os.getenv(env_var_name)


def set_bucket_permissions(bucket_name):
    """Changes the bucket permissions. Adding FullControl to the owner and
    Write, ReadACP for Log Delivery group.

    :param bucket_name: Name of bucket.
    :type bucket_name: str

    """
    bucket_acl = get_s3_resource().BucketAcl(bucket_name)
    owner_id = bucket_acl.owner['ID']
    log_delivery_uri = 'http://acs.amazonaws.com/groups/s3/LogDelivery'
    bucket_acl.put(
        GrantFullControl='id=' + owner_id,
        GrantWrite='uri=' + log_delivery_uri,
        GrantReadACP='uri=' + log_delivery_uri
    )


def is_versioning_enabled(bucket_name):
    """Checks if versioning is enabled in a bucket.

    :param bucket_name: Name of bucket.
    :type bucket_name: str

    :return: Result of versioning enabled check.
    :rtype: bool

    """
    status = get_s3_client().get_bucket_versioning(Bucket=bucket_name)
    if status.get('Status') == 'Enabled':
        return True
    return False


def is_logging_enabled(bucket_name):
    """Checks if logging is enabled in a bucket.

    :param bucket_name: Name of bucket.
    :type bucket_name: str

    :return: Result of logging enabled check.
    :rtype: bool

    """
    status = get_s3_client().get_bucket_logging(Bucket=bucket_name)
    if 'LoggingEnabled' in status:
        return True
    return False


def enable_versioning_logging(bucket_name=None, target_bucket=None):
    """Enables versioning and logging for the provided bucket_name and
    with target_bucket. Ignores buckets in IGNORE_BUCKETS list.

    :param bucket_name: Name of source bucket on which versioning and logging
                        is required.
    :type bucket_name: str

    :param target_bucket: Name of target bucket, in which logs would be
                          stored.
    :type target_bucket: str

    """
    if bucket_name not in IGNORE_BUCKETS:
        if not is_versioning_enabled(bucket_name):
            enable_versioning(bucket_name)
        if not is_logging_enabled(bucket_name):
            enable_logging(bucket_name, target_bucket)


def start_versioning_logging(bucket_list=None, target_bucket=None):
    """Enables versioning and logging in bucket_list, if provided, or applies
    to all the buckets in S3.

    :param bucket_list: List of buckets for which versioning and logging should
                        be enabled. (Optional)
    :type bucket_list: list

    """
    if bucket_list:
        for bucket in bucket_list:
            # enable logging and ver
            enable_versioning_logging(bucket, target_bucket)
    else:
        bg = bucket_generator()
        while True:
            bucket = next(bg, None)
            if bucket:
                enable_versioning_logging(bucket.name, target_bucket)
            else:
                break


if __name__ == '__main__':
    handle(None, None)
