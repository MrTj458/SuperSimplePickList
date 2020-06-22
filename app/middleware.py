import os
import hmac as hm
import hashlib
from urllib.parse import urlencode
from django.http import HttpResponseBadRequest


def check_hmac(get_response):
    """TODO"""
    def middleware(request):
        if request.path.startswith('/app/') and not 'uninstalled' in request.path:
            if request.GET.get('hmac') is not None:
                # Check hmac
                query = request.GET.copy()  # Copy query to make it mutable
                hmac = query.get('hmac')  # Save hmac
                query.pop('hmac')  # remove hmac from query
                # turn the query back to a url from dict
                query = urlencode(query)

                # Get value from secret key
                digest = hm.new(os.environ.get('SHOPIFY_SECRET').encode(),
                                query.encode(), hashlib.sha256)

                # Check that it matches the given hmac
                if not hm.compare_digest(hmac, digest.hexdigest()):
                    return HttpResponseBadRequest('Invalid hmac.')
            else:
                return HttpResponseBadRequest('No hmac provided.')

        # Middleware response
        response = get_response(request)
        return response

    return middleware
