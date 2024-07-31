import pytest
from unittest.mock import MagicMock
from base_repository import SupabaseSingleton, BaseRepository

def mock_supabase():
    return MagicMock()

