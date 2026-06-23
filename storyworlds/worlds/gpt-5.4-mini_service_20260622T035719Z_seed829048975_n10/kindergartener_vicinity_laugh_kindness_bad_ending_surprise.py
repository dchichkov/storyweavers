#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


def _lazy_asp():
    import asp  # type: ignore
    return asp


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    nearby: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    answer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Outcome:
    id: str
    label: str
    surprise_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, s: str) -> None:
        if s:
            self.paragraphs[-1].append(s)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = {k: asdict(v) and __import__("copy").deepcopy(v) for k, v in self.entities.items()}
        w.facts = __import__("copy").deepcopy(self.facts)
        w.history = __import__("copy").deepcopy(self.history)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    clue: str
    outcome: str
    name: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "hallway": Place("hallway", "the hallway", "near the classroom door", "quiet", {"find", "listen"}),
    "porch": Place("porch", "the porch", "near the steps", "windy", {"find", "listen"}),
    "garden": Place("garden", "the garden edge", "near the fence", "leafy", {"find", "listen"}),
    "vicinity": Place("vicinity", "the nearby vicinity", "right by the fence", "still", {"find", "listen"}),
}

CLUES = {
    "footprint": Clue("footprint", "a small footprint", "a small footprint in the dust", "a shoe had been there", {"dust", "foot"}),
    "ribbon": Clue("ribbon", "a blue ribbon", "a blue ribbon on a bush", "someone dropped it in a hurry", {"ribbon"}),
    "crumbs": Clue("crumbs", "a trail of crumbs", "a trail of crumbs along the path", "something had been carried past there", {"crumbs"}),
}

OUTCOMES = {
    "bad": Outcome("bad", "bad ending", "Then came a surprise: the clue led to the wrong door.", "The surprise was kind, but the ending was bad because the missing little box was gone for good.", {"surprise", "bad"}),
}


GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Noah", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for p in PLACES:
        for c in CLUES:
            for o in OUTCOMES:
                combos.append((p, c, o))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld: kind kindness, a clue, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("-n", "--n", type=int, default=1)
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
              and (args.outcome is None or c[2] == args.outcome)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, outcome = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice(["Ms. Reed", "Mr. Lane", "the librarian", "the neighbor"])
    return StoryParams(place=place, clue=clue, outcome=outcome, name=name, helper=helper)


def _do_find(world: World, child: Entity, clue: Clue, place: Place) -> None:
    child.memes["curiosity"] += 1
    child.memes["hope"] += 1
    world.say(f"{child.id}, a kindergartener, went quietly into {place.label} and looked around.")
    world.say(f"{place.mood.capitalize()} air hung in the {place.label}, and {child.id} noticed {clue.phrase}.")


def _do_kindness(world: World, child: Entity, helper: Entity, clue: Clue) -> None:
    child.memes["kindness"] += 1
    helper.memes["trust"] += 1
    world.say(f"{child.id} smiled and showed {helper.pronoun('object')} the clue instead of keeping it secret.")
    world.say(f"That little kindness made {helper.id} relax and laugh softly in the quiet room.")


def _do_surprise(world: World, child: Entity, clue: Clue, outcome: Outcome, helper: Entity) -> None:
    child.memes["surprise"] += 1
    world.say(outcome.surprise_line)
    world.say(f"{helper.id} frowned, because the clue meant {clue.answer}, but it pointed somewhere empty.")


def _do_bad_ending(world: World, child: Entity, helper: Entity, outcome: Outcome) -> None:
    child.memes["sadness"] += 1
    helper.memes["sadness"] += 1
    world.say(f"{child.id} gave a small laugh that sounded nervous, then looked down at the bare floor.")
    world.say(outcome.ending_line)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in GIRL_NAMES else "boy", role="kindergartener"))
    helper = world.add(Entity(id="Helper", kind="character", type="woman", label=params.helper))
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    outcome = OUTCOMES[params.outcome]

    world.facts.update(child=child, helper=helper, place=place, clue=clue, outcome=outcome)
    _do_find(world, child, clue, place)
    world.para()
    _do_kindness(world, child, helper, clue)
    _do_surprise(world, child, clue, outcome, helper)
    world.para()
    _do_bad_ending(world, child, helper, outcome)
    world.event("ended", result="bad")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, place, clue = f["child"], f["place"], f["clue"]
    return [
        f'Write a short mystery for a young child named {child.id} that includes the words "kindergartener", "vicinity", and "laugh".',
        f"Tell a gentle mystery in {place.label} where {child.id} finds {clue.phrase}, shows kindness, and then a surprise changes the ending.",
        f"Write a child-friendly story about a kindergartener who searches the vicinity, laughs softly, and ends with a bad ending that still feels calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, place, clue, outcome = f["child"], f["helper"], f["place"], f["clue"], f["outcome"]
    return [
        QAItem(
            question=f"Where did {child.id} look for the clue?",
            answer=f"{child.id} looked in {place.label}, because the mystery seemed to begin in that nearby place. The clue was sitting there before anyone understood what it meant.",
        ),
        QAItem(
            question=f"Why did {child.id} show {helper.id} the clue?",
            answer=f"{child.id} showed {helper.id} the clue because {child.id} was being kind and wanted help. That kindness made it easier to notice the surprise, even though the ending stayed bad.",
        ),
        QAItem(
            question=f"What made the ending a bad one?",
            answer=f"The clue pointed to the wrong place, so the missing thing was not recovered. The surprise was interesting, but it did not fix the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a kindergartener?", "A kindergartener is a very young child who is usually in the first school years."),
        QAItem("What does vicinity mean?", "Vicinity means the nearby area around a place."),
        QAItem("What does laugh mean?", "To laugh means to make a happy or playful sound because something feels funny."),
        QAItem("What is a mystery?", "A mystery is a story where someone tries to figure something out that is not clear at first."),
        QAItem("What is kindness?", "Kindness means being gentle, helpful, and caring toward someone else."),
        QAItem("What is a surprise?", "A surprise is something unexpected that suddenly happens."),
    ]


ASP_RULES = r"""
combo(P,C,O) :- place(P), clue(C), outcome(O).
"""


def asp_facts() -> str:
    asp = _lazy_asp()
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for o in OUTCOMES:
        lines.append(asp.fact("outcome", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    asp = _lazy_asp()
    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, outcome=None, name=None, helper=None), random.Random(777)))
        assert sample.story
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        ok = False
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.outcome not in OUTCOMES:
        raise StoryError("Invalid params.")
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, dict(e.meters), dict(e.memes))
    if qa:
        print()
        for q in sample.prompts:
            print(q)
        print()
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show combo/3."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, clue=c, outcome=o, name="Mia", helper="the neighbor")) for p, c, o in valid_combos()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
