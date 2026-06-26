#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/heaven_strap_transformation_conflict_space_adventure.py
=============================================================================================================================

A small space-adventure storyworld about a child astronaut, a special strap,
and a tricky transformation that can help or cause conflict.

Seed image:
---
A child on a bright space station finds a strange strap in a storage drawer.
When they put it on, it can transform them into a floating helper form that
can cross a dangerous gap near a glowing place nicknamed Heaven. But the strap
also makes them feel different, and they argue with a worried crew member before
choosing how to use it safely.

World premise:
---
- The hero wants to explore a beautiful sky-lane above a station.
- A transformation strap can change the hero into a more capable form.
- The strap is useful, but the change creates conflict because the crew worries
  about safety and identity.
- Resolution comes when the hero uses the strap in a careful, shared way.

This file follows the Storyweavers world contract:
- typed entities with physical meters and emotional memes
- a reasonableness gate in Python and an inline ASP twin
- story-driven prose, Q&A, trace output, JSON, and verification
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
# Entities
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    form: str = "normal"
    safe_form: Optional[str] = None
    risk_form: Optional[str] = None
    transformable: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Dock:
    name: str
    place: str
    affords: set[str] = field(default_factory=set)
    has_view: bool = False


@dataclass
class Strap:
    id: str
    label: str
    phrase: str
    transforms_to: str
    risky_to: str
    safe_use: str
    prepares_for: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, dock: Dock) -> None:
        self.dock = dock
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.notes: list[str] = []

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
        import copy as _copy
        clone = World(self.dock)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.notes = list(self.notes)
        return clone


# ---------------------------------------------------------------------------
# World data
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    dock: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    strap: str
    seed: Optional[int] = None


DOCKS = {
    "skyport": Dock(
        name="Skyport Ring",
        place="the Skyport Ring",
        affords={"float_gap", "view_heaven"},
        has_view=True,
    ),
    "lumen_gate": Dock(
        name="Lumen Gate",
        place="the Lumen Gate",
        affords={"float_gap", "view_heaven"},
        has_view=True,
    ),
    "star_wharf": Dock(
        name="Star Wharf",
        place="the Star Wharf",
        affords={"float_gap"},
        has_view=False,
    ),
}

STRAPS = {
    "glide_strap": Strap(
        id="glide_strap",
        label="glide strap",
        phrase="a silver strap with tiny star buckles",
        transforms_to="glider",
        risky_to="normal",
        safe_use="clip it on and switch to the glider form",
        prepares_for="cross the open gap",
        guards={"vacuum", "spin"},
    ),
    "light_strap": Strap(
        id="light_strap",
        label="light strap",
        phrase="a bright strap woven with soft blue thread",
        transforms_to="lightform",
        risky_to="normal",
        safe_use="wear it to become a lighter, steadier helper",
        prepares_for="float past the drifting crates",
        guards={"vacuum"},
    ),
}

