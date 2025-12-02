import os
import yaml
from dotenv import load_dotenv
from gemini_analyzer import GeminiAnalyzer


def main():
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print('Missing GEMINI_API_KEY in .env')
        return

    model = 'models/gemini-2.5-pro'
    if os.path.exists('config.yaml'):
        try:
            with open('config.yaml', 'r') as f:
                cfg = yaml.safe_load(f)
                model = cfg.get('gemini', {}).get('model', model)
        except Exception:
            pass

    analyzer = GeminiAnalyzer(api_key=api_key, model=model)

    test_text = (
        "Title: What do you automate with Python?\n\n"
        "I'm curious what daily tasks everyone automates with Python.\n"
        "I currently use it for:\n- Web scraping\n- File organization\n- Report generation\n\n"
        "What about you?"
    )

    result = analyzer.analyze_post(
        post_text=test_text,
        subreddit="Python",
        title="What do you automate with Python?",
        metadata={"score": 100, "comment_count": 50}
    )

    print("Gemini analysis result:")
    print(result)

    if "automate" in (result.get('core_issue', '') or '').lower():
        print("\n✅ GEMINI ANALYSIS WORKING")
    else:
        print("\n❌ GEMINI ANALYSIS BROKEN")


if __name__ == "__main__":
    main()
