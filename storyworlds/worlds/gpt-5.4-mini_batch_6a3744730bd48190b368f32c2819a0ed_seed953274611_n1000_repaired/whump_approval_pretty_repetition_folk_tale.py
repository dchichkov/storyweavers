#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/whump_approval_pretty_repetition_folk_tale.py
==============================================================================

A small standalone storyworld about a folk-tale village, a pretty thing that
needs approval, a repeated attempt, and a heavy whump that changes the plan.

Seed words:
- whump
- approval
- pretty

Style:
- Folk Tale

Feature:
- Repetition

The world is intentionally tiny: one child, one elder, one pretty object, one
practical helper, and a repeated refrain that nudges the action forward. The
story model keeps the narration state-driven: the pretty object starts the tale
as a wish, the repeated tries add tension, the whump marks a turning point, and
approval closes the tale with a visible change in the world.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/whump_approval_pretty_repetition_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/whump_approval_pretty_repetition_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/whump_approval_pretty_repetition_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/whump_approval_pretty_repetition_folk_tale.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    pretty: bool = True
    approval_need: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
    helper: str
    charm: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        clone.entities = {k: Entity(**asdict(v)) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "village": "a little village by the river",
    "meadow": "a green meadow beyond the hill",
    "cottage": "a snug cottage with a warm hearth",
}

CHARMS = {
    "ribbon": Charm("ribbon", "pretty ribbon", "a pretty ribbon"),
    "crown": Charm("crown", "pretty crown", "a pretty crown"),
    "cloak": Charm("cloak", "pretty cloak", "a pretty cloak"),
}

