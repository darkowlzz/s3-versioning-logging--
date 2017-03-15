# Findings


## AWS CLI cmds

### Logging

`$ aws s3api put-bucket-logging --bucket <source_bucket_name> --bucket-logging-status file://logging.json`

`$ aws s3api get-bucket-logging --bucket=<source_bucket_name>`

logging.json content

```
{
  "LoggingEnabled": {
    "TargetPrefix": "<source_bucket_name>/",
    "TargetBucket": "<target_bucket_name>"
  }
}
```

### Versioning

`$ aws s3api put-bucket-versioning --bucket <bucket_name> --versioning-configuration Status=Enabled`

`$ aws s3api put-bucket-versioning --bucket <bucket_name> --versioning-configuration Status=Suspended`

`$ aws s3api get-bucket-versioning --bucket=<bucket_name>`


### Boto Code

```
import boto3

s3 = boto3.resource('s3')
bucket_logging = s3.BucketLogging('<source_bucket_name>')
bucket_logging.put(BucketLoggingStatus={'LoggingEnabled': {'TargetBucket': '<target_bucket_name>', 'TargetPrefix': '<source_bucket_name>/'}})

b = s3.BucketVersioning('<bucket_name>')
b.enable()
```
