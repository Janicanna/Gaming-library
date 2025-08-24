from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login
from django.db import connection
from django.contrib.auth.models import User
from .models import Game
import requests, re


def home(request):
    return HttpResponse("Gaming-Library")


# A01: Broken Access Control
def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    # The mistake: the owner is not checked
    return HttpResponse(f"Game: {game.name}, owner_id={game.owner_id}")

    # How to fix:
    # if game.owner != request.user:
    #     return HttpResponseForbidden("Not your game")
    # return HttpResponse(f"Game: {game.name}")


# A03: Injection (SQL Injection)
def search(request):
    q = request.GET.get("q", "")
    # The mistake: user input is inserted directly into the SQL string
    with connection.cursor() as c:
        c.execute(f"SELECT id, name FROM core_game WHERE name LIKE '%{q}%'")
        rows = c.fetchall()
    return HttpResponse(str(rows))

    # How to fix:
    # with connection.cursor() as c:
    #     c.execute("SELECT id, name FROM core_game WHERE name LIKE %s", [f"%{q}%"])
    #     rows = c.fetchall()
    # return HttpResponse(str(rows))

# A07: Identification & Authentication Failures
def login_simple(request):
    username = request.GET.get("username", "")
    if username:
        try:
            # The mistake: login without password, only by username
            user = User.objects.get(username=username)
            login(request, user)
            return HttpResponse("Logged in (insecure).")
        except User.DoesNotExist:
            return HttpResponse("No such user")
    return HttpResponse("Use ?username=<name> to login (insecure demo).")

    # How to fix:
    # if request.method == "POST":
    #     username = request.POST.get("username", "")
    #     password = request.POST.get("password", "")
    #     user = authenticate(request, username=username, password=password)
    #     if user:
    #         login(request, user)
    #         return HttpResponse("Logged in (secure).")
    #     return HttpResponse("Wrong credentials")
    # return HttpResponse(
    #     '<form method="post">'
    #     '<input name="username" placeholder="username">'
    #     '<input name="password" type="password" placeholder="password">'
    #     '<button>Login</button></form>'
    # )

# A10: Server-Side Request Forgery
def fetch_url(request):
    url = request.GET.get("url", "")
    if not url:
        return HttpResponse("Use ?url=<http(s)://...> to fetch")

    # The mistake: any external or internal URL can be fetched
    try:
        r = requests.get(url, timeout=5)
        return HttpResponse(
            f"Fetched: {url}\nStatus: {r.status_code}\nLength: {len(r.text)}\n\n{r.text[:300]}"
        )
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=400)

    # How to fix:
    # allowed = re.compile(r"^https?://(example\.com|httpbin\.org)(/|$)", re.I)
    # if not allowed.match(url):
    #     return HttpResponseForbidden("Domain not allowed")
    # if "127.0.0.1" in url or "localhost" in url:
    #     return HttpResponseForbidden("Local targets not allowed")
    # try:
    #     r = requests.get(url, timeout=3)
    #     return HttpResponse(r.text[:300])
    # except Exception as e:
    #     return HttpResponse(f"Error: {e}")

