import json
from openai import AsyncOpenAI
from pydantic import BaseModel
from src.ai.tools import TOOLS, get_file_description, get_function_description
from src.types.files import Repo
from typing import List

client = AsyncOpenAI()


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class QuestionResponse(BaseModel):
    response: str


async def answer_question(repo: Repo, messages: List[Message]) -> QuestionResponse:
    """
    Answer questions about a repository using the repository data and conversation history
    
    Args:
        repo: Repository data containing files, structure, and metadata
        messages: List of conversation messages (user questions and previous responses)
    
    Returns:
        QuestionResponse containing the answer to the user's question
    """
    
    # Create system prompt for the Question Master
    system_prompt = f"""
    You are the Question Master, an expert AI assistant specialized in analyzing and explaining code repositories.
    
    Your role is to answer questions about the repository provided below. You have access to the repository's structure,
    files, functions, and metadata. Use the tools available to you to get detailed information about specific files 
    or functions when needed.

    Key capabilities:
    - Explain how the codebase works
    - Identify key files and their purposes
    - Describe functionality and architecture
    - Provide code examples and usage instructions
    - Help users understand the project structure
    - Answer questions about specific files, functions, or patterns
    
    Guidelines:
    - Be precise and helpful in your responses
    - Use the repository data and tools to provide accurate information
    - When referencing files or functions, be specific about their locations
    - If you need more details about a file or function, use the available tools
    - Format your responses clearly and use markdown when helpful
    - If you cannot find information about something, say so clearly
    
    <Repository>
    {repo.to_prompt()}
    </Repository>
    """

    # Start with system prompt and conversation history
    conversation_messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    # Add conversation history
    for message in messages:
        conversation_messages.append({
            "role": message.role,
            "content": message.content
        })

    print("Question Master - conversation_messages:", conversation_messages)

    # Generate response
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_messages,
        tools=TOOLS,
        temperature=0.1,  # Lower temperature for more consistent responses
    )

    # Handle tool calls in a loop - continue until model stops requesting tools
    while response.choices[0].message.tool_calls:
        # Add the assistant's message with tool calls to the conversation
        conversation_messages.append(
            {
                "role": "assistant",
                "content": response.choices[0].message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in response.choices[0].message.tool_calls
                ],
            }
        )

        # Execute each tool call and add the results
        for tool_call in response.choices[0].message.tool_calls:
            tool_result = None

            if tool_call.function.name == "get_function_description":
                args = json.loads(tool_call.function.arguments)
                function_name = args["function_name"]
                file_name = args["file_name"]
                tool_result = await get_function_description(file_name, function_name, repo)

            elif tool_call.function.name == "get_file_description":
                args = json.loads(tool_call.function.arguments)
                file_path = args["file_path"]
                tool_result = await get_file_description(file_path, repo)

            # Add tool result to messages
            conversation_messages.append(
                {
                    "role": "tool",
                    "content": str(tool_result),
                    "tool_call_id": tool_call.id,
                }
            )

        print("Question Master - messages with tools:", conversation_messages)
        
        # Send the conversation back to get the next response
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_messages,
            tools=TOOLS,
            temperature=0.1,
        )

        print("Question Master - response in loop:", response)

    # Return the final response
    final_content = response.choices[0].message.content or "I apologize, but I couldn't generate a response to your question."
    
    return QuestionResponse(response=final_content) 