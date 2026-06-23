#!/usr/bin/env python3
"""
A small fable-like storyworld: two friends find a tennis court already occupied,
then choose a kinder plan and share the space. The story keeps a child-friendly
fable tone, includes the required words "occupy" and "tennis", and ends in a
happy friendship image.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str | None = None
    caretaker: str | None = None
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
class StoryParams:
    place: str
    court: str
    occupier: str
    requester: str
    helper: str
    animal: str
    seed: int | None = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: Entity(**{
            **{f: getattr(v, f) for f in ("id","kind","type","label","phrase","traits","role","owner","caretaker","plural","tags","attrs")},
            "meters": defaultdict(float, dict(v.meters)),
            "memes": defaultdict(float, dict(v.memes)),
        }) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: Any


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["shared_space"] < THRESHOLD:
            continue
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["joy"] += 1
        out.append(f"{ent.id} smiled because the court was shared fairly.")
    return out


CAUSAL_RULES = [Rule("relief", _r_relief)]


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


@dataclass
class Setting:
    place: str
    court_name: str


@dataclass
class Court:
    label: str
    occupied_by: str = ""
    can_share: bool = True


@dataclass
class Animal:
    id: str
    type: str
    label: str
    phrase: str
    kindness: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "meadow": Setting(place="the meadow", court_name="the old tennis court"),
    "orchard": Setting(place="the orchard", court_name="the little tennis court"),
    "village": Setting(place="the village green", court_name="the bright tennis court"),
}

ANIMALS = {
    "rabbit": Animal(id="rabbit", type="rabbit", label="rabbit", phrase="a quick rabbit", kindness="gentle", tags={"friendship", "tennis"}),
    "fox": Animal(id="fox", type="fox", label="fox", phrase="a clever fox", kindness="polite", tags={"friendship", "tennis"}),
    "hare": Animal(id="hare", type="hare", label="hare", phrase="a lively hare", kindness="warm", tags={"friendship", "tennis"}),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Tia", "Sora"]
BOY_NAMES = ["Pip", "Theo", "Bram", "Jules", "Oren"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for court in ("court",):
            for occupier in ANIMALS:
                for requester in ANIMALS:
                    if requester != occupier:
                        combos.append((place, court, occupier, requester))
    return combos


def safe_combo(params: StoryParams) -> bool:
    return params.occupier in ANIMALS and params.requester in ANIMALS and params.occupier != params.requester


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the court arrangement needs two different animals so the fable has a true conflict and a fair ending.)"


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.place]
    occupier = world.add(Entity(id="occupier", kind="character", type=params.occupier, label=params.occupier, phrase=ANIMALS[params.occupier].phrase, traits=["busy"], tags={"friendship", "tennis"}))
    requester = world.add(Entity(id="requester", kind="character", type=params.requester, label=params.requester, phrase=ANIMALS[params.requester].phrase, traits=["kind"], tags={"friendship", "tennis"}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper, phrase=ANIMALS[params.helper].phrase, traits=["wise"], tags={"friendship", "tennis"}))
    court = world.add(Entity(id="court", type="place", label=setting.court_name, phrase=setting.court_name, attrs={"place": setting.place, "game": "tennis"}))

    world.facts.update(setting=setting, occupier=occupier, requester=requester, helper=helper, court=court)

    world.say(f"In {setting.place}, {occupier.ref()} had chosen to occupy {setting.court_name}, because the morning was fine and the {court.label} looked perfect for tennis.")
    world.say(f"{requester.ref()} arrived with a small ball and asked if {requester.pronoun()} could play tennis too.")
    world.para()
    requester.memes["want"] += 1
    occupier.memes["pride"] += 1
    world.say(f"At first, {occupier.id} stayed firm, but {helper.ref()} reminded the two friends that a field is happier when it welcomes more than one heart.")
    world.say(f"Then {helper.id} offered a simple game: they would take turns serving and counting points, so nobody would be left out.")
    requester.meters["shared_space"] += 1
    occupier.meters["shared_space"] += 1
    helper.meters["shared_space"] += 1
    propagate(world, narrate=True)
    world.para()
    requester.memes["joy"] += 1
    occupier.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"The friends laughed, the ball skipped over the lines, and the {court.label} rang with tennis instead of quarrels.")
    world.say(f"By sunset, {occupier.id} and {requester.id} had shared the court kindly, and the little fable ended with friendship growing stronger than the need to occupy anything alone.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    return [
        f'Write a short fable for a child about friendship, tennis, and how to share a place when someone tries to occupy it.',
        f'Tell a happy-ending story set in {setting.place} where two animals learn to share {setting.court_name} for tennis.',
        f'Write a gentle fable that includes the words "occupy" and "tennis" and ends with friends playing together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s = f["setting"]
    o = f["occupier"]
    r = f["requester"]
    h = f["helper"]
    c = f["court"]
    return [
        QAItem(
            question=f"Who occupied {c.label} at the start of the story?",
            answer=f"{o.ref()} occupied {c.label} first. That created the problem, because {r.ref()} also wanted to play tennis there."
        ),
        QAItem(
            question=f"How did {h.ref()} help the friends?",
            answer=f"{h.ref()} suggested that they take turns and share the court. That kind idea turned the disagreement into a fair game."
        ),
        QAItem(
            question=f"How did the story end in {s.place}?",
            answer=f"It ended happily, with {o.ref()} and {r.ref()} laughing together at {c.label}. Their friendship became stronger than the wish to occupy the space alone."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does occupy mean?",
            answer="To occupy something means to be in it or use it for a time. In a story, it can cause trouble if someone wants the same place."
        ),
        QAItem(
            question="What is tennis?",
            answer="Tennis is a game where players hit a ball back and forth with rackets. It can be shared when friends take turns."
        ),
        QAItem(
            question="Why is friendship important in a fable?",
            answer="Friendship helps characters choose kindness, fairness, and peace. Fables often show that a good choice leaves everyone happier."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"history={world.history}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like storyworld about friendship and a tennis court.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--occupier", choices=ANIMALS.keys())
    ap.add_argument("--requester", choices=ANIMALS.keys())
    ap.add_argument("--helper", choices=ANIMALS.keys())
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
    if args.occupier and args.requester and args.occupier == args.requester:
        raise StoryError("The occupier and requester must be different so the story has a true friendship choice.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.occupier:
        combos = [c for c in combos if c[2] == args.occupier]
    if args.requester:
        combos = [c for c in combos if c[3] == args.requester]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, court, occupier, requester = rng.choice(sorted(combos))
    helper_choices = [a for a in ANIMALS if a not in {occupier, requester}]
    helper = args.helper if args.helper else rng.choice(helper_choices)
    return StoryParams(place=place, court=court, occupier=occupier, requester=requester, helper=helper, animal=occupier)


def generate(params: StoryParams) -> StorySample:
    if not safe_combo(params):
        raise StoryError(explain_rejection(params))
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


ASP_RULES = r"""
valid(P, O, R, H) :- place(P), animal(O), animal(R), animal(H), O != R, H != O, H != R.
happy_end(P, O, R, H) :- valid(P, O, R, H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    ok = True
    if py != asp_set:
        ok = False
        print("MISMATCH:", sorted(py ^ asp_set))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story and sample.prompts
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        ok = False
    if ok:
        print(f"OK: verify passed with {len(py)} combos.")
        return 0
    return 1


CURATED = [
    StoryParams(place="meadow", court="court", occupier="rabbit", requester="fox", helper="hare", animal="rabbit"),
    StoryParams(place="orchard", court="court", occupier="hare", requester="rabbit", helper="fox", animal="hare"),
    StoryParams(place="village", court="court", occupier="fox", requester="hare", helper="rabbit", animal="fox"),
]


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base + i))
            p.seed = base + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
