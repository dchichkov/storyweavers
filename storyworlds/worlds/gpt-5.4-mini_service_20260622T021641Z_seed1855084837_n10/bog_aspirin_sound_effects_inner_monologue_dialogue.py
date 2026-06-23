#!/usr/bin/env python3
"""
storyworlds/worlds/bog_aspirin_sound_effects_inner_monologue_dialogue.py
=========================================================================

A standalone story world for a small fairy-tale domain about a child, a bog,
and a tiny aspirin remedy. The world uses physical meters and emotional memes,
with sound effects, inner monologue, and dialogue driving a stateful story.

Seed tale premise:
- A little traveler wants to cross a bog to help someone with a sore head.
- A risky shortcut is considered, but a helpful voice warns against it.
- A safe, gentle plan appears: use a proper path, a lantern, and aspirin.
- The ending shows mud, relief, and a calm fairy-tale image.

Words to include: bog, aspirin
Features: Sound Effects, Inner Monologue, Dialogue
Style: Fairy Tale
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))


@dataclass
class Setting:
    id: str
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
class Remedy:
    id: str
    label: str
    phrase: str
    good_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}
        self.weather: str = ""

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.weather = self.weather
        return c


@dataclass
class StoryParams:
    setting: str
    activity: str
    remedy: str
    light: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent_name: str
    parent_gender: str
    trait: str
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
    "marsh_edge": Setting(id="marsh_edge", place="the mossy edge of the bog", indoors=False, affords={"wander", "splash"}),
    "lantern_cottage": Setting(id="lantern_cottage", place="the lantern cottage by the reeds", indoors=False, affords={"wander"}),
}

ACTIVITIES = {
    "wander": Activity(
        id="wander",
        verb="walk through the bog",
        gerund="walking through the bog",
        rush="dash into the bog",
        mess="muddy",
        soil="muddy and cold",
        zone={"feet", "legs"},
        tags={"bog", "mud"},
    ),
    "splash": Activity(
        id="splash",
        verb="splash in the bog",
        gerund="splashing in the bog",
        rush="race into the bog",
        mess="muddy",
        soil="muddy and dripping",
        zone={"feet", "legs"},
        tags={"bog", "mud"},
    ),
}

REMEDIES = {
    "aspirin": Remedy(
        id="aspirin",
        label="aspirin",
        phrase="a tiny aspirin tablet",
        good_for={"headache", "aching"},
        tags={"aspirin", "heal"},
    ),
    "herb_tea": Remedy(
        id="herb_tea",
        label="herb tea",
        phrase="a warm cup of herb tea",
        good_for={"tired", "aching"},
        tags={"tea", "heal"},
    ),
}

LIGHTS = {
    "lantern": Light(id="lantern", label="lantern", phrase="a brass lantern", glow="glowed like a calm star", tags={"light"}),
    "candle": Light(id="candle", label="candle", phrase="a little candle", glow="flickered softly", tags={"light"}),
}

GIRL_NAMES = ["Mira", "Anya", "Lina", "Ella", "Nina"]
BOY_NAMES = ["Bram", "Owen", "Tomas", "Pavel", "Eli"]
TRAITS = ["brave", "gentle", "curious", "kind", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid in setting.affords:
            for rid, remedy in REMEDIES.items():
                if "aspirin" in remedy.id and aid in {"wander", "splash"}:
                    combos.append((sid, aid, rid))
    return combos


def reasonableness_gate(setting: Setting, activity: Activity, remedy: Remedy) -> bool:
    return setting.id in SETTINGS and activity.id in ACTIVITIES and remedy.id in REMEDIES


def predict_mud(world: World, hero: Entity, activity: Activity) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters[activity.mess] = sim.get(hero.id).meters.get(activity.mess, 0.0) + 1.0
    return sim.get(hero.id).meters.get("muddy", 0.0) >= THRESHOLD


def tell(setting: Setting, activity: Activity, remedy: Remedy, light: Light,
         hero_name: str, hero_gender: str, helper_name: str, helper_gender: str,
         parent_name: str, parent_gender: str, trait: str) -> World:
    world = World(setting)
    world.weather = "misty"
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero",
                            meters={"muddy": 0.0, "relief": 0.0, "curiosity": 0.0, "fear": 0.0},
                            memes={"hope": 1.0, "worry": 0.0, "joy": 0.0},
                            attrs={"trait": trait}, tags={"child"}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper",
                              meters={"muddy": 0.0, "relief": 0.0},
                              memes={"worry": 0.0, "kindness": 1.0},
                              attrs={}, tags={"child"}))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent",
                              meters={"work": 0.0, "relief": 0.0},
                              memes={"worry": 0.0, "love": 1.0},
                              attrs={}, tags={"adult"}))
    world.add(Entity(id="bog", kind="thing", type="bog", label="the bog", meters={"wet": 1.0}, memes={}, tags={"place", "bog"}))
    world.add(Entity(id="remedy", kind="thing", type=remedy.id, label=remedy.label, phrase=remedy.phrase, tags=remedy.tags))
    world.add(Entity(id="light", kind="thing", type=light.id, label=light.label, phrase=light.phrase, tags=light.tags))

    hero.memes["curiosity"] = 1.0
    world.say(f"Once in a fairy tale, {hero.id} and {helper.id} came to {setting.place}, where the reeds shone silver.")
    world.say(f"The lantern {light.glow}, and the bog answered with a soft, sleepy hush.")
    world.say(f'{hero.id} thought, "I could {activity.verb} and bring {remedy.label} to the sick mouse in the willow hut."')
    world.say(f'But {helper.id} said, "{activity.verb.capitalize()}? The bog will swallow your boots!"')

    world.para()
    hero.memes["worry"] += 1.0
    world.say(f"{hero.id} listened to the squish of the mud. Squelch. Splat.")
    if predict_mud(world, hero, activity):
        world.say(f'{"I should be careful,"} {hero.id} thought. {"The bog is no place for a careless leap."}')
    world.say(f'{hero.id} whispered, "I want to help, but I do not want to sink."')

    world.para()
    helper.memes["worry"] += 1.0
    parent.meters["work"] += 1.0
    world.say(f'{helper.id} said, "Let us take the board path instead. Tap-tap, and no one will lose a shoe."')
    world.say(f'{parent.id} nodded. "Very wise," {parent.pronoun().capitalize()} said. "And for the little headache, here is {remedy.phrase}."')
    world.say(f"Glug-glug, the cup went down, and the aspirin rested in a spoon of honey.")

    hero.memes["joy"] += 1.0
    hero.memes["relief"] += 1.0
    helper.memes["relief"] += 1.0
    parent.meters["work"] += 1.0
    world.say(f"{hero.id} took the safe path. Tap, tap, tap. The bog stayed behind the reeds.")
    world.say(f"The mouse drank the remedy, and soon its tiny ears perked up again.")
    world.say(f"At the end, {hero.id}'s boots were only a little muddy, {remedy.label} had done its gentle work, and the lantern still glowed like a star.")

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        setting=setting,
        activity=activity,
        remedy=remedy,
        light=light,
        safe_path=True,
        muddy=hero.meters["muddy"] > 0,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a young child that includes the words "bog" and "{f["remedy"].label}".',
        f'Tell a gentle story with dialogue, sound effects, and inner monologue about {f["hero"].id} crossing a bog to help someone.',
        f'Write a short fairy tale where a child chooses a safe path through a bog and uses {f["remedy"].phrase} to help.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    remedy = f["remedy"]
    activity = f["activity"]
    light = f["light"]
    return [
        QAItem(
            question=f"Why did {hero.id} want to go through the bog?",
            answer=f"{hero.id} wanted to go through the bog because {hero.id} was trying to help the sick mouse in the willow hut. {remedy.label} was part of the little healing plan, but the path still had to be safe.",
        ),
        QAItem(
            question=f"What did {helper.id} say when {hero.id} wanted to {activity.verb}?",
            answer=f"{helper.id} warned that the bog could swallow boots and told {hero.id} to use the board path instead. That warning kept the story safe and helped everyone choose a wiser way.",
        ),
        QAItem(
            question=f"How did {parent.id} help at the end?",
            answer=f"{parent.id} gave {hero.id} {remedy.phrase} and praised the careful choice. The help worked because the child stayed out of the bog and chose the safer road.",
        ),
        QAItem(
            question=f"What happened to the lantern?",
            answer=f"The lantern {light.glow} all through the tale. It made the path bright enough to follow the safe boards and still felt like a fairy-tale star.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is a bog?",
            answer="A bog is a wet, muddy place where the ground can feel soft and slippery. It is the kind of place where careful steps matter.",
        ),
        QAItem(
            question="What is aspirin?",
            answer="Aspirin is a medicine that grown-ups use for some aches and pains. It should be used the right way and with care.",
        ),
        QAItem(
            question="Why do lanterns help in the dark?",
            answer="Lanterns give steady light, so people can see where to step. That makes a tricky path easier and safer to follow.",
        ),
    ]
    if f["remedy"].id == "aspirin":
        out.append(QAItem(
            question="Why was the remedy safe in this story?",
            answer="The remedy was safe because it was given as part of a careful helping plan. The story also showed a safe path, so the child could help without rushing into danger.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="marsh_edge", activity="wander", remedy="aspirin", light="lantern",
                hero_name="Mira", hero_gender="girl", helper_name="Bram", helper_gender="boy",
                parent_name="Queen Alder", parent_gender="woman", trait="careful"),
    StoryParams(setting="marsh_edge", activity="splash", remedy="aspirin", light="lantern",
                hero_name="Eli", hero_gender="boy", helper_name="Anya", helper_gender="girl",
                parent_name="King Rowan", parent_gender="man", trait="gentle"),
]


ASP_RULES = r"""
safe_route(hero) :- hero(hero), not into_bog(hero).
muddy(hero) :- into_bog(hero).
better_choice(hero) :- safe_route(hero), remedy(aspirin).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
    lines.append(asp.fact("uses", "aspirin"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_smoke() -> bool:
    import asp
    model = asp.one_model(asp_program("#show safe_route/1."))
    return isinstance(model, list)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale bog world with aspirin, sound effects, inner monologue, and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.activity is None or c[1] == args.activity)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, aid, rid = rng.choice(sorted(combos))
    setting = SETTINGS[sid]
    activity = ACTIVITIES[aid]
    remedy = REMEDIES[rid]
    light = args.light or rng.choice(sorted(LIGHTS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    parent_gender = args.parent_gender or rng.choice(["woman", "man"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero_name])
    parent_name = args.parent_name or rng.choice(["Queen Rowan", "King Alder", "Lady Fern", "Lord Reed"])
    trait = args.trait or rng.choice(TRAITS)
    if not reasonableness_gate(setting, activity, remedy):
        raise StoryError("The chosen combination does not make a reasonable fairy-tale story.")
    return StoryParams(setting=sid, activity=aid, remedy=rid, light=light,
                       hero_name=hero_name, hero_gender=hero_gender,
                       helper_name=helper_name, helper_gender=helper_gender,
                       parent_name=parent_name, parent_gender=parent_gender,
                       trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.activity not in ACTIVITIES or params.remedy not in REMEDIES or params.light not in LIGHTS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], REMEDIES[params.remedy], LIGHTS[params.light],
                 params.hero_name, params.hero_gender, params.helper_name, params.helper_gender,
                 params.parent_name, params.parent_gender, params.trait)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            ok = False
            print("MISMATCH: story generation produced empty text.")
    except Exception as e:
        ok = False
        print(f"MISMATCH: generation failed: {e}")
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos")
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
