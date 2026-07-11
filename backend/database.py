import os
import threading
import psycopg2
from psycopg2 import pool as pg_pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def _dsn():
    conn_str = DATABASE_URL
    if conn_str and "sslmode" not in conn_str:
        sep = "&" if "?" in conn_str else "?"
        conn_str = conn_str + sep + "sslmode=require"
    return conn_str


# ── Connection pool ──────────────────────────────────────────
# SECURITY_CHECKLIST II: "Connection pooling configurado — nunca conexao nova
# por request". A shared pool replaces the previous connect-per-request. If the
# pool is disabled/unavailable/exhausted we fall back to a direct connection, so
# behavior degrades to the old path instead of failing.
_POOL_ENABLED = os.getenv("DB_POOL_ENABLED", "true").strip().lower() not in ("0", "false", "no")
_POOL_MIN = int(os.getenv("DB_POOL_MIN", "1"))
_POOL_MAX = int(os.getenv("DB_POOL_MAX", "10"))

_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = pg_pool.ThreadedConnectionPool(
                    _POOL_MIN, _POOL_MAX, _dsn(), cursor_factory=RealDictCursor
                )
    return _pool


class _PooledConnection:
    """Proxies a pooled connection so existing code calling conn.close() returns
    it to the pool instead of destroying it. Any open/aborted transaction is
    rolled back on return, so a connection is never handed to the next request
    in a dirty state."""

    def __init__(self, pool, conn):
        self.__dict__["_pool"] = pool
        self.__dict__["_conn"] = conn
        self.__dict__["_returned"] = False

    def close(self):
        if self.__dict__["_returned"]:
            return
        self.__dict__["_returned"] = True
        conn = self.__dict__["_conn"]
        try:
            try:
                conn.rollback()
            except Exception:
                pass
            self.__dict__["_pool"].putconn(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

    def __getattr__(self, name):
        return getattr(self.__dict__["_conn"], name)

    def __setattr__(self, name, value):
        setattr(self.__dict__["_conn"], name, value)


def get_connection():
    """Get a database connection from the shared pool.

    Falls back to a direct connection if pooling is disabled, the pool cannot be
    created, or it is momentarily exhausted — never worse than the old
    connect-per-request behavior."""
    if _POOL_ENABLED:
        try:
            pool = _get_pool()
            return _PooledConnection(pool, pool.getconn())
        except Exception as e:
            print(f"DB pool unavailable, using direct connection: {e}")
    return psycopg2.connect(_dsn(), cursor_factory=RealDictCursor)


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
    # Add columns if missing (existing installations)
    cur.execute("""
        DO $$ BEGIN
            ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
            ALTER TABLE users ADD COLUMN IF NOT EXISTS force_password_reset BOOLEAN DEFAULT false;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255);
            ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;
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

    # Persist houses + aspects for saved charts (additive, non-destructive) so
    # reopening a saved chart renders the full wheel, not a degraded one.
    cur.execute("""
        DO $$ BEGIN
            ALTER TABLE charts ADD COLUMN IF NOT EXISTS houses_json JSONB;
            ALTER TABLE charts ADD COLUMN IF NOT EXISTS aspects_json JSONB;
        EXCEPTION WHEN others THEN NULL;
        END $$;
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

    # Add plan feature columns to products (migration-safe)
    cur.execute("""
        DO $$ BEGIN
            ALTER TABLE products ADD COLUMN IF NOT EXISTS max_saved_charts INTEGER DEFAULT 0;
            ALTER TABLE products ADD COLUMN IF NOT EXISTS recurrence VARCHAR(20) DEFAULT 'none';
            ALTER TABLE products ADD COLUMN IF NOT EXISTS stripe_subscription_price_id VARCHAR(255);
        EXCEPTION WHEN others THEN NULL;
        END $$;
    """)

    # Add subscription tracking to users
    cur.execute("""
        DO $$ BEGIN
            ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_product_id UUID;
            ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_stripe_id VARCHAR(255);
            ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(30) DEFAULT 'none';
            ALTER TABLE users ADD COLUMN IF NOT EXISTS max_saved_charts INTEGER DEFAULT 1;
        EXCEPTION WHEN others THEN NULL;
        END $$;
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

    # Synastry is a premium product with its OWN credit type: interpretation
    # credits must not unlock synastry and vice-versa. Additive, non-destructive.
    cur.execute("""
        DO $$ BEGIN
            ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS synastry_credits INTEGER DEFAULT 0;
        EXCEPTION WHEN others THEN NULL;
        END $$;
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

    # Defense-in-depth against double-crediting a payment: a partial unique index
    # so a given Stripe session can only ever produce one 'purchase' transaction.
    # Only covers type='purchase' (manual/refund rows legitimately share a
    # reference_id). Wrapped so pre-existing duplicates can't block startup — the
    # row-lock in _fulfill_purchase already prevents new ones.
    cur.execute("""
        DO $$ BEGIN
            CREATE UNIQUE INDEX IF NOT EXISTS uq_credit_tx_purchase_reference
                ON credit_transactions (reference_id)
                WHERE type = 'purchase' AND reference_id IS NOT NULL;
        EXCEPTION WHEN others THEN NULL;
        END $$;
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

    # ── Support Tickets ──────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            subject VARCHAR(200) NOT NULL,
            status VARCHAR(30) DEFAULT 'open',
            priority VARCHAR(20) DEFAULT 'normal',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ticket_messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ticket_id UUID REFERENCES tickets(id) ON DELETE CASCADE,
            sender_type VARCHAR(20) NOT NULL,
            sender_id UUID,
            sender_name VARCHAR(100),
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # ── Refunds ──────────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS refunds (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            purchase_id UUID REFERENCES purchases(id),
            user_id UUID REFERENCES users(id),
            admin_email VARCHAR(255),
            amount_cents INTEGER NOT NULL,
            reason VARCHAR(500),
            stripe_refund_id VARCHAR(255),
            status VARCHAR(30) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # ── Email Logs ───────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS email_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            to_email VARCHAR(255) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            template VARCHAR(100),
            status VARCHAR(30) DEFAULT 'sent',
            resend_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # ── Chart Generation Log (tracks ALL generations, not just saved) ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chart_generations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            name VARCHAR(100),
            birth_date DATE,
            birth_time TIME,
            birth_city VARCHAR(150),
            birth_country VARCHAR(100),
            lat DECIMAL(9,6),
            lng DECIMAL(9,6),
            ip_address VARCHAR(50),
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # ── Chart Interpretation Cache ────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chart_interpretations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            positions_hash VARCHAR(64) NOT NULL,
            name VARCHAR(100),
            interpretation_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, positions_hash)
        );
    """)

    # ── Instagram Posts ──────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS instagram_posts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            post_date DATE NOT NULL UNIQUE,
            horoscope_text TEXT,
            transits_text TEXT,
            image_path VARCHAR(255),
            instagram_media_id VARCHAR(255),
            instagram_permalink VARCHAR(255),
            status VARCHAR(30) DEFAULT 'pending',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            published_at TIMESTAMP
        );
    """)

    # ── Blog Posts ─────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blog_posts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            slug VARCHAR(255) UNIQUE NOT NULL,
            title VARCHAR(255) NOT NULL,
            meta_description VARCHAR(320),
            content TEXT NOT NULL,
            category VARCHAR(100),
            tags TEXT,
            featured_image_url VARCHAR(500),
            status VARCHAR(20) DEFAULT 'draft',
            views INTEGER DEFAULT 0,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # ── Twitter Posts ──────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS twitter_posts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            post_date DATE NOT NULL UNIQUE,
            tweet_text TEXT,
            twitter_post_id VARCHAR(255),
            status VARCHAR(30) DEFAULT 'pending',
            error_message TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            published_at TIMESTAMP
        );
    """)

    # ── Newsletter ────────────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS newsletter_subscribers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            status VARCHAR(20) DEFAULT 'active',
            subscribed_at TIMESTAMP DEFAULT NOW(),
            unsubscribed_at TIMESTAMP
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS newsletter_editions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            subject VARCHAR(255) NOT NULL,
            content_html TEXT,
            week_start DATE,
            week_end DATE,
            sent_count INTEGER DEFAULT 0,
            status VARCHAR(30) DEFAULT 'draft',
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # ── Referral Program ──────────────────────────────
    cur.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            referrer_id UUID REFERENCES users(id) ON DELETE CASCADE,
            referred_id UUID REFERENCES users(id) ON DELETE SET NULL,
            referral_code VARCHAR(50) NOT NULL,
            credits_awarded INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # Add referral_code to users
    cur.execute("""
        DO $$ BEGIN
            ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code VARCHAR(50);
            ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by UUID;
        EXCEPTION WHEN others THEN NULL;
        END $$;
    """)

    cur.execute("""
        INSERT INTO system_config (key, value, description) VALUES
        ('ai_model', 'claude-sonnet-4-6', 'Modelo Anthropic utilizado nas interpretacoes'),
        ('credits_per_interpretation', '1', 'Creditos consumidos por interpretacao completa'),
        ('credits_per_synastry', '2', 'Creditos consumidos por sinastria'),
        ('free_credits_on_register', '0', 'Creditos gratis ao criar conta'),
        ('maintenance_mode', 'false', 'Modo manutencao do sistema'),
        ('support_email', 'suporte@astrara.online', 'Email de suporte exibido para usuarios'),
        ('referral_credits', '1', 'Creditos concedidos por indicacao'),
        ('newsletter_auto_subscribe', 'true', 'Inscrever novos usuarios na newsletter automaticamente')
        ON CONFLICT (key) DO NOTHING;
    """)

    conn.commit()
    cur.close()
    conn.close()
