#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/obscene_transformation_bedtime_story.py
=======================================================================

A standalone storyworld for a tiny bedtime-style domain about a child, a
troublesome toy phrase, and a gentle transformation into something calm,
clean, and sleepy.

Seed: obscene
Feature: Transformation
Style: Bedtime Story
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
CALM_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "glow": 0.0, "sleepiness": 0.0, "change": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "fear": 0.0, "comfort": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Toy:
    id: str
    label: str
    phrase: str
    texture: str
    change_to: str
    calm_word: str
    taboo_word: str = ""
    noisy: bool = False
    obscenable: bool = False
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
class Softening:
    id: str
    label: str
    phrase: str
    action: str
    effect: str
    power: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
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


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    for toy in list(world.entities.values()):
        if toy.meters["mess"] < THRESHOLD:
            continue
        sig = ("soften", toy.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        toy.meters["change"] += 1
        toy.meters["sleepiness"] += 1
        out.append("__soften__")
    return out


CAUSAL_RULES = [Rule("soften", "physical", _r_soften)]


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


def reasonable(toy: Toy, tool: Softening) -> bool:
    return toy.obscenable and tool.power >= 2


def predict_change(world: World, toy_id: str) -> dict:
    sim = world.copy()
    _do_obscene(sim, sim.get(toy_id), narrate=False)
    return {
        "transformed": sim.get(toy_id).meters["change"] >= THRESHOLD,
        "sleepy": sim.get("room").meters["sleepiness"] if "room" in sim.entities else 0.0,
    }


def _do_obscene(world: World, toy: Entity, narrate: bool = True) -> None:
    toy.meters["mess"] += 1
    toy.meters["glow"] += 1
    propagate(world, narrate=narrate)


def tidy_setup(world: World, child: Entity, toy: Toy) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At bedtime, {child.id} sat with {toy.phrase} on the blanket. "
        f"It looked a little {toy.texture}, a little wild, and not at all sleepy."
    )
    world.say(
        f'{child.id} whispered, "That word sounds obscene," and reached closer '
        f"just to see what would happen."
    )


def warn(world: World, parent: Entity, child: Entity, toy: Toy) -> None:
    pred = predict_change(world, "toy")
    if pred["transformed"]:
        child.memes["fear"] += 1
        world.facts["predicted"] = True
        world.say(
            f'{parent.label_word.capitalize()} bent down and said, "If you keep '
            f"shaking it, {toy.label} will change into something softer, but it "
            f"may get too bright to ignore. Let's slow down together."
        )


def transform(world: World, child: Entity, toy_ent: Entity, toy: Toy, tool: Softening) -> None:
    _do_obscene(world, toy_ent)
    toy_ent.attrs["form"] = toy.change_to
    world.say(
        f"{tool.label.capitalize()} {tool.action}, and the little thing began to "
        f"shift. The rough edges melted into {toy.calm_word}, and the noisy shine "
        f"settled into a gentle glow."
    )


def settle(world: World, parent: Entity, child: Entity, toy: Toy, tool: Softening) -> None:
    child.memes["comfort"] += 1
    child.memes["pride"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled and tucked the blanket higher. "
        f'"Now it is {tool.effect}," {parent.pronoun()} said. "{toy.label} can '
        f"rest."
    )
    world.say(
        f"{child.id} held the changed {toy.label} close. It was still the same "
        f"toy, but now it felt calm enough for dreams."
    )


