--- Enter to campus_picks, run sqlite3 db.sqlite3 and run this script
-- to delete all data from the database

PRAGMA foreign_keys = OFF;

DELETE FROM acid_db_bet;
DELETE FROM acid_db_event_home_team;
DELETE FROM acid_db_event_away_team;
DELETE FROM acid_db_event;
DELETE FROM acid_db_team;
DELETE FROM acid_db_user;

PRAGMA foreign_keys = ON;

DELETE FROM sqlite_sequence WHERE name='acid_db_bet';