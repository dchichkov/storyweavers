#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flute_reward_pride_flashback_conflict_heartwarming.py
=====================================================================================

A standalone story world about a child, a flute, a small conflict, a proud mistake,
and a heartwarming reward. The domain is intentionally tiny and classical:

- a child learns flute practice takes patience,
- a flashback reminds them why the flute matters,
- conflict arises when pride tempts them to skip practice or show off,
- a kind adult guides them back,
- the final reward is earned by careful, warm effort.

The story keeps state in meters and memes, and the prose is driven by that state.
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
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



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
    mood: str

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
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    delicate: bool = True
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
class Reward:
    id: str
    label: str
    phrase: str
    gives: str
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    if not kid:
        return out
    if kid.memes["pride"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["conflict"] += 1
    out.append("__conflict__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    adult = world.entities.get("adult")
    if not kid or not adult:
        return out
    if kid.memes["hurt"] < THRESHOLD or kid.memes["listening"] < THRESHOLD:
        return out
    sig = ("soften",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["calm"] += 1
    adult.memes["warmth"] += 1
    out.append("__soften__")
    return out


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("soften", "social", _r_soften),
]


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


def _practice(world: World, kid: Entity, inst: Instrument, narrate: bool = True) -> None:
    kid.meters["practice"] += 1
    kid.memes["patience"] += 1
    kid.memes["pride"] = max(0.0, kid.memes["pride"] - 0.5)
    if narrate:
        world.say(f"{kid.id} lifted {kid.pronoun('possessive')} flute and practiced a few careful notes.")
        world.say(f"The flute answered with a soft {inst.sound} in the warm room.")


def _flashback(world: World, kid: Entity, inst: Instrument) -> None:
    kid.memes["memory"] += 1
    world.say(
        f"For a moment, {kid.id} remembered the day {kid.pronoun('possessive')} "
        f"grandma had first placed {inst.phrase} in {kid.pronoun('possessive')} hands."
    )
    world.say(
        f"Back then, the first clear tune had made everyone smile, and that happy feeling had become a little treasure inside {kid.id}."
    )


def _tempt(world: World, kid: Entity) -> None:
    kid.memes["pride"] += 1
    world.say(
        f"That memory made {kid.id} stand a little taller, and {kid.pronoun().capitalize()} thought {kid.pronoun('subject')} could play perfectly without more practice."
    )


def _warn(world: World, adult: Entity, kid: Entity) -> None:
    world.say(
        f"{adult.id} noticed the proud look and smiled gently. \"A sweet song grows best when we keep trying,\" {adult.pronoun()} said."
    )


def _defy(world: World, kid: Entity, inst: Instrument) -> None:
    world.say(
        f"{kid.id} tried to show off with the flute, but the notes wobbled and slipped into a squeaky little jumble."
    )
    kid.meters["oops"] += 1


def _hurt(world: World, kid: Entity, adult: Entity, inst: Instrument) -> None:
    kid.memes["hurt"] += 1
    kid.memes["conflict"] += 1
    kid.memes["listening"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{kid.id}'s cheeks grew hot with pride, and {kid.id} looked down when the song did not sound the way {kid.pronoun('subject')} wanted."
    )
    world.say(
        f"{adult.id} knelt beside {kid.id} and said, \"Everyone starts small. The kind thing is to keep going.\""
    )


def _reward(world: World, kid: Entity, inst: Instrument, reward: Reward) -> None:
    kid.meters["practice"] += 1
    kid.memes["joy"] += 1
    kid.memes["pride"] = max(0.0, kid.memes["pride"] - 0.5)
    world.say(
        f"After one more careful try, the flute sang a brighter tune, and {kid.id} felt the sound settle into place."
    )
    world.say(
        f"{reward.label_word.capitalize()} smiled and gave {kid.id} {reward.phrase} because {kid.id} had stayed patient and kind."
    )
    world.say(
        f"{kid.id} held {reward.phrase} close, and the little room felt full of warm, happy pride that was gentle instead of boastful."
    )


def tell(setting: Setting, inst: Instrument, reward: Reward,
         child_name: str = "Maya", child_gender: str = "girl",
         adult_name: str = "Grandma", adult_gender: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    child.memes["pride"] = 1.0
    child.memes["love_music"] = 1.0
    adult.memes["warmth"] = 1.0

    world.say(
        f"On a cozy afternoon in the {setting.place}, {child.id} sat with {inst.phrase} while {adult.id} listened nearby."
    )
    world.say(
        f"{child.id} loved the flute because it had once made a room feel magical, and the old memory still glowed in {child.pronoun('possessive')} heart."
    )

    world.para()
    _flashback(world, child, inst)
    _tempt(world, child)
    _warn(world, adult, child)
    _defy(world, child, inst)

    world.para()
    propagate(world, narrate=False)
    _hurt(world, child, adult, inst)

    world.para()
    _practice(world, child, inst)
    _reward(world, child, inst, reward)

    world.facts.update(
        child=child, adult=adult, setting=setting, instrument=inst, reward=reward,
        conflict=child.memes["conflict"] >= THRESHOLD,
        flashed=True, proud=child.memes["pride"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "music_room": Setting("music_room", "music room", "cozy"),
    "living_room": Setting("living_room", "living room", "soft"),
    "porch_evening": Setting("porch_evening", "porch at dusk", "golden"),
}

INSTRUMENTS = {
    "flute": Instrument("flute", "flute", "the flute", "toot-toot", True, {"flute"}),
}

REWARDS = {
    "star": Reward("star", "gold star", "a gold star sticker", "earned", {"reward"}),
    "applause": Reward("applause", "round of applause", "a round of applause", "shared", {"reward"}),
    "cookie": Reward("cookie", "butter cookie", "a butter cookie", "enjoyed", {"reward"}),
}

CHILD_NAMES = ["Maya", "Noah", "Lina", "Eli", "Zara", "Theo"]
ADULT_NAMES = [("Grandma", "woman"), ("Dad", "man"), ("Aunt May", "woman"), ("Mom", "woman")]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, "flute", r) for s in SETTINGS for r in REWARDS]


@dataclass
@dataclass
class StoryParams:
    setting: str
    instrument: str
    reward: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming flute story world with flashback and conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in INSTRUMENTS:
        lines.append(asp.fact("instrument", iid))
    for rid in REWARDS:
        lines.append(asp.fact("reward", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, R) :- setting(S), instrument(I), reward(R).
sensible(I) :- instrument(I).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(v[0] for v in asp.atoms(model, "sensible"))


def explain_response(rid: str) -> str:
    return f"(Refusing choice '{rid}': this tiny world only has a sensible flute story.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.instrument and args.instrument != "flute":
        raise StoryError(explain_response(args.instrument))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.reward is None or c[2] == args.reward)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, inst, reward = rng.choice(combos)
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    adult_name, adult_gender = (args.adult, args.adult_gender) if args.adult and args.adult_gender else rng.choice(ADULT_NAMES)
    return StoryParams(setting, inst, reward, child_name, child_gender, adult_name, adult_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "flute", "reward", and "pride".',
        f"Tell a story where {f['child'].id} remembers an earlier moment with the flute, gets tangled up in pride, then learns gently and earns a reward.",
        f"Write a warm story with flashback and conflict in which a child practicing the flute makes a mistake, listens, tries again, and ends with a happy reward.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    reward: Reward = f["reward"]
    return [
        (f"Why did {child.id} feel proud at first?",
         f"{child.id} remembered an earlier happy moment with the flute, and that memory made {child.id} stand a little taller. Pride grew because the flute already felt special to {child.id}."),
        (f"What conflict happened in the middle of the story?",
         f"{child.id} wanted to play perfectly right away, but the notes wobbled and came out wrong. That made {child.id} feel upset, and {adult.id} had to answer with patience."),
        (f"How did the story end?",
         f"{child.id} practiced again, listened carefully, and earned {reward.phrase}. The ending is heartwarming because the reward came after kindness and effort."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a flute?",
         "A flute is a music instrument that makes a high, breathy sound when you blow across it and press its holes or keys."),
        ("What does a reward mean?",
         "A reward is something nice you get after doing well or trying hard. It can be a sticker, a treat, applause, or a kind word."),
        ("What is pride?",
         "Pride can mean feeling pleased with yourself. It is best when it stays gentle and does not stop you from learning."),
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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("music_room", "flute", "star", "Maya", "girl", "Grandma", "woman"),
    StoryParams("living_room", "flute", "applause", "Noah", "boy", "Dad", "man"),
    StoryParams("porch_evening", "flute", "cookie", "Lina", "girl", "Aunt May", "woman"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        INSTRUMENTS[params.instrument],
        REWARDS[params.reward],
        params.child_name,
        params.child_gender,
        params.adult_name,
        params.adult_gender,
    )
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


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    p = set(valid_combos())
    rc = 0
    if a == p:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if a - p:
            print("  only in clingo:", sorted(a - p))
        if p - a:
            print("  only in python:", sorted(p - a))
    sens = set(asp_sensible())
    if sens == {"flute"}:
        print("OK: sensible instrument set matches.")
    else:
        rc = 1
        print("MISMATCH in sensible set:", sorted(sens))
    try:
        generate(CURATED[0])
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible instruments: {', '.join(asp_sensible())}\n")
        for s, i, r in asp_valid_combos():
            print(f"  {s:12} {i:8} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
