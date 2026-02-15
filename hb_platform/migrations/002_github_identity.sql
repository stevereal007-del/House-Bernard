-- Add GitHub identity to citizens table
-- Citizen ID ↔ GitHub Username ↔ Solana Wallet

ALTER TABLE citizens ADD COLUMN github_username TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_citizens_github
    ON citizens(github_username) WHERE github_username IS NOT NULL;
