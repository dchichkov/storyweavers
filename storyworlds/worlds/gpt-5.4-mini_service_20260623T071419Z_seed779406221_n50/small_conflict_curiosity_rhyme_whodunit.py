#!/usr/bin/env python3
"""
storyworlds/worlds/small_conflict_curiosity_rhyme_whodunit.py
=============================================================

A small whodunit storyworld with conflict, curiosity, and rhyme.

Premise:
A child notices a tiny oddity in a small room, follows clues, and a gentle
mystery ends with a clear reveal. The story keeps the tone child-facing and
concrete, with a little rhyme as a memorable clue.

The world models:
- typed entities with physical meters and emotional memes
- a simple clue trail
- a harmless conflict beat
- a curiosity-driven investigation
- a rhyme that points to the answer
- a final reveal proving what changed

This script follows the Storyweavers storyworld contract:
- standalone stdlib Python script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    small: bool = True
    clue_spots: set[str] = field(default_factory=set)
    plausible_oddity: str = ""


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    rhyme: str
    spot: str
    reveals: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    question: str
    suspect: str
    answer: str
    trick: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_curiosity(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes.get("curiosity", 0) < THRESHOLD:
        return out
    sig = ("curiosity",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["looking"] = child.meters.get("looking", 0) + 1
    out.append("The child looked closer.")
    return out


def _r_conflict(world: World) -> list[str]:
    child = world.get("child")
    adult = world.get("adult")
    if child.memes.get("curiosity", 0) < THRESHOLD or adult.memes.get("worry", 0) < THRESHOLD:
        return []
    if ("conflict",) in world.fired:
        return []
    world.fired.add(("conflict",))
    child.memes["conflict"] = child.memes.get("conflict", 0) + 1
    adult.memes["conflict"] = adult.memes.get("conflict", 0) + 1
    return ["The room went quiet with a small conflict."]


def _r_reveal(world: World) -> list[str]:
    child = world.get("child")
    clue = world.get("clue")
    suspect = world.get("suspect")
    if child.meters.get("looking", 0) < THRESHOLD:
        return []
    if clue.meters.get("found", 0) < THRESHOLD:
        return []
    if ("reveal",) in world.fired:
        return []
    world.fired.add(("reveal",))
    world.facts["reveal"] = suspect.label
    clue.meters["understood"] = 1
    return [f"The answer was {suspect.label_word} all along."]


CAUSAL_RULES = [
    Rule(name="curiosity", apply=_r_curiosity),
    Rule(name="conflict", apply=_r_conflict),
    Rule(name="reveal", apply=_r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def rhyme_hint(clue: Clue) -> str:
    return clue.rhyme


def clue_matches_mystery(clue: Clue, mystery: Mystery) -> bool:
    return clue.reveals == mystery.answer


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for clue_id, clue in CLUES.items():
            for mystery_id, mystery in MYSTERIES.items():
                if place.small and clue.spot in place.clue_spots and clue_matches_mystery(clue, mystery):
                    combos.append((place_id, clue_id, mystery_id))
    return combos


@dataclass
class StoryParams:
    place: str
    clue: str
    mystery: str
    name: str
    gender: str
    adult: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place(id="kitchen", label="the small kitchen", clue_spots={"table", "sink", "mat"}, plausible_oddity="a missing spoon"),
    "hall": Place(id="hall", label="the narrow hall", clue_spots={"shoe-rack", "rug", "bench"}, plausible_oddity="a tilted frame"),
    "study": Place(id="study", label="the tiny study", clue_spots={"desk", "shelf", "lamp"}, plausible_oddity="an open drawer"),
}

CLUES = {
    "crumbs": Clue(id="crumbs", label="crumbs", phrase="a little trail of crumbs", rhyme="Crumbs and hums by the table come", spot="table", reveals="cookie", tags={"small", "food", "rhyme"}),
    "sock": Clue(id="sock", label="sock", phrase="one lonely sock", rhyme="A sock on the rug will tug your eye", spot="rug", reveals="cat", tags={"small", "lost", "rhyme"}),
    "note": Clue(id="note", label="note", phrase="a folded note", rhyme="A note in sight can make things right", spot="desk", reveals="bird", tags={"small", "paper", "rhyme"}),
}

MYSTERIES = {
    "cookie": Mystery(id="cookie", label="cookie mystery", question="who took the cookie", suspect="cookie jar", answer="cookie", trick="crumbs", tags={"small", "food"}),
    "cat": Mystery(id="cat", label="cat mystery", question="where the cat hid", suspect="under the rug", answer="cat", trick="sock", tags={"small", "pet"}),
    "bird": Mystery(id="bird", label="bird mystery", question="what opened the window", suspect="the breeze", answer="bird", trick="note", tags={"small", "paper"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Sam"]
ADULTS = ["mother", "father", "grandmother", "grandfather"]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.small:
            lines.append(asp.fact("small", pid))
        for spot in sorted(p.clue_spots):
            lines.append(asp.fact("spot", pid, spot))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("reveal", cid, c.reveals))
        lines.append(asp.fact("spot", c.id, c.spot))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("answer", mid, m.answer))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,M) :- place(P), small(P), clue(C), mystery(M), spot(P,S), spot(C,S), reveal(C,R), answer(M,R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    ok = 0
    if py != asp_set:
        print("MISMATCH between Python and ASP valid_combos()")
        print("python-only:", sorted(py - asp_set))
        print("asp-only:", sorted(asp_set - py))
        ok = 1
    else:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    # smoke test
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        ok = 1
    return ok


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Small whodunit storyworld with curiosity, conflict, and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULTS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(ADULTS)
    return StoryParams(place=place, clue=clue, mystery=mystery, name=name, gender=gender, adult=adult)


def tell(place: Place, clue: Clue, mystery: Mystery, child_name: str, gender: str, adult: str) -> World:
    w = World(place)
    child = w.add(Entity(id="child", kind="character", type=gender, label=child_name, meters={}, memes={}))
    parent = w.add(Entity(id="adult", kind="character", type=adult, label=f"the {adult}", meters={}, memes={}))
    clue_ent = w.add(Entity(id="clue", kind="thing", type="clue", label=clue.label, phrase=clue.phrase, meters={"found": 0.0}, memes={}))
    suspect = w.add(Entity(id="suspect", kind="thing", type="suspect", label=mystery.suspect, phrase=mystery.suspect, meters={"hidden": 1.0}, memes={}))
    # initialize all state before propagation
    child.memes["curiosity"] = 1.0
    parent.memes["worry"] = 1.0
    child.meters["steps"] = 0.0
    parent.meters["listening"] = 1.0

    w.say(f"{child_name} was a little {gender} with a big question in {w.place.label}.")
    w.say(f"{child_name} noticed {clue.phrase} by the {clue.spot}, and the clue felt important.")
    w.para()
    child.meters["steps"] += 1
    child.memes["curiosity"] += 1.0
    propagate(w, narrate=True)
    w.say(f'"{clue.rhyme}," {child_name} said, and looked again.')
    clue_ent.meters["found"] = 1.0
    w.para()
    if child.memes.get("conflict", 0) >= THRESHOLD:
        w.say(f"{adult.capitalize()} frowned for a moment, because the little mystery was becoming a small conflict.")
    propagate(w, narrate=True)
    w.para()
    clue_ent.meters["understood"] = 1.0
    w.facts["answer"] = mystery.answer
    w.say(f"At last, {child_name} solved the {mystery.label}: the answer was {mystery.answer}.")
    w.say(f"The small room felt calm again, and {child_name} smiled at the tidy clue trail.")
    w.facts.update(child=child, adult=parent, clue=clue_ent, suspect=suspect, place=place, clue_cfg=clue, mystery=mystery, resolved=True)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small whodunit for a child named {f["child"].label} in {f["place"].label} with one curious clue and one gentle conflict.',
        f"Tell a rhyme-filled mystery where {f['child'].label} notices {f['clue_cfg'].phrase} and solves a tiny puzzle in {f['place'].label}.",
        f"Write a child-friendly whodunit that ends when the answer turns out to be {f['mystery'].answer}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    clue = f["clue_cfg"]
    mystery = f["mystery"]
    return [
        QAItem(question=f"Who is the story about?", answer=f"It is about {child.label}, who notices a clue and follows it in {f['place'].label}."),
        QAItem(question=f"What clue did {child.label} find?", answer=f"{child.label} found {clue.phrase}. That clue helped point the mystery in the right direction."),
        QAItem(question=f"What rhyme did {child.label} say?", answer=f"{clue.rhyme} It helped {child.label} remember the clue."),
        QAItem(question=f"What was the answer to the mystery?", answer=f"The answer was {mystery.answer}. In the end, the little whodunit was solved."),
        QAItem(question=f"Why was there a small conflict?", answer=f"{adult.label_word.capitalize()} worried because the clue hunt made the room feel tense for a moment, but the worry helped the story turn toward the solution."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is curiosity?", answer="Curiosity is the feeling that makes you want to look, ask, and learn."),
        QAItem(question="What is a clue?", answer="A clue is a little piece of information that helps solve a mystery."),
        QAItem(question="What is a rhyme?", answer="A rhyme is when words sound alike at the end, like cat and hat."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", clue="crumbs", mystery="cookie", name="Mia", gender="girl", adult="mother"),
    StoryParams(place="hall", clue="sock", mystery="cat", name="Leo", gender="boy", adult="father"),
    StoryParams(place="study", clue="note", mystery="bird", name="Nora", gender="girl", adult="grandmother"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.mystery not in MYSTERIES:
        raise StoryError("Invalid parameters.")
    if not clue_matches_mystery(CLUES[params.clue], MYSTERIES[params.mystery]):
        raise StoryError("Chosen clue and mystery do not match.")
    if CLUES[params.clue].spot not in PLACES[params.place].clue_spots:
        raise StoryError("Chosen clue does not fit the place.")
    world = tell(PLACES[params.place], CLUES[params.clue], MYSTERIES[params.mystery], params.name, params.gender, params.adult)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for p, c, m in combos:
            print(f"  {p:8} {c:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
