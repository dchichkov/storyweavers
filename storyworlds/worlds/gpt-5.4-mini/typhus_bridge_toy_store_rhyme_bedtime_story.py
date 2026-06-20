#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/typhus_bridge_toy_store_rhyme_bedtime_story.py
================================================================================

A small standalone storyworld for a bedtime-style toy-store tale with rhyme.
The seed words are woven into a child-facing, state-driven world about a toy
store, a bridge, and a scary word that gets handled with calm care.

The story premise:
- A child and a parent visit a toy store.
- The child notices a toy bridge display and wants to climb or rush across it.
- A dusty box or old book with the word "typhus" appears, and the parent warns
  that old dust and germs are not for little hands.
- The child listens, chooses a softer, safer toy path, and the ending proves
  what changed: safer play, cleaner hands, and bedtime calm.

The text is kept lightly rhyming, like a bedtime story, without turning into a
frozen rhyme template. The world model drives the turn and the ending image.
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
    mood: str
    closing: str

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
class Toy:
    id: str
    label: str
    phrase: str
    rhyme: str
    soft: bool = False
    climbable: bool = False
    dusty: bool = False
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
class Warning:
    id: str
    label: str
    line: str
    sense: int
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
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


def _r_spooked(world: World) -> list[str]:
    out: list[str] = []
    if "child" not in world.entities or "warning" not in world.facts:
        return out
    child = world.get("child")
    if child.memes["worry"] >= THRESHOLD and ("spook", 1) not in world.fired:
        world.fired.add(("spook", 1))
        child.memes["quiet"] += 1
        out.append("__quiet__")
    return out


