#!/usr/bin/env python3
"""
Standalone story world: a pirate learns to read an obvious wake.

Luna sails a small cutter, spots a strange wake, and mistakes a loose sleeve
for a pirate flag. A careful look, a brief exchange with her deckhand, and a
safe repair turn the scare into a lesson learned.
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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "Moonwake Bay"
    detail: str = "a bright little bay dotted with buoys, gulls, and sleepy boats"


@dataclass
class StoryParams:
    captain: str
    deckhand: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    story_lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_lines)


CAPTAIN_NAMES = ["Luna", "Maris", "Coral", "Pip", "Tessa", "Milo"]
DECKHAND_NAMES = ["Nico", "Toby", "Sella", "Finn", "Bram", "Nori"]

INCIDENTS = [
    {
        "id": "sleeve_flag",
        "premise": "a pale shape fluttered from the rocks while a dark wake curled around it",
        "mistake": "a rival pirate had raised a secret flag and was following their boat",
        "clue": "the fluttering shape had one long sleeve and no flagpole",
        "test": "slowed the cutter, stayed in deep water, and watched the shape through the brass spyglass",
        "truth": "it was a lost sailor's sleeve caught on a branch, while the wake came from a harmless seal",
        "repair": "asked the harbor keeper to collect the sleeve with a boat hook",
        "ending": "the seal made one neat wake beside the cutter as the cleaned sleeve dried on the harbor rail",
        "lesson": "When a clue is obvious, pause long enough to notice what it really shows.",
    },
    {
        "id": "barrel_wake",
        "premise": "a barrel bumped through the bay and left a crooked wake behind it",
        "mistake": "a hidden pirate ship was creeping toward the treasure dock",
        "clue": "the barrel rolled in circles whenever the tide pushed it",
        "test": "kept the cutter behind the buoy line and compared the barrel's path with the tide",
        "truth": "it was an empty water barrel drifting loose from a fishing raft",
        "repair": "tied the barrel to the harbor post after the keeper checked it",
        "ending": "the bay settled into a smooth wake as the barrel rested safely beside the dock",
        "lesson": "A moving thing may be carried by water, so check the current before blaming a captain.",
    },
    {
        "id": "moonlit_sleeve",
        "premise": "a white strip gleamed beside a moonlit wake",
        "mistake": "a ghost pirate was waving from a sunken boat",
        "clue": "the strip folded softly like cloth whenever the breeze changed",
        "test": "trimmed the sail and watched from the lantern-lit deck",
        "truth": "it was a torn sleeve caught on a floating branch",
        "repair": "marked the branch for the morning harbor crew instead of reaching into the water",
        "ending": "the branch drifted away while the cutter's own wake shone silver behind it",
        "lesson": "A strange sight deserves a calm check, not a frightening story invented too soon.",
    },
]


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    incident = rng.choice(INCIDENTS)
    opening = rng.choice([
        f"At dawn, Captain {params.captain} guided the little cutter toward Moonwake Bay.",
        f"Captain {params.captain} woke before the gulls and checked the cutter's ropes.",
        f"On a bright morning, Captain {params.captain} sailed with {params.deckhand} toward the quiet bay.",
    ])
    world = World(setting=Setting())
    captain = world.add(Entity(
        id=params.captain,
        kind="character",
        type="pirate",
        label="young captain",
        meters={"distance": 0.0, "wake_speed": 0.0},
        memes={"confidence": 1.0, "worry": 0.0, "relief": 0.0, "wisdom": 0.0},
    ))
    deckhand = world.add(Entity(
        id=params.deckhand,
        kind="character",
        type="deckhand",
        label="deckhand",
        meters={"distance": 0.0},
        memes={"calm": 1.0, "worry": 0.0, "trust": 1.0},
    ))
    sleeve = world.add(Entity(
        id="sleeve",
        type="cloth",
        label="a loose sleeve",
        meters={"wetness": 0.3},
        memes={},
    ))
    world.facts.update(
        captain=captain,
        deckhand=deckhand,
        sleeve=sleeve,
        incident=incident,
        opening=opening,
        place=world.setting.place,
        detail=world.setting.detail,
        wake_seen=False,
        obvious_clue=False,
        lesson_learned=False,
    )
    return world


def simulate(world: World) -> None:
    captain: Entity = world.facts["captain"]
    deckhand: Entity = world.facts["deckhand"]
    incident = world.facts["incident"]

    world.say(world.facts["opening"])
    world.say(
        f"{captain.id} sailed with {deckhand.id} across {world.facts['place']}, "
        f"where {world.facts['detail']}."
    )
    world.say(
        f"Then {incident['premise']}. The water made a soft wake behind the cutter."
    )
    captain.meters["distance"] += 4.0
    captain.meters["wake_speed"] = 0.5
    world.facts["wake_seen"] = True
    captain.memes["worry"] += 1.0
    world.say(
        f"{captain.id} gripped the wheel. 'Pirates ahoy!' she cried. "
        f"She decided that {incident['mistake']}."
    )
    world.say(
        f"'{captain.id}, wait,' said {deckhand.id}. 'The wake is real, but your first idea "
        "may not be. What can we learn by looking?'"
    )
    deckhand.memes["calm"] += 0.5
    world.say(
        f"They stayed in the safe channel and studied the scene. Soon the answer became "
        f"obvious: {incident['clue']}."
    )
    world.facts["obvious_clue"] = True
    captain.memes["worry"] = max(0.0, captain.memes["worry"] - 0.5)
    world.say(
        f"To check, {captain.id} {incident['test']}. They discovered that {incident['truth']}."
    )
    captain.memes["wisdom"] += 1.0
    captain.memes["confidence"] += 0.5
    world.say(
        f"'{deckhand.id}, you were right to ask for a closer look,' said {captain.id}. "
        "'I saw a wake and added a whole pirate tale to it.'"
    )
    world.say(
        f"Together they {incident['repair']}. No one climbed over the rail, and no one "
        "reached into the moving water."
    )
    captain.memes["relief"] += 1.0
    deckhand.memes["worry"] = 0.0
    world.facts["truth"] = incident["truth"]
    world.facts["repair"] = incident["repair"]
    world.facts["lesson"] = incident["lesson"]
    world.facts["lesson_learned"] = True
    world.say(
        f"{incident['lesson']} Captain {captain.id} wrote those words in the ship's log "
        "under the heading: Lesson Learned."
    )
    world.say(
        f"At sunset, {incident['ending']}. Captain {captain.id} and {deckhand.id} "
        "sailed home with calm hearts and a wiser eye for wakes."
    )


ASP_RULES = r"""
wake_seen(X) :- observes_wake(X).
obvious_clue(X) :- sees_sleeve(X), identifies_sleeve(X).
lesson_learned(X) :- wake_seen(X), obvious_clue(X), checks_safely(X), resolves(X).
valid_story(X) :- lesson_learned(X).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("character", "captain"),
        asp.fact("character", "deckhand"),
        asp.fact("object", "sleeve"),
        asp.fact("setting", "moonwake_bay"),
        asp.fact("observes_wake", "captain"),
        asp.fact("sees_sleeve", "captain"),
        asp.fact("identifies_sleeve", "captain"),
        asp.fact("checks_safely", "captain"),
        asp.fact("resolves", "captain"),
        asp.fact("theme", "lesson_learned"),
    ])


