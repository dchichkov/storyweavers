#!/usr/bin/env python3
"""
A tiny nursery-rhyme-style story world about an ambitious young helper,
an ancestor's old trough, a surprise, and a misunderstanding that clears up
into a gentle ending.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        if self.kind == "character" and self.role in {"child", "girl", "boy"}:
            return "they"
        return "it"


@dataclass
class Setting:
    place: str
    weather: str
    time_of_day: str
    sound: str


@dataclass
class StoryParams:
    place: str = "the nursery"
    name: str = "Milo"
    ancestor_name: str = "Granny Pip"
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
    "nursery": Setting(place="the nursery", weather="soft rain", time_of_day="morning", sound="a hush-hush hum"),
    "kitchen": Setting(place="the kitchen", weather="soft rain", time_of_day="morning", sound="a clink and a hum"),
    "garden": Setting(place="the garden", weather="bright rain", time_of_day="morning", sound="a drip and a hum"),
}

THINGS = {
    "trough": {
        "label": "old trough",
        "phrase": "an old wooden trough",
        "use": "to carry water",
        "is_ancestor_thing": True,
    },
    "spoon": {
        "label": "big spoon",
        "phrase": "a shiny spoon",
        "use": "to stir porridge",
        "is_ancestor_thing": False,
    },
}

ACTIONS = {
    "shine": {
        "verb": "make the trough shine",
        "attempt": "scrub and scrub",
        "surprise": "the trough was hiding a tiny frog",
        "misunderstanding": "the ancestor thought the frog was a loose splinter",
        "fix": "the child gently lifted the frog away",
    },
    "plant": {
        "verb": "plant beans in the trough",
        "attempt": "tip in soil and seeds",
        "surprise": "there was a little nest tucked in one corner",
        "misunderstanding": "the ancestor thought the child had spilled the seeds",
        "fix": "the child showed the nest and moved the beans to a tray",
    },
    "wash": {
        "verb": "wash the trough for tea",
        "attempt": "fetch warm water",
        "surprise": "a silver coin rang at the bottom",
        "misunderstanding": "the ancestor thought the child had lost the coin",
        "fix": "the child found the coin and handed it back with a bow",
    },
}


# ---------------------------------------------------------------------------
# Reasonableness gate + ASP twin
# ---------------------------------------------------------------------------

def valid_combo(place: str, action: str, thing: str) -> bool:
    if place not in SETTINGS or action not in ACTIONS or thing not in THINGS:
        return False
    if thing != "trough":
        return False
    return True


ASP_RULES = r"""
#show valid/3.
setting(nursery). setting(kitchen). setting(garden).
action(shine). action(plant). action(wash).
thing(trough).

