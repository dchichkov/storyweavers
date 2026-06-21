#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/affection_kindness_superhero_story.py
======================================================================

A small superhero storyworld about affection, kindness, and a gentle rescue.

The world models a child-friendly superhero scene:
- a hero notices someone feeling low or stuck,
- kindness changes the situation,
- affection is shown through care, praise, and a warm ending image.

The script supports:
- normal generation
- -n / --all / --seed
- --trace / --qa / --json
- --asp / --verify / --show-asp

It follows the shared Storyweavers result container API and includes an inline
ASP twin of the Python validity gate and ending logic.
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class HeroConfig:
    id: str
    title: str
    cape_color: str
    signal: str
    kindness_words: tuple[str, str]
    affection_words: tuple[str, str]
    intro: str
    rescue_verb: str
    ending_image: str
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


@dataclass
class Trouble:
    id: str
    label: str
    label_the: str
    need: str
    pressure: str
    risk: str
    resolved_by: str
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


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    action: str
    comfort: str
    tags: set[str] = field(default_factory=set)
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
        return clone


@dataclass
class Rule:
    name: str
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


def _r_affection(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["affection"] >= THRESHOLD and (("affection",) not in world.fired):
            world.fired.add(("affection",))
            out.append("Their kindness made the whole street feel warmer.")
    return out


def _r_helped(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["helped"] >= THRESHOLD and ("helped", e.id) not in world.fired:
            world.fired.add(("helped", e.id))
            out.append(f"{e.id} stood straighter, because someone had truly helped.")
    return out


CAUSAL_RULES = [Rule("affection", _r_affection), Rule("helped", _r_helped)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predicted_help(world: World, aid: Aid, trouble_id: str) -> dict:
    sim = world.copy()
    do_aid(sim, sim.get(aid.id), narrate=False)
    t = sim.get(trouble_id)
    return {"helped": t.meters["helped"] >= THRESHOLD, "comfort": t.memes["comfort"]}


def do_trouble(world: World, trouble: Entity) -> None:
    trouble.meters["stuck"] += 1
    trouble.memes["worry"] += 1
    world.say(
        f"{trouble.id} was caught by {trouble.label_the}, and the whole block felt a little too quiet."
    )


def warn_and_choose(world: World, hero: Entity, trouble: Entity, aid: Aid) -> None:
    pred = predicted_help(world, aid, trouble.id)
    if pred["helped"]:
        world.say(
            f'{hero.id} smiled. "I can fix this with {aid.label}," {hero.pronoun()} said. '
            f'Kindness was the real superpower here.'
        )
    else:
        world.say(
            f'{hero.id} frowned gently. "This needs more than a quick trick," {hero.pronoun()} said.'
        )


def do_aid(world: World, aid: Entity, narrate: bool = True) -> None:
    aid.meters["helped"] += 1
    aid.memes["kindness"] += 1
    aid.memes["affection"] += 1
    propagate(world, narrate=narrate)


def rescue(world: World, hero: Entity, trouble: Entity, aid: Aid, sidekick: Entity) -> None:
    trouble.meters["stuck"] = 0
    trouble.memes["worry"] = 0
    trouble.meters["helped"] += 1
    world.say(
        f"{hero.id} used {aid.phrase} and {aid.action}. In a blink, {trouble.id} was safe again."
    )
    world.say(
        f"{sidekick.id} cheered, because {aid.comfort} meant nobody had to be afraid anymore."
    )


def affection_ending(world: World, hero: Entity, sidekick: Entity, citizen: Entity, config: HeroConfig) -> None:
    hero.memes["affection"] += 1
    sidekick.memes["affection"] += 1
    citizen.memes["affection"] += 1
    world.say(
        f"Afterward, {hero.id} gave everyone a bright grin and a careful hug. "
        f"{config.ending_image}"
    )
    world.say(
        f"That night, the city slept easier, because kindness and affection had saved the day."
    )


def tell(config: HeroConfig, trouble: Trouble, aid: Aid, hero_name: str = "Nova",
         sidekick_name: str = "Pip", citizen_name: str = "Mina",
         hero_type: str = "girl", sidekick_type: str = "boy",
         citizen_type: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero",
                            label=config.title, traits=["brave", "kind"], tags=set(config.tags)))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_type,
                                role="sidekick", traits=["helpful"], tags={"sidekick"}))
    citizen = world.add(Entity(id=citizen_name, kind="character", type=citizen_type,
                               role="citizen", traits=["gentle"], tags={"citizen"}))
    trouble_ent = world.add(Entity(id=trouble.id, kind="thing", type="problem", label=trouble.label,
                                   attrs={"need": trouble.need}, tags=set(trouble.tags)))
    aid_ent = world.add(Entity(id=aid.id, kind="thing", type="tool", label=aid.label,
                               attrs={"comfort": aid.comfort}, tags=set(aid.tags)))

    hero.memes["kindness"] = 1.0
    hero.memes["affection"] = 1.0
    sidekick.memes["trust"] = 1.0
    citizen.memes["hope"] = 1.0

    world.say(
        f"On a bright afternoon, {hero.id} flew above the rooftops in a {config.cape_color} cape. "
        f"{config.intro}"
    )
    world.say(
        f"{sidekick.id} and {citizen.id} waved from below. They knew {hero.id} always noticed when someone needed help."
    )
    world.para()
    do_trouble(world, trouble_ent)
    warn_and_choose(world, hero, trouble_ent, aid)
    world.para()
    do_aid(world, aid_ent)
    rescue(world, hero, trouble_ent, aid, sidekick)
    world.para()
    affection_ending(world, hero, sidekick, citizen, config)

    world.facts.update(
        hero=hero, sidekick=sidekick, citizen=citizen, trouble=trouble_ent, aid=aid_ent,
        config=config, trouble_cfg=trouble, aid_cfg=aid,
        helped=trouble_ent.meters["helped"] >= THRESHOLD,
    )
    return world


