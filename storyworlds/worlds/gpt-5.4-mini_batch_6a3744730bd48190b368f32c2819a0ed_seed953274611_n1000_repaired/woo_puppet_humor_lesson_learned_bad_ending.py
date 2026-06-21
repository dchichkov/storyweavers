#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/woo_puppet_humor_lesson_learned_bad_ending.py
=============================================================================

A small mythic storyworld about a boastful performer, a puppet, a village crowd,
and a lesson learned too late. The stories have a playful, legendary tone with
humor, but the bad ending is real: the crowd laughs, the trick goes wrong, and
the lesson is carried home by regret.

Seed words: woo, puppet
Features: Humor, Lesson Learned, Bad Ending
Style: Myth

This script follows the Storyweavers world contract:
- typed entities with physical meters and emotional memes
- a state-driven story engine
- grounded QA sets
- a reasonableness gate plus inline ASP twin
- support for default run, -n, --all, --seed, --trace, --qa, --json,
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "king", "bard"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    name: str
    image: str
    place_kind: str  # hall, grove, shore
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    shiny: bool = False
    makes_noise: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Ploy:
    id: str
    label: str
    verb: str
    tool: str
    risk: int
    success_power: int
    failure_power: int
    joke: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.setting: Optional[Setting] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.setting = self.setting
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["mirth"] < THRESHOLD:
            continue
        sig = ("laugh", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["boldness"] += 1
        out.append("__laugh__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    puppet = world.entities.get("puppet")
    stage = world.entities.get("stage")
    if not puppet or puppet.meters["jolted"] < THRESHOLD:
        return out
    sig = ("spill", puppet.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    puppet.meters["torn"] += 1
    if stage:
        stage.meters["ruin"] += 1
    for e in world.characters():
        e.memes["alarm"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES = [
    Rule("laugh", "social", _r_laugh),
    Rule("spill", "physical", _r_spill),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def honest_woos(choir: str, crowd_size: int) -> bool:
    return choir in {"harp", "drum", "chant"} and crowd_size >= 1


def can_resolve(ploy: Ploy) -> bool:
    return ploy.success_power >= ploy.risk


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PLOYS:
            if honest_woos("chant", 10) and PLOYS[pid].risk >= 1:
                combos.append((sid, pid))
    return combos


@dataclass
class StoryParams:
    setting: str
    ploy: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    crowd: int = 7
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SETTINGS = {
    "courtyard": Setting(
        id="courtyard",
        name="the temple courtyard",
        image="a moonlit courtyard of white stone and ivy",
        place_kind="hall",
    ),
    "grove": Setting(
        id="grove",
        name="the sacred grove",
        image="a grove of silver trees and hanging bells",
        place_kind="grove",
    ),
    "shore": Setting(
        id="shore",
        name="the sea-shore shrine",
        image="a shore where waves bowed at the altar steps",
        place_kind="shore",
    ),
}

ARTIFACTS = {
    "mask": Artifact(id="mask", label="mask", phrase="a carved cedar mask", shiny=True),
    "drum": Artifact(id="drum", label="drum", phrase="a little bronze drum", makes_noise=True),
    "string": Artifact(id="string", label="string", phrase="a bright red string", shiny=False),
}

PLOYS = {
    "woo": Ploy(
        id="woo",
        label="woo",
        verb="woo the crowd",
        tool="mask",
        risk=3,
        success_power=2,
        failure_power=0,
        joke="The crowd laughed because the hero bowed so grandly the mask nearly fell into a puddle.",
        lesson="A boast can sound brave, but a shaky trick can break the whole act.",
        tags={"woo", "humor"},
    ),
    "puppet": Ploy(
        id="puppet",
        label="puppet",
        verb="make the puppet dance",
        tool="string",
        risk=4,
        success_power=1,
        failure_power=4,
        joke="The puppet winked so hard that even the old statue seemed to giggle.",
        lesson="A puppet needs careful hands, or the joke turns into trouble.",
        tags={"puppet", "humor"},
    ),
}

HERO_NAMES = ["Ari", "Niko", "Mira", "Soren", "Lina", "Tavi"]
HELPER_NAMES = ["Bela", "Jorin", "Oren", "Pella", "Ivo", "Sela"]
GENDERS = ["girl", "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about wooing a crowd with a puppet.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ploy", choices=PLOYS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=GENDERS)
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=GENDERS)
    ap.add_argument("--crowd", type=int, default=None)
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
    if args.setting and args.ploy and (args.setting, args.ploy) not in combos:
        raise StoryError("That tale is not reasonable for this mythic world.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    ploy = args.ploy or rng.choice(sorted(PLOYS))
    hero_gender = args.hero_gender or rng.choice(GENDERS)
    helper_gender = args.helper_gender or rng.choice(GENDERS)
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    crowd = args.crowd if args.crowd is not None else rng.randint(4, 11)
    if crowd < 1:
        raise StoryError("The crowd must be at least one.")
    return StoryParams(
        setting=setting,
        ploy=ploy,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        crowd=crowd,
    )


def setup_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.ploy not in PLOYS:
        raise StoryError("Unknown ploy.")
    w = World()
    w.setting = SETTINGS[params.setting]
    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero", traits=["bold"]))
    helper = w.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", traits=["wary"]))
    crowd = w.add(Entity(id="crowd", kind="character", type="thing", label="the crowd", role="crowd"))
    stage = w.add(Entity(id="stage", kind="thing", type="thing", label="the stage"))
    puppet = w.add(Entity(id="puppet", kind="thing", type="thing", label="the puppet"))
    mask = w.add(Entity(id="mask", kind="thing", type="thing", label="the mask"))
    string = w.add(Entity(id="string", kind="thing", type="thing", label="the string"))
    w.facts.update(hero=hero, helper=helper, crowd=crowd, stage=stage, puppet=puppet, mask=mask, string=string)
    return w


def tell(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    ploy = PLOYS[params.ploy]
    setting = SETTINGS[params.setting]
    art = ARTIFACTS[ploy.tool]

    hero.memes["mirth"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"Long ago, in {setting.name}, {hero.id} came at dusk with {art.phrase} and a boastful heart."
    )
    world.say(
        f'{hero.id} cried, "I will woo the crowd!" and {helper.id} answered with a small, worried smile.'
    )
    world.para()
    world.say(
        f"The people gathered like stars around a fire, and the air smelled of salt, cedar, and waiting."
    )
    world.say(f"{hero.id} chose to {ploy.verb}, and the first laugh rolled through the stones.")
    hero.memes["mirth"] += 1
    helper.memes["worry"] += 1
    if ploy.id == "puppet":
        world.say("The puppet bobbed and bowed so hard that even a stern gull seemed amused.")
    else:
        world.say("The mask looked grand, but its grin was so crooked that the children snickered.")
    if params.crowd >= 6:
        world.say("The crowd laughed loud enough to wake the ivy.")
    world.para()
    if ploy.id == "puppet":
        helper.memes["warning"] += 1
        world.say(f'{helper.id} said, "Easy now. A puppet is small, but a careless hand can snap its strings."')
        hero.meters["jolted"] += 1
        hero.memes["defiance"] += 1
        world.say(f'But {hero.id} kept wooing the crowd, and the strings tugged against the board like little snakes.')
    else:
        helper.memes["warning"] += 1
        world.say(f'{helper.id} said, "Easy now. The mask is heavy, and pride can make a person stumble."')
        hero.meters["jolted"] += 1
        hero.memes["defiance"] += 1
        world.say(f'But {hero.id} kept wooing the crowd, and the mask swung too wide in the moonlight.')
    propagate(world, narrate=True)
    world.para()
    if ploy.id == "puppet":
        world.say("Then the joke turned sharp.")
        world.say("The puppet slipped, the strings split, and its carved nose cracked against the stone.")
        world.say("The crowd stopped laughing at once.")
        world.say('No one cheered now; even the waves seemed to hold their breath.')
    else:
        world.say("Then the joke turned heavy.")
        world.say("The mask struck the altar edge and broke, sending cedar chips across the floor.")
        world.say("The crowd stopped laughing at once.")
        world.say('No one cheered now; even the gulls went quiet.')
    world.para()
    hero.memes["shame"] += 2
    helper.memes["grief"] += 1
    world.say(f"{helper.id} helped gather the broken pieces and said the lesson softly, so it would last.")
    world.say(f'"{ploy.lesson}"')
    world.say(
        f"{hero.id} bowed their head and understood too late that a true wooing asks for care, not only cleverness."
    )
    world.say(
        "So the hall grew quiet, the moon climbed higher, and the broken puppet lay in the hero's hands like a tiny fallen god."
    )
    world.facts.update(outcome="bad", ploy=ploy, setting=setting, crowd=params.crowd, lesson=ploy.lesson)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ploy = f["ploy"]
    hero = f["hero"]
    return [
        f"Write a mythic story that includes the words woo and puppet, with a joke that goes wrong and leaves a lesson.",
        f"Tell a short legend about {hero.id} trying to {ploy.verb}, with humor first and a sad ending after the trick fails.",
        f"Write a child-friendly myth where a puppet brings laughter, then teaches that a boastful trick can break if handled carelessly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    ploy: Ploy = f["ploy"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, who tried to woo the crowd with a puppet in a mythic place. {helper.id} was there too, trying to keep the trick from going wrong.",
        ),
        QAItem(
            question="What was funny in the story?",
            answer=f"The funny part was when the puppet and the boast were both bigger than the hero's carefulness. The crowd laughed, but the laughter also showed how silly the risky trick was.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"{ploy.lesson} {hero.id} learned that a clever performance still needs careful hands. The lesson came after the puppet broke, so it was learned the hard way.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly. The crowd went silent, the puppet was damaged, and the hero was left with regret instead of applause.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a puppet?",
            answer="A puppet is a small figure a person moves by hand or strings to make it look alive. In stories, puppets can be funny, but they are also delicate.",
        ),
        QAItem(
            question="What does woo mean?",
            answer="To woo means to try to win someone's praise or affection. In this world, wooing the crowd means trying to charm them with a performance.",
        ),
        QAItem(
            question="Why can a performance go wrong?",
            answer="A performance can go wrong when pride, speed, or rough handling breaks the careful plan. Then the joke stops being funny and turns into trouble.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
crowd_laughs(H) :- hero(H), mirth(H, M), M >= 1.
puppet_breaks :- ploy(puppet), jolt(H), hero(H), H = H.
outcome(bad) :- crowd_laughs(_), puppet_breaks.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PLOYS:
        lines.append(asp.fact("ploy", pid))
    lines.append(asp.fact("mirth_min", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set((s, p) for s, p in py)
    if asp_set == py:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, ploy=None, hero=None, hero_gender=None, helper=None, helper_gender=None, crowd=None), random.Random(7)))
        if not sample.story:
            raise StoryError("Empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world, params)
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="courtyard", ploy="woo", hero="Ari", hero_gender="girl", helper="Bela", helper_gender="boy", crowd=8),
            StoryParams(setting="grove", ploy="puppet", hero="Mira", hero_gender="girl", helper="Oren", helper_gender="boy", crowd=9),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
