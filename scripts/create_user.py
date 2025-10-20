"""
Script to manually create users and generate API tokens.

Create as: scripts/create_user.py

Usage:
    python scripts/create_user.py --username alice --email alice@gmail.com --password temp123

Output:
    User created: alice (alice@gmail.com)
    API Token: vba_abc123def456...
"""
import asyncio
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.auth_service import AuthService
from app.db.database import init_db
from config import logger


async def main():
    parser = argparse.ArgumentParser(description='Create user and generate API token')
    parser.add_argument('--username', required=True, help='Username (alphanumeric, 3-30 chars)')
    parser.add_argument('--email', required=True, help='Email address')
    parser.add_argument('--password', required=True, help='Password (min 8 chars)')
    parser.add_argument('--token-name', default=None, help='Optional token name (e.g., "CLI Token")')

    args = parser.parse_args()

    # Initialize database
    await init_db()

    auth_service = AuthService()

    # Create user
    print(f"\nCreating user: {args.username}")
    user, error = await auth_service.create_user(
        username=args.username,
        email=args.email,
        password=args.password
    )

    if error:
        print(f"❌ Error: {error}")
        sys.exit(1)

    print(f"✅ User created: {user.username} ({user.email})")
    print(f"   User ID: {user.id}")

    # Generate API token
    print(f"\nGenerating API token...")
    token, api_token = await auth_service.create_api_token(
        user_id=str(user.id),
        name=args.token_name or f"{user.username}'s Token"
    )

    print(f"✅ API Token generated")
    print(f"\n{'=' * 70}")
    print(f"API Token (save this - it won't be shown again):")
    print(f"\n{token}\n")
    print(f"{'=' * 70}")
    print(f"\nTo use this token:")
    print(f"1. Save it to ~/.ragagent/config.json:")
    print(f'   echo \'{{"api_token": "{token}"}}\' > ~/.ragagent/config.json')
    print(f"\n2. Or use it in API requests:")
    print(f'   curl -H "Authorization: Bearer {token}" http://localhost:8000/me')
    print(f"\n")


if __name__ == "__main__":
    asyncio.run(main())