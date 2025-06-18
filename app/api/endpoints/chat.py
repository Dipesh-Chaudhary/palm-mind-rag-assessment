from fastapi import APIRouter, HTTPException, Body
from langchain_core.messages import HumanMessage, AIMessage
from langchain_redis.chat_message_history import RedisChatMessageHistory
from app.services.agent_service import agent_runnable
from app.core.config import settings
import traceback
import asyncio

router = APIRouter()

def get_session_history(session_id: str) -> RedisChatMessageHistory:
    """Helper function to get Redis chat history for a session."""
    return RedisChatMessageHistory(
        session_id=session_id, redis_url=settings.REDIS_URL
    )

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

    try:
        # Get chat history
        history = get_session_history(session_id)
        
        # Get existing messages
        messages = history.messages
        messages.append(HumanMessage(content=user_input))

        # Invoke the agent with proper error handling
        try:
            response_from_agent = await agent_runnable.ainvoke({"messages": messages})
        except Exception as agent_error:
            logger.error(f"Agent invocation error: {agent_error}")
            traceback.print_exc()
            # Return a fallback response
            fallback_response = "I apologize, but I'm experiencing technical difficulties. Please try again later."
            await history.aadd_messages([
                HumanMessage(content=user_input),
                AIMessage(content=fallback_response)
            ])
            return {"response": fallback_response}

        # Extract the final response
        if 'messages' in response_from_agent and response_from_agent['messages']:
            final_ai_message = response_from_agent['messages'][-1]
            final_response_content = final_ai_message.content
        else:
            final_response_content = "I'm sorry, but I couldn't process your request properly."

        # Save messages to history using async method
        try:
            await history.aadd_messages([
                HumanMessage(content=user_input),
                AIMessage(content=final_response_content)
            ])
        except Exception as history_error:
            # If saving to history fails, still return the response
            print(f"Warning: Could not save to chat history: {history_error}")

        return {"response": final_response_content}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Agent invocation failed: {str(e)}")
