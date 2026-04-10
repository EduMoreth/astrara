import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    """Get a new database connection."""
    conn_str = DATABASE_URL
    if conn_str and "sslmode" not in conn_str:
        sep = "&" if "?" in conn_str else "?"
        conn_str = conn_str + sep + "sslmode=require"
    return psycopg2.connect(conn_str, cursor_factory=RealDictCursor)


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