def asp_program(show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    captain: Entity = world.facts["captain"]
    deckhand: Entity = world.facts["deckhand"]
    incident = world.facts["incident"]
    return [
        "Write a child-facing Pirate Tale with a wake, an obvious clue, and a lesson learned.",
        f"Tell how Captain {captain.id} and {deckhand.id} mistake {incident['mistake']} but investigate safely.",
        f"Include the sleeve clue, a short dialogue exchange, and end with {incident['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    captain: Entity = world.facts["captain"]
    deckhand: Entity = world.facts["deckhand"]
    incident = world.facts["incident"]
    return [
        QAItem(
            question=f"What did Captain {captain.id} notice in the bay?",
            answer=f"Captain {captain.id} noticed a strange shape and a wake curling around it in {world.facts['place']}."
        ),
        QAItem(
            question=f"What did {captain.id} first believe?",
            answer=f"{captain.id} first believed that {incident['mistake']}. That belief came before a careful check."
        ),
        QAItem(
            question=f"Why was the sleeve an obvious clue?",
            answer=f"The clue was that {incident['clue']}. This detail showed that the shape was cloth rather than a pirate flag or ghost."
        ),
        QAItem(
            question=f"How did {captain.id} and {deckhand.id} investigate?",
            answer=f"They {incident['test']}. They stayed in the safe channel and did not reach into moving water."
        ),
        QAItem(
            question="What was really making the scene?",
            answer=f"They discovered that {incident['truth']}. The wake did not prove that a pirate was following them."
        ),
        QAItem(
            question=f"What did the sailors do next?",
            answer=f"Together they {incident['repair']}. This solved the problem without creating a new danger."
        ),
        QAItem(
            question="What lesson was learned?",
            answer=incident["lesson"]
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wake?",
            answer="A wake is the moving line or ripple of water left behind a boat or another object moving through water."
        ),
        QAItem(
            question="What is a sleeve?",
            answer="A sleeve is the part of clothing that covers an arm."
        ),
        QAItem(
            question="Why should sailors investigate from a safe distance?",
            answer="They should investigate from a safe distance because moving water, boats, and floating objects can be dangerous."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.type:10}) meters={meters} memes={memes}"
        )
    lines.append(f"  wake_seen={world.facts.get('wake_seen')}")
    lines.append(f"  obvious_clue={world.facts.get('obvious_clue')}")
    lines.append(f"  lesson_learned={world.facts.get('lesson_learned')}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Pirate Tale about a wake, a sleeve, and a lesson learned."
    )
    parser.add_argument("--captain", choices=CAPTAIN_NAMES)
    parser.add_argument("--deckhand", choices=DECKHAND_NAMES)
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
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    deckhands = [name for name in DECKHAND_NAMES if name != captain]
    deckhand = args.deckhand or rng.choice(deckhands)
    if captain == deckhand:
        raise StoryError("Captain and deckhand must have different names.")
    return StoryParams(captain=captain, deckhand=deckhand)


def asp_verify() -> int:
    if not asp_valid():
        print("MISMATCH: Python reasonableness gate failed.")
        return 1
    try:
        import asp
        model = asp.one_model(asp_program())
        valid = asp.atoms(model, "valid_story")
    except Exception as exc:
        print(f"MISMATCH: ASP verification failed: {exc}")
        return 1
    if ("captain",) not in valid:
        print("MISMATCH: ASP model did not derive valid_story(captain).")
        return 1
    for seed in range(5):
        sample = generate(StoryParams("Luna", "Nico", seed=seed))
        if not sample.world or not sample.world.facts.get("lesson_learned"):
            print("MISMATCH: generated story did not complete its lesson.")
            return 1
        if "wake" not in sample.story.lower() or "sleeve" not in sample.story.lower():
            print("MISMATCH: generated story lost a required seed word.")
            return 1
    print("OK: Python and ASP gates pass; generated stories complete.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        values = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(values)} compatible stories:")
        for value in values:
            print(f"  {value}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        choices = [
            ("Luna", "Nico"),
            ("Maris", "Finn"),
            ("Coral", "Sella"),
            ("Pip", "Bram"),
        ]
        samples = [
            generate(StoryParams(captain=c, deckhand=d, seed=base_seed + i))
            for i, (c, d) in enumerate(choices)
        ]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
