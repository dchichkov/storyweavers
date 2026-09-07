"""Named reference sources for matched StoryWorld prompt trials."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORLDS = ROOT / "storyworlds/worlds"
CANONICAL_EXAMPLES = {
    "puddles": WORLDS / "puddles.py",
    "pirates": WORLDS / "pirates.py",
    "quesadilla": WORLDS / "gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/quesadilla_mystery_to_solve_bedtime_story.py",
    "thud": WORLDS / "gpt-5.4-mini_batch_6a3744730bd48190b368f32c2819a0ed_seed953274611_n1000_repaired/thud_teamwork_rhyming_story.py",
    "dining": WORLDS / "gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/alliance_shrivel_fifty_dining_room_surprise_detective.py",
    "garnet": WORLDS / "gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/garnet_humor_curiosity_repetition_tall_tale.py",
    "grocery": WORLDS / "gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/huge_movement_silo_grocery_store_moral_value.py",
}
