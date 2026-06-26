#!/usr/bin/env python3
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
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
    place: str
    light: str
    weather: str
    echoes: str
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
    hero: str
    hero_type: str
    companion: str
    companion_type: str
    seed: Optional[int] = None
    params: object | None = None
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
    "garden": Setting(place="the old garden", light="golden", weather="soft", echoes="breezy"),
    "cottage": Setting(place="the cottage yard", light="silver", weather="still", echoes="quiet"),
    "forest": Setting(place="the mossy forest edge", light="green", weather="cool", echoes="whispery"),
}

HEROES = {
    "girl": ["Lina", "Mina", "Elia", "Rosa", "Nora"],
    "boy": ["Theo", "Pip", "Nils", "Arlo", "Finn"],
}

COMPANIONS = {
    "owl": ("owl", "wise owl"),
    "cat": ("cat", "gray cat"),
    "fox": ("fox", "red fox"),
    "grandmother": ("grandmother", "gentle grandmother"),
}

TRAITS = ["curious", "bright-eyed", "soft-hearted", "restless"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class Cabbage:
    id: str
    label: str = "cabbage"
    phrase: str = "a round green cabbage with a secret"
    shell: str = "closed"
    glow: str = "soft"
    sweetness: float = 1.0
    cabbage: object | None = None
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
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_peek(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    cabbage = world.get("cabbage")
    if hero.memes.get("curiosity", 0) < 1:
        return out
    if cabbage.shell != "closed":
        return out
    sig = "peek"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cabbage.shell = "opened"
    cabbage.sweetness -= 0.5
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["regret"] = hero.memes.get("regret", 0) + 1
    out.append("The cabbage split open like a shy moon, and the secret inside began to fade.")
    return out


def _r_bad_ending(world: World) -> list[str]:
    hero = world.get("hero")
    cabbage = world.get("cabbage")
    if cabbage.shell != "opened":
        return []
    sig = "bad_ending"
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["hunger"] = hero.meters.get("hunger", 0) + 1
    hero.memes["sadness"] = hero.memes.get("sadness", 0) + 1
    world.get("companion").memes["worry"] = world.get("companion").memes.get("worry", 0) + 1
    return ["The sweet smell slipped away, and there was no turning the cabbage back again."]


RULES = [Rule("peek", _r_peek), Rule("bad_ending", _r_bad_ending)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def story_intro(world: World, hero: Entity, companion: Entity) -> None:
    world.say(
        f"Once in {world.setting.place}, there lived a little {hero.type} named {hero.id} "
        f"who had a bright and curious heart."
    )
    world.say(
        f"By the garden gate stood {companion.phrase}, who liked to whisper old warnings "
        f"when the wind turned chilly."
    )


def story_setup(world: World, hero: Entity, cabbage: Cabbage) -> None:
    hero.memes["curiosity"] = 1
    hero.memes["hope"] = 1
    world.say(
        f"One morning, {hero.id} found {cabbage.phrase} in the bed of beans, glimmering "
        f"as if it had swallowed a tiny lantern."
    )
    world.say(
        f"{hero.id} loved the strange cabbage at once and wanted to know what secret it kept inside."
    )


def story_warning(world: World, companion: Entity, hero: Entity, cabbage: Cabbage) -> None:
    world.say(
        f'"Do not pry into the cabbage," said {companion.phrase}. "Some doors should stay closed."'
    )
    world.say(
        f"But {hero.id}'s curiosity was bigger than the warning, and {hero.id} leaned closer to look."
    )


def story_turn(world: World, hero: Entity, cabbage: Cabbage) -> None:
    propagate(world, narrate=True)
    if cabbage.shell == "opened":
        world.say(
            f"{hero.id} pulled back a leaf and found only pale, fading sweetness where the magic had been."
        )


def story_end(world: World, hero: Entity, companion: Entity, cabbage: Cabbage) -> None:
    world.para()
    world.say(
        f"By dusk, the cabbage was no longer glowing, and {hero.id} sat quietly with a small ache in {hero.pronoun('possessive')} chest."
    )
    world.say(
        f"{companion.phrase} tucked the ruined leaves into the earth, and the garden became still again."
    )
    world.say(
        f"That was how {hero.id} learned that curiosity can open a thing once, but not always keep the wonder alive."
    )


def make_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    comp_type, comp_phrase = _safe_lookup(COMPANIONS, params.companion_type)
    companion = world.add(Entity(id="companion", kind="character", type=comp_type, label=comp_phrase))
    cabbage = Cabbage(id="cabbage")
    world.facts.update(hero=hero, companion=companion, cabbage=cabbage)
    story_intro(world, hero, companion)
    world.para()
    story_setup(world, hero, cabbage)
    story_warning(world, companion, hero, cabbage)
    story_turn(world, hero, cabbage)
    story_end(world, hero, companion, cabbage)
    world.facts["cabbage"] = cabbage
    return world


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    return [
        f"Write a short fairy tale about {hero.id} and a mysterious cabbage.",
        f"Tell a gentle story where curiosity leads {hero.id} to a bad ending with a cabbage.",
        "Write a child-friendly fairy tale with a warning, a tempting cabbage, and a sad lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    companion = _safe_fact(world, world.facts, "companion")
    cabbage = _safe_fact(world, world.facts, "cabbage")
    return [
        QAItem(
            question=f"Who found the strange cabbage in the garden?",
            answer=f"{hero.id} found the strange cabbage while exploring the garden.",
        ),
        QAItem(
            question=f"What did {companion.label} warn {hero.id} not to do?",
            answer=f"{companion.label} warned {hero.id} not to pry into the cabbage or open its secret leaves.",
        ),
        QAItem(
            question="What happened after the cabbage was opened?",
            answer="Its sweet glow faded, and the story ended sadly because the wonder could not be put back together.",
        ),
        QAItem(
            question="Did the cabbage stay magical at the end?",
            answer="No. By the end, the cabbage had lost its glow and its secret sweetness.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cabbage?",
            answer="A cabbage is a round vegetable with many leafy layers wrapped tightly together.",
        ),
        QAItem(
            question="Why do warnings matter in fairy tales?",
            answer="Warnings matter because they help a character avoid trouble, and ignoring them can lead to a bad ending.",
        ),
    ]


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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    cabbage: Cabbage = _safe_fact(world, world.facts, "cabbage")
    lines.append(f"  cabbage shell={cabbage.shell} sweetness={cabbage.sweetness}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
curious(H) :- hero(H), curiosity(H).
opened(cabbage) :- curious(H), cabbage_present.
bad_ending(H) :- opened(cabbage), hero(H).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("cabbage_present")]
    for h in HEROES:
        lines.append(asp.fact("hero_type", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/1."))
    atoms = sorted(set(asp.atoms(model, "bad_ending")))
    if atoms:
        print("OK: ASP predicts a bad ending.")
        return 0
    print("MISMATCH: ASP did not produce the expected bad ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fairy-tale world about cabbage and curiosity.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-type", choices=list(HEROES))
    ap.add_argument("--hero")
    ap.add_argument("--companion-type", choices=list(COMPANIONS))
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice(_safe_lookup(HEROES, hero_type))
    companion_type = getattr(args, "companion_type", None) or rng.choice(list(COMPANIONS))
    return StoryParams(place=place, hero=hero, hero_type=hero_type, companion=companion_type, companion_type=companion_type, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print(asp_program("#show bad_ending/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show bad_ending/1."))
        print(sorted(set(asp.atoms(model, "bad_ending"))))
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in SETTINGS:
            for hero_type in HEROES:
                for companion_type in COMPANIONS:
                    params = StoryParams(
                        place=place,
                        hero=rng.choice(_safe_lookup(HEROES, hero_type)),
                        hero_type=hero_type,
                        companion=companion_type,
                        companion_type=companion_type,
                        seed=getattr(args, "seed", None),
                    )
                    samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = getattr(args, "seed", None)
            samples.append(generate(params))

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
