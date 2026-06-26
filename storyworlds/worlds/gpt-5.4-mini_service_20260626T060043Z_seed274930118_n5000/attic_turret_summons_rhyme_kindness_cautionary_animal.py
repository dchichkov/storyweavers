#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/attic_turret_summons_rhyme_kindness_cautionary_animal.py
======================================================================================================

A small animal-story world about an attic, a turret, and a summons that can be
answered with rhyme, kindness, or caution.

Premise:
- A royal owl lives in a turret above an old house.
- A little mouse lives in the attic below.
- The owl sends a summons by rhyme, asking the mouse to bring back a lost key.
- The mouse wants to help, but the attic stairs are cramped, the turret is high,
  and the path is risky.
- Kindness and caution turn the tale from worry into a safe rescue.

The simulated world tracks:
- physical meters like trust, height, fatigue, and loss
- emotional memes like worry, courage, gratitude, and kindness

The story is not a frozen paragraph: the prose is driven by the state changes
that happen when the summons arrives, the mouse hesitates, and the two animals
choose a careful plan.
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

ATTIC_NOISE = ("soft rustle", "tiny creak", "dusty whisper")
TURRET_SOUND = ("windy hum", "stone sigh", "far bell")


@dataclass
class Animal:
    id: str
    kind: str = "character"
    species: str = "animal"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    height: float
    cozy: bool = False


@dataclass
class StoryParams:
    mouse_name: str
    owl_name: str
    attic: str
    turret: str
    summons_style: str
    virtue: str
    caution_level: str
    seed: Optional[int] = None


