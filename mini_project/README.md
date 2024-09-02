# YouTube Video Structured Element Analyzer

This mini project analyzes YouTube videos to identify and describe structured elements such as slides, graphs, and charts.

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your environment variables:
   - Create a `.env` file in the project root
   - Add your Google API key: `GOOGLE_API_KEY=your_api_key_here`

## Usage

Run the main script:

```
python mini_main.py
```

Follow the prompts to enter a YouTube video ID.

## Output

The script will generate:
- Captured images of structured elements in `m_output/`
- A markdown report `structured_elements_report.md` in `m_output/`
- An API statistics report in `m_output/`

## Note

This is a mini project and part of a larger video analysis system. It's designed to be modular for potential future integration.