import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    """Get a new database connection."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cur = conn.cursor()

    # ── Users ────────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            plan VARCHAR(20) DEFAULT 'free',
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    # Add status column if missing (existing installations)
    cur.execute("""
        DO $$ BEGIN
            ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
        EXCEPTION WHEN others THEN NULL;
        END $$;
    """)

    # ── Charts ───────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS charts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            birth_date DATE NOT NULL,
            birth_time TIME NOT NULL,
            birth_city VARCHAR(150) NOT NULL,
            birth_country VARCHAR(100),
            lat DECIMAL(9,6),
            lng DECIMAL(9,6),
            tz_str VARCHAR(60),
            positions_json JSONB,
            svg_data TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # ── Purchases ────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id),
            chart_id UUID REFERENCES charts(id),
            product_type VARCHAR(50),
            stripe_payment_id VARCHAR(255),
            amount_cents INTEGER,
            status VARCHAR(30) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # ── Products / Plans ─────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL,
            description TEXT,
            type VARCHAR(50) NOT NULL,
            price_cents INTEGER NOT NULL,
            credits INTEGER DEFAULT 0,
            stripe_product_id VARCHAR(255),
            stripe_price_id VARCHAR(255),
            active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # ── User Credits ─────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_credits (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
            credits_balance INTEGER DEFAULT 0,
            total_purchased INTEGER DEFAULT 0,
            total_used INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # ── Credit Transactions ──────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            admin_id UUID,
            type VARCHAR(30) NOT NULL,
            amount INTEGER NOT NULL,
            description VARCHAR(255),
            reference_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # ── Admin Logs ───────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            admin_email VARCHAR(255),
            action VARCHAR(100) NOT NULL,
            target_type VARCHAR(50),
            target_id VARCHAR(255),
            details JSONB,
            ip_address VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # ── System Config ────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key VARCHAR(100) PRIMARY KEY,
            value TEXT,
            description VARCHAR(255),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        INSERT INTO system_config (key, value, description) VALUES
        ('ai_model', 'claude-sonnet-4-6', 'Modelo Anthropic utilizado nas interpretacoes'),
        ('credits_per_interpretation', '1', 'Creditos consumidos por interpretacao completa'),
        ('credits_per_synastry', '2', 'Creditos consumidos por sinastria'),
        ('free_credits_on_register', '0', 'Creditos gratis ao criar conta'),
        ('maintenance_mode', 'false', 'Modo manutencao do sistema')
        ON CONFLICT (key) DO NOTHING;
    """)

    conn.commit()
    cur.close()
    conn.close()
