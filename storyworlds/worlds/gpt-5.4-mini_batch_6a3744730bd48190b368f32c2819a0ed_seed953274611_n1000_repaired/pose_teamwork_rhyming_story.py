#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pose_teamwork_rhyming_story.py
===============================================================

A tiny storyworld for a rhyming teamwork tale about two kids preparing a pose,
cooperating, and making a picture turn out right.

The seed idea is simple:
- A child wants a great pose.
- The pose needs teamwork to work well.
- A small snag happens.
- The children help each other and finish with a bright, cheerful result.

This world keeps the prose child-facing and lightly rhymed, while the state model
drives what actually happens.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
TEAMWORK_GOOD = 2.0
POSE_GOAL = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Cast:
    scene: str
    rhyme_a: str
    rhyme_b: str
    activity: str
    snag: str
    fix: str
    finish: str
    tags: set[str] = field(default_factory=set)
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
class Pose:
    id: str
    label: str
    need: str
    support: str
    risk: str
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
class Helper:
    id: str
    label: str
    method: str
    power: int
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.get("pair").memes["helping"] >= THRESHOLD and world.get("pose").meters["steady"] >= THRESHOLD:
        if ("teamwork",) not in world.fired:
            world.fired.add(("teamwork",))
            world.get("pose").meters["bright"] += 1
            world.get("pair").memes["pride"] += 1
            out.append("__teamwork__")
    return out


def _r_sag(world: World) -> list[str]:
    out: list[str] = []
    if world.get("pose").meters["wobbly"] >= THRESHOLD and ("sag",) not in world.fired:
        world.fired.add(("sag",))
        world.get("pose").meters["steady"] -= 0.5
        out.append("__sag__")
    return out


