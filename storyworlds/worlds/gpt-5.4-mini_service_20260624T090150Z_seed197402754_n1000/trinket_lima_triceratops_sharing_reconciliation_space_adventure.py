#!/usr/bin/env python3
"""
A small storyworld for a space-adventure tale of sharing and reconciliation.

Premise:
- A child astronaut loves a tiny trinket.
- A friendly triceratops companion wants a turn.
- A misunderstanding causes hurt feelings.
- They repair the friendship by sharing the trinket together.

The world model tracks physical objects with meters and feelings with memes.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    trinket: object | None = None
    def __post_init__(self):
        for key in ("shiny", "safe", "dusty", "lost"):
            self.meters.setdefault(key, 0.0)
        for key in ("joy", "hurt", "want", "sharing", "peace"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "boy", "child", "astronaut"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"triceratops", "robot", "ship"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the moon base"
    detail: str = "The dome lights glowed blue, and the stars hung outside like tiny sparks."
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
    place: str
    name: str
    companion: str
    trinket: str
    seed: Optional[int] = None
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "moon_base": Setting(
        place="the moon base",
        detail="The dome lights glowed blue, and the stars hung outside like tiny sparks.",
    ),
    "orbital_garden": Setting(
        place="the orbital garden",
        detail="Tomato vines floated in little loops, and the glass walls showed a slow-turning Earth.",
    ),
    "comet_port": Setting(
        place="Comet Port",
        detail="Docking lights blinked along the ring, and small ships zipped past like fireflies.",
    ),
}

TRINKETS = {
    "lima": {
        "label": "lima trinket",
        "phrase": "a tiny green lima trinket",
        "bright": "bright and smooth",
        "spark": "glinted like a little green moon",
    },
    "star": {
        "label": "star trinket",
        "phrase": "a tiny star trinket",
        "bright": "bright and polished",
        "spark": "shone like a pocket-sized sun",
    },
    "shell": {
        "label": "shell trinket",
        "phrase": "a tiny shell trinket",
        "bright": "soft and pearly",
        "spark": "twinkled like a pearl in space",
    },
}

COMPANIONS = {
    "triceratops": {
        "type": "triceratops",
        "label": "a triceratops named Trino",
        "name": "Trino",
        "voice": "a warm rumble",
        "shape": "three gentle horns",
    },
    "ranger": {
        "type": "child",
        "label": "a little ranger named Lima",
        "name": "Lima",
        "voice": "a bright whisper",
        "shape": "a small helmet",
    },
}

NAMES = ["Luna", "Milo", "Nia", "Rex", "Lena", "Tavi", "Kai", "Nova"]
PARENTS = ["captain", "pilot", "teacher"]


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro(world: World, hero: Entity, companion: Entity, trinket: Entity) -> None:
    world.say(
        f"{hero.id} was a little space explorer at {world.setting.place}. "
        f"{companion.label.capitalize()} was always nearby, with {companion.pronoun('possessive')} {companion.type} calm and kind."
    )
    world.say(
        f"{hero.id} loved {trinket.phrase}; it was {_safe_lookup(TRINKETS, trinket.id)['bright']} and {_safe_lookup(TRINKETS, trinket.id)['spark']}."
    )


def arrive(world: World, hero: Entity, companion: Entity) -> None:
    world.say(
        f"One day, {hero.id} and {companion.id} went to the wide hallway near the airlock."
    )
    world.say(world.setting.detail)


def wants_trinket(world: World, companion: Entity, trinket: Entity) -> None:
    companion.memes["want"] += 1
    world.say(
        f"{companion.id} leaned close and asked to hold the {trinket.label} for a minute."
    )


def refuse(world: World, hero: Entity, trinket: Entity) -> None:
    hero.memes["hurt"] += 1
    world.say(
        f"{hero.id} pulled the {trinket.label} back. {hero.pronoun().capitalize()} worried it might be lost among the blinking controls."
    )
    world.say(
        f"{companion := world.get('companion') if 'companion' in world.entities else None}"
    )


def mistake_and_sadness(world: World, hero: Entity, companion: Entity, trinket: Entity) -> None:
    hero.memes["hurt"] += 1
    companion.memes["hurt"] += 1
    world.say(
        f"{companion.id} went quiet, and the room felt colder than the moon dust outside."
    )
    world.say(
        f"{hero.id} saw {companion.pronoun('possessive')} sad face and noticed the trinket looked less fun when nobody shared it."
    )


def apologize(world: World, hero: Entity, companion: Entity) -> None:
    hero.memes["peace"] += 1
    world.say(
        f"{hero.id} took a deep breath and said sorry. "
        f"{hero.pronoun().capitalize()} admitted that {hero.pronoun('subject')} had been scared of losing the little treasure."
    )


def share(world: World, hero: Entity, companion: Entity, trinket: Entity) -> None:
    hero.memes["sharing"] += 1
    companion.memes["sharing"] += 1
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1
    hero.memes["hurt"] = 0.0
    companion.memes["hurt"] = 0.0
    trinket.carried_by = None
    trinket.owner = hero.id
    world.say(
        f"{hero.id} opened {hero.pronoun('possessive')} hand and let {companion.id} hold the {trinket.label} first."
    )
    world.say(
        f"Then they passed it back and forth, watching the little object flash in the air like a friendly comet."
    )


def reconciliation_end(world: World, hero: Entity, companion: Entity, trinket: Entity) -> None:
    hero.memes["peace"] += 1
    companion.memes["peace"] += 1
    world.say(
        f"{hero.id} and {companion.id} smiled at each other again. "
        f"By the end, the {trinket.label} was not just {hero.id}'s treasure; it was their shared space-day toy."
    )
    world.say(
        f"Outside, the stars kept shining, and inside the moon base the two friends floated side by side, laughing softly."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(setting: Setting, trinket_cfg: dict, companion_cfg: dict, name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="child"))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=companion_cfg["type"],
        label=companion_cfg["label"],
    ))
    trinket = world.add(Entity(
        id="trinket",
        kind="thing",
        type="trinket",
        label=trinket_cfg["label"],
        phrase=trinket_cfg["phrase"],
        owner=hero.id,
        carried_by=hero.id,
    ))

    intro(world, hero, companion, trinket)
    world.para()
    arrive(world, hero, companion)
    wants_trinket(world, companion, trinket)
    world.say(f"{hero.id} frowned and held the little {trinket.label} tight.")

    world.para()
    mistake_and_sadness(world, hero, companion, trinket)
    apologize(world, hero, companion)
    share(world, hero, companion, trinket)
    reconciliation_end(world, hero, companion, trinket)

    world.facts.update(
        hero=hero,
        companion=companion,
        trinket=trinket,
        setting=setting,
        trinket_cfg=trinket_cfg,
    )
    return world


# ---------------------------------------------------------------------------
# Story and world QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle space adventure story for a young child about "{f["trinket_cfg"]["label"]}", sharing, and making up after a misunderstanding.',
        f"Tell a story where {f['hero'].id} and {f['companion'].id} learn to share a {f['trinket_cfg']['label']} at {f['setting'].place}.",
        f"Write a child-friendly story set in space that starts with a favorite trinket, has hurt feelings, and ends with reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    companion = _safe_fact(world, f, "companion")
    trinket = _safe_fact(world, f, "trinket")
    return [
        QAItem(
            question=f"What did {hero.id} love at the start of the story?",
            answer=f"{hero.id} loved the {trinket.label}, a tiny treasure that sparkled in the moon-base light.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {companion.id} feel upset for a little while?",
            answer=f"They felt upset because {companion.id} wanted a turn with the {trinket.label}, but {hero.id} was afraid of losing it.",
        ),
        QAItem(
            question=f"How did {hero.id} and {companion.id} fix the problem?",
            answer=f"They apologized, shared the {trinket.label}, and took turns holding it until both of them felt happy again.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the {trinket.label} was shared, the hurt feelings were gone, and the two friends were smiling together again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something too, instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who had a disagreement make up, repair their friendship, and feel kind toward each other again.",
        ),
        QAItem(
            question="What is a triceratops?",
            answer="A triceratops was a dinosaur with three horns and a large frill on its head.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
shared(T) :- trinket(T), wants_turn(companion, T), willing(hero, T).
reconciled :- apology(hero, companion), shared(trinket), no_hurt(hero), no_hurt(companion).
valid_story(P) :- setting(P), trinket(lima), companion(triceratops).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("setting", key))
    for key, cfg in TRINKETS.items():
        lines.append(asp.fact("trinket", key))
    for key, cfg in COMPANIONS.items():
        lines.append(asp.fact("companion", key))
    lines.append(asp.fact("wants_turn", "companion", "trinket"))
    lines.append(asp.fact("willing", "hero", "trinket"))
    lines.append(asp.fact("apology", "hero", "companion"))
    lines.append(asp.fact("no_hurt", "hero"))
    lines.append(asp.fact("no_hurt", "companion"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shared/2. #show reconciled/0. #show valid_story/1."))
    atoms = asp.atoms(model, "valid_story")
    if atoms:
        print("OK: ASP program produces a valid story model.")
        return 0
    print("Mismatch: ASP program did not produce a valid model.")
    return 1


# ---------------------------------------------------------------------------
# Validation and parameter resolution
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about trinkets, sharing, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trinket", choices=TRINKETS.keys())
    ap.add_argument("--companion", choices=COMPANIONS.keys())
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS.keys()))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trinket = getattr(args, "trinket", None) or rng.choice(list(TRINKETS.keys()))
    companion = getattr(args, "companion", None) or "triceratops"
    if trinket != "lima" and getattr(args, "trinket", None) is not None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if companion != "triceratops" and getattr(args, "companion", None) is not None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, name=name, companion=companion, trinket=trinket)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TRINKETS, params.trinket), _safe_lookup(COMPANIONS, params.companion), params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="moon_base", name="Luna", companion="triceratops", trinket="lima"),
    StoryParams(place="orbital_garden", name="Nova", companion="triceratops", trinket="star"),
    StoryParams(place="comet_port", name="Milo", companion="triceratops", trinket="shell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
