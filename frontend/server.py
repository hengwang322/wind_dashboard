from waitress import serve
from app import server #so "app" is the name of my Dash script I want to serve

serve(server)
