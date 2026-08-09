import asyncio
from core.database import init_db
from modules.models import ElectionSchema

async def run_debug():
    print("Connecting to DB...")
    await init_db()
    
    print("Fetching all elections...")
    elections = await ElectionSchema.find_all().to_list()
    
    print(f"Found {len(elections)} elections:")
    for e in elections:
        print(f" - {e.election_code} (Candidates: {len(e.candidates)})")

if __name__ == "__main__":
    # This magically handles the async event loop for you
    asyncio.run(run_debug())