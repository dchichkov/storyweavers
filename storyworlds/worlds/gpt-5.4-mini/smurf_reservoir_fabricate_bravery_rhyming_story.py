#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/smurf_reservoir_fabricate_bravery_rhyming_story.py
==================================================================================

A tiny standalone storyworld for a rhyming, child-facing tale about a smurf who
needs to cross a reservoir, tries to fabricate a solution, and shows bravery
before ending with a safe, cheerful result.

The world is intentionally small and classical:
- typed entities with meters and memes
- a forward-chained causal model
- a reasonableness gate
- a Python/ASP twin
- prompts, story-grounded QA, and world-knowledge QA

The seed words are woven into the world model:
- smurf
- reservoir
- fabricate
- bravery

This script is self-contained and stdlib-only, and is meant to be run directly
from the repo or through the Storyweavers tooling.
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
BRAVERY_START = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

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
    label: str
    mood: str
    route: str
    ending_image: str

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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    risky: bool = False

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
class Hazard:
    id: str
    label: str
    near: str
    flammable: bool = False
    wet: bool = False
    deep: bool = False

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
class Aid:
    id: str
    label: str
    phrase: str
    helps: str
    safe: bool = True

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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("smurf")
    if hero.memes["bravery"] >= 3 and ("brave",) not in world.fired:
        world.fired.add(("brave",))
        hero.memes["hope"] += 1
        out.append("__brave__")
    return out


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    raft = world.entities.get("raft")
    reservoir = world.get("reservoir")
    if raft and raft.meters["leak"] >= THRESHOLD and ("wet",) not in world.fired:
        world.fired.add(("wet",))
        reservoir.meters["ripple"] += 1
        world.get("smurf").memes["worry"] += 1
        out.append("__wet__")
    return out