RULES = [Rule("sag", "physical", _r_sag), Rule("teamwork", "social", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for cid, cast in CASTS.items():
        for pid, pose in POSES.items():
            for hid, helper in HELPERS.items():
                if pose.need in helper.tags and pose.support in helper.tags:
                    combos.append((cid, pid, hid))
    return combos


@dataclass
class StoryParams:
    cast: str
    pose: str
    helper: str
    name_a: str
    type_a: str
    name_b: str
    type_b: str
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


CASTS = {
    "photo_day": Cast(
        scene="a sunny schoolyard",
        rhyme_a="glee",
        rhyme_b="tree",
        activity="strike a pose",
        snag="the hat kept slipping with a breeze",
        fix="they leaned together and held still",
        finish="their picture shone for all to see",
        tags={"pose", "teamwork", "rhyming"},
    ),
    "stage_day": Cast(
        scene="a small stage",
        rhyme_a="light",
        rhyme_b="bright",
        activity="try a pose",
        snag="the curtain tugged and tipped the prop",
        fix="they balanced it with careful hands",
        finish="their show looked neat from bottom to top",
        tags={"pose", "teamwork", "rhyming"},
    ),
}

POSES = {
    "star_pose": Pose("star_pose", "star pose", "steady feet", "a wide, strong stance", "wobble", {"pose", "steady"}),
    "mirror_pose": Pose("mirror_pose", "mirror pose", "still hands", "a soft, even balance", "wobble", {"pose", "steady"}),
}

HELPERS = {
    "hold_hat": Helper("hold_hat", "hand to hold the hat", "held the hat", 2, {"hat", "steady", "support"}),
    "count_beat": Helper("count_beat", "counting beat", "counted one-two-three", 2, {"beat", "steady", "support"}),
}


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}"


def tell(cast: Cast, pose: Pose, helper: Helper, a: Entity, b: Entity) -> World:
    world = World()
    world.add(a)
    world.add(b)
    world.add(Entity(id="pair", kind="character", type="pair", role="team", label="the pair"))
    world.add(Entity(id="pose", type="thing", label=pose.label))
    world.add(Entity(id="helper", type="thing", label=helper.label))
    world.get("pair").memes["helping"] = 1.0
    world.get("pose").meters["steady"] = 1.0

    world.say(
        f"At {cast.scene}, {a.id} and {b.id} got ready with a grin and a glow. "
        f"{a.id} liked {cast.rhyme_a}, and {b.id} liked {cast.rhyme_b}."
    )
    world.say(
        f"They wanted to {cast.activity}, and make it look neat for the show. "
        f"Their {pose.label} needed {pose.need}, or else it might not go."
    )

    world.para()
    world.say(
        f"Then came a snag: {cast.snag}. The pose began to sway. "
        f"{a.id} reached out, {b.id} leaned in, and {helper.method} saved the day."
    )
    world.get("pose").meters["wobbly"] += 1
    world.get("pair").memes["helping"] += 1
    world.get("pair").memes["care"] += 1
    propagate(world, narrate=False)

    if world.get("pose").meters["bright"] >= THRESHOLD:
        world.say(
            f"With teamwork strong, the wobble was gone; {cast.fix}. "
            f"The pose stood tall, the smiles were gold, and the photo felt just right."
        )
    else:
        world.say(
            f"They kept on trying side by side, but the pose would not stay still. "
            f"It was a shaky little moment, and the picture missed its thrill."
        )

    world.para()
    world.say(
        f"At last they held their pose with care, and {cast.finish}. "
        f"One brave idea plus two kind hearts can make a cloudy day turn bright."
    )

    world.facts.update(
        cast=cast,
        pose=pose,
        helper=helper,
        a=a,
        b=b,
        outcome="bright" if world.get("pose").meters["bright"] >= THRESHOLD else "shaky",
        teamwork=world.get("pair").memes["helping"] >= THRESHOLD,
    )
    return world


PROMPTS = {
    "bright": [
        "Write a rhyming story about two kids who make a pose work by helping each other.",
        "Tell a teamwork story where a pose keeps wobbling until the children cooperate.",
        "Write a short rhyming tale that includes the word pose and ends with a cheerful picture.",
    ],
    "shaky": [
        "Write a rhyming story about two kids trying a pose and learning to work together.",
        "Tell a simple teamwork story with the word pose in it and a gentle ending image.",
        "Write a child-friendly rhyming story where a pose starts wobbly but the children keep trying.",
    ],
}

KNOWLEDGE = {
    "pose": [
        ("What is a pose?",
         "A pose is a way of standing or sitting on purpose, often for a picture or a show."),
    ],
    "teamwork": [
        ("What is teamwork?",
         "Teamwork means people help each other and work together toward the same goal."),
    ],
    "steady": [
        ("Why is it good to stand steady?",
         "Standing steady helps you keep your balance, so you do not wobble or fall."),
    ],
    "support": [
        ("What does support mean?",
         "Support means helping something stay up, stay safe, or stay strong."),
    ],
}
KNOWLEDGE_ORDER = ["pose", "teamwork", "steady", "support"]


def generation_prompts(world: World) -> list[str]:
    return PROMPTS[world.facts["outcome"]]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, cast, pose = f["a"], f["b"], f["cast"], f["pose"]
    qa = [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, who worked together on {pose.label}."),
        ("What problem did they face?",
         f"Their pose started to wobble, so they had to keep it steady together. "
         f"The small snag made teamwork important."),
    ]
    if f["outcome"] == "bright":
        qa.append((
            "How did they solve the problem?",
            f"They helped each other and used {f['helper'].label} to keep the pose steady. "
            f"That teamwork turned the wobble into a bright, happy picture."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a cheerful pose that looked just right. "
            f"The ending shows that working together made the day shine."
        ))
    else:
        qa.append((
            "How did they keep going?",
            f"They stayed side by side and kept trying even while the pose was shaky. "
            f"The story still ends with them learning to help one another."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["pose"].tags) | set(world.facts["helper"].tags) | {"teamwork"}
    out: list[tuple[str, str]] = []
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(cast="photo_day", pose="star_pose", helper="hold_hat",
                name_a="Mia", type_a="girl", name_b="Noah", type_b="boy"),
    StoryParams(cast="stage_day", pose="mirror_pose", helper="count_beat",
                name_a="Lia", type_a="girl", name_b="Ben", type_b="boy"),
]


def explain_rejection() -> str:
    return "(No story: that combination does not make a sensible teamwork pose.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CASTS:
        lines.append(asp.fact("cast", cid))
    for pid, p in POSES.items():
        lines.append(asp.fact("pose", pid))
        lines.append(asp.fact("need", pid, p.need))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for t in sorted(h.tags):
            lines.append(asp.fact("tag", hid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(C, P, H) :- cast(C), pose(P), helper(H), need(P, N), tag(H, N), tag(H, "support").
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryParams:
    cast: str
    pose: str
    helper: str
    name_a: str
    type_a: str
    name_b: str
    type_b: str
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.cast or args.pose or args.helper:
        combos = [c for c in combos
                  if (args.cast is None or c[0] == args.cast)
                  and (args.pose is None or c[1] == args.pose)
                  and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    cast, pose, helper = rng.choice(sorted(combos))
    type_a = args.type_a or rng.choice(["girl", "boy"])
    type_b = args.type_b or ("boy" if type_a == "girl" else "girl")
    name_a = args.name_a or rng.choice(["Mia", "Lia", "Ada", "Nia", "Zoe", "Eva"])
    name_b = args.name_b or rng.choice(["Noah", "Ben", "Kai", "Owen", "Leo", "Max"])
    return StoryParams(cast=cast, pose=pose, helper=helper, name_a=name_a, type_a=type_a, name_b=name_b, type_b=type_b)


def generate(params: StoryParams) -> StorySample:
    if params.cast not in CASTS or params.pose not in POSES or params.helper not in HELPERS:
        raise StoryError("Invalid story parameters.")
    world = tell(CASTS[params.cast], POSES[params.pose], HELPERS[params.helper],
                 Entity(id=params.name_a, kind="character", type=params.type_a, role="poser"),
                 Entity(id=params.name_b, kind="character", type=params.type_b, role="poser"))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming teamwork storyworld about pose.")
    ap.add_argument("--cast", choices=CASTS)
    ap.add_argument("--pose", choices=POSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name-a")
    ap.add_argument("--type-a", choices=["girl", "boy"])
    ap.add_argument("--name-b")
    ap.add_argument("--type-b", choices=["girl", "boy"])
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


def verify_smoke() -> int:
    rc = 0
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = format_qa(sample)
        print("OK: normal generation and QA smoke test passed.")
    except Exception as exc:
        print(f"FAIL: smoke test crashed: {exc}")
        return 1
    try:
        import asp  # noqa: F401
        py = set(valid_combos())
        cl = set(asp_valid_combos())
        if py == cl:
            print(f"OK: ASP parity matches valid_combos() ({len(py)} combos).")
        else:
            rc = 1
            print("MISMATCH in ASP parity.")
            if py - cl:
                print("  only in python:", sorted(py - cl))
            if cl - py:
                print("  only in asp:", sorted(cl - py))
    except Exception as exc:
        print(f"FAIL: ASP verification crashed: {exc}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(verify_smoke())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name_a} and {p.name_b}: {p.cast}, {p.pose}, {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
