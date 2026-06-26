#!/usr/bin/env python3
"""
storyworlds/worlds/rhine_outing_form_surprise_sharing_whodunit.py
==================================================================

A small whodunit storyworld about a Rhine outing, a missing form, surprise,
and sharing. The world is intentionally tiny and state-driven: a child
detective notices clues, suspects a harmless helper, and learns that a shared
booklet explains the surprise.
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

MYSTERY_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    features: set[str] = field(default_factory=set)
    offers: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    suspect: str
    suspect_type: str
    form_type: str
    surprise: str
    sharing: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def infer_missing(world: World, detective: Entity, form: Entity) -> None:
    detective.memes["curious"] = detective.memes.get("curious", 0) + 1
    detective.memes["mystery"] = detective.memes.get("mystery", 0) + 1
    world.say(
        f"{detective.id} noticed the {form.label} was gone from the bag. "
        f"The river breeze on the Rhine made the empty pocket feel extra strange."
    )


def clue_by_helper(world: World, helper: Entity, detective: Entity, form: Entity) -> None:
    helper.memes["helpful"] = helper.memes.get("helpful", 0) + 1
    world.say(
        f"{helper.id} pointed to a neat stack of papers and said, "
        f'"I was sharing the forms so nobody would miss their turn."'
    )


def reveal(world: World, suspect: Entity, form: Entity, detective: Entity) -> None:
    suspect.memes["surprise"] = suspect.memes.get("surprise", 0) + 1
    world.say(
        f"Then came the surprise: {form.label} was not stolen at all. "
        f"It was tucked inside {suspect.pronoun('possessive')} folder, safe and dry."
    )
    world.say(
        f"{detective.id} realized the clue had been sharing, not stealing. "
        f"{suspect.id} had saved one copy for {detective.pronoun('object')} "
        f"and one for the rest of the outing."
    )


def tell_story(params: StoryParams) -> World:
    place = PLACE_REGISTRY[params.place]
    world = World(place)

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type))
    suspect = world.add(Entity(id=params.suspect, kind="character", type=params.suspect_type))
    form = world.add(Entity(
        id="form",
        type=params.form_type,
        label=f"{params.form_type} form",
        phrase=f"a {params.form_type} form for the outing",
        owner=hero.id,
        held_by=suspect.id,
        hidden=True,
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        suspect=suspect,
        form=form,
        place=place,
        surprise=params.surprise,
        sharing=params.sharing,
    )

    world.say(
        f"On a bright day by the Rhine, {hero.id} came to the outing with "
        f"a folder, a pencil, and one important {form.label}."
    )
    world.say(
        f"{hero.id} had planned to fill out the {form.label} before the boat left, "
        f"but the paper was missing."
    )
    world.para()
    infer_missing(world, hero, form)
    world.say(
        f"{hero.id} looked at {suspect.id}, because {suspect.id} had been near the table."
    )
    clue_by_helper(world, helper, hero, form)
    world.para()
    reveal(world, suspect, form, hero)
    world.say(
        f"In the end, the outing still went ahead, and {hero.id} carried the "
        f"{form.label} back in hand while everyone shared the last biscuits on deck."
    )
    return world


PLACE_REGISTRY = {
    "rhine": Place(
        name="the Rhine",
        features={"river", "boat", "dock", "breeze"},
        offers={"outing", "sharing", "surprise"},
    ),
    "park": Place(
        name="the park",
        features={"bench", "tree", "path"},
        offers={"outing", "sharing", "surprise"},
    ),
}

NAME_POOL = {
    "girl": ["Mina", "Lena", "Pia", "Tess"],
    "boy": ["Noah", "Eli", "Max", "Owen"],
    "mother": ["Mara", "Nina"],
    "father": ["Jon", "Otto"],
    "helper": ["June", "Tara", "Robin", "Ivo"],
    "suspect": ["Puck", "Sven", "Ruth", "Bela"],
}

FORMS = ["signup", "permission", "outing", "river"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whodunit storyworld about a Rhine outing and a missing form.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "rhine"
    hero_type = rng.choice(["girl", "boy"])
    helper_type = rng.choice(["mother", "father"])
    suspect_type = rng.choice(["girl", "boy"])
    hero = rng.choice(NAME_POOL[hero_type])
    helper = rng.choice(NAME_POOL[helper_type])
    suspect = rng.choice(NAME_POOL["suspect"])
    form_type = "outing"
    surprise = "surprise"
    sharing = "sharing"
    return StoryParams(
        place=place,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        suspect=suspect,
        suspect_type=suspect_type,
        form_type=form_type,
        surprise=surprise,
        sharing=sharing,
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit story for children set on {f["place"].name} with a missing form.',
        f"Tell a mystery about {f['hero'].id} on an outing, where the surprise is that the form was being shared, not stolen.",
        f'Write a gentle detective story that includes the words "Rhine", "outing", and "sharing".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, suspect, form, place = f["hero"], f["helper"], f["suspect"], f["form"], f["place"]
    return [
        QAItem(
            question=f"What was missing at the start of the Rhine outing?",
            answer=f"The missing thing was {form.label}. {hero.id} expected to use it before the outing began.",
        ),
        QAItem(
            question=f"Why did {hero.id} think {suspect.id} might be involved?",
            answer=f"{hero.id} thought {suspect.id} might be involved because {suspect.id} was near the table when the {form.label} disappeared.",
        ),
        QAItem(
            question=f"What turned out to be the real clue?",
            answer=f"The real clue was sharing. {helper.id} explained that the papers had been shared so nobody would be left out.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer=f"The surprise was that the {form.label} was not stolen at all; it was tucked safely inside {suspect.id}'s folder.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the Rhine?",
            answer="The Rhine is a river. People can take outings there, and boats often travel on it.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving others a turn or letting them use something too, so everyone can take part.",
        ),
        QAItem(
            question="What is a form?",
            answer="A form is a paper you fill out with information, often to ask permission or sign up for something.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.hidden:
            bits.append("hidden=True")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(rhine).
offers(rhine,outing).
offers(rhine,sharing).
offers(rhine,surprise).

valid_story(P) :- place(P), offers(P,outing), offers(P,sharing), offers(P,surprise).
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        for feat in sorted(place.features):
            lines.append(asp.fact("feature", pid, feat))
        for off in sorted(place.offers):
            lines.append(asp.fact("offers", pid, off))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "valid_story"))
    py = {(pid,) for pid, p in PLACE_REGISTRY.items() if {"outing", "sharing", "surprise"} <= p.offers}
    if atoms == py:
        print(f"OK: ASP matches Python ({len(py)} valid story place(s)).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("Python:", sorted(py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(vals)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    for i in range(args.n):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
