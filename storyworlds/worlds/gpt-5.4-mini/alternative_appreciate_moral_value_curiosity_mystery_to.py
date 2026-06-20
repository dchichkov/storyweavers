#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/alternative_appreciate_moral_value_curiosity_mystery_to.py
==========================================================================================

A tiny bedtime storyworld about a child following curiosity through a small
mystery, learning a moral value, and choosing an alternative way to solve it.

Seed words:
- alternative
- appreciate

Features:
- Moral Value
- Curiosity
- Mystery to Solve

Style:
- Bedtime Story
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
SENSE_MIN = 2


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
class Setting:
    id: str
    place: str
    bedtime: str
    quiet_detail: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Mystery:
    id: str
    clue: str
    hidden: str
    value: str
    moral: str
    question: str
    answer: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Alternative:
    id: str
    label: str
    way: str
    helps: str
    closing: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_relief(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["solved"] >= THRESHOLD and ("relief", e.id) not in world.fired:
            world.fired.add(("relief", e.id))
            e.memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def mystery_risk(mystery: Mystery) -> bool:
    return True


def best_alternative() -> Alternative:
    return max(ALTERNATIVES.values(), key=lambda a: len(a.helps))


def sensible_alternatives() -> list[Alternative]:
    return [a for a in ALTERNATIVES.values() if a.id != "wrong"]


def _solve_with(world: World, alt: Alternative, mystery: Mystery) -> None:
    solver = world.get("child")
    puzzle = world.get("mystery")
    solver.meters["solved"] += 1
    puzzle.meters["solved"] += 1
    solver.memes["joy"] += 1
    solver.memes["pride"] += 1
    world.say(
        f"{solver.id} tried {alt.way}, and {alt.helps}. "
        f"{alt.closing}."
    )
    propagate(world, narrate=False)


def predict(world: World, mystery: Mystery, alt: Alternative) -> bool:
    sim = world.copy()
    _solve_with(sim, alt, mystery)
    return sim.get("mystery").meters["solved"] >= THRESHOLD


def bedtime_setup(world: World, child: Entity, parent: Entity, setting: Setting, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At bedtime, {child.id} was tucked into {setting.place}. "
        f"{setting.bedtime} {setting.quiet_detail}."
    )
    world.say(
        f"Just then, {child.id} noticed {mystery.clue} and wondered about the little mystery."
    )


def ask_and_value(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    world.say(
        f'"What is it?" {child.id} whispered. '
        f'{parent.label_word.capitalize()} smiled and said, '
        f'"It is a chance to be curious and gentle at the same time."'
    )
    child.memes["curiosity"] += 1
    child.memes["moral_value"] += 1


def choose_alternative(world: World, child: Entity, parent: Entity, alt: Alternative, mystery: Mystery) -> None:
    world.say(
        f"{child.id} wanted to poke at it right away, but {parent.label_word} offered an "
        f"{alt.label} as an alternative."
    )
    if alt.id == "lamp":
        world.say(f"{alt.label.capitalize()} {alt.way}, so {child.id} could look without trouble.")
    else:
        world.say(f"{alt.label.capitalize()} helped {child.id} look closely and safely.")


def resolve(world: World, child: Entity, parent: Entity, mystery: Mystery, alt: Alternative) -> None:
    _solve_with(world, alt, mystery)
    world.say(
        f"At last, the mystery was solved: {mystery.answer}. "
        f"{child.id} could appreciate the kind lesson, and {parent.label_word} could appreciate the calm choice."
    )
    world.say(
        f"The room grew quiet again, and {child.id} fell asleep feeling warm, wise, and happy."
    )


def tell(setting: Setting, mystery: Mystery, alt: Alternative,
         child_name: str = "Mia", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    puzzle = world.add(Entity(id="mystery", type="mystery", label=mystery.id))
    world.facts.update(setting=setting, mystery=mystery, alternative=alt)

    bedtime_setup(world, child, parent, setting, mystery)
    world.para()
    ask_and_value(world, child, parent, mystery)
    choose_alternative(world, child, parent, alt, mystery)
    world.para()
    resolve(world, child, parent, mystery, alt)

    world.facts.update(child=child, parent=parent, puzzle=puzzle, solved=True)
    return world


SETTINGS = {
    "nursery": Setting("nursery", "the nursery", "The lamp was low and gold.", "A soft nightlight blinked near the window."),
    "cabin": Setting("cabin", "the little cabin", "The fire was quiet, and the blankets were warm.", "Snow whispered outside the wall."),
    "bedroom": Setting("bedroom", "the bedroom", "The moon was round in the window.", "The curtain made a silver shape on the floor."),
}

MYSTERIES = {
    "lantern": Mystery("lantern", "a tiny glow under the bed", "a paper lantern toy", "a safe bedtime treasure", "Curiosity is good when it stays gentle.", "What made the glow?", "A paper lantern toy had rolled under the bed.", tags={"curiosity", "mystery"}),
    "music": Mystery("music", "a small tinkling sound in the hall", "a wind-up music box", "a forgotten bedtime toy", "It is wise to look before worrying.", "What made the tinkling sound?", "A wind-up music box had been left on a shelf.", tags={"curiosity", "mystery"}),
    "shell": Mystery("shell", "a shiny shape by the pillow", "a smooth seashell", "a kept treasure from the beach", "It is kind to appreciate what we find.", "What was the shiny shape?", "It was a seashell from a sunny walk.", tags={"curiosity", "mystery", "appreciate"}),
}

ALTERNATIVES = {
    "look": Alternative("look", "a small flashlight", "shone softly under the bed", "the child could look carefully", "The gentle light did not scare the mystery away", tags={"alternative"}),
    "ask": Alternative("ask", "a question", "let the parent explain", "the child could learn the answer without touching anything", "The answer came with a calm smile", tags={"alternative"}),
    "lamp": Alternative("lamp", "the bedside lamp", "made the shadows thin and kind", "the child could inspect the clue safely", "The warm light showed the clue plainly", tags={"alternative"}),
}



@dataclass
class StoryParams:
    setting: str
    mystery: str
    alternative: str
    child: str
    gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

CURATED = [
    StoryParams("nursery", "lantern", "look", "Mia", "girl", "mother"),
    StoryParams("bedroom", "music", "ask", "Noah", "boy", "father"),
    StoryParams("cabin", "shell", "lamp", "Ava", "girl", "mother"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for a in ALTERNATIVES:
                combos.append((s, m, a))
    return combos


def explain_rejection() -> str:
    return "(No story: the chosen pieces do not make a believable bedtime mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime mystery storyworld with curiosity and an alternative.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--alternative", choices=ALTERNATIVES)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.alternative is None or c[2] == args.alternative)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, mystery, alternative = rng.choice(sorted(combos))
    child = args.child or rng.choice(["Mia", "Noah", "Ava", "Leo", "Ella", "Finn"])
    gender = args.gender or ("girl" if child in {"Mia", "Ava", "Ella"} else "boy")
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, mystery, alternative, child, gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    return [
        f'Write a bedtime story that includes the words "{m.id}" and "alternative".',
        f"Tell a gentle story where a curious child notices {m.clue} and learns to ask for help.",
        f'Write a short moral-value story about curiosity, a mystery to solve, and how to appreciate a calm alternative.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    m: Mystery = f["mystery"]
    alt: Alternative = f["alternative"]
    return [
        QAItem(
            question="What was the child curious about?",
            answer=f"{child.id} was curious about {m.clue}. {parent.label_word.capitalize()} helped make the mystery feel safe to explore.",
        ),
        QAItem(
            question="What alternative did they use?",
            answer=f"They used {alt.label} as an alternative. It let {child.id} solve the mystery without poking at anything directly.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The mystery was solved, and {child.id} could appreciate the kind lesson. The room stayed calm and bedtime stayed sweet.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery"]
    alt: Alternative = f["alternative"]
    items = [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more about something. It helps children ask questions and learn.",
        ),
        QAItem(
            question="What is an alternative?",
            answer="An alternative is another choice you can use instead. It can help you solve a problem in a safer or kinder way.",
        ),
    ]
    if "mystery" in m.tags:
        items.append(QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not understand yet. You can solve it by looking carefully and asking good questions.",
        ))
    if "appreciate" in m.tags or alt.id:
        items.append(QAItem(
            question="What does it mean to appreciate something?",
            answer="To appreciate something means to notice it and feel thankful for it. It helps you value a kind choice or a sweet answer.",
        ))
    return items


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
    for aid, a in ALTERNATIVES.items():
        lines.append(asp.fact("alternative", aid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, A) :- setting(S), mystery(M), alternative(A).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {exc}")
    else:
        print("OK: verify smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], ALTERNATIVES[params.alternative],
                 params.child, params.gender, params.parent)
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
        print("== QA ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
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
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
