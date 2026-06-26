#!/usr/bin/env python3
"""
Standalone storyworld: a small heartwarming, humorous mishap about pain,
alcohol, and doody.

A child gets a sore tummy and an embarrassing doody accident. A grown-up tries
a sensible cleaning-and-comfort plan, but the child mishears "alcohol" and
imagines something dramatic. The story turns on the correction: the alcohol is
just for cleaning, the pain is from tummy cramps, and the loving fix is warm
care, clean clothes, and a shared laugh.

This file implements:
- a tiny world model with physical meters and emotional memes
- constraint-checked generation
- story, QA, trace, JSON, and ASP twin support
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bathroom"


@dataclass
class Event:
    id: str
    verb: str
    symptom: str
    trigger: str
    cleanup: str
    mess: str
    risk_zone: str = "clothes"


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    purpose: str
    safe: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        chunks: list[str] = []
        cur: list[str] = []
        for line in self.lines:
            if line == "":
                if cur:
                    chunks.append(" ".join(cur))
                    cur = []
            else:
                cur.append(line)
        if cur:
            chunks.append(" ".join(cur))
        return "\n\n".join(chunks)


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    event: str
    comfort: str
    seed: Optional[int] = None


SETTING = Setting(place="the bathroom")

EVENTS = {
    "tummy": Event(
        id="tummy",
        verb="hurts",
        symptom="tummy pain",
        trigger="ate too much candy",
        cleanup="needed a careful clean-up",
        mess="doody",
        risk_zone="clothes",
    ),
    "bathroom": Event(
        id="bathroom",
        verb="hurts",
        symptom="a sore belly",
        trigger="felt a cramp after dinner",
        cleanup="needed a gentle cleanup",
        mess="doody",
        risk_zone="clothes",
    ),
}

COMFORTS = {
    "wipe": Comfort(
        id="wipe",
        label="warm wipes",
        phrase="warm wipes",
        purpose="clean up the doody",
    ),
    "bath": Comfort(
        id="bath",
        label="a quick bath",
        phrase="a small bath",
        purpose="get clean and calm down",
    ),
    "blanket": Comfort(
        id="blanket",
        label="a soft blanket",
        phrase="a soft blanket",
        purpose="feel cozy after the scare",
    ),
}

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Ava", "Zoe"],
    "boy": ["Theo", "Ben", "Finn", "Leo", "Sam"],
}
PARENTS = ["mother", "father"]
GENDERS = ["girl", "boy"]


class NarrativeWorld(World):
    pass


def _story_entity_name(hero: Entity) -> str:
    return hero.id


def tell(params: StoryParams) -> World:
    world = NarrativeWorld(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"pain": 0.0}, memes={"worry": 0.0, "humor": 0.0, "relief": 0.0, "love": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}", meters={"patience": 0.0}, memes={"care": 1.0, "humor": 0.0, "love": 1.0}))
    event = EVENTS[params.event]
    comfort = COMFORTS[params.comfort]
    cloth = world.add(Entity(id="clothes", type="clothes", label="pajamas", phrase="striped pajamas", owner=hero.id, caretaker=parent.id, worn_by=hero.id, meters={"dirty": 0.0, "smelly": 0.0}))

    world.facts.update(hero=hero, parent=parent, event=event, comfort=comfort, cloth=cloth)

    world.say(f"{hero.id} was a little {params.gender} who loved bedtime stories and silly giggles.")
    world.say(f"One evening, {hero.id} said {hero.pronoun('possessive')} tummy {event.verb} and rubbed {hero.pronoun('possessive')} belly with a tiny frown.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {params.parent} noticed the smell and the mess and said, \"Looks like {event.mess}!\"")
    world.say(f"{hero.id} blinked. \"Do I need alcohol?\" {hero.id} asked, sounding very serious.")
    world.say(f"{params.parent.capitalize()} smiled and said, \"Just the kind for cleaning, not for drinking. We use it very carefully, then we use warm wipes.\"")
    hero.memes["worry"] += 1
    hero.memes["humor"] += 1
    cloth.meters["dirty"] += 1
    hero.meters["pain"] += 1

    world.para()
    world.say(f"{params.parent.capitalize()} brought {comfort.phrase} and helped {hero.id} sit by {world.setting.place}.")
    world.say(f"First they cleaned the doody, because {event.cleanup}.")
    world.say(f"Then they washed {hero.pronoun('object')} hands, opened the window, and made the room smell fresh again.")
    hero.meters["pain"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["love"] += 1
    parent.memes["humor"] += 1
    cloth.meters["dirty"] = 0.0

    world.para()
    world.say(f"{hero.id} laughed at the word alcohol, because it had sounded like a giant spooky monster, but it was only a bottle for cleaning.")
    world.say(f"Then {hero.id} snuggled under {comfort.phrase} and felt better, while {params.parent} tucked {hero.pronoun('object')} in with a grin.")
    world.say(f"By the end, {hero.id} was cozy, clean, and smiling, and the little bathroom felt warm with relief.")

    return world


def valid_combos() -> list[tuple[str, str]]:
    return [("the bathroom", e.id, c.id) for e in EVENTS.values() for c in COMFORTS.values() if c.safe]


@dataclass
class ASPFacts:
    pass


ASP_RULES = r"""
event(E) :- event_id(E).
comfort(C) :- comfort_id(C).

