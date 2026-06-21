#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/recover_mystery_to_solve_mystery.py
====================================================================

A standalone story world for a tiny mystery: something important goes missing,
the child follows clues, recovers the missing thing, and solves the mystery.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a few causal rules over state
- a reasonableness gate for valid mysteries
- three QA sets grounded in the simulated world
- an inline ASP twin for the gate and the outcome model

The seed word is "recover"; the style is mystery; the narrative instrument is a
mystery to solve. The result is a child-facing detective tale with a clear
beginning, middle turn, and ending image showing what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    kind: str
    dark: bool = False
    clueable: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    missing_phrase: str
    recover_verb: str
    tags: set[str] = field(default_factory=set)
    hidden: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    leads_to: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    phrase: str
    innocent_hint: str
    culprit_hint: str
    innocent: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


@dataclass
class StoryParams:
    place: str
    missing: str
    clue1: str
    clue2: str
    suspect: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    adult: str
    seed: Optional[int] = None


def _r_clue(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    clue1 = world.facts.get("clue1")
    clue2 = world.facts.get("clue2")
    if hero.meters["searching"] < THRESHOLD:
        return out
    if clue1 and clue1.id not in world.fired and world.facts.get("searched_room") == clue1.leads_to:
        world.fired.add((clue1.id, "found"))
        hero.memes["hope"] += 1
        out.append(f"They noticed {clue1.phrase}.")
    if clue2 and clue2.id not in world.fired and world.facts.get("followed_clue1"):
        world.fired.add((clue2.id, "found"))
        hero.memes["certainty"] += 1
        out.append(f"That pointed them toward {clue2.phrase}.")
    return out


CAUSAL_RULES = [Rule("clue", _r_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for missing in ITEMS:
            if not ITEMS[missing].hidden:
                continue
            for clue1 in CLUES:
                for clue2 in CLUES:
                    if clue1 != clue2 and CLUES[clue1].leads_to == missing and CLUES[clue2].leads_to == missing:
                        combos.append((place, missing, clue1))
    return combos


def reasonableness_gate(place: Place, item: Item) -> bool:
    return place.clueable and item.hidden


def outcome_of(params: StoryParams) -> str:
    item = ITEMS[params.missing]
    return "recovered" if item.hidden else "lost"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a small mystery that gets solved.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--missing", choices=ITEMS)
    ap.add_argument("--clue1", choices=CLUES)
    ap.add_argument("--clue2", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
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
    if args.missing and args.place and not reasonableness_gate(PLACES[args.place], ITEMS[args.missing]):
        raise StoryError("That mystery would not have enough clues to solve.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.missing is None or c[1] == args.missing)
              and (args.clue1 is None or c[2] == args.clue1)]
    if not combos:
        raise StoryError("(No valid mystery matches the given options.)")
    place, missing, clue1 = rng.choice(sorted(combos))
    clue2s = [cid for cid, c in CLUES.items() if c.leads_to == missing and cid != clue1]
    clue2 = args.clue2 or rng.choice(sorted(clue2s))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    hero_name = rng.choice(GIRL_NAMES + BOY_NAMES)
    hero_gender = "girl" if hero_name in GIRL_NAMES else "boy"
    helper_name = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    helper_gender = "girl" if helper_name in GIRL_NAMES else "boy"
    return StoryParams(place=place, missing=missing, clue1=clue1, clue2=clue2, suspect=suspect,
                       hero_name=hero_name, hero_gender=hero_gender,
                       helper_name=helper_name, helper_gender=helper_gender,
                       adult=adult)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name, role="detective"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name, role="helper"))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult, label="the grown-up", role="adult"))
    place = world.add(Entity(id="place", type="place", label=PLACES[params.place].label))
    missing = world.add(Entity(id="missing", type="item", label=ITEMS[params.missing].label))
    clue1 = world.add(Entity(id="clue1", type="clue", label=CLUES[params.clue1].label))
    clue2 = world.add(Entity(id="clue2", type="clue", label=CLUES[params.clue2].label))
    suspect = world.add(Entity(id="suspect", type="suspect", label=SUSPECTS[params.suspect].label))
    world.facts.update(place=PLACES[params.place], missing=ITEMS[params.missing], clue1=CLUES[params.clue1], clue2=CLUES[params.clue2], suspect=SUSPECTS[params.suspect])
    world.facts["searched_room"] = CLUES[params.clue1].leads_to
    world.facts["followed_clue1"] = True

    hero.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(f"One quiet afternoon, {params.hero_name} and {params.helper_name} noticed that {ITEMS[params.missing].phrase} was gone from {PLACES[params.place].label}.")
    world.say(f"{params.hero_name} frowned. {params.helper_name} looked around the room and said they would solve the mystery.")
    world.para()
    hero.meters["searching"] += 1
    world.say(f"They started at {PLACES[params.place].label}. Under a chair, they found {CLUES[params.clue1].phrase}.")
    propagate(world)
    world.say(f"{CLUES[params.clue1].leads_to.capitalize()} gave them another place to look.")
    world.para()
    world.say(f"At last they followed a second clue: {CLUES[params.clue2].phrase}.")
    hero.memes["certainty"] += 1
    missing.hidden = False
    missing.meters["recovered"] += 1
    hero.meters["solved"] += 1
    world.say(f"That trail led straight to the missing {ITEMS[params.missing].label}, tucked safely away.")
    world.say(f"{params.adult.capitalize()} smiled, and the whole mystery was solved before supper.")
    world.say(f"{params.hero_name} held the recovered {ITEMS[params.missing].label} close, proud to have found it.")

    world.facts.update(hero=hero, helper=helper, adult=adult, missing_item=missing, suspect=suspect, place_entity=place, outcome="recovered")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the word "recover" and takes place at {f["place"].label}.',
        f"Tell a story where {world.facts['hero'].label} and {world.facts['helper'].label} solve a mystery and recover the missing {f['missing'].label}.",
        f"Write a gentle mystery where clues lead to the recovered {f['missing'].label} and the grown-up is pleased at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    missing = f["missing"]
    qas = [
        ("What was missing?", f"The missing thing was {missing.phrase}. That was the mystery they needed to solve."),
        ("How did they solve the mystery?", f"They followed {f['clue1'].phrase} and then {f['clue2'].phrase}. The clues led them back to the place where the missing {missing.label} was hidden."),
        ("What happened at the end?", f"They recovered the {missing.label} and the grown-up smiled. The mystery was solved, and the child could hold the recovered thing safely again."),
    ]
    qas.append((
        "Why was the mystery solvable?",
        f"The place had clues, so the children could search in order instead of guessing. That made the trail clear enough to recover the missing {missing.label}."
    ))
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clue?", "A clue is a small hint that helps you figure something out. In a mystery, clues lead you toward the answer."),
        ("What does recover mean?", "Recover means to get something back after it was lost or taken away. You can recover a missing thing by finding it again."),
        ("Why do detectives look carefully?", "Detectives look carefully because little details can point to the truth. A tiny clue can solve the whole mystery."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


PLACES = {
    "attic": Place(id="attic", label="the attic", kind="room", dark=True, clueable=True, tags={"dark"}),
    "library": Place(id="library", label="the little library", kind="room", dark=False, clueable=True, tags={"books"}),
    "kitchen": Place(id="kitchen", label="the kitchen", kind="room", dark=False, clueable=True, tags={"home"}),
}

ITEMS = {
    "key": Item(id="key", label="brass key", phrase="a tiny brass key", missing_phrase="the brass key", recover_verb="recover", tags={"metal"}),
    "cat": Item(id="cat", label="toy cat", phrase="a soft toy cat", missing_phrase="the toy cat", recover_verb="recover", tags={"toy"}),
    "hat": Item(id="hat", label="red hat", phrase="a red hat", missing_phrase="the red hat", recover_verb="recover", tags={"cloth"}),
}

CLUES = {
    "dust": Clue(id="dust", label="dusty footprints", phrase="dusty footprints near the stairs", leads_to="attic", tags={"dust"}),
    "note": Clue(id="note", label="a folded note", phrase="a folded note with one word: attic", leads_to="attic", tags={"paper"}),
    "spoon": Clue(id="spoon", label="a shiny spoon", phrase="a shiny spoon by the table", leads_to="kitchen", tags={"metal"}),
    "book": Clue(id="book", label="an open book", phrase="an open book marked with a page number", leads_to="library", tags={"book"}),
}

SUSPECTS = {
    "wind": Suspect(id="wind", label="the wind", phrase="a windy hallway", innocent_hint="the wind could not carry it far", culprit_hint="the wind had no hands", innocent=True, tags={"weather"}),
    "cat": Suspect(id="cat", label="the cat", phrase="the sleepy cat", innocent_hint="the cat was napping the whole time", culprit_hint="the cat was only watching", innocent=True, tags={"pet"}),
    "sneaky": Suspect(id="sneaky", label="the sneaky cousin", phrase="a sneaky cousin", innocent_hint="the cousin was actually helping", culprit_hint="the cousin hid it as a prank", innocent=False, tags={"person"}),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Ben", "Tom", "Leo", "Finn", "Eli"]


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="attic", missing="key", clue1="dust", clue2="note", suspect="sneaky", hero_name="Mia", hero_gender="girl", helper_name="Ben", helper_gender="boy", adult="mother"),
        StoryParams(place="library", missing="hat", clue1="book", clue2="note", suspect="cat", hero_name="Leo", hero_gender="boy", helper_name="Ava", helper_gender="girl", adult="father"),
    ]


ASP_RULES = r"""
place(P) :- room(P).
item(I) :- thing(I).
solve(P,I) :- clue(C1), clue(C2), leads_to(C1,P), leads_to(C2,P), missing(I), clueable(P).
recovered(I) :- solve(_,I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("room", pid))
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("clueable", pid))
    for iid in ITEMS:
        lines.append(asp.fact("missing", iid))
        lines.append(asp.fact("thing", iid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("leads_to", cid, c.leads_to))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solve/2."))
    return sorted(set(asp.atoms(model, "solve")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set((p, i) for p, i, _ in valid_combos()):
        print("OK: ASP gate matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, missing=None, clue1=None, clue2=None, suspect=None, adult=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        return 1 if not print(f"SMOKE TEST FAILED: {exc}") else 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.missing not in ITEMS or params.clue1 not in CLUES or params.clue2 not in CLUES or params.suspect not in SUSPECTS:
        raise StoryError("Invalid parameters.")
    if params.clue1 == params.clue2:
        raise StoryError("The mystery needs two different clues.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show solve/2.\n#show recovered/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} solve combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in curated()]
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
