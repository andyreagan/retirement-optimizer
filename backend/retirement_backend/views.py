from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import os

def index(request):
    """Serve the main frontend application"""
    static_dir = os.path.join(settings.BASE_DIR, 'staticfiles')
    index_file = os.path.join(static_dir, 'index.html')
    
    if os.path.exists(index_file):
        with open(index_file, 'r') as f:
            return HttpResponse(f.read(), content_type='text/html')
    else:
        return HttpResponse("Frontend not built. Please run './build_frontend.sh' to build the frontend.", 
                          content_type='text/plain')