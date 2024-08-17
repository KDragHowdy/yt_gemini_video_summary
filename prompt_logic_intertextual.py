import os
import json
from datetime import datetime
from content_generator import generate_content


def analyze_intertextual_references(video_analysis, transcript_analysis, video_title):
    prompt = f"""
    Analyze the following video content and transcript for intertextual references:

    Video Analysis:
    {video_analysis}

    Transcript Analysis:
    {transcript_analysis}

    Please identify and explain any references to:
    1. Literary works
    2. Philosophical concepts
    3. Historical events
    4. Scientific theories
    5. Pop culture
    6. AI technology and concepts
    7. Research papers or academic works
    8. Internet culture and memes
    9. Other notable works or ideas

    For each reference, provide:
    - The context in which it was mentioned
    - A brief explanation of the reference
    - Its significance or relevance to the speaker's point

    Format the output as a JSON object with the following structure:
    {{
        "references": [
            {{
                "type": "literary/philosophical/historical/scientific/pop_culture/ai_tech/research/internet_culture/other",
                "reference": "The actual reference",
                "context": "How it was used in the video",
                "explanation": "Brief explanation of the reference",
                "significance": "Why it's important in this context"
            }}
        ]
    }}
    """

    intertextual_analysis = generate_content(prompt)

    # Save the interim work product
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    condensed_title = "".join(e for e in video_title if e.isalnum())[:30]
    filename = f"interim wp - {condensed_title} - intertextual - {timestamp}.txt"

    interim_dir = "./interim"
    os.makedirs(interim_dir, exist_ok=True)

    with open(os.path.join(interim_dir, filename), "w") as f:
        f.write(intertextual_analysis)

    return json.loads(intertextual_analysis)


# Example usage
if __name__ == "__main__":
    # These would typically come from your main processing pipeline
    sample_video_analysis = """
    The video features a speaker discussing the implications of large language models.
    They mention GPT-3 and show a slide comparing it to BERT.
    The speaker makes a reference to the "Chinese Room" thought experiment.
    There's a meme image of a cat saying "I can haz AI" displayed at one point.
    """
    sample_transcript_analysis = """
    The speaker says: "Just as Turing's imitation game challenged our notions of intelligence, GPT-3 is forcing us to reconsider what it means for a machine to understand language."
    They later mention: "This reminds me of Hofstadter's concept of strange loops, which we see echoed in the recursive nature of these models."
    The talk concludes with: "As the AI winter thawed, we've entered what some call the 'eternal September' of AI development."
    """
    sample_video_title = "The Philosophy of Large Language Models"

    result = analyze_intertextual_references(
        sample_video_analysis, sample_transcript_analysis, sample_video_title
    )
    print(json.dumps(result, indent=2))
