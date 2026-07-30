from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ProfileSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    def get_object(self): return self.request.user


class AvatarView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        if "avatar" not in request.FILES: return Response({"detail": "Файл avatar обязателен."}, status=400)
        image = request.FILES["avatar"]
        if image.size > 3 * 1024 * 1024 or not image.content_type.startswith("image/"):
            return Response({"detail": "Нужна картинка не больше 3 МБ."}, status=400)
        request.user.avatar = image; request.user.save(update_fields=["avatar"])
        return Response(ProfileSerializer(request.user, context={"request": request}).data)
