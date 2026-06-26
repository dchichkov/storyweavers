#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero-style tale about caution, kindness,
and a crown that learns a lesson about refraction.

Premise:
- A proud child hero wants to wear a shiny crown to a bright parade.
- The crown catches sunlight and splits it into dazzling streaks by refraction.
- The streaks can distract onlookers and make the hero seem showy rather than helpful.
- A cautionary guide warns the hero.
- The hero chooses kindness, uses the crown in a gentler way, and helps others.

This world keeps the classical Storyweavers shape:
- physical meters: shine, worry, danger, calm, kindness, crowd_attention
- emotional memes: pride, caution, gratitude, confidence, concern

The story is small and constraint-driven rather than freeform.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "queen", "princess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "king", "prince"}:
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
    crowd: str
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
class Crown:
    label: str
    phrase: str
    refraction: str
    sparkle: str
    uses: str
    risk: str
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
    place: str
    hero_name: str
    hero_type: str
    guide_name: str
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
    "parade": Setting(place="the parade route", light="bright noon sun", crowd="a small cheering crowd"),
    "square": Setting(place="the town square", light="clear morning light", crowd="families and shopkeepers"),
    "roof": Setting(place="the rooftop garden", light="sparkling afternoon light", crowd="neighbors below"),
}

CROWNS = {
    "ruby": Crown(
        label="crown",
        phrase="a shiny crown with tiny red jewels",
        refraction="scatter rainbow stripes",
        sparkle="bright as a lantern",
        uses="help guide attention toward others",
        risk="flashy and hard to ignore",
    ),
    "glass": Crown(
        label="crown",
        phrase="a clear crown with smooth glass petals",
        refraction="bend the sunlight into little rainbows",
        sparkle="soft and glittering",
        uses="catch light without blinding anyone",
        risk="too dazzling when pointed at the sun",
    ),
}

HERO_NAMES = ["Mina", "Leo", "Aria", "Tao", "Nia", "Ezra", "Ivy", "Rin"]
GUIDE_NAMES = ["Aunt Sol", "Uncle Vale", "Captain Kind", "Ms. Beacon"]


class World:
    def __init__(self, setting: Setting, crown: Crown) -> None:
        self.setting = setting
        self.crown = crown
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in sorted(e.meters.items()) if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in sorted(e.memes.items()) if v)}}}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A crown is risky when bright light makes it refract strongly.
risky_crown(C) :- crown(C), refracts(C).

