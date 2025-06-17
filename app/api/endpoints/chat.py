from fastapi import APIRouter, HTTPException, Body
from langchain_core.messages import HumanMessage, AIMessage
from langchain_redis.chat_message_history import RedisChatMessageHistory
from app.services.agent_service import agent_runnable
from app.core.config import settings

router = APIRouter()

def get_session_history(session_id: str) -> RedisChatMessageHistory:
    return RedisChatMessageHistory(session_id, url=settings.REDIS_URL)

@router.post("/invoke")
async def invoke_agent(
    session_id: str = Body(..., embed=True),
    user_input: str = Body(..., embed=True)
):
    """
    Invokes the RAG agent with a user query and maintains conversation history.
    """
    if not session_id or not user_input:
        raise HTTPException(status_code=400, detail="session_id and user_input are required.")

    # Get chat history from Redis
    history = get_session_history(session_id)
    
    # Wrap the logic in a config to pass down history
    config = {"configurable": {"session_id": session_id}}

    try:
        # The agent expects a list of messages. We add the new human message.
        messages = history.messages
        messages.append(HumanMessage(content=user_input))

        # Invoke the agent graph
        response_ai_message = await agent_runnable.ainvoke({"messages": messages}, config)
        
        # The actual response content might be in the last AI message
        # LangGraph returns the full state, so we extract the last message
        final_response = response_ai_message['messages'][-1].content
        
        # Save the full turn (human input + AI response) to history
        await history.aadd_user_message(user_input)
        await history.aadd_ai_message(final_response)

        return {"response": final_response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent invocation failed: {str(e)}")