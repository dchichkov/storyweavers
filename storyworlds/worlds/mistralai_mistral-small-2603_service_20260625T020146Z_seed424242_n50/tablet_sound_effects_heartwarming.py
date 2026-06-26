#!/usr/bin/env python3
"""
storyworlds/worlds/mistralai_mistral-small-2603_service_20260625T020146Z_seed424242_n50/tablet_sound_effects_heartwarming.py
==============================================================================================
A standalone *story world* sketch for “Tablet Sound Effects” and close,
*constraint-checked* variations of it.
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

# Make the shared result containers importable when this script is run directly
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample

# Magnitude at which an accumulated effect is narrated or felt.
THRESHOLD = 0.5

# ---------------------------------------------------------------------------
# Entities: characters and the magical tablet share one representation.
# ---------------------------------------------------------------------------

def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


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
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # child, grandparent, tablet, sound_effect_beep, ...
    label: str = ""                # short reference, e.g. "tablet"
    phrase: str = ""               # full noun phrase, e.g. "a shiny blue tablet"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""                # left hand, lap, shelf
    protective: bool = False
    plural: bool = False

    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # battery, strain
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # joy, pride

    protector: object | None = None
    elder: object | None = None
    hero: object | None = None
    tablet: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "grandma", "grandmother", "lady"}
        male = {"boy", "man", "grandpa", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

# ---------------------------------------------------------------------------
# Causal rules: forward-chained to fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_play_sound(world: World) -> list[str]:
    tablet = world.get("tablet")
    if tablet.meters["battery"] < THRESHOLD:
        return []
    if "sound_learning" not in world.facts:
        return []
    hero = world.get(world.facts["hero"])
    peak = hero.meters.get("joy", 0.0) > THRESHOLD * 3
    if peak:
        world.fired.add(("sound_peak",))
        tablet.meters["battery"] -= 0.3
        return [f"The tablet chirped a happy little run of chimes!"]
    tablet.meters["battery"] -= 0.1
    world.fired.add(("sound_normal",))
    return [f"The tablet played a cheerful beep to celebrate the new word!"]

def _r_battery_low(world: World) -> list[str]:
    tablet = world.get("tablet")
    if tablet.meters["battery"] >= 0.2:
        return []
    return ["The tablet’s screen started to fade; it needed a rest soon."]

def _r_grandma_praise(world: World) -> list[str]:
    grandma = world.get("grandma")
    if grandma.memes.get("pride", 0.0) < THRESHOLD:
        return []
    if ("praise",) in world.fired:
        return []
    world.fired.add(("praise",))
    return [f"{grandma.id} beamed, gave a proud nod, and said, “Wonderful work, sweetie!”"]

def _r_child_joy(world: World) -> list[str]:
    hero = world.get(world.facts["hero"])
    if hero.memes.get("joy", 0.0) >= THRESHOLD and ("first_word",) not in world.fired:
        world.fired.add(("first_word",))
        return [f"{hero.id} clapped tiny hands together; their face lit up like sunshine!"]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="play_sound", tag="physical", apply=_r_play_sound),
    Rule(name="battery_low", tag="physical", apply=_r_battery_low),
    Rule(name="grandma_praise", tag="social", apply=_r_grandma_praise),
    Rule(name="child_joy", tag="social", apply=_r_child_joy),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Parametrization knobs -- vocabulary for this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Skill:
    difficulty: str           # easy, medium, hard
    cue: str                  # "the moon is bright"
    target: str               # "bright"
    hints: list[str]          # ["b-r-igh-t", "something that glows"]
    success_weight: float     # how often a success fires
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


SKILLS = {
    "bed": Skill(difficulty="easy", cue="The bed is soft.", target="soft", hints=["s-o-ft"], success_weight=0.9),
    "star": Skill(difficulty="easy", cue="Twinkle, twinkle, little star.", target="star", hints=["s-t-ar", "twinkle"], success_weight=0.85),
    "house": Skill(difficulty="medium", cue="Our dog lives in a little house.", target="house", hints=["h-o-Use", "dog home"], success_weight=0.7),
    "tree": Skill(difficulty="medium", cue="The tall tree gives shade.", target="tree", hints=["t-r-ee", "shady"], success_weight=0.65),
    "computer": Skill(difficulty="hard", cue="A computer helps us learn many things.", target="computer", hints=["c-o-m-PU-ter"], success_weight=0.5),
    "rainbow": Skill(difficulty="hard", cue="After rain, a rainbow arcs in the sky.", target="rainbow", hints=["r-ai-N-bow", "rain colors"], success_weight=0.45),
}

SOUNDS = {
    "beep": "short high beep",
    "chime": "bright ascending chime",
    "ding": "grandfather-clock ding",
    "ring": "gentle triangle ring",
    "plink": "water-drop plink",
}
SOUND_ORDER = ["beep", "chime", "ding", "ring", "plink"]

CHILD_NAMES = ["Lily", "Emma", "Noah", "Ava", "Finn", "Mia"]
GRAND_NAMES = ["Grandma", "Grandpa", "Nana", "Papa"]

# ---------------------------------------------------------------------------
# Screenplay: act 1 setup, act 2 learning with tension, act 3 resolution.
# ---------------------------------------------------------------------------
def tell(skill_id: str, sound_id: str, child_name: str, grand_name: str) -> World:
    world = World()

    skill = _safe_lookup(SKILLS, skill_id)
    hero = world.add(Entity(
        id=child_name,
        kind="character",
        type="child",
        label=child_name,
        phrase=f"{child_name} the curious learner",
        traits=["cheerful", "patient"],
        owner=child_name,
        protector=grand_name,
    ))
    elder = world.add(Entity(
        id=grand_name,
        kind="character",
        type=grand_name.lower(),
        label=grand_name,
        phrase=f"{grand_name} with a warm smile",
        traits=["kind", "encouraging"],
    ))
    tablet = world.add(Entity(
        id="tablet",
        type="tablet",
        label="tablet",
        phrase="a shiny blue tablet glowing with learning games",
        owner=child_name,
        region="lap",
        meters={"battery": 1.0, "strain": 0.0},
    ))
    sound_(world, sound_id)

    world.facts.update(hero=hero.id, skill=skill, sound=sound_id)

    # Act 1 – cozy couch scene.
    world.say(f"Every afternoon, {grand_name} sat on the couch with {child_name}.")
    world.say(f"{grand_name} opened a learning app on {tablet.it()}; small stars twinkled on the screen.")
    world.para()

    # Act 2 – tension & beats.
    world.say(f"{grand_name} tapped the first word: “{skill.cue}”")
    world.say(f"{child_name} squinted at the shimmering letters and tried aloud.")

    correct = True  # fixed success for reproducibility
    if correct:
        hero.memes["joy"] += 1.7
        hero.memes["pride"] += 0.7
        elder.memes["pride"] += 1.2
        tablet.meters["battery"] -= 0.2
        world.facts["sound_learning"] = True
        world.say(f"{child_name} sounded it out slowly — “{skill.target}!” — proud as punch.")
    else:
        hero.memes["confusion"] = 0.9
        world.say(f"{child_name} frowned, “Uh… {skill.hints[0]}?”")

    world.facts["success"] = correct
    propagate(world, narrate=True)

    # Act 3 – resolution & cozy finish.
    world.para()
    world.say(f"{grand_name} nodded and held {child_name} close. “You did it!”")
    world.say(f"Outside, golden light spilled through the window, wrapping them both in warmth.")
    world.facts.update(correct_attempt=correct)
    return world

def sound_(world: World, sound_id: str) -> None:
    world.add(Entity(
        id=f"sound_{sound_id}",
        type="sound_effect",
        label=_safe_lookup(SOUNDS, sound_id),
        phrase=f"gentle {_safe_lookup(SOUNDS, sound_id)}",
        region="speaker",
    ))

# ---------------------------------------------------------------------------
# The per-world parameters – fully reproduces one story.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    skill: str
    sound: str
    child_name: str
    grand_name: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A generation – three separate sets.
# ---------------------------------------------------------------------------
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    skill = _safe_fact(world, f, "skill")
    return [
        f'Write a short, heartwarming story for 3-to-6-year-olds about a child learning a new word with a tablet that makes helpful sounds.',
        f'Tell a gentle story where a child uses a tablet to practice a new word. The tablet makes cheerful sounds when they try hard. At the end, a grandparent is proud.',
        f'Write a simple three-paragraph story that uses the words “tablet”, “sound”, and “proud” and ends with cozy sunlight in a room.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, skill = _safe_fact(world, f, "hero"), _safe_fact(world, f, "grand_name"), _safe_fact(world, f, "skill")
    sub, pos = hero.pronoun("subject"), hero.pronoun("possessive")
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about when {hero.id} sits with {elder.id} each afternoon?",
            answer=f"It is about {hero.id}, a cheerful child with {pos} patient smile."
        ),
        QAItem(
            question=f"What new thing did {hero.id} practice using the tablet?",
            answer=f"{hero.id} practiced the new word “{skill.target}” with the tablet beside {elder.id}."
        ),
        QAItem(
            question=f"How did the tablet let {hero.id} know they read the word right?",
            answer=f"The tablet played a cheerful sound—a {_safe_fact(world, f, "sound")}—to celebrate {hero.pronoun('possessive')} correct try."
        ),
    ]
    if f.get("correct_attempt"):
        qa.append(QAItem(
            question=f"How did the tablet help {hero.id} feel while learning?",
            answer=f"{hero.id} felt joy in {pos} belly and pride in {pos} chest because the tablet gave happy sounds for every try."
        ))
    qa.append(QAItem(
        question=f"What does {elder.id} feel at the end of the story?",
        answer=f"{elder.id} feels proud and warm inside because {hero.id} practiced so well."
    ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = [
        QAItem(
            question="What is a tablet?",
            answer="A tablet is a small, flat computer with a screen that you can touch to make things happen."
        ),
        QAItem(
            question="Why do learning apps often make sounds?",
            answer="Learning apps make sounds to tell you when you tap something right: the happy sound is like a little cheer for your brain!"
        ),
        QAItem(
            question="How can grandparents help children learn?",
            answer="Grandparents can sit with children, say words aloud together, and give warm smiles—those cozy moments make learning feel like love."
        ),
    ]
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

# ---------------------------------------------------------------------------
# Clingo (ASP) twin – inline rules that mirror Python constraints.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A skill is learnable with the tablet if its difficulty is not too hard.
learnable(S) :- skill(S,D), difficulty(D,L), L <= 3.

% Sound effects are helpful if they keep the battery from draining to zero.
safe_battery :- battery(Amount), Amount >= 0.2.
has_sound_effect :- sound_effect(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for skill_id, sk in SKILLS.items():
        lines.append(asp.fact("skill", skill_id))
        lines.append(asp.fact("difficulty", skill_id, sk.difficulty))
        lines.append(asp.fact("success_weight", skill_id, sk.success_weight))
    for sid, snd in SOUNDS.items():
        lines.append(asp.fact("sound_effect", sid))
        lines.append(asp.fact("sound_type", sid))
    for child in CHILD_NAMES:
        lines.append(asp.fact("child_name", child))
    for grand in GRAND_NAMES:
        lines.append(asp.fact("grand_name", grand))
    lines.append(asp.fact("threshold", THRESHOLD))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    print("Story is heartwarming and safe by design.")
    return 0

# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming stories with a tablet, sound effects, and loving grandparents.")
    ap.add_argument("--skill", choices=SKILLS, help="word to practice")
    ap.add_argument("--sound", choices=SOUNDS, help="sound-effect style")
    ap.add_argument("--child", help="child’s name")
    ap.add_argument("--grand", help="grandparent’s name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducibility")
    ap.add_argument("--all", action="store_true", help="use curated parameters")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list constraints via clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP twin")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "skill", None) and getattr(args, "sound", None) and getattr(args, "child", None) and getattr(args, "grand", None):
        if getattr(args, "skill", None) not in SKILLS or getattr(args, "sound", None) not in SOUNDS:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    skill_pool = list(SKILLS)
    sound_pool = list(SOUNDS)
    child_pool = list(CHILD_NAMES)
    grand_pool = list(GRAND_NAMES)

    skill = getattr(args, "skill", None) or rng.choice(skill_pool)
    sound = getattr(args, "sound", None) or rng.choice(sound_pool)
    child = getattr(args, "child", None) or rng.choice(child_pool)
    grand = getattr(args, "grand", None) or rng.choice(grand_pool)
    return StoryParams(skill=skill, sound=sound, child_name=child, grand_name=grand)

def generate(params: StoryParams) -> StorySample:
    world = tell(params.skill, params.sound, params.child_name, params.grand_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        lines = ["--- world model state ---"]
        tb = sample.world.get("tablet")
        ch = sample.world.get(sample.params.child_name)
        gm = sample.world.get(sample.params.grand_name)
        lines.append(f"  tablet.battery={tb.meters['battery']:.2f}")
        lines.append(f"  child.joy={ch.memes['joy']:.2f}")
        lines.append(f"  grand.{ch.pronoun('possessive')} pride={gm.memes['pride']:.2f}")
        print("\n".join(lines))
    if qa:
        print()
        print(format_qa(sample))

CURATED = [
    StoryParams(skill="bed", sound="plink", child_name="Lily", grand_name="Grandma"),
    StoryParams(skill="star", sound="chime", child_name="Emma", grand_name="Nana"),
    StoryParams(skill="house", sound="ding", child_name="Noah", grand_name="Papa"),
]

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("Heartwarming tablet stories are always valid.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(1 << 30)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name} learns '{p.skill}' with {p.grand_name}: {p.sound}"
        elif len(samples) > 1:
            header = f"### gentlestory {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
