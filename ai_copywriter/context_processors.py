from decouple import config

def dicoding_metadata(request):
    """
    Context processor to provide Dicoding metadata for templates
    """
    return {
        'dicoding_email': config('DICODING_EMAIL', default=''),
    }