from main import bucket_generator, get_s3_resource


def disable_versioning_logging(bucket_name):
    """Disables versioning and logging on bucket_name

    :param bucket_name: Name of bucket which should have versioning and
                        logging disabled.
    :type bucket_name: str

    """
    # Disable logging
    bucket_logging = get_s3_resource().BucketLogging(bucket_name)
    bucket_logging.put(BucketLoggingStatus={})
    # Suspend versioning
    get_s3_resource().BucketVersioning(bucket_name).suspend()


if __name__ == '__main__':
    bg = bucket_generator()
    while True:
        bucket = next(bg, None)
        if bucket:
            print bucket.name
            disable_versioning_logging(bucket.name)
        else:
            break
