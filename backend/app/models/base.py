from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Schema is owned by database/schema.sql (Supabase migrations).

    These models exist for typed queries only — never run metadata.create_all().
    """
