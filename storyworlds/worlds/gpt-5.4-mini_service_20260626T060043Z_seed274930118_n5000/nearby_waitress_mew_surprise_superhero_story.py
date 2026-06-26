#!/usr/bin/env python3
"""
A small superhero-style storyworld about a nearby waitress, a mew, and a surprise.

Premise:
- A child hero loves helping people in a little city block.
- A nearby waitress carries a special tray.
- A tiny mew leads to a surprise that needs brave, kind action.
- The hero uses a simple gadget and a quick rescue to turn alarm into delight.

This world keeps the story close to a classic superhero shape:
setup -> problem -> decisive action -> smiling ending.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    nearby_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "waitress"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    name: str
    gender: str
    sidekick: str
    place: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "corner": "the corner cafe",
    "street": "the busy street",
    "plaza": "the sunny plaza",
}

HERO_NAMES = ["Nova", "Milo", "Riley", "Jules", "Pip", "Aria", "Theo", "Sunny"]
SIDEKICKS = ["spark glove", "pocket cape", "bubble visor", "flash boots"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str) -> bool:
    return place in PLACES


def explain_rejection(place: str) -> str:
    return f"(No story: the setting '{place}' is not part of this small superhero block.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H).
place(P) :- cafe(P).
nearby_waitress(W) :- waitress(W).
mew(M) :- cat(M).
surprise(S) :- event(S).

valid_story(H, P) :- hero(H), place(P), nearby_waitress(_), mew(_), surprise(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for h in HERO_NAMES:
        lines.append(asp.fact("hero", h))
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("cafe", pid))
    lines.append(asp.fact("waitress", "waitress"))
    lines.append(asp.fact("cat", "mew"))
    lines.append(asp.fact("event", "surprise"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    py = {(h, p) for h in HERO_NAMES for p in PLACES}
    clingo = set(asp_valid_stories())
    if clingo == py:
        print(f"OK: ASP matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(clingo - py))
    print("only in Python:", sorted(py - clingo))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place_label = PLACES[params.place]
    w = World(place=place_label)

    hero = w.add(Entity(
        id=params.name, kind="character", type="girl" if params.gender == "girl" else "boy",
        label=params.name, traits=["brave", "kind", "quick"]
    ))
    waitress = w.add(Entity(
        id="waitress", kind="character", type="waitress", label="the waitress",
        traits=["busy", "friendly"]
    ))
    cat = w.add(Entity(
        id="mew", kind="character", type="cat", label="a tiny cat",
        traits=["small", "alarmed"]
    ))
    gadget = w.add(Entity(
        id="sidekick", kind="thing", type="gadget", label=params.sidekick,
        owner=hero.id
    ))
    tray = w.add(Entity(
        id="tray", kind="thing", type="tray", label="a tray of hot cocoa",
        caretaker=waitress.id
    ))
    shiny_box = w.add(Entity(
        id="box", kind="thing", type="box", label="a small wrapped box",
        nearby_to=waitress.id
    ))

    hero.memes["hope"] = 1
    hero.memes["heroic"] = 1

    w.say(
        f"{hero.id} was a small superhero who loved helping people at {w.place}."
    )
    w.say(
        f"{hero.pronoun().capitalize()} wore {params.sidekick} and kept a watchful eye on everyone nearby."
    )
    w.say(
        f"At {w.place}, a busy waitress balanced {tray.label} near {shiny_box.label}."
    )

    w.para()
    w.say(
        f"Then {cat.label} gave a tiny mew from under a table."
    )
    cat.memes["fear"] = 1
    waitress.memes["surprise"] = 1
    w.say(
        f"The waitress blinked in surprise and looked down, because the sound came from nearby."
    )

    w.para()
    hero.memes["alert"] = 1
    hero.memes["care"] = 1
    w.say(
        f"{hero.id} rushed over with a calm smile and lifted the cloth beside the table."
    )
    w.say(
        f"There was the little cat, stuck behind the box and too shy to climb out."
    )
    cat.memes["stuck"] = 1

    w.para()
    cat.memes["safe"] = 1
    cat.memes["fear"] = 0
    waitress.memes["surprise"] = 0
    waitress.memes["joy"] = 1
    hero.memes["pride"] = 1
    w.say(
        f"{hero.id} slid the box aside, and the cat hopped free with another soft mew."
    )
    w.say(
        f"The waitress laughed in relief and set down the tray before anything could spill."
    )
    w.say(
        f"Inside the wrapped box was a thank-you note for the waiter next door, and the surprise was for the whole cafe."
    )

    w.para()
    w.say(
        f"By the end, {hero.id} was smiling, the waitress was grateful, and the tiny cat was curled up safely beside {hero.id}'s boots."
    )

    w.facts.update(
        hero=hero,
        waitress=waitress,
        cat=cat,
        gadget=gadget,
        tray=tray,
        box=shiny_box,
        params=params,
        place_label=place_label,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a short superhero story for children that includes a nearby waitress, a mew, and a surprise.",
        f"Tell a gentle rescue story where {hero.id} notices a mew near a waitress at {world.place}.",
        f"Write a simple story about a small hero who helps at {world.place} and discovers a surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    waitress = f["waitress"]
    cat = f["cat"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a small superhero who liked helping people."
        ),
        QAItem(
            question=f"What did the nearby waitress do when she heard the mew?",
            answer=f"The nearby waitress looked down in surprise because the sound came from near the table."
        ),
        QAItem(
            question=f"What happened after {hero.id} moved the box?",
            answer=f"The tiny cat hopped free with another soft mew, and the waitress could relax."
        ),
        QAItem(
            question=f"What was the surprise in the cafe?",
            answer=f"The surprise was a thank-you note inside a wrapped box, meant for the people at the cafe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a waitress?",
            answer="A waitress is a person who brings food and drinks to people in a cafe or restaurant."
        ),
        QAItem(
            question="What does mew mean?",
            answer="Mew is a soft sound a cat makes."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that can make people feel shocked, happy, or excited."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.nearby_to:
            bits.append(f"nearby_to={e.nearby_to}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero-style storyworld with a nearby waitress, a mew, and a surprise.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    place = args.place or rng.choice(list(PLACES))
    if not valid_combo(place):
        raise StoryError(explain_rejection(place))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(name=name, gender=gender, sidekick=sidekick, place=place)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(name="Nova", gender="girl", sidekick="flash boots", place="corner"),
    StoryParams(name="Milo", gender="boy", sidekick="bubble visor", place="plaza"),
    StoryParams(name="Riley", gender="girl", sidekick="pocket cape", place="street"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for h, p in asp_valid_stories():
            print(h, p)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
