# from django.db import models
#
#
# # DocumentType Enum
# class DocumentType(models.TextChoices):
#     OUTGOING_DOCUMENT = 'OUTGOING_DOCUMENT', 'Outgoing Document'
#     INCOMING_DOCUMENT = 'INCOMING_DOCUMENT', 'Incoming Document'
#     INTERNAL_DOCUMENT = 'INTERNAL_DOCUMENT', 'Internal Document'
#     OTHER_DOCUMENT = 'OTHER_DOCUMENT', 'Other Document'
#
#
# # UrgencyStatus Enum
# class UrgencyStatus(models.TextChoices):
#     HIGH = 'HIGH', 'High'
#     NORMAL = 'NORMAL', 'Normal'
#
#
# # DocumentAction Enum
# class DocumentForm(models.TextChoices):
#     OFFICIAL_LETTER = 'OFFICIAL_LETTER', 'Official Letter'
#     DECISION = 'DECISION', 'Decision'
#     ANNOUNCEMENT = 'ANNOUNCEMENT', 'Announcement'
#     DECREE = 'DECREE', 'Decree'
#
#
# # SecurityType Enum (example)
# class SecurityType(models.TextChoices):
#     CONFIDENTIAL = 'CONFIDENTIAL', 'Confidential'
#     NORMAL = 'NORMAL', 'Normal'
#
#
# # PublishType Enum (example)
# class PublishType(models.TextChoices):
#     INTERNAL = 'INTERNAL', 'Internal'
#
#
# # ProcessingStatus Enum (example)
# class ProcessingStatus(models.TextChoices):
#     PENDING = 'PENDING', 'Pending'
#     COMPLETED = 'COMPLETED', 'Completed'
#
#
# class NotifyEnum(models.TextChoices):
#     READ = 'READ'
#     UNREAD = 'UNREAD'
