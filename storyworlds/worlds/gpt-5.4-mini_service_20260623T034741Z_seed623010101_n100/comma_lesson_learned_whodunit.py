#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/comma_lesson_learned_whodunit.py
==============================================================================================================

A tiny whodunit storyworld built from the seed prompt:
- includes the word "comma"
- has a lesson learned
- keeps a child-facing mystery tone
- uses typed entities with meters and memes
- includes Python and ASP reasonableness checks

Premise:
A child loses a small object during a neighborhood game, and the clues point to
two plausible suspects. The ending proves who actually moved it, why the mistake
happened, and what lesson was learned about checking details.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, object] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    owner: str
    missing_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    points_to: str
    noisy: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def people(self) -> list[Entity]:
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            parts = rule.apply(world)
            if parts:
                changed = True
                out.extend(parts)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_worried(world: World) -> list[str]:
    out: list[str] = []
    for p in world.people():
        if p.memes.get("puzzled", 0.0) < THRESHOLD:
            continue
        if ("worry", p.id) in world.fired:
            continue
        world.fired.add(("worry", p.id))
        p.memes["worry"] = p.memes.get("worry", 0.0) + 1
        out.append(f"{p.label_word.capitalize()} looked worried.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.meters.get("proof", 0.0) >= THRESHOLD and ("lesson",) not in world.fired:
        world.fired.add(("lesson",))
        detective.memes["lesson"] = detective.memes.get("lesson", 0.0) + 1
        out.append("A careful look turned the mystery into a lesson learned.")
    return out


CAUSAL_RULES = [
    Rule("worry", _r_worried),
    Rule("lesson", _r_lesson),
]


@dataclass
class StoryParams:
    place: str
    detective_name: str
    helper_name: str
    culprit_name: str
    item: str
    clue: str
    seed: Optional[int] = None


PLACES = {
    "library": Place(id="library", label="the library", indoors=True, tags={"books", "quiet"}),
    "garden": Place(id="garden", label="the garden", indoors=False, tags={"plants", "paths"}),
    "porch": Place(id="porch", label="the front porch", indoors=False, tags={"steps", "door"}),
}

ITEMS = {
    "toy_bus": Item(id="toy_bus", label="toy bus", phrase="a red toy bus with a bell", owner="detective", missing_by="helper", tags={"toy", "bus"}),
    "blue_hat": Item(id="blue_hat", label="blue hat", phrase="a blue hat with a soft brim", owner="detective", missing_by="helper", tags={"hat", "cloth"}),
    "kite": Item(id="kite", label="kite", phrase="a striped kite string", owner="detective", missing_by="helper", tags={"kite", "string"}),
}

CLUES = {
    "comma_note": Clue(id="comma_note", label="comma note", phrase="a note with a comma in the middle", points_to="helper", noisy=False, tags={"comma", "note"}),
    "muddy_mark": Clue(id="muddy_mark", label="muddy mark", phrase="mud on one shoe and a small scrap of paper", points_to="culprit", noisy=True, tags={"mud", "scrap"}),
    "half_sentence": Clue(id="half_sentence", label="half-sentence", phrase="a half-sentence that stopped after the first word", points_to="helper", noisy=False, tags={"sentence", "comma"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Pia", "Tess"]
BOY_NAMES = ["Owen", "Ezra", "Jude", "Finn", "Bram"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for item in ITEMS:
            for clue in CLUES:
                if clue == "comma_note":
                    combos.append((place, item, clue))
    return combos


def reasonableness_gate(item: Item, clue: Clue) -> bool:
    return "comma" in clue.tags and item.owner == "detective"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("owned_by", iid, item.owner))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for tag in clue.tags:
            lines.append(asp.fact("has_tag", cid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,I,C) :- place(P), item(I), clue(C), owned_by(I, detective), has_tag(C, comma).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    detective = world.add(Entity(id="detective", kind="character", type="girl", label=params.detective_name, role="detective", traits=["careful"], meters={"proof": 0.0}, memes={"curious": 1.0, "puzzled": 0.0}))
    helper = world.add(Entity(id="helper", kind="character", type="boy", label=params.helper_name, role="helper", traits=["helpful"], meters={"proof": 0.0}, memes={"kind": 1.0}))
    culprit = world.add(Entity(id="culprit", kind="character", type="boy", label=params.culprit_name, role="culprit", traits=["sneaky"], meters={"proof": 0.0}, memes={"nervous": 1.0}))
    item = world.add(Entity(id="item", kind="thing", type=params.item, label=ITEMS[params.item].label, attrs={"phrase": ITEMS[params.item].phrase}, meters={"missing": 1.0}, memes={"important": 1.0}))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=CLUES[params.clue].label, attrs={"phrase": CLUES[params.clue].phrase, "points_to": CLUES[params.clue].points_to}, meters={"found": 1.0}, memes={"strange": 1.0}))

    detective.memes["puzzled"] = 1.0
    world.say(f"{detective.label_word.capitalize()} found that {item.attrs['phrase']} was missing at {place.label}.")
    world.say(f"{helper.label_word.capitalize()} and {culprit.label_word.capitalize()} both had reasons to be near the spot, so the mystery was not simple.")

    world.para()
    if clue.id == "comma_note":
        detective.meters["proof"] += 1.0
        helper.memes["nervous"] += 1.0
        world.say(f"Then {detective.label_word} spotted {clue.attrs['phrase']}, and the comma made the note feel like a message meant for only one helper.")
        world.say(f"{helper.label_word.capitalize()} admitted the note had been folded into a pocket, not hidden on purpose, because someone had rushed and left a message unfinished.")
    else:
        world.say(f"{detective.label_word.capitalize()} studied {clue.attrs['phrase']} and kept looking for a better clue.")

    world.para()
    world.say(f"At last, {detective.label_word.capitalize()} checked the scene again and found the missing {item.label} tucked where it had fallen during play.")
    culprit.meters["proof"] += 1.0
    detective.meters["proof"] += 1.0
    propagate(world, narrate=True)
    world.say(f"{detective.label_word.capitalize()} smiled. The whole mystery had been a mistake caused by haste, and the lesson learned was to read every note all the way through, comma and all.")

    world.facts.update(
        detective=detective,
        helper=helper,
        culprit=culprit,
        item=item,
        clue=clue,
        place=place,
        solved=True,
        lesson=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child that includes the word "comma" and ends with a lesson learned.',
        f"Tell a gentle mystery about {f['detective'].label_word} finding {f['item'].label} in {f['place'].label}, with a clue about a comma.",
        f"Write a tiny detective story where a message with a comma helps solve what happened to the missing {f['item'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d, h, c, item, clue, place = f["detective"], f["helper"], f["culprit"], f["item"], f["clue"], f["place"]
    return [
        QAItem(
            question=f"What was missing at {place.label}?",
            answer=f"The missing thing was {item.attrs['phrase']}. It had slipped out of place during the game, which is why everyone started wondering what happened.",
        ),
        QAItem(
            question=f"Why did the comma clue matter to {d.label_word}?",
            answer=f"The comma clue made the message easier to read as a message meant for one helper instead of a jumble of words. That helped {d.label_word} think about who had handled the note and where to look next.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{d.label_word.capitalize()} checked the scene again and found the {item.label} where it had fallen. The clue, the careful search, and the honest explanation turned the confusion into a clear answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a comma?",
            answer="A comma is a small mark used in writing to separate words or parts of a sentence. It helps readers pause in the right place and understand the message more clearly.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and asks questions to figure out what happened. The detective pays close attention to small details that other people might miss.",
        ),
        QAItem(
            question="Why do people read notes carefully?",
            answer="People read notes carefully so they do not miss an important detail. A tiny mark or word can change what the message means.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, item, clue = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        detective_name=args.detective or rng.choice(GIRL_NAMES),
        helper_name=args.helper or rng.choice(BOY_NAMES),
        culprit_name=args.culprit or rng.choice(BOY_NAMES),
        item=item,
        clue=clue,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.item not in ITEMS or params.clue not in CLUES:
        raise StoryError("Invalid params.")
    item = ITEMS[params.item]
    clue = CLUES[params.clue]
    if not reasonableness_gate(item, clue):
        raise StoryError("This mystery setup is not reasonable.")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny whodunit storyworld with comma and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--culprit")
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


CURATED = [
    StoryParams(place="library", detective_name="Mina", helper_name="Owen", culprit_name="Jude", item="toy_bus", clue="comma_note"),
    StoryParams(place="garden", detective_name="Lila", helper_name="Finn", culprit_name="Bram", item="blue_hat", clue="comma_note"),
    StoryParams(place="porch", detective_name="Nora", helper_name="Ezra", culprit_name="Owen", item="kite", clue="comma_note"),
]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    if ok:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("Mismatch:")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.to_json()
        print("OK: smoke test story generation succeeded.")
    except Exception as e:
        print(f"Smoke test failed: {e}")
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
