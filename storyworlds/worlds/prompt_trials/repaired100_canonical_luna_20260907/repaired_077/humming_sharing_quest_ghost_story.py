#!/usr/bin/env python3
"""
A gentle ghost story about humming, sharing, and a small quest.
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


NAMES = ["Luna", "Mira", "Pip", "Tavi", "Nori", "Sami", "Iris", "Theo"]
PLACES = ["the old moonlit house", "the quiet hill cottage", "the village lantern room", "the misty garden", "the sleepy seaside inn"]

QUESTS = [
    {
        "title": "the humming window",
        "setup": "a soft humming floated from a locked upstairs window",
        "clue": "the tune rose whenever the moon shone on the dusty glass",
        "ghost": "a pale little ghost named Wisp",
        "need": "Wisp had forgotten the way to the room where her silver music box rested",
        "share": "Luna shared her warm lantern light and the last honey biscuit",
        "task": "followed the humming through the hall and carried the lantern up the narrow stairs",
        "ending": "the music box chimed once, and Wisp's glow became warm instead of blue",
    },
    {
        "title": "the ghostly garden path",
        "setup": "a humming sound drifted between the sleeping flowers",
        "clue": "the humming stopped beside each flower that had lost its moon-colored ribbon",
        "ghost": "a shy garden ghost named Bell",
        "need": "Bell could not find the ribbons needed to mark a safe path home",
        "share": "Luna shared her spool of red thread and the little scissors in her pocket",
        "task": "followed the humming from stone to stone and tied a bright marker wherever the path bent",
        "ending": "Bell followed the red trail home, humming a cheerful tune beneath the roses",
    },
    {
        "title": "the lantern-room quest",
        "setup": "a lonely humming came from the room where the village lanterns were kept",
        "clue": "one lantern flickered in time with the three notes of the tune",
        "ghost": "a small ghost named Ash",
        "need": "Ash wanted to guide a lost moth-spirit back to the garden",
        "share": "Luna shared her candle flame and held the lantern steady",
        "task": "crossed the cold room, lit the dark lantern, and carried it toward the garden door",
        "ending": "the moth-spirit followed the golden light while Ash hummed with relief",
    },
    {
        "title": "the blanket by the stairs",
        "setup": "humming echoed under the stairs after midnight",
        "clue": "a tiny cold handprint appeared beside the folded blankets",
        "ghost": "a young ghost named June",
        "need": "June was cold and too frightened to ask anyone for help",
        "share": "Luna shared her soft blanket and made room beside the cheerful stove",
        "task": "knelt beneath the stairs, spoke gently, and carried the blanket to the warm room",
        "ending": "June's humming softened as the blanket wrapped her in a little circle of warmth",
    },
]

OPENINGS = [
    "The house was quiet when",
    "Just as the moon climbed over the roof,",
    "On an evening when every candle had been trimmed,",
    "While the village slept behind its shutters,",
    "Near the end of a rainy night,",
]

LESSONS = [
    "Luna learned that sharing could make a frightening mystery feel small enough to solve.",
    "The quest showed Luna that a ghost might need kindness more than screaming.",
    "A shared light did not grow dim; it made the whole path easier to see.",
    "Luna discovered that listening carefully was the first brave step of a quest.",
    "The night became gentler when nobody had to face it alone.",
]


@dataclass
class Being:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    place: str
    quest: str
    seed: Optional[int] = None


@dataclass
class World:
    child: Being
    ghost: Being
    place: str
    quest: str
    humming: bool = False
    shared: bool = False
    resolved: bool = False
    facts: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Humming sharing quest ghost story world.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--quest", choices=[q["title"] for q in QUESTS])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        place=args.place or rng.choice(PLACES),
        quest=args.quest or rng.choice([q["title"] for q in QUESTS]),
    )


def _reasonableness_gate(params: StoryParams) -> None:
    if params.name not in NAMES:
        raise StoryError("The child needs a name from this little world.")
    if params.place not in PLACES:
        raise StoryError("That setting is not part of the ghostly world.")
    if params.quest not in [q["title"] for q in QUESTS]:
        raise StoryError("That quest is not available tonight.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    quest = next(q for q in QUESTS if q["title"] == params.quest)
    opening = rng.choice(OPENINGS)
    lesson = rng.choice(LESSONS)
    child = Being(
        name=params.name,
        kind="child",
        meters={"warmth": 0.7, "courage": 0.6, "distance_to_ghost": 8.0},
        memes={"curiosity": 1.0, "kindness": 1.0},
    )
    ghost = Being(
        name=quest["ghost"].split()[-1],
        kind="ghost",
        meters={"warmth": 0.2, "courage": 0.3, "distance_to_home": 10.0},
        memes={"lonely": 1.0, "hopeful": 0.5},
    )
    world = World(child=child, ghost=ghost, place=params.place, quest=params.quest)
    world.humming = True
    world.facts["need"] = quest["need"]
    world.facts["clue"] = quest["clue"]

    lines = [
        f"{opening} {quest['setup']} in {params.place}.",
        f"{params.name} listened instead of hiding. The humming was gentle, but it carried a lonely little shake.",
        f"Then {quest['ghost']} appeared beside the wall. \"Please do not run,\" whispered the ghost. \"{quest['need'].capitalize()}.\"",
        f"{params.name} held the lantern close. \"I will not run,\" said {params.name}. \"Can you show me what the humming means?\"",
        f"The ghost nodded, and the sound became clearer. {quest['clue'].capitalize()}.",
        f"\"We can look together,\" said {params.name}. \"I have something we can share.\"",
        f"{params.name} {quest['share']}.",
        f"The sharing made the ghost's small shoulders loosen. Together they {quest['task']}.",
        f"At the hardest turn, the hallway groaned. {params.name} squeezed the lantern handle, and the ghost said, \"Keep humming with me.\"",
        f"\"One, two, three,\" hummed {params.name}. The ghost hummed back, and their two tunes made one brave sound.",
        f"The quest reached its end: {quest['ending']}.",
        lesson,
        f"Before dawn, {params.name} and the ghost shared the last quiet moment beside the light.",
    ]

    world.shared = True
    world.resolved = True
    world.facts["repair"] = quest["task"]
    world.facts["ending"] = quest["ending"]
    world.facts["lesson"] = lesson
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a gentle ghost story called {quest['title']} about humming and sharing.",
        f"Tell a child-friendly quest in {params.place} where {params.name} helps a lonely ghost.",
        f"Write a spooky-but-safe story in which a shared light and a shared song solve a mystery.",
    ]

    story_qa = [
        QAItem(
            question=f"Who was humming in {params.place}?",
            answer=f"The ghost named {ghost.name} was humming in {params.place}.",
        ),
        QAItem(
            question=f"Why did {ghost.name} need help?",
            answer=f"{ghost.name} needed help because {quest['need']}.",
        ),
        QAItem(
            question="What clue helped with the quest?",
            answer=f"The clue was that {quest['clue']}.",
        ),
        QAItem(
            question=f"What did {params.name} share?",
            answer=f"{params.name} shared {quest['share'].split('shared ', 1)[-1]}.",
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"The quest ended when {quest['ending']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a ghost in this story world?",
            answer="A ghost is a pale, mysterious being that can need comfort, directions, or company.",
        ),
        QAItem(
            question="Why can humming be useful during a quest?",
            answer="Humming can help friends stay together, follow a sound, and feel brave in a dark place.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means offering part of what you have so another person or being is not alone or without help.",
        ),
        QAItem(
            question="What makes a quest?",
            answer="A quest is a purposeful journey in which someone follows clues and works toward an important goal.",
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
        world = sample.world
        print("\n--- trace ---")
        print(f"child={world.child.name}, kind={world.child.kind}, meters={world.child.meters}, memes={world.child.memes}")
        print(f"ghost={world.ghost.name}, kind={world.ghost.kind}, meters={world.ghost.meters}, memes={world.ghost.memes}")
        print(f"place={world.place}, quest={world.quest}, humming={world.humming}, shared={world.shared}, resolved={world.resolved}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


ASP_RULES = r"""
valid_place(P) :- place(P).
valid_quest(Q) :- quest(Q).
humming_required(Q) :- quest(Q).
sharing_required(Q) :- quest(Q).
resolvable(Q) :- quest(Q), humming_required(Q), sharing_required(Q).

