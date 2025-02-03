import random
import uuid

from django.shortcuts import render

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User, Profile
from users.serializer import MyTokenObtainPairSerializer, PasswordChangeSerializer, RegisterSerializer, UserSerializer, EmailSerializer


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = RegisterSerializer


def generate_otp(length=7):
    # Generate a random 7-digit OTP
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp


class PasswordEmailVerifyView(generics.RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = EmailSerializer

    # def get_object(self):
    def get(self, request, *args, **kwargs):
        email = self.kwargs['email']
        user = User.objects.get(email=email)

        if user:
            user.otp = generate_otp()
            user.save()

            reset_token = '123'

            link = f"create-new-password?otp={user.otp}&uidb64={user.pk}&reset_token={reset_token}"

            return Response(
                {"link": link},
                status=status.HTTP_200_OK,
            )
            # return user
        else:
            return Response( {"message": "An Error Occured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class PasswordChangeView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        # print('************ PasswordChangeView ****************', request.data)
        serializer = PasswordChangeSerializer(data=request.data)

        if serializer.is_valid():
            print('************ PasswordChangeView validated_data ****************', serializer.validated_data['uidb64'])
            print('************ PasswordChangeView request.data ****************', request.data['uidb64'])
            user = User.objects.get(
                id=serializer.validated_data['uidb64'],
                otp=serializer.validated_data['otp'],
            )

            print('************ PasswordChangeView user ****************', user)

            if user:
                user.set_password(request.data['password'])
                user.otp = ""
                user.reset_token = ""
                user.save()
                return Response({
                    "message": "Password Changed Successfully",
                    "status": 200,
                })
            else:
                return Response( {"message": "No User"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response( {"message": "An Error Occured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    

# class PasswordChangeView(generics.CreateAPIView):
#     permission_classes = (AllowAny,)
#     serializer_class = UserSerializer

#     def create(self, request, *args, **kwargs):
#         payload = request.data

#         otp = payload["otp"]
#         uidb64 = payload["uidb64"]
#         reset_token = payload["reset_token"]
#         password = payload["password"]

#         user = User.objects.get(id=uidb64, otp=otp)

#         if user:
#             user.set_password(password)
#             user.otp = ""
#             user.reset_token = ""
#             user.save()

#             return Response( {"message": "Password Changed Successfully"}, status=status.HTTP_201_CREATED)
#         else:
#             return Response( {"message": "An Error Occured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)