"""
Frontend views for rendering the UI.
"""

from django.shortcuts import render
from django.views.generic import TemplateView


class IndexView(TemplateView):
    """View for serving the main frontend/dashboard."""
    template_name = 'base.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['app_name'] = 'AI Chatbot System'
        return context