class World:
    def __init__(self, attic: Place, turret: Place) -> None:
        self.attic = attic
        self.turret = turret
        self.entities: dict[str, Animal] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, ent: Animal) -> Animal:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Animal:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with attic, turret, and summons.")
    ap.add_argument("--mouse-name", choices=["Pip", "Nib", "Moss", "Tavi", "Rue"])
    ap.add_argument("--owl-name", choices=["Hoot", "Morrow", "Sable", "Orin", "Wren"])
    ap.add_argument("--attic", choices=list(ATTICS))
    ap.add_argument("--turret", choices=list(TURRETS))
    ap.add_argument("--summons-style", choices=list(SUMMONS_STYLES))
    ap.add_argument("--virtue", choices=["Rhyme", "Kindness", "Cautionary"])
    ap.add_argument("--caution-level", choices=["gentle", "careful", "very careful"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


ATTICS = {
    "lantern_attic": Place("lantern_attic", "the lantern attic", height=1.0, cozy=True),
    "dust_attic": Place("dust_attic", "the dust attic", height=1.2, cozy=False),
    "beam_attic": Place("beam_attic", "the beam attic", height=1.1, cozy=True),
}

TURRETS = {
    "north_turret": Place("north_turret", "the north turret", height=4.0, cozy=False),
    "west_turret": Place("west_turret", "the west turret", height=3.5, cozy=False),
    "green_turret": Place("green_turret", "the green turret", height=3.8, cozy=True),
}

SUMMONS_STYLES = {
    "rhyme": "a rhyme-summons",
    "bell": "a bell summons",
    "scroll": "a scroll summons",
    "feather": "a feather summons",
}


def make_world(params: StoryParams) -> World:
    world = World(ATTICS[params.attic], TURRETS[params.turret])
    mouse = world.add(Animal(id=params.mouse_name, label="mouse"))
    owl = world.add(Animal(id=params.owl_name, label="owl"))

    mouse.meters.update(trust=1.0, worry=0.0, courage=0.0, fatigue=0.0, climb=0.0, loss=0.0)
    mouse.memes.update(kindness=0.0, caution=0.0, gratitude=0.0, rhyme=0.0)
    owl.meters.update(trust=1.0, worry=0.0, height=world.turret.height, loss=1.0, fatigue=0.0)
    owl.memes.update(kindness=0.0, caution=0.0, gratitude=0.0, rhyme=0.0)

    world.facts.update(mouse=mouse, owl=owl, params=params)
    return world


def narrate_setup(world: World) -> None:
    m = world.facts["mouse"]
    o = world.facts["owl"]
    params: StoryParams = world.facts["params"]
    world.say(
        f"In {world.attic.label}, {m.id} lived under the rafters and listened to the "
        f"{random.choice(ATTIC_NOISE)} of the old boards."
    )
    world.say(
        f"High above in {world.turret.label}, {o.id} watched the lanes and the moon, "
        f"where the {random.choice(TURRET_SOUND)} could be heard on windy nights."
    )
    world.say(
        f"One day, {o.id} sent {m.id} {SUMMONS_STYLES[params.summons_style]}: "
        f'"Dear little helper, please come bring back my lost key."'
    )
    m.memes["rhyme"] += 1.0 if params.virtue == "Rhyme" else 0.0
    o.memes["kindness"] += 1.0 if params.virtue == "Kindness" else 0.0
    o.memes["caution"] += 1.0 if params.virtue == "Cautionary" else 0.0
    world.facts["asked_for"] = "lost key"


def caution_check(world: World) -> bool:
    m = world.facts["mouse"]
    o = world.facts["owl"]
    if o.meters["loss"] < 0.5:
        return False
    if world.turret.height > 3.0:
        m.meters["worry"] += 1.0
        m.memes["caution"] += 1.0
        world.say(
            f"{m.id} looked up at the tall turret and felt a little worry wobble in "
            f"{its(m)} paws."
        )
        return True
    return False


def its(animal: Animal) -> str:
    return "its"


def answer_in_rhyme(world: World) -> None:
    m = world.facts["mouse"]
    o = world.facts["owl"]
    m.meters["courage"] += 1.0
    m.memes["rhyme"] += 1.0
    world.say(
        f"{m.id} answered in rhyme, soft as a seedpod: "
        f'"I can help with care, if you meet me halfway there."'
    )
    world.say(
        f"{o.id} heard the rhyme and tucked in a gentle thanks, because the rhyme made "
        f"the summons feel warm instead of sharp."
    )


def choose_kindness(world: World) -> None:
    m = world.facts["mouse"]
    o = world.facts["owl"]
    m.memes["kindness"] += 1.0
    o.memes["kindness"] += 1.0
    world.say(
        f"{m.id} did not rush. Instead, {m.id} asked {o.id} to lower a small basket on a rope, "
        f"so the little helper could work without climbing too high."
    )


def resolve_key(world: World) -> None:
    m = world.facts["mouse"]
    o = world.facts["owl"]
    m.meters["fatigue"] += 0.5
    o.meters["fatigue"] += 0.2
    m.meters["trust"] += 1.0
    o.meters["trust"] += 1.0
    m.meters["worry"] = max(0.0, m.meters["worry"] - 1.0)
    o.meters["loss"] = 0.0
    m.memes["gratitude"] += 1.0
    o.memes["gratitude"] += 1.0
    world.say(
        f"At last, {m.id} found the tiny key under a loose beam in the attic and placed "
        f"it in the basket. The rope rose, the key returned, and {o.id} chirped with relief."
    )


def end_image(world: World) -> None:
    m = world.facts["mouse"]
    o = world.facts["owl"]
    world.para()
    world.say(
        f"By evening, {m.id} was back in {world.attic.label} with calmer ears, and "
        f"{o.id} was in {world.turret.label} keeping the key safe. "
        f"The summons had turned into a careful friendship, and both animals felt braver."
    )


def tell_story(params: StoryParams) -> World:
    world = make_world(params)
    narrate_setup(world)
    world.para()
    caution_check(world)
    if params.virtue == "Rhyme":
        answer_in_rhyme(world)
    elif params.virtue == "Kindness":
        choose_kindness(world)
    else:
        world.say(
            f"{world.facts['mouse'].id} decided the safest way was to move slowly, "
            f"ask for help, and keep both paws on the floor."
        )
        world.facts["mouse"].memes["caution"] += 1.0
    resolve_key(world)
    end_image(world)
    world.facts["resolved"] = True
    return world


def story_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write an animal story about an attic, a turret, and a {p.summons_style} that asks for help.",
        f"Tell a gentle tale where a {p.mouse_name} in the attic responds to {p.owl_name}'s summons with {p.virtue.lower()}.",
        f"Write a short story for children about a mouse, an owl, and a lost key in {world.turret.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    m = world.facts["mouse"]
    o = world.facts["owl"]
    return [
        QAItem(
            question=f"Who lived in the attic in this story?",
            answer=f"{m.id}, the little mouse, lived in {world.attic.label} under the rafters."
        ),
        QAItem(
            question=f"What did {o.id} send from the turret?",
            answer=f"{o.id} sent a summons asking {m.id} to bring back the lost key."
        ),
        QAItem(
            question=f"How did {m.id} help without making the climb too risky?",
            answer="The mouse asked for a basket and rope, so the key could travel safely without a dangerous climb."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer="The lost key was found, the owl's worry faded, and the mouse and owl felt more trusting and grateful."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an attic?",
            answer="An attic is a room near the roof of a house, often tucked above the main rooms."
        ),
        QAItem(
            question="What is a turret?",
            answer="A turret is a small tower or high round room on a building."
        ),
        QAItem(
            question="What is a summons?",
            answer="A summons is a call or request that asks someone to come or do something."
        ),
        QAItem(
            question="Why can kindness help in a hard situation?",
            answer="Kindness helps because it makes it easier to ask for help, listen carefully, and solve the problem without hurting anyone."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return story_prompts(world)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.label:7}) meters={meters} memes={memes}")
    lines.append(f"  facts: {{'attic': {world.attic.label!r}, 'turret': {world.turret.label!r}}}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_story/4.

asked_for(mouse, key).
place(attic).
place(turret).
virtue(rhyme).
virtue(kindness).
virtue(cautionary).

story(Attic, Turret, Summons, Virtue) :- place(Attic), place(Turret),
                                          Attic != Turret,
                                          virtue(Virtue),
                                          summons(Summons).

good_story(Attic, Turret, Summons, Virtue) :- story(Attic, Turret, Summons, Virtue),
                                              has_kindness(Virtue),
                                              has_caution(Virtue),
                                              has_rhyme(Virtue).

valid_story(Attic, Turret, Summons, Virtue) :- story(Attic, Turret, Summons, Virtue).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for a in ATTICS.values():
        lines.append(asp.fact("place", a.id))
    for t in TURRETS.values():
        lines.append(asp.fact("place", t.id))
    for s in SUMMONS_STYLES:
        lines.append(asp.fact("summons", s))
    lines.append(asp.fact("has_rhyme", "rhyme"))
    lines.append(asp.fact("has_kindness", "kindness"))
    lines.append(asp.fact("has_caution", "cautionary"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    items = asp_valid_stories()
    expected = len(ATTICS) * len(TURRETS) * len(SUMMONS_STYLES) * 3
    if len(items) == expected:
        print(f"OK: ASP produced {len(items)} valid story combinations.")
        return 0
    print(f"Mismatch: expected {expected}, got {len(items)}")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    attic = args.attic or rng.choice(list(ATTICS))
    turret = args.turret or rng.choice(list(TURRETS))
    summons_style = args.summons_style or rng.choice(list(SUMMONS_STYLES))
    virtue = args.virtue or rng.choice(["Rhyme", "Kindness", "Cautionary"])
    caution_level = args.caution_level or rng.choice(["gentle", "careful", "very careful"])
    mouse_name = args.mouse_name or rng.choice(["Pip", "Nib", "Moss", "Tavi", "Rue"])
    owl_name = args.owl_name or rng.choice(["Hoot", "Morrow", "Sable", "Orin", "Wren"])
    return StoryParams(
        mouse_name=mouse_name,
        owl_name=owl_name,
        attic=attic,
        turret=turret,
        summons_style=summons_style,
        virtue=virtue,
        caution_level=caution_level,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{x}" for x in asp_valid_stories()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Pip", "Hoot", "lantern_attic", "north_turret", "rhyme", "Rhyme", "careful"),
            StoryParams("Nib", "Morrow", "beam_attic", "green_turret", "bell", "Kindness", "gentle"),
            StoryParams("Moss", "Sable", "dust_attic", "west_turret", "scroll", "Cautionary", "very careful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
