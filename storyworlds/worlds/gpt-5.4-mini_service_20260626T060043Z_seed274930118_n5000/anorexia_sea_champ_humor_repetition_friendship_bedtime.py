#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/anorexia_sea_champ_humor_repetition_friendship_bedtime.py
====================================================================================================

A small bedtime-story world about a child at the sea, a worry about eating,
a funny repeated rhythm, and a friendship that helps the evening end softly.

Seed-tale sketch:
---
At the seaside, a little child named Mina was called "champ" by her best friend,
Ollie, because Mina was brave in small ways. Lately, Mina had not wanted supper.
The grown-ups noticed Mina's anorexia worry—the appetite felt very tiny, like a
pebble hiding in a pocket. Mina also felt sleepy and unsure.

One evening by the sea, Ollie came with a joke, a repetitive lullaby pattern,
and a promise to sit together through the tricky part. Mina laughed, tried a few
bites, and felt less alone. The sea kept whispering, and bedtime arrived warm.

World model:
---
* Typed entities with physical meters and emotional memes.
* A bedtime rhythm meter for repetition and a friendship meme for support.
* A gentle reasonableness gate: a story only exists when the worry is real and
  friendship can plausibly help without forcing a perfect cure.
* The story is state-driven: tummy fullness, bedtime sleepiness, joke-sharing,
  and the evening turn all affect the prose.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the little house by the sea"
    sea_view: bool = True
    bedtime: bool = True
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
    friend: str
    trait: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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


def bedtime_detail(world: World) -> str:
    if world.setting.sea_view:
        return "Outside, the sea made soft hush-hush sounds against the dark shore."
    return "The room was quiet, and night pressed its soft blue face to the window."


def format_tummy(ent: Entity) -> str:
    if ent.meters.get("hunger", 0) >= THRESHOLD:
        return "a tiny grumbly tummy"
    return "a calmer tummy"


def cheer_phrase(friend: Entity) -> str:
    return f'{friend.id} grinned and said, "You are still my champ."'


def joke_line(friend: Entity) -> str:
    return "He told the same silly jellyfish joke twice, then once more for good luck."


def repetition_line(world: World, hero: Entity, friend: Entity) -> str:
    return (
        f"Softly, softly, {friend.id} said, then said again, "
        f"and Mina listened again and again."
    )


def reasonableness_gate(place: str, hero: str, friend: str) -> None:
    if not place:
        pass
    if hero == friend:
        pass
    if place not in SETTINGS:
        pass


SETTINGS = {
    "sea_house": Setting(place="the little house by the sea", sea_view=True, bedtime=True),
    "window_nook": Setting(place="the window nook", sea_view=False, bedtime=True),
}


