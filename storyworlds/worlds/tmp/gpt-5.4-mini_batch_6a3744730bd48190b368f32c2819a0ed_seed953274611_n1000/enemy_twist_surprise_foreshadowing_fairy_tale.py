#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/enemy_twist_surprise_foreshadowing_fairy_tale.py
===============================================================================

A standalone story world for a tiny fairy-tale domain built from the seed words
enemy / twist / surprise / foreshadowing.

Premise
-------
A brave child or young helper follows a clue through a fairy-tale place, thinks
they face an enemy, and then the story turns: the "enemy" is not what they
seemed. A small surprise and a clear foreshadowed clue reveal the truth, and the
ending image shows the changed relationship.

The world models:
- typed entities with physical meters and emotional memes
- a tiny causal engine that drives the turn
- a reasonableness gate that only allows plausible setups
- Q&A derived from world state, not from parsing rendered prose
- an inline ASP twin for parity checks

This file is self-contained aside from the shared result containers in
storyworlds/results.py. ASP helpers are imported lazily only when needed.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "princess", "woman"}
        male = {"boy", "father", "king", "prince", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    scene: str
    dark_place: str
    clue_place: str
    ending_image: str
    enemy_title: str


@dataclass
class Enemy:
    id: str
    label: str
    looks: str
    clue: str
    truth: str
    surprise_line: str
    foreshadow_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    sparkle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    kind: str  # "mend", "reveal", "invite"
    text: str
    ending: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    enemy: str
    charm: str
    resolution: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    ruler: str
    ruler_gender: str
    seed: Optional[int] = None


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


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    foe = world.facts.get("foe")
    if not foe:
        return out
    if foe.meters["seen"] < THRESHOLD:
        return out
    sig = ("reveal", foe.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper = world.facts["helper"]
    hero = world.facts["hero"]
    foe.memes["fear"] = 0.0
    foe.memes["warmth"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    helper.memes["surprise"] += 1
    out.append("__reveal__")
    return out


def _r_mend(world: World) -> list[str]:
    out: list[str] = []
    foe = world.facts.get("foe")
    charm = world.facts.get("charm_ent")
    if not foe or not charm:
        return out
    if charm.meters["spark"] < THRESHOLD:
        return out
    sig = ("mend", charm.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    foe.meters["healed"] += 1
    foe.memes["relief"] += 1
    out.append("__mend__")
    return out


CAUSAL_RULES = [
    Rule("reveal", "social", _r_reveal),
    Rule("mend", "social", _r_mend),
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


def reasonableness_gate(setting: Setting, enemy: Enemy, resolution: Resolution) -> bool:
    return bool(setting.dark_place and enemy.clue and enemy.truth and resolution.sense >= SENSE_MIN)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for eid, e in ENEMIES.items():
            for rid, r in RESOLUTIONS.items():
                if reasonableness_gate(s, e, r):
                    combos.append((sid, eid, rid))
    return combos


def best_resolution() -> Resolution:
    return max(RESOLUTIONS.values(), key=lambda r: (r.sense, r.power))


def _set_scene(world: World, hero: Entity, helper: Entity, ruler: Entity, setting: Setting, enemy: Enemy) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Once upon a time, in {setting.scene}, {hero.id} and {helper.id} walked "
        f"under the soft moonlight while {ruler.id} watched from the window."
    )
    world.say(
        f"Far ahead was {setting.dark_place}, and everyone whispered about "
        f"{setting.enemy_title} {enemy.label}."
    )


def _foreshadow(world: World, hero: Entity, helper: Entity, enemy: Enemy) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"Before they reached it, {helper.id} noticed a small clue: {enemy.clue}. "
        f"{enemy.foreshadow_line}"
    )
    world.say(
        f'{hero.id} bit {hero.pronoun("possessive")} lip. "Do you think {enemy.label} '
        f'is our enemy?" {hero.pronoun()} asked.'
    )


def _surprise(world: World, enemy: Enemy, ruler: Entity) -> None:
    foe = world.facts["foe"]
    foe.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(enemy.surprise_line)
    world.say(f"Then {ruler.label_word} stepped closer, and the surprise grew even bigger.")


def _twist(world: World, enemy: Enemy, resolution: Resolution) -> None:
    foe = world.facts["foe"]
    if resolution.kind == "reveal":
        world.say(
            f"But the twist was this: {enemy.label} was not a true enemy at all. "
            f"{enemy.truth}"
        )
    elif resolution.kind == "invite":
        world.say(
            f"But the twist was this: {enemy.label} had only been guarding the way. "
            f"{enemy.truth}"
        )
    else:
        world.say(
            f"But the twist was this: {enemy.label} needed help, not fear. "
            f"{enemy.truth}"
        )
    foe.memes["trust"] += 1


def _resolution(world: World, enemy: Enemy, charm: Charm, resolution: Resolution, ruler: Entity) -> None:
    charm_ent = world.facts["charm_ent"]
    charm_ent.meters["spark"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{ruler.label_word.capitalize()} lifted {charm.phrase}, and it {charm.sparkle}. '
        f"{resolution.text}"
    )
    world.say(f"{resolution.ending}")
    world.say(
        f"In the end, {enemy.label} looked less like an enemy and more like someone "
        f"who had been waiting for kindness."
    )


def tell(setting: Setting, enemy: Enemy, charm: Charm, resolution: Resolution,
         hero_name: str = "Mira", hero_gender: str = "girl",
         helper_name: str = "Nico", helper_gender: str = "boy",
         ruler_name: str = "Queen Elin", ruler_gender: str = "queen") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    ruler = world.add(Entity(id=ruler_name, kind="character", type=ruler_gender, role="ruler", label="the ruler"))
    foe = world.add(Entity(id=enemy.id, kind="character", type="thing", role="enemy", label=enemy.label,
                           traits=["mysterious"], attrs={"setting": setting.id}))
    charm_ent = world.add(Entity(id=charm.id, kind="thing", type="thing", role="charm", label=charm.label))
    hero.memes["fear"] = 1.0
    helper.memes["surprise"] = 0.0
    world.facts.update(hero=hero, helper=helper, ruler=ruler, foe=foe, charm_ent=charm_ent)
    _set_scene(world, hero, helper, ruler, setting, enemy)
    world.para()
    _foreshadow(world, hero, helper, enemy)
    _surprise(world, enemy, ruler)
    world.para()
    _twist(world, enemy, resolution)
    _resolution(world, enemy, charm, resolution, ruler)
    world.facts.update(setting=setting, enemy_cfg=enemy, charm_cfg=charm, resolution_cfg=resolution,
                       outcome=resolution.kind)
    return world


SETTINGS = {
    "forest": Setting(
        id="forest",
        scene="an old fairy forest",
        dark_place="the hollow tree",
        clue_place="the mossy path",
        ending_image="fireflies blinked over the moss",
        enemy_title="the so-called enemy",
    ),
    "castle": Setting(
        id="castle",
        scene="a bright stone castle",
        dark_place="the tower stairs",
        clue_place="the narrow hallway",
        ending_image="the flags hummed in the breeze",
        enemy_title="the so-called enemy",
    ),
    "garden": Setting(
        id="garden",
        scene="a rose garden behind the palace",
        dark_place="the ivy arch",
        clue_place="the winding path",
        ending_image="roses swayed in the evening wind",
        enemy_title="the so-called enemy",
    ),
}

ENEMIES = {
    "wolf": Enemy(
        id="wolf",
        label="the wolf",
        looks="grey and stern",
        clue="one pawprint had a thorn stuck in it",
        truth="A thorn had pricked its paw, so it had been limping instead of chasing.",
        surprise_line="Out stepped the wolf, but it was limping, not lunging.",
        foreshadow_line="The pawprint clue had already hinted that something hurt was hidden there.",
        tags={"enemy", "wolf", "foreshadowing", "surprise", "twist"},
    ),
    "witch": Enemy(
        id="witch",
        label="the witch",
        looks="small and sharp-eyed",
        clue="the broom had been left upside down",
        truth="She had been carrying medicine for the king's garden, not a curse.",
        surprise_line="Out came the witch, but her basket held herbs, not trouble.",
        foreshadow_line="The upside-down broom was a sign that she had hurried, not schemed.",
        tags={"enemy", "witch", "foreshadowing", "surprise", "twist"},
    ),
    "dragon": Enemy(
        id="dragon",
        label="the dragon",
        looks="red and smoky",
        clue="warm smoke curled from the keyhole",
        truth="It was only guarding a sleeping chick, and it had asked for help without words.",
        surprise_line="The door opened with a creak, and the dragon blinked sleepily inside.",
        foreshadow_line="The warm smoke hinted that the fire was small and caring, not cruel.",
        tags={"enemy", "dragon", "foreshadowing", "surprise", "twist"},
    ),
}

CHARMS = {
    "song": Charm(id="song", label="a silver song", phrase="a silver song", sparkle="shimmered like dawn"),
    "bread": Charm(id="bread", label="a warm loaf of bread", phrase="a warm loaf of bread", sparkle="smelled sweet and safe"),
    "lantern": Charm(id="lantern", label="a little lantern", phrase="a little lantern", sparkle="glowed gold"),
}

RESOLUTIONS = {
    "mend": Resolution(
        id="mend",
        kind="mend",
        text="The light touched the hurt place, and the enemy sighed with relief.",
        ending="The dark place felt smaller, and the fear in the air melted away.",
        power=3,
        sense=3,
    ),
    "reveal": Resolution(
        id="reveal",
        kind="reveal",
        text="The truth came out at last, and everyone saw why the enemy had seemed so strange.",
        ending="The children stood still, then smiled when they understood.",
        power=4,
        sense=4,
    ),
    "invite": Resolution(
        id="invite",
        kind="invite",
        text="The ruler invited the enemy to come closer and explain its lonely watch.",
        ending="Soon the path was no longer lonely at all.",
        power=2,
        sense=2,
    ),
}

GIRL_NAMES = ["Mira", "Elsa", "Lina", "Iris", "Nora", "Tilda"]
BOY_NAMES = ["Nico", "Bram", "Otto", "Perry", "Alfie", "Gus"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world with enemy, twist, surprise, and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--enemy", choices=ENEMIES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--ruler")
    ap.add_argument("--ruler-gender", choices=["queen", "king"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.enemy is None or c[1] == args.enemy)
              and (args.resolution is None or c[2] == args.resolution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, enemy, resolution = rng.choice(sorted(combos))
    charm = args.charm or rng.choice(sorted(CHARMS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    ruler_gender = args.ruler_gender or rng.choice(["queen", "king"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    ruler = args.ruler or ("Queen Elin" if ruler_gender == "queen" else "King Oren")
    return StoryParams(
        setting=setting,
        enemy=enemy,
        charm=charm,
        resolution=resolution,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        ruler=ruler,
        ruler_gender=ruler_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    enemy = f["enemy_cfg"]
    return [
        f'Write a fairy-tale story for a young child in {setting.scene} that includes the word "enemy".',
        f"Tell a story with foreshadowing, a surprise, and a twist where {f['hero'].id} thinks {enemy.label} is an enemy, but the truth is kinder than it first seems.",
        f"Write a gentle fairy tale in which a clue at {setting.clue_place} hints that {enemy.label} is not what it appears to be.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    ruler = f["ruler"]
    enemy = f["enemy_cfg"]
    setting = f["setting"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id}, {helper.id}, and {ruler.id} in {setting.scene}. They are the ones who notice the strange enemy and follow the clue.",
        ),
        QAItem(
            question="What clue helped foreshadow the twist?",
            answer=f"The clue was {enemy.clue}. It foreshadowed that something about {enemy.label} was unusual, and that hint made the later surprise feel earned.",
        ),
        QAItem(
            question="What was the surprise in the story?",
            answer=f"The surprise was that {enemy.label} was not a true enemy. When the characters saw it up close, they learned the truth instead of the rumor.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {enemy.label} had been misunderstood. The story turned from fear to kindness once {enemy.truth.lower()}",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {enemy.label} no longer seeming like an enemy. The ending image was calm and bright, so the change from fear to understanding could be felt clearly.",
        ),
    ]
    if f["resolution_cfg"].kind == "mend":
        qa.append(QAItem(
            question="What did the ruler do with the charm?",
            answer=f"{ruler.id} lifted {f['charm_cfg'].phrase}, and it helped the scene feel gentle. That small act matched the fairy-tale mood and let relief spread.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["enemy_cfg"].tags) | set(f["setting"].id for _ in [0])
    tags |= set(f["charm_cfg"].tags)
    if f["resolution_cfg"].kind == "reveal":
        tags.add("surprise")
        tags.add("twist")
        tags.add("foreshadowing")
    items = []
    if "enemy" in tags:
        items.append(QAItem(
            question="What is an enemy?",
            answer="An enemy is someone or something that seems opposed or dangerous. In fairy tales, a story can later reveal that the enemy was misunderstood.",
        ))
    if "foreshadowing" in tags:
        items.append(QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small hint that comes early in a story. It helps the later surprise feel surprising but still fair.",
        ))
    if "surprise" in tags:
        items.append(QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the characters think. It often makes the story feel lively and memorable.",
        ))
    if "twist" in tags:
        items.append(QAItem(
            question="What is a twist?",
            answer="A twist is a turn in the story that changes the meaning of earlier events. It makes the ending feel different from what readers first guessed.",
        ))
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("dark_place", sid, s.dark_place))
        lines.append(asp.fact("clue_place", sid, s.clue_place))
    for eid, e in ENEMIES.items():
        lines.append(asp.fact("enemy", eid))
        lines.append(asp.fact("clue", eid, e.clue))
        lines.append(asp.fact("truth", eid, e.truth))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,E,R) :- setting(S), enemy(E), resolution(R).
sensible(R) :- resolution(R), sense(R,S), sense_min(M), S >= M.
outcome(reveal) :- resolution(R), kind(R,reveal).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if py - ap:
            print("  only in python:", sorted(py - ap))
        if ap - py:
            print("  only in asp:", sorted(ap - py))
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        return 1
    print("OK: default generation smoke test produced a story.")
    return rc


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    enemy = ENEMIES.get(params.enemy)
    charm = CHARMS.get(params.charm)
    resolution = RESOLUTIONS.get(params.resolution)
    if not all([setting, enemy, charm, resolution]):
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(
        setting=setting,
        enemy=enemy,
        charm=charm,
        resolution=resolution,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        ruler_name=params.ruler,
        ruler_gender=params.ruler_gender,
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


CURATED = [
    StoryParams(setting="forest", enemy="wolf", charm="song", resolution="reveal", hero="Mira", hero_gender="girl", helper="Nico", helper_gender="boy", ruler="Queen Elin", ruler_gender="queen"),
    StoryParams(setting="castle", enemy="witch", charm="bread", resolution="mend", hero="Lina", hero_gender="girl", helper="Bram", helper_gender="boy", ruler="King Oren", ruler_gender="king"),
    StoryParams(setting="garden", enemy="dragon", charm="lantern", resolution="invite", hero="Nora", hero_gender="girl", helper="Otto", helper_gender="boy", ruler="Queen Elin", ruler_gender="queen"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.enemy is None or c[1] == args.enemy)
              and (args.resolution is None or c[2] == args.resolution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, enemy, resolution = rng.choice(sorted(combos))
    charm = args.charm or rng.choice(sorted(CHARMS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    ruler_gender = args.ruler_gender or rng.choice(["queen", "king"])
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=hero)
    ruler = args.ruler or ("Queen Elin" if ruler_gender == "queen" else "King Oren")
    return StoryParams(setting=setting, enemy=enemy, charm=charm, resolution=resolution,
                       hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender,
                       ruler=ruler, ruler_gender=ruler_gender)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld with enemy, twist, surprise, and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--enemy", choices=ENEMIES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--ruler")
    ap.add_argument("--ruler-gender", choices=["queen", "king"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible resolutions: {', '.join(asp_sensible())}\n")
        for s, e, r in asp_valid_combos():
            print(f"  {s:7} {e:7} {r}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.setting}, {p.enemy}, {p.resolution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
