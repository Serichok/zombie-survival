from rest_framework import generics
from .models import GameHistory
from .serializers import GameHistorySerializer


class HistoryListView(generics.ListAPIView):
    serializer_class = GameHistorySerializer
    def get_queryset(self): return GameHistory.objects.filter(participant=self.request.user)
