"""Run matcher and seed staples."""
from scrapers.matcher import match_all
from scrapers.seed_staples import seed

print("=== MATCHING ===")
match_all()

print("\n=== SEEDING STAPLES ===")
seed()

print("\n=== DONE ===")
