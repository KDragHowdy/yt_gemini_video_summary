import google.generativeai as genai

model = genai.GenerativeModel("gemini-1.5-flash")


def generate_content(prompt, video_file=None):
    try:
        if video_file:
            response = model.generate_content(
                [video_file, prompt], request_options={"timeout": 600}
            )
        else:
            response = model.generate_content(prompt, request_options={"timeout": 600})

        if response.prompt_feedback:
            print(f"Prompt feedback: {response.prompt_feedback}")

        return response.text

    except Exception as e:
        print(f"Error generating content: {str(e)}")
        return f"Error in analysis: {str(e)}"


def analyze_video_content(video_file, chunk_start, chunk_end):
    prompt = f"""
    Analyze the visual content of the video from {chunk_start} to {chunk_end} minutes:

    Please provide a detailed list of observations that captures the essence of the video, including:
    1. Key visual elements and scenes
    2. Description of any visual aids (slides, charts, graphs) and their content
    3. Non-verbal cues or actions of importance
    4. Any text or captions shown on screen

    Important: Focus solely on what can be seen in the video. Do not include any audio information or spoken content in this analysis.

    Format the output as a numbered list of observations, maintaining chronological order.
    """

    return generate_content(prompt, video_file)


def analyze_transcript(transcript, chunk_start, chunk_end):
    prompt = f"""
    Analyze the following transcript content from {chunk_start} to {chunk_end} minutes:

    Transcript: {transcript}

    Please provide a detailed list of observations that captures the essence of the spoken content, including:
    1. Key points and information presented
    2. Notable quotes or statements
    3. Names of speakers or people mentioned (if identifiable)

    Important: Ignore and do not include in your analysis any content related to:
    - Requests for channel subscriptions
    - Promotional content about the channel
    - Discussions about video sponsors or advertisements

    Format the output as a numbered list of observations, maintaining chronological order.
    """

    return generate_content(prompt)


def create_first_draft(video_analysis, transcript_analysis, chunk_start, chunk_end):
    prompt = f"""
    Create a first draft summary based on the following video and transcript analyses for the segment from {chunk_start} to {chunk_end} minutes:

    Video Analysis:
    {video_analysis}

    Transcript Analysis:
    {transcript_analysis}

    Please provide a detailed report that combines and synthesizes the information from both analyses, including:
    1. Key points and information presented
    2. Notable quotes or statements, integrated naturally into the context
    3. Description of visual aids and their relevance to the spoken content
    4. Overall flow and structure of the video segment

    Important: Ensure that no content related to channel subscriptions, channel promotions, or sponsor discussions is included in the summary.

    Format the report in Markdown, using appropriate headings and structure.
    If there are clear examples of presentation materials, include that information within the relevant sections.
    """

    return generate_content(prompt)


def process_video_chunk(video_file, transcript, chunk_start, chunk_end):
    video_analysis = analyze_video_content(video_file, chunk_start, chunk_end)
    transcript_analysis = analyze_transcript(transcript, chunk_start, chunk_end)
    first_draft = create_first_draft(
        video_analysis, transcript_analysis, chunk_start, chunk_end
    )

    return first_draft