def tell(toy: Toy, tool: Softening, child_name: str = "Mia", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    toy_ent = world.add(Entity(id="toy", type="toy", label=toy.label, attrs={"form": toy.phrase}))

    tidy_setup(world, child, toy)
    world.para()
    warn(world, parent, child, toy)
    world.say(f"{child.id} took a breath and let the room get quiet.")
    world.para()
    transform(world, child, toy_ent, toy, tool)
    settle(world, parent, child, toy, tool)

    world.facts.update(
        child=child, parent=parent, room=room, toy=toy, toy_ent=toy_ent, tool=tool,
        transformed=toy_ent.meters["change"] >= THRESHOLD,
    )
    return world


TOYS = {
    "obscene": Toy(
        "obscene", "the obscene little doll", "an obscene little doll",
        "shiny", "a soft bedtime doll", "sleepy", taboo_word="obscene",
        noisy=True, obscenable=True, tags={"obscene", "change"},
    ),
    "rough": Toy(
        "rough", "the rough toy", "a rough toy truck", "scratchy", "a soft toy truck",
        "sleepy", obscenable=True, tags={"change"},
    ),
    "wild": Toy(
        "wild", "the wild stuffed star", "a wild stuffed star", "sparkly",
        "a calm stuffed star", "sleepy", obscenable=True, tags={"change"},
    ),
}

TOOLS = {
    "blanket": Softening("blanket", "blanket", "a warm blanket", "wrapped around it",
                         "wrapped in quiet comfort", 3, tags={"soft"}),
    "lullaby": Softening("lullaby", "lullaby", "a lullaby", "spilled over the room",
                         "soft and sleepy", 3, tags={"soft"}),
    "lamp": Softening("lamp", "night lamp", "a little night lamp", "glowed nearby",
                      "soft enough for bedtime", 2, tags={"soft"}),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ava", "Ella", "Lucy"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Leo", "Ben"]
TRAITS = ["curious", "gentle", "brave", "sleepy", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(t, s) for t in TOYS for s in TOOLS if reasonable(TOYS[t], TOOLS[s])]


@dataclass
@dataclass
class StoryParams:
    toy: str
    softener: str
    name: str
    gender: str
    parent: str
    trait: str
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


KNOWLEDGE = {
    "obscene": [("What does obscene mean?", "Obscene is a word for something rude or not polite. In a bedtime story, it can be treated carefully and turned gentle.")],
    "change": [("What is a transformation?", "A transformation is when something changes into a different form or feeling.")],
    "blanket": [("What is a blanket for?", "A blanket keeps you warm and cozy when you are resting.")],
    "lullaby": [("What is a lullaby?", "A lullaby is a soft song sung to help someone feel calm and sleepy.")],
    "lamp": [("What is a night lamp?", "A night lamp gives a small gentle light that helps a room feel safe at bedtime.")],
}
KNOWLEDGE_ORDER = ["obscene", "change", "blanket", "lullaby", "lamp"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    toy, tool = f["toy"], f["tool"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "{toy.taboo_word}" and shows a gentle transformation.',
        f"Tell a sleepy story where {f['child'].id} notices {toy.phrase} feels strange, then uses {tool.phrase} to help it change.",
        f'Write a calm bedtime story about a toy called "{toy.label}" becoming soft and safe by the end.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, toy, tool = f["child"], f["parent"], f["toy"], f["tool"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {parent.label_word}. They are sharing a quiet bedtime moment with {toy.phrase}."),
        ("What did the toy become?", f"It changed into {toy.change_to}. The transformation made it feel calmer and easier to rest beside."),
        ("How did the parent help?", f"{parent.label_word.capitalize()} used {tool.phrase} to soften the moment. That gentle help made the change peaceful instead of scary."),
    ]
    if f.get("transformed"):
        qa.append(("How did the story end?", f"It ended with the toy settled into its new form and the room feeling sleepy. {child.id} could hold it and drift off peacefully."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["toy"].tags) | set(world.facts["tool"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("obscene", "blanket", "Mia", "girl", "mother", "gentle"),
    StoryParams("rough", "lullaby", "Noah", "boy", "father", "curious"),
    StoryParams("wild", "lamp", "Ava", "girl", "mother", "careful"),
]


def explain_rejection(toy: Toy, tool: Softening) -> str:
    if not reasonable(toy, tool):
        return "(No story: that transformation is too weak for this toy.)"
    return "(No story: invalid combination.)"


def asp_facts() -> str:
    import asp
    lines = []
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
        lines.append(asp.fact("obscenable", tid))
    for sid, s in TOOLS.items():
        lines.append(asp.fact("softener", sid))
        lines.append(asp.fact("power", sid, s.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T,S) :- toy(T), softener(S), obscenable(T), power(S,P), P >= 2.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    sample = generate(resolve_params(argparse.Namespace(toy=None, softener=None, name=None, gender=None, parent=None, trait=None, seed=None), random.Random(7)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: story generation failed.")
    else:
        print("OK: generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a gentle transformation.")
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--softener", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
              if args.toy is None or c[0] == args.toy
              and args.softener is None or c[1] == args.softener]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    toy, softener = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(toy, softener, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(TOYS[params.toy], TOOLS[params.softener], params.name, params.gender, params.parent)
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
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t, s in asp_valid_combos():
            print(f"  {t} {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
