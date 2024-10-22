from enum import Enum

from rest_framework import status
from rest_framework.response import Response


class AppResponse(Enum):
    REGISTER_SUCCESS = status.HTTP_200_OK, "USER__REGISTER__SUCCESS"
    SEND_MAIL = status.HTTP_200_OK, "USER__SEND__SUCCESS"
    CHANGE_PASSWORD = status.HTTP_200_OK, "USER__CHANGE_PASSWORD__SUCCESS"
    LOGIN_SUCCESS = status.HTTP_200_OK, "USER__LOGIN__SUCCESS"
    UPDATE_USER_INFO = status.HTTP_200_OK, "USER__UPDATE__SUCCESS"
    DELETE_USER = status.HTTP_200_OK, "USER__DELETE__SUCCESS"
    CHANGE_PASSWORD_SUCCESS = status.HTTP_200_OK, "CHANGE__PASSWORD__SUCCESS"
    USER_INCORRECT_PASSWORD = status.HTTP_400_BAD_REQUEST, "USER__INCORRECT__PASSWORD"

    CREATE_DOCUMENTS = status.HTTP_201_CREATED, "DOCUMENTS__CREATE__SUCCESS"
    UPDATE_DOCUMENTS = status.HTTP_200_OK, "DOCUMENTS__UPDATE__SUCCESS"
    DELETE_DOCUMENTS = status.HTTP_200_OK, "DOCUMENTS__DELETE__SUCCESS"
    STATISTICS_DOCUMENTS = status.HTTP_200_OK, "DOCUMENTS__STATISTICS__SUCCESS"
    SEND_DOCUMENTS = status.HTTP_200_OK, "DOCUMENTS__SEND__SUCCESS"
    START_SIGNING_DOCUMENTS = status.HTTP_200_OK, "DOCUMENTS__START_SIGNING__SUCCESS"
    CONTINUES_SIGNING_DOCUMENTS = status.HTTP_200_OK, "DOCUMENTS__CONTINUES_SIGNING__SUCCESS"
    SEND_DOCUMENTS_FAILURE = status.HTTP_400_BAD_REQUEST, "DOCUMENTS__SEND__FAILURE"
    # DELETE_DOCUMENTS_FAILURE = status.HTTP_400_BAD_REQUEST, 'DOCUMENTS__DELETE__FAILURE'

    @property
    def status_code(self):
        return self.value[0]

    @property
    def message(self):
        return self.value[1]

    @property
    def success_response(self):
        return dict(message=self.value[1])

    @property
    def failure_response(self):
        return dict(detail=self.value[1])


class ErrorResponse:
    def __init__(self, err_messages):
        self.err_messages = err_messages

    def failure_response(self):
        return Response(
            dict(detail=self.err_messages),
            status=status.HTTP_400_BAD_REQUEST,
        )

    def serializer_error(self):
        self.err_messages = [err_messages.upper() for err_messages in self.err_messages]
        return dict(detail=self.err_messages)