valid(E,C) :- event(E), comfort(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for eid in EVENTS:
        lines.append(asp.fact("event_id", eid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort_id", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((e, c) for _, e, c in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    event = f["event"]
    comfort = f["comfort"]
    return [
        f'Write a heartwarming funny story for little kids about {hero.id}, a surprising {event.mess}, and {comfort.label}.',
        f"Tell a gentle story where {hero.id} worries about pain, hears the word alcohol, and gets comfort from {parent.label}.",
        f"Write a short story that includes doody, alcohol, and a cozy ending with {hero.id} feeling better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, event, comfort = f["hero"], f["parent"], f["event"], f["comfort"]
    return [
        QAItem(
            question=f"What was wrong with {hero.id} at the start of the story?",
            answer=f"{hero.id} had tummy pain and then a doody mess, so {parent.label} helped right away.",
        ),
        QAItem(
            question=f"Why did {hero.id} ask about alcohol?",
            answer=f"{hero.id} misheard the clean-up talk and thought alcohol might be for the tummy pain, but it was only for cleaning carefully.",
        ),
        QAItem(
            question=f"How did {parent.label} help {hero.id} feel better?",
            answer=f"{parent.label.capitalize()} cleaned the doody, used warm wipes, and brought {comfort.phrase} so {hero.id} could relax and smile again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is alcohol used for in a grown-up cleaning bottle?",
            answer="Alcohol can help clean some surfaces or skin when used carefully by a grown-up, but it is not something children should drink.",
        ),
        QAItem(
            question="What is doody?",
            answer="Doody is a kid-friendly word for poop.",
        ),
        QAItem(
            question="What does pain mean?",
            answer="Pain is a hurt feeling in the body, like a sore tummy or a bumped knee.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming humorous story world about pain, alcohol, and doody.")
    ap.add_argument("--name", choices=sorted({n for ns in NAMES.values() for n in ns}))
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--event", choices=sorted(EVENTS))
    ap.add_argument("--comfort", choices=sorted(COMFORTS))
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
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENTS)
    event = args.event or rng.choice(sorted(EVENTS))
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    return StoryParams(name=name, gender=gender, parent=parent, event=event, comfort=comfort)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible event/comfort combos:\n")
        for e, c in combos:
            print(f"  {e:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for _, e, c in valid_combos():
            params = StoryParams(
                name="Mia",
                gender="girl",
                parent="mother",
                event=e,
                comfort=c,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
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