% Kindness resolves caution if the hero listens, lowers the crown, and helps others.
resolved(H) :- hero(H), cautious(H), kind(H), lowers_crown(H), helps(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("light", sid, s.light))
    for cid, c in CROWNS.items():
        lines.append(asp.fact("crown", cid))
        lines.append(asp.fact("refracts", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def hero_intro(world: World, hero: Entity, guide: Entity) -> None:
    world.say(
        f"{hero.id} was a little superhero who liked to look brave, "
        f"but {guide.id} was the one who noticed danger first."
    )
    world.say(
        f"{hero.id} carried a {world.crown.label} because {world.crown.phrase} made "
        f"{hero.pronoun('possessive')} cape look splendid."
    )


def setting_scene(world: World, hero: Entity) -> None:
    world.para()
    world.say(
        f"One day at {world.setting.place}, the air was full of {world.setting.light} "
        f"and {world.setting.crowd}."
    )
    world.say(
        f"When the sun hit the {world.crown.label}, it began to {world.crown.refraction}."
    )
    hero.meters["shine"] += 1
    hero.meters["crowd_attention"] += 1
    hero.memes["pride"] += 1


def caution_warning(world: World, guide: Entity, hero: Entity) -> None:
    world.say(
        f'{guide.id} raised a hand and said, "Careful. That {world.crown.label} is '
        f'{world.crown.risk}. If you point it at the sun, it may bother the crowd."'
    )
    hero.memes["concern"] += 1
    hero.meters["worry"] += 1
    world.facts["warning"] = True


def hero_choice(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} looked at the bright streaks and remembered that a true hero "
        f"did not need to outshine everyone."
    )
    hero.memes["caution"] += 1
    hero.memes["pride"] = max(0.0, hero.memes.get("pride", 0.0) - 0.5)
    hero.meters["danger"] = max(0.0, hero.meters.get("danger", 0.0) - 0.5)
    world.facts["listened"] = True


def kindness_turn(world: World, guide: Entity, hero: Entity) -> None:
    world.para()
    hero.memes["gratitude"] += 1
    hero.memes["confidence"] += 1
    hero.meters["calm"] += 1
    hero.meters["kindness"] += 1
    hero.meters["crowd_attention"] = max(0.0, hero.meters.get("crowd_attention", 0.0) - 0.5)
    world.say(
        f'{hero.id} lowered the {world.crown.label} and said, "I can still help."'
    )
    world.say(
        f"Then {hero.id} used the shining edges to point the way for a lost child, "
        f"and {guide.id} smiled because the light was helping instead of showing off."
    )
    world.say(
        f"The crowd followed the gentle glow, and the parade became safer and kinder."
    )
    world.facts["kindness"] = True


def ending_image(world: World, hero: Entity) -> None:
    world.say(
        f"By the end, the {world.crown.label} still glittered, but now it meant guidance, "
        f"not bragging, and {hero.id} stood like a real superhero with a soft heart."
    )


def tell_story(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    crown = CROWNS["glass" if params.place != "roof" else "ruby"]
    world = World(setting, crown)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    guide = world.add(Entity(id=params.guide_name, kind="character", type="mentor"))

    hero_intro(world, hero, guide)
    setting_scene(world, hero)
    caution_warning(world, guide, hero)
    hero_choice(world, hero)
    kindness_turn(world, guide, hero)
    ending_image(world, hero)

    world.facts.update(hero=hero, guide=guide, setting=setting, crown=crown)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    guide: Entity = _safe_fact(world, f, "guide")  # type: ignore[assignment]
    crown: Crown = _safe_fact(world, f, "crown")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    return [
        f'Write a short superhero story for a young child about {hero.id}, a crown, and refraction.',
        f"Tell a gentle cautionary story where {guide.id} warns {hero.id} about a crown at {setting.place}.",
        f'Write a story in which kindness helps a superhero use a crown that can {crown.refraction}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    guide: Entity = _safe_fact(world, f, "guide")  # type: ignore[assignment]
    crown: Crown = _safe_fact(world, f, "crown")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {guide.id} warn {hero.id} about the crown?",
            answer=(
                f"{guide.id} warned {hero.id} because the crown was {crown.risk} in the bright "
                f"light at {setting.place}. The light could refract through it and distract the crowd."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} do after listening to the warning?",
            answer=(
                f"{hero.id} lowered the crown, chose caution, and used the light more gently. "
                f"That showed kindness instead of showy pride."
            ),
        ),
        QAItem(
            question=f"How did the crown help in the end?",
            answer=(
                f"In the end, the crown helped guide a lost child because its shining edges could "
                f"{crown.refraction}, so the light became helpful instead of harmful."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is refraction?",
            answer=(
                "Refraction is when light bends as it passes through something like glass or water."
            ),
        ),
        QAItem(
            question="Why can bright shiny things be distracting?",
            answer=(
                "Bright shiny things can catch the eye very quickly, so people may look at them "
                "instead of paying attention to what is safe."
            ),
        ),
        QAItem(
            question="What does kindness mean in a superhero story?",
            answer=(
                "Kindness means using power to help others, not to brag or push people aside."
            ),
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld about a crown and refraction.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--guide-name", choices=GUIDE_NAMES)
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
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    guide_name = getattr(args, "guide_name", None) or rng.choice(GUIDE_NAMES)
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, guide_name=guide_name)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "show_asp", None):
        print(asp_program("#show risky_crown/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        import asp

        model = asp.one_model(asp_program("#show risky_crown/1.\n#show resolved/1."))
        risky = set(asp.atoms(model, "risky_crown"))
        if risky != {("glass",), ("ruby",)}:
            print("ASP verification failed: expected both crowns to be risky in the model.")
            sys.exit(1)
        print("OK: ASP twin parsed and produced the expected crown facts.")
        return
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show risky_crown/1.\n#show resolved/1."))
        print("Risky crowns:", sorted(set(asp.atoms(model, "risky_crown"))))
        print("Resolved:", sorted(set(asp.atoms(model, "resolved"))))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in sorted(SETTINGS):
            params = StoryParams(
                place=place,
                hero_name=_safe_lookup(HERO_NAMES, 0),
                hero_type="girl",
                guide_name=_safe_lookup(GUIDE_NAMES, 0),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
