# bake reads this file; the code lives in src/python so tests can measure its coverage
from src.python.bakefile import MyBakebook, bakebook

__all__ = ["MyBakebook", "bakebook"]
