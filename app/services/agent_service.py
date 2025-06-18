from langchain_core.tools import tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_qdrant import Qdrant
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage
from app.core.config import settings
from app.services.booking_service import schedule_interview
from app.core.dependencies import AsyncSessionLocal

# --- 1. Define Agent State ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# --- 2. Define Tools (Fully Asynchronous) ---

@tool
async def document_retriever(query: str) -> str:
    """Asynchronously retrieves relevant information from ingested documents based on a user's query."""
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004", 
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Create the Qdrant store
        qdrant_store = Qdrant.from_existing_collection(
            embedding=embeddings,
            collection_name=settings.QDRANT_COLLECTION_NAME,
            url=settings.QDRANT_URL
        )
        retriever = qdrant_store.as_retriever(search_kwargs={"k": 3})
        
        # Use the asynchronous '.ainvoke()' method
        docs = await retriever.ainvoke(query)
        
        if not docs:
            return "No relevant information found in the documents matching that query."
        return "\n---\n".join([doc.page_content for doc in docs])
    except Exception as e:
        return f"Error retrieving documents: {str(e)}"

@tool
async def book_interview(full_name: str, email: str, date: str, time: str) -> str:
    """Books an interview for the given name, email, date, and time."""
    try:
        async with AsyncSessionLocal() as session:
            result = await schedule_interview(
                db=session,
                full_name=full_name,
                email=email,
                interview_date=date,
                interview_time=time
            )
            return result
    except Exception as e:
        return f"Error booking interview: {str(e)}"

tools = [document_retriever, book_interview]
tool_executor = ToolNode(tools)

# --- 3. Create the Agent Logic ---
system_prompt = (
    "You are a helpful assistant for Palm Mind Technology. "
    "Your primary goal is to answer user questions based on the documents provided. "
    "To do this, you MUST first use the 'document_retriever' tool. "
    "If a user asks to book an interview, you MUST use the 'book_interview' tool. "
    "Before calling the booking tool, ensure you have collected the user's full name, email, desired date, and time. "
    "If you don't have all the information, ask clarifying questions. "
    "Do not make up information. If the retriever finds nothing, say so. "
    "After a tool is used, summarize the result for the user (e.g., 'I have booked your interview.' or 'Based on the document, the answer is...')."
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    google_api_key=settings.GOOGLE_API_KEY
)
llm_with_tools = llm.bind_tools(tools)

# --- 4. Define Graph Nodes (Fully Asynchronous) ---

async def agent_node(state: AgentState):
    """Invokes the LLM asynchronously to decide the next action."""
    try:
        # Add system message to the beginning if not already present
        messages = state["messages"]
        if not messages or not any("Palm Mind Technology" in str(msg) for msg in messages[:1]):
            from langchain_core.messages import SystemMessage
            messages = [SystemMessage(content=system_prompt)] + list(messages)
        
        response = await llm_with_tools.ainvoke(messages)
        # Return a dictionary that matches the AgentState structure
        return {"messages": [response]}
    except Exception as e:
        from langchain_core.messages import AIMessage
        error_msg = AIMessage(content=f"I apologize, but I encountered an error: {str(e)}")
        return {"messages": [error_msg]}

# --- 5. Define Graph Edges (Conditional Logic) ---
def should_continue(state: AgentState) -> str:
    """Decides the next step after the agent node."""
    try:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END
    except Exception:
        return END

# --- 6. Construct and Compile the Graph ---
graph_builder = StateGraph(AgentState)

graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_executor)

graph_builder.set_entry_point("agent")
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", END: END},
)
graph_builder.add_edge("tools", "agent")

agent_runnable = graph_builder.compile()
