#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ergonomic_opinion_bad_ending_transformation_kindness_slice.py
==============================================================================================

A standalone story world for a small slice-of-life domain about a child, an
ergonomic chair, an opinion, a kind attempt to improve a room, and a bad ending
where the transformation goes wrong.

The world is built around a tiny domestic scene:
- a child has a favorite spot for reading or drawing,
- another person has an opinion about the room or the chair,
- a kind act tries to transform the setup,
- but the change ends badly, leaving a clear final image.

The story engine is intentionally small and classical:
typed entities with physical meters and emotional memes, forward causal rules,
a reasonableness gate, Python/ASP parity checks, and separate QA sets grounded
in the simulated state rather than in rendered text.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/ergonomic_opinion_bad_ending_transformation_kindness_slice.py
    python storyworlds/worlds/gpt-5.4-mini/ergonomic_opinion_bad_ending_transformation_kindness_slice.py --qa
    python storyworlds/worlds/gpt-5.4-mini/ergonomic_opinion_bad_ending_transformation_kindness_slice.py --all
    python storyworlds/worlds/gpt-5.4-mini/ergonomic_opinion_bad_ending_transformation_kindness_slice.py --verify
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
    room: str = ""
    support: str = ""
    ergonomic: bool = False
    comfortable: bool = False
    transformable: bool = False
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
    room: str
    quiet: str
    details: str

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
class Item:
    id: str
    label: str
    phrase: str
    room: str
    ergonomic: bool = False
    transformable: bool = False
    fragile: bool = False
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
class OpinionMove:
    id: str
    sense: int
    text: str
    fallout: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_uneasy(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    chair = world.entities.get("chair")
    if not child or not chair:
        return out
    if child.memes["worry"] >= THRESHOLD and chair.meters["wobble"] >= THRESHOLD:
        sig = ("uneasy",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            out.append("__uneasy__")
    return out


def _r_break(world: World) -> list[str]:
    out = []
    chair = world.entities.get("chair")
    if not chair:
        return out
    if chair.meters["strain"] >= THRESHOLD and chair.meters["wobble"] >= THRESHOLD:
        sig = ("break",)
        if sig not in world.fired:
            world.fired.add(sig)
            chair.meters["broken"] += 1
            out.append("__break__")
    return out


CAUSAL_RULES = [Rule("uneasy", "social", _r_uneasy), Rule("break", "physical", _r_break)]


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


def setup_story(world: World, child: Entity, other: Entity, chair: Entity, item: Item) -> None:
    child.memes["comfort"] += 1
    child.memes["taste"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} settled into {world.setting.quiet}. "
        f"{world.setting.details} {chair.label_word if hasattr(chair, 'label_word') else chair.label} sat by the desk."
    )
    world.say(
        f"{child.id} liked the {item.label}, because it felt {item.phrase} and helped "
        f"{child.pronoun()} sit up straight to read."
    )


def state_opinion(world: World, other: Entity, item: Item) -> None:
    other.memes["opinion"] += 1
    world.say(
        f'{other.id} peeked in and gave an opinion. "{item.label.capitalize()} looks a little too plain," '
        f'{other.pronoun()} said, though {other.pronoun("possessive")} voice was gentle.'
    )


def help_transform(world: World, child: Entity, other: Entity, chair: Entity, item: Item) -> None:
    child.memes["kindness"] += 1
    other.memes["kindness"] += 1
    chair.meters["wobble"] += 1
    chair.meters["strain"] += 1
    world.say(
        f"{child.id} wanted to be kind, so {child.pronoun()} tried to transform the corner. "
        f"{child.id} and {other.id} added a blanket, moved a lamp, and stacked a few books to make it look nicer."
    )
    world.say(
        f'For a moment, {child.id} smiled and said, "There, that is more ergonomic now."'
    )
    propagate(world, narrate=False)


def bad_turn(world: World, child: Entity, other: Entity, chair: Entity, item: Item) -> None:
    chair.meters["wobble"] += 1
    chair.meters["strain"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the little tower shifted. The chair gave a sad creak, leaned sideways, and the books slid to the floor."
    )
    world.say(
        f"{other.id} gasped, and {child.id} grabbed the desk edge just in time."
    )
    chair.meters["broken"] += 1


def ending(world: World, child: Entity, other: Entity, chair: Entity, item: Item) -> None:
    child.memes["sadness"] += 1
    other.memes["guilt"] += 1
    world.say(
        f"{other.id} was kind about it, but the cozy corner did not survive the experiment. "
        f"The blanket was wrinkled, the lamp had slid crooked, and the chair was cracked."
    )
    world.say(
        f"{child.id} sat on the rug instead, hugging {child.pronoun('possessive')} knees, while {other.id} promised to help fix it properly tomorrow."
    )


SETTINGS = {
    "bedroom": Setting(
        "bedroom",
        "the bedroom",
        "the room was very quiet",
        "A small desk stood under the window, with a lamp beside it and a soft rug on the floor.",
    ),
    "study": Setting(
        "study",
        "the study",
        "the room felt calm and tidy",
        "A narrow desk waited near the bookshelves, and the afternoon light made the walls glow.",
    ),
    "corner": Setting(
        "corner",
        "the nook",
        "the nook was peaceful",
        "A little reading corner held a desk, a lamp, and a low chair that was easy to miss until someone sat down.",
    ),
}

ITEMS = {
    "chair": Item("chair", "ergonomic chair", "supportive and easy on the back", "desk", ergonomic=True, fragile=False, transformable=True, tags={"ergonomic"}),
    "stool": Item("stool", "small stool", "simple and sturdy", "desk", ergonomic=False, fragile=False, transformable=True, tags={"simple"}),
    "cushion": Item("cushion", "seat cushion", "soft and helpful", "desk", ergonomic=True, fragile=True, transformable=True, tags={"ergonomic", "soft"}),
}

OPINIONS = {
    "plain": OpinionMove("plain", 2, "looks plain", "the corner ended up looking a little messy", tags={"opinion"}),
    "odd": OpinionMove("odd", 3, "looks odd", "the setup became unsteady", tags={"opinion"}),
    "small": OpinionMove("small", 2, "looks too small", "the books did not stay put", tags={"opinion"}),
}

CHILD_NAMES = ["Maya", "Lena", "Noah", "Eli", "Nia", "Theo", "Iris", "Sam"]
OTHER_NAMES = ["Aunt June", "Ben", "Mira", "Uncle Paul", "Rosa", "Finn"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    opinion: str
    child: str
    child_gender: str
    other: str
    other_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            if not item.ergonomic:
                continue
            for oid, op in OPINIONS.items():
                if op.sense >= SENSE_MIN:
                    out.append((sid, iid, oid))
    return out


def explain_rejection(item: Item) -> str:
    return f"(No story: {item.label} would not support the quiet transformation premise.)"


def explain_opinion(opinion: OpinionMove) -> str:
    return f"(No story: the opinion move '{opinion.id}' is too weak for the world rules.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about ergonomic things, opinions, kindness, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--opinion", choices=OPINIONS)
    ap.add_argument("--child")
    ap.add_argument("--other")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--other-gender", choices=["girl", "boy"])
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
    if args.item and not ITEMS[args.item].ergonomic:
        raise StoryError(explain_rejection(ITEMS[args.item]))
    if args.opinion and OPINIONS[args.opinion].sense < SENSE_MIN:
        raise StoryError(explain_opinion(OPINIONS[args.opinion]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.opinion is None or c[2] == args.opinion)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, opinion = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    other_gender = args.other_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    other = args.other or rng.choice([n for n in OTHER_NAMES if n != child])
    return StoryParams(setting, item, opinion, child, child_gender, other, other_gender)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity("child", kind="character", type=params.child_gender, label=params.child, role="child", room=world.setting.room))
    other = world.add(Entity("other", kind="character", type=params.other_gender, label=params.other, role="other", room=world.setting.room))
    chair = world.add(Entity("chair", kind="thing", type="chair", label=ITEMS[params.item].label, ergonomic=True, transformable=True, room=world.setting.room))
    world.facts["item"] = ITEMS[params.item]
    world.facts["opinion"] = OPINIONS[params.opinion]

    setup_story(world, child, other, chair, ITEMS[params.item])
    world.para()
    state_opinion(world, other, ITEMS[params.item])
    child.memes["worry"] += 1
    help_transform(world, child, other, chair, ITEMS[params.item])
    world.para()
    bad_turn(world, child, other, chair, ITEMS[params.item])
    ending(world, child, other, chair, ITEMS[params.item])

    world.facts.update(child=child, other=other, chair=chair, outcome="bad_ending")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    return [
        f'Write a slice-of-life story that includes the word "ergonomic" and the word "opinion".',
        f"Tell a small domestic story about {f['child'].label} and {f['other'].label} trying to improve a cozy corner, but the transformation goes wrong.",
        f"Write a gentle story where kindness leads to a room makeover, yet the ending is bad because the furniture shifts and breaks.",
        f"Include an ergonomic {item.label} and a child sharing an opinion about how the corner looks.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    other = f["other"]
    chair = f["chair"]
    item = f["item"]
    qs = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.label} and {other.label}, who spend a quiet afternoon in the same little room.",
        ),
        QAItem(
            question="What did the child like at first?",
            answer=f"{child.label} liked the {item.label} because it felt {item.phrase}. That made it easier to sit up straight and stay comfortable.",
        ),
        QAItem(
            question="What was the other person's opinion?",
            answer=f"{other.label} said the setup looked a bit plain. The opinion was gentle, but it still pushed the story toward change.",
        ),
        QAItem(
            question="Why did the ending go badly?",
            answer="The attempt to improve the corner used a shaky stack of books and a blanket. That made the chair wobble, then crack, so the transformation ended in a mess instead of a fix.",
        ),
        QAItem(
            question="How did kindness show up?",
            answer=f"{child.label} tried to help the corner look nicer, and {other.label} stayed gentle when the plan failed. Even after the chair broke, they spoke kindly and promised to fix it properly later.",
        ),
    ]
    return qs


