# Fixed base model - re-exports from db module
from ..db import Base, get_db
__all__ = ['Base', 'get_db']
