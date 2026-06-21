#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cranapple_grill_tuv_transformation_bedtime_story.py
====================================================================================

A small bedtime-story world about a child, a sleepy helper, and a gentle
transformation: a cold cranapple becomes warm, a grill makes light and warmth,
and a tuv learns to rest. The story is built from simulated state rather than a
fixed paragraph with swapped words.

The world supports:
- typed entities with physical meters and emotional memes,
- a reasonableness gate and inline ASP twin,
- story prompts, grounded Q&A, and world knowledge Q&A,
- default runs, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
  and --show-asp.

This is a standalone script for the Storyweavers repo.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MIN_WARMTH = 2
MIN_KINDNESS = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    warmable: bool = False
    transformable: bool = False
    emits_warmth: bool = False
    edible: bool = False
    fragile: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    bedtime_phrase: str
    afforded: set[str] = field(default_factory=set)
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Transform:
    id: str
    from_state: str
    to_state: str
    method: str
    line: str
    result_line: str
    power: int
    sense: int
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
    transform: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "cozy_kitchen": Setting(
        id="cozy_kitchen",
        place="the cozy kitchen",
        mood="soft and drowsy",
        bedtime_phrase="The lamp was low, and the whole room felt ready for sleep.",
        afforded={"warm", "rest"},
    ),
    "moon_porch": Setting(
        id="moon_porch",
        place="the moon porch",
        mood="quiet and silver",
        bedtime_phrase="The porch sat under the moon, quiet as a held breath.",
        afforded={"warm", "rest"},
    ),
}

