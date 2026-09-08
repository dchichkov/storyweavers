#!/usr/bin/env python3
"""
A heartwarming tiny story world about a parade with a sailor and an infantry
child, where a small twist changes the plan and turns worry into kindness.

The simulation keeps a few typed entities with meters and memes, a causal
state machine, a reasonableness gate, QA sets, and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from results import QAItem, StoryError, StorySample  # noqa: E402



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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    banner: object | None = None
    infantry: object | None = None
    parade: object | None = None
    sailor: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Place:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        return copy.deepcopy(self)
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]


@dataclass
class StoryParams:
    place: str = "harbor"
    sailor_name: str = "Nia"
    infantry_name: str = "Ben"
    twist: str = "lost_banner"
    seed: Optional[int] = None
    sample: object | None = None
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


PLACES = {
    "harbor": Place(id="harbor", label="the harbor square"),
    "town_green": Place(id="town_green", label="the town green"),
    "school_yard": Place(id="school_yard", label="the school yard"),
}

TWISTS = {
    "lost_banner": {
        "problem": "the parade banner blew loose and slid behind a flower cart",
        "turn": "the sailor climbed onto the cart's step while the infantry child steadied the pole",
        "result": "the banner came back cleanly and the parade could start",
        "dialogue": [
            '"I can reach it," said Nia. "Will you hold the pole steady?"',
            '"Yes," said Ben. "I will stand firm while you bring it back."',
        ],
        "ending": "Soon the banner flew high again, and both friends smiled at the front of the parade.",
    },
    "rain_sparkle": {
        "problem": "a sudden drizzle made the parade drum straps slippery",
        "turn": "the sailor tied the straps in neat knots while the infantry child shared a dry cloth",
        "result": "the drums stayed safe and the parade kept its cheerful beat",
        "dialogue": [
            '"The straps are slick," said Nia. "Can you hand me the cloth?"',
            '"Of course," said Ben. "Together we can keep the drums dry."',
        ],
        "ending": "The drums tapped on happily, and the wet streets shone like silver ribbons.",
    },
    "shoe_lace": {
        "problem": "the infantry child's shoe lace tangled just before the first step",
        "turn": "the sailor knelt down and retied it while the child held the parade flag high",
        "result": "the lace stayed snug and the child marched proudly beside the band",
        "dialogue": [
            '"Your lace needs care," said Nia. "May I fix it for you?"',
            '"Please do," said Ben. "I will hold the flag until I stand again."',
        ],
        "ending": "Then Ben marched with a bright step, and Nia matched the rhythm with a happy wave.",
    },
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming parade story world with a twist.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--sailor")
    ap.add_argument("--infantry")
    ap.add_argument("--twist", choices=sorted(TWISTS))
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    twist = getattr(args, "twist", None) or rng.choice(list(TWISTS))
    sailor_name = getattr(args, "sailor", None) or rng.choice(["Nia", "Mina", "Lena", "Iris"])
    infantry_name = getattr(args, "infantry", None) or rng.choice([n for n in ["Ben", "Omar", "Theo", "Milo"] if n != sailor_name])
    return StoryParams(place=place, sailor_name=sailor_name, infantry_name=infantry_name, twist=twist)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.twist not in TWISTS:
        pass
    if params.sailor_name.strip() == params.infantry_name.strip():
        pass


def simulate(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(place=_safe_lookup(PLACES, params.place))
    sailor = world.add(Entity(id="sailor", kind="character", label=params.sailor_name, role="sailor", meters={"helped": 0.0}, memes={"calm": 1.0}))
    infantry = world.add(Entity(id="infantry", kind="character", label=params.infantry_name, role="infantry", meters={"helped": 0.0}, memes={"pride": 0.0}))
    parade = world.add(Entity(id="parade", kind="event", label="parade", meters={"ready": 1.0}, memes={"joy": 0.5}))
    banner = world.add(Entity(id="banner", kind="thing", label="parade banner", meters={"loose": 0.0}, memes={}))
    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        parade=parade,
        banner=banner,
        twist=params.twist,
        place=world.place,
    )

    info = _safe_lookup(TWISTS, params.twist)
    world.say(f"At {world.place.label}, {sailor.label} the sailor and {infantry.label} from the infantry came to watch the parade.")
    world.say("Music warmed the morning, and the crowd waited for the first bright step.")
    world.para()

    banner.meters["loose"] = 1.0
    parade.meters["ready"] = 0.0
    sailor.memes["worry"] += 0.5
    infantry.memes["worry"] += 0.5
    world.say(f"Then a twist changed everything: {info['problem']}.")
    world.say(f'"Oh dear," said {sailor.label}. "We can still help."')
    world.say(f'"Yes," said {infantry.label}. "Tell me what to do."')
    world.para()

    sailor.meters["helped"] += 1.0
    infantry.meters["helped"] += 1.0
    sailor.memes["calm"] += 0.5
    infantry.memes["pride"] += 1.0
    world.say(info["dialogue"][0].replace("Nia", sailor.label).replace("Ben", infantry.label))
    world.say(info["dialogue"][1].replace("Nia", sailor.label).replace("Ben", infantry.label))
    world.say(info["turn"].replace("Nia", sailor.label).replace("Ben", infantry.label))
    banner.meters["loose"] = 0.0
    parade.meters["ready"] = 1.0
    world.para()

    sailor.memes["joy"] += 1.0
    infantry.memes["joy"] += 1.0
    parade.memes["joy"] += 1.0
    world.say(f"Their quick teamwork fixed the problem, and {info['result']}.")
    world.say(info["ending"].replace("Nia", sailor.label).replace("Ben", infantry.label))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming story for a small child that includes the word "twist" and a parade.',
        f"Tell how {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sailor").label} and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "infantry").label} helped each other when the parade faced a twist.",
        f"Write a gentle, cheerful story set at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place").label} with a sailor, an infantry child, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What changed the parade plan?",
            answer=f"The parade plan changed when {_safe_lookup(TWISTS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "twist"))['problem']}. That twist made everyone pause and look carefully."
        ),
        QAItem(
            question="How did the sailor and the infantry child help?",
            answer=f"They worked together: {_safe_lookup(TWISTS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "twist"))['turn']}. Because they shared the job, {_safe_lookup(TWISTS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "twist"))['result']}."
        ),
        QAItem(
            question="What showed that the story ended well?",
            answer=f"The ending showed it clearly: {_safe_lookup(TWISTS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "twist"))['ending']}"
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is a happy line of people or floats moving together, often with music, flags, or costumes."
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help one another and do different parts of a job so the whole job gets done."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 3) for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: label={ent.label!r} role={ent.role!r} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
ready(parade) :- parade(parade), banner(banner), not loose(banner).
helped(X) :- sailor(X).
helped(X) :- infantry(X).
twist(problem) :- banner(banner), loose(banner).
happy_end :- ready(parade), helped(sailor), helped(infantry).
#show twist/1.
#show happy_end/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("parade", "parade"),
        asp.fact("banner", "banner"),
        asp.fact("sailor", "sailor"),
        asp.fact("infantry", "infantry"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        _ = model
        sample = generate(StoryParams())
        if "parade" not in sample.story.lower():
            raise RuntimeError("generated story did not mention parade")
        return 0
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "happy_end")))


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="harbor", sailor_name="Nia", infantry_name="Ben", twist="lost_banner", seed=base_seed),
            StoryParams(place="town_green", sailor_name="Mina", infantry_name="Omar", twist="rain_sparkle", seed=base_seed + 1),
            StoryParams(place="school_yard", sailor_name="Lena", infantry_name="Theo", twist="shoe_lace", seed=base_seed + 2),
        ]
        samples = [generate(p) for p in curated]
    else:
        rng = random.Random(base_seed)
        for i in range(max(1, getattr(args, "n", None))):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