valid(P,A,T) :- setting(P), action(A), thing(T), T = trough.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for t in THINGS:
        lines.append(asp.fact("thing", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return set(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = {(p, a, t) for p in SETTINGS for a in ACTIONS for t in THINGS if valid_combo(p, a, t)}
    cl = asp_valid()
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("  only in Python:", sorted(py - cl))
    print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def pick_name(rng: random.Random) -> str:
    return rng.choice(["Milo", "Tessa", "Nia", "Pip", "Arlo", "June"])


def rhyme_intro(hero: Entity, ancestor: Entity, setting: Setting) -> str:
    return (
        f"At {setting.place}, in morning light, {hero.label} woke with an ambitious sight. "
        f"{ancestor.label} kept an ancient trough, a wooden thing that had seen enough."
    )


def generate_story(world: World, hero: Entity, ancestor: Entity, trough: Entity, action_key: str) -> None:
    act = ACTIONS[action_key]
    seti = world.setting

    world.say(rhyme_intro(hero, ancestor, seti))
    world.para()
    world.say(
        f"{hero.label} said, “I want to {act['verb']},” in a sing-song voice both bright and sure. "
        f"{ancestor.label} smiled and nodded slow, yet gave a warning soft and low."
    )
    world.say(
        f"“Be careful now,” said {ancestor.label}, “for old things keep a careful tune; "
        f"the trough may hide a sleepy surprise beneath its rings of dust and moon.”"
    )
    world.para()
    world.say(
        f"So {hero.label} began to {act['attempt']}, with {seti.sound} in the air. "
        f"Then {act['surprise']}, and both of them stood frozen there."
    )
    world.say(
        f"{ancestor.label} cried, “Oh dear, oh no!” and made a quick misunderstanding. "
        f"“You’ve broken it! You’ve spilled the day!” but {hero.label} shook their head and grinned."
    )
    world.say(
        f"“Not broke,” said {hero.label}, “just snug and small. The surprise was living there all along.” "
        f"Then {act['fix']}, and the worry melted soft as a song."
    )
    world.para()
    world.say(
        f"By evening time, the trough still shone, and {ancestor.label} laughed a warm hooray. "
        f"{hero.label} felt ambitious still, but kinder now, and proud of the day."
    )

    world.facts.update(
        hero=hero,
        ancestor=ancestor,
        trough=trough,
        action_key=action_key,
        surprise=act["surprise"],
        misunderstanding=act["misunderstanding"],
        resolved=True,
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting=setting)
    hero = world.add(Entity(id="hero", kind="character", label=params.name, role="child", memes={"ambition": 1.0}))
    ancestor = world.add(Entity(id="ancestor", kind="character", label=params.ancestor_name, role="ancestor"))
    trough = world.add(Entity(id="trough", kind="thing", label="the old trough", role="container", meters={"age": 100.0}))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short nursery-rhyme story about an ambitious child, an ancestor, and an old trough.',
        f"Tell a gentle story where {f['hero'].label} wants to {ACTIONS[f['action_key']]['verb']} but a surprise changes the plan.",
        f"Write a rhyme about a misunderstanding around {f['trough'].label} that ends in kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    ancestor = f["ancestor"].label
    action = ACTIONS[f["action_key"]]["verb"]
    surprise = f["surprise"]
    misunderstanding = f["misunderstanding"]
    return [
        QAItem(
            question=f"Who was ambitious in the story?",
            answer=f"{hero} was ambitious, because {hero} wanted to {action}.",
        ),
        QAItem(
            question=f"What did {ancestor} have in the story?",
            answer=f"{ancestor} had an old trough that mattered to the story.",
        ),
        QAItem(
            question="What surprise appeared near the trough?",
            answer=f"The surprise was that {surprise}.",
        ),
        QAItem(
            question="What misunderstanding did the ancestor have?",
            answer=f"The misunderstanding was that {misunderstanding}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the surprise understood, the worry calmed, and the trough still safe and shining.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ancestor?",
            answer="An ancestor is a family member from an earlier generation, like a grandparent or great-grandparent.",
        ),
        QAItem(
            question="What does ambitious mean?",
            answer="Ambitious means wanting to do something big and working hard to try.",
        ),
        QAItem(
            question="What is a trough?",
            answer="A trough is a long open container, often used for holding water, feed, or other things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} label={e.label!r} role={e.role!r} meters={e.meters} memes={e.memes}")
    lines.append(f"setting: {world.setting}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed)
    action_key = rng.choice(list(ACTIONS))
    world = build_world(params)
    generate_story(world, world.get("hero"), world.get("ancestor"), world.get("trough"), action_key)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about an ancestor and a trough.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--ancestor-name")
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
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    name = args.name or pick_name(rng)
    ancestor_name = args.ancestor_name or rng.choice(["Granny Pip", "Grandpa Reed", "Aunt Pru", "Uncle Wren"])
    return StoryParams(place=place, name=name, ancestor_name=ancestor_name)


def generate_all() -> list[StorySample]:
    samples = []
    base = [
        StoryParams(place="nursery", name="Milo", ancestor_name="Granny Pip"),
        StoryParams(place="kitchen", name="Tessa", ancestor_name="Grandpa Reed"),
        StoryParams(place="garden", name="Nia", ancestor_name="Aunt Pru"),
    ]
    for i, p in enumerate(base):
        p.seed = 100 + i
        samples.append(generate(p))
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = sorted(asp_valid())
        print(f"{len(triples)} valid combos:")
        for t in triples:
            print(" ", t)
        return

    if args.all:
        samples = generate_all()
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