HERO_NAMES = ["Mila", "Rin", "Tavi", "Nova", "Lio", "Zee"]
HELPER_NAMES = ["Pax", "Juno", "Iris", "Moro", "Sage"]
TRAITS = ["curious", "brave", "gentle", "restless", "hopeful", "inventive"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.
#show valid_story/3.

can_transform(H,S) :- hero(H), strap(S), transforms_to(S,_).
risk(H,S) :- hero(H), strap(S), risky_to(S,F), form(H,F).

safe(H,S) :- can_transform(H,S), not risk(H,S).
valid(D,S,Story) :- dock(D), strap(S), story(Story), usable_at(D,S), safe_story(D,S,Story).

safe_story(D,S,float_gap) :- affords(D,float_gap), strap(S), prepares_for(S,cross_gap).
safe_story(D,S,view_heaven) :- view(D), strap(S), transforms_to(S,glider).

valid_story(D,S,hero_and_helper) :- valid(D,S,hero_and_helper).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for did, d in DOCKS.items():
        lines.append(asp.fact("dock", did))
        if d.has_view:
            lines.append(asp.fact("view", did))
        for a in sorted(d.affords):
            lines.append(asp.fact("affords", did, a))
    for sid, s in STRAPS.items():
        lines.append(asp.fact("strap", sid))
        lines.append(asp.fact("transforms_to", sid, s.transforms_to))
        lines.append(asp.fact("risky_to", sid, s.risky_to))
        lines.append(asp.fact("prepares_for", sid, "cross_gap"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((d, s) for d, s in valid_pairs())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_pairs() ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and valid_pairs():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_pair(dock: Dock, strap: Strap) -> bool:
    return "float_gap" in dock.affords and strap.transforms_to in {"glider", "lightform"}


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for did, d in DOCKS.items():
        for sid, s in STRAPS.items():
            if valid_pair(d, s):
                out.append((did, sid))
    return out


def explain_rejection(dock: Dock, strap: Strap) -> str:
    if "float_gap" not in dock.affords:
        return f"(No story: {dock.place} does not have the open gap that needs a transformation strap.)"
    return f"(No story: {strap.label} would not help with the gap in a way the story can honestly solve.)"


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def predict(world: World, hero: Entity, strap: Strap) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.form = strap.transforms_to
    h.memes["transformed"] = h.memes.get("transformed", 0) + 1
    h.meters["stability"] = h.meters.get("stability", 0) + 1
    danger = strap.risky_to == hero.form
    return {"danger": danger, "transformed": h.form}


def setup(world: World, hero: Entity, helper: Entity, strap: Entity) -> None:
    world.say(
        f"{hero.id} lived on {world.dock.place}, where the windows showed a deep blue sky "
        f"and the faraway glow of Heaven Station."
    )
    world.say(
        f"{hero.id} loved looking toward the shining path, but {hero.pronoun('possessive')} "
        f"{helper.label_word} always reminded {hero.pronoun('object')} to move carefully."
    )
    world.say(
        f"One day, {hero.id} found {hero.pronoun('possessive')} {strap.label} in a storage drawer. "
        f"It looked like it could change a small flyer into something more fit for space."
    )
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1


def conflict(world: World, hero: Entity, helper: Entity, strap: Entity, dock: Dock) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0) + 1
    world.para()
    world.say(
        f"{hero.id} wanted to use the {strap.label} right away and cross the open gap near Heaven Station."
    )
    world.say(
        f'But {helper.id} frowned. "If you change too fast, you could spin out and lose your way," '
        f"{helper.pronoun('subject')} said."
    )
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    helper.memes["conflict"] = helper.memes.get("conflict", 0) + 1


def transform(world: World, hero: Entity, strap: Strap) -> None:
    hero.form = strap.transforms_to
    hero.meters["stability"] = hero.meters.get("stability", 0) + 1
    hero.meters["reach"] = hero.meters.get("reach", 0) + 1
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    world.say(
        f"{hero.id} clipped on the strap and felt their arms grow light and steady. "
        f"They shifted into a {strap.transforms_to} form that could glide without shaking."
    )


def resolve(world: World, hero: Entity, helper: Entity, strap: Strap) -> None:
    hero.memes["conflict"] = 0
    helper.memes["conflict"] = 0
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0) + 1
    world.para()
    world.say(
        f'{hero.id} nodded and said, "I will use it the safe way."'
    )
    world.say(
        f"So {hero.id} used the {strap.label} to become a {strap.transforms_to}, and {helper.id} "
        f"guided the route. Together they crossed the gap and reached the bright overlook above Heaven Station."
    )
    world.say(
        f"In the end, the strap did not just change how {hero.id} moved; it helped {hero.id} and {helper.id} "
        f"work together like a true space crew."
    )


def tell(dock: Dock, strap_cfg: Strap, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(dock)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", "spacefaring", "curious"],
        form="normal",
        safe_form=strap_cfg.transforms_to,
        risk_form="normal",
        transformable=True,
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        traits=["patient", "careful"],
        form="normal",
    ))
    strap = world.add(Entity(
        id=strap_cfg.id,
        type="strap",
        label=strap_cfg.label,
        phrase=strap_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        worn_by=hero.id,
    ))

    setup(world, hero, helper, strap)
    conflict(world, hero, helper, strap, dock)
    transform(world, hero, strap_cfg)
    resolve(world, hero, helper, strap_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        strap=strap_cfg,
        dock=dock,
        resolved=True,
        transformed_form=hero.form,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a young child that includes the word "heaven" and the word "strap".',
        f"Tell a story where {f['hero'].id} finds a {f['strap'].label} on {f['dock'].place} and uses it to cross a dangerous gap.",
        f"Write a child-friendly story about a transformation that causes a conflict, then ends with a careful teamwork solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    strap: Strap = f["strap"]
    dock: Dock = f["dock"]
    return [
        QAItem(
            question=f"Where did {hero.id} live at the start of the story?",
            answer=f"{hero.id} lived on {dock.place}, where the windows looked out toward Heaven Station.",
        ),
        QAItem(
            question=f"What did {hero.id} find that could change how {hero.pronoun('subject')} moved?",
            answer=f"{hero.id} found the {strap.label}, which could transform {hero.pronoun('object')} into a {strap.transforms_to}.",
        ),
        QAItem(
            question=f"Why was there conflict between {hero.id} and {helper.id}?",
            answer=f"There was conflict because {hero.id} wanted to use the {strap.label} right away, but {helper.id} worried the change might be unsafe.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {helper.id}?",
            answer=f"They used the {strap.label} carefully, crossed the gap together, and reached the bright overlook above Heaven Station.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a strap?",
            answer="A strap is a long strip of material used to tie, hold, or fasten something securely.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means a change from one form into another form.",
        ),
        QAItem(
            question="What is a space station?",
            answer="A space station is a place built to orbit above a planet where people can live and work for a while.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.transformable:
            bits.append(f"form={e.form}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.dock and args.strap and not valid_pair(DOCKS[args.dock], STRAPS[args.strap]):
        raise StoryError(explain_rejection(DOCKS[args.dock], STRAPS[args.strap]))
    pairs = [p for p in valid_pairs()
             if (args.dock is None or p[0] == args.dock)
             and (args.strap is None or p[1] == args.strap)]
    if not pairs:
        raise StoryError("(No valid combination matches the given options.)")
    dock, strap = rng.choice(sorted(pairs))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    return StoryParams(
        dock=dock,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        strap=strap,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        DOCKS[params.dock],
        STRAPS[params.strap],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
    )
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
    ap = argparse.ArgumentParser(
        description="Space adventure storyworld: a child, a strap, a transformation, and a conflict."
    )
    ap.add_argument("--dock", choices=DOCKS)
    ap.add_argument("--strap", choices=STRAPS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2.\n#show valid_story/3."))
        pairs = sorted(set(asp.atoms(model, "valid")))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} compatible dock/strap pairs:")
        for d, s in pairs:
            print(f"  {d:12} {s}")
        if stories:
            print("\nGender/story-compatible entries:")
            for item in stories:
                print(f"  {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for did, sid in sorted(valid_pairs()):
            params = StoryParams(
                dock=did,
                hero_name="Mila",
                hero_type="girl",
                helper_name="Pax",
                helper_type="boy",
                strap=sid,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
