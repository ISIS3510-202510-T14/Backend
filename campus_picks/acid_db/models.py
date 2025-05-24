# acid_db/models.py
import uuid
from django.db import models

class Team(models.Model):
    team_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, db_index=True)
    logo = models.CharField(max_length=255, blank=True, null=True)  # URL o path al logo

    def __str__(self):
        return self.name


class User(models.Model):
    user_id = models.CharField(primary_key=True, max_length=128, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

class Event(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rt_event_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    home_team = models.ManyToManyField(Team, related_name='events')
    away_team = models.ManyToManyField(Team, related_name='away_events')
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.event_id

class Bet(models.Model):
    bet_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bets')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bets')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='bets')  # Equipo al que se apuesta
    stake = models.DecimalField(max_digits=10, decimal_places=2)
    odds = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, default='placed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bet {self.bet_id} on {self.event}"


class Product(models.Model):
    """Simple product model for the marketplace."""
    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name

class Purchase(models.Model):
    purchase_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='purchases')
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Purchase {self.purchase_id} by {self.user.email}'

