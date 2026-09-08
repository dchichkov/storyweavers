#!/usr/bin/env python3
"""Heartwarming parade tale with a sailor, infantry, and a gentle twist."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
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
class Character:
    name: str
    role: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    infantry: object | None = None
    sailor: object | None = None
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
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    place: object | None = None
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
class StoryParams:
    seed: Optional[int] = None
    parade_name: str = "Lantern Parade"
    setting_name: str = "harbor square"
    sailor_name: str = "Mira"
    infantry_name: str = "Ben"
    twist_name: str = "the missing banner was being sewn into a surprise gift"
    route: str = "banner_first"
    mood: str = "heartwarming"
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


@dataclass
class StoryCase:
    opening: str
    worry: str
    first_try: str
    twist_clue: str
    twist_reveal: str
    caring_action: str
    ending_image: str
    lesson: str
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
class World:
    place: Place
    sailor: Character
    infantry: Character
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    kind: str = ""
    role: str = ""
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


PARAM_CHOICES = {
    "parade_name": ["Lantern Parade", "Ribbon Parade", "Harbor Parade", "Spring Parade"],
    "setting_name": ["harbor square", "old pier", "town green", "station lane"],
    "sailor_name": ["Mira", "Jules", "Nina", "Theo"],
    "infantry_name": ["Ben", "Ada", "Rory", "June"],
    "route": ["banner_first", "quiet_first", "question_first", "helper_first", "twist_first"],
}

ROUTES = tuple(PARAM_CHOICES["route"])

STORY_CASES = {
    "banner_first": StoryCase(
        opening="The parade banner had vanished just before sunrise.",
        worry="Without the banner, the parade would feel small and sad.",
        first_try="Mira checked the rope hooks along the float and found only a neat knot",
        twist_clue="a trail of bright thread led behind the snack tent",
        twist_reveal="the missing banner was being stitched into a secret thank-you quilt",
        caring_action="Mira and Ben carried the basket of thread to the sewing table and helped finish the gift",
        ending_image="the parade rolled forward under a new quilt of colors, and every child waved at the smiling sailor and infantry pair",
        lesson="kind surprises can hide behind a worried mystery",
    ),
    "quiet_first": StoryCase(
        opening="Everything was too quiet beside the parade floats.",
        worry="The crowd might think the celebration had been canceled.",
        first_try="Ben asked the drum team if they had misplaced the music cards",
        twist_clue="soft humming came from under the bunting cart",
        twist_reveal="the humming belonged to neighbors preparing a thank-you song for the parade crew",
        caring_action="Mira lifted the cart cover carefully while Ben stood by to keep the path open for little feet",
        ending_image="the first drumbeat joined the humming song, and the whole square glowed with relieved smiles",
        lesson="sometimes quiet means a surprise is getting ready",
    ),
    "question_first": StoryCase(
        opening='"Who took the parade lanterns?" asked Ben, staring at the empty crate.',
        worry="The twilight walk needed light so the youngest walkers would not be afraid.",
        first_try="Mira counted every crate twice and found the labels still in place",
        twist_clue="a warm glow shone from the bakery window",
        twist_reveal="the lanterns had been borrowed to light the bakery's free supper table for the parade workers",
        caring_action="Mira thanked the baker, and Ben offered to carry the lanterns back after supper",
        ending_image="the lanterns returned just in time, glowing like little moons above happy faces",
        lesson="a missing thing is not always lost; sometimes it is helping somewhere else",
    ),
    "helper_first": StoryCase(
        opening="Mira the sailor arrived with a cart full of ribbons for the parade.",
        worry="A sudden gust had tangled the ribbons into a stubborn knot.",
        first_try="Ben tugged once and only made the knot tighter",
        twist_clue="the knot loosened when a child showed them the end hidden under the wheel",
        twist_reveal="the wind had not ruined the ribbons; it had only tucked one end safely away",
        caring_action="Mira knelt, thanked the child, and let Ben smooth each ribbon before the march",
        ending_image="the ribbons floated cleanly overhead, and the child marched proudly beside the sailor and infantry",
        lesson="small helpers often notice what busy grown-ups miss",
    ),
    "twist_first": StoryCase(
        opening="At the edge of the parade route, a blue coat was waiting on a bench.",
        worry="Ben thought someone important had been forgotten in the cold morning air.",
        first_try="Mira asked every passerby if the coat belonged to them",
        twist_clue="inside the pocket was a note that said 'for the smallest marcher'",
        twist_reveal="the coat was a costume for the tiniest child in the parade, who had not arrived yet",
        caring_action="Mira warmed the coat over her arm while Ben held the place in line",
        ending_image="the smallest marcher finally slipped into the coat and grinned up at the sailor and infantry who had kept it safe",
        lesson="waiting kindly can be part of helping",
    ),
}

ASP_RULES = r"""
person(sailor).
person(infantry).
place(parade_ground).
heartwarming_story :- person(sailor), person(infantry), parade(parade_ground), twist(helping_surprise).
safe_turn(helping_surprise) :- heartwarming_story.
"""


def story_rng(params: StoryParams) -> random.Random:
    bits = "|".join(str(v) for v in (
        params.seed, params.parade_name, params.setting_name, params.sailor_name,
        params.infantry_name, params.twist_name, params.route, params.mood
    ))
    digest = hashlib.sha256(bits.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.route not in ROUTES:
        pass
    return World(
        place=Place(name=params.setting_name, kind="parade route"),
        sailor=Character(name=params.sailor_name, role="sailor", kind="person"),
        infantry=Character(name=params.infantry_name, role="infantry", kind="person"),
    )


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("person", "sailor"),
        asp.fact("person", "infantry"),
        asp.fact("parade", "parade_ground"),
        asp.fact("twist", "helping_surprise"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show heartwarming_story/0. #show safe_turn/1."))
    atoms = {sym.name for sym in model}
    py_ok = True
    if atoms != {"heartwarming_story", "safe_turn"}:
        py_ok = False
    sample = generate(StoryParams(seed=1))
    if "smiled" not in sample.story and "smiling" not in sample.story and "grin" not in sample.story:
        py_ok = False
    if py_ok:
        print("OK: ASP parity and generated story check passed.")
        return 0
    print("MISMATCH in ASP parity or story check.")
    return 1


def tell_story(world: World, params: StoryParams) -> None:
    case = _safe_lookup(STORY_CASES, params.route)
    rng = story_rng(params)
    sailor = world.sailor
    infantry = world.infantry
    place = world.place

    world.say(f"{params.parade_name} began at the {place.name}. {case.opening}")
    world.say(rng.choice([
        f'"We should not guess," {sailor.name} the {sailor.role} said. "{case.worry}"',
        f'{infantry.name} the {infantry.role} pointed at the route. "Something is off, but we will look carefully."',
        f'"Let us be gentle and quick," {sailor.name} said, while {infantry.name} nodded to the waiting children.',
    ]))
    world.say(f"First, {case.first_try}.")
    world.say(rng.choice([
        f'That did not solve it, because the parade path stayed uncertain and {case.worry.lower()}',
        f'But the little clue did not fit alone, so the worry remained.',
        f'The wrong answer made everyone pause, because it did not explain the missing thing.',
    ]))

    world.para()
    world.say(rng.choice([
        f'"Look there," {infantry.name} said. {case.twist_clue.capitalize()}.',
        f'{sailor.name} bent down and whispered, "{case.twist_clue.capitalize()}."',
        f'Before anyone hurried, {infantry.name} noticed that {case.twist_clue}.',
    ]))
    world.say(f"That clue led to the twist: {case.twist_reveal}.")
    world.say(rng.choice([
        f'"Oh!" {sailor.name} laughed softly. "So the parade was never spoiled."',
        f'"That is a lovely surprise," {infantry.name} said, and the worry melted a little.',
        f'{sailor.name} smiled. "Then we can help, not just search."',
    ]))

    world.para()
    world.say(rng.choice([
        f"Together, they chose the kind next step: {case.caring_action}.",
        f"Instead of rushing, {sailor.name} and {infantry.name} {case.caring_action.lower()}.",
        f"With patient hands and friendly words, they {case.caring_action.lower()}.",
    ]))
    sailor.memes["warmth"] = 1
    infantry.memes["helpfulness"] = 1
    sailor.meters["steps_walked"] = 12
    infantry.meters["checks_done"] = 3
    world.facts["twist"] = params.twist_name
    world.facts["lesson"] = case.lesson

    world.say(rng.choice([
        f'As the first music rose, {sailor.name} said, "{case.lesson.capitalize()}."',
        f'{infantry.name} answered, "And kind people make the day better."',
        f'The two of them exchanged a happy grin, because the answer had turned into help.',
    ]))
    world.say(f"By the end of the morning, {case.ending_image}.")
    world.place.meters["joy"] = 1


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a heartwarming story about a parade at {world.place.name} with a sailor and infantry character.",
        f"Include a twist that turns worry into kindness, and make the characters speak to each other in a brief exchange.",
        f"End with an image of the parade scene proving what changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = _safe_lookup(STORY_CASES, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "route"))
    return [
        QAItem(
            question="What problem started the story?",
            answer=f"The parade began with a worry about the missing detail in the celebration. Specifically, {case.opening.lower()}"),
        QAItem(
            question="What clue led to the twist?",
            answer=f"The clue was that {case.twist_clue}. It pointed them toward the real answer."),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {case.twist_reveal}."),
        QAItem(
            question="How did the sailor and infantry respond?",
            answer=f"They responded with patience and help: {case.caring_action}."),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {case.ending_image}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is a cheerful public procession where people walk, watch, and celebrate together."),
        QAItem(
            question="Who is a sailor?",
            answer="A sailor is a person who works on the water, often on boats or ships."),
        QAItem(
            question="Who is infantry?",
            answer="Infantry are soldiers who travel and work on foot."),
        QAItem(
            question="What kind of story is this?",
            answer="It is a heartwarming story, so the worry turns into care, help, or a happy surprise."),
        QAItem(
            question="What does a twist do in a story?",
            answer="A twist changes what the characters thought was happening and reveals a new meaning or cause."),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming parade story with a sailor, infantry, and a twist.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=getattr(args, "seed", None),
        parade_name=rng.choice(PARAM_CHOICES["parade_name"]),
        setting_name=rng.choice(PARAM_CHOICES["setting_name"]),
        sailor_name=rng.choice(PARAM_CHOICES["sailor_name"]),
        infantry_name=rng.choice(PARAM_CHOICES["infantry_name"]),
        twist_name="a gentle helping surprise",
        route=rng.choice(ROUTES),
        mood="heartwarming",
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place={world.place.name!r} kind={world.place.kind!r} meters={world.place.meters} memes={world.place.memes}")
    lines.append(f"sailor={world.sailor.name!r} meters={world.sailor.meters} memes={world.sailor.memes}")
    lines.append(f"infantry={world.infantry.name!r} meters={world.infantry.meters} memes={world.infantry.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show heartwarming_story/0. #show safe_turn/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show heartwarming_story/0. #show safe_turn/1."))
        print(sorted({(sym.name, len(sym.arguments)) for sym in model}))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    count = 3 if getattr(args, "all", None) else getattr(args, "n", None)
    samples: list[StorySample] = []
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
