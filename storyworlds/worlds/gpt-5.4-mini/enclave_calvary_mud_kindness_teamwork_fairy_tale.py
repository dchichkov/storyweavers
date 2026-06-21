#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/enclave_calvary_mud_kindness_teamwork_fairy_tale.py
===================================================================================

A small fairy-tale storyworld about a secluded enclave, a muddy path, and a
kind teamwork rescue.

Seed words:
- enclave
- calvary
- mud

Features:
- Kindness
- Teamwork

Style:
- Fairy Tale
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "princess"}
        male = {"boy", "father", "king", "man", "prince", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



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
    enclave: bool
    features: set[str] = field(default_factory=set)

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
class CharacterRole:
    id: str
    type: str
    title: str
    intro: str
    virtue: str

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
class Trouble:
    id: str
    label: str
    effect: str
    risk: str
    can_mess: bool = True
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
class Help:
    id: str
    label: str
    method: str
    strength: int
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
        clone = World(self.setting)
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


def _r_mud(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["stuck"] < THRESHOLD:
            continue
        sig = ("mud", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__mud__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kind", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hope"] += 1
        out.append("__kind__")
    return out


CAUSAL_RULES = [Rule("mud", _r_mud), Rule("kindness", _r_kindness)]


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


def muddy_enough(trouble: Trouble, setting: Setting) -> bool:
    return trouble.can_mess and "mud" in setting.features


def can_rescue(help_item: Help, trouble: Trouble) -> bool:
    return help_item.strength >= 1 and trouble.can_mess


def predict(world: World, hero_id: str) -> dict:
    sim = world.copy()
    sim.get(hero_id).meters["stuck"] += 1
    propagate(sim, narrate=False)
    return {
        "stuck": sim.get(hero_id).meters["stuck"] >= THRESHOLD,
        "worry": sim.get(hero_id).memes["worry"],
    }


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"Long ago, in a quiet {setting.place}, there was an {setting.id} where "
        f"{hero.id} and {friend.id} lived in peace behind a silver gate."
    )
    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type}, and {friend.id} was a "
        f"{friend.traits[0]} {friend.type} who loved to help."
    )


def trouble_arrives(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.metes = hero.meters  # harmless alias? avoid. but should not leak.
    hero.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"One gray morning, a deep patch of {trouble.label} blocked the path by "
        f"the gate, and {hero.id} could not cross without getting {trouble.effect}."
    )


def warning(world: World, friend: Entity, hero: Entity, trouble: Trouble) -> None:
    pred = predict(world, hero.id)
    friend.memes["kindness"] += 1
    world.facts["predicted"] = pred
    world.say(
        f'{friend.id} smiled gently and said, "{hero.id}, let us be kind to the '
        f'path and not rush. That {trouble.label} is deep, and it will leave '
        f'you {trouble.risk}."'
    )


def teamwork(world: World, hero: Entity, friend: Entity, help_item: Help) -> None:
    hero.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    world.say(
        f'Then {hero.id} nodded, and together they chose {help_item.label}. '
        f'With {help_item.method}, they worked side by side.'
    )


def resolve(world: World, hero: Entity, friend: Entity, help_item: Help) -> None:
    hero.meters["stuck"] = 0.0
    friend.memes["joy"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"Slowly, the mud gave way. In time, {hero.id} reached the lantern-lit "
        f"steps, and {friend.id} wiped the last brown splash from {hero.id}'s "
        f"boots."
    )
    world.say(
        f"By sunset, the whole enclave was bright again, and the two friends "
        f"stood together as proud as little heroes."
    )


def tell(setting: Setting, hero_role: CharacterRole, friend_role: CharacterRole,
         trouble: Trouble, help_item: Help) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_role.id, kind="character", type=hero_role.type, role="hero",
        traits=[hero_role.virtue, "brave"]))
    friend = world.add(Entity(
        id=friend_role.id, kind="character", type=friend_role.type, role="friend",
        traits=[friend_role.virtue, "gentle"]))
    gate = world.add(Entity(id="gate", label="the silver gate"))
    world.facts["gate"] = gate.id

    introduce(world, hero, friend, setting)
    world.para()
    trouble_arrives(world, hero, trouble)
    warning(world, friend, hero, trouble)
    world.para()
    teamwork(world, hero, friend, help_item)
    resolve(world, hero, friend, help_item)

    world.facts.update(
        hero=hero, friend=friend, trouble=trouble, help_item=help_item,
        setting=setting, outcome="rescued",
    )
    return world


