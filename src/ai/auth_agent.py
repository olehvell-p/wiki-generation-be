import json
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel
from src.ai.tools import TOOLS, get_file_description, get_function_description
from src.types.files import Repo

client = AsyncOpenAI()


class AuthAnalysis(BaseModel):

    class AuthFile(BaseModel):
        fileName: str
        explaination: str

    summary: str
    relevantFiles: list[AuthFile]


async def get_auth_analysis(repo: Repo, summary: str) -> AuthAnalysis:
    system_prompt = f"""
    You are expert programmer and software engineer. Your goal is to analyze repo given below and provide auth analysis of the repo.

    For example, explain authentication methods, authentication flow, security measures, access control, session management, authorization mechanisms, security vulnerabilities, etc.

    If you need more data about specific file or function, use tool provided to you.

    The summary should be written in markdown format.

    For each auth analysis, provide a reference file where you found this auth analysis and explaination for why you included this file in your analysis.
    
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
        {
            "role": "user",
            "content": "Analyze the repository structure and code to understand how authentication and authorization work. Look at authentication routes, middleware, user models, session handling, and security implementations.",
        },
    ]

    response = await client.beta.chat.completions.parse(
        model="o4-mini",
        messages=messages,
        tools=TOOLS,
        response_format=AuthAnalysis,
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
                tool_result = await  get_function_description(file_name, function_name, repo)

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
            response_format=AuthAnalysis,
        )

        print("response in loop", response)

    # Return the final response when no more tool calls are requested
    return response.choices[0].message.parsed
