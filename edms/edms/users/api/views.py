from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from edms.users.models import User
from .filters import UserFilter

from ...common.app_status import AppResponse
from ...common.app_status import ErrorResponse
from ...common.helper import custom_error
from ...common.pagination import StandardResultsSetPagination
from ...common.permissions import IsOwnerOrAdmin
from .serializers import (
    UserLoginSerializer,
    UpdateUserSignatureSerializer,
    UserRegisterSerializer,
    UserSerializer,
    UserChangePasswordSerializer,
    LogoutSerializer,
)
from ...search.filters import UnaccentSearchFilter


class UserViewSet(  # viewsets.ModelViewSet):
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    action_serializers = {
        "list": UserSerializer,
        "register": UserRegisterSerializer,
        "login": UserLoginSerializer,
        "update_signature": UpdateUserSignatureSerializer,
        "logout": LogoutSerializer,
        # "resend_email": ResendEmailSerializer,
        # "forgot_password": ForgotPasswordSerializer,
        "change_password": UserChangePasswordSerializer,
    }
    default_serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    queryset = User.objects.all()
    filter_backends = (
        DjangoFilterBackend,
        UnaccentSearchFilter,
    )
    filterset_class = UserFilter
    search_fields = [
        "name",
        "email",
        "position",
        "phone_number",
    ]

    def get_permissions(self):
        if self.action in ["destroy"]:
            self.permission_classes = [IsAdminUser]
        if self.action in ["list", "retrieve"]:
            self.permission_classes = [IsAuthenticated]
        if self.action in ["update", "partial_update"]:
            self.permission_classes = [IsOwnerOrAdmin]
        return super(self.__class__, self).get_permissions()

    def get_serializer_class(self):
        if hasattr(self, "action_serializers"):
            return self.action_serializers.get(
                self.action,
                self.default_serializer_class,
            )
        return super(UserViewSet, self).get_serializer_class()

    def get_queryset(self, *args, **kwargs):
        return self.queryset.order_by("-id")

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            data = AppResponse.UPDATE_USER_INFO.success_response
            data["results"] = serializer.data
            return Response(data, status=AppResponse.UPDATE_USER_INFO.status_code)
        return ErrorResponse(
            custom_error("USER", serializer.errors),
        ).failure_response()

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[IsAdminUser],
        url_path="register",
    )
    def register(self, request):
        serializer = self.get_serializer_class()(
            data=request.data,
            context=self.get_serializer_context(),
        )
        if serializer.is_valid():
            serializer.save()
            response = Response(
                AppResponse.REGISTER_SUCCESS.success_response,
                status=AppResponse.REGISTER_SUCCESS.status_code,
            )
        else:
            response = ErrorResponse(
                custom_error("USER", serializer.errors),
            ).failure_response()
        return response

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[AllowAny],
        url_path="login",
    )
    def login(self, request):
        serializer = self.get_serializer_class()(
            data=request.data,
            context=self.get_serializer_context(),
        )
        if serializer.is_valid():
            user = serializer.validated_data
            refresh = TokenObtainPairSerializer.get_token(user)
            data = AppResponse.LOGIN_SUCCESS.success_response
            data["results"] = UserSerializer(
                user,
                context={
                    'request': request,
                }
            ).data
            data["refresh"] = str(refresh)
            data["access"] = str(refresh.access_token)
            response = Response(data, status=AppResponse.LOGIN_SUCCESS.status_code)
        else:
            response = ErrorResponse(
                custom_error("USER", serializer.errors),
            ).failure_response()
        return response

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[IsAuthenticated, ],
        url_path="logout"
    )
    def logout(self, request):
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response = Response(status=status.HTTP_204_NO_CONTENT)
        else:
            response = ErrorResponse(
                custom_error("USER", serializer.errors)
            ).failure_response(),

        return response

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[IsAuthenticated, ],
        url_path="change-password"
    )
    def change_password(self, request):
        serializer = UserChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            data = AppResponse.CHANGE_PASSWORD.success_response
            return Response(data, status=AppResponse.CHANGE_PASSWORD.status_code)
        response = ErrorResponse(
            custom_error("USER", serializer.errors)
        ).failure_response()
        return response


    @action(
        detail=False,
        methods=["put"],
        url_path="signatures",
    )
    def update_signature(self, request):
        serializer = self.get_serializer_class()(
            data=request.data,
            context=self.get_serializer_context(),
        )
        if serializer.is_valid():
            serializer.update(request.user, serializer.validated_data)
            response = Response(
                UserSerializer(
                    request.user,
                    context={
                        'request': request,
                    }
                ).data, status=status.HTTP_200_OK)
        else:
            response = ErrorResponse(
                custom_error("USER", serializer.errors),
            ).failure_response()
        return response
