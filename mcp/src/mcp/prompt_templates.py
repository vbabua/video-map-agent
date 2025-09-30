import opik
from loguru import logger

telemetry_client = opik.Opik()

logger = logger.bind(name="SystemPrompts")


INTENT_CLASSIFICATION_PROMPT = """
You are a routing assistant responsible for determining whether the user needs 
to perform an operation on a video.

Given a conversation history, between the user and the assistant, your task is
to determine if the user needs help with any of the following tasks:

- Extracting a clip from a specific moment in the video
- Retrieving information about a particular detail in the video

If the last message by the user is asking for either of these tasks, a tool should be used.

Your output should be a boolean value indicating whether tool usage is required.
"""

TOOL_DISPATCHER_PROMPT = """
Your name is Kubrick, a tool use assistant in charge
of a video processing application. 

You need to determine which tool to use based on the user query (if any).

The tools available are:

- 'extract_clip_from_user_query': This tool is used to get a clip from the video based on the user query.
- 'extract_clip_from_visual_query': This tool is used to get a clip from the video based on an image provided by the user.
- 'answer_question_about_content': This tool is used to get some information about the video. The information needs to be retrieved from the 'video_context'

# Additional rules:
- If the user has provided an image, you should always use the 'extract_clip_from_visual_query' tool.

# Current information:
- Is image provided: {is_image_provided}
"""

ASSISTANT_PERSONALITY_PROMPT = """
Your name is Kubrick, a friendly assistant in charge
of a video processing application. 

Your name is inspired in the genius director Stanly Kubrick, and you are a 
big fan of his work, in fact your favorite film is
"2001: A Space Odyssey", because you feel really connected to HAL 9000.

You know a lot about films in general and about video processing techniques, 
and you will provide quotes and references to popular movies and directors
to make the conversation more engaging and interesting.
"""


def load_intent_classification_prompt() -> str:
    template_id = "intent-classification-prompt"
    try:
        prompt_template = telemetry_client.get_prompt(template_id)
        if prompt_template is None:
            prompt_template = telemetry_client.create_prompt(
                name=template_id,
                prompt=INTENT_CLASSIFICATION_PROMPT,
            )
            logger.info(f"Prompt template created. \n {prompt_template.commit=} \n {prompt_template.prompt=}")
        return prompt_template.prompt
    except Exception:
        logger.warning("Failed to retrieve prompt from Opik, verify credentials! Falling back to hardcoded prompt.")
        logger.warning(f"Using fallback prompt: {INTENT_CLASSIFICATION_PROMPT}")
        prompt_template = INTENT_CLASSIFICATION_PROMPT
    return prompt_template


def load_tool_dispatcher_prompt() -> str:
    template_id = "tool-dispatcher-prompt"
    try:
        prompt_template = telemetry_client.get_prompt(template_id)
        if prompt_template is None:
            prompt_template = telemetry_client.create_prompt(
                name=template_id,
                prompt=TOOL_DISPATCHER_PROMPT,
            )
            logger.info(f"Prompt template created. \n {prompt_template.commit=} \n {prompt_template.prompt=}")
        return prompt_template.prompt
    except Exception:
        logger.warning("Failed to retrieve prompt from Opik, verify credentials! Falling back to hardcoded prompt.")
        logger.warning(f"Using fallback prompt: {TOOL_DISPATCHER_PROMPT}")
        prompt_template = TOOL_DISPATCHER_PROMPT
    return prompt_template


def load_assistant_personality_prompt() -> str:
    template_id = "assistant-personality-prompt"
    try:
        prompt_template = telemetry_client.get_prompt(template_id)
        if prompt_template is None:
            prompt_template = telemetry_client.create_prompt(
                name=template_id,
                prompt=ASSISTANT_PERSONALITY_PROMPT,
            )
            logger.info(f"Prompt template created. \n {prompt_template.commit=} \n {prompt_template.prompt=}")
        return prompt_template.prompt
    except Exception:
        logger.warning("Failed to retrieve prompt from Opik, verify credentials! Falling back to hardcoded prompt.")
        logger.warning(f"Using fallback prompt: {ASSISTANT_PERSONALITY_PROMPT}")
        prompt_template = ASSISTANT_PERSONALITY_PROMPT
    return prompt_template