TRANSFORMS = {
    "cranapple_to_warm_treat": Transform(
        id="cranapple_to_warm_treat",
        from_state="cold cranapple",
        to_state="warm cranapple treat",
        method="letting the grill warm it very gently",
        line="The cranapple rested on the grill and slowly changed from cool and firm to soft and warm.",
        result_line="At the end, the cranapple was no longer chilly; it smelled sweet, red, and ready for bedtime nibbling.",
        power=2,
        sense=3,
        tags={"cranapple", "grill", "warm"},
    ),
    "tuv_to_sleepy_tuv": Transform(
        id="tuv_to_sleepy_tuv",
        from_state="wiggly tuv",
        to_state="sleepy tuv",
        method="tucking tuv beside the warm grill light",
        line="The tuv watched the glow, yawned, and grew calm as the warmth curled through the room.",
        result_line="By the end, the tuv was sleepy, tucked in, and snug as a little moon bean.",
        power=1,
        sense=3,
        tags={"tuv", "warm", "bedtime"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Mina"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Finn", "Eli", "Milo"]
HELPER_NAMES = ["Pip", "Momo", "Tula", "Rin"]
HELPER_ROLES = ["kitten", "mouse", "owl", "bear"]
TRAITS = ["gentle", "sleepy", "careful", "kind", "curious"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, tr in TRANSFORMS.items():
            if sid in SETTINGS and tr.sense >= MIN_KINDNESS:
                combos.append((sid, tid))
    return combos


def explain_rejection(setting: Setting, transform: Transform) -> str:
    return (
        f"(No story: this bedtime world needs a gentle transformation that can happen "
        f"in {setting.place}, and '{transform.id}' is not reasoned as gentle enough.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: cranapple, grill, tuv, and a gentle transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-role", choices=HELPER_ROLES)
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
    if args.setting and args.transform:
        if (args.setting, args.transform) not in valid_combos():
            raise StoryError(explain_rejection(SETTINGS[args.setting], TRANSFORMS[args.transform]))
    combos = [c for c in valid_combos()
              if args.setting is None or c[0] == args.setting
              if args.transform is None or c[1] == args.transform]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, transform = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    helper_role = args.helper_role or rng.choice(HELPER_ROLES)
    return StoryParams(setting=setting, transform=transform, child_name=name, child_gender=gender,
                       helper_name=helper_name, helper_gender=helper_gender, helper_role=helper_role)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    tr = TRANSFORMS[params.transform]
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender,
                             role="child", traits=["sleepy", "gentle"]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender,
                              role="helper", traits=[params.helper_role, "kind"]))
    grill = world.add(Entity(id="grill", kind="thing", type="grill", label="the grill",
                             warmable=True, emits_warmth=True, fragile=False))
    cranapple = world.add(Entity(id="cranapple", kind="thing", type="cranapple",
                                 label="cranapple", phrase="a bright red cranapple",
                                 transformable=True, warmable=True, edible=True))
    tuv = world.add(Entity(id="tuv", kind="thing", type="tuv", label="tuv",
                           phrase="a little tuv", transformable=True))
    child.memes["sleepiness"] = 1
    helper.memes["kindness"] = 1
    world.say(f"It was bedtime in {setting.place}, and everything felt {setting.mood}. {setting.bedtime_phrase}")
    world.say(f"{child.id} had {tr.from_state}, and {helper.id} the {helper_role} sat near the little grill.")
    world.para()
    world.say(f'"Can the cranapple change?" {child.id} whispered.')
    world.say(f'{helper.id} nodded softly. "{tr.line}"')
    world.para()
    child.memes["wonder"] += 1
    grill.meters["warmth"] += tr.power
    cranapple.meters["warmth"] += tr.power
    cranapple.meters["transformed"] += 1
    tuv.memes["calm"] += 1
    world.say(f"{child.id} used the grill for warmth, not flames, and {tr.method}.")
    world.say(tr.result_line)
    world.para()
    world.say(f"The tuv watched the glowing grill, yawned, and curled closer to sleep.")
    world.say(f"{helper.id} tucked the tuv into a soft corner while {child.id} held the warm cranapple carefully.")
    world.say(f"Then the whole room grew quiet again, with the grill low and the bedtime feeling made complete.")
    world.facts.update(child=child, helper=helper, grill=grill, cranapple=cranapple, tuv=tuv, transform=tr)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tr = f["transform"]
    return [
        f'Write a bedtime story that includes the words "cranapple", "grill", and "tuv".',
        f"Tell a gentle story where a child watches a cranapple change on a grill and a tuv grows sleepy.",
        f'Write a soft story about "{tr.id}" with a calm ending and a warm room.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, tr = f["child"], f["helper"], f["transform"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, {helper.id}, the grill, the cranapple, and the tuv. The room stays gentle and sleepy from beginning to end."),
        ("What changed in the story?",
         f"The cranapple changed from cold to warm on the grill. That little transformation made the bedtime moment feel cozy and special."),
        ("What happened to the tuv?",
         f"The tuv grew calm and sleepy while the grill glowed softly. The warmth helped the tuv settle down for the night."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a grill?",
         "A grill is a cooking thing that can get warm or hot. Grown-ups use it to heat food."),
        ("What is a cranapple?",
         "A cranapple is a made-up fruit in this story world. It can be warmed until it changes into a soft bedtime treat."),
        ("What is a tuv?",
         "A tuv is a tiny made-up bedtime helper in this story world. It can grow calm and sleepy when the room turns quiet."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="cozy_kitchen", transform="cranapple_to_warm_treat",
                child_name="Lily", child_gender="girl", helper_name="Pip",
                helper_gender="boy", helper_role="owl"),
    StoryParams(setting="moon_porch", transform="tuv_to_sleepy_tuv",
                child_name="Theo", child_gender="boy", helper_name="Momo",
                helper_gender="girl", helper_role="bear"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, tr in TRANSFORMS.items():
        lines.append(asp.fact("transform", tid))
        lines.append(asp.fact("sense", tid, tr.sense))
    lines.append(asp.fact("sense_min", MIN_KINDNESS))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T) :- setting(S), transform(T), sense(T, X), sense_min(M), X >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, transform=None, name=None, gender=None,
            helper_name=None, helper_gender=None, helper_role=None), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.transform not in TRANSFORMS:
        raise StoryError("(Invalid params.)")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for s, t in asp_valid_combos():
            print(f"  {s:14} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
