#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chitter_transformation_bad_ending_adventure.py
===============================================================================

A small standalone storyworld for an adventure tale about a curious child,
a strange chittering relic, an unwanted transformation, and a bad ending.

The world is built around a tiny expedition: someone explores a narrow place,
hears a chitter, touches a strange object, transforms into a small creature,
and then cannot get back before dusk. The story engine keeps the simulated
state moving so the prose reflects what actually changed.

This script follows the shared Storyweavers world contract:
- typed entities with meters and memes
- a reasonableness gate
- a Python/ASP twin
- three QA sets grounded in simulated state
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    transformed_into: str = ""

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
    dark_place: str
    has_exit: bool = True

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
class Relic:
    id: str
    label: str
    phrase: str
    chitter: str
    touch_line: str
    transforms_into: str
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
class Transformation:
    id: str
    label: str
    body: str
    feet: str
    voice: str
    scared_of: str
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
class Ending:
    id: str
    label: str
    power: int
    text: str
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


def _r_chitter(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    relic = world.entities.get("relic")
    if not hero or not relic:
        return out
    if hero.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("chitter",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["heard_chitter"] = True
    hero.memes["unease"] += 1
    out.append("__chitter__")
    return out


def _r_transform(world: World) -> list[str]:
    hero = world.entities.get("hero")
    relic = world.entities.get("relic")
    if not hero or not relic:
        return []
    if hero.meters["touch"] < THRESHOLD or world.facts.get("transformed"):
        return []
    sig = ("transform",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.type = relic.transforms_into
    hero.transformed_into = relic.transforms_into
    hero.meters["changed"] += 1
    hero.memes["panic"] += 2
    world.facts["transformed"] = True
    return ["__transform__"]


def _r_bad_end(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if not hero:
        return []
    if hero.memes["panic"] < THRESHOLD:
        return []
    sig = ("bad_end",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["bad_ending"] = True
    return ["__bad_end__"]


CAUSAL_RULES: list[Rule] = [
    Rule("chitter", "sound", _r_chitter),
    Rule("transform", "magic", _r_transform),
    Rule("bad_end", "ending", _r_bad_end),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def danger_check(relic: Relic, setting: Setting) -> bool:
    return bool(relic.chitter and setting.dark_place)


def acceptable_ending(ending: Ending) -> bool:
    return ending.power >= 2


def can_transform(relic: Relic, transformation: Transformation) -> bool:
    return relic.transforms_into == transformation.id


def look_ahead(world: World, relic: Relic) -> dict:
    sim = world.copy()
    sim.get("hero").meters["touch"] += 1
    propagate(sim, narrate=False)
    return {
        "transformed": sim.facts.get("transformed", False),
        "bad_ending": sim.facts.get("bad_ending", False),
    }


def setup(world: World, hero: Entity, guide: Entity, setting: Setting, relic: Relic) -> None:
    hero.memes["curiosity"] += 1
    guide.memes["worry"] += 1
    world.say(
        f"On the first morning of the trek, {hero.id} and {guide.id} followed a "
        f"crumbled path into {setting.place}. The air grew still near {setting.dark_place}, "
        f"and something in the shadows gave a tiny {relic.chitter}."
    )
    world.say(
        f'{hero.id} leaned closer. "Did you hear that?" {hero.pronoun()} whispered. '
        f'"It sounds like a secret."'
    )


def warn(world: World, guide: Entity, hero: Entity, relic: Relic, trans: Transformation) -> None:
    guide.memes["worry"] += 1
    pred = look_ahead(world, relic)
    world.facts["predicted_bad"] = pred["bad_ending"]
    world.say(
        f'{guide.id} grabbed {hero.pronoun("possessive")} sleeve. '
        f'"Don\'t touch it," {guide.pronoun()} said. "{relic.label.capitalize()} '
        f'is not safe, and it can turn you into {trans.label.lower()}."'
    )


def defy(world: World, hero: Entity, relic: Relic) -> None:
    hero.memes["boldness"] += 1
    world.say(
        f'"I want to see," {hero.id} said, and reached out anyway. '
        f'{relic.chitter.capitalize()}!'
    )


def touch(world: World, hero: Entity, relic: Relic, trans: Transformation) -> None:
    hero.meters["touch"] += 1
    world.say(
        f"{relic.phrase.capitalize()} pulsed warm under {hero.pronoun('possessive')} fingers. "
        f"{relic.touch_line.capitalize()} Then the light slipped over {hero.id} like a coat."
    )
    propagate(world, narrate=False)
    if hero.transformed_into:
        world.say(
            f"When it faded, {hero.id} was no longer {hero.pronoun('subject')}self. "
            f"{hero.pronoun().capitalize()} had become {trans.label}, with {trans.body} and {trans.feet}."
        )


def bad_finish(world: World, hero: Entity, guide: Entity, ending: Ending) -> None:
    if ending.id == "lost":
        world.say(
            f"{guide.id} called for help, but the path behind them had already vanished "
            f"into the fog. {hero.id} tried to answer, yet the new {hero.transformed_into} "
            f"voice came out as a weak {ending.text}."
        )
        world.say(
            "By dusk, the sky turned purple and the trail grew colder. They never found "
            "the way back before night, and the little adventure ended in silence."
        )
    else:
        world.say(
            f"{guide.id} ran, but the tiny door in the rock slammed shut with a sharp click. "
            f"{hero.id} pressed to the stone, while the {ending.text} left the cave dark."
        )
    world.facts["ending"] = ending.id


def tell(
    setting: Setting,
    relic: Relic,
    trans: Transformation,
    ending: Ending,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    guide_name: str = "Pip",
    guide_type: str = "boy",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type, role="guide"))
    world.add(Entity(id="relic", type="thing", label=relic.label))
    world.facts.update(relic=relic, trans=trans, ending_def=ending, hero=hero, guide=guide, setting=setting)
    setup(world, hero, guide, setting, relic)
    world.para()
    warn(world, guide, hero, relic, trans)
    defy(world, hero, relic)
    touch(world, hero, relic, trans)
    world.para()
    bad_finish(world, hero, guide, ending)
    return world


SETTINGS = {
    "cavern": Setting("cavern", "the old cliff cave", "the back tunnel"),
    "ruins": Setting("ruins", "the mossy ruins", "the broken hall"),
    "island": Setting("island", "the windy island path", "the black stone arch"),
}

RELICS = {
    "chime": Relic("chime", "a metal chime", "the little chime", "chitter-chitter", "It woke like a bug in the dark.", "mouse"),
    "idol": Relic("idol", "a carved idol", "the carved idol", "chitter-chitter", "It hummed like tiny teeth.", "lizard"),
    "shell": Relic("shell", "a shell charm", "the shell charm", "chitter-chitter", "It clicked like a hidden nest.", "bird"),
}

TRANSFORMATIONS = {
    "mouse": Transformation("mouse", "a small mouse", "tiny whiskers", "quick feet", "a squeaky voice", "owl-light", tags={"chitter", "transformation"}),
    "lizard": Transformation("lizard", "a little lizard", "a scaly back", "small claws", "a thin hiss", "cold stone", tags={"chitter", "transformation"}),
    "bird": Transformation("bird", "a little bird", "soft feathers", "light toes", "a peeping voice", "the open sky", tags={"chitter", "transformation"}),
}

ENDINGS = {
    "lost": Ending("lost", "lost", 2, "faint chittering", tags={"bad_ending"}),
    "sealed": Ending("sealed", "sealed", 2, "a sealed door", tags={"bad_ending"}),
}

HERO_NAMES = ["Mina", "Nora", "Lia", "Tess", "Rin", "Pia"]
GUIDE_NAMES = ["Pip", "Jory", "Finn", "Beck", "Oren", "Sol"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    relic: str
    transformation: str
    ending: str
    hero: str
    hero_type: str
    guide: str
    guide_type: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for rid, rel in RELICS.items():
            for tid, tr in TRANSFORMATIONS.items():
                if can_transform(rel, tr) and danger_check(rel, SETTINGS[sid]):
                    for eid, ending in ENDINGS.items():
                        if acceptable_ending(ending):
                            combos.append((sid, rid, tid, eid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with chittering transformation and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-type", choices=["girl", "boy"])
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
    if args.relic and args.transformation:
        if not can_transform(RELICS[args.relic], TRANSFORMATIONS[args.transformation]):
            raise StoryError("That relic cannot cause that transformation.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.relic is None or c[1] == args.relic)
              and (args.transformation is None or c[2] == args.transformation)
              and (args.ending is None or c[3] == args.ending)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, rid, tid, eid = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    guide_type = args.guide_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(HERO_NAMES)
    guide = args.guide or rng.choice([n for n in GUIDE_NAMES if n != hero])
    return StoryParams(sid, rid, tid, eid, hero, hero_type, guide, guide_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the word "chitter" and ends badly.',
        f"Tell a short adventure where {f['hero'].id} hears something chittering, touches a strange relic, and transforms into {f['trans'].label}.",
        f"Write a scary little exploration story where a child follows a sound into a dark place and the ending is sad.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    relic = f["relic"]
    trans = f["trans"]
    ans1 = (
        f"{hero.id} and {guide.id} went exploring together. "
        f"They found a strange relic that made a chittering sound in a dark place."
    )
    ans2 = (
        f"{hero.id} touched the relic and transformed into {trans.label}. "
        f"That changed {hero.id}'s body and voice, which made the situation worse."
    )
    ans3 = (
        f"The ending was bad because they could not get back before night. "
        f"The adventure stopped with {hero.id} still trapped after the transformation."
    )
    return [
        QAItem("Who went on the adventure?", ans1),
        QAItem("What happened when the child touched the relic?", ans2),
        QAItem("Why is the ending bad?", ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    rel: Relic = f["relic"]
    trans: Transformation = f["trans"]
    ending: Ending = f["ending_def"]
    return [
        QAItem("What does chittering sound like?", "Chittering sounds like tiny quick clicks or little scratchy sounds."),
        QAItem("Why can a dark cave be scary?", "A dark cave is scary because it is hard to see what is there, so surprises can hide in the shadows."),
        QAItem("What is transformation in a story?", "Transformation means something changes into something else, like a child turning into a small animal."),
        QAItem("What makes a bad ending?", "A bad ending leaves the characters stuck, lost, or unable to fix the problem before the story is over."),
        QAItem("What does the relic do?", f"The relic is a strange object that can change someone into {trans.label}."),
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
        if e.transformed_into:
            bits.append(f"transformed_into={e.transformed_into}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cavern", "chime", "mouse", "lost", "Mina", "girl", "Pip", "boy"),
    StoryParams("ruins", "idol", "lizard", "sealed", "Nora", "girl", "Finn", "boy"),
    StoryParams("island", "shell", "bird", "lost", "Tess", "girl", "Beck", "boy"),
]


def explain_rejection(relic: Relic, setting: Setting) -> str:
    if not danger_check(relic, setting):
        return "(No story: that relic would not create a good chittering danger in this setting.)"
    return "(No story: this combination has no valid adventure hazard.)"


def outcome_of(params: StoryParams) -> str:
    if params.ending not in ENDINGS:
        return "?"
    return "bad"


ASP_RULES = r"""
danger(R, S) :- relic(R), setting(S), chitter(R), dark(S).
touch_triggers(R, T) :- relic(R), transformation(T), transforms_into(R, T).
bad(outcome) :- touched(hero), transformed(hero), bad_end(E).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SETTINGS.items():
        if s.dark_place:
            lines.append(asp.fact("dark", sid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("chitter", rid))
        lines.append(asp.fact("transforms_into", rid, r.transforms_into))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    for eid in ENDINGS:
        lines.append(asp.fact("bad_end", eid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, relic=None, transformation=None, ending=None, hero=None, hero_type=None, guide=None, guide_type=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        RELICS[params.relic],
        TRANSFORMATIONS[params.transformation],
        ENDINGS[params.ending],
        params.hero, params.hero_type, params.guide, params.guide_type,
    )
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c in asp_valid_combos():
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
