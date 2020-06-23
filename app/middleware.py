import os
import hmac as hm
import hashlib
from urllib.parse import urlencode
from django.http import HttpResponseBadRequest


def check_hmac(get_response):
    """Compare the hmac given by shopify to the secret key to authenticate valid requests."""
    def middleware(request):
        if request.path.startswith('/app/') and not 'uninstalled' in request.path:
            if request.GET.get('hmac') is not None:
                hmac = request.GET.get('hmac')

                if request.GET.getlist('ids[]') == []:
                    # Normal request

                    params = request.GET.copy()  # Copy query to make it mutable
                    params.pop('hmac')  # remove hmac from query
                    # turn the query back to a url from dict
                    params = urlencode(params)
                else:
                    # Bulk admin button selected.
                    # Put the id's in the format shopify wants

                    ids = request.GET.getlist('ids[]')
                    ids = str(ids).replace("'", '"')
                    params = f'ids={ids}&locale=en&session={request.GET.get("session")}&shop={request.GET.get("shop")}&timestamp={request.GET.get("timestamp")}'

                # Get value from secret key
                digest = hm.new(os.environ.get('SHOPIFY_SECRET').encode(),
                                params.encode(), hashlib.sha256)

                # Check that it matches the given hmac
                if not hm.compare_digest(hmac, digest.hexdigest()):
                    return HttpResponseBadRequest('Invalid hmac.')
            else:
                return HttpResponseBadRequest('No hmac provided.')

        # Middleware response
        response = get_response(request)
        return response

    return middleware