HEROES = {
    "sunburst": HeroConfig(
        id="sunburst", title="Sunburst", cape_color="gold", signal="a warm star-sign",
        kindness_words=("kindness", "gentle"), affection_words=("affection", "warmth"),
        intro="Sunburst never rushed past a sad face, and always carried a tiny smile like a lantern.",
        rescue_verb="helps", ending_image="The cape fluttered like sunrise over the whole block.",
        tags={"hero", "kindness", "affection"},
    ),
    "moonlace": HeroConfig(
        id="moonlace", title="Moonlace", cape_color="silver", signal="a moon-shaped spark",
        kindness_words=("kindness", "care"), affection_words=("affection", "tenderness"),
        intro="Moonlace listened carefully before doing anything, because listening was part of the rescue.",
        rescue_verb="helps", ending_image="The silver cape shone softly, like a lamp left on for the night.",
        tags={"hero", "kindness", "affection"},
    ),
}

TROUBLES = {
    "kite": Trouble(
        id="kite", label="a kite", label_the="a kite tangled on the tall clock tower",
        need="to come down safely", pressure="the windy rope",
        risk="the line could snap", resolved_by="a careful rescue",
        tags={"rescue", "height"},
    ),
    "cat": Trouble(
        id="cat", label="a kitten", label_the="a kitten stuck on a balcony ledge",
        need="to get back down", pressure="the narrow ledge",
        risk="the kitten could panic", resolved_by="a calm rescue",
        tags={"rescue", "animal"},
    ),
    "lantern": Trouble(
        id="lantern", label="a lantern", label_the="a lantern that had gone dark in the park",
        need="to shine again", pressure="the missing battery",
        risk="the path was too dark", resolved_by="a cheerful rescue",
        tags={"light", "park"},
    ),
}

AIDS = {
    "ladder": Aid(
        id="ladder", label="the rescue ladder", phrase="the rescue ladder",
        action="climbed just high enough to free the kite", comfort="help from the top rung",
        tags={"height", "rescue"},
    ),
    "blanket": Aid(
        id="blanket", label="the soft blanket", phrase="the soft blanket and calm hands",
        action="wrapped the kitten in a gentle hug", comfort="a safe, warm bundle",
        tags={"animal", "rescue", "affection"},
    ),
    "battery": Aid(
        id="battery", label="a spare battery", phrase="a spare battery and a bright smile",
        action="swapped in a fresh battery and turned the lantern back on", comfort="light returned to the path",
        tags={"light", "park"},
    ),
}

@dataclass
class StoryParams:
    hero: str
    trouble: str
    aid: str
    hero_name: str = "Nova"
    sidekick_name: str = "Pip"
    citizen_name: str = "Mina"
    hero_type: str = "girl"
    sidekick_type: str = "boy"
    citizen_type: str = "girl"
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


