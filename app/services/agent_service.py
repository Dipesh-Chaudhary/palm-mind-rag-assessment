from langchain_core.tools import tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_qdrant import Qdrant
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage
from app.core.config import settings
from app.services.booking_service import schedule_interview
from app.core.dependencies import get_db_session  # We'll use this to pass a session to the tool

# --- 1. Define Agent State ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# --- 2. Define Tools ---
# Note: Tools need access to a DB session. We'll handle this at the endpoint level.
@tool
def document_retriever(query: str) -> str:
    """Retrieves relevant information from the ingested documents based on a user's query."""
    # This is a simplified retriever. A production one would be more complex.
    if settings.embedding_model == "google":
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=settings.GOOGLE_API_KEY)
    else:
        embeddings = HuggingFaceBgeEmbeddings(model_name="BAAI/bge-small-en-v1.5", encode_kwargs={'normalize_embeddings': True})
    
    qdrant_store = Qdrant.from_existing_collection(
        embedding=embeddings,
        collection_name=settings.QDRANT_COLLECTION_NAME,
        url=settings.QDRANT_URL
    )
    retriever = qdrant_store.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    return "\n---\n".join([doc.page_content for doc in docs])

@tool
async def book_interview(full_name: str, email: str, date: str, time: str) -> str:
    """Books an interview for the given name, email, date, and time, then sends a confirmation."""
    # The `async for` loop allows us to properly use the async generator dependency
    async for session in get_db_session():
        result = await schedule_interview(session, full_name, email, date, time)
        return result

tools = [document_retriever, book_interview]

# --- 3. Create the Agent Logic ---
# This prompt template includes tool usage instructions.
system_prompt = (
    "You are a helpful assistant for Palm Mind Technology. "
    "Your primary goal is to answer user questions based on the documents provided. "
    "Use the 'document_retriever' tool to find information. "
    "If a user wants to book an interview, you MUST use the 'book_interview' tool. "
    "Collect the user's full name, email, desired date, and time before calling the tool. "
    "Do not make up information. If you don't know the answer, say so. "
    "Respond directly to the user's last message."
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-05-20", google_api_key=settings.GOOGLE_API_KEY)

# Bind the tools to the LLM so it knows how to call them
llm_with_tools = llm.bind_tools(tools)

# --- 4. Define Graph Nodes ---
# The agent node decides whether to call a tool or respond directly
def agent_node(state):
    return llm_with_tools.invoke(state["messages"])

# The tool node executes the chosen tool
tool_node = ToolNode(tools)

# --- 5. Define Graph Edges (Conditional Logic) ---
def should_continue(state):
    last_message = state["messages"][-1]
    # If the LLM response has tool calls, we execute them
    if last_message.tool_calls:
        return "tools"
    # Otherwise, we end the conversation turn
    return END

# --- 6. Construct and Compile the Graph ---
graph_builder = StateGraph(AgentState)

graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)

graph_builder.set_entry_point("agent")
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END,
    },
)
graph_builder.add_edge("tools", "agent") # Loop back to the agent after tool execution

# The final, runnable agent
agent_runnable = graph_builder.compile()