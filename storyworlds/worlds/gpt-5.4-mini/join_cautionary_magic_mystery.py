#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/join_cautionary_magic_mystery.py
=================================================================

A standalone storyworld for a tiny cautionary magic mystery:
a curious child finds a strange note, tries to "join" a hidden magic circle,
and a cautious helper warns them before the magic becomes too risky.

The domain is deliberately small and state-driven:
- physical meters: glow, mist, rumble, tidiness, risk
- emotional memes: curiosity, caution, relief, wonder, fear
- the story turns on whether the child follows the warning and uses a safe
  way to join the mystery, or ignores it and causes a spooky mishap.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/join_cautionary_magic_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/join_cautionary_magic_mystery.py --all
    python storyworlds/worlds/gpt-5.4-mini/join_cautionary_magic_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/join_cautionary_magic_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/join_cautionary_magic_mystery.py --verify
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
CAUTION_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
    place: str
    dark_corner: str
    clue: str
    mystery_style: str
    join_phrase: str

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
class Charm:
    id: str
    label: str
    glow: str
    makes_spell: bool = False
    safe_join: bool = False
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
class Warning:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    calm: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["glow"] < THRESHOLD and ent.meters["mist"] < THRESHOLD and ent.meters["rumble"] < THRESHOLD:
            continue
        sig = ("risk", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["risk"] += 1
        for e in list(world.entities.values()):
            if e.role in {"child", "watcher"}:
                e.memes["fear"] += 1
        out.append("__risk__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("solved"):
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in list(world.entities.values()):
                if e.role in {"child", "watcher"}:
                    e.memes["relief"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("risk", "physical", _r_risk), Rule("calm", "social", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def cautious_enough(helper: Entity) -> bool:
    return helper.memes["caution"] >= CAUTION_MIN or "careful" in helper.traits


def predict_join(world: World, charm: Charm) -> dict:
    sim = world.copy()
    _do_magic_join(sim, charm, narrate=False)
    return {
        "risky": sim.get("room").meters["risk"] >= THRESHOLD,
        "glow": sim.get("room").meters["risk"],
    }


def _do_magic_join(world: World, charm: Charm, narrate: bool = True) -> None:
    if charm.makes_spell:
        world.get("sigil").meters["glow"] += 1
        world.get("sigil").meters["mist"] += 1
    else:
        world.get("token").meters["glow"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    helper.memes["caution"] += 1
    world.say(
        f"At {setting.place}, {child.id} found a note tucked beside a cold stone. "
        f"It pointed to {setting.dark_corner}, where a tiny mystery seemed to wait."
    )
    world.say(
        f'{child.id} and {helper.id} followed the clue with slow steps. '
        f'The air felt quiet, as if the room itself was trying to keep a secret.'
    )


def find_charm(world: World, child: Entity, charm: Charm, setting: Setting) -> None:
    world.say(
        f"In the dark corner they found {charm.label}, and it gave off a {charm.glow}. "
        f"The glow made the shadows look like they were listening."
    )


def warn(world: World, helper: Entity, child: Entity, charm: Charm, setting: Setting) -> None:
    pred = predict_join(world, charm)
    helper.memes["caution"] += 1
    world.facts["predicted_risk"] = pred["glow"]
    world.say(
        f'{helper.id} bit {helper.pronoun("possessive")} lip. "{child.id}, don\'t touch '
        f"{charm.label} yet. Magic can be tricky, and a mystery is safer when we look first.\""
    )


def invite_join(world: World, child: Entity, helper: Entity, charm: Charm, setting: Setting) -> None:
    child.memes["wonder"] += 1
    world.say(
        f'{child.id} wanted to join the magic at once, because the glow looked kind and warm. '
        f'For a breath, the whole room felt like a fairy tale.'
    )


def choose_safe_join(world: World, child: Entity, helper: Entity, charm: Charm, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'But {child.id} looked at {helper.id} and asked, "What if we join the mystery '
        f'without opening the spell?"'
    )
    world.say(
        f"Together they tied a bright ribbon around {charm.label} and marked the spot, so "
        f"no one would step too close. Then they listened for the hidden sound instead."
    )


def trigger_spell(world: World, child: Entity, charm: Charm, setting: Setting) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'{child.id} did not wait. {child.id} said, "I can handle it," and touched {charm.label}. '
        f"At once the glow jumped high, and the mist began to spin."
    )


def alarm(world: World, helper: Entity, child: Entity, setting: Setting) -> None:
    world.say(
        f'"{child.id}, stop!" {helper.id} shouted. "That magic is not ready for you!"'
    )


def resolve_good(world: World, child: Entity, helper: Entity, charm: Charm, setting: Setting) -> None:
    world.facts["solved"] = True
    world.get("room").meters["risk"] = 0.0
    world.say(
        f"{helper.label_word.capitalize()} smiled and showed {child.id} how to watch from a safe step away. "
        f"The glow became gentle, and the mystery stayed where it belonged."
    )
    world.say(
        f"At the end, {child.id} and {helper.id} could still join the story -- but only by using careful eyes, "
        f"quiet voices, and a safe circle around the charm."
    )


def resolve_bad(world: World, child: Entity, helper: Entity, charm: Charm, setting: Setting) -> None:
    world.get("room").meters["risk"] += 1
    world.say(
        f"The spell burst into a swirl of blue mist that made the windows shiver. "
        f"Nothing broke, but the room felt spooky and wrong."
    )
    world.say(
        f"{helper.label_word.capitalize()} pulled {child.id} back and covered the charm with a cloth. "
        f"After that, they knew the mystery had to wait."
    )
    world.say(
        f"The last thing {child.id} saw was {charm.label} glimmering under the cloth, quiet again."
    )


def tell(setting: Setting, charm: Charm, warning: Warning,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Nora", helper_gender: str = "girl",
         helper_trait: str = "careful", outcome: str = "safe") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="watcher", traits=[helper_trait]))
    room = world.add(Entity(id="room", type="room", label="the room"))
    sigil = world.add(Entity(id="sigil", type="sigil", label="the sigil"))
    token = world.add(Entity(id="token", type="token", label="the token"))

    child.memes["curiosity"] = 5.0
    helper.memes["caution"] = 5.0

    opening(world, child, helper, setting)
    world.para()
    find_charm(world, child, charm, setting)
    warn(world, helper, child, charm, setting)
    invite_join(world, child, helper, charm, setting)

    world.para()
    if outcome == "safe":
        choose_safe_join(world, child, helper, charm, setting)
        resolve_good(world, child, helper, charm, setting)
        solved = True
    else:
        trigger_spell(world, child, charm, setting)
        alarm(world, helper, child, setting)
        resolve_bad(world, child, helper, charm, setting)
        solved = False

    world.facts.update(
        child=child,
        helper=helper,
        room=room,
        sigil=sigil,
        token=token,
        setting=setting,
        charm=charm,
        warning=warning,
        solved=solved,
        outcome=outcome,
    )
    return world


SETTINGS = {
    "attic": Setting("the attic", "the shadow under the rafters", "a silver note", "mystery", "join"),
    "library": Setting("the old library", "the corner behind the shelves", "a folded card", "mystery", "join"),
    "garden": Setting("the moonlit garden", "the hedge gap", "a torn ribbon", "mystery", "join"),
}

CHARMS = {
    "sigil": Charm("sigil", "a tiny sigil stone", "a soft blue glow", makes_spell=True, safe_join=False, tags={"magic", "mystery"}),
    "token": Charm("token", "a moonlit token", "a pale silver glow", makes_spell=False, safe_join=True, tags={"magic", "mystery"}),
}

WARNINGS = {
    "careful": Warning("careful", 3, 4,
                       "look first; magic can twist if you rush",
                       "tried to fix it, but the magic was already too wild",
                       "waited calmly and watched from a safe place",
                       tags={"cautionary"}),
    "slow": Warning("slow", 2, 3,
                    "the best mysteries are joined gently",
                    "couldn't stop the spell in time",
                    "moved slowly and kept everyone safe",
                    tags={"cautionary"}),
}



@dataclass
class StoryParams:
    setting: str
    charm: str
    warning: str
    outcome: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_trait: str
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
    ("attic", "token", "careful", "safe"),
    ("library", "sigil", "careful", "bad"),
    ("garden", "token", "slow", "safe"),
]



def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CHARMS:
            for w in WARNINGS:
                for outcome in ("safe", "bad"):
                    if c == "sigil" and outcome == "bad":
                        combos.append((s, c, w, outcome))
                    if c == "token" and outcome == "safe":
                        combos.append((s, c, w, outcome))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny cautionary magic mystery world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--outcome", choices=["safe", "bad"])
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
              and (args.charm is None or c[1] == args.charm)
              and (args.warning is None or c[2] == args.warning)
              and (args.outcome is None or c[3] == args.outcome)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, charm, warning, outcome = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        charm=charm,
        warning=warning,
        outcome=outcome,
        child_name=rng.choice(["Mina", "Lena", "Pia", "Toby", "Nico"]),
        child_gender=rng.choice(["girl", "boy"]),
        helper_name=rng.choice(["Nora", "June", "Mara", "Eli", "Iris"]),
        helper_gender=rng.choice(["girl", "boy"]),
        helper_trait="careful",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary magic mystery story that includes the word "join" and takes place in {f["setting"].place}.',
        f"Tell a child-sized mystery where {f['child'].id} wants to join the strange magic, but {f['helper'].id} warns them first.",
        f"Write a gentle spooky story with a safe ending where a curious child and a careful helper investigate {f['charm'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, charm, setting = f["child"], f["helper"], f["charm"], f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who found a mystery in {setting.place}."),
        ("What did the child want to do?",
         f"{child.id} wanted to join the magic around {charm.label}. The glow made the idea feel exciting."),
    ]
    if f["solved"]:
        qa.append((
            "How did they stay safe?",
            f"They did not open the spell. Instead, they marked a safe circle and watched carefully from a distance, so the mystery stayed calm."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely, with the glow becoming gentle and the child learning that caution can keep magic fun."
        ))
    else:
        qa.append((
            "What went wrong?",
            f"{child.id} touched {charm.label} too soon, and the magic burst into blue mist. {helper.id} had to pull them back and cover it."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the mystery shut down for safety, after the room felt spooky and wrong."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["charm"].tags) | set(f["warning"].tags)
    if f["solved"]:
        tags.add("cautionary")
    items = []
    if "magic" in tags:
        items.append(("What is magic in a story?", "Magic is something strange and impossible that can make surprising things happen. In stories, it can be wonderful, but it can also be risky if nobody is careful."))
    if "mystery" in tags:
        items.append(("What is a mystery?", "A mystery is something that is not explained yet. People look for clues to learn what is really happening."))
    if "cautionary" in tags:
        items.append(("What does cautionary mean?", "Cautionary means the story teaches you to be careful. It shows what can happen if you rush and why a warning matters."))
    return items


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
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CHARMS[params.charm],
        WARNINGS[params.warning],
        outcome=params.outcome,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_trait=params.helper_trait,
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


ASP_RULES = r"""
valid(S,C,W,O) :- setting(S), charm(C), warning(W), outcome(O).
safe(C) :- charm(C), safe_join(C).
bad(C) :- charm(C), not safe_join(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if c.safe_join:
            lines.append(asp.fact("safe_join", cid))
    for wid in WARNINGS:
        lines.append(asp.fact("warning", wid))
    for o in ("safe", "bad"):
        lines.append(asp.fact("outcome", o))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, charm=None, warning=None, outcome=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def explain_rejection() -> str:
    return "(No story: the chosen magic clue does not make a good cautionary mystery.)"


def valid_story(params: StoryParams) -> bool:
    if params.charm == "sigil" and params.outcome != "bad":
        return False
    if params.charm == "token" and params.outcome != "safe":
        return False
    return True


def resolve_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def _smoke_default() -> StoryParams:
    return StoryParams("attic", "token", "careful", "safe", "Mina", "girl", "Nora", "girl", "careful")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show safe/1.\n#show bad/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, c, w, o, "Mina", "girl", "Nora", "girl", "careful")) for s, c, w, o in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_choice(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