KNOWLEDGE = {
    "ergonomic": [(
        "What does ergonomic mean?",
        "Ergonomic means made to fit the body well and help you sit, stand, or work in a comfortable way."
    )],
    "opinion": [(
        "What is an opinion?",
        "An opinion is what someone thinks or believes about something. Different people can have different opinions about the same thing."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness means being gentle, helpful, and thoughtful toward someone else."
    )],
    "chair": [(
        "What is a chair for?",
        "A chair is for sitting on. A good chair helps a person rest their body while they read, draw, or talk."
    )],
    "broken": [(
        "What does it mean when something is broken?",
        "If something is broken, it does not work the way it should anymore and may need to be fixed or replaced."
    )],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"ergonomic", "opinion", "kindness", "chair", "broken"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id:8} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bedroom", "chair", "plain", "Maya", "girl", "Aunt June", "girl"),
    StoryParams("study", "chair", "odd", "Noah", "boy", "Rosa", "girl"),
    StoryParams("corner", "chair", "small", "Iris", "girl", "Ben", "boy"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.ergonomic:
            lines.append(asp.fact("ergonomic", iid))
    for oid, op in OPINIONS.items():
        lines.append(asp.fact("opinion", oid))
        lines.append(asp.fact("sense", oid, op.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, O) :- setting(S), item(I), ergonomic(I), opinion(O), sense(O, V), sense_min(M), V >= M.
"""


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, i, o) for s in SETTINGS for i in ITEMS if ITEMS[i].ergonomic for o in OPINIONS if OPINIONS[o].sense >= SENSE_MIN]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid_combos()")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(7)))
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
