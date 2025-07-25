import json
from openai import AsyncOpenAI
from pydantic import BaseModel
from src.ai.tools import TOOLS, get_file_description, get_function_description
from src.types.files import Repo

client = AsyncOpenAI()


class OverviewSummary(BaseModel):
    class KeyFunctionality(BaseModel):
        veryShortDescription: str
        description: str
        referenceFile: str
        explaination: str

    summary: str
    keyFunctionality: list[KeyFunctionality]


async def get_repo_overview(repo: Repo) -> OverviewSummary:

    # Create system prompt for repo summary generation
    system_prompt = f"""
    You are expert programmer and software engineer. Your goal is to analyze repo given below and provide summary and key functionality of the repo.

    If you need more data about specific file or function, use tool provided to you.

    The summary should be written in markdown format.

    For each key functionality, provide description for this feature, file that you based your analysis on and explaination for why this you included this file in your analysis.

    <Repo>
    {repo.to_prompt()}
    </Repo>
    """

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    print("system_prompt", system_prompt)

    # Generate repo summary
    response = await client.beta.chat.completions.parse(
        model="o4-mini",
        messages=messages,
        tools=TOOLS,
        response_format=OverviewSummary,
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

        print("messages", messages)
        # Send the conversation back to get the next response
        response = await client.beta.chat.completions.parse(
            model="o4-mini",
            messages=messages,
            tools=TOOLS,
            response_format=OverviewSummary,
        )

        print("response in loop", response)

    # Return the final response when no more tool calls are requested
    return response.choices[0].message.parsed