#show valid_place/1.
#show valid_quest/1.
#show resolvable/1.
"""


def asp_facts() -> str:
    import asp
    facts = [asp.fact("place", place) for place in PLACES]
    facts.extend(asp.fact("quest", quest["title"]) for quest in QUESTS)
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    places = set(asp.atoms(asp.one_model(asp_program("#show valid_place/1.")), "valid_place"))
    quests = set(asp.atoms(asp.one_model(asp_program("#show valid_quest/1.")), "valid_quest"))
    py_places = {(p,) for p in PLACES}
    py_quests = {(q["title"],) for q in QUESTS}
    if places != py_places or quests != py_quests:
        print("MISMATCH between Python registries and ASP registries.")
        return 1
    for index, quest in enumerate(QUESTS):
        sample = generate(StoryParams(name=NAMES[index % len(NAMES)], place=PLACES[index % len(PLACES)], quest=quest["title"], seed=index))
        if not sample.story or "humming" not in sample.story.lower() or "share" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP matches {len(PLACES)} places and {len(QUESTS)} quests; generated stories pass.")
    return 0


def generation_params(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(name=NAMES[i % len(NAMES)], place=PLACES[i % len(PLACES)], quest=QUESTS[i % len(QUESTS)]["title"])
            for i in range(len(PLACES) * len(QUESTS))
        ]
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_place/1.\n#show valid_quest/1.\n#show resolvable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_place/1.\n#show valid_quest/1.\n#show resolvable/1."))
        for predicate in ("valid_place", "valid_quest", "resolvable"):
            for atom in sorted(asp.atoms(model, predicate)):
                print(f"{predicate}{atom}")
        return

    samples = []
    for index, params in enumerate(generation_params(args)):
        params.seed = (args.seed if args.seed is not None else 0) + index
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