CAUSAL_RULES = [Rule("spooked", _r_spooked)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def child_name_rng(rng: random.Random) -> tuple[str, str]:
    girl = ["Mia", "Lily", "Nora", "Rose", "Ava"]
    boy = ["Theo", "Finn", "Eli", "Jack", "Noah"]
    gender = rng.choice(["girl", "boy"])
    return rng.choice(girl if gender == "girl" else boy), gender


SETTINGS = {
    "toy_store": Setting("toy_store", "the toy store", "bright and merry", "like a lullaby"),
}

TOYS = {
    "bridge_blocks": Toy(
        "bridge_blocks", "block bridge", "a wooden bridge of blocks", "light",
        climbable=True, tags={"bridge"},
    ),
    "stuffed_bear": Toy(
        "stuffed_bear", "stuffed bear", "a soft stuffed bear", "care",
        soft=True, tags={"soft"},
    ),
    "music_box": Toy(
        "music_box", "music box", "a little music box", "glow",
        soft=True, tags={"music"},
    ),
    "toy_train": Toy(
        "toy_train", "toy train", "a tiny toy train", "choo",
        tags={"train"},
    ),
    "story_book": Toy(
        "story_book", "picture book", "a bedtime picture book", "moon",
        soft=True, tags={"book"},
    ),
    "dusty_box": Toy(
        "dusty_box", "dusty box", "an old dusty box", "hush",
        dusty=True, tags={"typhus"},
    ),
}

WARNINGS = {
    "typhus": Warning(
        "typhus", "typhus", "That dusty box says typhus, a germ word. Dust stays away from little hands.", 3, tags={"typhus"}
    ),
    "bridge": Warning(
        "bridge", "bridge", "That bridge of blocks looks wobbly, so we keep our feet on the floor.", 3, tags={"bridge"}
    ),
}

CURATED_TOYS = ["bridge_blocks", "stuffed_bear", "music_box", "toy_train", "story_book", "dusty_box"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    toy: str
    warning: str
    child_name: str
    child_gender: str
    parent_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for toy_id, toy in TOYS.items():
        if toy_id == "dusty_box":
            combos.append(("toy_store", toy_id, "typhus"))
        if toy.climbable:
            combos.append(("toy_store", toy_id, "bridge"))
    return combos


def reasonableness_gate(toy: Toy, warning: Warning) -> bool:
    if warning.id == "typhus":
        return toy.dusty
    if warning.id == "bridge":
        return toy.climbable
    return False


def explain_rejection(toy: Toy, warning: Warning) -> str:
    if warning.id == "typhus" and not toy.dusty:
        return "(No story: typhus needs a dusty thing to make a sensible warning.)"
    if warning.id == "bridge" and not toy.climbable:
        return "(No story: the bridge warning only fits a toy that can wobble or be climbed.)"
    return "(No story: that combination does not make a gentle bedtime problem.)"


ASP_RULES = r"""
hazard(bridge_blocks, bridge) :- climbable(bridge_blocks).
hazard(dusty_box, typhus) :- dusty(dusty_box).
valid(toy_store, T, W) :- setting(toy_store), toy(T), warning(W), hazard(T, W).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("setting", "toy_store"))
    for tid, toy in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if toy.climbable:
            lines.append(asp.fact("climbable", tid))
        if toy.dusty:
            lines.append(asp.fact("dusty", tid))
    for wid in WARNINGS:
        lines.append(asp.fact("warning", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(toy=None, warning=None, seed=None), random.Random(7)))
        _ = sample.story
    except Exception as err:
        print(f"MISMATCH: normal generation failed: {err}")
        return 1
    print(f"OK: valid_combos match and generation works ({len(valid_combos())} combos).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Toy store bedtime rhyme story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.toy and args.warning:
        if not reasonableness_gate(TOYS[args.toy], WARNINGS[args.warning]):
            raise StoryError(explain_rejection(TOYS[args.toy], WARNINGS[args.warning]))
    valid = [c for c in valid_combos()
             if (args.toy is None or c[1] == args.toy)
             and (args.warning is None or c[2] == args.warning)]
    if not valid:
        raise StoryError("(No valid story matches those choices.)")
    _, toy_id, warning_id = rng.choice(valid)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or child_name_rng(rng)[0]
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams("toy_store", toy_id, warning_id, name, gender, parent)


def tell(params: StoryParams) -> World:
    rng = random.Random(params.seed or 0)
    world = World()
    child = world.add(Entity("child", "character", params.child_gender, role="child"))
    parent = world.add(Entity("parent", "character", params.parent_type, label="the parent"))
    toy = world.add(Entity("toy", "thing", label=TOYS[params.toy].label))
    child.memes["curious"] += 1
    child.memes["love"] += 1
    world.say(f"In the toy store, {child.id} walked slow and bright, where shelves shone soft in the evening light.")
    world.say(f"{child.id} saw {TOYS[params.toy].phrase}, and it looked like a bridge to a dreamy height.")
    world.say(f'"I want that bridge," {child.id} sang, "for a little play and a little ride."')
    world.para()
    if params.warning == "bridge":
        child.memes["worry"] += 1
        world.say(f'The parent smiled, then said, "{WARNINGS[params.warning].line}"')
        world.say(f'"A bridge is for looking, not leaping," {parent.label_word} hummed, "so keep your feet beside."')
    else:
        child.memes["worry"] += 1
        world.say(f'From a dusty shelf came a small sign that read "typhus," and the parent gave a calm, kind sigh.')
        world.say(f'"{WARNINGS[params.warning].line}" {parent.label_word} said. "We wash our hands, and we let that old box lie."')
    world.para()
    child.memes["trust"] += 1
    world.say(f"{child.id} nodded and chose {TOYS['stuffed_bear'].phrase} instead, all soft and snug like a pillow of sky.")
    world.say(f"Together they found a bedtime book and a little song box, then walked to the counter with a sleepy goodbye.")
    world.say(f"At home that night, the bridge stayed on the shelf, the dusty word stayed put, and clean hands made the room feel dry and spry.")
    world.say(f"{child.id} hugged the soft bear close and listened to the music, then drifted to sleep with a yawn and a rhyme.")
    world.facts.update(child=child, parent=parent, toy=toy, params=params, warning=WARNINGS[params.warning])
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    if p.warning == "typhus":
        return [
            'Write a bedtime story set in a toy store that includes the word "typhus" and ends with a soft, safe choice.',
            f"Tell a rhyming bedtime story where {p.child_name} notices a dusty box in a toy store and listens to a parent warning about typhus.",
            "Write a gentle story about a toy store, clean hands, and a child choosing a cuddly toy instead of a dusty surprise.",
        ]
    return [
        'Write a bedtime story set in a toy store that includes the word "bridge" and ends with a safe choice.',
        f"Tell a rhyming bedtime story where {p.child_name} sees a toy bridge in a toy store and stays on the floor instead of climbing it.",
        "Write a gentle story about a toy store, a wobbly bridge of blocks, and a child choosing careful play.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    warn = world.facts["warning"]
    ans1 = f"It is about {p.child_name}, {p.child_name}'s {world.get('parent').label_word}, and a toy store full of sleepy, shiny things."
    ans2 = f"{p.child_name} wanted {world.get('toy').label}, but listened when the parent gave a calm warning."
    if warn.id == "typhus":
        ans3 = "The dusty box stayed closed, and the child chose a soft toy instead. That kept the story calm and clean."
    else:
        ans3 = "The child kept feet on the floor and admired the bridge without climbing it. That kept the play safe and slow."
    return [
        QAItem("Who is the story about?", ans1),
        QAItem("What did the child want at first?", ans2),
        QAItem("How did the story end?", ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    warn = world.facts["warning"]
    if warn.id == "typhus":
        return [
            QAItem("What is typhus?", "Typhus is a germ-related illness word. Children should avoid dusty old things and wash their hands."),
            QAItem("Why should you wash your hands after dusty play?", "Washing hands helps brush away dirt and germs, so little hands stay clean and safe."),
        ]
    return [
        QAItem("What is a bridge?", "A bridge is something that helps you go over or across something else."),
        QAItem("Why should children be careful on a bridge?", "A bridge can wobble or be high up, so careful feet and a grown-up's help keep play safe."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id}: type={e.type} role={e.role} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
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


CURATED = [
    StoryParams("toy_store", "bridge_blocks", "bridge", "Mia", "girl", "mother"),
    StoryParams("toy_store", "dusty_box", "typhus", "Noah", "boy", "father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.toy} / {p.warning}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
