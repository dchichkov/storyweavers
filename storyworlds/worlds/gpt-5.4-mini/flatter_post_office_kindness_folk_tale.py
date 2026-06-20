#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flatter_post_office_kindness_folk_tale.py
=========================================================================

A standalone story world about a small post office, a proud child, a sweet
bit of flattery, and a kindness turn worthy of a folk tale.

Seed premise:
- Setting: post office
- Feature: Kindness
- Word: flatter
- Style: Folk tale

The world models a tiny postal errand in which a child tries to flatter a clerk
to get special treatment, discovers that kindness matters more than compliments,
and ends by helping the line move for everyone.

The simulation uses typed entities with physical meters and emotional memes, a
small causal rule engine, a reasonableness gate, an inline ASP twin, and a
state-driven renderer. It is deliberately self-contained and stdlib-only.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    precious: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    used_for: str
    kindness: int
    boost: int
    text: str
    fail: str
    qa_text: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_impress(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["flatter"] < THRESHOLD or e.memes["shame"] < THRESHOLD:
            continue
        sig = ("impress", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["nervous"] += 1
        out.append("__impress__")
    return out


def _r_kindness_spread(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in world.characters():
            if other.id != e.id:
                other.memes["calm"] += 0.5
        out.append("__kindness__")
    return out


def _r_help_line(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["helping"] < THRESHOLD:
            continue
        sig = ("help_line", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "line" in world.entities:
            world.get("line").meters["speed"] += 1
        out.append("__line__")
    return out


CAUSAL_RULES = [Rule("impress", _r_impress), Rule("kindness", _r_kindness_spread), Rule("help_line", _r_help_line)]


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


def favorable_combos() -> list[tuple[str, str]]:
    combos = []
    for aid, a in ACTIONS.items():
        for iid, item in ITEMS.items():
            if a.targets == item.kind:
                combos.append((aid, iid))
    return combos


def reward_for(action: str, item: str) -> bool:
    return ACTIONS[action].targets == ITEMS[item].kind


@dataclass
class Action:
    id: str
    want: str
    risk: str
    targets: str
    use_word: str


@dataclass
class StoryParams:
    action: str
    item: str
    charm: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "post_office": Setting(
        "post_office",
        "the post office",
        "The room smelled of paper, ink, and warm envelopes, and the brass bell by the door gave a bright little ring."
    )
}

ACTIONS = {
    "faster": Action("faster", "get the parcel first", "being in a hurry", "parcel", "flatter"),
    "stamp": Action("stamp", "have the stamp admired", "waiting too long", "stamp", "praise"),
    "window": Action("window", "reach the window first", "cutting the line", "line", "flatter"),
}

ITEMS = {
    "parcel": Item("parcel", "parcel", "the parcel", "parcel", precious=True),
    "stamp": Item("stamp", "stamp", "the stamp", "stamp", precious=True),
    "line": Item("line", "line", "the line", "line", precious=False),
}

CHARMS = {
    "flatter": Charm(
        "flatter",
        "flatter",
        "flatter the clerk",
        "praise",
        kindness=1,
        boost=3,
        text="smiled wide and tried to flatter the clerk until the words came sweet as honey",
        fail="kept flattering and only made the waiting feel longer",
        qa_text="tried to flatter the clerk, but learned that sweet words are not the same as kind words",
    ),
    "gift": Charm(
        "gift",
        "little gift",
        "offer a little gift",
        "kindness",
        kindness=3,
        boost=2,
        text="offered a little gift and a kind word with it",
        fail="held out a little gift, but it was not enough to solve the problem",
        qa_text="offered a little gift and used it kindly",
    ),
    "help": Charm(
        "help",
        "helping hands",
        "help the clerk",
        "kindness",
        kindness=4,
        boost=4,
        text="rolled up their sleeves and helped sort the parcels with helping hands",
        fail="wanted to help, but the task was still too big for little hands alone",
        qa_text="helped sort the parcels with helping hands",
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Ivy", "Tara", "Nina", "Ruby", "Mina", "Nora"]
BOY_NAMES = ["Owen", "Eli", "Pax", "Milo", "Nico", "Theo", "Finn", "Jude"]
TRAITS = ["brave", "curious", "gentle", "quick", "thoughtful", "eager"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: flatter, kindness, and a post office folk tale.")
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.item and not reward_for(args.action, args.item):
        raise StoryError("That is not a reasonable thing to flatter about in the post office.")
    combos = [c for c in favorable_combos()
              if (args.action is None or c[0] == args.action)
              and (args.item is None or c[1] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    action, item = rng.choice(sorted(combos))
    charm = args.charm or rng.choice(sorted(CHARMS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or _pick_name(rng, child_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=child)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(action, item, charm, child, child_gender, helper, helper_gender, parent)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["post_office"])
    child = world.add(Entity(params.child, "character", params.child_gender, role="seeker", traits=["young"]))
    helper = world.add(Entity(params.helper, "character", params.helper_gender, role="helper", traits=["kind"]))
    parent = world.add(Entity("Parent", "character", params.parent, label="the parent"))
    clerk = world.add(Entity("Clerk", "character", "woman", label="the clerk"))
    line = world.add(Entity("line", "thing", "thing", label="the line"))

    child.memes["flatter"] = 1.0
    child.memes["shame"] = 1.0
    helper.memes["kindness"] = 1.0

    action = ACTIONS[params.action]
    item = ITEMS[params.item]
    charm = CHARMS[params.charm]

    world.say(
        f"Long ago, in the little post office by the square, {child.id} came with {child.pronoun('possessive')} {item.label} tucked close. "
        f"The room smelled of paper, ink, and warm envelopes, and the brass bell by the door gave a bright little ring."
    )
    world.say(
        f"{child.id} wanted to {action.want}, and {child.pronoun().capitalize()} thought a sweet tongue could make the day go faster. "
        f"So {child.id} began to {charm.used_for}."
    )

    world.para()
    child.memes["flatter"] += 1
    child.memes["shame"] += 1
    world.say(f"{child.id} {charm.text}.")
    helper.memes["kindness"] += 1
    world.say(
        f"But {helper.id} saw the line and remembered that a post office is for everyone, not only for the bold or the loud."
    )
    world.say(f'"Kindness first," said {helper.id}, "and the line will move when it is meant to."')

    if params.charm == "help":
        child.memes["helping"] += 1
        world.para()
        propagate(world, narrate=False)
        world.say(
            f"{child.id} listened, stepped back from the front, and helped sort the parcels beside {helper.id}."
        )
        world.say(
            f"That is how the waiting grew shorter, and when the clerk finally smiled, {child.id} knew the smile had been earned by kindness."
        )
    elif params.charm == "gift":
        world.para()
        world.say(
            f"{child.id} offered the little gift, but the clerk only nodded and kept serving the people in order."
        )
        world.say(
            f"{helper.id} took {child.id}'s hand and showed {child.pronoun('object')} how to hold the parcel patiently."
        )
        child.memes["kindness"] += 1
        child.memes["helping"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Before long, {child.id} was helping with the labels, and the line moved kindly for all."
        )
    else:
        world.para()
        world.say(
            f"{child.id} kept flattering the clerk, but the words only floated like feathers in a draft."
        )
        world.say(f"{helper.id} shook {helper.pronoun('possessive')} head and showed a better way: help, wait, and be gentle.")
        child.memes["helping"] += 1
        child.memes["kindness"] += 1
        propagate(world, narrate=False)
        world.say(
            f"In the end, {child.id} set aside the flattery, helped sort the parcels, and the whole room felt lighter."
        )

    world.facts.update(child=child, helper=helper, parent=parent, clerk=clerk, item=item,
                       action=action, charm=charm, outcome="kind")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    action = f["action"]
    charm = f["charm"]
    return [
        f'Write a folk-tale style story set in a post office about {child.id} and the word "flatter".',
        f"Tell a kindness story where {child.id} wants to {action.want} by being flattering, but learns a better way.",
        f"Write a small post-office tale in which kind behavior matters more than flattery."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    action = f["action"]
    charm = f["charm"]
    item = f["item"]
    qa = [
        ("Where does the story take place?",
         "It takes place in a post office, where people come to send parcels and buy stamps. That setting matters because everyone must wait their turn there."),
        (f"What did {child.id} try to do?",
         f"{child.id} tried to {action.want} by using {charm.label}. {child.id} hoped sweet words would make the clerk hurry."),
        (f"How did {helper.id} answer that idea?",
         f"{helper.id} reminded {child.id} that kindness matters more than flattery. Then {helper.id} showed a better way by helping with the waiting and the parcels."),
    ]
    if world.facts["charm"].id == "help":
        qa.append((
            f"How did {child.id} solve the problem?",
            f"{child.id} listened and helped sort the parcels. That kind choice made the line move for everyone."
        ))
    elif world.facts["charm"].id == "gift":
        qa.append((
            f"What happened after {child.id} offered a little gift?",
            f"The clerk still kept serving people in order, so {child.id} learned that a gift is not the same as patience. Then {child.id} helped, which was the kinder choice."
        ))
    else:
        qa.append((
            f"How did the story end?",
            f"{child.id} stopped flattering and chose kindness instead. By helping in the post office, {child.id} made the room feel calmer and brighter."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {f["charm"].id, "post_office", "kindness"}
    if f["charm"].id == "help":
        tags.add("help")
    return [item for tag in tags for item in KNOWLEDGE.get(tag, [])]


KNOWLEDGE = {
    "post_office": [("What is a post office?",
                    "A post office is a place where people send letters and parcels, buy stamps, and ask for mailing help.")],
    "kindness": [("What is kindness?",
                 "Kindness means using gentle words and helpful actions so other people feel respected and safe.")],
    "flatter": [("What does it mean to flatter someone?",
                 "To flatter someone is to praise them in a way meant to win favor, not always because the praise is needed or true.")],
    "help": [("Why is helping a good thing?",
              "Helping makes hard jobs easier and shows care for other people. It can also make a busy place feel calmer.")],
}

ASP_RULES = r"""
kind_action(A) :- action(A), action_kind(A).
better_than_flatter(A) :- kind_action(A), not flattery(A).
valid_story(A, I) :- action(A), item(I), targets(A, I).
kind_end :- helper_kindness, not bad_end.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("post_office", "post_office"))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_kind", aid) if aid == "help" else asp.fact("flattery", aid))
        lines.append(asp.fact("targets", aid, a.targets))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    lines.append(asp.fact("helper_kindness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    py = set(favorable_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches favorable_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return favorable_combos()


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = favorable_combos()
    if args.action and args.item and not reward_for(args.action, args.item):
        raise StoryError("That is not a reasonable story combination.")
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    filtered = [c for c in combos if (args.action is None or c[0] == args.action) and (args.item is None or c[1] == args.item)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    action, item = rng.choice(sorted(filtered))
    charm = args.charm or rng.choice(sorted(CHARMS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or _pick_name(rng, child_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=child)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(action, item, charm, child, child_gender, helper, helper_gender, parent)


def build_sample_sequence(args: argparse.Namespace, base_seed: int) -> list[StorySample]:
    samples: list[StorySample] = []
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
    return samples


CURATED = [
    StoryParams("faster", "parcel", "flatter", "Mira", "girl", "Owen", "boy", "mother"),
    StoryParams("window", "line", "gift", "Nico", "boy", "Mina", "girl", "father"),
    StoryParams("stamp", "stamp", "help", "Lena", "girl", "Finn", "boy", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible action/item pairs:")
        for a, i in asp_valid_combos():
            print(f"  {a:8} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = build_sample_sequence(args, base_seed)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.action} with {p.charm} at the post office"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
