#!/usr/bin/env python3
"""
A small mystery storyworld about an interrupted search, a brief conflict, and a careful reveal.
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
        for key in ("dust", "noise", "attention", "hidden"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "worry", "conflict", "relief", "embarrassment", "joy"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the library"
    indoor: bool = True
    afford_mystery: bool = True


@dataclass
class Mystery:
    id: str
    clue: str
    hidden: str
    interrupt: str
    turn: str
    reveal: str


@dataclass
class Object:
    id: str
    label: str
    phrase: str
    type: str
    place: str
    owner: Optional[str] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, Object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_object(self, o: Object) -> Object:
        self.objects[o.id] = o
        return o

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


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "library": Setting(place="the library", indoor=True),
    "attic": Setting(place="the attic", indoor=True),
    "museum": Setting(place="the museum", indoor=True),
    "garden": Setting(place="the garden shed", indoor=False),
}

MYSTERIES = {
    "lost_note": Mystery(
        id="lost_note",
        clue="a tiny folded note under a blue book",
        hidden="the note was the map to the missing key",
        interrupt="a loud sneeze interrupted the search",
        turn="the sneeze blew the note out from under the book",
        reveal="the note led them straight to the key in a teacup",
    ),
    "missing_key": Mystery(
        id="missing_key",
        clue="a silver key mark on the dust near the shelf",
        hidden="the key had been tucked inside a cracked jar",
        interrupt="someone knocked over a stack of papers",
        turn="the falling papers uncovered the jar behind the lamp",
        reveal="the jar held the key the whole time",
    ),
    "quiet_toy": Mystery(
        id="quiet_toy",
        clue="a toy rabbit with one bent ear",
        hidden="the rabbit had been hidden inside a basket",
        interrupt="a cat jumped onto the chair",
        turn="the cat pawed the basket right onto the floor",
        reveal="the basket opened and the rabbit hopped out",
    ),
}

HEROES = {
    "girl": ["Mina", "Ivy", "June", "Luna", "Nora"],
    "boy": ["Eli", "Noah", "Theo", "Milo", "Finn"],
}
HELPERS = {
    "girl": ["Pia", "Sage", "Ruby", "Ada"],
    "boy": ["Owen", "Leo", "Ben", "Reed"],
}


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_interrupt(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    mystery = world.facts["mystery"]
    sig = ("interrupt", mystery.id)
    if sig in world.fired:
        return out
    if hero.memes["curiosity"] >= THRESHOLD:
        world.fired.add(sig)
        hero.memes["worry"] += 1
        world.facts["interrupted"] = True
        out.append(mystery.interrupt)
    return out


def _r_conflict(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    if world.facts.get("interrupted") and ("conflict", hero.id) not in world.fired:
        world.fired.add(("conflict", hero.id))
        hero.memes["conflict"] += 1
        helper.memes["worry"] += 1
        out.append(f"{hero.id} and {helper.id} frowned at each other for a moment.")
    return out


def _r_turn(world: World) -> list[str]:
    out = []
    mystery = world.facts["mystery"]
    if world.facts.get("interrupted") and ("turn", mystery.id) not in world.fired:
        world.fired.add(("turn", mystery.id))
        world.facts["turned"] = True
        out.append(mystery.turn)
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    if world.facts.get("turned") and ("reveal", mystery.id) not in world.fired:
        world.fired.add(("reveal", mystery.id))
        hero.memes["joy"] += 1
        hero.memes["relief"] += 1
        helper.memes["joy"] += 1
        helper.memes["relief"] += 1
        hero.memes["conflict"] = 0.0
        helper.memes["worry"] = 0.0
        out.append(mystery.reveal)
    return out


CAUSAL_RULES = [
    Rule("interrupt", _r_interrupt),
    Rule("conflict", _r_conflict),
    Rule("turn", _r_turn),
    Rule("reveal", _r_reveal),
]


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


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add_entity(Entity(id=params.hero, kind="character", type="girl" if params.hero in HEROES["girl"] else "boy"))
    helper = world.add_entity(Entity(id=params.helper, kind="character", type="girl" if params.helper in HELPERS["girl"] else "boy"))
    object_name = "box"
    if mystery.id == "lost_note":
        obj = world.add_object(Object(id="book", label="blue book", phrase="a blue book", type="book", place=setting.place))
    elif mystery.id == "missing_key":
        obj = world.add_object(Object(id="lamp", label="lamp", phrase="the lamp", type="lamp", place=setting.place))
    else:
        obj = world.add_object(Object(id="basket", label="basket", phrase="a basket", type="basket", place=setting.place))

    world.facts.update(hero=hero, helper=helper, mystery=mystery, object=obj)

    hero.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1

    world.say(f"{hero.id} and {helper.id} were in {setting.place}, looking for a clue.")
    world.say(f"They noticed {mystery.clue}.")
    world.para()
    world.say(f"{hero.id} wanted to solve the mystery carefully, but {helper.id} had a different idea.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"At last, the clue led them onward.")
    if world.facts.get("interrupted"):
        world.say(f"The final answer felt simple once the trouble passed: {mystery.hidden}.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    return [
        f'Write a short mystery story for a young child that includes the word "interrupt".',
        f"Tell a gentle story where {hero.id} and {helper.id} search for a clue in {world.setting.place} and then face a small conflict.",
        f"Write a simple mystery with a clear clue, an interruption, and a reveal about {mystery.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    obj = f["object"]
    return [
        QAItem(
            question=f"Where were {hero.id} and {helper.id} when they started looking for the clue?",
            answer=f"They were in {world.setting.place}, looking carefully for a sign of what was hidden.",
        ),
        QAItem(
            question=f"What clue did they notice before the interruption?",
            answer=f"They noticed {mystery.clue}. That clue was the first sign that the mystery could be solved.",
        ),
        QAItem(
            question=f"What caused the conflict in the middle of the story?",
            answer=f"The conflict began when {mystery.interrupt}. That interruption made the search feel messy for a moment.",
        ),
        QAItem(
            question=f"What helped them finish the mystery at the end?",
            answer=f"The turning point was when {mystery.turn}. After that, they could see that {mystery.reveal}.",
        ),
        QAItem(
            question=f"What object was important in the story?",
            answer=f"The important object was {obj.phrase}, because it helped point them toward the hidden answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what is going on.",
        ),
        QAItem(
            question="What does interrupt mean?",
            answer="To interrupt means to break into something that is happening and make it stop or change for a moment.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the part where characters want different things or run into a problem before things get better.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: {e.type} meters={meters} memes={memes}")
    lines.append(f"facts: {sorted(world.facts.keys())}")
    lines.append(f"fired: {sorted(world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the requested options do not describe a reasonable mystery.)"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for mystery in MYSTERIES:
            for gender in ("girl", "boy"):
                out.append((place, mystery, gender))
    return out


@dataclass
class ASPItem:
    pass


ASP_RULES = r"""
interrupt(M) :- mystery(M), clue(M).
conflict(H) :- hero(H), interrupt(_).
turn(M) :- mystery(M), interrupt(M).
reveal(M) :- mystery(M), turn(M).
valid(P, M, G) :- setting(P), mystery(M), hero_gender(G).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for g in ("girl", "boy"):
        lines.append(asp.fact("hero_gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(python_set - asp_set))
    print("  only in clingo:", sorted(asp_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with an interrupt and a conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError(explain_rejection())
    place, mystery, gender = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES[gender])
    helper = args.helper or rng.choice([h for h in HELPERS[gender] if h != hero])
    return StoryParams(place=place, mystery=mystery, hero=hero, helper=helper)


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="library", mystery="lost_note", hero="Mina", helper="Pia"),
            StoryParams(place="attic", mystery="missing_key", hero="Eli", helper="Owen"),
            StoryParams(place="museum", mystery="quiet_toy", hero="Ivy", helper="Ruby"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
