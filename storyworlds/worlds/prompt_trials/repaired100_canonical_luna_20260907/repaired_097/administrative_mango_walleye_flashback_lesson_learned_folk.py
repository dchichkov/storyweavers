#!/usr/bin/env python3
"""
A small folk-tale storyworld about an administrative mango, a walleye,
a flashback, and a lesson learned.
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
    helper: str = "Tavi"
    elder: str = "Aunt Sela"
    village: str = "Riverbend"
    incident_id: int = 0
    voice_id: int = 0


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
    paragraphs: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs.append(text)

    def render(self) -> str:
        return "\n\n".join(self.paragraphs)


INCIDENTS = [
    {
        "title": "The Mango Register",
        "premise": "The village's finest mango disappeared from the basket beside the council desk.",
        "clue": "a bright mango leaf caught beneath the walleye boat's oar",
        "cause": "the walleye had nudged the boat while the wind carried the mango into its woven net",
        "action": "followed the leaf trail from the council desk to the river landing",
        "resolution": "The mango was found in the boat's net, still whole, and the village register was corrected.",
        "ending": "At sunset, the mango rested on the council table beneath a clean green leaf.",
        "lesson": "A careful record is useful, but a careful look is wiser than a hurried accusation.",
    },
    {
        "title": "The Administrative Stamp",
        "premise": "An official mango stamp appeared on the wrong page of the village book.",
        "clue": "a smear of golden fruit beside the walleye fisher's empty lunch bowl",
        "cause": "the stamp had been pressed into mango pulp before touching the page",
        "action": "compared the page, the stamp, and the lunch bowl without tearing the book",
        "resolution": "The elder washed the stamp, marked the page correctly, and gave the fisher a fresh bowl.",
        "ending": "The repaired book dried beside a slice of mango in the warm light.",
        "lesson": "When a mark looks mysterious, learn what touched it before deciding what it means.",
    },
    {
        "title": "The Walleye Permit",
        "premise": "The administrative clerk said that the walleye fisher had no permit, though the fisher insisted it had been filed.",
        "clue": "a mango-colored corner showing beneath the old market ledger",
        "cause": "the permit had slipped behind the ledger when someone used a mango as a paperweight",
        "action": "lifted the ledger gently and checked the permit number against the village list",
        "resolution": "The permit was returned to its proper folder, and the fisher was welcomed back to the river.",
        "ending": "The folder closed with the mango-colored corner safely tucked inside.",
        "lesson": "A missing paper may need patience, not punishment.",
    },
    {
        "title": "The River Basket",
        "premise": "A basket of ripe mangoes was listed as delivered, but the market stall stood empty.",
        "clue": "small walleye scales glittering beside a damp wheel track",
        "cause": "the delivery cart had stopped at the river, where a walleye basket tipped against it",
        "action": "followed the wheel track and asked the boat keeper what had happened",
        "resolution": "The mangoes were gathered, counted, and delivered after the administrative list was updated.",
        "ending": "The market bell rang above a full basket and a freshly written list.",
        "lesson": "Good work joins kindness with accurate counting.",
    },
]


VOICES = [
    "Old folk say that a village grows wise one question at a time.",
    "The river had seen many mistakes, and it never laughed at one that was mended.",
    "In those days, even a small fruit could teach a large lesson.",
    "The villagers believed that truth liked patient footsteps.",
]


def reason_gate(params: StoryParams) -> None:
    names = [params.protagonist.strip(), params.helper.strip(), params.elder.strip()]
    if any(not name for name in names):
        raise StoryError("protagonist, helper, and elder names must not be empty")
    if len(set(names)) != len(names):
        raise StoryError("protagonist, helper, and elder must have different names")
    if not params.village.strip():
        raise StoryError("village must not be empty")
    if params.incident_id < 0 or params.voice_id < 0:
        raise StoryError("incident and voice choices must be non-negative")


def build_world(params: StoryParams) -> World:
    world = World(params)
    world.add(Entity(
        "hero", "character", params.protagonist,
        meters={"attention": 0.0},
        memes={"curiosity": 0.0, "confidence": 0.0},
        location="council hall",
    ))
    world.add(Entity(
        "helper", "character", params.helper,
        meters={"attention": 0.0},
        memes={"curiosity": 1.0, "trust": 0.0},
        location="river landing",
    ))
    world.add(Entity(
        "elder", "character", params.elder,
        meters={"paperwork": 1.0},
        memes={"worry": 0.0, "patience": 1.0},
        location="council hall",
    ))
    world.add(Entity(
        "mango", "fruit", "the golden mango",
        meters={"ripe": 1.0, "moved": 0.0, "found": 0.0},
        memes={"importance": 1.0},
        location="council table",
    ))
    world.add(Entity(
        "walleye", "fish", "the silver walleye",
        meters={"scales": 1.0, "near_boat": 1.0},
        memes={"mystery": 0.0},
        location="river net",
    ))
    world.add(Entity(
        "register", "object", "the administrative register",
        meters={"open": 0.0, "corrected": 0.0},
        memes={},
        location="council desk",
    ))
    world.facts["village"] = params.village
    return world


def tell(params: StoryParams) -> World:
    reason_gate(params)
    incident = INCIDENTS[params.incident_id % len(INCIDENTS)]
    voice = VOICES[params.voice_id % len(VOICES)]
    world = build_world(params)

    hero = world.entities["hero"]
    helper = world.entities["helper"]
    elder = world.entities["elder"]
    mango = world.entities["mango"]
    register = world.entities["register"]

    hero.memes["curiosity"] = 1.0
    elder.memes["worry"] = 1.0
    world.facts.update(
        title=incident["title"],
        premise=incident["premise"],
        clue=incident["clue"],
        cause=incident["cause"],
        action=incident["action"],
        resolution=incident["resolution"],
        ending=incident["ending"],
        lesson=incident["lesson"],
        solved=False,
    )

    world.say(
        f"Long ago in {params.village}, {params.protagonist} helped {params.elder} "
        f"keep the administrative register. {voice}"
    )
    world.say(
        f"One morning, {incident['premise']} {params.elder} frowned at the empty place, "
        f"while {params.protagonist} noticed that the river wind had turned a page."
    )
    world.say(
        f"'{params.protagonist}, find the truth before we blame a neighbor,' said {params.elder}. "
        f"'I will look by the river,' said {params.helper}. 'And I will listen to every clue.'"
    )

    world.paragraphs.append(
        f"Before setting out, {params.protagonist} remembered a flashback. The day before, "
        f"{params.helper} had carried a walleye basket past the council hall while a ripe mango "
        f"balanced on the desk. The memory made {params.protagonist} wonder whether the wind, "
        f"rather than a thief, had joined the story."
    )
    world.say(
        f"{params.protagonist} and {params.helper} {incident['action']}. "
        f"Near the boat they found {incident['clue']}. "
        f"'The clue does not accuse anyone,' said {params.helper}. "
        f"'No,' said {params.protagonist}, 'but it tells us where to look next.'"
    )
    world.say(
        f"They checked the river net and the administrative papers. At last they learned that "
        f"{incident['cause']}. {params.elder} hurried down the path, then smiled when the evidence "
        f"made the answer plain."
    )

    mango.meters["moved"] = 1.0
    mango.meters["found"] = 1.0
    mango.location = "council table"
    register.meters["corrected"] = 1.0
    register.meters["open"] = 0.0
    hero.memes["confidence"] = 1.0
    helper.memes["trust"] = 1.0
    elder.memes["worry"] = 0.0
    world.facts["solved"] = True

    world.say(incident["resolution"])
    world.say(
        f"'{incident['lesson']}' said {params.elder}. "
        f"{params.protagonist} nodded, and {params.helper} placed the walleye basket safely "
        f"away from the papers."
    )
    world.say(
        f"This was the lesson learned: {incident['lesson']} "
        f"{incident['ending']}"
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Tell a folk tale about {facts['title']} in {world.params.village}.",
        f"Use a flashback to explain how the administrative mystery began with a mango and a walleye.",
        f"End with the lesson learned: {facts['lesson']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            f"What problem did {p.protagonist} and {p.elder} face?",
            f"They faced this problem: {f['premise']} They investigated before accusing anyone.",
        ),
        QAItem(
            f"What clue helped {p.protagonist} and {p.helper}?",
            f"They found {f['clue']}. That clue connected the administrative mystery to the river and the walleye boat.",
        ),
        QAItem(
            "How did the flashback help?",
            f"The flashback reminded {p.protagonist} that {p.helper} had carried a walleye basket near the mango. That memory suggested a wind or basket accident instead of theft.",
        ),
        QAItem(
            "How was the mystery resolved?",
            f"They {f['action']}. They learned that {f['cause']}. {f['resolution']}",
        ),
        QAItem(
            "What lesson was learned?",
            f"The lesson learned was that {f['lesson']}",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        "What is an administrative register?",
        "An administrative register is an organized record used to keep track of names, goods, permissions, or other village business.",
    ),
    QAItem(
        "What is a mango?",
        "A mango is a sweet tropical fruit with fragrant golden flesh around a large seed.",
    ),
    QAItem(
        "What is a walleye?",
        "A walleye is a freshwater fish known for its pale eyes and silvery body.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:9} {entity.kind:10} location={entity.location!r} "
            f"meters={meters} memes={memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
mango_found :- mango(m), moved(m), found(m).
record_correct :- register(r), corrected(r).
safe_story :- mango_found, record_correct, clue(c), walleye(w).
#show safe_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("mango", "mango"),
        asp.fact("moved", "mango"),
        asp.fact("found", "mango"),
        asp.fact("register", "register"),
        asp.fact("corrected", "register"),
        asp.fact("clue", "leaf"),
        asp.fact("walleye", "walleye"),
    ])


def asp_program(show: str = "#show safe_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    ok = any(symbol.name == "safe_story" for symbol in model)
    if not ok:
        print("MISMATCH: ASP did not find a safe story.")
        return 1
    sample = generate(StoryParams())
    if "lesson learned" not in sample.story.lower() or "flashback" not in sample.story.lower():
        print("MISMATCH: generated story lacks required narrative instruments.")
        return 1
    print("OK: ASP and Python checks agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Administrative mango and walleye folk-tale storyworld."
    )
    parser.add_argument("--protagonist")
    parser.add_argument("--helper")
    parser.add_argument("--elder")
    parser.add_argument("--village", default="Riverbend")
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
    protagonist = args.protagonist or rng.choice(["Luna", "Mira", "Nia", "Suri"])
    helper = args.helper or rng.choice(["Tavi", "Beni", "Oko", "Pema"])
    elder = args.elder or rng.choice(["Aunt Sela", "Grandmother Iri", "Uncle Jaro"])
    params = StoryParams(
        seed=args.seed,
        protagonist=protagonist,
        helper=helper,
        elder=elder,
        village=args.village,
        incident_id=sample_seed % len(INCIDENTS),
        voice_id=(sample_seed // len(INCIDENTS)) % len(VOICES),
    )
    reason_gate(params)
    return params


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
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print("\n".join(str(symbol) for symbol in asp.one_model(asp_program())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        choices = [
            ("Luna", "Tavi", "Aunt Sela"),
            ("Mira", "Beni", "Grandmother Iri"),
            ("Nia", "Oko", "Uncle Jaro"),
            ("Suri", "Pema", "Aunt Sela"),
        ]
        for i, (hero, helper, elder) in enumerate(choices):
            params = StoryParams(
                seed=base_seed + i,
                protagonist=hero,
                helper=helper,
                elder=elder,
                village=args.village,
                incident_id=i % len(INCIDENTS),
                voice_id=i % len(VOICES),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 0)):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed), seed)
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

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
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
