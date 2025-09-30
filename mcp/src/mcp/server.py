import click
from fastmcp import FastMCP
from mcp.prompt_templates import (
    fetch_conversational_assistant_prompt,
    fetch_decision_routing_prompt,
    fetch_function_selection_prompt,
)
from mcp.resources import retrieve_all_tables
from mcp.tools import (
    analyze_media_content,
    answer_question_about_content,
    extract_clip_from_user_query,
    extract_clip_from_visual_query,
)


def register_mcp_tools(mcp_server: FastMCP):
    mcp_server.add_tool(
        name="analyze_media_content",
        description="Process a media file and prepare it for searching.",
        fn=analyze_media_content,
        tags={"media", "process"},
    )
    mcp_server.add_tool(
        name="extract_clip_from_user_query",
        description="Use this tool to get a media clip from a media file based on a user query or question.",
        fn=extract_clip_from_user_query,
        tags={"media", "clip", "query", "question"},
    )
    mcp_server.add_tool(
        name="extract_clip_from_visual_query",
        description="Use this tool to get a media clip from a media file based on a user image.",
        fn=extract_clip_from_visual_query,
        tags={"media", "clip", "image"},
    )
    mcp_server.add_tool(
        name="answer_question_about_content",
        description="Use this tool to get an answer to a question about the media content.",
        fn=answer_question_about_content,
        tags={"ask", "question", "information"},
    )


def register_mcp_resources(mcp_server: FastMCP):
    mcp_server.add_resource_fn(
        fn=retrieve_all_tables,
        uri="file:///app/.storage_records/records.json",
        name="retrieve_all_tables",
        description="List all media indexes currently available.",
        tags={"resource", "all"},
    )


def register_mcp_prompts(mcp_server: FastMCP):
    mcp_server.add_prompt(
        fn=fetch_decision_routing_prompt,
        name="fetch_decision_routing_prompt",
        description="Latest version of the routing prompt from Opik.",
        tags={"prompt", "routing"},
    )
    mcp_server.add_prompt(
        fn=fetch_function_selection_prompt,
        name="fetch_function_selection_prompt",
        description="Latest version of the tool use prompt from Opik.",
        tags={"prompt", "tool_use"},
    )
    mcp_server.add_prompt(
        fn=fetch_conversational_assistant_prompt,
        name="fetch_conversational_assistant_prompt",
        description="Latest version of the general prompt from Opik.",
        tags={"prompt", "general"},
    )


mcp_server = FastMCP("MediaAnalyzer")

register_mcp_prompts(mcp_server)
register_mcp_tools(mcp_server)
register_mcp_resources(mcp_server)


@click.command()
@click.option("--port", default=9090, help="FastMCP server port")
@click.option("--host", default="0.0.0.0", help="FastMCP server host")
@click.option("--transport", default="streamable-http", help="MCP Transport protocol type")
def start_mcp_server(port, host, transport):
    """
    Run the FastMCP server with the specified port, host, and transport protocol.
    """
    mcp_server.run(host=host, port=port, transport=transport)


if __name__ == "__main__":
    start_mcp_server()