"""
🗄️ SUPABASE DATABASE INTEGRATION
Production-ready database for Travel Planner scaling
"""

import os
import streamlit as st
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TravelPlannerDB:
    def __init__(self):
        """Initialize Supabase connection"""
        self.supabase_url = os.getenv('SUPABASE_URL', '')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY', '')
        
        if self.supabase_url and self.supabase_key:
            try:
                from supabase import create_client
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                self.connected = True
                print("🗄️ Connected to Supabase Database")
            except ImportError:
                st.error("📦 Please install supabase: pip install supabase")
                self.connected = False
            except Exception as e:
                st.error(f"❌ Database connection failed: {e}")
                self.connected = False
        else:
            self.connected = False
    
    def save_email_signup(self, email, source="travel_planner", marketing_optin=True):
        """Save email signup to database"""
        if not self.connected:
            return False
        
        try:
            data = {
                'email': email,
                'signup_date': datetime.now().isoformat(),
                'source': source,
                'marketing_optin': marketing_optin,
                'ip_address': self._get_user_ip()
            }
            
            result = self.supabase.table('email_signups').insert(data).execute()
            return True
            
        except Exception as e:
            st.error(f"Database error: {e}")
            return False
    
    def track_user_event(self, email, event_type, event_data=None):
        """Track user events for analytics"""
        if not self.connected:
            return False
        
        try:
            data = {
                'email': email,
                'event_type': event_type,
                'event_data': event_data or {},
                'timestamp': datetime.now().isoformat(),
                'session_id': st.session_state.get('session_id', 'unknown')
            }
            
            result = self.supabase.table('user_events').insert(data).execute()
            return True
            
        except Exception as e:
            print(f"Event tracking error: {e}")
            return False
    
    def save_travel_plan(self, email, destination, plan_data):
        """Save generated travel plan"""
        if not self.connected:
            return False
        
        try:
            data = {
                'user_email': email,
                'destination': destination,
                'plan_data': plan_data,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('travel_plans').insert(data).execute()
            return True
            
        except Exception as e:
            print(f"Travel plan save error: {e}")
            return False
    
    def get_analytics_data(self, days=30):
        """Get analytics data for dashboard"""
        if not self.connected:
            return {}
        
        try:
            # Get email signups
            signups = self.supabase.table('email_signups').select("*").execute()
            
            # Get user events
            events = self.supabase.table('user_events').select("*").execute()
            
            # Get travel plans
            plans = self.supabase.table('travel_plans').select("*").execute()
            
            return {
                'signups': signups.data,
                'events': events.data,
                'plans': plans.data
            }
            
        except Exception as e:
            print(f"Analytics query error: {e}")
            return {}
    
    def _get_user_ip(self):
        """Get user IP address (simplified)"""
        try:
            import requests
            return requests.get('https://api.ipify.org', timeout=2).text
        except:
            return 'unknown'

# Database setup SQL (run once in Supabase)
SETUP_SQL = """
-- Email signups table
CREATE TABLE IF NOT EXISTS email_signups (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR NOT NULL,
    signup_date TIMESTAMP DEFAULT NOW(),
    source VARCHAR DEFAULT 'travel_planner',
    marketing_optin BOOLEAN DEFAULT true,
    ip_address VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User events table for analytics
CREATE TABLE IF NOT EXISTS user_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    event_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    session_id VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Travel plans table
CREATE TABLE IF NOT EXISTS travel_plans (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_email VARCHAR NOT NULL,
    destination VARCHAR NOT NULL,
    plan_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Users table (for future authentication)
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT false,
    password_hash VARCHAR,
    profile_data JSONB,
    subscription_tier VARCHAR DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_email_signups_email ON email_signups(email);
CREATE INDEX IF NOT EXISTS idx_user_events_email ON user_events(email);
CREATE INDEX IF NOT EXISTS idx_user_events_type ON user_events(event_type);
CREATE INDEX IF NOT EXISTS idx_travel_plans_email ON travel_plans(user_email);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
"""

# Initialize database connection
db = TravelPlannerDB()
