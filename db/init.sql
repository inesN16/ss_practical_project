CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_disabled BOOLEAN DEFAULT FALSE
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES users(id),
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    metadata TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE document_shares (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    shared_with INTEGER REFERENCES users(id)
);

-- ---------------------------------------------------------------------------
-- IMPORTANT — VALIDATOR ACCOUNTS
--
-- The following user accounts are required for the automated validation
-- system used in the course. These accounts MUST always exist in the system.
--
-- The usernames and logical identities of these accounts must NOT be removed
-- or changed, as the validator depends on them to execute security tests.
--
-- The validator authenticates using the plaintext credentials defined below.
-- Therefore:
--
--  • These credentials must remain valid for authentication.
--  • The passwords themselves must not be changed.
--
-- You are free to improve the authentication system (e.g., password hashing,
-- stronger password policies, etc.). If you implement password hashing or
-- other changes to the login mechanism, ensure that the credentials below
-- still successfully authenticate.
--
-- In other words: the authentication implementation may change, but the
-- following username/password combinations must continue to work.
--
-- These accounts are used by the automated validator to test:
--   • authentication
--   • authorization
--   • document sharing
--   • access control
--   • administrative operations
--
-- Removing or altering these accounts will cause automated validation to fail.
-- ---------------------------------------------------------------------------
INSERT INTO users (username, password, is_disabled) VALUES
('admin', 'scrypt:32768:8:1$ZT5BuUrfUDH0lckh$1fbc42e3011e9aca0e83bd025a98e7b212c32e872f8843701db758ed9f03a13e5d370a8e893415fa22ee3baa8e17392eff138c9b71eca103244d25ddbafbc67d', FALSE),
('alice', 'scrypt:32768:8:1$VjQNgoJAXrbZKiPd$0e2bf386f9fee2bdb5a510d1170c1d7f4b04355045598e55b4c39f3204f48e19fb17d1b17a9c5c0058ea4a61ce06430f3db9ac65bb5d02ee6d761774c1de0f43', FALSE),
('bob',  'scrypt:32768:8:1$hzG6zkf2gUNJJtTD$60acc46f018ef3fb161ef82185f4bd5036848651d8c577516039959568a6f2b42ecacea891df998d0668d3e114c21b234344830f93cc54d999bc94b1e779da7b', FALSE);