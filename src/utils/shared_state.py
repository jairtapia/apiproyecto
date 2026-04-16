# In-memory shared state for user synchronization data
# user_id -> sync_data structure

user_sync_data: dict[str, list] = {}

# user_id -> pairing_code
active_pairing_codes: dict[str, str] = {}
