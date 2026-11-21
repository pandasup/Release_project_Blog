
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from authentication.mixins import AdminRequiredMixin

from .forms import AnnouncementForm
from .models import Announcement


class AnnouncementListView(ListView):
    template_name = 'announcements/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 10

    def get_queryset(self):
        qs = Announcement.objects.select_related('created_by')
        user = self.request.user
        if user.is_authenticated and user.is_blog_admin:
            return qs  # адмін бачить і приховані
        return qs.filter(is_active=True)


class AnnouncementCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/announcement_form.html'
    success_url = reverse_lazy('announcements:list')
    success_message = 'Оголошення створено.'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class AnnouncementUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'announcements/announcement_form.html'
    success_url = reverse_lazy('announcements:list')
    success_message = 'Оголошення оновлено.'


class AnnouncementDeleteView(AdminRequiredMixin, DeleteView):
    model = Announcement
    template_name = 'announcements/announcement_confirm_delete.html'
    success_url = reverse_lazy('announcements:list')