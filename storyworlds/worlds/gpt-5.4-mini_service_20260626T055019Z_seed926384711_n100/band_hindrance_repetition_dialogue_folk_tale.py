#!/usr/bin/env python3
"""
storyworlds/worlds/band_hindrance_repetition_dialogue_folk_tale.py
===================================================================

A small folk-tale storyworld about a band that must cross a hindrance,
using repetition and dialogue.

Premise:
- A village band wants to play at the hilltop fair.
- A narrow bridge, a broken cartwheel, or a stormy path can hinder the trip.
- The band tries the same way more than once, learns from the hindrance, and
  finds a kinder path forward.

The world model tracks physical meters and emotional memes:
- meters: distance, load, wear, blocked
- memes: hope, worry, courage, calm, stubbornness, joy

The story is generated from a simulated sequence:
setup -> attempt -> repeated hindrance -> spoken advice -> improved plan -> arrival.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["distance", "load", "wear", "blocked"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "worry", "courage", "calm", "stubbornness", "joy"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        feminine = {"woman", "girl", "mother", "daughter", "singer"}
        masculine = {"man", "boy", "father", "son", "drummer"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    path: str
    hinderance: str
    detail: str


@dataclass
class BandMember:
    name: str
    role: str
    type: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    attempts: int = 0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "brook": Setting(
        place="the brook road",
        path="a stepping-stone path",
        hinderance="the brook had swollen and covered the stones",
        detail="Water shone over the missing stones, and the old bridge stood too far away.",
    ),
    "hill": Setting(
        place="the hill road",
        path="a muddy hill path",
        hinderance="the mud kept sliding underfoot",
        detail="Every step sank a little, and the cart behind them groaned.",
    ),
    "forest": Setting(
        place="the forest path",
        path="a rooty forest lane",
        hinderance="a fallen log blocked the lane",
        detail="The log lay across the way like a sleeping giant.",
    ),
}

BAND_ROLES = [
    ("fiddle", "fiddler", "woman"),
    ("drum", "drummer", "man"),
    ("flute", "flutist", "woman"),
    ("horn", "horn player", "man"),
]

HELPERS = [
    ("goat cart", "cart", "thing"),
    ("old donkey", "donkey", "thing"),
    ("wise lantern-bearer", "guide", "woman"),
    ("river child", "child", "boy"),
]

SAYINGS = {
    "greet": [
        "Good day, good day, all the road is ours to try.",
        "Step by step, and song by song, we shall go on.",
    ],
    "hindrance": [
        "The road says no today.",
        "This way is not ready for us.",
        "The path has tied a knot in our going.",
    ],
    "fix": [
        "If one way is blocked, another may open.",
        "A hard road grows kinder when travelers listen.",
        "We need not fight the road; we can outthink it.",
    ],
    "ending": [
        "So the band played at the fair with bright hearts and steady feet.",
        "And the music reached the hilltop just as the sun turned gold.",
        "In the end, the band’s song went farther than the hindrance.",
    ],
}


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_places() -> list[str]:
    return sorted(SETTINGS.keys())


def build_band(world: World, rng: random.Random) -> list[Entity]:
    names = ["Mara", "Jory", "Tess", "Pip", "Oren", "Nina"]
    rng.shuffle(names)
    band = []
    for idx, (instrument, role, type_) in enumerate(BAND_ROLES):
        ent = world.add(Entity(
            id=names[idx],
            kind="character",
            type=type_,
            label=names[idx],
            phrase=f"{names[idx]} the {role}",
        ))
        ent.meters["distance"] = 0
        band.append(ent)
        world.facts.setdefault("roles", []).append((ent.id, role, instrument))
    return band


def build_helper(world: World, rng: random.Random) -> Entity:
    name, role, type_ = rng.choice(HELPERS)
    return world.add(Entity(
        id=name,
        kind="character" if type_ != "thing" else "thing",
        type=type_,
        label=name,
        phrase=f"{name} the {role}",
    ))


def repetition_line(count: int) -> str:
    if count == 1:
        return "They tried once."
    if count == 2:
        return "They tried again."
    return "They tried once more."


def choose_dialogue(key: str, rng: random.Random) -> str:
    return rng.choice(SAYINGS[key])


def setup_world(params: StoryParams, rng: random.Random) -> World:
    setting = SETTINGS[params.place]
    world = World(setting=setting)
    band = build_band(world, rng)
    helper = build_helper(world, rng)
    world.facts["band"] = band
    world.facts["helper"] = helper
    world.facts["setting"] = setting
    world.facts["attempts"] = 0
    return world


def hindrance_level(world: World) -> float:
    setting = world.setting
    if setting.hinderance.startswith("the mud"):
        return 2.0
    if setting.hinderance.startswith("a fallen log"):
        return 1.5
    return 1.0


def first_attempt(world: World, rng: random.Random) -> str:
    band = world.facts["band"]
    for member in band:
        member.memes["hope"] += 1
        member.meters["distance"] += 1
    world.facts["attempts"] += 1
    world.say(f"Once upon a time, a little band set out for {world.setting.place}.")
    world.say(
        f"They walked along {world.setting.path}, and each one hummed the same brave tune."
    )
    world.say(choose_dialogue("greet", rng))
    world.say(repetition_line(world.facts["attempts"]))
    world.say(world.setting.detail)
    return "blocked"


def second_attempt(world: World, rng: random.Random) -> str:
    band = world.facts["band"]
    helper = world.facts["helper"]
    world.facts["attempts"] += 1
    for member in band:
        member.memes["worry"] += 1
        member.memes["stubbornness"] += 1
    world.say(repetition_line(world.facts["attempts"]))
    world.say(
        f'The fiddler said, "We cannot pass this way."'
    )
    world.say(
        f'The drummer said, "{choose_dialogue("hindrance", rng)}"'
    )
    helper.memes["calm"] += 1
    world.say(
        f'The {helper.phrase} answered, "{choose_dialogue("fix", rng)}"'
    )
    return "blocked"


def find_way(world: World, rng: random.Random) -> str:
    band = world.facts["band"]
    helper = world.facts["helper"]
    setting = world.setting

    for member in band:
        member.memes["courage"] += 1
        member.memes["hope"] += 1
        member.memes["worry"] = max(0.0, member.memes["worry"] - 1.0)

    if setting.place == "the brook road":
        path = "They found a plank beside the mill and made a little bridge."
    elif setting.place == "the hill road":
        path = "They moved the cart to the grass and climbed where the ground was firm."
    else:
        path = "They climbed over the fallen log with the helper's lantern leading the way."

    world.say(
        f'The band asked, "What if we try a kinder road?"'
    )
    world.say(
        f'The {helper.label} smiled and said, "Yes, yes, there is another way."'
    )
    world.say(path)
    world.say(
        f"They went on together, and the hindrance was left behind like a dark stone at the roadside."
    )
    world.say(choose_dialogue("ending", rng))
    for member in band:
        member.memes["joy"] += 1
    helper.memes["joy"] += 1
    return "clear"


def tell(params: StoryParams, rng: random.Random) -> World:
    world = setup_world(params, rng)
    first_attempt(world, rng)
    world.para()
    second_attempt(world, rng)
    world.para()
    find_way(world, rng)
    world.facts["resolved"] = True
    world.facts["params"] = params
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    setting = world.facts["setting"]
    return [
        f'Write a short folk tale about a band trying to reach {setting.place} despite a hindrance.',
        f"Tell a simple repetition-and-dialogue story where a band faces {setting.hinderance} and keeps going.",
        f"Write a child-friendly folk tale with a band, a hindrance, and a helpful spoken answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    band = world.facts["band"]
    helper = world.facts["helper"]
    setting = world.facts["setting"]
    leader = band[0]
    return [
        QAItem(
            question=f"Where was the band trying to go?",
            answer=f"The band was trying to reach {setting.place}.",
        ),
        QAItem(
            question=f"What was the hindrance on the road?",
            answer=f"The hindrance was that {setting.hinderance}.",
        ),
        QAItem(
            question=f"Who helped the band find a better way?",
            answer=f"The {helper.phrase} helped them find a better way.",
        ),
        QAItem(
            question=f"What did {leader.label} say when the road would not open?",
            answer='The band asked, "What if we try a kinder road?" and kept looking for another way.',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a band?",
            answer="A band is a group of people who make music together.",
        ),
        QAItem(
            question="What is a hindrance?",
            answer="A hindrance is something that makes a task harder or slows it down.",
        ),
        QAItem(
            question="What does repetition do in a folk tale?",
            answer="Repetition means a story repeats a phrase or action, which makes it easy to remember.",
        ),
        QAItem(
            question="Why do stories use dialogue?",
            answer="Dialogue lets characters speak, so the story feels lively and clear.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(brook).
setting(hill).
setting(forest).

hindrance(brook, swollen_water).
hindrance(hill, slippery_mud).
hindrance(forest, fallen_log).

can_travel(brook, plank_bridge).
can_travel(hill, firm_grass).
can_travel(forest, climb_over).

resolved(P) :- setting(P), hindrance(P, H), can_travel(P, Fix).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
        if key == "brook":
            lines.append(asp.fact("hinderance", key, "swollen_water"))
        elif key == "hill":
            lines.append(asp.fact("hinderance", key, "slippery_mud"))
        elif key == "forest":
            lines.append(asp.fact("hinderance", key, "fallen_log"))
        lines.append(asp.fact("fix", key, {
            "brook": "plank_bridge",
            "hill": "firm_grass",
            "forest": "climb_over",
        }[key]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    return sorted({a[0] for a in asp.atoms(model, "resolved")})


def asp_verify() -> int:
    py = set(valid_places())
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches valid_places() ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small folk-tale storyworld about a band and a hindrance."
    )
    ap.add_argument("--place", choices=valid_places())
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(valid_places())
    return StoryParams(place=place)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = tell(params, rng)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:16} ({ent.kind:8}) {' '.join(bits)}")
    lines.append(f"  attempts={world.facts.get('attempts', 0)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in valid_places():
            params = StoryParams(place=place, seed=base_seed)
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
