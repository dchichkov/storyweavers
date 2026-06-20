#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/physical_friendship_twist_folk_tale.py
======================================================================

A standalone storyworld for a tiny folk-tale domain about two friends, a
physical challenge, and a twist that turns the ending.

Seed premise
------------
A small village has a special bridge, a slippery stream, a lost bundle, or a
broken cart path. Two friends try to solve a practical problem together. The
physical world matters: weight, reach, balance, distance, and carried items
change what happens. The twist is not a random gimmick; it is a state change in
the world that reveals the friends' kindness, resourcefulness, or trust.

This world keeps a folk-tale feel:
- concrete names and simple repeated phrasing
- a clear beginning, middle turn, and ending image
- a moral-like resolution rooted in friendship
- small, authored prose, not a template log

It supports:
- default generation, -n, --all, --seed, --trace, --qa, --json
- --asp, --verify, --show-asp
- a Python reasonableness gate plus an inline ASP twin
- state-driven QA from simulated world facts

The word "physical" is intentionally included in the domain vocabulary and can
appear in story text and QA.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
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
    detail: str
    mood: str
    affords: set[str] = field(default_factory=set)

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
class Challenge:
    id: str
    label: str
    need: str
    risk: str
    heavy: bool = False
    slippery: bool = False
    far: bool = False
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
class HelperTool:
    id: str
    label: str
    use: str
    safe: bool = True
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
class Twist:
    id: str
    reveal: str
    consequence: str
    ending_image: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

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


