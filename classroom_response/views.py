from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect

def remote_login(request):
    """ Used to redirect to the desired page after loggin in. Wherever login is
    directed should be protected by the remote user.
    """
    next_page = request.GET['next']
    import pdb; pdb.set_trace()
    return redirect(next_page)
