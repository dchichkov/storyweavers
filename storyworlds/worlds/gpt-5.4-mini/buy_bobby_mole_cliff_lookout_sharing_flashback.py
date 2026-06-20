#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/buy_bobby_mole_cliff_lookout_sharing_flashback.py
=================================================================================

A standalone storyworld for a tiny mythic domain set at a cliff lookout.

Seeded premise:
- Words: buy, bobby, mole
- Setting: cliff lookout
- Features: Sharing, Flashback
- Style: Myth

World idea:
A child named Bobby comes to a cliff lookout with a bought snack or charm.
A shy mole appears near the lookout stones. A remembered flashback shows that
Bobby once received kindness when lost in a storm. That memory turns Bobby from
keeping the treat to sharing it. The shared offering calms the mole, reveals a
safe path, and the ending proves a changed bond: food divided, fear reduced, and
the lookout feels warmer than before.

Contract notes:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
- includes Python reasonableness gate and inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.meters = {**{"hunger": 0.0, "fear": 0.0, "trust": 0.0, "warmth": 0.0}, **self.meters}
        self.memes = {**{"joy": 0.0, "memory": 0.0, "sharing": 0.0}, **self.memes}

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
    horizon: str
    mood: str

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
class Offering:
    id: str
    label: str
    phrase: str
    shared_phrase: str
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
class Creature:
    id: str
    label: str
    type: str = "mole"
    shy: bool = True
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
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


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    b = world.entities.get("bobby")
    m = world.entities.get("mole")
    if not b or not m:
        return out
    if b.memes["sharing"] >= THRESHOLD and m.meters["trust"] >= THRESHOLD:
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("lookout").meters["warmth"] += 1
            out.append("__calm__")
    return out


def _r_open_path(world: World) -> list[str]:
    look = world.get("lookout")
    mole = world.entities.get("mole")
    if look.meters["warmth"] >= THRESHOLD and mole and mole.meters["trust"] >= THRESHOLD:
        sig = ("path",)
        if sig not in world.fired:
            world.fired.add(sig)
            look.meters["safety"] += 1
            return ["__path__"]
    return []


