#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/want_magic_fable.py
===================================================

A small standalone story world sketch for a fable-like tale about wanting
something magical, making a foolish choice, and learning a calmer way.

The domain is deliberately tiny:
- one want-driven character
- one magical object or spell
- one fragile target or need
- one wiser helper
- one ending that shows what changed

This file follows the Storyweavers world contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify,
  and --show-asp
- includes Python and ASP parity checks
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
MEME_LESSON = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"dust": 0.0, "glow": 0.0, "fracture": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"want": 0.0, "worry": 0.0, "calm": 0.0, "joy": 0.0, "lesson": 0.0})

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "witch"}
        male = {"boy", "father", "man", "king", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    sparkle: str
    risky: bool = False
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
class Target:
    id: str
    label: str
    phrase: str
    fragile: bool
    place: str
    damage: str
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
class Helper:
    id: str
    label: str
    advice: str
    remedy: str
    remedy_text: str
    power: int
    sense: int
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
        clone.facts = dict(self.facts)
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


def _r_glimmer(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["glow"] < THRESHOLD:
            continue
        sig = ("glimmer", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        out.append("__glimmer__")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    charm = world.facts.get("charm")
    target = world.facts.get("target")
    if not charm or not target:
        return out
    if not world.facts.get("sparked"):
        return out
    if target.meters["fracture"] >= THRESHOLD:
        sig = ("damage", target.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["hurt"] = True
            out.append("__damage__")
    return out


CAUSAL_RULES = [
    Rule("glimmer", "magic", _r_glimmer),
    Rule("damage", "physical", _r_damage),
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


def reasonableness_ok(charm: Charm, target: Target) -> bool:
    return charm.risky and target.fragile


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for cid, c in CHARMS.items():
        for tid, t in TARGETS.items():
            if reasonableness_ok(c, t):
                combos.append((cid, tid))
    return combos


def _readable_names(kind: str) -> list[str]:
    return HERO_NAMES_GIRL if kind == "girl" else HERO_NAMES_BOY


@dataclass
@dataclass
class StoryParams:
    charm: str
    target: str
    helper: str
    hero: str
    gender: str
    elder: str
    elder_gender: str
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


def aspirational_vs_safe(world: World, hero: Entity, charm: Charm, target: Target, helper: Helper) -> None:
    hero.memes["want"] += 1
    world.say(
        f"On a bright morning, {hero.id} saw {charm.phrase} in the lane and wanted it at once. "
        f"The little village looked quiet, but the shiny thing seemed to promise a grander day."
    )
    world.say(
        f'"I want {charm.label}," {hero.id} said, and {hero.pronoun("possessive")} eyes kept following the sparkle.'
    )
    world.para()
    world.say(
        f"Then {hero.id} hurried toward {target.place}. {target.place.capitalize()} was already crowded with {target.label}."
    )
    world.say(
        f'"If I use it here," {hero.id} thought, "the {target.label} will be covered in {target.damage}."'
    )
    hero.memes["worry"] += 1


def warn(world: World, elder: Entity, hero: Entity, charm: Charm, target: Target) -> None:
    elder.memes["calm"] += 1
    world.say(
        f'{elder.id} noticed the wish and spoke softly. "{charm.label.capitalize()} is not for play," '
        f'{elder.id} said. "It can make a quick bright mess, and {target.label} would suffer."'
    )


def choose_wrongly(world: World, hero: Entity, charm: Charm, target: Target) -> None:
    hero.memes["want"] += 1
    world.say(
        f'But {hero.id} still reached for it. {charm.sparkle} Then the magic leapt out, bright as a little storm.'
    )
    target.meters["fracture"] += 1
    target.meters["dust"] += 1
    world.facts["sparked"] = True
    propagate(world, narrate=False)


def fix_with_reason(world: World, helper: Entity, charm: Charm, target: Target) -> None:
    helper.memes["calm"] += 1
    body = helper.attrs["helper"].remedy_text.replace("{target}", target.label)
    world.say(
        f"{helper.id} came at once and {body}."
    )
    if world.facts.get("hurt"):
        world.say(
            f"The bright mess faded, and the {target.label} stayed in one piece after the scare."
        )
    else:
        world.say(
            f"The magic settled into a small harmless glow, leaving the {target.label} untouched."
        )


def lesson(world: World, elder: Entity, hero: Entity, charm: Charm) -> None:
    hero.memes["lesson"] += 1
    hero.memes["joy"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {elder.id} smiled and knelt beside {hero.id}. "
        f'"Wanting is not wrong," {elder.id} said. "But wisdom asks what a wish will do."'
    )
    world.say(
        f'{hero.id} nodded and promised to choose kinder magic next time. '
        f'The little spark that had seemed so grand now looked small beside that promise.'
    )


def ending(world: World, hero: Entity, helper: Entity, charm: Charm, target: Target) -> None:
    world.say(
        f"Afterward, {helper.id} showed {hero.id} a gentler charm: one that made only a soft glow on the path."
    )
    hero.memes["joy"] += 1
    hero.meters["glow"] += 1
    world.say(
        f"{hero.id} carried the safe glow home, and {target.label} stayed neat and whole in the morning light."
    )


def tell(charm: Charm, target: Target, helper_cfg: Helper, hero_name: str = "Mina",
         gender: str = "girl", elder_name: str = "Owl", elder_gender: str = "old_wise",
         resolved: bool = True) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, role="hero"))
    elder = world.add(Entity(id=elder_name, kind="character", type="owl", role="elder"))
    helper = world.add(Entity(id="Helper", kind="character", type="owl", role="helper", attrs={"helper": helper_cfg}))
    t = world.add(Entity(id="target", kind="thing", type="thing", label=target.label))
    c = world.add(Entity(id="charm", kind="thing", type="thing", label=charm.label))
    world.facts.update(hero=hero, elder=elder, helper=helper, target=t, charm=c, helper_cfg=helper_cfg)
    aspirational_vs_safe(world, hero, charm, target, helper_cfg)
    world.para()
    warn(world, elder, hero, charm, target)
    choose_wrongly(world, hero, charm, target)
    world.para()
    if resolved:
        fix_with_reason(world, helper, charm, target)
        lesson(world, elder, hero, charm)
        world.para()
        ending(world, hero, helper, charm, target)
    else:
        world.say(
            f"{helper.id} tried the remedy, but the magic was too tangled to finish neatly."
        )
        world.say(
            f"Even so, {hero.id} learned to stop and ask before using wild magic again."
        )
    world.facts["resolved"] = resolved
    return world


CHARRMISSING = ""  # placeholder-free strictness, unused but harmless

CHARMS = {
    "wand": Charm("wand", "wand", "a silver wand", "make a tiny bright spell", "The wand flashed like a star.", True, {"magic", "spark"}),
    "dust": Charm("dust", "glitter dust", "a pocket of glitter dust", "wake up old magic", "The dust swirled in a shining cloud.", True, {"magic", "spark"}),
    "bell": Charm("bell", "spell bell", "a little spell bell", "call a helpful charm", "The bell sang with a clear note.", True, {"magic", "spark"}),
}

TARGETS = {
    "mirror": Target("mirror", "mirror", "the mirror in the hall", True, "the hall", "cloudy marks", {"magic", "fragile"}),
    "lantern": Target("lantern", "lantern", "the old lantern on the shelf", True, "the shelf", "smudges", {"magic", "fragile"}),
    "garden": Target("garden", "garden gate", "the painted garden gate", True, "the gate", "scratches", {"magic", "fragile"}),
}

HELPERS = {
    "owl": Helper("owl", "owl", "noticed the trouble from the tree", "soften", "softened the spell and turned it into a small glow around {target}", 3, 3, {"wisdom", "magic"}),
    "turtle": Helper("turtle", "turtle", "came plodding up the path", "settle", "settled the spell and tucked the shimmer away from {target}", 3, 3, {"wisdom", "magic"}),
}

HERO_NAMES_GIRL = ["Mina", "Lila", "Nora", "Miri"]
HERO_NAMES_BOY = ["Pip", "Jax", "Tobi", "Ren"]


def valid_story_combos() -> list[tuple[str, str, str]]:
    out = []
    for cid, c in CHARMS.items():
        for tid, t in TARGETS.items():
            if reasonableness_ok(c, t):
                for hid in HELPERS:
                    out.append((cid, tid, hid))
    return out


@dataclass
class StoryParams:
    charm: str
    target: str
    helper: str
    hero: str
    gender: str
    elder: str
    elder_gender: str
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


KNOWLEDGE = {
    "magic": [("What is magic in stories?", "Magic is a pretend force in stories that can make strange and wonderful things happen.")],
    "wand": [("What does a wand do in a story?", "A wand is often a magic tool used to point, cast, or guide a spell.")],
    "owl": [("Why are owls often wise in fables?", "Owls are often shown as wise because they watch quietly and seem to know a lot.")],
    "turtle": [("Why are turtles often patient in fables?", "Turtles are often shown as patient because they move slowly and steadily.")],
    "glow": [("What is a glow?", "A glow is a soft light that shines gently, not too bright and not harsh.")],
    "fragile": [("What does fragile mean?", "Fragile means something can be hurt or broken easily.")],
}

KNOWLEDGE_ORDER = ["magic", "wand", "owl", "turtle", "glow", "fragile"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a child that includes the word "want" and a little bit of magic.',
        f"Tell a moral story where {f['hero'].id} wants {f['charm'].label}, but {f['elder'].id} warns that it could harm {f['target'].label}.",
        f"Write a simple fable ending where the magic is changed into a gentler light.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, elder, target = f["hero"], f["elder"], f["target"]
    charm, helper = f["charm"], f["helper_cfg"]
    qa = [
        ("Who is the story about?", f"It is about {hero.id}, who wanted {charm.label}, and the wise helper who guided the choice."),
        ("What did {0} want?".format(hero.id), f"{hero.id} wanted {charm.label}. That wish pushed the story forward and led to trouble near {target.label}."),
        ("What did the wise elder say?", f"{elder.id} warned that {charm.label} was not for play and could harm {target.label}. That warning gave the hero a chance to choose better."),
    ]
    if f.get("resolved"):
        qa.append(("How was the problem solved?", f"{helper.remedy_text.replace('{target}', target.label)}. The magic changed from risky to gentle, so {target.label} stayed safe."))
        qa.append(("How did the story end?", f"It ended with a safe glow and a wiser hero. {hero.id} carried home a calmer kind of magic and remembered the lesson."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["charm"].tags) | set(world.facts["target"].tags) | set(world.facts["helper_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("wand", "mirror", "owl", "Mina", "girl", "owl", "old_wise"),
    StoryParams("dust", "lantern", "turtle", "Pip", "boy", "turtle", "old_wise"),
]


def explain_rejection(charm: Charm, target: Target) -> str:
    if not reasonableness_ok(charm, target):
        return f"(No story: {charm.label} and {target.label} do not make a good magical fable pair.)"
    return "(No story: invalid combination.)"


def valid_combos_python() -> list[tuple[str, str, str]]:
    combos = []
    for cid, c in CHARMS.items():
        for tid, t in TARGETS.items():
            if reasonableness_ok(c, t):
                for hid in HELPERS:
                    combos.append((cid, tid, hid))
    return combos


ASP_RULES = r"""
risky_pair(C, T) :- charm(C), target(T), risky(C), fragile(T).
valid(C, T, H) :- risky_pair(C, T), helper(H).

% outcome is always resolved in this world; the helper softens the magic.
resolved :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if c.risky:
            lines.append(asp.fact("risky", cid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if t.fragile:
            lines.append(asp.fact("fragile", tid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos_python())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid combos ({len(py)}).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable-like magic story world.")
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["old_wise"])
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
    if args.charm and args.target:
        if not reasonableness_ok(CHARMS[args.charm], TARGETS[args.target]):
            raise StoryError(explain_rejection(CHARMS[args.charm], TARGETS[args.target]))
    combos = [
        c for c in valid_combos_python()
        if (args.charm is None or c[0] == args.charm)
        and (args.target is None or c[1] == args.target)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    charm, target, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(_readable_names(gender))
    elder = args.elder or rng.choice(["Owl", "Turtle"])
    return StoryParams(charm=charm, target=target, helper=helper, hero=hero, gender=gender, elder=elder, elder_gender="old_wise")


def generate(params: StoryParams) -> StorySample:
    world = tell(CHARMS[params.charm], TARGETS[params.target], HELPERS[params.helper], params.hero, params.gender, params.elder, params.elder_gender)
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
        print(asp_program("", "#show valid/3.\n#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for c, t, h in asp_valid_combos():
            print(f"  {c:8} {t:8} {h}")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.charm} near {p.target}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
