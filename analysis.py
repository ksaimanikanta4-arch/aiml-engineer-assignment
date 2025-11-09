"""
Data Analysis Script
Analyzes the member messages dataset for anomalies and inconsistencies
"""

import httpx
import asyncio
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Set
import json


EXTERNAL_API_BASE_URL = "https://november7-730026606190.europe-west1.run.app"


async def fetch_all_messages():
    """Fetch all messages from the API"""
    all_messages = []
    skip = 0
    limit = 100
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        while True:
            try:
                response = await client.get(
                    f"{EXTERNAL_API_BASE_URL}/messages/",
                    params={"skip": skip, "limit": limit}
                )
                response.raise_for_status()
                data = response.json()
                
                messages = data.get("items", [])
                if not messages:
                    break
                    
                all_messages.extend(messages)
                
                if len(all_messages) >= data.get("total", 0):
                    break
                    
                skip += limit
                
            except Exception as e:
                print(f"Error: {e}")
                break
    
    return all_messages


def analyze_data(messages: List[Dict]):
    """Analyze messages for anomalies and inconsistencies"""
    
    print(f"Total messages: {len(messages)}\n")
    
    # 1. User analysis
    users_by_id = defaultdict(set)  # user_id -> set of user_names
    users_by_name = defaultdict(set)  # user_name -> set of user_ids
    user_message_count = Counter()
    
    for msg in messages:
        user_id = msg.get("user_id", "")
        user_name = msg.get("user_name", "")
        users_by_id[user_id].add(user_name)
        users_by_name[user_name].add(user_id)
        user_message_count[user_name] += 1
    
    print("=" * 60)
    print("USER ANALYSIS")
    print("=" * 60)
    print(f"Unique user IDs: {len(users_by_id)}")
    print(f"Unique user names: {len(users_by_name)}")
    
    # Check for user_id inconsistencies
    inconsistent_users = []
    for user_id, names in users_by_id.items():
        if len(names) > 1:
            inconsistent_users.append((user_id, names))
    
    if inconsistent_users:
        print(f"\n⚠️  Found {len(inconsistent_users)} user IDs with multiple names:")
        for user_id, names in inconsistent_users[:5]:
            print(f"  User ID {user_id}: {names}")
    else:
        print("✓ User IDs are consistent (one name per ID)")
    
    # Check for user_name inconsistencies
    inconsistent_names = []
    for user_name, ids in users_by_name.items():
        if len(ids) > 1:
            inconsistent_names.append((user_name, ids))
    
    if inconsistent_names:
        print(f"\n⚠️  Found {len(inconsistent_names)} user names with multiple IDs:")
        for user_name, ids in inconsistent_names[:5]:
            print(f"  User name '{user_name}': {ids}")
    else:
        print("✓ User names are consistent (one ID per name)")
    
    # 2. Message analysis
    print("\n" + "=" * 60)
    print("MESSAGE ANALYSIS")
    print("=" * 60)
    
    message_ids = set()
    duplicate_ids = []
    empty_messages = []
    null_fields = []
    
    for msg in messages:
        msg_id = msg.get("id", "")
        if not msg_id:
            null_fields.append("id")
        elif msg_id in message_ids:
            duplicate_ids.append(msg_id)
        else:
            message_ids.add(msg_id)
        
        if not msg.get("message", "").strip():
            empty_messages.append(msg_id)
        
        if not msg.get("user_id"):
            null_fields.append("user_id")
        if not msg.get("user_name"):
            null_fields.append("user_name")
        if not msg.get("timestamp"):
            null_fields.append("timestamp")
    
    print(f"Unique message IDs: {len(message_ids)}")
    if duplicate_ids:
        print(f"⚠️  Found {len(duplicate_ids)} duplicate message IDs")
    else:
        print("✓ No duplicate message IDs")
    
    if empty_messages:
        print(f"⚠️  Found {len(empty_messages)} empty messages")
    else:
        print("✓ No empty messages")
    
    if null_fields:
        null_field_counts = Counter(null_fields)
        print(f"⚠️  Found null/empty fields:")
        for field, count in null_field_counts.items():
            print(f"  {field}: {count}")
    else:
        print("✓ No null/empty required fields")
    
    # 3. Timestamp analysis
    print("\n" + "=" * 60)
    print("TIMESTAMP ANALYSIS")
    print("=" * 60)
    
    timestamp_formats = Counter()
    invalid_timestamps = []
    
    for msg in messages:
        timestamp = msg.get("timestamp", "")
        if not timestamp:
            invalid_timestamps.append(msg.get("id", "unknown"))
            continue
        
        # Try to identify timestamp format
        if "T" in timestamp:
            timestamp_formats["ISO 8601 (with T)"] += 1
        elif "-" in timestamp and ":" in timestamp:
            timestamp_formats["Date-time format"] += 1
        else:
            timestamp_formats["Other/Unknown"] += 1
    
    print("Timestamp format distribution:")
    for fmt, count in timestamp_formats.items():
        print(f"  {fmt}: {count}")
    
    if invalid_timestamps:
        print(f"⚠️  Found {len(invalid_timestamps)} messages with invalid/missing timestamps")
    else:
        print("✓ All timestamps are valid")
    
    # 4. Message length analysis
    print("\n" + "=" * 60)
    print("MESSAGE LENGTH ANALYSIS")
    print("=" * 60)
    
    message_lengths = [len(msg.get("message", "")) for msg in messages]
    if message_lengths:
        print(f"Average message length: {sum(message_lengths) / len(message_lengths):.1f} characters")
        print(f"Shortest message: {min(message_lengths)} characters")
        print(f"Longest message: {max(message_lengths)} characters")
    
    # 5. Top users
    print("\n" + "=" * 60)
    print("TOP USERS BY MESSAGE COUNT")
    print("=" * 60)
    for user_name, count in user_message_count.most_common(10):
        print(f"  {user_name}: {count} messages")
    
    # 6. Summary
    print("\n" + "=" * 60)
    print("SUMMARY OF ISSUES")
    print("=" * 60)
    
    issues = []
    if inconsistent_users:
        issues.append(f"{len(inconsistent_users)} user IDs with multiple names")
    if inconsistent_names:
        issues.append(f"{len(inconsistent_names)} user names with multiple IDs")
    if duplicate_ids:
        issues.append(f"{len(duplicate_ids)} duplicate message IDs")
    if empty_messages:
        issues.append(f"{len(empty_messages)} empty messages")
    if null_fields:
        issues.append(f"Null/empty fields in {len(set(null_fields))} field types")
    if invalid_timestamps:
        issues.append(f"{len(invalid_timestamps)} invalid/missing timestamps")
    
    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ No major issues found in the dataset")
    
    return {
        "total_messages": len(messages),
        "unique_users": len(users_by_name),
        "inconsistent_users": len(inconsistent_users),
        "inconsistent_names": len(inconsistent_names),
        "duplicate_ids": len(duplicate_ids),
        "empty_messages": len(empty_messages),
        "invalid_timestamps": len(invalid_timestamps)
    }


async def main():
    print("Fetching messages from API...")
    messages = await fetch_all_messages()
    
    if not messages:
        print("No messages found!")
        return
    
    print(f"Fetched {len(messages)} messages\n")
    analyze_data(messages)


if __name__ == "__main__":
    asyncio.run(main())

