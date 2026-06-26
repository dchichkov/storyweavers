#!/usr/bin/env python3
"""
A small storyworld about a gulf-side ghost story where teamwork and a little
magic help children handle a cautionary mystery safely.

The premise is simple: a child hears about a glow drifting over the gulf at
night. The child wants to follow it, but the older helper knows the wind, the
rocks, and the water can be dangerous. The story turns when they work together,
use a small charm lantern, and choose a safe way to look without going too far.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    weather: str
    features: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    effect: str
    safety: str
    phrase: str


@dataclass
class StoryParams:
    place: str
    charm: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


THRESHOLD = 1.0


def _warn_risk(world: World, child: Entity, helper: Entity, charm: Charm) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{child.id} loved the hush of the gulf at night and kept staring at the blue glow beyond the rocks."
    )
    world.say(
        f'But {helper.label} said, "Do not follow a light that you do not understand; the tide and stones can trick a sleepy walker."'
    )


def _teamwork(world: World, child: Entity, helper: Entity, charm: Charm) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    helper.memes["care"] = helper.memes.get("care", 0.0) + 1
    world.say(
        f"Instead of going alone, {child.id} and {helper.id} tied a rope to the porch post, carried {charm.label}, and walked together to the edge of the path."
    )


def _magic(world: World, child: Entity, helper: Entity, charm: Charm) -> None:
    child.meters["safe_light"] = child.meters.get("safe_light", 0.0) + 1
    helper.meters["safe_light"] = helper.meters.get("safe_light", 0.0) + 1
    world.say(
        f"The little {charm.label} glimmered softly and showed the wet stones, the black water, and the gap where the surf could grab a foot."
    )


def _resolve(world: World, child: Entity, helper: Entity, charm: Charm) -> None:
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(
        f"At last they saw the glow was only moonlight on flying spray, and the ghostly shape was a drifting fishing net, not a lost spirit."
    )
    world.say(
        f"{child.id} laughed, because the mystery had been scary from far away but ordinary up close, and {helper.id} was right to be careful."
    )
    world.say(
        f"By the time they went home, {child.id} still held {charm.effect}, and the gulf looked beautiful instead of dangerous."
    )


def tell(setting: Setting, charm: Charm, name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=helper_type))
    lantern = world.add(Entity(id=charm.id, type="charm", label=charm.label, phrase=charm.phrase, owner=child.id))

    child.meters["curiosity"] = 1
    child.memes["curiosity"] = 1
    lantern.carried_by = child.id

    world.say(
        f"{child.id} was a {trait} {gender} who lived near the gulf and liked ghost stories."
    )
    world.say(
        f"One evening, {child.id} found {charm.phrase}, a tiny charm that seemed to hold a friendly kind of magic."
    )

    world.para()
    _warn_risk(world, child, helper, charm)

    world.para()
    _teamwork(world, child, helper, charm)
    _magic(world, child, helper, charm)
    _resolve(world, child, helper, charm)

    world.facts.update(
        child=child,
        helper=helper,
        charm=lantern,
        setting=setting,
        charm_cfg=charm,
        trait=trait,
    )
    return world


SETTINGS = {
    "gulf": Setting(place="the gulf shore", weather="windy", features={"gulf", "water", "night"}),
}

CHARMS = {
    "lantern": Charm(
        id="lantern",
        label="lantern charm",
        effect="its tiny golden glow",
        safety="steady light",
        phrase="a small lantern charm with a glass bead",
    ),
    "shell": Charm(
        id="shell",
        label="shell charm",
        effect="its pearly shimmer",
        safety="gentle light",
        phrase="a shell charm that hummed like a soft song",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Rosa", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Leo", "Max"]
TRAITS = ["brave", "curious", "quiet", "lively", "careful", "dreamy"]


KNOWLEDGE = {
    "gulf": [
        QAItem(
            question="What is a gulf?",
            answer="A gulf is a large part of the sea that reaches into the land.",
        )
    ],
    "ghost": [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale that feels spooky or mysterious, even when nothing magical is truly there.",
        )
    ],
    "lantern": [
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives off light so people can see in the dark.",
        )
    ],
    "together": [
        QAItem(
            question="Why do people work together?",
            answer="People work together so they can do hard jobs more safely and more easily.",
        )
    ],
    "careful": [
        QAItem(
            question="Why should you be careful near water at night?",
            answer="You should be careful near water at night because it is dark, and rocks or waves can be hard to see.",
        )
    ],
}


ASP_RULES = r"""
% A child is cautious when a mystery light is near water at night.
cautionary(S) :- setting(S), night(S), water(S).

% Teamwork means the child and helper both contribute to a safe choice.
teamwork(C,H) :- child(C), helper(H), walk_together(C,H), carry_charm(C).

% Magic is present when the charm produces safe_light.
magic(L) :- charm(L), safe_light(L).

% A story is valid when the gulf setting, teamwork, and a cautionary reason all exist.
valid_story(P, C, H, L) :- gulf(P), child(C), helper(H), charm(L),
                           cautionary(P), teamwork(C,H), magic(L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("gulf", pid))
        lines.append(asp.fact("setting", pid))
        if "night" in s.features:
            lines.append(asp.fact("night", pid))
        if "water" in s.features:
            lines.append(asp.fact("water", pid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if "glow" in c.effect or "light" in c.effect:
            lines.append(asp.fact("safe_light", cid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("walk_together", "child", "helper"))
    lines.append(asp.fact("carry_charm", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("gulf", charm, gender) for charm in CHARMS for gender in ("girl", "boy")]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((place, charm, gender) for place, charm, gender in valid_combos())
    cl = set((p, c, h) for p, c, h, _ in asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world at the gulf.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
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
    if args.gender == "girl":
        default_name = rng.choice(GIRL_NAMES)
    elif args.gender == "boy":
        default_name = rng.choice(BOY_NAMES)
    else:
        default_name = rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = args.gender or ("girl" if default_name in GIRL_NAMES else "boy")
    helper = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    charm = args.charm or rng.choice(list(CHARMS))
    name = args.name or default_name
    return StoryParams(place="gulf", charm=charm, name=name, gender=gender, helper=helper, trait=rng.choice(TRAITS))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, charm = f["child"], f["helper"], f["charm"]
    return [
        f'Write a short ghost story for a child named {child.id} near the gulf that includes teamwork and magic.',
        f"Tell a cautionary story where {child.id} and {helper.id} must be careful at the gulf, but a charm helps them see safely.",
        f"Write a gentle spooky tale about {child.id}, {helper.id}, and {charm.label} at night by the water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, charm = f["child"], f["helper"], f["charm"]
    return [
        QAItem(
            question=f"Where did {child.id} go in the story?",
            answer=f"{child.id} went to the gulf shore with {helper.id}.",
        ),
        QAItem(
            question=f"What worried {helper.id} about the ghostly glow?",
            answer="The glow could lead someone toward dark water and slippery rocks at night.",
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} handle the spooky mystery?",
            answer=f"They worked together and used the {charm.label} so they could look safely.",
        ),
        QAItem(
            question=f"What did the magic charm help them see?",
            answer="It helped them see the wet stones, the water, and the thing that made the glow look spooky from far away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ("gulf", "ghost", "lantern", "together", "careful"):
        out.extend(KNOWLEDGE[key])
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
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CHARMS[params.charm], params.name, params.gender, params.helper, params.trait)
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
    StoryParams(place="gulf", charm="lantern", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="gulf", charm="shell", name="Theo", gender="boy", helper="aunt", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
