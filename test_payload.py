"""Test script to send sample Notion webhook payload"""

import json
import httpx


# Sample Notion webhook payload
notion_payload = {
    "properties": {
        "작성일": {
            "date": {
                "start": "2025-10-18"
            }
        },
        "AI 제공자": {
            "select": {
                "name": "claude"
            }
        },
        "맛": {
            "select": {
                "name": "spicy"
            }
        },
        "사용자 ID": {
            "rich_text": [
                {
                    "plain_text": "U05258DMFEE"
                }
            ]
        }
    }
}


async def test_webhook():
    """Send test payload to local server"""

    url = "http://localhost:8000/api/notion-to-slack"

    print("📤 Sending test payload to webhook adapter...")
    print(f"Payload:\n{json.dumps(notion_payload, indent=2, ensure_ascii=False)}\n")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                json=notion_payload,
                timeout=10.0
            )

            print(f"✅ Status: {response.status_code}")
            print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")

        except httpx.ConnectError:
            print("❌ Failed to connect to server. Make sure the server is running:")
            print("   python main.py")

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_webhook())
