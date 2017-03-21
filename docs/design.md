# Design

## Flow

* List of S3 buckets is obtained (from env var or fetch all the S3 buckets in
  account).
* Target bucket(s) is/are obtained from (env var).
* All the buckets are iterated one-by-one and versioning and logging is enabled
  in each one of them, considering `IGNORE_BUCKETS` list.
* This is run frequently at a given time to ensure all the buckets (including
  newly created buckets) have logging and versioning enabled as per the
  requirements for consistency.


## Source Buckets

* Source buckets are the buckets on which versioning and logging should be
  enabled.
* There are 2 ways in which source buckets are picked:
  1. From environment variables
  2. All the S3 buckets in a account
* By default, if buckets are not set in env var, all the buckets in S3 are
  picked.
* If a list of buckets is specified in env var, only those buckets are picked.
* Source bucket list in env var are set by setting env var `SOURCE_BUCKETS`,
  value being a comma separated list of bucket names.


## Target Buckets

* Target buckets are the buckets that would store the logs, when logging is
  enabled, for various buckets.
* Target buckets can be specified in 2 forms:
  1. Region-wise target bucket
  2. Single target bucket
* Region-wise target buckets are set in env var with name prefix `TARGET_`.
  Example: `TARGET_ap_southeast_1`, `TARGET_us_east_1`, etc.
* Single target bucket is set with env var `TARGET_BUCKET`.
* If all the buckets in source bucket list are in the same region, single target
  bucket could be used.
* If there source buckets belonging to different AWS regions, region wise
  target buckets should be set.


## Ignore Buckets

* Ignore buckets are the buckets that should be ignore. This could also include
  the buckets that contain logs of other buckets.
* This should be specified as a comma separated list of bucket names.
* All the buckets in this list would be ignored by this function.


## Detailed Flow

When the function runs,

* Environment variable `SOURCE_BUCKETS` is checked for a list of bucket names.
  If the variable is empty, a list of all the available S3 buckets is
  fetched from AWS and used as source bucket list.
* Environment variable `TARGET_BUCKET` is checked for a common bucket. If it's
  set, this bucket is used as the common target bucket for all the source
  buckets. If `TARGET_BUCKET` is not set, `TARGET_` prefix env var is check
  for every enable logging based on the source bucket region.
* Once the correct target bucket name is inferred, logging is enabled for
  bucket, with log target prefix same as the source bucket name. If no proper
  target bucket in the right region is found, enabling logging would not be
  enabled for the particular source bucket and would crash the whole function.
  It is designed to crash so that function failures don't happen silently, but
  cloudwatch alarms can be raised on failures.
* Versioning is enabled along with logging. Versioning doesn't required any
  extra info, unlink logging. If versioning or logging is already enabled in a
  bucket, nothing would be changed.
* If the target bucket doesn't has the required permission for Log Delivery
  group to deliver logs, permission is automatically added.
  NOTE: This could even remove any existing permissions on the target bucket.
  FullControl permission for owner of the bucket is maintained, but any other
  permissions are overwritten.
