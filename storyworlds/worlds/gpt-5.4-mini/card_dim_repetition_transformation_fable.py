#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/card_dim_repetition_transformation_fable.py
===========================================================================

A small, standalone story world for a fable-like tale about a child, a dim
card, patient repetition, and a transformation that makes the ending brighter.

The domain is deliberately tiny:
- a child finds a dim card
- the child repeats a careful act several times
- the card transforms into a clearer, brighter keepsake
- the story ends with a fable-style lesson about patience

The repeated action and the transformation are modeled as world state, not as a
frozen paragraph with swapped nouns.
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
REPEAT_TARGET = 3
BRIGHT_GOAL = 2.0
DIM_LIMIT = 0.8


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Card:
    id: str
    label: str
    phrase: str
    image: str
    dim_start: float = 0.6
    bright_start: float = 0.0
    can_transform: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Action:
    id: str
    label: str
    repeat_need: int
    brighten: float
    transform_text: str
    failure_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    card = world.entities.get("card")
    if not kid or not card:
        return out
    if kid.meters["tries"] < REPEAT_TARGET:
        return out
    sig = ("repeat_ready",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["patience"] += 1
    card.memes["trust"] += 1
    out.append("__repeat__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    card = world.entities.get("card")
    kid = world.entities.get("child")
    if not card or not kid:
        return out
    if kid.meters["tries"] < REPEAT_TARGET:
        return out
    if card.meters["brightness"] < BRIGHT_GOAL:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    card.meters["transformed"] = 1
    out.append("__transform__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("repeat", "social", _r_repeat),
    Rule("transform", "physical", _r_transform),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_try(world: World, child: Entity, action: Action, card: Entity, narrate: bool = True) -> None:
    child.meters["tries"] += 1
    child.memes["hope"] += 1
    card.meters["brightness"] += action.brighten
    propagate(world, narrate=narrate)


def predict_outcome(world: World, action: Action) -> dict:
    sim = world.copy()
    _do_try(sim, sim.get("child"), action, sim.get("card"), narrate=False)
    return {
        "tries": sim.get("child").meters["tries"],
        "bright": sim.get("card").meters["brightness"],
        "transformed": sim.get("card").meters["transformed"] >= THRESHOLD,
    }


def tell_setup(world: World, child: Entity, card: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"One morning, {child.id} found {card.phrase} at the edge of the path. "
        f"It was {card.image}, dim as a whistle in the fog."
    )
    world.say(
        f'{child.id} held it in both hands and said, "If I care for it, maybe it '
        f"will shine again."
    )


def repeat_beat(world: World, child: Entity, action: Action, card: Entity) -> None:
    world.say(
        f"{child.id} did not rush. {child.pronoun().capitalize()} tried {action.label} "
        f"once, then again, then again."
    )
    world.say(
        f"Each time, the little card grew a touch brighter, and {child.id} learned "
        f"that small steps can do what a single hurry cannot."
    )


def transform_beat(world: World, child: Entity, card: Entity, action: Action) -> None:
    if card.meters["transformed"] < THRESHOLD:
        return
    world.say(
        f"At last, the dim card transformed. The faded picture turned clear, and "
        f"a gold edge appeared where only gray had been before."
    )
    world.say(
        f"{child.id} smiled, because {action.transform_text}."
    )


def lesson(world: World, child: Entity, card: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["wisdom"] += 1
    world.say(
        f"{card.label_word.capitalize()} became a bright keepsake in {child.id}'s "
        f"pocket, and {child.id} promised to be patient with hard things."
    )
    world.say(
        "The little fable ended with a gentle lesson: repeated care can bring a "
        "quiet transformation."
    )


def tell(action: Action, card: Card, child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))
    c = world.add(Entity(id="card", type="thing", label=card.label, phrase=card.phrase))
    c.meters["brightness"] = card.dim_start
    c.meters["transformed"] = 0.0
    c.memes["trust"] = card.bright_start

    tell_setup(world, child, c)
    world.para()
    world.say(
        f"{child.id}'s {parent.label_word} watched and said, "
        f'"Try again gently. Some things wake up slowly."'
    )
    for i in range(action.repeat_need):
        _do_try(world, child, action, c)
        if i + 1 < action.repeat_need:
            world.say(f"{child.id} tried once more.")
    world.para()
    repeat_beat(world, child, action, c)
    transform_beat(world, child, c, action)
    lesson(world, child, c)
    world.facts.update(
        child=child, parent=parent, card=c, action=action,
        repeated=child.meters["tries"] >= REPEAT_TARGET,
        transformed=c.meters["transformed"] >= THRESHOLD,
    )
    return world


CARDS = {
    "postcard": Card("postcard", "postcard", "a little postcard", "a dim picture of a boat"),
    "bookmark": Card("bookmark", "bookmark", "a narrow bookmark", "a dim drawing of a fox"),
    "note": Card("note", "note", "a folded note", "a dim sketch of a star"),
}

ACTIONS = {
    "rub": Action("rub", "rub the card with a soft cloth", 3, 0.8,
                  "the smudges faded little by little",
                  "the cloth could not help"),
    "polish": Action("polish", "polish it with care", 3, 0.75,
                     "the dullness turned to a soft shine",
                     "there was not enough shine yet"),
}

NAMES_GIRL = ["Mina", "Lila", "Tia", "Nora", "Ivy"]
NAMES_BOY = ["Pico", "Oren", "Tobi", "Nico", "Eli"]


@dataclass
@dataclass
class StoryParams:
    card: str
    action: str
    child: str
    child_gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for cid, card in CARDS.items():
        if card.can_transform:
            for aid in ACTIONS:
                combos.append((cid, aid))
    return combos


def explain_rejection(card: Card, action: Action) -> str:
    return f"(No story: {action.label} cannot reasonably transform {card.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about a dim card, repetition, and transformation.")
    ap.add_argument("--card", choices=CARDS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child")
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
    if args.card and args.action:
        if (args.card, args.action) not in valid_combos():
            raise StoryError(explain_rejection(CARDS[args.card], ACTIONS[args.action]))
    combos = [c for c in valid_combos()
              if (args.card is None or c[0] == args.card)
              and (args.action is None or c[1] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    card, action = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(card, action, child, gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a young child that includes the words "card-dim" and tells how {f["child"].id} made a dim card brighter by repeating a careful action.',
        f"Tell a gentle story where {f['child'].id} finds a card that is card-dim, keeps trying, and watches it transform into something bright and useful.",
        f'Write a short story with repetition and transformation in a fable style, ending with a lesson about patience and care.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, card, action = f["child"], f["parent"], f["card"], f["action"]
    qa = [
        ("What did the child find?",
         f"{child.id} found {card.phrase}, and it was card-dim at first."),
        ("What did the child do over and over?",
         f"{child.id} repeated {action.label}. {child.id} did it several times before the change happened."),
        ("How did the parent help?",
         f"{parent.label_word.capitalize()} told {child.id} to try again gently. That encouragement helped the child keep going until the card changed."),
    ]
    if f["transformed"]:
        qa.append((
            "What changed by the end?",
            f"The dim card transformed into a brighter keepsake. The picture became clear, and the child could see the gold edge that was hidden before."
        ))
        qa.append((
            "What lesson did the story teach?",
            "It taught that patient repetition can help something change for the better. Small careful steps can make a big difference."
        ))
    return qa


WORLD_KNOWLEDGE = {
    "card": [("What is a card?",
              "A card is a small flat piece of paper or cardboard. People can write on it, draw on it, or keep it as a little keepsake.")],
    "dim": [("What does dim mean?",
             "Dim means not very bright or not easy to see. A dim thing needs more light or care before it looks clear.")],
    "repeat": [("Why do people repeat things?",
                "People repeat things to practice, to learn, or to help something change little by little.")],
    "transform": [("What does transform mean?",
                   "Transform means to change into something different. Sometimes the change is small, and sometimes it is big.")],
    "patience": [("What is patience?",
                  "Patience means waiting and trying again without getting upset. It helps when things take time.")],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    keys = ["card", "dim", "repeat", "transform", "patience"]
    out = []
    for k in keys:
        out.extend(WORLD_KNOWLEDGE[k])
    return out


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
repeat_ready :- tries(T), repeat_target(R), T >= R.
transformed :- repeat_ready, bright(B), bright_goal(G), B >= G.
valid(C,A) :- card(C), action(A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for cid in CARDS:
        lines.append(asp.fact("card", cid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    lines.append(asp.fact("repeat_target", REPEAT_TARGET))
    lines.append(asp.fact("bright_goal", BRIGHT_GOAL))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in ASP combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("postcard", "rub", "Mina", "girl", "mother"),
    StoryParams("bookmark", "polish", "Oren", "boy", "father"),
    StoryParams("note", "rub", "Lila", "girl", "mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(CARDS[params.card], ACTIONS[params.action], params.child, params.child_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
if __name__ == "__main__":
    main()
