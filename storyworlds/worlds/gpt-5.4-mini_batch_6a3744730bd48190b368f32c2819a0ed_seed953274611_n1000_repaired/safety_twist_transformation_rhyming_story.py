#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/safety_twist_transformation_rhyming_story.py
=============================================================================

A small, child-facing storyworld about a playful craft day that takes a twist,
changes form, and ends with safety. The story style aims for a gentle rhyming
storybook feel: short beats, simple concrete images, and an ending that proves
what transformed.

Premise:
- A child starts with a paper kite or ribbon toy.
- A twist happens when a risky choice threatens the play.
- A grown-up or careful helper redirects the moment safely.
- The object transforms into a safer version, and the ending celebrates safety.

This file is self-contained except for the shared result containers and the lazy
ASP helper used in verification modes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Setting:
    id: str
    name: str
    rhyme_a: str
    rhyme_b: str
    indoor: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
class Toy:
    id: str
    name: str
    phrase: str
    twist_phrase: str
    safe_form: str
    safe_phrase: str
    fragile: bool = False
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
class Twist:
    id: str
    warning: str
    risk: str
    safe_fix: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
class Transformation:
    id: str
    before: str
    after: str
    verb: str
    ending_line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
    toy: str
    twist: str
    transformation: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
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
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "garden": Setting("garden", "the garden", "green", "scene", tags={"outdoor"}),
    "porch": Setting("porch", "the porch", "bright", "light", tags={"outdoor"}),
    "playroom": Setting("playroom", "the playroom", "soft", "sway", indoor=True, tags={"indoor"}),
}

TOYS = {
    "kite": Toy("kite", "kite", "a paper kite", "the paper kite's tail", "a ribbon kite", "a ribbon kite", fragile=True, tags={"air", "paper"}),
    "pinwheel": Toy("pinwheel", "pinwheel", "a little pinwheel", "the pinwheel's spin", "a safe sun-catcher", "a safe sun-catcher", fragile=False, tags={"spin"}),
    "train": Toy("train", "train", "a toy train", "the toy train's track", "a soft pull-toy", "a soft pull-toy", fragile=False, tags={"track"}),
}

TWISTS = {
    "wind": Twist("wind", "A gust of wind came by", "the paper kite could tear or fly away", "tie on a ribbon tail and hold it low", tags={"wind"}),
    "spill": Twist("spill", "A spilled cup made the floor slick", "a fast run could make someone slip", "slow down and wipe the floor first", tags={"wet"}),
    "tangle": Twist("tangle", "A string got tangled in little fingers", "a tug could pinch or scrape", "unwind it gently and ask for help", tags={"string"}),
}

