# FALEORA Backend Domain Model Blueprint

This document defines the initial shared data model for web, iOS, Android, Business, Admin and Enterprise clients.

## Core user domain
- users: identity, locale, timezone, consent state, plan
- profiles: optional birth data, preferences, personalization settings
- journeys: goal, duration, progress, milestones
- daily_checkins: mood, note, energy, user-owned private data
- tarot_draws: spread type, cards, interpretation metadata
- coffee_readings: media references, detected symbols, reading result metadata
- dream_entries: text/audio reference, extracted symbols, user notes
- memories: user-created memory capsules
- future_messages: future-me capsule, unlock_at
- collections: tarot cards, symbols, badges, city/venue stamps
- relationship_spaces: explicit participant membership and sharing permissions
- oracle_sessions: user prompts, permitted context references, response metadata

## Places and loyalty
- venues: public venue profile
- venue_locations: branch/store records
- tables: optional table identifiers
- qr_tokens: signed, expiring QR/NFC tokens
- campaigns: eligibility, reward, dates, limits
- redemptions: validated reward usage
- loyalty_memberships: explicit opt-in membership
- loyalty_events: visit/stamp/reward activity
- passports: city/venue discovery progress
- events: FALEORA Night / venue experiences

## Business domain
- businesses: legal/business account
- business_members: staff membership
- business_roles: owner, manager, waiter, cashier, campaign_manager
- business_invites: expiring staff invitations
- subscriptions: business SaaS plan
- business_metrics_daily: aggregated venue performance only

## Partner / network domain
- partners: representative/agency account
- partner_regions: country/region/city responsibility
- partner_leads: prospective venues
- commissions: rules and settlements

## Enterprise domain
- enterprise_accounts
- enterprise_markets
- enterprise_stores
- enterprise_experiences
- enterprise_campaigns
- experiments
- integrations
- event_exports

## Platform governance
- consents: purpose-based user consent
- audit_logs: privileged actions
- notifications: user-configurable delivery preferences
- feature_flags: rollout and A/B flags
- abuse_events: QR, reward and account abuse signals

## Privacy boundaries
1. Private fortune, dream, relationship, journal and Oracle content must not be exposed to venue/business dashboards.
2. Business analytics use aggregated operational events unless a user has explicitly joined a loyalty program and consented to permitted uses.
3. Relationship spaces require explicit membership and per-content sharing controls.
4. Oracle context must be permission-scoped and traceable to source records shown to the user.
5. QR/NFC redemption should use signed expiring tokens, rate limits and server-side validation.

## Suggested API surface
- /api/v1/auth
- /api/v1/me
- /api/v1/daily
- /api/v1/journeys
- /api/v1/oracle
- /api/v1/readings
- /api/v1/dreams
- /api/v1/memories
- /api/v1/places
- /api/v1/passport
- /api/v1/business
- /api/v1/admin
- /api/v1/enterprise

## Production note
The current GitHub Pages project is a front-end demonstration only. Authentication, payments, personal data, QR rewards and partner analytics must move to a real backend before production use.