SETTINGS = {
    "enclave": Setting("enclave", "enclave", True, {"mud"}),
    "forest_enclave": Setting("forest_enclave", "forest enclave", True, {"mud"}),
    "hill_village": Setting("hill_village", "hill village", True, {"mud"}),
}

ROLES = {
    "princess": CharacterRole("princess", "girl", "princess", "kind", "gentle"),
    "knight": CharacterRole("knight", "boy", "knight", "kind", "helpful"),
    "page": CharacterRole("page", "girl", "page", "careful", "kind"),
    "squire": CharacterRole("squire", "boy", "squire", "steady", "kind"),
}

TROUBLES = {
    "mud": Trouble("mud", "mud", "muddy", "stuck in mud", True, {"mud"}),
    "mudbank": Trouble("mudbank", "mudbank", "mud-splashed", "stuck in the muck", True, {"mud"}),
}

HELPS = {
    "plank": Help("plank", "a wooden plank", "laying down a wooden plank bridge", 2, {"teamwork"}),
    "rope": Help("rope", "a rope and a helping hand", "tying a rope to steady the crossing", 2, {"teamwork"}),
    "boots": Help("boots", "clean boots and two hands", "taking careful turns and sharing the load", 1, {"kindness", "teamwork"}),
}



@dataclass
class StoryParams:
    setting: str
    trouble: str
    hero: str
    friend: str
    help_item: str
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
    StoryParams("enclave", "mud", "princess", "knight", "plank"),
    StoryParams("forest_enclave", "mudbank", "page", "squire", "rope"),
]



def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, trouble in TROUBLES.items():
            if not muddy_enough(trouble, setting):
                continue
            for hid, hero in ROLES.items():
                for fid, friend in ROLES.items():
                    if hero.type == friend.type and hero.id == friend.id:
                        continue
                    for help_id, help_item in HELPS.items():
                        if can_rescue(help_item, trouble):
                            combos.append((sid, tid, hid, fid, help_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    trouble = f["trouble"]
    return [
        f'Write a fairy tale for a young child that includes the words "enclave", "{trouble.label}", and "calvary".',
        f"Tell a kindness story where {friend.id} helps {hero.id} cross a muddy path in a small enclave.",
        f"Write a teamwork story with a muddy gate, a gentle friend, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    trouble = f["trouble"]
    help_item = f["help_item"]
    return [
        QAItem(
            question="Who was in the story?",
            answer=f"It was about {hero.id} and {friend.id}, two little friends in a quiet enclave. They stayed close to each other when the path got muddy."
        ),
        QAItem(
            question="What was blocking the path?",
            answer=f"A deep patch of {trouble.label} blocked the way by the gate. It made the crossing slippery and hard to do alone."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used {help_item.label} and worked together. That teamwork helped them cross safely without getting lost in the mud."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring to someone else. A kind person tries to make things easier for others."
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together. When a team shares the work, the job often gets done faster and safer."
        ),
        QAItem(
            question="What is mud?",
            answer="Mud is wet earth that can be slippery and messy. It sticks to boots and makes the ground hard to walk on."
        ),
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this tale needs mud in an enclave and a helping tool that can solve it.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about an enclave, mud, kindness, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--hero", choices=ROLES)
    ap.add_argument("--friend", choices=ROLES)
    ap.add_argument("--help-item", choices=HELPS)
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
              and (args.trouble is None or c[1] == args.trouble)
              and (args.hero is None or c[2] == args.hero)
              and (args.friend is None or c[3] == args.friend)
              and (args.help_item is None or c[4] == args.help_item)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, trouble, hero, friend, help_item = rng.choice(sorted(combos))
    return StoryParams(setting, trouble, hero, friend, help_item)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ROLES[params.hero], ROLES[params.friend],
                 TROUBLES[params.trouble], HELPS[params.help_item])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(S, T, H, F, G) :- setting(S), trouble(T), hero(H), friend(F), help(G),
                         muddy(S, T), rescues(T, G), distinct(H, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("muddy", "enclave", tid))
        lines.append(asp.fact("muddy", "forest_enclave", tid))
        lines.append(asp.fact("muddy", "hill_village", tid))
    for hid in ROLES:
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("friend", hid))
    for gid in HELPS:
        lines.append(asp.fact("help", gid))
        lines.append(asp.fact("rescues", "mud", gid))
        lines.append(asp.fact("rescues", "mudbank", gid))
    lines.append(asp.fact("distinct", "a", "b"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


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
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
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
            if sample.story not in seen:
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