RULES = [Rule("calm", _r_calm), Rule("open_path", _r_open_path)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def can_share(offering: Offering) -> bool:
    return "share" in offering.tags


def reasonableness_gate(offering: Offering, setting: Setting, creature: Creature) -> bool:
    return can_share(offering) and setting.id == "cliff_lookout" and creature.type == "mole"


def flashback_line(world: World, bobby: Entity) -> str:
    if bobby.memes["memory"] >= THRESHOLD:
        return (
            f"As the wind rose, Bobby remembered a far older night: when {bobby.pronoun()} had been lost, "
            f"a kindly traveler shared bread and stayed until the stars found the road."
        )
    return ""


def set_scene(world: World, setting: Setting) -> None:
    world.say(
        f"At the cliff lookout, where the sea wore a silver crown, Bobby stood beside the stone wall. "
        f"The place was all salt wind, bright sky, and long shadows leaning over the edge."
    )
    world.say(
        f"Bobby had gone there after {world.facts['purchase']}, carrying {world.facts['offering'].phrase} "
        f"wrapped in a cloth as careful as a secret."
    )


def meet_mole(world: World, bobby: Entity, mole: Entity, offering: Offering) -> None:
    bobby.memes["joy"] += 1
    mole.meters["fear"] += 1
    world.say(
        f"Then a small mole peeped from between the cliff stones. Its whiskers trembled in the wind, "
        f"and its dark nose twitched toward {offering.label}."
    )
    world.say(
        f'"Please," whispered the mole, "the path below is cold, and I am far from my hill."'
    )


def remember_and_choose(world: World, bobby: Entity, mole: Entity, offering: Offering) -> None:
    bobby.memes["memory"] += 1
    world.say(flashback_line(world, bobby))
    world.say(
        f"Bobby looked at {offering.label}, then at the little mole, and felt the remembered kindness "
        f"wake up like a lantern."
    )
    bobby.memes["sharing"] += 1
    bobby.meters["warmth"] += 1
    mole.meters["trust"] += 1
    world.say(
        f'"Here," Bobby said, and broke the {offering.label} in two. "{offering.shared_phrase}."'
    )


def resolve(world: World, setting: Setting, mole: Entity, offering: Offering) -> None:
    propagate(world, narrate=False)
    world.say(
        f"The mole took the smaller piece with both paws. At once its fear faded, and it led Bobby to a narrow, safe path "
        f"that curled down the cliff where the stones were firm."
    )
    world.say(
        f"Together they ate in the wind, the sea below shining like a shield, and the lookout felt less lonely than before."
    )
    world.say(
        f"By the time the sun touched the water, Bobby and the mole had shared the last crumbs, and the cliff lookout was warm with a new friendship."
    )


def tell(setting: Setting, offering: Offering, creature: Creature,
         bobby_name: str = "Bobby", parent_type: str = "mother") -> World:
    world = World()
    bobby = world.add(Entity(id=bobby_name, kind="character", type="boy", role="hero"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    mole = world.add(Entity(id="mole", kind="creature", type="mole", label=creature.label))
    lookout = world.add(Entity(id="lookout", kind="place", type="place", label="the cliff lookout"))
    world.facts.update(setting=setting, offering=offering, creature=creature, parent=parent, bobby=bobby, mole=mole, lookout=lookout)

    bobby.meters["warmth"] = 0.0
    bobby.memes["sharing"] = 0.0
    set_scene(world, setting)
    world.para()
    meet_mole(world, bobby, mole, offering)
    world.para()
    remember_and_choose(world, bobby, mole, offering)
    resolve(world, setting, mole, offering)

    world.facts.update(
        outcome="shared",
        shared=bobby.memes["sharing"] >= THRESHOLD,
        trusted=mole.meters["trust"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "cliff_lookout": Setting("cliff_lookout", "the cliff lookout", "the sea below", "mythic"),
}

OFFERINGS = {
    "honeycakes": Offering("honeycakes", "honey cakes", "a paper pouch of honey cakes", "let's share the honey cakes", {"share", "food"}),
    "apple": Offering("apple", "a red apple", "a red apple wrapped in cloth", "let's share the apple", {"share", "food"}),
    "bread": Offering("bread", "round bread", "a round loaf of bread", "let's share the bread", {"share", "food"}),
}

CREATURES = {
    "mole": Creature("mole", "little mole", "mole", True, {"mole", "burrow", "earth"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    offering: str
    creature: str
    parent: str = "mother"
    bobby: str = "Bobby"
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
    return [(s, o, c) for s in SETTINGS for o in OFFERINGS for c in CREATURES if reasonableness_gate(OFFERINGS[o], SETTINGS[s], CREATURES[c])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic cliff-lookout sharing storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--bobby")
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
              and (args.offering is None or c[1] == args.offering)
              and (args.creature is None or c[2] == args.creature)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, offering, creature = rng.choice(sorted(combos))
    return StoryParams(setting, offering, creature, parent=args.parent or rng.choice(["mother", "father"]), bobby=args.bobby or "Bobby")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a mythic story set at a cliff lookout that includes the words "buy", "bobby", and "mole".',
        f"Tell a gentle sharing story about Bobby at {f['setting'].place} who buys {f['offering'].label} and meets a mole in the wind.",
        "Use a flashback to show why Bobby chooses to share, and end with a warm image of the lookout.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bobby = f["bobby"]
    mole = f["mole"]
    offering = f["offering"]
    return [
        QAItem(
            question="Where does the story take place?",
            answer="It takes place at the cliff lookout, where the sea is below and the wind moves around the stones."
        ),
        QAItem(
            question="What did Bobby buy?",
            answer=f"Bobby bought {offering.phrase} to carry to the lookout. That made the sharing moment possible when the mole appeared."
        ),
        QAItem(
            question="Why did Bobby share with the mole?",
            answer="Bobby remembered a kinder time from the past, when someone had shared food with Bobby in a hard moment. Because of that flashback, Bobby chose to share instead of keeping the food alone."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with Bobby and the mole eating together and finding a safe path down from the cliff lookout. The final image shows that sharing turned a lonely place into a friendly one."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mole?",
            answer="A mole is a small, shy animal that lives in tunnels under the ground and uses its nose and paws to find its way."
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else have some of what you have. It is a kind way to help both people feel cared for."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory scene from earlier time that comes into the story for a moment. It helps explain why a character makes a choice now."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, o in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        if "share" in o.tags:
            lines.append(asp.fact("shareable", oid))
    for cid in CREATURES:
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("mole", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, O, C) :- setting(S), offering(O), creature(C), shareable(O), S = cliff_lookout, C = mole.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python validity differ.")
    # smoke test normal generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OFFERINGS[params.offering], CREATURES[params.creature], params.bobby, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in [StoryParams(*c) for c in valid_combos()[:3]]]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
