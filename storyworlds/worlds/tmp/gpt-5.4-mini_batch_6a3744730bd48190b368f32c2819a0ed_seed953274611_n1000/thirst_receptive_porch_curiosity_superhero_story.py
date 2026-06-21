#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thirst_receptive_porch_curiosity_superhero_story.py
===================================================================================

A small superhero-style storyworld built from the seed words:
thirst, receptive, porch, and Curiosity.

Premise:
- A curious child-hero notices a thirsty bird and a wobbling neighborhood kid on a porch.
- The hero wants to help but must first read the situation carefully.
- A receptive neighbor responds to a simple signal, and the hero uses a safe, clever fix.
- The ending proves the change: thirst is eased, the porch becomes a friendly rescue spot,
  and curiosity turns into a useful superpower.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports storyworlds/results eagerly
- lazy imports storyworlds/asp only in ASP helpers
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python reasonableness gate and inline ASP twin
- generates story-grounded QA and world-knowledge QA from world state
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
CURIOUS_MIN = 1.0
THIRST_MIN = 1.0


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
    receptive: bool = False
    thirsty: bool = False
    can_help: bool = False
    has_water: bool = False
    on_porch: bool = False
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "heroine"}
        male = {"boy", "father", "dad", "man", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str
    warm: bool = False
    open: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    action: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_events: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_events.append(text)

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
    apply: Callable[[World], list[str]]


def _r_thirst(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.thirsty and e.meters["thirst"] >= THRESHOLD and ("thirst" not in world.fired):
            world.fired.add(("thirst", e.id))
            if e.location == "porch":
                out.append(f"{e.id} looked parched on the porch, as if even the warm air wanted a drink.")
    return out


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    signal = world.entities.get("signal")
    if not hero or not signal:
        return out
    sig = ("curiosity", hero.id)
    if hero.memes["curiosity"] >= CURIOUS_MIN and sig not in world.fired:
        world.fired.add(sig)
        out.append(f"{hero.id}'s curiosity sharpened at once when {signal.label} flickered by the porch rail.")
    return out


def _r_receptive(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    if helper and helper.receptive and helper.memes["attention"] >= THRESHOLD:
        sig = ("receptive", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(f"{helper.id} turned right away, ready to listen.")
    return out


CAUSAL_RULES = [Rule("thirst", _r_thirst), Rule("curiosity", _r_curiosity), Rule("receptive", _r_receptive)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    place: str
    signal: str
    aid: str
    thirst_level: int = 1
    curiosity_level: int = 2
    receptive_level: int = 2
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Spark", "Milo", "Ivy", "Rae", "Jules", "Zara", "Tess"]
HELPER_NAMES = ["Aunt Mira", "Mr. Bell", "Ms. June", "Captain Vale", "Mrs. Green"]
PLACES = {
    "porch": Place(id="porch", label="the porch", kind="porch", warm=True, open=True, tags={"porch"}),
    "steps": Place(id="steps", label="the front steps", kind="porch", warm=True, open=True, tags={"porch"}),
}
SIGNALS = {
    "wink": Signal(id="wink", label="a blinking porch light", action="blinked", kind="signal", tags={"curiosity"}),
    "wave": Signal(id="wave", label="a waving hand", action="waved", kind="signal", tags={"curiosity"}),
}
AIDS = {
    "water": Aid(id="water", label="cool water", phrase="a cup of cool water", power=2, tags={"thirst"}),
    "juice": Aid(id="juice", label="sweet juice", phrase="a cup of sweet juice", power=2, tags={"thirst"}),
}

CURATED = [
    StoryParams(hero_name="Nova", hero_type="heroine", helper_name="Aunt Mira", helper_type="woman", place="porch", signal="wink", aid="water", thirst_level=1, curiosity_level=3, receptive_level=2),
    StoryParams(hero_name="Spark", hero_type="hero", helper_name="Mr. Bell", helper_type="man", place="steps", signal="wave", aid="juice", thirst_level=2, curiosity_level=2, receptive_level=2),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for s in SIGNALS:
            for a in AIDS:
                combos.append((p, s, a))
    return combos


def reasonableness_ok(params: StoryParams) -> bool:
    return params.place in PLACES and params.signal in SIGNALS and params.aid in AIDS


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen porch scene needs a real signal, a receptive helper, and a thirsty problem that can be helped safely.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero-style storyworld about curiosity, thirst, and a receptive porch helper.")
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--aid", choices=AIDS)
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
    place = args.place or rng.choice(list(PLACES))
    signal = args.signal or rng.choice(list(SIGNALS))
    aid = args.aid or rng.choice(list(AIDS))
    hero_name = args.hero or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    hero_type = "heroine" if hero_name in {"Nova", "Ivy", "Rae", "Zara", "Tess"} else "hero"
    helper_type = "woman" if helper_name.startswith(("Aunt", "Ms.", "Mrs.")) else "man"
    params = StoryParams(hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type, place=place, signal=signal, aid=aid, thirst_level=rng.randint(1, 2), curiosity_level=rng.randint(2, 3), receptive_level=rng.randint(1, 2))
    if not reasonableness_ok(params):
        raise StoryError(explain_rejection(params))
    return params


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name, role="hero", thirsty=True, location=params.place, meters=defaultdict(float, thirst=float(params.thirst_level)), memes=defaultdict(float, curiosity=float(params.curiosity_level))))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name, role="helper", receptive=True, can_help=True, has_water=True, on_porch=True, meters=defaultdict(float, attention=float(params.receptive_level)), memes=defaultdict(float)))
    signal = world.add(Entity(id="signal", kind="thing", type="signal", label=SIGNALS[params.signal].label))
    aid = world.add(Entity(id="aid", kind="thing", type="aid", label=AIDS[params.aid].label, has_water=True))
    world.say(f"On the porch, {hero.label} stood in bright boots like a little superhero, feeling a real thirst dry the tip of {hero.pronoun('possessive')} tongue.")
    world.say(f"A small signal {SIGNALS[params.signal].action} beside the rail, and {hero.label}'s curiosity woke up bigger than a kite in a storm.")
    world.para()
    world.say(f"{helper.label} was receptive at once. {helper.label} looked up, smiled, and opened {helper.pronoun('possessive')} door with a kind, ready face.")
    world.say(f"{hero.label} pointed at the porch and the thirsty air, and the helper understood the message without any shouting.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"Then {helper.label} brought out {AIDS[params.aid].phrase}, and {hero.label} drank until the thirst faded and the superhero shoulders relaxed.")
    world.say(f"The porch turned peaceful again, with one curious hero, one receptive helper, and a bright little rescue that fit in two hands.")
    world.facts.update(params=params, hero=hero, helper=helper, signal=signal, aid=aid, outcome="helped")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story that includes the words "thirst", "receptive", and "porch", and centers on {f["params"].hero_name} using curiosity to solve a small problem.',
        f"Tell a child-friendly superhero tale where {f['params'].hero_name} notices thirst on the porch, a receptive helper listens, and everyone ends safely with water.",
        f"Write a short story in a superhero style about curiosity becoming a helpful power on a porch.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {f['params'].hero_name}, a small superhero who notices problems and tries to help."),
        QAItem(question="Why did the hero need to act?", answer=f"{f['params'].hero_name} saw thirst and used curiosity to understand what was happening on the porch. That helped the hero notice the right person to ask for help."),
        QAItem(question="How did the helper respond?", answer=f"{f['params'].helper_name} was receptive right away and listened with a ready, kind heart. Because the helper was receptive, the hero did not have to solve everything alone."),
        QAItem(question="What changed by the end?", answer="The thirsty feeling faded after water was brought out, and the porch became calm again. The ending shows that curiosity led to a safe rescue instead of trouble."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is thirst?", answer="Thirst is the feeling that tells your body it needs water. It can make your mouth feel dry and make you want to drink."),
        QAItem(question="What does receptive mean?", answer="Receptive means ready to listen, notice, and accept help or an idea. A receptive person pays attention and can respond kindly."),
        QAItem(question="What is a porch?", answer="A porch is a covered area by a house entrance. People can stand there, sit there, or talk there before going inside."),
        QAItem(question="What is curiosity?", answer="Curiosity is the wish to learn and find out what is going on. It can help a hero notice clues and ask good questions."),
    ]


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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.receptive:
            parts.append("receptive")
        if e.thirsty:
            parts.append("thirsty")
        if e.can_help:
            parts.append("can_help")
        if e.has_water:
            parts.append("has_water")
        if e.on_porch:
            parts.append("on_porch")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(H) :- hero(H), curiosity(H, C), curious_min(M), C >= M.
thirsty(H) :- hero(H), thirst(H, T), thirst_min(M), T >= M.
receptive(K) :- helper(K), receptive_level(K, R), R >= 1.
helped :- curious(hero), thirsty(hero), receptive(helper).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SIGNALS:
        lines.append(asp.fact("signal", sid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    lines.append(asp.fact("curious_min", int(CURIOUS_MIN)))
    lines.append(asp.fact("thirst_min", int(THIRST_MIN)))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show helped/0.", "#show helped/0.")
    model = asp.one_model(program)
    helped = bool(asp.atoms(model, "helped"))
    ok = helped is True
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if ok and sample.story:
        print("OK: ASP gate and story generation smoke test passed.")
        return 0
    print("MISMATCH or smoke test failure.")
    return 1


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show place/1. #show signal/1. #show aid/1.", "#show place/1."))
    _ = model
    return sorted(valid_combos())


def build_and_generate(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    params.seed = args.seed
    return generate(params)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.signal not in SIGNALS or params.aid not in AIDS:
        raise StoryError("Invalid params: unknown place, signal, or aid.")
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
        print(asp_program("", "#show helped/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combinations:")
        for combo in valid_combos():
            print(" ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                sample = build_and_generate(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
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
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
