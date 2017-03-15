import boto3
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


s3_client = None
s3_resource = None


def handler(event, context):
    """Lambda handler"""
    return


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
    return response['LocationConstraint']


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


def enable_logging(source_bucket_name, target_bucket_name):
    """Enable logging for a source bucket in a target bucket with prefix
    as the name of source bucket.

    :param source_bucket_name: Bucket in which logging has to be enabled.
    :type source_bucket_name: str

    :param target_bucket_name: Bucket where the logs would be stored.
    :type target_bucket_name: str

    """
    pass
