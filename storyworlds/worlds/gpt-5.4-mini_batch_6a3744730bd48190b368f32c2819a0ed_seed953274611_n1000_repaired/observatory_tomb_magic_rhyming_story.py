#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/observatory_tomb_magic_rhyming_story.py
=======================================================================

A tiny, self-contained storyworld for a rhyming magical tale set between an
observatory and a tomb.

Premise
-------
A child apprentice and a cautious helper explore an old observatory after
finding a rune key that can open a hidden tomb chamber. A small spell goes
wrong, then a wiser magic turn turns the scare into a safe reveal: the tomb is
not a monster's home but a listening room full of stars, bells, and a gentle
map. The story keeps a rhyming, child-facing tone, but the state machine still
drives the turn and ending image.

This file follows the Storyweavers world contract:
- stdlib-only script
- imports shared results eagerly
- imports shared asp lazily inside ASP helpers
- includes StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
MAGIC_SAFE_MIN = 2
FEAR_LIMIT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
class Setting:
    id: str
    label: str
    place_line: str
    hush_line: str
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    magical: bool = False
    dangerous: bool = False
    luminous: bool = False
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
class Spell:
    id: str
    label: str
    cast_line: str
    power: int
    sense: int
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
class Helper:
    id: str
    label: str
    role_line: str
    traits: list[str] = field(default_factory=list)
    cautious: bool = False
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
class StoryParams:
    setting: str
    object: str
    spell: str
    helper: str
    hero_name: str
    hero_gender: str
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


SETTINGS = {
    "observatory": Setting(
        id="observatory",
        label="the observatory",
        place_line="A round old observatory stood on the hill, where moonbeams liked to play.",
        hush_line="Inside, the dome was hushed, and glassy stars were painted on the wall.",
        tags={"observatory", "stars", "night"},
    ),
    "tomb": Setting(
        id="tomb",
        label="the tomb",
        place_line="A stone tomb slept under the cypress tree, with silver moss along the seam.",
        hush_line="Inside, the chamber was cool and still, and every footstep sounded like a dream.",
        tags={"tomb", "stone", "night"},
    ),
    "courtyard": Setting(
        id="courtyard",
        label="the moonlit courtyard",
        place_line="A moonlit courtyard shone with vines and little archways in a ring.",
        hush_line="The night was calm, the marble bright, and every corner seemed to sing.",
        tags={"courtyard", "night"},
    ),
}

OBJECTS = {
    "astrolabe": ObjectCfg(
        id="astrolabe",
        label="the astrolabe",
        phrase="a brass astrolabe with a tiny star",
        tags={"observatory", "stars"},
        magical=True,
        luminous=True,
    ),
    "rune_key": ObjectCfg(
        id="rune_key",
        label="the rune key",
        phrase="a rune key with a moon-bright spark",
        tags={"tomb", "magic"},
        magical=True,
        dangerous=False,
        luminous=True,
    ),
    "sealed_door": ObjectCfg(
        id="sealed_door",
        label="the sealed door",
        phrase="a sealed door with a sleepy lock",
        tags={"tomb"},
        magical=True,
        dangerous=True,
    ),
    "lantern": ObjectCfg(
        id="lantern",
        label="the lantern",
        phrase="a little lantern of blue glass",
        tags={"night"},
        luminous=True,
    ),
}

SPELLS = {
    "glimmer": Spell(
        id="glimmer",
        label="glimmer spell",
        cast_line="The child whispered a glimmer spell, and a silver thread of light began to hum.",
        power=2,
        sense=3,
        tags={"magic", "light"},
    ),
    "rhyme_unseal": Spell(
        id="rhyme_unseal",
        label="rhyme unseal spell",
        cast_line="They spoke in rhyme, soft and low, and made the rune key start to glow.",
        power=3,
        sense=3,
        tags={"magic", "rhyme"},
    ),
    "spark_burst": Spell(
        id="spark_burst",
        label="spark burst spell",
        cast_line="They tried a spark burst spell in pride, and crackling sparks leapt far and wide.",
        power=1,
        sense=1,
        tags={"magic", "risk"},
    ),
}

