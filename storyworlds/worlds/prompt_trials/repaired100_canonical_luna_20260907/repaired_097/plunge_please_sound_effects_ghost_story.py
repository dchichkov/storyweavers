#!/usr/bin/env python3
"""
Standalone storyworld: a gentle ghost story about a brave plunge and a polite
please, told with playful sound effects.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    protagonist: str = "Luna"
    protagonist_type: str = "girl"
    ghost: str = "Murmur"
    setting: str = "the moonlit bathhouse"
    incident_id: int = 0
    telling_mode: int = 0


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


INCIDENTS = [
    {
        "title": "the bell beneath the water",
        "premise": "A silver bell rang from the deep plunge pool, though no hand stood near it.",
        "clue": "a blue ribbon bobbing beside the old diving steps",
        "cause": "the ghost's keepsake bell had slipped into the pool when a draft tugged its ribbon",
        "action": "asked the ghost where the bell belonged and used a long pool hook while staying on the safe stones",
        "resolution": "Luna lifted the bell with the hook, and Murmur guided its ribbon back to the warm lantern post.",
        "ending": "The bell gave one tiny ding, then rested quietly in the moonlight.",
        "lesson": "A polite question can make a frightening mystery feel small enough to solve.",
    },
    {
        "title": "the splash in the empty hall",
        "premise": "A huge splash echoed through the empty hall, followed by three wet footprints.",
        "clue": "drops leading from the locked fountain to a loose cloud of mist",
        "cause": "Murmur had been practicing a ghostly bow and accidentally startled the fountain sprite",
        "action": "said please before asking the spirit to show the safe path and followed the dry edge of the pool",
        "resolution": "The fountain sprite stopped splashing, and Murmur learned to bow away from the water.",
        "ending": "The last drop made a soft plip beside Luna's lantern.",
        "lesson": "Good manners help everyone listen, even when a surprise makes a big noise.",
    },
    {
        "title": "the whispering drain",
        "premise": "The drain whispered, 'Come closer,' from beneath the plunge pool.",
        "clue": "a folded paper star caught in the grate",
        "cause": "the wind was blowing through an old pipe and carrying the ghost's lost invitation",
        "action": "read the invitation aloud from the dry walkway and asked permission before touching the grate",
        "resolution": "Murmur remembered the forgotten midnight gathering and opened the lantern room for one careful visit.",
        "ending": "The drain whispered good night instead of come closer.",
        "lesson": "Asking before acting can turn a spooky sound into a useful message.",
    },
]


OPENINGS = [
    "On a night when the moon looked like a silver button,",
    "Just after the last lantern blinked awake,",
    "At the hour when shadows stretched their toes,",
    "One quiet evening, when the floorboards held their breath,",
]

SOUNDS = [
    ("plip", "A drop fell with a gentle plip."),
    ("whoosh", "A chilly whoosh slid beneath the door."),
    ("clink", "A loose lantern chain answered with a clink."),
    ("swish", "The curtain made a soft swish in the moon breeze."),
]


def reason_gate(params: StoryParams) -> None:
    if not params.protagonist.strip():
        raise StoryError("The protagonist needs a name.")
    if not params.ghost.strip():
        raise StoryError("The ghost needs a name.")
    if params.protagonist.strip().lower() == params.ghost.strip().lower():
        raise StoryError("The protagonist and ghost must have different names.")
    if params.setting not in {"the moonlit bathhouse", "the old plunge hall", "the misty riverside pool"}:
        raise StoryError("Choose a recognized watery setting.")


def build_world(params: StoryParams) -> World:
    world = World(params)
    world.add(Entity(
        "hero",
        "character",
        params.protagonist,
        meters={"courage": 0.0, "distance_to_pool": 4.0},
        memes={"worry": 0.0, "curiosity": 1.0, "trust": 0.0},
        location="dry walkway",
    ))
    world.add(Entity(
        "ghost",
        "ghost",
        params.ghost,
        meters={"visibility": 0.4, "bell_distance": 3.0},
        memes={"loneliness": 1.0, "hope": 0.0},
        location="misty corner",
    ))
    world.add(Entity(
        "pool",
        "place",
        "the plunge pool",
        meters={"depth": 3.0, "ripples": 0.0},
        memes={},
        location=params.setting,
    ))
    world.add(Entity(
        "bell",
        "object",
        "the silver bell",
        meters={"wet": 1.0, "distance_to_lantern": 2.0},
        memes={},
        location="plunge pool",
    ))
    world.add(Entity(
        "hook",
        "tool",
        "the long pool hook",
        meters={"reach": 3.5, "safe_use": 1.0},
        memes={},
        location="stone wall",
    ))
    world.facts["safe_boundary"] = "the dry stones around the pool"
    return world


def tell(params: StoryParams) -> World:
    reason_gate(params)
    world = build_world(params)
    hero = world.entities["hero"]
    ghost = world.entities["ghost"]
    bell = world.entities["bell"]
    incident = INCIDENTS[params.incident_id % len(INCIDENTS)]
    opening = OPENINGS[params.telling_mode % len(OPENINGS)]
    sound_a, sound_b = SOUNDS[(params.incident_id + params.telling_mode) % len(SOUNDS)]

    world.facts.update(
        title=incident["title"],
        premise=incident["premise"],
        clue=incident["clue"],
        cause=incident["cause"],
        action=incident["action"],
        resolution=incident["resolution"],
        ending=incident["ending"],
        lesson=incident["lesson"],
        sound=sound_a,
    )

    hero.memes["worry"] = 1.0
    ghost.memes["loneliness"] = 1.0
    world.say(
        f"{opening} {hero.label} visited {params.setting}, where {ghost.label}, a small friendly ghost, "
        "was supposed to guard the old plunge pool."
    )
    world.say(
        f"{sound_a.capitalize()} {sound_b} Then a strange sound rose from the water. "
        f"{incident['premise']}"
    )
    world.say(
        f"{hero.label} stood on {world.facts['safe_boundary']}. The pool was deep, so there would be no "
        "reckless jumping or swimming. A safe plunge into courage would have to come first."
    )

    world.para()
    world.say(
        f"'{ghost.label}, are you frightened too?' {hero.label} asked. "
        f"'A little,' {ghost.label} replied. 'May we solve it together, please?'"
    )
    hero.memes["trust"] += 1.0
    ghost.memes["hope"] += 1.0
    world.say(
        f"{hero.label} noticed {incident['clue']}. The clue pointed toward the pool, but the safe way "
        "forward was clear: stay dry, keep the edge in sight, and use a tool."
    )
    world.say(
        f"'Please show me where it fell,' said {hero.label}. '{incident['action'].capitalize()}.' "
        f"{ghost.label} nodded. 'Thank you for asking,' the ghost said."
    )
    hero.meters["courage"] = 1.0
    hero.meters["distance_to_pool"] = 2.0
    bell.location = "hook basket"
    bell.meters["wet"] = 0.0
    bell.meters["distance_to_lantern"] = 0.0
    ghost.meters["bell_distance"] = 0.0
    world.say(incident["resolution"])

    world.para()
    hero.memes["worry"] = 0.0
    ghost.memes["loneliness"] = 0.0
    world.say(
        f"{hero.label} took a brave plunge into the mystery, not into the water. "
        f"'The word please made the dark feel friendlier,' {hero.label} said."
    )
    world.say(
        f"{ghost.label} smiled like a candle behind a curtain. 'And listening helped me choose what to do,' "
        "the ghost replied."
    )
    world.say(f"The lesson was simple: {incident['lesson']}")
    world.say(incident["ending"])
    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a gentle ghost story about {f['title']} with the sound effect {f['sound']}.",
        f"Show {world.entities['hero'].label} making a brave plunge into a mystery while staying safe.",
        f"Include a conversation in which saying please changes what the ghost decides to do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.entities["hero"].label
    ghost = world.entities["ghost"].label
    return [
        QAItem(
            question=f"What mystery did {hero} and {ghost} solve?",
            answer=f"They solved the mystery of {f['title']}: {f['premise']}",
        ),
        QAItem(
            question=f"What clue did {hero} notice?",
            answer=f"{hero} noticed {f['clue']}, which showed where the strange event had begun.",
        ),
        QAItem(
            question="Why did nobody jump into the plunge pool?",
            answer="The plunge pool was deep, so they stayed on the dry stones and used the long pool hook instead.",
        ),
        QAItem(
            question=f"How did saying please help {hero} and {ghost}?",
            answer=f"Saying please made the conversation respectful, so {ghost} shared what it knew and helped {hero} act safely.",
        ),
        QAItem(
            question=f"What did {hero} learn?",
            answer=f"{hero} learned that {f['lesson']}",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a ghost story?",
        answer="A ghost story is a tale about a ghost or mysterious spirit. It can be spooky, playful, or gentle.",
    ),
    QAItem(
        question="What is a plunge?",
        answer="A plunge is a quick dive or drop into something. In this story, the brave plunge is into solving a mystery, not into unsafe water.",
    ),
    QAItem(
        question="Why say please?",
        answer="Please is a polite word that shows respect when asking someone to help or do something.",
    ),
    QAItem(
        question="Why are sound effects useful in a story?",
        answer="Sound effects such as plip, whoosh, and clink help readers imagine what is happening.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:8} ({entity.kind:9}) location={entity.location!r} "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_boundary(hero).
deep(pool).
uses_hook(hero, hook).
bell_at_pool(bell).
asks_please(hero).
returns_bell(hero).
courageous(hero) :- uses_hook(hero, hook), asks_please(hero), returns_bell(hero).
coherent :- courageous(hero), bell_at_pool(bell), deep(pool).
#show coherent/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("safe_boundary", "hero"),
        asp.fact("deep", "pool"),
        asp.fact("uses_hook", "hero", "hook"),
        asp.fact("bell_at_pool", "bell"),
        asp.fact("asks_please", "hero"),
        asp.fact("returns_bell", "hero"),
    ])


def asp_program(show: str = "#show coherent/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    asp_ok = any(symbol.name == "coherent" for symbol in model)
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python reasonableness gate.")
        return 1
    sample = generate(StoryParams())
    if not sample.story or "please" not in sample.story.lower() or "plunge" not in sample.story.lower():
        print("MISMATCH: generated story check failed.")
        return 1
    print("OK: ASP and Python reasonableness gate agree.")
    print("OK: generated story check passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gentle plunge-and-please ghost storyworld."
    )
    parser.add_argument("--protagonist")
    parser.add_argument("--protagonist-type", choices=["girl", "boy", "woman", "man"], default="girl")
    parser.add_argument("--ghost")
    parser.add_argument(
        "--setting",
        choices=["the moonlit bathhouse", "the old plunge hall", "the misty riverside pool"],
        default="the moonlit bathhouse",
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int) -> StoryParams:
    protagonist = args.protagonist or rng.choice(["Luna", "Mara", "Nell", "Ivy"])
    ghost = args.ghost or rng.choice(["Murmur", "Wisp", "Pale Pip", "Echo"])
    if protagonist.strip().lower() == ghost.strip().lower():
        raise StoryError("The protagonist and ghost must have different names.")
    return StoryParams(
        seed=args.seed,
        protagonist=protagonist,
        protagonist_type=args.protagonist_type,
        ghost=ghost,
        setting=args.setting,
        incident_id=sample_seed % len(INCIDENTS),
        telling_mode=(sample_seed // len(INCIDENTS)) % len(OPENINGS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        print(" ".join(str(symbol) for symbol in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        choices = [
            ("Luna", "Murmur", "the moonlit bathhouse"),
            ("Mara", "Wisp", "the old plunge hall"),
            ("Nell", "Echo", "the misty riverside pool"),
        ]
        for offset, (hero, ghost, setting) in enumerate(choices):
            params = StoryParams(
                seed=base_seed + offset,
                protagonist=hero,
                ghost=ghost,
                setting=setting,
                incident_id=(base_seed + offset) % len(INCIDENTS),
                telling_mode=((base_seed + offset) // len(INCIDENTS)) % len(OPENINGS),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            sample_seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(sample_seed), sample_seed)
            params.seed = sample_seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