CURATED = [
    StoryParams(
        hero="sunburst", trouble="kite", aid="ladder", hero_name="Nova", sidekick_name="Pip",
        citizen_name="Mina", seed=None,
    ) if False else None
]
CURATED = [
    StoryParams(hero="sunburst", trouble="kite", aid="ladder", hero_name="Nova", sidekick_name="Pip", citizen_name="Mina", hero_type="girl", sidekick_type="boy", citizen_type="girl", seed=None),
    StoryParams(hero="moonlace", trouble="cat", aid="blanket", hero_name="Luna", sidekick_name="Toby", citizen_name="Ivy", hero_type="girl", sidekick_type="boy", citizen_type="girl", seed=None),
    StoryParams(hero="sunburst", trouble="lantern", aid="battery", hero_name="Ray", sidekick_name="Ben", citizen_name="Lila", hero_type="boy", sidekick_type="boy", citizen_type="girl", seed=None),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hid, h in HEROES.items():
        for tid, t in TROUBLES.items():
            for aid, a in AIDS.items():
                if t.tags & a.tags:
                    combos.append((hid, tid, aid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about kindness and affection.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.hero is None or c[0] == args.hero)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.aid is None or c[2] == args.aid)]
    if args.hero and args.trouble and args.aid and (args.hero, args.trouble, args.aid) not in combos:
        raise StoryError("(No valid combination matches the given options.)")
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    hero, trouble, aid = rng.choice(sorted(combos))
    return StoryParams(
        hero=hero, trouble=trouble, aid=aid,
        hero_name=rng.choice(["Nova", "Luna", "Ray", "Mira", "Jett"]),
        sidekick_name=rng.choice(["Pip", "Toby", "Ben", "Ivy", "Zed"]),
        citizen_name=rng.choice(["Mina", "Lila", "Iris", "Sage", "Oona"]),
        hero_type=rng.choice(["girl", "boy"]),
        sidekick_type=rng.choice(["girl", "boy"]),
        citizen_type=rng.choice(["girl", "boy"]),
        seed=None,
    )


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, sidekick, citizen = f["hero"], f["sidekick"], f["citizen"]
    trouble, aid, config = f["trouble"], f["aid"], f["config"]
    return [
        (f"Who is the story about?",
         f"It is about {hero.id}, the superhero {config.title}. {sidekick.id} and {citizen.id} are part of the rescue too."),
        (f"Why did {hero.id} stop?",
         f"{hero.id} stopped because {trouble.label_the} needed help. {config.kindness_words[0].capitalize()} made the hero notice the problem right away."),
        (f"What did {hero.id} use to help?",
         f"{hero.id} used {aid.phrase} and fixed the trouble with care. That was the kind way to solve the problem."),
        (f"How did the story end?",
         f"It ended with everyone safe and smiling. The final image was that {config.ending_image.lower()}"),
    ]


def world_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does kindness mean?",
         "Kindness means helping gently, sharing care, and trying to make another person's day better."),
        ("What is affection?",
         "Affection is warm caring feelings that people show with smiles, hugs, kind words, and thoughtful help."),
        ("What should a superhero do first when someone needs help?",
         "A superhero should look carefully, stay calm, and choose the safest helpful action."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story that includes the word "affection" and shows {f["config"].title} using kindness to help someone.',
        f"Tell a child-friendly superhero story where {f['hero'].id} helps {f['trouble'].label} with {f['aid'].label}, ending in warmth and affection.",
        f'Create a short story about a superhero whose special power is kindness, and include the feeling of affection in the ending.',
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES or params.trouble not in TROUBLES or params.aid not in AIDS:
        raise StoryError("Invalid parameters.")
    if (params.hero, params.trouble, params.aid) not in valid_combos():
        raise StoryError("(No valid combination matches the given options.)")
    world = tell(HEROES[params.hero], TROUBLES[params.trouble], AIDS[params.aid],
                 hero_name=params.hero_name, sidekick_name=params.sidekick_name,
                 citizen_name=params.citizen_name, hero_type=params.hero_type,
                 sidekick_type=params.sidekick_type, citizen_type=params.citizen_type)
    return StorySample(
        params=params, story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_qa(world)],
        world=world,
    )


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
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
valid(H,T,A) :- hero(H), trouble(T), aid(A), compatible(T,A).
compatible(kite,ladder).
compatible(cat,blanket).
compatible(lantern,battery).
outcome(helped) :- valid(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    for t, a in [("kite", "ladder"), ("cat", "blanket"), ("lantern", "battery")]:
        lines.append(asp.fact("compatible", t, a))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: ASP gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("only in ASP:", sorted(a - p))
        print("only in Python:", sorted(p - a))
    try:
        sample = generate(resolve_params(argparse.Namespace(hero=None, trouble=None, aid=None), random.Random(7)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"FAILED smoke test: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(" ".join(c))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero}: {p.trouble} with {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
