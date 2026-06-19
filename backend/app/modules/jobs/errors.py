class JobStoreError(Exception):
    pass


class SourceNotFoundError(JobStoreError):
    pass


class JobNotFoundError(JobStoreError):
    pass


class QueueFullError(JobStoreError):
    pass
