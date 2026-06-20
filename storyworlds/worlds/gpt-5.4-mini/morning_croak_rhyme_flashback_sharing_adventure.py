#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/morning_croak_rhyme_flashback_sharing_adventure.py
==================================================================================

A tiny storyworld about a morning adventure with a croaking frog, a remembered
flashback, a rhyming clue, and a sharing turn. A child or small group heads out
on an early adventure, hears a frog croak near a pond or brook, remembers a past
clue, follows a simple rhyme to find a lost item, then shares the discovery so
everyone gets part of the reward.

This world is intentionally small and classical:
- typed entities with meters and memes
- simulated state drives prose
- one stateful turn, one resolution turn
- Python reasonableness gate with an inline ASP twin
- story-grounded and world-knowledge QA from world state, not rendered text
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
SENSE_MIN = 2


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
    name: str
    morning_detail: str
    path_detail: str
    place_hint: str

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
class CharacterSpec:
    id: str
    type: str
    role: str

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
class ObjectSpec:
    id: str
    label: str
    kind: str
    can_hide: bool = False
    can_float: bool = False

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
class Clue:
    id: str
    rhyme: str
    flash: str
    place_word: str
    reward: str

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
    tag: str
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


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["soaked"] < THRESHOLD:
            continue
        sig = ("wet", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["unease"] += 1
        out.append("__wet__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    crown = world.entities.get("reward")
    if not crown:
        return out
    if crown.meters["found"] < THRESHOLD or crown.meters["shared"] >= THRESHOLD:
        return out
    sig = ("share", crown.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    finder = world.get("hero")
    friend = world.get("friend")
    finder.memes["joy"] += 1
    friend.memes["joy"] += 1
    crown.meters["shared"] = 1.0
    out.append("__share__")
    return out


CAUSAL_RULES = [Rule("wet", "physical", _r_wet), Rule("share", "social", _r_share)]


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


def predict_path(world: World, choice: str) -> dict:
    sim = world.copy()
    if choice == "pond":
        sim.get("frog").meters["croak"] += 1
        sim.get("lantern").meters["found"] += 1
    elif choice == "bridge":
        sim.get("bridge").meters["reached"] += 1
    return {
        "croak": sim.get("frog").meters["croak"] >= THRESHOLD,
        "found": sim.get("reward").meters["found"] >= THRESHOLD,
    }


def safe_choice(text: str) -> str:
    return text.replace("{", "").replace("}", "")


def tell(setting: Setting, clue: Clue, reward: str, hero: str, friend: str, parent: str) -> World:
    world = World()
    h = world.add(Entity(hero, kind="character", type="boy" if hero in BOY_NAMES else "girl", role="hero"))
    f = world.add(Entity(friend, kind="character", type="boy" if friend in BOY_NAMES else "girl", role="friend"))
    p = world.add(Entity(parent, kind="character", type="mother" if parent in {"Mia", "Lina", "Nora"} else "father", role="parent"))
    frog = world.add(Entity("frog", kind="character", type="thing", label="a frog", role="guide"))
    reward_ent = world.add(Entity("reward", kind="thing", type="thing", label=reward, role="reward"))
    bridge = world.add(Entity("bridge", kind="thing", type="thing", label="a little bridge"))
    lantern = world.add(Entity("lantern", kind="thing", type="thing", label="a paper lantern"))

    world.facts["setting"] = setting
    world.facts["clue"] = clue
    world.facts["reward"] = reward
    world.facts["hero_name"] = hero
    world.facts["friend_name"] = friend
    world.facts["parent_name"] = parent

    h.memes["curiosity"] += 1
    f.memes["curiosity"] += 1

    world.say(f"On a bright morning, {hero} and {friend} set out on a small adventure near {setting.name}.")
    world.say(f"{setting.morning_detail} {setting.path_detail}")
    world.say(f"They were hunting for {reward}, because yesterday their {parent} had hidden a surprise for them.")
    world.para()
    world.say(f"Near the water, a frog gave a loud croak, and the sound seemed to point the way.")
    world.say(f'{friend} blinked. "{clue.rhyme}" {hero} said, remembering a rhyme from an old game.')

    flashback = f"That rhyme brought back a flashback: the last time they played here, {parent} had pointed out {clue.flash}."
    world.say(flashback)

    if setting.id == "pond":
        frog.meters["croak"] += 1
        reward_ent.meters["found"] += 1
        world.para()
        world.say(f"They followed the croak to {clue.place_word}, where {reward} was tucked away.")
        world.say(f"{hero} held it up, and {friend} smiled at once.")
        world.say(f"But the best part was sharing: {hero} gave {friend} one half of the {clue.reward}, and kept the other half.")
        propagate(world, narrate=False)
        world.say(f"Then {parent} came to the edge of the path and laughed, happy to see them take turns and share.")
        world.say("The morning adventure ended with wet shoes, bright grins, and both children carrying a piece of the prize.")
    else:
        world.para()
        world.say(f"They crossed the little bridge together, listening for the croak again.")
        world.say(f"At the far side, they found {reward} beside {clue.place_word}.")
        reward_ent.meters["found"] += 1
        world.say(f"{hero} and {friend} shared it right away, so neither one had to wait.")
        world.say(f"When {parent} arrived, the pair were already laughing and planning their next rhyme.")
        world.say("The adventure ended with two happy friends and one shared treasure.")

    world.facts.update(
        hero=h, friend=f, parent=p, frog=frog, reward_ent=reward_ent,
        outcome="shared", flashback=True, croak=frog.meters["croak"] >= THRESHOLD
    )
    return world


SETTING_REGISTRY = {
    "pond": Setting("pond", "the pond", "The water was still and silver.", "A narrow path curved around the reeds.", "by the reeds"),
    "brook": Setting("brook", "the brook", "The morning mist sat low on the stones.", "A stepping-stone path crossed the water.", "under the willow"),
}

CLUE_REGISTRY = {
    "reeds": Clue("reeds", "If you hear a croak, then look by the reeds.", "the reeds shaking in the breeze", "by the reeds", "pearl shell"),
    "willow": Clue("willow", "If you hear a croak, then look under the willow.", "the willow branches brushing the water", "under the willow", "silver bead"),
}

BOY_NAMES = ["Ben", "Leo", "Theo", "Noah", "Milo", "Sam"]
GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Zoe", "June"]
PARENT_NAMES = ["Mia", "Lina", "Nora", "Dad", "Mom", "Papa", "Mama"]

REWARD_REGISTRY = ["pearl shell", "silver bead"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    reward: str
    hero: str
    friend: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTING_REGISTRY.items():
        for cid, clue in CLUE_REGISTRY.items():
            if clue.place_word in setting.place_hint:
                for reward in REWARD_REGISTRY:
                    combos.append((sid, cid, reward))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the words "morning" and "croak" and a rhyming clue.',
        f"Tell a small adventure where {f['hero_name']} and {f['friend_name']} hear a croak, remember a rhyme, and share the prize.",
        f"Write a gentle story with a flashback in which a child remembers an old rhyme and shares a found treasure with a friend.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero_name"]
    friend = f["friend_name"]
    parent = f["parent_name"]
    reward = f["reward"]
    clue = f["clue"]
    return [
        ("What kind of day was it?",
         "It was a morning adventure, so the children started out early and the day felt fresh and bright."),
        ("What sound did they hear near the water?",
         "They heard a croak from a frog near the water. That sound helped guide them toward the hidden prize."),
        ("What did the children remember?",
         "They remembered a rhyme from an earlier game, and that flashback helped them think of the right place to look."),
        ("How did they end the adventure?",
         f"They shared {reward}, so both children got part of the prize. {parent} was happy to see them take turns and share."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a frog do?", "A frog can croak, which is a loud sound it makes with its voice."),
        ("What is a rhyme?", "A rhyme is a line or song where words sound alike at the end."),
        ("What is a flashback?", "A flashback is a memory of something that happened before."),
        ("What does sharing mean?", "Sharing means giving some of what you have to another person so you both can use it or enjoy it."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pond", "reeds", "pearl shell", "Ben", "Mia", "Mom"),
    StoryParams("brook", "willow", "silver bead", "Lina", "Theo", "Dad"),
]


def explain_rejection(setting: Setting, clue: Clue) -> str:
    return "(No story: the setting and clue do not fit the morning croak trail well enough.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for cid in CLUE_REGISTRY:
        lines.append(asp.fact("clue", cid))
    for rid in REWARD_REGISTRY:
        lines.append(asp.fact("reward", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, R) :- setting(S), clue(C), reward(R).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: ASP gate matches valid_combos() ({len(p)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print(" only in python:", sorted(p - a))
        print(" only in asp:", sorted(a - p))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, reward=None, hero=None, friend=None, parent=None), random.Random(1)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Morning croak rhyme flashback sharing adventure.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--clue", choices=CLUE_REGISTRY)
    ap.add_argument("--reward", choices=REWARD_REGISTRY)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--parent")
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
    combos = valid_combos()
    if args.setting or args.clue or args.reward:
        combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
                  and (args.clue is None or c[1] == args.clue)
                  and (args.reward is None or c[2] == args.reward)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, cid, rid = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(BOY_NAMES + GIRL_NAMES)
    friend = args.friend or rng.choice([n for n in BOY_NAMES + GIRL_NAMES if n != hero])
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(sid, cid, rid, hero, friend, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING_REGISTRY[params.setting], CLUE_REGISTRY[params.clue], params.reward,
                 params.hero, params.friend, params.parent)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
