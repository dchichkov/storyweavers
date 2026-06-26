#!/usr/bin/env python3
"""
A standalone story world for a small ghost-story domain.

Premise:
- A knowledgeable child or caretaker leads a careful march through a dark place.
- Small signs foreshadow that a ghost is nearby.
- The hero's inner monologue builds suspense.
- The ending resolves with a gentle, friendly ghost reveal.

The world is deliberately tiny: one setting, one march, one clue, one lantern,
one ghostly surprise, and one harmless resolution.
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

# ---------------------------------------------------------------------------
# Typed world model
# ---------------------------------------------------------------------------


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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    ghost: object | None = None
    guide: object | None = None
    hero: object | None = None
    lantern: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
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
class Setting:
    place: str = "the old house"
    clue_place: str = "the hall"
    echo_place: str = "the stairs"
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
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    trait: str
    guide_name: str
    guide_type: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "house": Setting(place="the old house", clue_place="the hall", echo_place="the stairs"),
    "museum": Setting(place="the sleepy museum", clue_place="the gallery", echo_place="the long corridor"),
    "school": Setting(place="the empty school", clue_place="the locker hall", echo_place="the stage"),
}

NAMES = {
    "girl": ["Mina", "Ivy", "Nora", "Lena", "Pia"],
    "boy": ["Eli", "Finn", "Noah", "Theo", "Milo"],
}

TRAITS = ["curious", "careful", "knowledgeable", "brave", "thoughtful"]

# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def _ruled_suspense(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    ghost = world.get("ghost")
    lantern = world.get("lantern")
    if hero.memes.get("suspense", 0) < 1:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lantern.meters["light"] = 1
    ghost.meters["near"] = 1
    out.append("A pale shape waited at the edge of the lantern light.")
    return out


def _ruled_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    ghost = world.get("ghost")
    if hero.memes.get("understanding", 0) < 1:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["friendly"] = 1
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1)
    out.append("The spooky hush turned gentle, like a whisper saying hello.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_ruled_suspense, _ruled_calm):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def foreshadow(world: World) -> None:
    world.say(
        "Before anyone saw a ghost, the hallway gave a tiny clue: a cold draft "
        "slipped under the door and made the curtain twitch."
    )
    world.facts["foreshadow"] = True


def inner_monologue(world: World) -> None:
    hero = world.get("hero")
    hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
    world.say(
        f"{hero.id} kept marching forward, thinking, "
        f'"Stay calm. If I listen carefully, I can understand this place."'
    )
    propagate(world, narrate=True)


def march(world: World) -> None:
    hero = world.get("hero")
    guide = world.get("guide")
    hero.meters["steps"] = hero.meters.get("steps", 0) + 3
    guide.meters["steps"] = guide.meters.get("steps", 0) + 3
    world.say(
        f"{hero.id} and {guide.id} began a slow march through {world.setting.place}, "
        f"their shoes making soft taps on the floor."
    )
    world.say(
        f"They passed {world.setting.clue_place}, where the air felt colder than it should."
    )


def reveal(world: World) -> None:
    hero = world.get("hero")
    ghost = world.get("ghost")
    hero.memes["understanding"] = hero.memes.get("understanding", 0) + 1
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1)
    ghost.meters["seen"] = 1
    world.say(
        "At last, the ghost stepped into the light: it was a small, round, smiling ghost "
        "holding the missing bell for the museum door."
    )
    world.say(
        "It had not been trying to frighten anyone at all. It only wanted help finding its way."
    )
    propagate(world, narrate=True)


def resolve(world: World) -> None:
    hero = world.get("hero")
    guide = world.get("guide")
    ghost = world.get("ghost")
    ghost.memes["friendly"] = 1
    world.say(
        f"{hero.id} nodded and lifted the bell back into place, and {guide.id} smiled proudly."
    )
    world.say(
        "The hallway felt warm again. The ghost gave a tiny bow and floated away, "
        "leaving only a soft, moon-white glow behind."
    )
    hero.memes["peace"] = 1
    guide.memes["pride"] = 1


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=[params.trait, "knowledgeable", "careful"],
        meters={"steps": 0},
        memes={"curiosity": 1},
    ))
    guide = world.add(Entity(
        id=params.guide_name,
        kind="character",
        type=params.guide_type,
        traits=["knowledgeable", "steady"],
        meters={"steps": 0},
        memes={"calm": 1},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="ghost",
        meters={"near": 0},
        memes={"mystery": 1},
    ))
    lantern = world.add(Entity(
        id="lantern",
        type="lantern",
        label="lantern",
        phrase="a small lantern",
        owner=hero.id,
        carried_by=hero.id,
        meters={"light": 0},
    ))

    world.facts.update(hero=hero, guide=guide, ghost=ghost, lantern=lantern, setting=setting)

    world.say(
        f"{hero.id} was a {params.trait} {params.hero_type} who knew the old stories of {setting.place}."
    )
    world.say(
        f"{guide.id} was a knowledgeable {params.guide_type} who carried {lantern.phrase} and said they should march slowly."
    )
    world.para()
    foreshadow(world)
    march(world)
    inner_monologue(world)
    world.para()
    world.say(
        f"The shadows deepened near {setting.echo_place}, and {hero.id} heard a soft little clink."
    )
    world.say(
        f"{hero.id} held {hero.pronoun('possessive')} breath and listened."
    )
    reveal(world)
    world.para()
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# QA and prose helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    setting = _safe_fact(world, f, "setting")
    return [
        "Write a gentle ghost story for a young child with foreshadowing, inner monologue, and suspense.",
        f"Tell a story where {hero.id} and {guide.id} march through {setting.place} and discover that the ghost is not scary.",
        "Write a short spooky story that begins with a clue, builds suspense, and ends with kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    setting = _safe_fact(world, f, "setting")
    qa = [
        QAItem(
            question=f"Who marched through {setting.place} with {hero.id}?",
            answer=f"{guide.id} marched with {hero.id}, and {guide.id} helped keep the pace slow and steady.",
        ),
        QAItem(
            question=f"What clue foreshadowed the ghost near {setting.clue_place}?",
            answer="A cold draft slipped under the door and made the curtain twitch, which hinted that something spooky was nearby.",
        ),
        QAItem(
            question=f"What was {hero.id} thinking during the suspenseful part?",
            answer=(
                f"{hero.id} thought, \"Stay calm. If I listen carefully, I can understand this place,\" "
                "which showed brave inner monologue."
            ),
        ),
        QAItem(
            question="What turned out to be true about the ghost?",
            answer="The ghost was friendly and only wanted help finding its missing bell.",
        ),
    ]
    return qa


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is foreshadowing in a story?",
        answer="Foreshadowing is a small clue early in a story that hints at something that will happen later.",
    ),
    QAItem(
        question="What is an inner monologue?",
        answer="An inner monologue is the words a character thinks in their own mind.",
    ),
    QAItem(
        question="What is suspense?",
        answer="Suspense is the feeling of worry or excitement when you do not know what will happen next.",
    ),
    QAItem(
        question="What is a ghost in a story?",
        answer="A ghost is often a spooky-looking character, but in a gentle story it can also be kind and lonely.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(house).
setting(museum).
setting(school).

hero_type(girl).
hero_type(boy).

clue(house, hall).
clue(museum, gallery).
clue(school, locker_hall).

echo(house, stairs).
echo(museum, corridor).
echo(school, stage).

foreshadows(P) :- setting(P).
suspense(P) :- foreshadows(P).
resolve(P) :- setting(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_sets() -> list[tuple[str]]:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    py = sorted((k,) for k in SETTINGS)
    cl = asp_sets()
    if py == cl:
        print(f"OK: ASP matches Python registry ({len(py)} settings).")
        return 0
    print("MISMATCH between ASP and Python registries:")
    print("python:", py)
    print("asp:", cl)
    return 1


# ---------------------------------------------------------------------------
# Required interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with foreshadowing and suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-type", choices=["mother", "father", "teacher", "librarian"])
    ap.add_argument("--trait", choices=TRAITS)
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    guide_type = getattr(args, "guide_type", None) or rng.choice(["mother", "father", "teacher", "librarian"])
    guide_name = getattr(args, "guide_name", None) or rng.choice(["Ms. Vale", "Mr. Reed", "Mrs. Lane", "Aunt June"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        hero_type=gender,
        trait=trait,
        guide_name=guide_name,
        guide_type=guide_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), params)
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
    StoryParams(setting="house", hero_name="Mina", hero_type="girl", trait="knowledgeable", guide_name="Mrs. Lane", guide_type="mother"),
    StoryParams(setting="museum", hero_name="Eli", hero_type="boy", trait="curious", guide_name="Mr. Reed", guide_type="teacher"),
    StoryParams(setting="school", hero_name="Nora", hero_type="girl", trait="thoughtful", guide_name="Aunt June", guide_type="librarian"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show setting/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show setting/1."))
        print(f"{len(SETTINGS)} settings; ASP sees: {sorted(set(asp.atoms(model, 'setting')))}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.hero_name} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
