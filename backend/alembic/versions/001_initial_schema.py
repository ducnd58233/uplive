"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-19

"""

from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    op.execute(
        """
        CREATE TABLE sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            url TEXT NOT NULL,
            status VARCHAR(32) NOT NULL,
            duration DOUBLE PRECISION,
            title TEXT,
            path TEXT,
            error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute("CREATE INDEX idx_sources_status ON sources (status);")
    op.execute(
        """
        CREATE TABLE jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
            clips JSONB NOT NULL,
            transition VARCHAR(16) NOT NULL,
            transition_duration DOUBLE PRECISION NOT NULL DEFAULT 0,
            status VARCHAR(32) NOT NULL,
            progress INTEGER NOT NULL DEFAULT 0,
            result_path TEXT,
            error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute("CREATE INDEX idx_jobs_source_id ON jobs (source_id);")
    op.execute("CREATE INDEX idx_jobs_status ON jobs (status);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS jobs CASCADE;")
    op.execute("DROP TABLE IF EXISTS sources CASCADE;")
