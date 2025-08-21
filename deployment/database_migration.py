#!/usr/bin/env python3
"""
Database Migration Script: SQLite to PostgreSQL
Migrates existing Amazon Insights data from SQLite to PostgreSQL with enhanced schema
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, List
import json

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import sqlalchemy as sa
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker
import pandas as pd

from config.config import DATABASE_URL, SQLITE_FALLBACK
from src.models.product_models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Handles migration from SQLite to PostgreSQL"""

    def __init__(self):
        self.sqlite_url = "sqlite:///data/amazon_insights.db"
        self.postgres_url = DATABASE_URL

        # Ensure we have valid PostgreSQL URL
        if "sqlite" in self.postgres_url.lower():
            raise ValueError("PostgreSQL URL required for migration")

        logger.info(f"Migration: SQLite -> PostgreSQL")
        logger.info(f"Source: {self.sqlite_url}")
        logger.info(f"Target: {self.postgres_url}")

    def migrate_data(self) -> Dict[str, Any]:
        """Execute complete data migration"""
        try:
            migration_results = {
                "started_at": datetime.now().isoformat(),
                "tables_migrated": [],
                "records_migrated": {},
                "errors": [],
                "completed_at": None,
                "success": True,
            }

            # Create engines
            sqlite_engine = create_engine(self.sqlite_url)
            postgres_engine = create_engine(self.postgres_url)

            # Test connections
            self._test_connections(sqlite_engine, postgres_engine)

            # Create PostgreSQL schema
            logger.info("Creating PostgreSQL schema...")
            self._create_postgres_schema(postgres_engine)

            # Migrate data
            tables_to_migrate = [
                "products",
                "product_snapshots",
                "price_alerts",
                "competitive_groups",
                "competitive_group_members",
            ]

            for table_name in tables_to_migrate:
                try:
                    records_count = self._migrate_table(
                        sqlite_engine, postgres_engine, table_name
                    )
                    migration_results["tables_migrated"].append(table_name)
                    migration_results["records_migrated"][table_name] = records_count
                    logger.info(
                        f"✅ Migrated {records_count} records from {table_name}"
                    )
                except Exception as e:
                    error_msg = f"Failed to migrate table {table_name}: {str(e)}"
                    logger.error(error_msg)
                    migration_results["errors"].append(error_msg)

            # Create indexes and constraints
            self._create_postgres_indexes(postgres_engine)

            # Verify migration
            verification_results = self._verify_migration(
                sqlite_engine, postgres_engine
            )
            migration_results["verification"] = verification_results

            migration_results["completed_at"] = datetime.now().isoformat()

            if migration_results["errors"]:
                migration_results["success"] = False
                logger.warning(
                    f"Migration completed with {len(migration_results['errors'])} errors"
                )
            else:
                logger.info("✅ Migration completed successfully!")

            return migration_results

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _test_connections(self, sqlite_engine, postgres_engine):
        """Test database connections"""
        # Test SQLite
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ SQLite connection successful")

        # Test PostgreSQL
        with postgres_engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"✅ PostgreSQL connection successful: {version}")

    def _create_postgres_schema(self, postgres_engine):
        """Create PostgreSQL schema with enhanced design"""

        # Drop existing tables if they exist
        with postgres_engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS api_usage_logs CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS competitive_analyses CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS alerts CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS alert_rules CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS api_keys CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS task_executions CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS product_features CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS competitive_group_members CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS competitive_groups CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS price_alerts CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS product_snapshots CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS products CASCADE"))
            conn.commit()

        # Create enhanced schema
        schema_sql = """
        -- Products table
        CREATE TABLE products (
            asin VARCHAR(10) PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            brand VARCHAR(100),
            category VARCHAR(200),
            manufacturer VARCHAR(100),
            model VARCHAR(100),
            dimensions JSONB,
            weight DECIMAL(8,2),
            first_tracked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            is_active BOOLEAN NOT NULL DEFAULT true,
            tracking_frequency INTERVAL DEFAULT '24 hours',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        -- Product snapshots (partitioned)
        CREATE TABLE product_snapshots (
            id BIGSERIAL NOT NULL,
            asin VARCHAR(10) NOT NULL,
            title VARCHAR(500),
            price DECIMAL(10,2),
            buybox_price DECIMAL(10,2),
            rating DECIMAL(3,2) CHECK (rating >= 0 AND rating <= 5),
            review_count INTEGER DEFAULT 0,
            bsr_data JSONB DEFAULT '{}',
            availability_status VARCHAR(50),
            bullet_points TEXT[],
            product_description TEXT,
            images JSONB DEFAULT '[]',
            scraped_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            raw_data JSONB,
            processing_status VARCHAR(20) DEFAULT 'processed',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            
            PRIMARY KEY (id, scraped_at),
            FOREIGN KEY (asin) REFERENCES products(asin) ON DELETE CASCADE
        ) PARTITION BY RANGE (scraped_at);
        
        -- Create partitions for current and next month
        CREATE TABLE product_snapshots_current PARTITION OF product_snapshots
        FOR VALUES FROM (DATE_TRUNC('month', CURRENT_DATE)) TO (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month');
        
        CREATE TABLE product_snapshots_next PARTITION OF product_snapshots
        FOR VALUES FROM (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month') TO (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '2 months');
        
        -- Price alerts
        CREATE TABLE price_alerts (
            id SERIAL PRIMARY KEY,
            asin VARCHAR(10) NOT NULL,
            alert_type VARCHAR(50) NOT NULL,
            old_value DECIMAL(10,2),
            new_value DECIMAL(10,2),
            change_percentage DECIMAL(5,2),
            threshold_value DECIMAL(5,2),
            message TEXT NOT NULL,
            severity VARCHAR(10) DEFAULT 'medium',
            is_resolved BOOLEAN DEFAULT false,
            triggered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            resolved_at TIMESTAMP WITH TIME ZONE,
            
            FOREIGN KEY (asin) REFERENCES products(asin) ON DELETE CASCADE
        );
        
        -- Competitive groups
        CREATE TABLE competitive_groups (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            main_product_asin VARCHAR(10) NOT NULL,
            industry_category VARCHAR(100),
            analysis_frequency INTERVAL DEFAULT '24 hours',
            auto_update BOOLEAN DEFAULT true,
            is_active BOOLEAN DEFAULT true,
            created_by VARCHAR(50),
            settings JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            
            FOREIGN KEY (main_product_asin) REFERENCES products(asin)
        );
        
        -- Competitive group members
        CREATE TABLE competitive_group_members (
            id SERIAL PRIMARY KEY,
            group_id INTEGER NOT NULL,
            competitor_asin VARCHAR(10) NOT NULL,
            competitor_name VARCHAR(200),
            priority INTEGER DEFAULT 1,
            is_active BOOLEAN DEFAULT true,
            added_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            added_by VARCHAR(50),
            
            FOREIGN KEY (group_id) REFERENCES competitive_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (competitor_asin) REFERENCES products(asin),
            UNIQUE(group_id, competitor_asin)
        );
        
        -- API keys for authentication
        CREATE TABLE api_keys (
            id SERIAL PRIMARY KEY,
            key_id VARCHAR(50) UNIQUE NOT NULL,
            key_hash VARCHAR(64) NOT NULL,
            name VARCHAR(100),
            key_type VARCHAR(10) NOT NULL, -- public, secret, admin
            permissions JSONB NOT NULL DEFAULT '[]',
            rate_limit_tier VARCHAR(20) DEFAULT 'free',
            is_active BOOLEAN DEFAULT true,
            last_used_at TIMESTAMP WITH TIME ZONE,
            usage_count BIGINT DEFAULT 0,
            expires_at TIMESTAMP WITH TIME ZONE,
            created_by VARCHAR(50),
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        """

        with postgres_engine.connect() as conn:
            conn.execute(text(schema_sql))
            conn.commit()

        logger.info("✅ PostgreSQL schema created successfully")

    def _migrate_table(self, sqlite_engine, postgres_engine, table_name: str) -> int:
        """Migrate specific table from SQLite to PostgreSQL"""

        # Check if table exists in SQLite
        with sqlite_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
                ),
                {"table_name": table_name},
            )
            if not result.fetchone():
                logger.warning(f"Table {table_name} not found in SQLite, skipping")
                return 0

        # Read data from SQLite
        df = pd.read_sql_table(table_name, sqlite_engine)

        if df.empty:
            logger.info(f"Table {table_name} is empty, skipping")
            return 0

        # Transform data for PostgreSQL
        df = self._transform_data_for_postgres(df, table_name)

        # Write to PostgreSQL
        df.to_sql(
            table_name, postgres_engine, if_exists="append", index=False, method="multi"
        )

        return len(df)

    def _transform_data_for_postgres(
        self, df: pd.DataFrame, table_name: str
    ) -> pd.DataFrame:
        """Transform data to match PostgreSQL schema"""

        # Convert datetime columns
        datetime_columns = [
            "created_at",
            "updated_at",
            "scraped_at",
            "triggered_at",
            "added_at",
            "first_tracked_at",
            "last_updated_at",
        ]
        for col in datetime_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])

        # Handle JSON columns
        json_columns = ["bsr_data", "raw_data", "metadata", "settings"]
        for col in json_columns:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: json.dumps(x) if x and not isinstance(x, str) else x
                )

        # Table-specific transformations
        if table_name == "product_snapshots":
            # Ensure scraped_at is not null
            if "scraped_at" in df.columns:
                df["scraped_at"] = df["scraped_at"].fillna(datetime.now())

            # Convert bullet_points to PostgreSQL array format
            if "bullet_points" in df.columns:
                df["bullet_points"] = df["bullet_points"].apply(
                    lambda x: (
                        x if isinstance(x, list) else [] if pd.isna(x) else [str(x)]
                    )
                )

        # Remove any None values that should be handled by defaults
        df = df.where(pd.notnull(df), None)

        return df

    def _create_postgres_indexes(self, postgres_engine):
        """Create optimized indexes for PostgreSQL"""

        index_sql = """
        -- Primary performance indexes
        CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
        CREATE INDEX IF NOT EXISTS idx_products_last_updated ON products(last_updated_at);
        CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);
        CREATE INDEX IF NOT EXISTS idx_products_metadata ON products USING GIN(metadata);
        
        -- Product snapshots indexes
        CREATE INDEX IF NOT EXISTS idx_snapshots_asin_time ON product_snapshots(asin, scraped_at DESC);
        CREATE INDEX IF NOT EXISTS idx_snapshots_price ON product_snapshots(price) WHERE price IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_snapshots_rating ON product_snapshots(rating) WHERE rating IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_snapshots_bsr ON product_snapshots USING GIN(bsr_data);
        
        -- Competitive analysis indexes
        CREATE INDEX IF NOT EXISTS idx_competitive_groups_main_asin ON competitive_groups(main_product_asin);
        CREATE INDEX IF NOT EXISTS idx_competitive_groups_active ON competitive_groups(is_active);
        CREATE INDEX IF NOT EXISTS idx_group_members_group_id ON competitive_group_members(group_id);
        CREATE INDEX IF NOT EXISTS idx_group_members_asin ON competitive_group_members(competitor_asin);
        
        -- Alert system indexes
        CREATE INDEX IF NOT EXISTS idx_alerts_asin_time ON price_alerts(asin, triggered_at DESC);
        CREATE INDEX IF NOT EXISTS idx_alerts_severity ON price_alerts(severity);
        CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON price_alerts(is_resolved) WHERE is_resolved = false;
        
        -- API keys indexes
        CREATE UNIQUE INDEX IF NOT EXISTS idx_api_keys_key_id ON api_keys(key_id);
        CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
        CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);
        """

        with postgres_engine.connect() as conn:
            conn.execute(text(index_sql))
            conn.commit()

        logger.info("✅ PostgreSQL indexes created successfully")

    def _verify_migration(self, sqlite_engine, postgres_engine) -> Dict[str, Any]:
        """Verify migration data integrity"""
        verification = {
            "table_counts": {},
            "data_integrity_checks": {},
            "missing_records": [],
            "success": True,
        }

        tables = ["products", "product_snapshots", "price_alerts"]

        for table in tables:
            try:
                # Count records in both databases
                with sqlite_engine.connect() as conn:
                    sqlite_count = conn.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    ).scalar()

                with postgres_engine.connect() as conn:
                    postgres_count = conn.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    ).scalar()

                verification["table_counts"][table] = {
                    "sqlite": sqlite_count,
                    "postgresql": postgres_count,
                    "match": sqlite_count == postgres_count,
                }

                if sqlite_count != postgres_count:
                    verification["success"] = False
                    verification["missing_records"].append(
                        f"{table}: SQLite={sqlite_count}, PostgreSQL={postgres_count}"
                    )

            except Exception as e:
                logger.error(f"Verification failed for {table}: {str(e)}")
                verification["success"] = False

        return verification

    def create_sample_api_key(self, postgres_engine) -> str:
        """Create a sample API key for testing"""
        import secrets
        import hashlib

        # Generate API key
        key_id = f"sk_live_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key_id.encode()).hexdigest()

        insert_sql = """
        INSERT INTO api_keys (key_id, key_hash, name, key_type, permissions, rate_limit_tier)
        VALUES (:key_id, :key_hash, :name, :key_type, :permissions, :tier)
        """

        with postgres_engine.connect() as conn:
            conn.execute(
                text(insert_sql),
                {
                    "key_id": key_id,
                    "key_hash": key_hash,
                    "name": "Default Development Key",
                    "key_type": "secret",
                    "permissions": json.dumps(
                        [
                            "read:products",
                            "write:products",
                            "read:competitive",
                            "write:competitive",
                            "read:alerts",
                        ]
                    ),
                    "tier": "pro",
                },
            )
            conn.commit()

        return key_id


def main():
    """Main migration function"""
    print("🚀 Starting Amazon Insights Database Migration")
    print("=" * 60)

    try:
        migrator = DatabaseMigrator()
        results = migrator.migrate_data()

        if results["success"]:
            print("✅ Migration completed successfully!")
            print(f"📊 Tables migrated: {len(results['tables_migrated'])}")
            print(f"📈 Total records: {sum(results['records_migrated'].values())}")

            # Create sample API key
            postgres_engine = create_engine(migrator.postgres_url)
            sample_key = migrator.create_sample_api_key(postgres_engine)
            print(f"🔑 Sample API key created: {sample_key}")
            print("\n⚠️  Save this API key for testing! It won't be shown again.")

        else:
            print("❌ Migration failed or completed with errors")
            for error in results.get("errors", []):
                print(f"   Error: {error}")

        # Save migration report
        with open("migration_report.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Migration report saved to: migration_report.json")

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return 1

    return 0 if results["success"] else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
