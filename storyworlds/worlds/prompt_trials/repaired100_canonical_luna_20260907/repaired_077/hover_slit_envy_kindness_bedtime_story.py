#!/usr/bin/env python3
"""
A gentle bedtime story world about a hovering moth, a narrow moonlit slit,
envy, and the kindness that turns comparison into companionship.
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

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    friend_name: str
    place: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    friend: Character
    place: str
    lantern_light: str = "steady"
    envy: bool = False
    kindness: bool = False
    safe: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Luna", "Mira", "Pip", "Nell", "Tavi", "Sora", "Milo", "Ivy"]
PLACES = [
    "the quiet attic",
    "the moonlit bedroom",
    "the little tower room",
    "the garden shed",
    "the window seat",
]

SCENES = [
    {
        "title": "the narrow moon slit",
        "setup": "a bright moth hovered beside a narrow slit in the curtain",
        "envy": "the moth's silver wings seemed more beautiful than Luna's small brown wings",
        "risk": "the slit led toward a high window that had not been checked for drafts",
        "clue": "the moonbeam showed that the safe lamp was shining below the window",
        "action": "moved the lamp closer and guided the moth away from the unlatched window",
        "ending": "both wings rested in the warm moonbeam while the curtain lay safely still",
    },
    {
        "title": "the star-shaped shadow",
        "setup": "a tiny moth hovered inside a star-shaped patch of light",
        "envy": "Luna wished she could glow as brightly as the moth",
        "risk": "she nearly climbed through a slit between two stacked boxes to reach the light",
        "clue": "the shadow of a paper star made the glow, not the moth itself",
        "action": "asked her friend to move the boxes and placed the paper star beside the bed",
        "ending": "the paper star shone on the wall while the moth slept in a safe corner",
    },
    {
        "title": "the quiet lantern",
        "setup": "a little moth hovered over a covered lantern near bedtime",
        "envy": "Luna felt jealous of its brave, fluttering dance",
        "risk": "she reached toward a slit in the lantern cover before anyone knew it was warm",
        "clue": "the cover felt hot, while the open shelf beside it was cool",
        "action": "closed the lantern safely and made a soft paper moon for the moth to circle",
        "ending": "the paper moon turned slowly as the real lantern cooled behind its cover",
    },
    {
        "title": "the window-seat wish",
        "setup": "a moth hovered above the window seat where moonlight made every dust mote sparkle",
        "envy": "Luna wished her own wings could make such a lovely dance",
        "risk": "she followed the moth toward a slit behind the curtain and almost lost sight of the room",
        "clue": "the moth always returned to the same safe patch of light",
        "action": "placed a pale ribbon near the bed and invited the moth to follow its gentle shadow",
        "ending": "the ribbon swayed softly while the moth and Luna shared the same patch of light",
    },
    {
        "title": "the bedtime button",
        "setup": "a moth hovered near a glowing button on the bedside clock",
        "envy": "Luna thought the moth had a brighter little star than she did",
        "risk": "she tried to squeeze through a slit behind the clock to touch it",
        "clue": "the glow came from the clock's button, not from the moth",
        "action": "moved the clock away from the wall and let the moth settle on a folded blanket",
        "ending": "the clock glowed gently while two sleepy shapes rested far from its narrow gap",
    },
    {
        "title": "the borrowed sparkle",
        "setup": "a moth hovered over a silver thread beside the bedtime basket",
        "envy": "Luna wished she owned a sparkle that followed her everywhere",
        "risk": "the thread had slipped through a narrow slit in the basket and could tangle a wing",
        "clue": "the sparkle belonged to a ribbon, and its loose end was caught under the basket",
        "action": "freed the ribbon with help and tied it in a loose bow on the bedpost",
        "ending": "the ribbon gleamed on the bedpost while the moth rested with its wings untangled",
    },
]

OPENINGS = [
    "When the house grew quiet,",
    "Just before the bedtime story ended,",
    "Under a round and patient moon,",
    "As the last lamp began to soften,",
    "When sleepy shadows stretched across the floor,",
]

REACTIONS = [
    '"I wanted what it had," Luna whispered. "But I do not want it to be unsafe."',
    '"I felt envy," Luna admitted. "Can kindness help me look again?"',
    '"Its light is lovely," Luna said, "and my wings can still be gentle."',
    'Luna took a slow breath. "I can admire my friend without chasing the danger."',
    '"Please show me the safe way," Luna asked. "I want both of us to rest well."',
]

LESSONS = [
    "Kindness did not make the envy disappear at once; it gave the feeling a softer place to land.",
    "Luna learned that another creature's sparkle did not make her own wings less special.",
    "When envy whispered, kindness answered by noticing what a friend needed.",
    "The room felt larger when Luna stopped comparing and began helping.",
    "A gentle heart can admire a bright friend and still choose a safe path.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a hovering moth and kindness.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--place", choices=PLACES)
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
    name = args.name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([n for n in NAMES if n != name])
    place = args.place or rng.choice(PLACES)
    return StoryParams(name=name, friend_name=friend, place=place)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.name == params.friend_name:
        raise StoryError("The two bedtime friends need different names.")
    if params.place not in PLACES:
        raise StoryError("That place is not part of this quiet bedtime world.")
    if not params.name or not params.friend_name:
        raise StoryError("Both sleepy friends need names.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    scene = rng.choice(SCENES)
    opening = rng.choice(OPENINGS)
    reaction = rng.choice(REACTIONS)
    lesson = rng.choice(LESSONS)
    hero = Character(
        name=params.name,
        kind="young moth",
        meters={"distance_to_window": 1.0, "distance_to_friend": 0.8},
        memes={"curiosity": 0.8, "envy": 0.0, "kindness": 0.4},
    )
    friend = Character(
        name=params.friend_name,
        kind="silver moth",
        meters={"distance_to_window": 1.2, "distance_to_friend": 0.9},
        memes={"brightness": 0.9, "calm": 0.8},
    )
    world = World(hero=hero, friend=friend, place=params.place)
    world.envy = True
    world.facts.update(
        title=scene["title"],
        risk=scene["risk"],
        clue=scene["clue"],
    )

    lines = [
        f"{opening} {params.name} rested near {params.place}, listening to the house breathe.",
        f"Then {scene['setup']}.",
        f"{params.name} watched and felt envy: {scene['envy']}.",
        f"The feeling tugged {params.name} toward trouble because {scene['risk']}.",
        f"{params.friend_name} fluttered lower. \"Are you all right?\" they asked.",
        f"{reaction}",
        f"Together they paused and looked closely. {scene['clue'].capitalize()}.",
        f"{params.friend_name} said, \"Your wings do not have to copy mine. Let us make this safe for both of us.\"",
        f"With kindness, {params.name} {scene['action']}.",
        lesson,
        f"At last, {scene['ending']}.",
        f"{params.friend_name} yawned. \"Good night, {params.name}.\"",
        f"\"Good night,\" said {params.name}, no longer wishing to be someone else.",
    ]
    world.kindness = True
    world.safe = True
    world.lantern_light = "soft and safe"
    world.hero.memes["envy"] = 0.2
    world.hero.memes["kindness"] = 1.0
    world.hero.meters["distance_to_window"] = 1.4
    world.facts["repair"] = scene["action"]
    world.facts["ending"] = scene["ending"]
    world.facts["lesson"] = lesson
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a gentle bedtime story called {scene['title']} about {params.name} and {params.friend_name}.",
        f"Tell a child-friendly story in {params.place} that includes a hovering moth, a narrow slit, envy, and kindness.",
        "Show how a kind conversation changes a worried choice and ends with a peaceful image.",
    ]

    story_qa = [
        QAItem(
            question=f"What made {params.name} feel envy?",
            answer=f"{params.name} felt envy because {scene['envy']}.",
        ),
        QAItem(
            question=f"What danger did {params.name} notice?",
            answer=f"The danger was that {scene['risk']}.",
        ),
        QAItem(
            question=f"What clue helped the friends understand the scene?",
            answer=f"They noticed that {scene['clue']}.",
        ),
        QAItem(
            question=f"How did {params.friend_name} show kindness?",
            answer=f"{params.friend_name} spoke gently, listened to {params.name}, and helped {params.name} choose a safe solution.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended when {scene['ending']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does hover mean?",
            answer="To hover means to stay in one place in the air while moving gently enough not to land.",
        ),
        QAItem(
            question="What is a slit?",
            answer="A slit is a narrow opening or cut between two surfaces.",
        ),
        QAItem(
            question="What is envy?",
            answer="Envy is the uncomfortable wish to have something another person or creature seems to have.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means noticing another being's needs and choosing words or actions that help rather than hurt.",
        ),
        QAItem(
            question="Why should someone check a narrow opening before reaching through it?",
            answer="A narrow opening may hide heat, sharp edges, tangles, or a drop, so checking first helps keep everyone safe.",
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
        w = sample.world
        print("\n--- trace ---")
        print(f"hero={w.hero.name}, kind={w.hero.kind}, meters={w.hero.meters}, memes={w.hero.memes}")
        print(f"friend={w.friend.name}, kind={w.friend.kind}, meters={w.friend.meters}, memes={w.friend.memes}")
        print(f"place={w.place}, lantern_light={w.lantern_light}, envy={w.envy}, kindness={w.kindness}, safe={w.safe}")
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
valid_place(P) :- place(P).
safe_choice :- has_slit, has_hover, has_envy, has_kindness.
#show valid_place/1.
#show safe_choice/0.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("place", place) for place in PLACES]
    facts.extend(
        [
            asp.fact("has_hover"),
            asp.fact("has_slit"),
            asp.fact("has_envy"),
            asp.fact("has_kindness"),
        ]
    )
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    try:
        py = set((place,) for place in PLACES)
        cl = set(asp_valid_places())
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 0
    if py != cl:
        print("MISMATCH between Python and ASP places.")
        return 1
    for seed in range(5):
        params = StoryParams(
            name=NAMES[seed],
            friend_name=NAMES[(seed + 1) % len(NAMES)],
            place=PLACES[seed % len(PLACES)],
            seed=seed,
        )
        sample = generate(params)
        if not sample.story or "kindness" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity and generated stories verified ({len(py)} places).")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(
                name=NAMES[i % len(NAMES)],
                friend_name=NAMES[(i + 1) % len(NAMES)],
                place=place,
                seed=i,
            )
            for i, place in enumerate(PLACES)
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_place/1.\n#show safe_choice/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            print("\n".join(place[0] for place in asp_valid_places()))
        except ImportError as exc:
            raise SystemExit(f"ASP mode requires clingo: {exc}")
        return

    samples = []
    for i, params in enumerate(generation_params(args)):
        if params.seed is None:
            params.seed = (args.seed if args.seed is not None else 0) + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