HELPERS = {
    "kite_string": Helper("kite_string", "kite string", "tied it up well", power=2),
    "peg": Helper("peg", "wooden peg", "fastened it tight", power=1),
    "basket": Helper("basket", "basket", "carried it safely", power=3),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Tessa", "Elin", "Mara"]
BOY_NAMES = ["Pip", "Tom", "Evan", "Gideon", "Rory", "Jasper"]
ELDER_NAMES = ["Grandma Willow", "Grandma Rose", "Grandpa Ash", "Grandpa Rowan"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for charm in CHARMS:
            for helper in HELPERS:
                combos.append((setting, charm, helper))
    return combos


def tell(setting: str, child_name: str, child_gender: str, elder_name: str,
         elder_gender: str, helper_id: str, charm_id: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    helper = world.add(Entity(id=HELPERS[helper_id].label, kind="thing", type="tool", label=HELPERS[helper_id].label))
    charm = world.add(Entity(id=CHARMS[charm_id].label, kind="thing", type="charm", label=CHARMS[charm_id].label))
    world.facts.update(setting=setting, child=child, elder=elder, helper=helper, charm=charm)

    child.memes["want"] += 1
    child.memes["hope"] += 1
    charm.meters["shine"] += 1

    world.say(
        f"In {SETTINGS[setting]}, {child.id} found {CHARMS[charm_id].phrase} in a old wooden chest."
    )
    world.say(
        f"{child.id} held it up and said, \"Oh, what a pretty thing!\""
    )
    world.say(
        f"But {child.id} did not yet have {elder.label_word.capitalize()} approval, and that mattered in the little village."
    )

    world.para()
    child.memes["longing"] += 1
    world.say(
        f"{child.id} tried once to carry the charm to the square, and once to set it on the sill, and once to tie it to the door."
    )
    world.say(
        f"Each time it slipped a little, and each time {child.id} tried again, because {child.id} wanted it to look even prettier."
    )

    world.para()
    charm.meters["unstable"] += 1
    helper_name = HELPERS[helper_id].label
    if helper_id == "basket":
        world.say(
            f"At last {child.id} placed it in a basket. Whump went the basket on the table, and the pretty charm stayed still at last."
        )
    elif helper_id == "kite_string":
        world.say(
            f"At last {child.id} tied it with kite string. Whump went the knot as it pulled snug, and the pretty charm stopped sliding."
        )
    else:
        world.say(
            f"At last {child.id} used a wooden peg. Whump went the peg against the board, and the pretty charm hung straight."
        )
    charm.meters["steady"] += 1

    world.para()
    elder.memes["approval"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{elder.id} came close, looked at the pretty work, and nodded with approval."
    )
    world.say(
        f"\"There now,\" said {elder.id}, \"pretty things shine best when they are set just so.\""
    )
    world.say(
        f"So {child.id} smiled, and the pretty charm stayed safe where everyone could admire it."
    )

    world.facts["outcome"] = "approved"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"].id
    elder = f["elder"].id
    charm = f["charm"].label
    return [
        f"Write a folk tale for a young child where {child} finds a {charm}, repeats a careful action, hears a whump, and wins {elder}'s approval.",
        f"Tell a repetitive, cozy story in which a pretty treasure needs to be set just right before the elder smiles with approval.",
        f"Write a village story that includes the words whump, approval, and pretty, with a repeated try-and-try-again beat.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    charm = f["charm"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {elder.id}. {child.id} is the one who first wanted the pretty thing, and {elder.id} is the one whose approval mattered at the end.",
        ),
        (
            "Why did the child keep trying again and again?",
            f"{child.id} wanted the pretty charm to look just right, so {child.id} kept trying until the way was safe and neat. That repetition made the change in the story feel patient and careful.",
        ),
        (
            "What happened when the child finally found the right way?",
            f"Whump went the basket, peg, or string, and the pretty charm stayed still at last. That meant {child.id} could show it proudly and get approval instead of worry.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        (
            "What does approval mean?",
            "Approval means someone thinks something is good or right. In a folk tale, it often comes as a nod, a smile, or a kind word.",
        ),
        (
            "What does whump sound like?",
            "Whump is a heavy sound, like something soft and big landing with a thud. It is a word people use when they want the sound to feel strong and round.",
        ),
        (
            "What does pretty mean?",
            "Pretty means nice to look at. A pretty thing can be shiny, bright, neat, or sweet-looking.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:18} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale storyworld with repetition and approval.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child")
    ap.add_argument("--elder")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    child_gender = rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_gender = rng.choice(["mother", "father", "grandmother", "grandfather"])
    elder = args.elder or rng.choice(ELDER_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    charm = args.charm or rng.choice(list(CHARMS))
    return StoryParams(
        setting=setting,
        child=child,
        child_gender=child_gender,
        elder=elder,
        elder_gender=elder_gender,
        helper=helper,
        charm=charm,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.charm not in CHARMS:
        raise StoryError("Unknown charm.")
    world = tell(
        setting=params.setting,
        child_name=params.child,
        child_gender=params.child_gender,
        elder_name=params.elder,
        elder_gender=params.elder_gender,
        helper_id=params.helper,
        charm_id=params.charm,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
pretty(charm).
needs_approval(charm).
repetition(story).
valid(setting, helper, charm) :- setting(setting), helper(helper), charm(charm).
approval_story :- valid(_, _, _).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    asp_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if asp_set != py_set:
        print("MISMATCH between ASP and Python valid_combos().")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))
        return 1
    try:
        sample = generate(StoryParams(
            setting="village",
            child="Mina",
            child_gender="girl",
            elder="Grandma Willow",
            elder_gender="grandmother",
            helper="basket",
            charm="ribbon",
            seed=1,
        ))
        _ = sample.story
    except Exception as err:
        print(f"Smoke test failed: {err}")
        return 1
    print(f"OK: ASP matches Python for {len(asp_set)} combos, and generation works.")
    return 0


CURATED = [
    StoryParams(setting="village", child="Mina", child_gender="girl", elder="Grandma Willow", elder_gender="grandmother", helper="basket", charm="ribbon"),
    StoryParams(setting="meadow", child="Pip", child_gender="boy", elder="Grandpa Rowan", elder_gender="grandfather", helper="peg", charm="crown"),
    StoryParams(setting="cottage", child="Nora", child_gender="girl", elder="Grandma Rose", elder_gender="grandmother", helper="kite_string", charm="cloak"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(x) for x in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