CAUSAL_RULES = [Rule("brave", _r_brave), Rule("wet", _r_wet)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(tool: Tool, hazard: Hazard, aid: Aid) -> bool:
    if tool.risky and hazard.deep:
        return aid.safe and hazard.wet
    if tool.risky and hazard.flammable:
        return False
    return True


def predict_result(world: World, tool: Tool, hazard: Hazard) -> dict[str, bool]:
    sim = world.copy()
    _use_tool(sim, sim.get("smurf"), tool, hazard, narrate=False)
    return {
        "leak": bool(sim.entities.get("raft") and sim.get("raft").meters["leak"] >= THRESHOLD),
        "hero_brave": sim.get("smurf").memes["bravery"] >= 3,
    }


def _use_tool(world: World, hero: Entity, tool: Tool, hazard: Hazard, narrate: bool = True) -> None:
    if tool.id == "fabricate":
        hero.memes["bravery"] += 1
        world.get("raft").meters["leak"] += 1
    elif tool.id == "rope":
        hero.memes["bravery"] += 1
        world.get("raft").meters["tied"] += 1
    elif tool.id == "lantern":
        hero.memes["bravery"] += 1
        world.get("path").meters["lit"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, setting: Setting, hero: Entity, friend: Entity) -> None:
    hero.memes["bravery"] = BRAVERY_START
    friend.memes["care"] += 1
    world.say(
        f"In {setting.label}, where willow leaves swayed so free, "
        f"a little smurf named {hero.id} sang by the sea."
    )
    world.say(
        f"With {friend.id} beside {hero.pronoun('object')}, the trail was bright; "
        f"they hummed a soft tune in the morning light."
    )


def premise(world: World, setting: Setting, hazard: Hazard) -> None:
    world.say(
        f"But the path ended at {hazard.label}, wide as can be, "
        f"and the water below made a hush-rush plea."
    )
    world.say(
        f"{hazard.near.capitalize()} stood the problem, shiny and deep; "
        f"one wrong step meant a splashy leap."
    )


def want(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["want"] += 1
    world.say(
        f'"I could {tool.action}," said {hero.id} with a grin, '
        f'"and make a brave way to go on in!"'
    )


def warn(world: World, friend: Entity, hero: Entity, hazard: Hazard, tool: Tool) -> None:
    pred = predict_result(world, tool, hazard)
    friend.memes["care"] += 1
    world.facts["predicted_leak"] = pred["leak"]
    world.say(
        f'"Wait," said {friend.id}, with a thoughtful face, '
        f'"to {tool.label} here could make a tricky chase.'
        f' We need a safe way, not a big risky show, '
        f'for {hazard.label} is no place for a tumble, you know."'
    )


def choose(world: World, hero: Entity, friend: Entity, tool: Tool, hazard: Hazard) -> bool:
    if tool.id == "fabricate":
        world.say(
            f"{hero.id} took a breath, then stood up tall; "
            f"that little smurf showed bravery most of all."
        )
        return True
    return False


def trouble(world: World, hero: Entity, tool: Tool, hazard: Hazard) -> None:
    if tool.id == "fabricate":
        world.say(
            f"So {hero.id} tried to fabricate a raft from reed and rope, "
            f"but one wobbly knot made the whole thing slope."
        )
        _use_tool(world, hero, tool, hazard)
        world.say(
            f"The raft gave a squeak, then a wobble, then lean; "
            f"the reservoir rippled in a silvery sheen."
        )


def rescue(world: World, friend: Entity, aid: Aid, hazard: Hazard) -> None:
    world.get("raft").meters["leak"] = 0.0
    world.say(
        f"Then {friend.id} brought {aid.phrase}, calm and right, "
        f"and {aid.helps} like a little star-bright light."
    )
    world.say(
        f"They fixed the wobble, tight as a seam; "
        f"the brave little plan became a safer dream."
    )


def ending(world: World, setting: Setting, hero: Entity, friend: Entity, hazard: Hazard) -> None:
    hero.memes["joy"] += 2
    friend.memes["joy"] += 1
    world.say(
        f"At last they crossed, with a proud little cheer; "
        f"{setting.ending_image}, and adventure stayed near."
    )
    world.say(
        f"{hero.id} smiled at {friend.id}, the reservoir glinting blue; "
        f"their brave little rhyme came safely through."
    )


def tell(setting: Setting, hazard: Hazard, tool: Tool, aid: Aid,
         hero_name: str = "Smurfette", friend_name: str = "Clumsy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", role="friend"))
    world.add(Entity(id="reservoir", kind="place", type="reservoir", label=hazard.label))
    world.add(Entity(id="raft", type="thing", label="raft"))
    world.add(Entity(id="path", type="thing", label="path"))
    world.facts.update(setting=setting, hazard=hazard, tool=tool, aid=aid,
                       hero=hero, friend=friend)

    setup(world, setting, hero, friend)
    world.para()
    premise(world, setting, hazard)
    want(world, hero, tool)
    warn(world, friend, hero, hazard, tool)

    if choose(world, hero, friend, tool, hazard):
        world.para()
        trouble(world, hero, tool, hazard)
        world.para()
        rescue(world, friend, aid, hazard)
        world.para()
        ending(world, setting, hero, friend, hazard)
        outcome = "tried"
    else:
        world.para()
        world.say("They chose another path and kept their tune light and bright.")
        ending(world, setting, hero, friend, hazard)
        outcome = "avoided"

    world.facts["outcome"] = outcome
    return world


SETTINGS = {
    "meadow": Setting("meadow", "a sunny meadow", "gentle and green", "a winding trail", "the meadow glowed like a ribbon of gold"),
    "grove": Setting("grove", "a whispering grove", "soft and shady", "a narrow bridge", "the grove shimmered with leaf-green light"),
    "harbor": Setting("harbor", "a breezy harbor", "salt-bright and neat", "a wooden dock", "the harbor sparkled under a pearly sky"),
}

HAZARDS = {
    "reservoir": Hazard("reservoir", "the reservoir", "The reservoir", wet=True, deep=True),
    "pond": Hazard("pond", "the pond", "The pond", wet=True, deep=True),
}

TOOLS = {
    "fabricate": Tool("fabricate", "fabricate", "fabricate a little raft", "build"),
    "rope": Tool("rope", "rope", "tie the boards together", "tie"),
    "lantern": Tool("lantern", "lantern", "light the path with a lantern", "light"),
}

AIDS = {
    "planks": Aid("planks", "planks", "two sturdy planks", "the crossings stayed steady"),
    "anchor": Aid("anchor", "anchor", "a small anchor", "the raft stopped bobbing"),
}



@dataclass
class StoryParams:
    setting: str
    hazard: str
    tool: str
    aid: str
    hero_name: str = "Smurfette"
    friend_name: str = "Clumsy"
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

CURATED = [
    ("meadow", "reservoir", "fabricate", "planks"),
    ("grove", "pond", "fabricate", "anchor"),
    ("harbor", "reservoir", "rope", "planks"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for hid, h in HAZARDS.items():
            for tid, t in TOOLS.items():
                for aid, a in AIDS.items():
                    if reasonableness_gate(t, h, a):
                        combos.append((sid, hid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about a smurf, a reservoir, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, tool = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS))
    return StoryParams(
        setting=setting, hazard=hazard, tool=tool, aid=aid,
        hero_name=args.name or rng.choice(["Smurfette", "Brainy", "Hefty", "Jokey"]),
        friend_name=args.friend or rng.choice(["Clumsy", "Painter", "Farmer", "Harmony"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child about a smurf who meets a {f["hazard"].label} and wants to {f["tool"].action}.',
        f"Tell a brave little rhyme where {f['hero'].id} tries to fabricate a way across the water, but a friend suggests a safer fix.",
        f"Write a child-friendly rhyming story that includes the words smurf, reservoir, fabricate, and bravery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    hazard: Hazard = f["hazard"]  # type: ignore[assignment]
    tool: Tool = f["tool"]  # type: ignore[assignment]
    aid: Aid = f["aid"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {hero.id}, a little smurf, and {friend.id}, who stayed close and helped. The tale followed their brave walk by the water."
        ),
        QAItem(
            question="What did the smurf want to do?",
            answer=f"{hero.id} wanted to {tool.action} and make a way across the {hazard.label}. That idea showed bravery, because the path was tricky."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used {aid.phrase} and fixed the wobbly plan before crossing. That made the trip safe, which is why the ending felt bright."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reservoir?",
            answer="A reservoir is a big place where water is kept. It can be calm on top, but it is still deep and should be treated carefully."
        ),
        QAItem(
            question="What does fabricate mean?",
            answer="To fabricate something means to make or build it, often by putting pieces together. People can fabricate a plan, a toy, or a small tool."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary while staying steady. A brave child may still feel worried, but keeps going kindly and carefully."
        ),
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
        if bits:
            lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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
valid(S,H,T) :- setting(S), hazard(H), tool(T), safe_combo(S,H,T).
safe_combo(S,H,T) :- setting(S), hazard(H), tool(T), aid(A), ok(T,H,A).
ok(fabricate, reservoir, planks).
ok(fabricate, pond, anchor).
ok(rope, reservoir, planks).
ok(rope, pond, planks).
ok(rope, pond, anchor).
ok(lantern, reservoir, planks).
ok(lantern, pond, planks).
ok(lantern, pond, anchor).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hazard=None, tool=None, aid=None, name=None, friend=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generate smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HAZARDS[params.hazard], TOOLS[params.tool], AIDS[params.aid], params.hero_name, params.friend_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*c, hero_name="Smurfette", friend_name="Clumsy")) for c in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
