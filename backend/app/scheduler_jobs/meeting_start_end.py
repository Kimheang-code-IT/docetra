from app.core.messaging import publish
async def run(meeting_id:str,event:str): await publish(f"meeting.{event}",{"meetingId":meeting_id})
