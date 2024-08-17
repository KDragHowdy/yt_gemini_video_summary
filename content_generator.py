import google.generativeai as genai

model = genai.GenerativeModel("gemini-1.5-flash")


def generate_content(video_file, prompt):
    try:
        response = model.generate_content(
            [video_file, prompt], request_options={"timeout": 600}
        )

        if response.prompt_feedback:
            print(f"Prompt feedback: {response.prompt_feedback}")

        return response.text

    except Exception as e:
        print(f"Error generating content: {str(e)}")
        return f"Error in analysis: {str(e)}"


def process_video_chunk(video_file, transcript, chunk_start, chunk_end):
    prompt = f"""
    Analyze the following video content from {chunk_start} to {chunk_end} minutes:

    Transcript: {transcript}

    Please provide a detailed report that captures the essence of the video, including:
    1. Key points and information presented
    2. Notable quotes or statements
    3. Description of any visual aids (slides, charts, graphs) and their content
    4. The overall tone and style of presentation

    Format the report in Markdown, using appropriate headings and structure.
    If there are clear examples of presentation materials, recreate that information in a separate appendix section.
    """

    return generate_content(video_file, prompt)


def process_video_chunk_second_draft(first_draft):
    prompt = f"""
    Rewrite the following first draft of a video analysis report:

    {first_draft}

    In this second draft:
    1. Incorporate the quotes from the "Notable Quotes or Statements" section naturally into the "Key Points and Information" section.
    2. Expand on relevant parts of the "Key Points and Information" to provide context for the quotes.
    3. Maintain the individual key points, but present them in a more holistic manner.
    4. Remove the "Notable Quotes or Statements" section entirely.
    5. Try to identify the speaker by name and refer to them by their first name throughout the report, not as "the speaker".
    6. Ensure that any visual information from the "Description of Visual Aids" section is incorporated into the main content where relevant.
    7. Format the output in Markdown.
    8. Do not include any statements about the absence of visual information or inability to process visual content.
    """

    return generate_content(None, prompt)  # No video file needed for second draft
