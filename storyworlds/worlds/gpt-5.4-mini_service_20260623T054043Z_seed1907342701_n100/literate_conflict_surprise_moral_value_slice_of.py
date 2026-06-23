#!/usr/bin/env python3
"""
storyworlds/worlds/literate_conflict_surprise_moral_value_slice_of.py
=====================================================================

A small slice-of-life storyworld about a literate child, a gentle conflict,
a surprising turn, and a moral-value ending. The domain stays small on purpose:
a child wants to do a reading-related task, an adult worries about a real-world
risk, something unexpected changes the situation, and the story ends with a
quiet image proving what changed.

Seed premise:
- The word "literate" must appear naturally.
- Features: conflict, surprise, moral value.
- Style: slice of life.

The world centers on a child, a place, a reading task, a book-like object, a
small helper, and a surprise item. The stories are built from world state, not
from a fixed paragraph template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    owner: str = ""
    caretaker: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    cozy: bool = True
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BookishObject:
    id: str
    label: str
    phrase: str
    risk: str
    zone: str
    fixable_by: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    reveal: str
    helps: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    outcome: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.zone: str = ""

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = self.zone
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _apply_reading(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    task: Task = world.facts["task"]
    obj: BookishObject = world.facts["object"]
    if child.meters["desire"] < THRESHOLD:
        return out
    if world.zone != task.zone:
        return out
    sig = ("risk", obj.id, task.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obj.meters[task.risk] += 1
    obj.meters["touched"] += 1
    if task.risk == "wet":
        obj.meters["warped"] += 1
        out.append(f"The {obj.label} curled at the edges from the damp air.")
    else:
        obj.meters["creased"] += 1
        out.append(f"The {obj.label} bent a little from too much handling.")
    return out


def _apply_surprise(world: World) -> list[str]:
    out: list[str] = []
    surprise: Surprise = world.facts["surprise"]
    if world.facts.get("surprised"):
        return out
    if surprise.helps:
        world.facts["surprised"] = True
        out.append(f"Inside the {world.facts['object'].label}, there was {surprise.reveal}.")
    return out


def _apply_fix(world: World) -> list[str]:
    out: list[str] = []
    obj: BookishObject = world.facts["object"]
    fix: Fix | None = world.facts.get("fix")
    helper: Entity = world.facts["helper"]
    if not fix:
        return out
    if obj.meters["wet"] < THRESHOLD and obj.meters["creased"] < THRESHOLD:
        return out
    sig = ("fix", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obj.meters["saved"] += 1
    helper.memes["care"] += 1
    out.append(f"{helper.label_word.capitalize()} used {fix.label} to help.")
    return out


CAUSAL_RULES = [_apply_reading, _apply_surprise, _apply_fix]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_story(place: Place, task: Task, obj: BookishObject) -> bool:
    return task.zone in place.supports and task.risk == obj.risk and obj.zone == task.zone


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, task in TASKS.items():
            for oid, obj in OBJECTS.items():
                if can_story(place, task, obj) and task.id in obj.fixable_by:
                    combos.append((pid, tid, oid))
    return combos


@dataclass
class StoryParams:
    place: str = ""
    task: str = ""
    object: str = ""
    surprise: str = ""
    fix: str = ""
    child_name: str = ""
    child_gender: str = ""
    helper_name: str = ""
    helper_gender: str = ""
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen table", cozy=True, supports={"table"}),
    "porch": Place(id="porch", label="the porch bench", cozy=True, supports={"bench"}),
    "nook": Place(id="nook", label="the reading nook", cozy=True, supports={"chair"}),
    "library": Place(id="library", label="the little library corner", cozy=True, supports={"chair", "bench", "table"}),
}

TASKS = {
    "read": Task(id="read", verb="read", gerund="reading", risk="creased", zone="chair", clue="a quiet page"),
    "copy": Task(id="copy", verb="copy", gerund="copying", risk="creased", zone="table", clue="a neat line"),
    "write_note": Task(id="write_note", verb="write a note", gerund="writing notes", risk="creased", zone="bench", clue="a short sentence"),
    "sort_cards": Task(id="sort_cards", verb="sort cards", gerund="sorting cards", risk="wet", zone="table", clue="a careful stack"),
}

OBJECTS = {
    "storybook": BookishObject(id="storybook", label="storybook", phrase="a favorite storybook", risk="creased", zone="chair", fixable_by={"read", "write_note"}),
    "notebook": BookishObject(id="notebook", label="notebook", phrase="a blue notebook", risk="creased", zone="table", fixable_by={"copy", "write_note"}),
    "cards": BookishObject(id="cards", label="index cards", phrase="a pack of index cards", risk="wet", zone="table", fixable_by={"sort_cards"}),
    "recipe": BookishObject(id="recipe", label="recipe card", phrase="a recipe card", risk="wet", zone="table", fixable_by={"copy", "sort_cards"}),
}

SURPRISES = {
    "bookmark_note": Surprise(id="bookmark_note", label="bookmark note", reveal="a tiny bookmark with a thank-you note", helps=True, tags={"note", "bookmark"}),
    "spare_page": Surprise(id="spare_page", label="spare page", reveal="a spare page tucked in the back", helps=True, tags={"page"}),
    "sticker": Surprise(id="sticker", label="sticker", reveal="a bright sticker of a smiling star", helps=False, tags={"sticker"}),
    "receipt": Surprise(id="receipt", label="receipt", reveal="a grocery receipt folded into a square", helps=False, tags={"paper"}),
}

FIXES = {
    "towel": Fix(id="towel", label="a dry towel", prep="dry", outcome="dried"),
    "tape": Fix(id="tape", label="paper tape", prep="patch", outcome="patched"),
    "press": Fix(id="press", label="a heavy book to press it flat", prep="press", outcome="flattened"),
}

CHILD_NAMES = ["Mia", "Nora", "Leo", "Finn", "Ava", "Eli", "Lina", "Owen"]
HELPER_NAMES = ["Mom", "Dad", "Aunt June", "Mr. Hale", "Ms. Inez"]

TRAITS = ["literate", "careful", "curious", "patient", "book-loving"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    task: Task = f["task"]
    obj: BookishObject = f["object"]
    surprise: Surprise = f["surprise"]
    return [
        f'Write a slice-of-life story about a literate child named {child.id} who wants to {task.verb} with {obj.phrase}.',
        f"Tell a gentle story where {child.id} and {f['helper'].label_word} disagree about {obj.label}, then find a calmer way after a surprise appears.",
        f'Write a short everyday story that includes the word "literate" and ends with {surprise.reveal.lower()}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    task: Task = f["task"]
    obj: BookishObject = f["object"]
    surprise: Surprise = f["surprise"]
    fix: Fix | None = f.get("fix")
    qa = [
        QAItem(
            question=f"Who is the story about when {child.id} wants to {task.verb}?",
            answer=f"It is about {child.id}, a literate child who likes quiet reading-time things. {helper.label_word.capitalize()} is part of the story too because they help with the problem.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with {obj.label} in the {world.place.label}?",
            answer=f"{child.id} wanted to {task.verb} with {obj.phrase}. That mattered because the task fit the place and the object could be affected by it.",
        ),
        QAItem(
            question=f"Why did {helper.label_word.capitalize()} worry about {obj.label}?",
            answer=f"{helper.label_word.capitalize()} worried because {obj.label} could get {task.risk} during {task.gerund}. They were trying to keep the object in good shape, not spoil the fun.",
        ),
    ]
    if f.get("surprised"):
        qa.append(QAItem(
            question=f"What surprise did {child.id} find?",
            answer=f"{child.id} found {surprise.reveal}. It changed the mood because the unexpected thing turned the problem into something kinder.",
        ))
    if fix:
        qa.append(QAItem(
            question=f"How did {helper.label_word.capitalize()} help with {obj.label}?",
            answer=f"{helper.label_word.capitalize()} used {fix.label} so the object could be cared for after the rough moment. That was the practical part of the solution.",
        ))
        qa.append(QAItem(
            question=f"How did {child.id} feel after the problem was solved?",
            answer=f"{child.id} felt calmer and glad. The ending showed a small, peaceful change: {obj.label} was safe again and the room was tidy.",
        ))
    else:
        qa.append(QAItem(
            question=f"What did the story prove at the end?",
            answer=f"It proved that a small surprise can change a disagreement without making the day bad. The final image is a quiet one, with the important thing still in good shape.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags) | set(world.facts["surprise"].tags) | {"literate"}
    out: list[QAItem] = []
    if "literate" in tags:
        out.append(QAItem(
            question="What does literate mean?",
            answer="Literate means a person can read and write. It usually means books, notes, and letters are things they can handle with confidence.",
        ))
    if "note" in tags:
        out.append(QAItem(
            question="Why do people leave notes in books?",
            answer="People leave notes to remind, thank, or mark a page. A note can help someone remember something kind or useful.",
        ))
    if "bookmark" in tags:
        out.append(QAItem(
            question="What is a bookmark for?",
            answer="A bookmark shows where you stopped reading. It helps you find the same page again later without folding the book.",
        ))
    if "page" in tags:
        out.append(QAItem(
            question="What is a spare page?",
            answer="A spare page is an extra page kept in case one gets torn or missing. It can help a book stay complete.",
        ))
    return out


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
    lines.append("== (3) World knowledge ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(place: Place, task: Task, obj: BookishObject, surprise: Surprise, fix: Fix,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, label=child_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, label=helper_name))
    book = world.add(Entity(id=obj.id, type="thing", label=obj.label, phrase=obj.phrase))
    world.facts.update(child=child, helper=helper, object=obj, task=task, surprise=surprise, fix=fix, book=book)
    world.zone = task.zone

    child.memes["joy"] += 1
    child.memes["love"] += 1
    child.memes["desire"] += 1
    helper.memes["care"] += 1

    world.say(f"{child.id} was a literate child who liked quiet moments at {place.label}.")
    world.say(f"{child.id} wanted to {task.verb} with {obj.phrase}, because {task.clue} felt just right.")
    world.say(f"At first, {helper.label_word.lower()} said {book.label_word if hasattr(book, 'label_word') else obj.label} should stay safe, and that started the conflict.")
    world.para()
    world.say(f"{child.id} reached for the {obj.label}, and the room felt very still.")
    if task.id in obj.fixable_by:
        obj.meters["wet" if task.risk == "wet" else "creased"] += 1
    if surprise.helps:
        world.say(f"Then came a surprise: {surprise.reveal}.")
        world.facts["surprised"] = True
    propagate(world, narrate=True)
    world.para()
    if surprise.helps:
        helper.meters["kindness"] += 1
        helper.memes["relief"] += 1
        world.say(f"{helper.label_word.capitalize()} smiled and used {fix.label} so the little problem would not spread.")
        obj.meters["saved"] += 1
        child.memes["calm"] += 1
        world.say(f"By the end, {child.id} put the {obj.label} back on the table, and the surprise made the whole day gentler.")
    else:
        world.say(f"The day stayed ordinary, with the {obj.label} settled neatly where it belonged.")
    world.facts["resolved"] = True
    return world


CURATED = [
    StoryParams(place="library", task="read", object="storybook", surprise="bookmark_note", fix="towel", child_name="Mia", child_gender="girl", helper_name="Mom", helper_gender="woman"),
    StoryParams(place="nook", task="copy", object="notebook", surprise="spare_page", fix="press", child_name="Leo", child_gender="boy", helper_name="Dad", helper_gender="man"),
    StoryParams(place="porch", task="write_note", object="cards", surprise="sticker", fix="tape", child_name="Ava", child_gender="girl", helper_name="Aunt June", helper_gender="woman"),
    StoryParams(place="kitchen", task="sort_cards", object="recipe", surprise="receipt", fix="towel", child_name="Finn", child_gender="boy", helper_name="Ms. Inez", helper_gender="woman"),
]


def explain_rejection(place: Place, task: Task, obj: BookishObject) -> str:
    return f"(No story: {place.label} does not fit {task.gerund} with {obj.label} in a sensible way.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a literate child, a small conflict, a surprise, and a moral-value ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy", "woman", "man"])
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
              and (args.task is None or c[1] == args.task)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, obj = rng.choice(sorted(combos))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    fix = args.fix or rng.choice(sorted(FIXES))
    if TASKS[task].id not in OBJECTS[obj].fixable_by:
        raise StoryError("(No valid fix matches this object and task.)")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place,
        task=task,
        object=obj,
        surprise=surprise,
        fix=fix,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.task not in TASKS or params.object not in OBJECTS:
        raise StoryError("(Invalid params.)")
    place = PLACES[params.place]
    task = TASKS[params.task]
    obj = OBJECTS[params.object]
    surprise = SURPRISES[params.surprise]
    fix = FIXES[params.fix]
    if not can_story(place, task, obj):
        raise StoryError(explain_rejection(place, task, obj))
    if task.id not in obj.fixable_by:
        raise StoryError("(The chosen fix does not fit the object.)")
    world = tell(place, task, obj, surprise, fix, params.child_name, params.child_gender, params.helper_name, params.helper_gender)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


ASP_RULES = r"""
valid(P,T,O) :- place(P), task(T), object(O), supports(P,Z), zone(T,Z), risk(T,R), risk(O,R), fixable(O,T).
surprised(O) :- surprise_helpful(S), chosen_surprise(S), helps(S), chosen_object(O).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for z in sorted(p.supports):
            lines.append(asp.fact("supports", pid, z))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("zone", tid, t.zone))
        lines.append(asp.fact("risk", tid, t.risk))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("zone", oid, o.zone))
        lines.append(asp.fact("risk", oid, o.risk))
        for t in sorted(o.fixable_by):
            lines.append(asp.fact("fixable", oid, t))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        if s.helps:
            lines.append(asp.fact("helps", sid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    if ok:
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: generate() smoke test passed.")
    return 0


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
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
