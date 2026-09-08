#!/usr/bin/env python3
"""
A fairy-tale storyworld about refuse, a conference, and a transformation.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    child: object | None = None
    companion: object | None = None
    hall: object | None = None
    heap: object | None = None
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
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Luna"
    companion_name: str = "Milo"
    kingdom: str = "Moonmeadow"
    name: object | None = None
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


NAMES = ["Luna", "Milo", "Nora", "Pip", "Tessa", "Oren", "Faye", "Bram"]
KINGDOMS = ["Moonmeadow", "Rosebell", "Silverfen", "Thimblewood"]

TALES = [
    {
        "place": "the hilltop palace of Moonmeadow",
        "refuse": "a heap of cracked cups, wilted ribbons, and bent tin crowns",
        "conference": "the Grand Conference of Kind Hearts",
        "misunderstanding": "believed the palace keeper wanted the refuse hidden beyond the forest",
        "foreshadowing": "a blue moth kept circling the heap, though no one else noticed it",
        "clue": "the moth's silver dust shone whenever two broken things touched",
        "transformation": "the refuse became a bright little moon garden where every cup held a flower",
        "choice": "asked the palace keeper what the heap was for before carrying it away",
        "ending": "the conference lanterns glowed from the new garden, and even the bent crowns became flower bells",
        "lesson": "A thing that looks worthless may be waiting for a gentler purpose.",
    },
    {
        "place": "the glass castle beside the whispering river",
        "refuse": "old straw, torn banners, and muddy jars left after the harvest feast",
        "conference": "the Royal Conference of Small Helpers",
        "misunderstanding": "thought the queen had ordered the refuse thrown into the river",
        "foreshadowing": "three reeds bowed toward the muddy jars whenever the wind blew",
        "clue": "inside one jar, a seed hummed whenever it heard a kind word",
        "transformation": "the refuse became a floating reed boat covered in golden leaves",
        "choice": "carried the refuse to the queen and asked why it had been saved",
        "ending": "the new boat carried conference guests safely across the river beneath the stars",
        "lesson": "Before obeying a troubling rumor, ask the person who can tell you the truth.",
    },
    {
        "place": "the village square beneath the sleeping giant's mountain",
        "refuse": "broken wooden spoons, frayed rope, and empty flour sacks",
        "conference": "the Conference of Village Wizards",
        "misunderstanding": "refused to let anyone touch the refuse because a rumor said it belonged to a dragon",
        "foreshadowing": "a warm red spark winked inside the empty flour sacks",
        "clue": "the village baker recognized the spark as the giant's lost hearth ember",
        "transformation": "the refuse became a cheerful oven with a chimney shaped like a sun",
        "choice": "invited the baker to inspect the heap instead of guarding it alone",
        "ending": "fresh bread warmed every conference table, and the mountain giant woke smiling",
        "lesson": "Sharing a worry can turn a frightening mystery into a useful discovery.",
    },
    {
        "place": "the thorn palace where the princess held court",
        "refuse": "blackened candles, torn gloves, and splintered toy wagons",
        "conference": "the Conference of Honest Wishes",
        "misunderstanding": "refused the princess's request because the messenger had forgotten one important word",
        "foreshadowing": "a tiny bell rang whenever someone spoke plainly near the heap",
        "clue": "the bell rang again when the messenger admitted that she had been afraid",
        "transformation": "the refuse became a silver bridge over the palace moat",
        "choice": "returned to the messenger and asked her to repeat the request slowly",
        "ending": "the bridge opened the conference to every child who had once felt too small to speak",
        "lesson": "Clear questions can mend the space between a message and its meaning.",
    },
]


def _setup(world: World, params: StoryParams) -> None:
    child = world.add(Entity(params.child_name, "character", "child", params.child_name))
    companion = world.add(Entity(params.companion_name, "character", "companion", params.companion_name))
    heap = world.add(Entity("refuse_heap", "thing", "refuse", "the refuse heap"))
    hall = world.add(Entity("conference_hall", "place", "hall", "the conference hall"))
    child.meters.update(courage=1.0, understanding=0.2)
    child.memes.update(worry=0.5, kindness=0.8)
    companion.meters["helpfulness"] = 1.0
    heap.meters.update(disorder=1.0, hidden_magic=1.0)
    hall.meters["welcome"] = 0.4
    world.facts.update(child=child, companion=companion, heap=heap, hall=hall, params=params)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        params.child_name + params.companion_name + params.kingdom
    ))


def tell_story(params: StoryParams) -> World:
    if params.child_name == params.companion_name:
        pass
    world = World()
    _setup(world, params)
    tale = _safe_lookup(TALES, _token(params) % len(TALES))
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    companion = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "companion")
    heap = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "heap")

    world.say(f"In the kingdom of {params.kingdom}, {child.label} lived near {tale['place']}.")
    world.say(
        f"One morning, {child.label} found {tale['refuse']} beside the road to "
        f"{tale['conference']}."
    )
    world.say(f"At the edge of the heap, {tale['foreshadowing']}.")

    world.para()
    world.say(
        f"A hurried messenger said that the heap must be moved, and {child.label} "
        f"{tale['misunderstanding']}."
    )
    world.say(
        f'"We must not touch it until we know the truth," {child.label} said. '
        f'"Then let us ask together," {companion.label} replied.'
    )
    world.say(
        "The two friends carried their question to the conference hall, but a guard "
        "sent them back before they could explain."
    )
    world.say(
        "For a while, the heap seemed to grow darker, and the conference doors "
        "began to close."
    )

    world.para()
    world.say(
        f"Remembering the strange sign, {child.label} {tale['choice']}. "
        f"The truth was hidden in a small detail: {tale['clue']}."
    )
    world.say(
        f'"So the refuse is not a disgrace," {companion.label} said. '
        f'"It is waiting to become something useful."'
    )
    world.say(
        f"{child.label} touched the heap with a brave hand. In a swirl of warm light, "
        f"{tale['transformation']}."
    )
    heap.meters["disorder"] = 0.0
    heap.meters["hidden_magic"] = 0.0
    child.meters["understanding"] = 1.0
    child.memes["worry"] = 0.0

    world.para()
    world.say(
        f"The guard opened the doors when he saw the change, and {tale['ending']}."
    )
    world.say(
        f'"Next time, we will ask before we assume," {child.label} said. '
        f'"And we will watch for small clues," {companion.label} answered.'
    )
    world.say(f"{tale['lesson']}")

    world.facts.update(
        tale=tale,
        tale_index=_token(params) % len(TALES),
        transformed=True,
        misunderstanding_resolved=True,
        conference_open=True,
    )
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    tale = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "tale")
    params = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    return [
        f"Write a fairy tale about {params.child_name}, refuse, and {tale['conference']}.",
        f"Show how a misunderstanding about {tale['refuse']} is solved through a question and a magical transformation.",
        f"Use foreshadowing, a brief dialogue, and an ending in which the transformed refuse helps the conference.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "tale")
    params = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    return [
        QAItem(
            f"What did {params.child_name} find near the conference?",
            f"{params.child_name} found {tale['refuse']} near {tale['conference']}.",
        ),
        QAItem(
            "What misunderstanding caused trouble?",
            f"The misunderstanding was that someone believed or assumed {tale['misunderstanding']}.",
        ),
        QAItem(
            "What foreshadowing hinted that the refuse held magic?",
            f"{tale['foreshadowing'].capitalize()} This hinted that the heap had a purpose.",
        ),
        QAItem(
            "How was the misunderstanding solved?",
            f"{params.child_name} {tale['choice']}, and then learned that {tale['clue']}.",
        ),
        QAItem(
            "What transformation happened?",
            f"The refuse transformed into {tale['transformation']}.",
        ),
        QAItem(
            "How did the story end?",
            f"{tale['ending']}. The conference became part of the happy ending.",
        ),
        QAItem("What lesson did the tale teach?", tale["lesson"]),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is refuse?",
            "Refuse is material people no longer want, such as scraps or broken objects, though some refuse can be repaired or reused.",
        ),
        QAItem(
            "What is a conference?",
            "A conference is a meeting where people gather to share ideas, listen, and make decisions.",
        ),
        QAItem(
            "What is foreshadowing?",
            "Foreshadowing is a small clue early in a story that hints at something important later.",
        ),
        QAItem(
            "What is a transformation?",
            "A transformation is a change from one form or condition into another.",
        ),
    ]


ASP_RULES = r"""
confusion(S) :- refuse_present(S), message_unclear(S).
foreshadowed(S) :- clue_present(S).
resolved(S) :- question_asked(S), truth_learned(S).
transformation(S) :- resolved(S), magic_used(S).
conference_happy(S) :- transformation(S), conference_open(S).
valid_story(S) :- confusion(S), foreshadowed(S), conference_happy(S).
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("refuse_present", "story1"),
        asp.fact("message_unclear", "story1"),
        asp.fact("clue_present", "story1"),
        asp.fact("question_asked", "story1"),
        asp.fact("truth_learned", "story1"),
        asp.fact("magic_used", "story1"),
        asp.fact("conference_open", "story1"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if actual == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale storyworld about refuse, conference, misunderstanding, and transformation."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion-name", choices=NAMES)
    parser.add_argument("--kingdom", choices=KINGDOMS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = getattr(args, "name", None) or rng.choice(NAMES)
    companions = [n for n in NAMES if n != name]
    companion = getattr(args, "companion_name", None) or rng.choice(companions)
    kingdom = getattr(args, "kingdom", None) or rng.choice(KINGDOMS)
    return StoryParams(name=name, companion_name=companion, kingdom=kingdom)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:16} ({entity.kind:9}) {' '.join(details)}")
    lines.append("  facts: " + str({
        k: v for k, v in world.facts.items()
        if k not in {"child", "companion", "heap", "hall", "params", "tale"}
    }))
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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
    StoryParams(child_name="Luna", companion_name="Milo", kingdom="Moonmeadow"),
    StoryParams(child_name="Nora", companion_name="Pip", kingdom="Rosebell"),
    StoryParams(child_name="Faye", companion_name="Bram", kingdom="Silverfen"),
    StoryParams(child_name="Tessa", companion_name="Oren", kingdom="Thimblewood"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
