from django.db import models


class Shop(models.Model):
    name = models.TextField(blank=True)
    access_token = models.TextField(blank=True)
    scope = models.TextField(blank=True)
    nonce = models.TextField(blank=True)
