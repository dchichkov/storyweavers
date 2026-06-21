#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cheer_curl_hock_magic_lesson_learned_myth.py
=============================================================================

A small myth-style storyworld about a child or novice helper who uses a piece of
magic in a tiny sacred task, makes a mistake, learns a lesson, and ends with a
clear changed image.

Seed words: cheer, curl, hock
Features: Magic, Lesson Learned
Style: Myth
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
MAGIC_MIN = 2


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
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
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
    scene: str
    sacred_place: str
    weather: str
    echo: str
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
class Magic:
    id: str
    name: str
    shimmer: str
    power: int
    safe: bool
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
class Relic:
    id: str
    name: str
    phrase: str
    fragile: bool
    can_bend: bool
    region: str
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


@dataclass
class Lesson:
    id: str
    text: str
    corrective: str
    gift: str
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_hush(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["storm"] >= THRESHOLD and ("hush" not in e.memes or e.memes["hush"] < THRESHOLD):
            sig = ("hush", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["fear"] += 1
            out.append("__hush__")
    return out


def _r_bend(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["bent"] >= THRESHOLD:
            sig = ("bend", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["worn"] += 1
            out.append(f"{e.label or e.id} grew bent and old.")
    return out


CAUSAL_RULES = [Rule("hush", _r_hush), Rule("bend", _r_bend)]


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


def hazard(magic: Magic, relic: Relic) -> bool:
    return magic.safe and relic.fragile


def valid_combo(magic: Magic, relic: Relic) -> bool:
    return hazard(magic, relic)


def lesson_needed(hero: Entity, relic: Relic, magic: Magic) -> bool:
    return magic.power >= MAGIC_MIN and relic.fragile


def predict(world: World, relic_id: str, magic_id: str) -> dict:
    sim = world.copy()
    relic = sim.get(relic_id)
    relic.meters["storm"] += 1
    relic.meters["bent"] += 1
    propagate(sim, narrate=False)
    return {"bent": sim.get(relic_id).meters["bent"] >= THRESHOLD}


def cast_spell(world: World, hero: Entity, magic: Magic, relic: Entity) -> None:
    hero.memes["daring"] += 1
    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} hands and called on {magic.name}. "
        f"{magic.shimmer} The air answered at once."
    )
    relic.meters["storm"] += 1
    if magic.power > 2:
        relic.meters["bent"] += 1
    propagate(world)


def warning(world: World, elder: Entity, hero: Entity, magic: Magic, relic: Relic) -> None:
    pred = predict(world, "relic", magic.id)
    elder.memes["care"] += 1
    world.facts["predicted_bent"] = pred["bent"]
    world.say(
        f'{elder.id} lifted a hand. "{hero.id}, not that charm. '
        f'It may bend {relic.name}. The old thing is brittle as dry bark."'
    )


def response(world: World, elder: Entity, magic: Magic, relic: Entity, lesson: Lesson) -> None:
    relic.meters["storm"] = 0
    if relic.meters["bent"] >= THRESHOLD:
        world.say(
            f"{elder.id} stepped in with the safer rite, and the wild shimmer settled. "
            f"The relic stopped shaking, though a little mark remained."
        )
    else:
        world.say(
            f"{elder.id} stepped in with the safer rite, and the wild shimmer settled. "
            f"The relic stayed whole."
        )
    world.say(
        f'"{lesson.text}" {elder.id} said. "{lesson.corrective}"'
    )
    world.say(
        f"Then {elder.id} gave {hero_name(world)} {lesson.gift} so the work could continue."
    )


def hero_name(world: World) -> str:
    return world.facts["hero"].id


def finish(world: World, hero: Entity, relic: Relic) -> None:
    if relic.fragile and relic.can_bend and relic_id(world).meters["bent"] >= THRESHOLD:
        world.say(
            f"In the end, {hero.id} held the bent relic carefully, and the lesson sat in "
            f"{hero.pronoun('possessive')} heart like a bright ember."
        )
    else:
        world.say(
            f"In the end, {hero.id} held the relic with steady hands, and the lesson sat in "
            f"{hero.pronoun('possessive')} heart like a bright ember."
        )


def relic_id(world: World) -> Entity:
    return world.get("relic")


def tell(setting: Setting, magic: Magic, relic: Relic, lesson: Lesson,
         hero_name_: str = "Mira", hero_type: str = "girl",
         elder_name: str = "Aunt", elder_type: str = "woman") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name_, kind="character", type=hero_type, role="hero"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder", label="the elder"))
    relic_ent = world.add(Entity(id="relic", type="relic", label=relic.name))
    world.facts["hero"] = hero
    world.facts["elder"] = elder
    world.facts["magic"] = magic
    world.facts["relic_cfg"] = relic
    world.facts["lesson_cfg"] = lesson

    world.say(
        f"Long ago, when {setting.echo} and {setting.scene} lay beneath the sky, "
        f"{hero.id} lived beside {setting.sacred_place}."
    )
    world.say(
        f"{hero.id} loved the old stories of {magic.name}. The people said its light could "
        f"make a small room cheer and make a dark path curl open."
    )
    world.say(
        f"One day {hero.id} found {relic.phrase}, and the finding felt like a sign."
    )

    world.para()
    world.say(
        f"{hero.id} raised {hero.pronoun('possessive')} chin and whispered a cheer to the wind. "
        f"Then {hero.id} reached for the charm."
    )
    warning(world, elder, hero, magic, relic)

    if lesson_needed(hero, relic, magic):
        world.say(
            f"{hero.id} did not listen at first. {hero.id} cast the magic anyway."
        )
        cast_spell(world, hero, magic, relic_ent)
        world.para()
        response(world, elder, magic, relic_ent, lesson)
        world.para()
        world.say(
            f"{hero.id} bowed {hero.pronoun('possessive')} head and learned the lesson well."
        )
    else:
        world.say(f"{hero.id} listened at once and kept the charm still.")
        world.para()
        world.say(
            f"Together they carried the relic to its place without harm, and {hero.id} learned "
            f"that restraint can be holy too."
        )
        relic_ent.meters["bent"] = 0

    world.para()
    finish(world, hero, relic)
    world.facts["outcome"] = "bent" if relic_ent.meters["bent"] >= THRESHOLD else "safe"
    world.facts["relic"] = relic_ent
    return world


SETTINGS = {
    "temple": Setting(
        id="temple",
        scene="the temple stones glowed with dusk",
        sacred_place="the hill temple",
        weather="golden",
        echo="the drums were quiet",
    ),
    "grove": Setting(
        id="grove",
        scene="the grove leaves shivered in the hush",
        sacred_place="the moon grove",
        weather="silver",
        echo="the owl kept watch",
    ),
}

MAGICS = {
    "cheer": Magic(
        id="cheer",
        name="the cheer spell",
        shimmer="A bright note leaped from the air like a bird.",
        power=3,
        safe=True,
        tags={"cheer", "magic"},
    ),
    "curl": Magic(
        id="curl",
        name="the curl spell",
        shimmer="A ribbon of light curled around the relic like smoke.",
        power=2,
        safe=True,
        tags={"curl", "magic"},
    ),
    "hock": Magic(
        id="hock",
        name="the hock spell",
        shimmer="A hard blue spark snapped like a thrown stone.",
        power=1,
        safe=False,
        tags={"hock", "magic"},
    ),
}

RELICS = {
    "horn": Relic(
        id="horn",
        name="the ivory horn",
        phrase="the ivory horn on the altar",
        fragile=True,
        can_bend=True,
        region="hands",
        tags={"myth", "fragile"},
    ),
    "crown": Relic(
        id="crown",
        name="the gold crown",
        phrase="the gold crown on the cloth",
        fragile=True,
        can_bend=True,
        region="hands",
        tags={"myth", "fragile"},
    ),
    "stone": Relic(
        id="stone",
        name="the river stone",
        phrase="the river stone beside the lamp",
        fragile=False,
        can_bend=False,
        region="hands",
        tags={"myth", "stone"},
    ),
}

LESSONS = {
    "care": Lesson(
        id="care",
        text="A wise hand does not strike the old thing first.",
        corrective="Choose the gentler way when the relic is fragile.",
        gift="a soft cloth for the relic",
        tags={"lesson", "gentle"},
    ),
    "patience": Lesson(
        id="patience",
        text="Power without patience becomes a bruise.",
        corrective="Move slowly, and let old things keep their shape.",
        gift="a lamp with a calm flame",
        tags={"lesson", "patience"},
    ),
}

@dataclass
class StoryParams:
    setting: str
    magic: str
    relic: str
    lesson: str
    hero_name: str = "Mira"
    hero_type: str = "girl"
    elder_name: str = "Aunt"
    elder_type: str = "woman"
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
    StoryParams(setting="temple", magic="cheer", relic="horn", lesson="care", hero_name="Mira", hero_type="girl", elder_name="Aunt", elder_type="woman"),
    StoryParams(setting="grove", magic="curl", relic="crown", lesson="patience", hero_name="Toma", hero_type="boy", elder_name="Uncle", elder_type="man"),
    StoryParams(setting="temple", magic="hock", relic="horn", lesson="care", hero_name="Sera", hero_type="girl", elder_name="Priest", elder_type="man"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for sid in SETTINGS:
        for mid, magic in MAGICS.items():
            for rid, relic in RELICS.items():
                for lid in LESSONS:
                    if valid_combo(magic, relic):
                        out.append((sid, mid, rid, lid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child where {f["hero"].id} uses the {f["magic"].name}, and include the words cheer, curl, and hock.',
        f"Tell a tiny myth in which {f['hero'].id} nearly harms {f['relic_cfg'].name} with magic, learns a lesson, and ends wiser.",
        f"Write a magical lesson story in a myth style about restraint, bright power, and an elder's warning.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    relic = f["relic_cfg"]
    magic = f["magic"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do with the magic?",
            answer=f"{hero.id} wanted to use {magic.name} on {relic.name}. {hero.id} thought the magic would make the old place brighter, but the relic was too fragile for a rough charm.",
        ),
        QAItem(
            question=f"Why did {elder.id} warn {hero.id}?",
            answer=f"{elder.id} warned {hero.id} because the relic was fragile and the spell could bend it. The warning gave {hero.id} a chance to choose a gentler path before real harm spread.",
        ),
    ]
    if world.facts["outcome"] == "bent":
        qa.append(
            QAItem(
                question="What changed after the mistake?",
                answer="The relic bent and the mood turned quiet, so the lesson became real. After that, the story ends with a softer touch and a better choice for next time.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="It ended safely, with the relic kept whole and the warning respected. The hero learned that even magic must be handled gently.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    magic = f["magic"]
    relic = f["relic_cfg"]
    items = [
        QAItem(
            question="What is a spell in a myth story?",
            answer="A spell is a magic action or chant that is meant to change something. In myths, spells can be beautiful, helpful, or dangerous if used carelessly.",
        ),
        QAItem(
            question="Why do people respect old relics?",
            answer="People respect old relics because they are precious and often fragile. A careful touch helps them last for many years.",
        ),
    ]
    if magic.id == "cheer":
        items.append(QAItem(
            question="What does cheer mean in this story?",
            answer="Cheer is the bright, hopeful feeling that lifts the room like a song. Here it also names a magic that sounds joyful but still needs wisdom.",
        ))
    if magic.id == "curl":
        items.append(QAItem(
            question="What does curl mean in this story?",
            answer="Curl means to bend in a smooth round shape. The curl spell makes light wrap around things like a ribbon.",
        ))
    if magic.id == "hock":
        items.append(QAItem(
            question="What does hock mean in this story?",
            answer="Hock sounds sharp and hard, like a quick snap. In the story it is the roughest spell, so it is the least safe around a fragile relic.",
        ))
    if relic.fragile:
        items.append(QAItem(
            question="What should you do with something fragile?",
            answer="You should move slowly and use a gentle touch. Fragile things can bend or break if they are handled too roughly.",
        ))
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.magic and args.relic:
        if not valid_combo(MAGICS[args.magic], RELICS[args.relic]):
            raise StoryError("That magic is too rough for that relic; the myth would not hold together.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.magic is None or c[1] == args.magic)
              and (args.relic is None or c[2] == args.relic)
              and (args.lesson is None or c[3] == args.lesson)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, magic, relic, lesson = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        magic=magic,
        relic=relic,
        lesson=lesson,
        hero_name=args.hero_name or rng.choice(["Mira", "Sera", "Toma", "Ila"]),
        hero_type=args.hero_type or rng.choice(["girl", "boy"]),
        elder_name=args.elder_name or rng.choice(["Aunt", "Uncle", "Priest", "Sage"]),
        elder_type=args.elder_type or rng.choice(["woman", "man"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.magic not in MAGICS:
        raise StoryError(f"Unknown magic: {params.magic}")
    if params.relic not in RELICS:
        raise StoryError(f"Unknown relic: {params.relic}")
    if params.lesson not in LESSONS:
        raise StoryError(f"Unknown lesson: {params.lesson}")
    world = tell(
        SETTINGS[params.setting],
        MAGICS[params.magic],
        RELICS[params.relic],
        LESSONS[params.lesson],
        hero_name_=params.hero_name,
        hero_type=params.hero_type,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(S,M,R,L) :- setting(S), magic(M), relic(R), lesson(L), safe_magic(M), fragile_relic(R).
outcome(bent) :- chosen_magic(M), chosen_relic(R), rough(M), fragile_relic(R), magic_power(M,P), P >= 2.
outcome(safe) :- chosen_magic(M), chosen_relic(R), safe_magic(M), fragile_relic(R), magic_power(M,P), P < 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        if m.safe:
            lines.append(asp.fact("safe_magic", mid))
        else:
            lines.append(asp.fact("rough", mid))
        lines.append(asp.fact("magic_power", mid, m.power))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        if r.fragile:
            lines.append(asp.fact("fragile_relic", rid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: ASP matches Python valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if a - b:
            print(" only in ASP:", sorted(a - b))
        if b - a:
            print(" only in Python:", sorted(b - a))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic magic storyworld with a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=["woman", "man"])
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
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for combo in combos:
            print(" ".join(map(str, combo)))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1
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
