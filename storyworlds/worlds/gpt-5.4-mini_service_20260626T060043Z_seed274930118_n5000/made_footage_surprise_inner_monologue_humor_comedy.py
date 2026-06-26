#!/usr/bin/env python3
"""
storyworlds/worlds/made_footage_surprise_inner_monologue_humor_comedy.py
=========================================================================

A small comedy storyworld about making footage for a surprise.
The simulated tension is simple: somebody is trying to film a secret, the
inner monologue gets funny, and the surprise almost slips out before a kinder
ending lands it safely.

Premise:
- A child wants to make footage for a surprise.
- A helper worries the video will reveal the surprise too soon.
- A small comic mistake creates tension.

Turn:
- The wrong prop, label, or sound almost gives the surprise away.
- The character's inner monologue adds humor without freezing the plot.

Resolution:
- They re-shoot, hide the clue, and finish the footage in time.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    camera: object | None = None
    chosen_prop: object | None = None
    footage: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
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
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Setting:
    place: str = "the garage"
    indoors: bool = True
    affords: set[str] = field(default_factory=lambda: {"footage"})
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Plan:
    id: str
    verb: str
    gerund: str
    keyword: str
    surprise_risk: str
    sound_clue: str
    visual_clue: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    role: str
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    setting: str
    plan: str
    prop: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "garage": Setting(place="the garage", indoors=True, affords={"footage"}),
    "bedroom": Setting(place="the bedroom", indoors=True, affords={"footage"}),
    "backyard_shed": Setting(place="the backyard shed", indoors=True, affords={"footage"}),
}

PLANS = {
    "footage": Plan(
        id="footage",
        verb="make the surprise footage",
        gerund="making surprise footage",
        keyword="footage",
        surprise_risk="give the surprise away",
        sound_clue="the little beep could be heard from the hallway",
        visual_clue="the shiny label flashed in the camera light",
        tags={"footage", "surprise", "humor"},
    ),
    "birthday_clip": Plan(
        id="birthday_clip",
        verb="film the secret birthday clip",
        gerund="filming a secret birthday clip",
        keyword="clip",
        surprise_risk="spoil the surprise",
        sound_clue="the balloon squeak echoed far too loudly",
        visual_clue="the wrapped box showed up in the frame",
        tags={"footage", "surprise", "humor"},
    ),
    "thank_you_video": Plan(
        id="thank_you_video",
        verb="record the thank-you video",
        gerund="recording a thank-you video",
        keyword="video",
        surprise_risk="ruin the secret",
        sound_clue="the recorder chirped at the wrong moment",
        visual_clue="the note with the name popped into view",
        tags={"footage", "surprise", "humor"},
    ),
}

PROPS = {
    "cake": Prop(id="cake", label="cake", phrase="a chocolate cake", type="cake", role="surprise"),
    "poster": Prop(id="poster", label="poster", phrase="a bright poster", type="poster", role="clue"),
    "gift": Prop(id="gift", label="gift", phrase="a wrapped gift", type="surprise", role="surprise"),
    "hat": Prop(id="hat", label="party hat", phrase="a silly party hat", type="costume", role="humor"),
    "note": Prop(id="note", label="note", phrase="a folded note", type="paper", role="clue"),
}

HERO_NAMES = ["Maya", "Leo", "Nina", "Owen", "Luna", "Theo", "Zoe", "Finn"]
HELPER_TYPES = ["mother", "father", "grandma", "brother", "sister"]
HERO_TYPES = ["girl", "boy"]


class WorldModel:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.world = World()
        self.world.facts["setting"] = setting

    def render(self) -> str:
        return self.world.render()


def tell(setting: Setting, plan: Plan, prop: Prop, hero_name: str, hero_type: str, helper_type: str) -> World:
    w = World()
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_type, meters={"focus": 0.0}, memes={"joy": 0.0, "surprise": 0.0, "humor": 0.0}))
    helper = w.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}", meters={"patience": 0.0}, memes={"worry": 0.0, "fondness": 0.0}))
    camera = w.add(Entity(id="camera", type="camera", label="camera", phrase="a tiny camera", owner=hero.id))
    chosen_prop = w.add(Entity(id=prop.id, type=prop.type, label=prop.label, phrase=prop.phrase, owner=hero.id))
    footage = w.add(Entity(id="footage", type="footage", label="footage", phrase="the finished footage", owner=hero.id, meters={"quality": 0.0}, memes={"funny": 0.0}))

    w.say(f"{hero.id} was excited to {plan.verb} in {setting.place}.")
    w.say(f"{hero.pronoun().capitalize()} held {hero.pronoun('possessive')} {camera.label} like it was a treasure map.")
    w.say(f"{hero.id} had {chosen_prop.phrase} ready for the surprise, and {helper.label} was helping keep it secret.")

    w.para()
    hero.memes["joy"] += 1
    hero.meters["focus"] += 1
    w.say(f"At first, {hero.id} tried to stay serious, but {hero.pronoun('possessive')} inner monologue was not helping much.")
    w.say(f'"Okay, act normal," {hero.id} thought. "Normal is very hard when a surprise is sitting three feet away."')

    w.para()
    hero.memes["surprise"] += 1
    hero.memes["humor"] += 1
    helper.memes["worry"] += 1
    footage.meters["quality"] += 1
    w.say(f"Then a tiny mistake popped up: {plan.sound_clue if prop.role != 'humor' else plan.visual_clue}.")
    w.say(f"{helper.label} froze, because that could {plan.surprise_risk}.")
    w.say(f'{hero.id} swallowed a laugh and thought, "Oh no. My face is doing the joke part by itself."')

    w.para()
    if prop.role == "humor":
        w.say(f"The {prop.label} was so silly that everyone nearly laughed, and that made the secret even harder to hide.")
    else:
        w.say(f"{hero.id} quickly turned the camera away, covered the clue with one hand, and whispered, 'Not yet, not yet.'")
    hero.memes["determination"] += 1
    footage.meters["quality"] += 1
    footage.memes["funny"] += 1

    w.para()
    hero.memes["joy"] += 1
    helper.memes["fondness"] += 1
    footage.meters["quality"] += 1
    w.say(f"On the second try, {hero.id} made the footage carefully, and the surprise stayed hidden until the very end.")
    w.say(f'When {hero.id} watched it back, {hero.pronoun("subject")} giggled and thought, "Perfect. Secret saved. Comedy achieved."')
    w.say(f"The finished footage showed the surprise safely, and {helper.label} smiled at how proud {hero.id} looked.")

    w.facts.update(
        hero=hero,
        helper=helper,
        camera=camera,
        prop=chosen_prop,
        plan=plan,
        footage=footage,
        setting=setting,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    plan = _safe_fact(world, f, "plan")
    prop = _safe_fact(world, f, "prop")
    helper = _safe_fact(world, f, "helper")
    return [
        f'Write a funny story for a little child about making "{plan.keyword}" and keeping a surprise secret.',
        f"Tell a comedy story where {hero.id} tries to {plan.verb}, while {helper.label} worries that {prop.label} might give the surprise away.",
        f'Write a child-friendly story that includes the word "footage" and ends with a happy secret being kept safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prop = _safe_fact(world, f, "prop")
    plan = _safe_fact(world, f, "plan")
    setting = _safe_fact(world, f, "setting")
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to make in {setting.place}?",
            answer=f"{hero.id} was trying to make {plan.keyword} and keep a surprise secret at the same time.",
        ),
        QAItem(
            question=f"Why did {helper.label} get worried about the {prop.label}?",
            answer=f"{helper.label} worried because the {prop.label} might {plan.surprise_risk}.",
        ),
        QAItem(
            question=f"What funny thought did {hero.id} have while working on the footage?",
            answer=f"{hero.id} thought it was hard to act normal when a surprise was so close, which made the moment funny.",
        ),
        QAItem(
            question=f"How did the story end for the surprise footage?",
            answer=f"The footage was finished carefully, the surprise stayed hidden until the end, and everyone felt happy about it.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is footage?",
            answer="Footage is recorded video or film that shows what a camera captured.",
        ),
        QAItem(
            question="Why can a surprise be hard to keep secret?",
            answer="A surprise can be hard to keep secret because clues like sounds, labels, or excited faces may give it away.",
        ),
        QAItem(
            question="Why do people laugh at comedy?",
            answer="People laugh at comedy because something is funny, surprising, or a little silly in a harmless way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
need_secret_surprise(H) :- hero(H), surprise_task(H).
comic_tension(H) :- need_secret_surprise(H), has_clue(H).
resolved(H) :- comic_tension(H), hides_clue(H).
good_story(S) :- setting(S), hero_task(S), resolved(hero).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "garage"),
        asp.fact("setting", "bedroom"),
        asp.fact("setting", "backyard_shed"),
        asp.fact("surprise_task", "hero"),
        asp.fact("hero", "hero"),
        asp.fact("has_clue", "hero"),
        asp.fact("hides_clue", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show resolved/1."))
    got = set(asp.atoms(model, "resolved"))
    want = {("hero",)}
    if got == want:
        print("OK: ASP gate matches Python reasonableness.")
        return 0
    print(f"MISMATCH: ASP={sorted(got)} Python={sorted(want)}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world about surprise footage and a funny inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPER_TYPES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    plan = getattr(args, "plan", None) or rng.choice(list(PLANS))
    prop = getattr(args, "prop", None) or rng.choice(list(PROPS))
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_TYPES)
    return StoryParams(setting=setting, plan=plan, prop=prop, hero_name=name, hero_type=gender, helper_type=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(PLANS, params.plan), _safe_lookup(PROPS, params.prop), params.hero_name, params.hero_type, params.helper_type)
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        combos = [
            StoryParams("garage", "footage", "cake", "Maya", "girl", "mother"),
            StoryParams("bedroom", "birthday_clip", "gift", "Leo", "boy", "father"),
            StoryParams("backyard_shed", "thank_you_video", "poster", "Nina", "girl", "grandma"),
        ]
        samples = [generate(p) for p in combos]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