HELPERS = {
    "owl": Helper(
        id="owl",
        label="an old owl",
        role_line="An old owl perched nearby and blinked, as if it knew the ancient tune.",
        traits=["wise", "quiet"],
        cautious=True,
    ),
    "cat": Helper(
        id="cat",
        label="a white cat",
        role_line="A white cat padded in and curled beside the door, calm as a stone.",
        traits=["quiet", "watchful"],
        cautious=True,
    ),
    "cousin": Helper(
        id="cousin",
        label="a cousin",
        role_line="A cousin came along, singing softly so the nerves would not grow mean.",
        traits=["brave", "kind"],
        cautious=False,
    ),
}

GENTLE_NAMES = ["Mina", "Oren", "Sage", "Lina", "Perry", "Nia", "Arlo", "June", "Tavi", "Mara"]
GENTLE_GENDERS = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for o in OBJECTS:
            for sp in SPELLS:
                if reasonableness_ok(s, o, sp):
                    combos.append((s, o, sp))
    return combos


def reasonableness_ok(setting_id: str, object_id: str, spell_id: str) -> bool:
    setting = SETTINGS[setting_id]
    obj = OBJECTS[object_id]
    spell = SPELLS[spell_id]
    if setting_id == "observatory" and not (obj.magical or "stars" in obj.tags):
        return False
    if setting_id == "tomb" and not obj.magical:
        return False
    if spell.sense < SENSE_MIN:
        return False
    if obj.dangerous and spell.power < MAGIC_SAFE_MIN:
        return False
    return True


def best_spell() -> Spell:
    return max(SPELLS.values(), key=lambda s: s.sense)


def predict(world: World, object_id: str, spell_id: str) -> dict:
    sim = world.copy()
    _cast_spell(sim, sim.get("hero"), OBJECTS[object_id], SPELLS[spell_id], narrate=False)
    return {
        "fear": sim.get("hero").meme("fear"),
        "reveal": sim.facts.get("reveal", ""),
        "light": sim.facts.get("light", 0.0),
    }


def _cast_spell(world: World, hero: Entity, obj: ObjectCfg, spell: Spell, narrate: bool = True) -> None:
    hero.meters["magic"] = hero.meter("magic") + 1
    hero.memes["wonder"] = hero.meme("wonder") + 1
    if spell.id == "spark_burst":
        hero.memes["fear"] = hero.meme("fear") + 1
        world.get("room").meters["dust"] = world.get("room").meter("dust") + 1
        if narrate:
            world.say(spell.cast_line)
    else:
        world.facts["light"] = world.facts.get("light", 0.0) + spell.power
        if narrate:
            world.say(spell.cast_line)


def tension(world: World, hero: Entity, helper: Entity, setting: Setting, obj: ObjectCfg) -> None:
    hero.memes["curiosity"] = hero.meme("curiosity") + 1
    world.say(setting.place_line)
    world.say(f"{setting.hush_line} {hero.id} and {helper.id} stood there like two dots in a rhyme.")
    world.say(f'"Look there," {helper.id} said, "the {obj.label} and the hidden thing behind it shine."')


def invite(world: World, hero: Entity, helper: Entity, obj: ObjectCfg, spell: Spell) -> None:
    world.say(f"{hero.id} grinned at {helper.id} and lifted {obj.phrase}.")
    world.say(f'"I know a {spell.label}," {hero.id} said, "and it may make the dark go thin."')


def warn(world: World, helper: Entity, hero: Entity, obj: ObjectCfg, spell: Spell) -> None:
    pred = predict(world, obj.id, spell.id)
    helper.memes["caution"] = helper.meme("caution") + 1
    if pred["fear"] >= FEAR_LIMIT:
        world.say(f'"Careful now," {helper.id} said. "A wild spell can make a small worry swell."')
    else:
        world.say(f'"Careful now," {helper.id} said, "let us choose a spell that keeps the air well."')


