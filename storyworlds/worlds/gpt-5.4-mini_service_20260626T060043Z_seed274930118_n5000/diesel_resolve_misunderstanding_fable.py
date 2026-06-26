#!/usr/bin/env python3
"""
storyworlds/worlds/diesel_resolve_misunderstanding_fable.py
===========================================================

A small fable-style story world about a diesel machine, a misunderstanding,
and a gentle resolution.

Premise:
A hardworking diesel boat, cart, or engine arrives in a village where some
animals misunderstand its rumble. They think it is angry or dangerous, but the
truth is simpler: the machine is carrying useful work and wants to help.

Story shape:
- setup: the diesel helper arrives and is noticed
- tension: a misunderstanding spreads
- turn: someone looks closely and explains the real cause
- resolution: the characters choose a safer, kinder plan and the world settles

The world is intentionally small and constraint-checked. It generates child-
facing fable prose from world state, not from a frozen template with swapped
nouns.
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

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"animal", "fox", "goat", "mule", "donkey"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"boy", "father", "man", "lion"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    village: bool = True


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    sound: str
    work: str
    soot: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow"),
    "harbor": Setting(place="the harbor"),
    "mill": Setting(place="the mill yard"),
    "lane": Setting(place="the village lane"),
}

HELPERS = {
    "diesel_wagon": Helper(
        id="diesel_wagon",
        label="diesel wagon",
        phrase="a small diesel wagon with a steady cough",
        sound="rumbled and hummed",
        work="carry flour and apples",
        soot="a little soot",
        keyword="diesel",
        tags={"diesel", "work", "sound"},
    ),
    "diesel_boat": Helper(
        id="diesel_boat",
        label="diesel boat",
        phrase="a diesel boat with a slow, even thrum",
        sound="throbbed softly",
        work="bring fish and salt",
        soot="a little smoke",
        keyword="diesel",
        tags={"diesel", "water", "sound"},
    ),
    "diesel_cart": Helper(
        id="diesel_cart",
        label="diesel cart",
        phrase="a sturdy diesel cart with brass lanterns",
        sound="chugged along",
        work="deliver grain and tools",
        soot="a gray puff",
        keyword="diesel",
        tags={"diesel", "road", "sound"},
    ),
}

CHARACTERS = {
    "fox": {"type": "fox", "name": "Fenn", "traits": ["quick", "curious"]},
    "goat": {"type": "goat", "name": "Gilda", "traits": ["careful", "kind"]},
    "mule": {"type": "mule", "name": "Milo", "traits": ["patient", "plainspoken"]},
    "sparrow": {"type": "sparrow", "name": "Suri", "traits": ["small", "bright"]},
}

SPEAKERS = ["fox", "goat", "mule", "sparrow"]


@dataclass
class StoryParams:
    place: str
    helper: str
    speaker: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
misunderstood(H, C) :- helper(H), character(C), hears(C, H), noisy(H), not knows(C, H).
resolved(H, C) :- misunderstood(H, C), explained(C, H).
safe_story(Place, H, C) :- setting(Place), helper_at(Place, H), character(C), resolved(H, C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("noisy", hid))
        for t in sorted(h.tags):
            lines.append(asp.fact("tag", hid, t))
    for cid, c in CHARACTERS.items():
        lines.append(asp.fact("character", cid))
        lines.append(asp.fact("knows", cid, "ordinary_work"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_safe_story() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_story/3."))
    return sorted(set(asp.atoms(model, "safe_story")))

def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown diesel helper.")
    if params.speaker not in CHARACTERS:
        raise StoryError("Unknown speaker.")
    if params.helper == "diesel_boat" and params.place == "mill":
        raise StoryError("A boat does not make sense in the mill yard.")
    if params.helper == "diesel_cart" and params.place == "harbor":
        raise StoryError("A cart is not the right helper for the harbor.")
    if params.helper == "diesel_wagon" and params.place == "harbor":
        raise StoryError("A wagon is not the right helper for the harbor.")


# ---------------------------------------------------------------------------
# Story dynamics
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    w = World(SETTINGS[params.place])
    helper_def = HELPERS[params.helper]
    speaker_def = CHARACTERS[params.speaker]

    helper = w.add(Entity(
        id=helper_def.id,
        kind="thing",
        type="machine",
        label=helper_def.label,
        phrase=helper_def.phrase,
        traits=["diesel", "hardworking"],
    ))
    speaker = w.add(Entity(
        id=speaker_def["name"],
        kind="character",
        type=speaker_def["type"],
        traits=speaker_def["traits"],
    ))
    return w

def intro(world: World) -> None:
    h = next(e for e in world.entities.values() if e.id in HELPERS)
    world.say(f"At {world.setting.place}, there was {h.label_word} that {h.pronoun('subject')} {HELPERS[h.id].sound} while doing useful work.")
    world.say(f"It came to {HELPERS[h.id].work}, and the village noticed its steady way.")

def misunderstanding(world: World, speaker: Entity) -> None:
    helper = next(e for e in world.entities.values() if e.id in HELPERS)
    speaker.memes["worry"] = speaker.memes.get("worry", 0.0) + 1
    speaker.memes["misunderstanding"] = speaker.memes.get("misunderstanding", 0.0) + 1
    helper.memes["noticed"] = helper.memes.get("noticed", 0.0) + 1
    world.say(f"{speaker.id} heard the deep {HELPERS[helper.id].sound} and frowned.")
    world.say(f'"Is it angry?" {speaker.pronoun("subject")} asked, and the others stepped back.')

def explain(world: World, speaker: Entity) -> None:
    helper = next(e for e in world.entities.values() if e.id in HELPERS)
    speaker.memes["understanding"] = speaker.memes.get("understanding", 0.0) + 1
    speaker.memes["worry"] = 0.0
    world.say(f"{speaker.id} walked closer and looked at the wheels, the load, and the path.")
    world.say(f'"No," {speaker.id} said softly, "it is not angry. It is only {HELPERS[helper.id].work}."')

def resolve(world: World, speaker: Entity) -> None:
    helper = next(e for e in world.entities.values() if e.id in HELPERS)
    helper.memes["calm"] = helper.memes.get("calm", 0.0) + 1
    speaker.memes["kindness"] = speaker.memes.get("kindness", 0.0) + 1
    world.say(f"The village listened, and the fear began to shrink.")
    world.say(f"Then {speaker.id} made a clear path, and {helper.label_word} could go on with its work.")
    world.say(f"By evening, the air was peaceful, and the little diesel helper still {HELPERS[helper.id].sound} in the distance.")

def tell(params: StoryParams) -> World:
    world = setup_world(params)
    helper = world.get(params.helper)
    speaker = world.get(CHARACTERS[params.speaker]["name"])

    intro(world)
    world.para()
    misunderstanding(world, speaker)
    world.para()
    explain(world, speaker)
    resolve(world, speaker)

    world.facts.update(
        helper=helper,
        speaker=speaker,
        helper_def=HELPERS[params.helper],
        place=params.place,
        misunderstood=True,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    h = f["helper_def"]
    s = f["speaker"]
    return [
        f'Write a short fable for children about a {h.label} and a misunderstanding at {f["place"]}.',
        f'Tell a gentle story where {s.id} first mistakes the sound of a diesel helper for trouble, then learns the truth.',
        f'Write a simple fable using the word "diesel" and ending with a misunderstanding being resolved kindly.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h = f["helper_def"]
    s = f["speaker"]
    return [
        QAItem(
            question=f"Where did the diesel helper arrive?",
            answer=f"It arrived at {f['place']}, where the villagers could hear its steady sound.",
        ),
        QAItem(
            question=f"Why did {s.id} think the machine was a problem at first?",
            answer=f"{s.id} heard the deep {h.sound} and misunderstood it, so {s.id} thought it might be angry or dangerous.",
        ),
        QAItem(
            question="How was the misunderstanding resolved?",
            answer=f"{s.id} looked more closely, explained that the helper was only {h.work}, and then the village made room for it to continue.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is diesel?",
            answer="Diesel is a kind of fuel used by some engines and machines to make them run.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but they have not understood it correctly.",
        ),
        QAItem(
            question="What does it mean to resolve something?",
            answer="To resolve something means to fix it or bring it to a peaceful end.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about diesel and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--speaker", choices=SPEAKERS)
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
    place = args.place or rng.choice(list(SETTINGS))
    helper = args.helper or rng.choice(list(HELPERS))
    speaker = args.speaker or rng.choice(SPEAKERS)
    params = StoryParams(place=place, helper=helper, speaker=speaker)
    reasonableness_gate(params)
    return params

def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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


# ---------------------------------------------------------------------------
# ASP / verification
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp
    python_ok = {(p.place, p.helper, p.speaker) for p in CURATED}
    model = asp.one_model(asp_program("#show safe_story/3."))
    asp_ok = set(asp.atoms(model, "safe_story"))
    if python_ok == asp_ok:
        print(f"OK: ASP parity matches curated reasoning ({len(asp_ok)} stories).")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("only in python:", sorted(python_ok - asp_ok))
    print("only in asp:", sorted(asp_ok - python_ok))
    return 1

def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_story/3."))
    return sorted(set(asp.atoms(model, "safe_story")))


CURATED = [
    StoryParams(place="meadow", helper="diesel_wagon", speaker="fox"),
    StoryParams(place="harbor", helper="diesel_boat", speaker="goat"),
    StoryParams(place="lane", helper="diesel_cart", speaker="mule"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        items = asp_list()
        print(f"{len(items)} safe stories:")
        for item in items:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
