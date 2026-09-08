#!/usr/bin/env python3
"""
A heartwarming little world about a parade, a sailor, and infantry who help each
other through a twist.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    sailor_name: str
    infantry_name: str
    setting: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    sailor: Character
    infantry: Character
    setting: str
    parade_started: bool = False
    twist: str = ""
    resolved: bool = False
    keepsake: str = ""
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = [
    "Mara", "Jonah", "Pia", "Elio", "Nina", "Tomas", "Sana", "Lio", "Mina", "Ren",
]
SETTINGS = [
    "the town square",
    "the harbor road",
    "the school courtyard",
    "the riverside lane",
    "the bright market street",
]
TWISTS = [
    {
        "title": "the missing ribbon",
        "setup": "the parade banner had lost one bright ribbon just before the music began",
        "twist": "the ribbon had tangled on the sailor's knapsack instead of blowing away",
        "problem": "the marchers could not finish the banner the way they had practiced",
        "clue": "a blue thread peeked from under the sailor's pack strap",
        "turn": "the infantry members noticed the thread and followed it with a careful finger",
        "fix": "the sailor knelt, untied the ribbon, and handed it back with an apology and a smile",
        "ending": "the banner rose straight again, with every ribbon fluttering in the same warm wind",
    },
    {
        "title": "the wrong drumbeat",
        "setup": "the parade drums sounded too fast and made everyone hurry their steps",
        "twist": "the sailor had been tapping the tempo on a tin cup, practicing a song for the children",
        "problem": "the infantry thought the parade leader wanted a racing pace",
        "clue": "the sailor's tune matched the lullaby from the lighthouse window",
        "turn": "the infantry listened again and heard the gentler rhythm hidden under the clatter",
        "fix": "they slowed the beat, and the sailor promised to save the cup-song for later",
        "ending": "the parade moved like one calm river, steady and proud",
    },
    {
        "title": "the forgotten coat",
        "setup": "a little coat was left on a bench where the parade would pass",
        "twist": "it belonged to the sailor's younger sister, who had joined the infantry band and grown sleepy",
        "problem": "the child would feel cold when the clouds rolled in",
        "clue": "the infantry noticed the coat label stitched with a tiny anchor",
        "turn": "the sailor recognized the stitch, and the hero carried the coat through the crowd",
        "fix": "the coat was returned before the first rain drop fell, and the child woke smiling",
        "ending": "the parade continued with one more jacket buttoned and one more face glowing",
    },
    {
        "title": "the flower confusion",
        "setup": "petals scattered across the parade route after a basket tipped over",
        "twist": "the petals were for the sailor to give to an honored neighbor, not for decoration on the boots",
        "problem": "everyone thought the petals had been lost",
        "clue": "the infantry saw the basket still tied with a yellow bow near the fountain",
        "turn": "the hero traced the bow to the basket, and the sailor laughed in relief",
        "fix": "together they gathered the petals into a neat handful and shared them at the right stop",
        "ending": "the honored neighbor received the flowers exactly when the parade paused to cheer",
    },
    {
        "title": "the sideways sign",
        "setup": "a sign pointing to the parade route had been turned by the wind",
        "twist": "it had not been broken at all; the sailor had turned it to shade a sleeping kitten",
        "problem": "the infantry nearly marched the wrong way",
        "clue": "a tiny paw print marked the cool patch under the sign",
        "turn": "the infantry saw the kitten and realized the strange angle had a kind reason",
        "fix": "the sailor rotated the sign back after the kitten woke, then carried the kitten to its owner",
        "ending": "the road stayed clear, the kitten purred, and the parade kept to its cheerful path",
    },
    {
        "title": "the extra whistle",
        "setup": "one sharp whistle interrupted the music right before the parade turned the corner",
        "twist": "the sailor had blown it to warn the infantry about a dropped drumstick",
        "problem": "the sudden sound made the crowd think there was trouble",
        "clue": "the whistle pointed to the drumstick rolling near a cobblestone crack",
        "turn": "the hero bent down and caught the stick before it could slip farther",
        "fix": "the sailor thanked the hero, and the infantry marched on with the recovered beat",
        "ending": "the parade corner opened into sunshine, and the music sounded even kinder after the scare",
    },
    {
        "title": "the lantern swap",
        "setup": "two lanterns waited beside the parade float, one small and one tall",
        "twist": "the sailor had borrowed the small lantern to light a map for the infantry",
        "problem": "the float looked unfinished without its matching lantern",
        "clue": "the map's corner glowed with the same orange glass as the missing lantern",
        "turn": "the infantry followed the light and found the sailor near the gatehouse",
        "fix": "the sailor returned the lantern and showed the map, and everyone helped guide the float",
        "ending": "both lanterns shone together, and the parade looked complete again",
    },
    {
        "title": "the parade pausing point",
        "setup": "the parade stopped at a bench where someone had left a lunch basket",
        "twist": "the basket belonged to the infantry captain, who was feeding a stray dog in secret",
        "problem": "the captain feared a stern scolding if the secret was discovered",
        "clue": "a soft wagging tail peeked from under the bench cloth",
        "turn": "the sailor smiled first, making the captain feel safe enough to explain",
        "fix": "the hero helped carry the basket to a quiet corner where the dog could eat safely",
        "ending": "the captain relaxed, the dog wagged happily, and the parade moved on more kindly than before",
    },
    {
        "title": "the coat-pocket note",
        "setup": "a note slipped from the sailor's coat pocket during the parade",
        "twist": "it was a thank-you card from the infantry children, meant to surprise the sailor later",
        "problem": "the note almost got trampled before anyone could read it",
        "clue": "the hero saw the folded paper land beside a boot, still dry and bright",
        "turn": "the infantry recognized their own handwriting and gathered around in a grin",
        "fix": "the sailor read the card aloud, and the children cheered for the happy secret",
        "ending": "the parade ended with the sailor holding the note close and smiling at the whole crowd",
    },
    {
        "title": "the banner shadow",
        "setup": "the parade banner cast a long shadow over the infantry line",
        "twist": "the sailor had held it high so a shy child could walk under the shade",
        "problem": "others thought the banner was being carried too low",
        "clue": "the child under the shadow was carrying a bright, tired smile",
        "turn": "the infantry made room once they understood the reason",
        "fix": "the sailor lifted the banner again only after the child reached the fountain to rest",
        "ending": "the shaded child drank cool water, and the parade looked like it had made a little kindness on purpose",
    },
]

OPENINGS = [
    "On a bright morning in {setting},",
    "When the drums first woke {setting},",
    "As the parade gathered in {setting},",
    "Just before the banners lifted in {setting},",
    "During a busy hour in {setting},",
]

REACTIONS = [
    "\"Oh,\" said {sailor}, soft and careful. \"I meant to help, not hide it.\"",
    "{infantry} blinked, then said, \"That explains the strange part.\"",
    "\"Wait,\" said {hero}, \"the clue is right there.\"",
    "{sailor} took a breath. \"Thank you for looking twice,\" they said.",
    "{infantry} smiled with relief. \"We can fix this together.\"",
]

ENDINGS = [
    "The parade went on with warmer hearts than before.",
    "Everyone kept marching, but now they listened to one another first.",
    "The day felt smaller in the best way: one problem, one clue, one kind fix.",
    "The crowd cheered not for perfection, but for the way they helped each other.",
    "By the final turn, the parade looked brighter because no one had been left alone with the mistake.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming parade/sailor/infantry story world.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--sailor-name", choices=NAMES)
    ap.add_argument("--infantry-name", choices=NAMES)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.name or rng.choice(NAMES)
    sailor = args.sailor_name or rng.choice([n for n in NAMES if n != hero])
    infantry = args.infantry_name or rng.choice([n for n in NAMES if n not in (hero, sailor)])
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(hero_name=hero, sailor_name=sailor, infantry_name=infantry, setting=setting)


def _reasonableness_gate(params: StoryParams) -> None:
    if len({params.hero_name, params.sailor_name, params.infantry_name}) < 3:
        raise StoryError("The hero, sailor, and infantry need different names for the twist to land clearly.")
    if params.setting not in SETTINGS:
        raise StoryError("That setting is not part of this little parade world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    twist = rng.choice(TWISTS)
    opening = rng.choice(OPENINGS).format(setting=params.setting)
    reaction = rng.choice(REACTIONS).format(hero=params.hero_name, sailor=params.sailor_name, infantry=params.infantry_name)
    ending_line = rng.choice(ENDINGS)

    hero = Character(name=params.hero_name, role="hero", meters={"steps": 0.0}, memes={"care": 1.0, "warmth": 1.0})
    sailor = Character(name=params.sailor_name, role="sailor", meters={"rope": 1.0}, memes={"helpful": 1.0, "steady": 1.0})
    infantry = Character(name=params.infantry_name, role="infantry", meters={"march": 1.0}, memes={"alert": 1.0, "kind": 1.0})

    world = World(hero=hero, sailor=sailor, infantry=infantry, setting=params.setting)
    world.parade_started = True
    world.twist = twist["title"]
    world.keepsake = "a small ribbon, note, lantern, coat, or flower depending on the day"

    lines = [
        f"{opening} {params.hero_name} watched the parade line up with {params.sailor_name} and {params.infantry_name}.",
        f"The day seemed simple at first: {twist['setup']}.",
        f"Then came the twist: {twist['twist']}.",
        f"At first, that looked like a problem because {twist['problem']}.",
        reaction,
        f"{params.hero_name} noticed a clue: {twist['clue']}.",
        f"That clue helped everyone see the truth. The infantry {twist['turn']}.",
        f"{params.sailor_name} did the kind repair: {twist['fix']}.",
        f"In the end, {twist['ending']}.",
        ending_line,
    ]
    world.resolved = True
    world.facts["twist_detail"] = twist["twist"]
    world.facts["clue"] = twist["clue"]
    world.facts["repair"] = twist["fix"]
    world.facts["ending_image"] = twist["ending"]
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a heartwarming parade story with {params.hero_name}, {params.sailor_name}, and {params.infantry_name}.",
        f"Include a gentle twist at {params.setting} and end with a kind repair.",
        "Make the characters speak to each other, notice a clue, and finish the parade happily.",
    ]

    story_qa = [
        QAItem(
            question=f"What was the twist in the parade story?",
            answer=f"The twist was that {twist['twist']}.",
        ),
        QAItem(
            question=f"What clue helped {params.hero_name} understand what was really happening?",
            answer=f"The clue was that {twist['clue']}.",
        ),
        QAItem(
            question=f"How did {params.sailor_name} help fix the problem?",
            answer=f"{params.sailor_name} helped by {twist['fix']}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the parade was back on track and everyone felt kinder and calmer.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is a cheerful public walk or march, often with music, banners, and people moving together.",
        ),
        QAItem(
            question="What is a sailor?",
            answer="A sailor is a person who works on or around boats and knows about water, ropes, and the sea.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers or marchers who move on foot.",
        ),
        QAItem(
            question="What does a heartwarming story feel like?",
            answer="A heartwarming story feels caring, gentle, and hopeful, especially when people help each other.",
        ),
        QAItem(
            question="What does a twist do in a story?",
            answer="A twist adds a surprising change that makes characters notice the situation in a new way.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        w = sample.world
        print(f"setting={w.setting}, parade_started={w.parade_started}, twist={w.twist}, resolved={w.resolved}")
        print(f"hero={w.hero.name}, role={w.hero.role}, meters={w.hero.meters}, memes={w.hero.memes}")
        print(f"sailor={w.sailor.name}, role={w.sailor.role}, meters={w.sailor.meters}, memes={w.sailor.memes}")
        print(f"infantry={w.infantry.name}, role={w.infantry.role}, meters={w.infantry.meters}, memes={w.infantry.memes}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
valid_setting(S) :- setting(S).
distinct_roles(hero,sailor,infantry).
twist_ok(T) :- twist(T).

#show valid_setting/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("setting", setting) for setting in SETTINGS)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_settings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_setting/1."))
    return sorted(set(asp.atoms(model, "valid_setting")))


def asp_verify() -> int:
    py = set((s,) for s in SETTINGS)
    cl = set(asp_valid_settings())
    if py == cl:
        print(f"OK: clingo gate matches SETTINGS ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_samples(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        out: list[StoryParams] = []
        for i, setting in enumerate(SETTINGS):
            hero = NAMES[i % len(NAMES)]
            sailor = NAMES[(i + 1) % len(NAMES)]
            infantry = NAMES[(i + 2) % len(NAMES)]
            if len({hero, sailor, infantry}) < 3:
                infantry = NAMES[(i + 3) % len(NAMES)]
            out.append(StoryParams(hero_name=hero, sailor_name=sailor, infantry_name=infantry, setting=setting))
        return out
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p[0]}" for p in asp_valid_settings()))
        return

    samples: list[StorySample] = []
    for i, params in enumerate(generation_samples(args)):
        params.seed = (args.seed if args.seed is not None else 0) + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