def resolve_path(world: World, hero: Entity, helper: Entity) -> str:
    return "safe" if helper.meme("caution") >= 1 else "bold"


def decide(world: World, hero: Entity, helper: Entity, obj: ObjectCfg, spell: Spell) -> bool:
    if spell.sense >= best_spell().sense:
        return True
    return helper.cautious


def reveal_magic(world: World, hero: Entity, helper: Entity, setting: Setting, obj: ObjectCfg) -> None:
    if setting.id == "observatory":
        world.say("The room brightened, and the hidden map on the dome began to gleam.")
        world.say("The stars on the wall looked near enough to hum a tune.")
    else:
        world.say("The stone gave a sigh, and a secret seam shone like thread.")
        world.say("Under the dust, a silver map blinked, as if the tomb had been read.")


def end_image(world: World, hero: Entity, helper: Entity, setting: Setting, obj: ObjectCfg) -> None:
    if setting.id == "observatory":
        world.say(f'At last {hero.id} held the {obj.label} high, and the ceiling took the light.')
        world.say(f'{helper.id} smiled, and the observatory looked warm instead of night.')
    else:
        world.say(f'At last {hero.id} set the {obj.label} down, and the tomb looked kind and still.')
        world.say(f'{helper.id} smiled, and the little silver map slept on the sill.')