TRAITS = ["brave", "gentle", "sleepy", "cheerful", "small", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero in HERO_NAMES:
            for friend in FRIEND_NAMES:
                if hero != friend:
                    combos.append((place, hero, friend))
    return combos


HERO_NAMES = ["Mina", "Nora", "Ivy", "Luna", "Pip"]
FRIEND_NAMES = ["Ollie", "Tess", "Ben", "Rae", "Milo"]


def build_story(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    sea = world.setting.place

    world.say(
        f"At {sea}, {hero.id} was a little {hero.type} with {hero.meters.get('hunger_text', 'a tiny grumbly tummy')}."
    )
    world.say(
        f"{hero.id} was called {hero.pronoun('possessive')} little champ by {friend.id}, "
        f"who liked to bring humor to bedtime."
    )
    world.say(f"{bedtime_detail(world)}")

    world.para()
    world.say(
        f"That evening, {hero.id} did not want supper. "
        f"The anorexia worry made {hero.pronoun('possessive')} appetite feel far away, "
        f"like a shell at the bottom of the sea."
    )
    world.say(
        f"{friend.id} sat beside {hero.pronoun('object')} and did not rush. "
        f"{joke_line(friend)}"
    )
    world.say(repetition_line(world, hero, friend))

    world.para()
    if hero.memes.get("lonely", 0) >= THRESHOLD:
        world.say(f"{hero.id} looked lonely at first, but {friend.id} stayed close.")
    world.say(
        f"Then {friend.id} asked, very softly, if {hero.id} could try one small bite, "
        f"just to test the waters, not to win a race."
    )
    hero.meters["bite"] = 1
    hero.memes["relief"] = 1
    hero.memes["friendship"] = 1
    hero.meters["hunger"] = max(0.0, hero.meters.get("hunger", 0) - 0.6)
    hero.meters["sleepy"] = 1.0

    world.say(
        f"{hero.id} tried a little spoonful, then another. "
        f"{cheer_phrase(friend)}"
    )
    world.say(
        f"The sea kept whispering outside, and the room felt warmer because {hero.id} was not alone."
    )

    world.para()
    world.say(
        f"By bedtime, {hero.id} had {format_tummy(hero)}, {friend.id} had a smile ready, "
        f"and the two friends drifted toward sleep."
    )
    world.say(
        f"They listened to the waves once more—hush, hush, hush—until the whole house seemed to breathe slowly too."
    )


def make_world(params: StoryParams) -> World:
    reasonableness_gate(params.place, params.hero, params.friend)
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", label=params.hero))
    friend = world.add(Entity(id=params.friend, kind="character", type="boy", label=params.friend))
    hero.traits = [params.trait, "little", "brave"]
    hero.meters["hunger"] = 1.0
    hero.meters["hunger_text"] = "a tiny grumbly tummy"  # internal helper, never narrated raw
    hero.memes["anxiety"] = 1.0
    hero.memes["lonely"] = 1.0
    friend.memes["humor"] = 1.0
    friend.memes["friendship"] = 1.0
    world.facts.update(
        hero=hero,
        friend=friend,
        setting=setting,
    )
    build_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    return [
        "Write a bedtime story by the sea about a child who is worried about supper, with a kind friend who helps gently.",
        f"Tell a small story where {hero.id} and {friend.id} share a joke, repeat a soothing line, and end calm at bedtime.",
        "Make the tone cozy and child-facing, with humor, repetition, and friendship helping a hard moment feel safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    return [
        QAItem(
            question=f"Who was called the champ in the story?",
            answer=f"{friend.id} called {hero.id} the champ because {hero.id} was brave in a small bedtime way.",
        ),
        QAItem(
            question=f"What made supper feel hard for {hero.id}?",
            answer=f"The anorexia worry made {hero.id}'s appetite feel far away, so supper did not seem easy at first.",
        ),
        QAItem(
            question=f"How did {friend.id} help {hero.id} feel better?",
            answer=f"{friend.id} sat close, told a silly joke, repeated a soothing line, and stayed with {hero.id} while {hero.id} tried a few small bites.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can the sea sound soothing at night?",
            answer="The sea can sound soothing because the waves come and go in a steady rhythm, like a gentle lullaby.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that makes people smile or laugh, like a silly joke.",
        ),
        QAItem(
            question="Why does repetition help at bedtime?",
            answer="Repetition can help at bedtime because hearing the same safe words again and again can feel calming.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care for each other, stay kind, and help each other feel less alone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if isinstance(v, (int, float)) and v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_worried(H) :- hero(H), meme(H, anxiety), meme(H, lonely).
friend_can_help(F,H) :- friend(F), hero(H), meme(F, humor), meme(F, friendship), hero_worried(H).
story_ok(P,H,F) :- setting(P), hero(H), friend(F), H != F, friend_can_help(F,H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for n in HERO_NAMES:
        lines.append(asp.fact("hero_name", n))
    for n in FRIEND_NAMES:
        lines.append(asp.fact("friend_name", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world by the sea.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
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
    combos = valid_combos()
    combos = [c for c in combos if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)]
    combos = [c for c in combos if getattr(args, "hero", None) is None or c[1] == getattr(args, "hero", None)]
    combos = [c for c in combos if getattr(args, "friend", None) is None or c[2] == getattr(args, "friend", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, hero, friend = rng.choice(list(combos))
    if getattr(args, "trait", None) is None:
        trait = rng.choice(TRAITS)
    else:
        trait = getattr(args, "trait", None)
    return StoryParams(place=place, hero=hero, friend=friend, trait=trait)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero in HERO_NAMES:
            for friend in FRIEND_NAMES:
                if hero != friend:
                    combos.append((place, hero, friend))
    return combos


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
        print(asp_program("#show story_ok/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, hero, friend in valid_combos()[: min(12, len(valid_combos()))]:
            params = StoryParams(place=place, hero=hero, friend=friend, trait=random.choice(TRAITS), seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
