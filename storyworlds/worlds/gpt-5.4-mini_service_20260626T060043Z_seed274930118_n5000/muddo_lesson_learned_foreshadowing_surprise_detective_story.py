#!/usr/bin/env python3
"""
A small detective-story world about a missing clue, a careful lesson, a
foreshadowed trail, and a surprise reveal.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    name: str = ""
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    weather: str
    has_lamp: bool = False
    has_mud: bool = False
    has_window: bool = False


@dataclass
class Clue:
    id: str
    label: str
    place_hint: str
    shine: str
    mess: str
    significance: str
    hint_before: str


@dataclass
class Suspect:
    id: str
    label: str
    role: str
    oddity: str
    innocent: bool = True


@dataclass
class StoryParams:
    place: str
    clue: str
    suspect: str
    hero: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "name": v.name, "label": v.label,
            "traits": list(v.traits), "owner": v.owner, "location": v.location,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "alley": Setting(place="the old alley", weather="foggy", has_lamp=True, has_mud=True),
    "museum": Setting(place="the quiet museum", weather="rainy", has_lamp=True, has_window=True),
    "dock": Setting(place="the moonlit dock", weather="windy", has_lamp=False, has_mud=True),
}

CLUES = {
    "muddo": Clue(
        id="muddo",
        label="muddo",
        place_hint="near wet ground",
        shine="a little shine",
        mess="mud",
        significance="the hidden path",
        hint_before="The detective noticed a muddy print before anything else.",
    ),
    "button": Clue(
        id="button",
        label="a brass button",
        place_hint="by a coat",
        shine="a dull gleam",
        mess="dust",
        significance="the missing coat",
        hint_before="Something shiny caught the eye under the bench.",
    ),
    "note": Clue(
        id="note",
        label="a folded note",
        place_hint="under a lamp",
        shine="a pale edge",
        mess="ink",
        significance="the secret message",
        hint_before="A corner of paper peeked from the floorboards.",
    ),
}

SUSPECTS = {
    "baker": Suspect(id="baker", label="the baker", role="baker", oddity="flour on their sleeves", innocent=True),
    "janitor": Suspect(id="janitor", label="the janitor", role="janitor", oddity="a ring of keys", innocent=True),
    "artist": Suspect(id="artist", label="the artist", role="artist", oddity="paint on their cuff", innocent=True),
}

HERO_NAMES = ["Nia", "Milo", "June", "Owen", "Tess", "Arlo"]
SIDEKICKS = ["Pip", "Bea", "Luca", "Mina", "Zed", "Rae"]
TRAITS = ["careful", "brave", "curious", "patient", "sharp"]


ASP_RULES = r"""
clue(C) :- clue_id(C).
foreshadow(C) :- clue(C), hint_before(C,H), note(H).
surprise(C) :- clue(C), reveal(C,R), unexpected(R).
lesson_learned(H) :- detective(H), solves(H), after(H, foreshadowing).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_lamp:
            lines.append(asp.fact("has_lamp", sid))
        if s.has_mud:
            lines.append(asp.fact("has_mud", sid))
        if s.has_window:
            lines.append(asp.fact("has_window", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_id", cid))
        lines.append(asp.fact("hint_before", cid, c.hint_before))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect_id", sid))
        lines.append(asp.fact("role", sid, s.role))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show clue/1."))
    asp_clues = set(asp.atoms(model, "clue"))
    py_clues = {(cid,) for cid in CLUES}
    if asp_clues == py_clues:
        print(f"OK: clingo gate matches Python registries ({len(py_clues)} clues).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(asp_clues - py_clues))
    print("only in Python:", sorted(py_clues - asp_clues))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective-story world with a lesson, foreshadowing, and a surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    clue = args.clue or rng.choice(list(CLUES))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICKS if n != hero])
    return StoryParams(place=place, clue=clue, suspect=suspect, hero=hero, sidekick=sidekick)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="detective", name=params.hero, label=params.hero, traits=["curious", "careful"]))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="child", name=params.sidekick, label=params.sidekick, traits=["loyal"]))
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]
    world.add(Entity(id="clue", type="thing", label=clue.label, location=clue.place_hint, meters={"mess": 1.0}, memes={"importance": 1.0}))
    world.add(Entity(id="suspect", kind="character", type="person", label=suspect.label, location=setting.place, memes={"nervous": 0.0}))
    world.facts.update(hero=hero, sidekick=sidekick, clue=clue, suspect=suspect, setting=setting)
    return world


def narrate(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    clue: Clue = f["clue"]
    suspect: Suspect = f["suspect"]
    setting: Setting = f["setting"]

    world.say(f"At {setting.place}, {hero.name} and {sidekick.name} worked like a tiny detective team.")
    world.say(f"The case began with {clue.hint_before} {clue.label} had {clue.shine} and seemed ordinary, but it pointed toward {clue.significance}.")
    world.para()
    world.say(f"{hero.name} followed the muddy trail through {setting.place} while {sidekick.name} watched the corners.")
    world.say(f"That was the foreshadowing: each print matched {clue.place_hint}, and the trail kept leading back to the same doorway.")
    world.para()
    world.say(f"They found {suspect.label}, who looked harmless except for {suspect.oddity}.")
    world.say(f"Then came the surprise: the muddy clue did not belong to {suspect.role} at all; it had been made by a crate that tipped near the back hall and rolled the trail into place.")
    world.para()
    world.say(f"{hero.name} smiled and said the lesson learned was simple: a detective should look twice before blaming anyone.")
    world.say(f"{sidekick.name} nodded, and together they cleaned the path, leaving {clue.label} safely in an evidence bag.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue"]
    return [
        f'Write a short detective story for a young child featuring {clue.label} and a careful clue trail.',
        f"Tell a story where a detective notices {clue.label}, gets a surprise, and learns not to jump to conclusions.",
        f'Write a simple mystery story that includes the word "മുഡോ" sound-alike and ends with a clear lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    clue: Clue = f["clue"]
    suspect: Suspect = f["suspect"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who solved the mystery at {setting.place}?",
            answer=f"{hero.name} solved it with help from {sidekick.name}. They followed the clue trail and figured out what really happened.",
        ),
        QAItem(
            question=f"What was special about {clue.label}?",
            answer=f"{clue.label} looked small, but it gave the first important hint. It was muddy, and it pointed to the hidden path in the case.",
        ),
        QAItem(
            question=f"Why was the ending a surprise?",
            answer=f"The surprise was that {suspect.label} was not guilty. The muddy clue came from a tipped crate, so the detective had to think again.",
        ),
        QAItem(
            question=f"What lesson did {hero.name} learn?",
            answer=f"{hero.name} learned to look twice before blaming someone. Careful thinking matters in a mystery.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to figure out what really happened.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps solve a mystery.",
        ),
        QAItem(
            question="What does foreshadowing mean?",
            answer="Foreshadowing is when a story gives a small hint about something important that will happen later.",
        ),
        QAItem(
            question="What is a lesson learned in a story?",
            answer="A lesson learned is the important idea a character understands by the end, like being careful or kind.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
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


CURATED = [
    StoryParams(place="alley", clue="muddo", suspect="baker", hero="Nia", sidekick="Pip"),
    StoryParams(place="museum", clue="note", suspect="janitor", hero="Milo", sidekick="Bea"),
    StoryParams(place="dock", clue="button", suspect="artist", hero="June", sidekick="Luca"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show clue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show clue/1."))
        print(sorted(set(asp.atoms(model, "clue"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} in {p.place} ({p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
