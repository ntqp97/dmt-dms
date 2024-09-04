from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
    location = "media"
    default_acl = "public-read"
    file_overwrite = True


class PrivateMediaStorage(S3Boto3Storage):
    location = "private"
    default_acl = "private"
    file_overwrite = True
    custom_domain = True


class MyS3Storage(S3Boto3Storage):
    def copy(self, from_path, to_path):
        from_path = self._normalize_name(self._clean_name(from_path))
        to_path = self._normalize_name(self._clean_name(to_path))

        copy_result = self.connection.meta.client.copy_object(
            Bucket=self.bucket_name,
            CopySource=self.bucket_name + "/" + from_path,
            Key=to_path,
        )

        if copy_result["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return True
        else:
            return False
