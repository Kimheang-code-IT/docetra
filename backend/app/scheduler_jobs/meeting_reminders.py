from app.core.messaging import publish
async def run(meeting_id:str): await publish("meeting.reminder",{"meetingId":meeting_id})