def tell(setting: Setting, obj: ObjectCfg, spell: Spell, helper_cfg: Helper,
         hero_name: str, hero_gender: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_cfg.id, kind="character", type="owl" if helper_cfg.id == "owl" else "cat", role="helper"))
    world.add(Entity(id="room", type="room", label=setting.label))
    world.facts["setting"] = setting.id
    world.facts["object"] = obj.id
    world.facts["spell"] = spell.id
    world.facts["helper"] = helper_cfg.id
    tension(world, hero, helper, setting, obj)
    world.para()
    invite(world, hero, helper, obj, spell)
    warn(world, helper, hero, obj, spell)
    if decide(world, hero, helper, obj, spell):
        _cast_spell(world, hero, obj, spell)
        world.para()
        reveal_magic(world, hero, helper, setting, obj)
        world.para()
        end_image(world, hero, helper, setting, obj)
        world.facts["ending"] = "wonder"
    else:
        _cast_spell(world, hero, obj, SPELLS["spark_burst"])
        world.para()
        world.say("The sparks hissed, the helper gasped, and the child chose a calmer way.")
        world.say("They tried again with a gentler rhyme, and the dark grew warm and sweet.")
        world.facts["ending"] = "calm"
    world.facts["hero"] = hero
    world.facts["helper_ent"] = helper
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a rhyming magical story that includes the words "observatory" and "tomb".',
        f"Tell a child-friendly rhyme story where {f['hero'].id} explores an {f['setting']} with magic, and a helper warns them to be careful.",
        f"Write a short magical rhyme about a {f['object']} in the {f['setting']} that leads to a hidden tomb reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    setting = SETTINGS[world.facts["setting"]]
    obj = OBJECTS[world.facts["object"]]
    helper_cfg = HELPERS[world.facts["helper"]]
    hero = world.facts["hero"]
    qa = [
        QAItem(
            question="Where did the story happen?",
            answer=f"It happened in {setting.label}. The story also mentions a tomb, and the setting shaped the whole magical rhyme."
        ),
        QAItem(
            question="What did the child use magic on?",
            answer=f"{hero.id} used magic with {obj.phrase}. That choice mattered because the object could help reveal something hidden."
        ),
        QAItem(
            question="Who helped the child be careful?",
            answer=f"{helper_cfg.label} helped by warning {hero.id} to choose a safer spell. That kept the magic from turning too wild."
        ),
    ]
    if world.facts.get("ending") == "wonder":
        qa.append(QAItem(
            question="How did the story end?",
            answer="It ended with a gentle reveal and a bright image. The observatory or tomb changed from scary to kind, and the magic stayed safe."
        ))
    else:
        qa.append(QAItem(
            question="How did the story end?",
            answer="It ended calmly after a bad spark attempt. The child slowed down, used a gentler rhyme, and the dark became safe to see in."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    obj = OBJECTS[world.facts["object"]]
    setting = SETTINGS[world.facts["setting"]]
    items = [
        QAItem(
            question="What is an observatory?",
            answer="An observatory is a place where people look at stars and the sky. It often has a dome or a big sky window."
        ),
        QAItem(
            question="What is a tomb?",
            answer="A tomb is a stone place built for the dead. It is usually quiet, cool, and meant to be left alone."
        ),
    ]
    if "magic" in obj.tags:
        items.append(QAItem(
            question="What does it mean when something is magical?",
            answer="Magical things can do surprising or enchanted things in a story. They may glow, open hidden doors, or reveal secret shapes."
        ))
    if setting.id == "observatory":
        items.append(QAItem(
            question="Why might an observatory feel special?",
            answer="An observatory feels special because it is made for looking at stars. That makes it a good place for glowing magic."
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
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="observatory", object="astrolabe", spell="glimmer", helper="owl", hero_name="Mina", hero_gender="girl"),
    StoryParams(setting="tomb", object="rune_key", spell="rhyme_unseal", helper="cat", hero_name="Arlo", hero_gender="boy"),
    StoryParams(setting="observatory", object="lantern", spell="glimmer", helper="cousin", hero_name="Nia", hero_gender="girl"),
]


def explain_rejection(setting_id: str, object_id: str, spell_id: str) -> str:
    if not reasonableness_ok(setting_id, object_id, spell_id):
        if setting_id == "tomb" and not OBJECTS[object_id].magical:
            return "(No story: the tomb needs a magical object, or the scene loses its hidden-turn spark.)"
        if SPELLS[spell_id].sense < SENSE_MIN:
            return "(No story: that spell is too shaky for a child-safe rhyming story.)"
        return "(No story: this combination does not fit the observatory/tomb magic premise.)"
    return "(No story: this combination is not available.)"


def valid_story_paths() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming magical storyworld about an observatory and a tomb.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--object", choices=list(OBJECTS))
    ap.add_argument("--spell", choices=list(SPELLS))
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_story_paths()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)
              and (args.spell is None or c[2] == args.spell)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, object_id, spell_id = rng.choice(sorted(combos))
    if not reasonableness_ok(setting_id, object_id, spell_id):
        raise StoryError(explain_rejection(setting_id, object_id, spell_id))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(GENTLE_GENDERS)
    name = args.name or rng.choice(GENTLE_NAMES)
    return StoryParams(
        setting=setting_id,
        object=object_id,
        spell=spell_id,
        helper=helper_id,
        hero_name=name,
        hero_gender=gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.object not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object}")
    if params.spell not in SPELLS:
        raise StoryError(f"Unknown spell: {params.spell}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if not reasonableness_ok(params.setting, params.object, params.spell):
        raise StoryError(explain_rejection(params.setting, params.object, params.spell))
    world = tell(SETTINGS[params.setting], OBJECTS[params.object], SPELLS[params.spell], HELPERS[params.helper], params.hero_name, params.hero_gender)
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


ASP_RULES = r"""
magical_object(O) :- object(O), magical(O).
safe_spell(S) :- spell(S), sense(S, N), sense_min(M), N >= M.
valid(P, O, S) :- setting(P), object(O), spell(S), magical_object(O), safe_spell(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.magical:
            lines.append(asp.fact("magical", oid))
    for spid, sp in SPELLS.items():
        lines.append(asp.fact("spell", spid))
        lines.append(asp.fact("sense", spid, sp.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_story_paths())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid story paths:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    else:
        print(f"OK: gate matches valid_story_paths() ({len(py)} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke-tested generate() on a curated default story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, object, spell) combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.hero_name}: {p.setting} / {p.object} / {p.spell}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