TRANSFORMATIONS = {
    "ribbon": Transformation("ribbon", "paper kite", "ribbon kite", "turned into", "Now it fluttered soft and free.", tags={"kite"}),
    "lantern": Transformation("lantern", "pinwheel", "safe sun-catcher", "became", "It glowed in the light and never poked a hand.", tags={"pinwheel"}),
    "pulltoy": Transformation("pulltoy", "toy train", "soft pull-toy", "changed into", "It rolled along in a gentler way.", tags={"train"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Leo", "Sam"]
HELPER_NAMES = ["Mum", "Dad", "Gran", "Auntie", "Papa"]
HELPER_ROLES = ["mother", "father", "grandparent", "aunt"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, toy in TOYS.items():
            for wid, twist in TWISTS.items():
                for rid, trans in TRANSFORMATIONS.items():
                    if tid in trans.tags and toy.fragile and wid == "wind":
                        combos.append((sid, tid, wid, rid))
                    elif tid in trans.tags and wid in {"spill", "tangle"}:
                        combos.append((sid, tid, wid, rid))
    return combos


def explain_rejection(toy: Toy, twist: Twist, trans: Transformation) -> str:
    return (
        f"(No story: {twist.warning.lower()} does not fit well with {toy.phrase}, "
        f"and the chosen transformation must actually change that toy into a safer form.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming safety storyworld with twists and transformations.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-role", choices=HELPER_ROLES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.toy and args.twist and args.transformation:
        toy = TOYS[args.toy]
        twist = TWISTS[args.twist]
        trans = TRANSFORMATIONS[args.transformation]
        if args.toy not in trans.tags:
            raise StoryError(explain_rejection(toy, twist, trans))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.toy is None or c[1] == args.toy)
              and (args.twist is None or c[2] == args.twist)
              and (args.transformation is None or c[3] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, toy, twist, trans = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        toy=toy,
        twist=twist,
        transformation=trans,
        child_name=args.name or _pick_name(rng, child_gender),
        child_gender=child_gender,
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        helper_gender=helper_gender,
        helper_role=args.helper_role or rng.choice(HELPER_ROLES),
    )


def propagate(world: World) -> None:
    pass


def _scene(world: World, child: Entity, helper: Entity, setting: Setting, toy: Toy) -> None:
    world.say(
        f"In {setting.name}, {child.id} played with {toy.phrase} in the sun, "
        f"with a hum and a tune."
    )
    world.say(
        f"{child.id} laughed and sang, 'A game so bright, a day so light, "
        f"it feels like sweet delight.'"
    )


def _twist(world: World, child: Entity, helper: Entity, toy: Toy, twist: Twist) -> None:
    child.memes["joy"] += 1
    child.memes["curious"] += 1
    world.say(
        f"{twist.warning}, and {child.id} heard the call. "
        f"But {child.id} saw a chance to test it all."
    )
    world.say(
        f'"{twist.risk}," {helper.id} said, with a careful grin, '
        f'"let\'s slow down now and let safety win."'
    )


def _turn(world: World, child: Entity, helper: Entity, toy: Toy, twist: Twist, trans: Transformation) -> None:
    child.memes["worry"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"So they followed {twist.safe_fix}, neat and right, "
        f"and tucked the worry out of sight."
    )
    world.say(
        f"Then {trans.before} {trans.verb} into {trans.after}, "
        f"and the whole small play felt new."
    )


def _ending(world: World, child: Entity, helper: Entity, trans: Transformation) -> None:
    child.memes["safety"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"{trans.ending_line} {child.id} smiled; {helper.id} did too. "
        f"And safety shone in what they knew."
    )
    world.say(
        f"So when the day was done, they tucked away the fun, "
        f"and kept their hearts and hands in safety, every one."
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    toy = TOYS[params.toy]
    twist = TWISTS[params.twist]
    trans = TRANSFORMATIONS[params.transformation]
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper", attrs={"helper_role": params.helper_role}))
    world.add(Entity(id="toy", type="toy", label=toy.name))
    _scene(world, child, helper, setting, toy)
    world.para()
    _twist(world, child, helper, toy, twist)
    world.para()
    _turn(world, child, helper, toy, twist, trans)
    world.para()
    _ending(world, child, helper, trans)
    world.facts.update(
        child=child, helper=helper, setting=setting, toy=toy, twist=twist, trans=trans,
        safe="safety", transformed=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the word "{f["safe"]}" and shows a twist and a transformation.',
        f"Tell a gentle safety story where {f['child'].id} starts with {f['toy'].phrase}, faces {f['twist'].warning.lower()}, and then changes it into something safer.",
        "Write a short rhyming story that begins with play, turns with a small problem, and ends with a safe transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    toy = f["toy"]
    twist = f["twist"]
    trans = f["trans"]
    return [
        QAItem(
            question=f"What was the story about?",
            answer=f"It was about {child.id} and {helper.id} playing with {toy.phrase}. The story turned when {twist.warning.lower()} and they chose safety.",
        ),
        QAItem(
            question=f"What changed in the story?",
            answer=f"{toy.phrase} {trans.verb} into {trans.after}. That transformation made the game safer and gave the ending a bright new shape.",
        ),
        QAItem(
            question=f"Why did they slow down?",
            answer=f"They slowed down because {twist.risk}. So they used {twist.safe_fix} and kept the play gentle and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is safety?",
            answer="Safety means keeping people and things from getting hurt. It often means slowing down, asking for help, and choosing the careful way.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what is happening. It can make a story more exciting and lead to a new choice.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another. In stories, it can turn a toy, plan, or moment into something new.",
        ),
    ]


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def valid_story_params(params: StoryParams) -> bool:
    return (
        params.setting in SETTINGS and
        params.toy in TOYS and
        params.twist in TWISTS and
        params.transformation in TRANSFORMATIONS and
        params.toy in TRANSFORMATIONS[params.transformation].tags
    )


ASP_RULES = r"""
valid(S,T,W,R) :- setting(S), toy(T), twist(W), trans(R), compatible(T,R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
    for wid in TWISTS:
        lines.append(asp.fact("twist", wid))
    for rid, trans in TRANSFORMATIONS.items():
        lines.append(asp.fact("trans", rid))
        for tg in sorted(trans.tags):
            lines.append(asp.fact("compatible", tg, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        py = set(valid_combos())
        cl = set(asp_valid_combos())
        if py == cl:
            print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        else:
            rc = 1
            print("MISMATCH in valid combo gate:")
            print("only python:", sorted(py - cl))
            print("only asp:", sorted(cl - py))
        # smoke test ordinary generation
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story.strip()
        assert sample.prompts and sample.story_qa and sample.world_qa
        print("OK: story generation smoke test passed.")
    except Exception:
        rc = 1
        traceback.print_exc()
    return rc


def generate(params: StoryParams) -> StorySample:
    if not valid_story_params(params):
        raise StoryError("(Invalid story parameters.)")
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
    StoryParams(setting="garden", toy="kite", twist="wind", transformation="ribbon", child_name="Lily", child_gender="girl", helper_name="Mum", helper_gender="girl", helper_role="mother"),
    StoryParams(setting="porch", toy="pinwheel", twist="tangle", transformation="lantern", child_name="Tom", child_gender="boy", helper_name="Dad", helper_gender="boy", helper_role="father"),
    StoryParams(setting="playroom", toy="train", twist="spill", transformation="pulltoy", child_name="Mia", child_gender="girl", helper_name="Gran", helper_gender="girl", helper_role="grandparent"),
]


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.toy is None or c[1] == args.toy)
              and (args.twist is None or c[2] == args.twist)
              and (args.transformation is None or c[3] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, toy, twist, trans = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        toy=toy,
        twist=twist,
        transformation=trans,
        child_name=args.name or _pick_name(rng, child_gender),
        child_gender=child_gender,
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        helper_gender=helper_gender,
        helper_role=args.helper_role or rng.choice(HELPER_ROLES),
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, toy in TOYS.items():
            for wid, twist in TWISTS.items():
                for rid, trans in TRANSFORMATIONS.items():
                    if tid in trans.tags:
                        combos.append((sid, tid, wid, rid))
    return combos


def build_parser_alias() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", *c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_story_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
