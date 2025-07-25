from src.types.files import Repo
from openai import AsyncOpenAI
from pydantic import BaseModel
from src.ai.tools import TOOLS, get_function_description, get_file_description
import json

client = AsyncOpenAI()


class EntryPoints(BaseModel):

    class EntryPointFile(BaseModel):
        fileName: str
        explaination: str

    summary: str
    relevantFiles: list[EntryPointFile]


async def get_entry_points(repo: Repo, summary: str) -> EntryPoints:
    system_prompt = f"""You are expert programmer and software engineer. Your goal is to analyze repo and give explai how user can interact with the codebase.

    If it's a web app, you should return list of all api endpoints and their description.
    If it's a CLI app, you should return list of all commands and their description.
    If it's a library, you should return list of all functions and their description.
    If it's a framework, you should return list of all entry points and their description.
    If it's a tool, you should return list of all entry points and their description.
    If it's a service, you should return list of all entry points and their description.
    

    Write a summary of all entry points in Markdown format.

    For each entry point, provide a reference file where you found this entry and explaination for why you included this file in your analysis. For each entry point, provide a how to interact with this entry point. (if it's a explain types of requests)

    If you need more data about specific file or function, use tool provided to you.

    <RepoSummary>
    {summary}
    </RepoSummary>

    <Directories>
    {repo.directories}
    </Directories>

    <Files>
    {repo.files}
    </Files>
    """

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # Generate repo overview
    response = await client.beta.chat.completions.parse(
        model="o4-mini",
        messages=messages,
        tools=TOOLS,
        response_format=EntryPoints,
    )

    # Handle tool calls in a loop - continue until model stops requesting tools
    while response.choices[0].message.tool_calls:
        # Add the assistant's message with tool calls to the conversation
        messages.append(
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
            print(tool_call)
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
            messages.append(
                {
                    "role": "tool",
                    "content": str(tool_result),
                    "tool_call_id": tool_call.id,
                }
            )

        # Send the conversation back to get the next response
        response = await client.beta.chat.completions.parse(
            model="o4-mini",
            messages=messages,
            tools=TOOLS,
            response_format=EntryPoints,
        )

        print("response in loop", response)

    # Return the final response when no more tool calls are requested
    return response.choices[0].message.parsed
