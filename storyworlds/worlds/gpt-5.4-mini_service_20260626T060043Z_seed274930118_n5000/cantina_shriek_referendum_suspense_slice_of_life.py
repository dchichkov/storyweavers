#!/usr/bin/env python3
"""
storyworlds/worlds/cantina_shriek_referendum_suspense_slice_of_life.py
======================================================================

A small slice-of-life suspense world set in a neighborhood cantina where a
sudden shriek and a community referendum create a careful, grounded turn.

Seed tale:
---
In a little cantina on a warm evening, Mara counted cups while the kettle
hummed. The regulars chatted softly until a sharp shriek came from the side
room. Everyone froze. It turned out to be Nia, who had found a trapped kitten
behind a stack of crates. While Mara soothed the kitten and the room settled
down, the owner mentioned a referendum about whether the cantina should stay
open late for neighbors. The patrons worried, talked, and finally chose a calm
plan that kept the cantina welcoming without making the nights too noisy.
---

World model:
- Entities have physical meters and emotional memes.
- The shriek raises tension; the referendum measures whether the room feels
  safe enough for a late-night gathering.
- Suspense comes from not knowing if the cantina will close early or become a
  quieter community space.
- Slice-of-life details are driven by state: cups, lamps, stools, voices,
  nervousness, trust, and the kitten's calming effect.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother", "host"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def possessive_name(self) -> str:
        return self.label


@dataclass
class Place:
    name: str = "the cantina"
    closed_late: bool = False
    permits_late_referendum: bool = True


@dataclass
class StoryParams:
    place: str = "cantina"
    hero: str = "Mara"
    host: str = "Elena"
    visitor: str = "Nia"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Simulation rules
# ---------------------------------------------------------------------------

def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    out: list[str] = []
    while changed:
        changed = False
        for sent in _rules(world):
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)


def _rules(world: World) -> list[list[str]]:
    out: list[list[str]] = []

    # A shriek spikes the room's tension.
    if world.facts.get("shrieked") and ("tension",) not in world.fired:
        world.fired.add(("tension",))
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["tension"] = ent.memes.get("tension", 0.0) + 1
        out.append(["The shriek made every conversation stop at once."])

    # The kitten calms the room if it is found and held gently.
    if world.facts.get("kitten_safe") and ("calm",) not in world.fired:
        world.fired.add(("calm",))
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["tension"] = max(0.0, ent.memes.get("tension", 0.0) - 1.0)
                ent.memes["relief"] = ent.memes.get("relief", 0.0) + 1
        out.append(["Once the kitten was safe, the room began to breathe again."])

    # A referendum resolves if enough people trust the host and tension has eased.
    if world.facts.get("vote_called") and world.facts.get("vote_ready") and ("vote",) not in world.fired:
        world.fired.add(("vote",))
        outcome = "late_open" if world.facts.get("vote_yes", 0) >= world.facts.get("vote_no", 0) else "early_close"
        world.facts["referendum_result"] = outcome
        out.append([f"The referendum settled on {outcome.replace('_', ' ')}."])
    return out


# ---------------------------------------------------------------------------
# Domain helpers
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, host: Entity) -> None:
    world.say(
        f"{hero.id} worked at {world.place.name}, counting cups and wiping the counter "
        f"while {host.id} kept the kettle humming."
    )


def everyday_scene(world: World, hero: Entity, visitor: Entity) -> None:
    world.say(
        f"The afternoon was ordinary in the nicest way: stools scraped softly, "
        f"spoons clinked, and {visitor.id} sat near the window with a warm drink."
    )


def trigger_shriek(world: World, visitor: Entity) -> None:
    world.facts["shrieked"] = True
    visitor.memes["fear"] = visitor.memes.get("fear", 0.0) + 1
    world.say(
        f"Then a sharp shriek flashed from the side room, and {visitor.id} jerked up so fast "
        f"that their cup nearly tipped."
    )


def discover_kitten(world: World, hero: Entity, visitor: Entity) -> None:
    kitten = world.add(Entity(id="kitten", kind="animal", type="kitten", label="kitten"))
    kitten.meters["safety"] = 0.0
    world.say(
        f"{visitor.id} peeked behind the crates and found a small kitten tangled in a ribbon, "
        f"more startled than hurt."
    )
    world.say(
        f"{hero.id} crouched down, held out a palm, and let the kitten climb into the warmth of {hero.pronoun('possessive')} hands."
    )
    world.facts["kitten_safe"] = True
    kitten.meters["safety"] = 1.0
    hero.memes["care"] = hero.memes.get("care", 0.0) + 1
    visitor.memes["relief"] = visitor.memes.get("relief", 0.0) + 1


def call_referendum(world: World, host: Entity, hero: Entity) -> None:
    if not world.place.permits_late_referendum:
        raise StoryError("This cantina does not allow a referendum in the story setup.")
    world.facts["vote_called"] = True
    world.say(
        f"With the kitten safe, {host.id} set out a neat stack of paper slips and called for a referendum "
        f"about whether the cantina should stay open later for neighbors."
    )
    world.say(
        f"{hero.id} listened closely, because the choice would change the quiet of the room after sunset."
    )


def vote(world: World, hero: Entity, host: Entity, visitor: Entity) -> None:
    tension = sum(ent.memes.get("tension", 0.0) for ent in world.entities.values() if ent.kind == "character")
    world.facts["vote_ready"] = True
    # Calm room favors yes; nervous room favors no.
    world.facts["vote_yes"] = 2 if tension < 2.0 else 1
    world.facts["vote_no"] = 1 if tension < 2.0 else 2
    if world.facts["vote_yes"] >= world.facts["vote_no"]:
        world.say(
            f"The neighbors agreed to keep the cantina open later, but with softer music, earlier last call, "
            f"and one corner left quiet for anyone who needed a calm seat."
        )
    else:
        world.say(
            f"The neighbors decided not to stay open too late, though they promised to host a calm community hour next week."
        )


def closing_image(world: World, hero: Entity, visitor: Entity, host: Entity) -> None:
    result = world.facts.get("referendum_result", "late_open")
    if result == "late_open":
        world.say(
            f"By the end of the night, the lamp over the counter glowed warm, the kitten slept safe in a basket, "
            f"and the cantina felt a little more like a shared living room."
        )
    else:
        world.say(
            f"By closing time, the kitten was safe, the cups were stacked, and the cantina had settled into a "
            f"quiet promise to try again another evening."
        )


def tell_story(params: StoryParams) -> World:
    world = World(Place(name="the cantina"))
    hero = world.add(Entity(id=params.hero, kind="character", type="woman", label=params.hero))
    host = world.add(Entity(id=params.host, kind="character", type="woman", label=params.host))
    visitor = world.add(Entity(id=params.visitor, kind="character", type="girl", label=params.visitor))

    hero.memes["calm"] = 1.0
    host.memes["patience"] = 1.0
    visitor.memes["curiosity"] = 1.0

    introduce(world, hero, host)
    world.para()
    everyday_scene(world, hero, visitor)
    trigger_shriek(world, visitor)
    propagate(world)

    world.para()
    discover_kitten(world, hero, visitor)
    propagate(world)

    world.para()
    call_referendum(world, host, hero)
    vote(world, hero, host, visitor)
    propagate(world)

    world.para()
    closing_image(world, hero, visitor, host)

    world.facts.update(hero=hero, host=host, visitor=visitor)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

NAMES = ["Mara", "Elena", "Nia", "Luz", "Rosa", "Iris", "Tessa", "June"]
VISITORS = ["Nia", "Sofi", "Pia", "Lina", "Mina", "Ruby"]
HOSTS = ["Elena", "Ada", "Clara", "Dora", "Selma"]


# ---------------------------------------------------------------------------
# Story generation + QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short slice-of-life suspense story set in a cantina where a sudden shriek changes the mood.',
        f"Tell a gentle story in {world.place.name} where {f['hero'].id} hears a shriek, helps safely, and then joins a referendum.",
        "Write a small, concrete story about a neighborhood cantina, a startled room, and a calm vote about staying open late.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    host: Entity = f["host"]
    visitor: Entity = f["visitor"]
    result = f.get("referendum_result", "late_open")
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in the cantina, where cups, stools, and a warm kettle make an ordinary evening feel close and familiar.",
        ),
        QAItem(
            question=f"What caused everyone to freeze at first?",
            answer=f"A sharp shriek came from the side room, and the whole cantina went quiet before anyone knew what was wrong.",
        ),
        QAItem(
            question=f"Who found the problem behind the crates?",
            answer=f"{visitor.id} found the frightened kitten behind the crates, and {hero.id} helped make it safe.",
        ),
        QAItem(
            question=f"What was the referendum about?",
            answer=f"{host.id} called a referendum about whether the cantina should stay open later for neighbors.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                "The kitten was safe, the room was calm again, and "
                + (
                    "the neighbors chose to keep the cantina open later with quieter rules."
                    if result == "late_open"
                    else "the neighbors chose to close early, with a promise to try another calm gathering later."
                )
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cantina?",
            answer="A cantina is a small place where people can sit, eat, drink, and talk together.",
        ),
        QAItem(
            question="What is a shriek?",
            answer="A shriek is a sudden, sharp cry that usually sounds like someone is startled or in trouble.",
        ),
        QAItem(
            question="What is a referendum?",
            answer="A referendum is a vote where a group of people decide what choice should be made.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% place(P)., person(X)., shriek_event., referendum_topic(late_open)., kitten_safe.

tension_rises :- shriek_event.
calm_returns :- kitten_safe.

vote_open_late :- referendum_topic(late_open), calm_returns.
vote_close_early :- referendum_topic(late_open), tension_rises, not calm_returns.

chosen(late_open) :- vote_open_late.
chosen(early_close) :- vote_close_early.

#show chosen/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "cantina"),
            asp.fact("person", "mara"),
            asp.fact("person", "elena"),
            asp.fact("person", "nia"),
            asp.fact("shriek_event"),
            asp.fact("referendum_topic", "late_open"),
            asp.fact("kitten_safe"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_outcome() -> list[tuple]:
    import asp
    import asp as aspmod  # lazy, but explicit
    _ = aspmod
    model = asp.one_model(asp_program("#show chosen/1."))
    return sorted(set(asp.atoms(model, "chosen")))


def asp_verify() -> int:
    py = "late_open"
    asp_choice = asp_outcome()
    expected = [("late_open",)]
    if asp_choice == expected:
        print("OK: ASP and Python agree on the referendum outcome.")
        return 0
    print(f"MISMATCH: python={py} asp={asp_choice}")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small cantina suspense storyworld with a referendum.")
    ap.add_argument("--place", choices=["cantina"])
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--host", choices=HOSTS)
    ap.add_argument("--visitor", choices=VISITORS)
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
    return StoryParams(
        place=args.place or "cantina",
        hero=args.hero or rng.choice(NAMES),
        host=args.host or rng.choice(HOSTS),
        visitor=args.visitor or rng.choice(VISITORS),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


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
        print(asp_program("#show chosen/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_outcome())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(place="cantina", hero="Mara", host="Elena", visitor="Nia", seed=base_seed)
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
