from django.shortcuts import render

def index(request):
    # Pass any URL parameters to the template
    return render(request, 'index.html')

def countdown(request):
    token = request.GET.get('token', '')
    video_name = request.GET.get('videoName', '')
    context = {
        'token': token,
        'video_name': video_name
    }
    return render(request, 'countdown.html', context)
