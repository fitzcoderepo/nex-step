from django.contrib import admin
from .models import Flow, Node, NodeMedia

# Register your models here.

admin.site.register([Flow, Node, NodeMedia])
