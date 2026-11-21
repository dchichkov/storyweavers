"""Exact baseline extracted from storyworlds/openai_story_quality.py."""
from datetime import datetime, timezone

BASELINE_STORY = (
    "Once upon a time, in a peaceful town, there lived a little boy named Tim. "
    "Tim loved to run and play outside. One day, Tim saw a race in the park. "
    "He was excited and wanted to join the race.  Tim went to his friend, "
    "Sarah, and said, \"Let's start the race!\" Sarah smiled and said, "
    "\"Yes, let's go!\" They lined up with the other kids and waited for the "
    "race to begin. When they heard the word \"Go!\", they started running as "
    "fast as they could.  Tim and Sarah ran with all their speed, laughing and "
    "having fun. They could feel the wind in their hair as they raced to the "
    "finish line. In the end, Tim won the race and Sarah came in second. They "
    "were both so happy and proud of themselves. They celebrated with their "
    "friends and had a great day at the park."
)
BASELINE_RATING = {
    "coherence": 7,
    "style": 6,
    "grammar": 7,
    "storytelling": 7,
    "overall": 7,
}
RATING_KEYS = ("coherence", "style", "grammar", "storytelling", "overall")

def now_stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