def _r_weight(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["carrying"] >= THRESHOLD and ("back" not in e.attrs):
            if ("weight" + e.id) in world.fired:
                continue
            world.fired.add(("weight" + e.id,))
            e.memes["strain"] += 1
            out.append("__weight__")
    return out


def _r_slip(world: World) -> list[str]:
    out = []
    if world.facts.get("wet_ground") and world.facts.get("carrying_bridge") and not world.facts.get("has_rope"):
        if ("slip",) in world.fired:
            return out
        world.fired.add(("slip",))
        for e in world.characters():
            e.memes["alarm"] += 1
        world.get("challenge").meters["stuck"] += 1
        out.append("__slip__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    rules = [Rule("weight", _r_weight), Rule("slip", _r_slip)]
    while changed:
        changed = False
        for r in rules:
            s = r.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable_combo(setting: Setting, challenge: Challenge, tool: HelperTool, twist: Twist) -> bool:
    if challenge.heavy and tool.id != "cart":
        return False
    if challenge.slippery and tool.id != "rope":
        return False
    if challenge.far and tool.id not in {"rope", "lantern"}:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for cid, c in CHALLENGES.items():
            if sid not in s.affords:
                continue
            for tid, t in TOOLS.items():
                for wid, w in TWISTS.items():
                    if reasonable_combo(s, c, t, w):
                        combos.append((sid, cid, tid, wid))
    return combos


def _move(world: World, hero: Entity, amount: float, item: Entity) -> None:
    hero.meters["carrying"] += amount
    item.meters["carried"] += amount


def _act(world: World, hero: Entity, friend: Entity, challenge: Challenge, tool: Optional[HelperTool]) -> None:
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"In {world.setting.place}, {hero.id} and {friend.id} were close as two sparks in the same fire. "
        f"{world.setting.detail} They set out to solve a physical problem by the stream."
    )
    world.say(
        f"They found {challenge.label}, and the trouble was plain: it was {challenge.need}, "
        f"and the ground around it was {challenge.risk}."
    )
    if tool:
        world.say(f"{friend.id} held up {tool.label} and said, \"Let us use this wisely.\"")
    else:
        world.say(f"{friend.id} looked at the trouble and said, \"We must think before we lift.\"")


def _warning(world: World, hero: Entity, friend: Entity, challenge: Challenge) -> None:
    hero.memes["want"] += 1
    friend.memes["caution"] += 1
    world.say(
        f"{hero.id} wanted to hurry, for the bundle looked small from far away. "
        f"But {friend.id} touched {hero.pronoun('possessive')} sleeve and warned that a careless step could make the load slip."
    )


def _twist_reveal(world: World, twist: Twist, hero: Entity, friend: Entity) -> None:
    hero.memes["surprise"] += 1
    friend.memes["surprise"] += 1
    world.say(twist.reveal)


def _resolve(world: World, challenge: Challenge, tool: HelperTool, twist: Twist) -> None:
    world.say(
        f"Together they used {tool.label} {tool.use}, and the work became slow but sure."
    )
    world.say(twist.consequence)
    world.say(twist.ending_image)


SETTINGS = {
    "stream": Setting("stream", "the stream path", "The brook sang under the stones, and willow branches hung low.", "bright", {"bundle", "bridge", "cart"}),
    "hill": Setting("hill", "the hill road", "The road climbed high, with grass bending like combed hair.", "windy", {"cart", "basket", "lantern"}),
    "market": Setting("market", "the market lane", "Stalls stood side by side, and the cobbles shone after morning rain.", "busy", {"basket", "cart", "bundle"}),
}

CHALLENGES = {
    "bundle": Challenge("bundle", "a lost bundle of cloth", "light enough to carry, but awkward in two hands", "damp and slick", heavy=False, slippery=True, far=False, tags={"physical", "bundle"}),
    "cart": Challenge("cart", "a broken cart wheel", "too heavy to move alone", "far from the shed", heavy=True, slippery=False, far=False, tags={"physical", "cart"}),
    "lamp": Challenge("lamp", "a lantern left on a branch", "far above the path", "wet and dark beneath", heavy=False, slippery=False, far=True, tags={"physical", "lamp"}),
}

TOOLS = {
    "rope": HelperTool("rope", "a sturdy rope", "to lower it carefully"),
    "cart": HelperTool("cart", "the village cart", "to bear the weight"),
    "lantern": HelperTool("lantern", "a lantern", "to light the way"),
}

TWISTS = {
    "bird": Twist("bird", "Then a blackbird swooped down and tugged at the cloth, showing that the bundle had been caught on a thorn.", "That meant the friends no longer had to wrestle it from the water; they only had to free it gently.", "By and by, the bundle lay on the grass like a rescued blanket, and the blackbird hopped away with a bright feather in its beak.", {"twist", "friendship"}),
    "grandma": Twist("grandma", "Then they found that the 'heavy' cart was not a trap at all: old Grandma had tied the wheel with a knot only she could undo.", "That meant the friends could fix the wheel by following her knot, not by forcing the wood.", "Soon the cart rolled again, and the friends pushed it side by side under the evening sky.", {"twist", "friendship"}),
    "hidden_key": Twist("hidden_key", "Then, tucked beneath the stone, they found a little brass key with their names scratched on it.", "That key opened the shed and revealed the missing hook, which made the whole task simple.", "At last the lantern shone over the hook, and the friends laughed as the path grew bright.", {"twist", "friendship"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    challenge: str
    tool: str
    twist: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
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


GIRL_NAMES = ["Mina", "Tessa", "Nora", "Lila", "Sana", "Ivy"]
BOY_NAMES = ["Pip", "Jon", "Oren", "Milo", "Toby", "Finn"]


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    challenge = CHALLENGES[params.challenge]
    tool = TOOLS[params.tool]
    twist = TWISTS[params.twist]
    world = World(setting)
    hero = world.add(Entity(params.hero, "character", params.hero_gender, role="hero"))
    friend = world.add(Entity(params.friend, "character", params.friend_gender, role="friend"))
    ch = world.add(Entity("challenge", "thing", challenge.label))
    world.facts["wet_ground"] = challenge.slippery
    world.facts["carrying_bridge"] = challenge.heavy or challenge.far
    world.facts["has_rope"] = tool.id == "rope"

    _act(world, hero, friend, challenge, tool)
    world.para()
    _warning(world, hero, friend, challenge)

    if challenge.heavy:
        _move(world, hero, 2.0, ch)
    elif challenge.slippery:
        _move(world, hero, 1.0, ch)
    else:
        _move(world, hero, 0.5, ch)
    propagate(world, narrate=False)

    world.say(
        f"At first the work seemed impossible. Then the friends remembered how each one could do only part of the task."
    )
    world.para()
    _twist_reveal(world, twist, hero, friend)
    world.para()
    _resolve(world, challenge, tool, twist)
    world.facts.update(hero=hero, friend=friend, challenge=challenge, tool=tool, twist=twist,
                       setting=setting, outcome="twist")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ch = f["challenge"]
    tw = f["twist"]
    return [
        f"Write a folk tale for a young child about friendship and a physical problem involving {ch.label}.",
        f"Tell a warm story where two friends face {ch.label}, discover a twist, and finish with a gentle, happy image.",
        f'Write a story that includes the word "physical" and ends by showing how the friends changed the world together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    challenge = f["challenge"]
    twist = f["twist"]
    return [
        QAItem(
            question="Who are the story's friends?",
            answer=f"The story is about {hero.id} and {friend.id}, who stayed together and shared the work."
        ),
        QAItem(
            question="What physical trouble did they face?",
            answer=f"They faced {challenge.label}, which was {challenge.need}. The work needed careful hands and a calm plan."
        ),
        QAItem(
            question="What was the twist?",
            answer=f"{twist.reveal} That changed the problem from a hard struggle into something the friends could solve gently."
        ),
        QAItem(
            question="How did the ending prove the friends helped each other?",
            answer=f"They finished side by side, and the ending image shows {twist.ending_image.lower()}"
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem("What does physical mean?", "Physical means something real and body-like, such as weight, balance, distance, or touch. It is about the things you can feel and move."),
        QAItem("Why do friends work better together?", "Friends can share the load and notice things one person might miss. That makes a hard task easier and safer."),
    ]
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combo_reason(setting: Setting, challenge: Challenge, tool: HelperTool) -> bool:
    return reasonable_combo(setting, challenge, tool, TWISTS["bird"])


def valid_combos_python() -> list[tuple[str, str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
valid(S, C, T, W) :- setting(S), challenge(C), tool(T), twist(W), afford(S, C), compatible(C, T).
compatible(bundle, rope).
compatible(cart, cart).
compatible(lamp, rope).
compatible(lamp, lantern).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for c in s.affords:
            lines.append(asp.fact("afford", sid, c))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for wid in TWISTS:
        lines.append(asp.fact("twist", wid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos_python())
    if a == p:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only in asp:", sorted(a - p))
        print("  only in python:", sorted(p - a))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generate smoke test succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale storyworld about friendship, a physical task, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    combos = valid_combos_python()
    if args.setting or args.challenge or args.tool:
        combos = [c for c in combos
                  if (args.setting is None or c[0] == args.setting)
                  and (args.challenge is None or c[1] == args.challenge)
                  and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, challenge, tool, twist = rng.choice(sorted(combos))
    challenge_obj = CHALLENGES[challenge]
    gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    return StoryParams(setting, challenge, tool, twist, hero, gender, friend, friend_gender)


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
    StoryParams("stream", "bundle", "rope", "bird", "Mina", "girl", "Pip", "boy"),
    StoryParams("hill", "cart", "cart", "grandma", "Toby", "boy", "Nora", "girl"),
    StoryParams("market", "lamp", "lantern", "hidden_key", "Lila", "girl", "Finn", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
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
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
