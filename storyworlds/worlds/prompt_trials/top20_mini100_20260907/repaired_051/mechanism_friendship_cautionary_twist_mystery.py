#!/usr/bin/env python3
"""
A small mystery storyworld about a mechanism, friendship, a cautionary twist,
and a careful clue trail.

The world is built around a child-facing mystery: friends discover that a
useful mechanism is not working as expected, investigate the cause, make one
careful mistake, and then solve the problem through observation, trust, and a
twist that changes what they thought they knew.

Physical state is tracked with meters and emotional state with memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


SETTINGS = [
    "the old clock room",
    "the garden shed",
    "the small museum hall",
    "the riverside boathouse",
    "the attic with the round window",
]

NAMES = [
    "Mina",
    "Toby",
    "Rae",
    "Pip",
    "Lila",
    "Noah",
    "June",
    "Cleo",
]

KINDS = [
    "rabbit",
    "fox",
    "mouse",
    "duck",
    "cat",
    "bear",
    "goat",
    "badger",
]

MECHANISMS = [
    "a tiny wind-up gate",
    "a bell pull mechanism",
    "a pop-up drawer latch",
    "a rotating lantern arm",
    "a toy lift mechanism",
    "a music box crank",
]



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
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {
        "distance": 0.0,
        "weight": 0.0,
        "completeness": 0.0,
        "shine": 0.0,
        "safety": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "worry": 0.0,
        "trust": 0.0,
        "curiosity": 0.0,
        "courage": 0.0,
        "relief": 0.0,
    })

    friend: object | None = None
    hero: object | None = None
    keeper: object | None = None
    mechanism: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "she", "cat", "rabbit", "duck"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "he", "fox", "bear", "goat", "mouse", "badger"}:
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
class Setting:
    place: str
    world: object | None = None
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
    setting: str = ""
    hero_name: str = ""
    hero_type: str = ""
    friend_name: str = ""
    friend_type: str = ""
    keeper_name: str = ""
    mechanism: str = ""
    scenario_index: int = 0
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace_log: list[str] = []

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SCENARIOS = [
    {
        "mystery": "Something in the room kept clicking by itself, even when no one touched it.",
        "mistake": "They pulled the handle too hard, and the latch snapped shut with a loud clack.",
        "clue": "A thin ribbon of paint dust lay under the left gear, showing that the gear was rubbing against the side wall.",
        "twist": "The noisy trouble was not a broken part at all; a loose ribbon had been brushing the mechanism each time the wind came in.",
        "fix": "The friends tied the ribbon back, cleaned the dust away, and turned the gear slowly until it moved freely.",
        "ending": "After that, the mechanism worked with a soft, happy click.",
        "lesson": "a careful look can solve a mystery faster than a quick tug",
        "dialogue": "Let's look before we pull",
        "final_image": "the small gear turned like a silver moon and the room grew calm",
    },
    {
        "mystery": "The mechanism in the corner was supposed to open a little panel, but it only shook.",
        "mistake": "They guessed the string had come loose and tied it tighter, which only made the shaking worse.",
        "clue": "A pebble sat in the track, hidden where the sliding piece needed to pass.",
        "twist": "The string was not the problem; a curious sparrow had dropped the pebble there and then flown away.",
        "fix": "The friends lifted the pebble out with a spoon and tested the slide again.",
        "ending": "This time the panel opened at once, as neat as a secret door.",
        "lesson": "not every mystery begins with a broken string",
        "dialogue": "That pebble has been the real trick all along",
        "final_image": "the panel slid open and revealed a bright little drawer",
    },
    {
        "mystery": "A music box mechanism should have played three notes, but it stopped after one.",
        "mistake": "They wound it again and again, which only made the spring groan.",
        "clue": "A tiny crumb of wax had stuck to the wheel, and the wheel was skipping over it.",
        "twist": "The mechanism was not tired; it was trying to protect a hidden paper note tucked under the lid.",
        "fix": "The friends removed the wax, lifted the note out, and let the wheel turn freely.",
        "ending": "Then the music box sang its three notes, and the paper note read, Thank you for being careful.",
        "lesson": "some puzzles hide a kind message instead of danger",
        "dialogue": "It was trying to tell us something kind",
        "final_image": "the music note card rested beside the box like a white feather",
    },
    {
        "mystery": "The lantern arm at the museum kept dipping low, making the lamp sway.",
        "mistake": "They thought the arm needed more weight, so they added a stone and nearly made it tip.",
        "clue": "The balance mark on the board showed that one side had been set too far to the left.",
        "twist": "The keeper had moved the display for cleaning and forgotten to reset the balance mark.",
        "fix": "The friends slid the arm back to the mark and removed the extra stone.",
        "ending": "The lamp stood still at last, bright and steady above the exhibit.",
        "lesson": "a helpful change can become a problem if nobody checks it",
        "dialogue": "We should trust the mark, not just the wobble",
        "final_image": "the steady lamp shone over the glass case like a small sun",
    },
    {
        "mystery": "The toy lift mechanism carried boxes up and down, but one box stayed stuck halfway.",
        "mistake": "They tugged the rope from below, which only jammed the wheels harder.",
        "clue": "A strip of sticky jam had dried on the pulley wheel, shining in the light.",
        "twist": "The jam came from the friendly keeper's lunch basket, so the mystery was an accident rather than a trick.",
        "fix": "The friends cleaned the wheel with a damp cloth and moved the box by guiding it gently.",
        "ending": "Soon the lift rose and lowered every box without a hitch.",
        "lesson": "even an accident deserves a calm answer",
        "dialogue": "No blame first—let's find the sticky part",
        "final_image": "the clean wheel spun like a little brown star",
    },
    {
        "mystery": "The bell pull mechanism should have rung the dinner bell, but the rope went slack.",
        "mistake": "They climbed too fast and bumped the bell, making it ring once in the wrong pattern.",
        "clue": "A small knot in the rope had caught under the pulley.",
        "twist": "The knot had been tied there by the keeper's kitten, who wanted to stop the bell from startling a sleeping baby.",
        "fix": "The friends untied the knot and then rang the bell softly themselves.",
        "ending": "The dinner bell sounded kindly instead of loudly, and everyone came in smiling.",
        "lesson": "a mystery can have a gentle reason",
        "dialogue": "The kitten was trying to be thoughtful",
        "final_image": "the bell hung still while the warm dinner steam curled upward",
    },
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about a mechanism and a careful friendship.")
    ap.add_argument("--setting")
    ap.add_argument("--name")
    ap.add_argument("--type")
    ap.add_argument("--friend")
    ap.add_argument("--friend-type")
    ap.add_argument("--keeper")
    ap.add_argument("--mechanism")
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
    setting = getattr(args, "setting", None) or rng.choice(SETTINGS)
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    hero_type = getattr(args, "type", None) or rng.choice(KINDS)
    friend_name = getattr(args, "friend", None) or rng.choice([n for n in NAMES if n != hero_name])
    friend_type = getattr(args, "friend_type", None) or rng.choice([k for k in KINDS if k != hero_type])
    keeper_name = getattr(args, "keeper", None) or rng.choice(["Mr. Bell", "Mrs. Vale", "Aunt Rowe", "Keeper Finch"])
    mechanism = getattr(args, "mechanism", None) or rng.choice(MECHANISMS)
    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        keeper_name=keeper_name,
        mechanism=mechanism,
        scenario_index=rng.randrange(len(SCENARIOS)),
        seed=None,
    )


def tell(params: StoryParams) -> World:
    if not params.setting:
        pass
    if not params.mechanism:
        pass
    scen = _safe_lookup(SCENARIOS, params.scenario_index % len(SCENARIOS))
    world = World(Setting(place=params.setting))

    hero = world.add(Entity(id="hero", kind="animal", type=params.hero_type, label=params.name or params.hero_name))
    friend = world.add(Entity(id="friend", kind="animal", type=params.friend_type, label=params.friend_name))
    keeper = world.add(Entity(id="keeper", kind="animal", type="cat", label=params.keeper_name))
    mechanism = world.add(Entity(id="mechanism", kind="thing", type="thing", label=params.mechanism, phrase=f"the {params.mechanism}"))

    world.facts.update(hero=hero, friend=friend, keeper=keeper, mechanism=mechanism, scen=scen)

    hero.memes["curiosity"] += 1
    friend.memes["trust"] += 1

    world.say(f"On a quiet afternoon at {world.setting.place}, {hero.label} and {friend.label} found {mechanism.phrase}.")
    world.say(f'{keeper.label} frowned. "{scen["mystery"]}"')
    world.say(f'{hero.label} said, "{scen["dialogue"]} Let us be careful and look for clues."')
    world.para()

    world.say(f"At first, they made a mistake. {scen['mistake']}")
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(f'{friend.label} whispered, "Maybe we should stop pulling and check the path the part uses."')
    world.say(f'Then {hero.label} noticed the clue: {scen["clue"]}')
    world.para()

    mechanism.meters["safety"] = 0.4
    mechanism.memes["worry"] += 0.5
    world.say(f"The friends followed the clue, and the mystery turned. {scen['twist']}")
    world.say(f'{keeper.label} blinked and said, "So it was not a mean trick at all?"')
    world.say(f'{friend.label} shook their head. "No. We only needed to fix the small thing that was in the way."')
    world.para()

    mechanism.meters["safety"] = 1.0
    mechanism.meters["completeness"] = 1.0
    hero.memes["courage"] += 1
    friend.memes["courage"] += 1
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    keeper.memes["relief"] += 1
    world.say(scen["fix"])
    world.say(scen["ending"])
    world.say(f"{hero.label} smiled at {friend.label}. \"{scen['lesson']}.\"")
    world.say(f"At the end, {scen['final_image']}.")
    world.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    keeper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "keeper")
    mechanism: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mechanism")
    scen: dict[str, str] = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "scen")
    return [
        f"Write a child-friendly mystery story about {hero.label} and {friend.label} investigating {mechanism.phrase} at {world.setting.place}.",
        f"Tell a story where {keeper.label} shares a mystery, the friends make one mistake, and a twist changes what they think is wrong.",
        f'Use the words "{mechanism.label}" and "mechanism" in a gentle mystery with friendship and a careful ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    keeper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "keeper")
    mechanism: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mechanism")
    scen: dict[str, str] = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "scen")
    return [
        QAItem(
            question=f"What were {hero.label} and {friend.label} trying to understand?",
            answer=f"They were trying to understand why {mechanism.phrase} was not working properly at {world.setting.place}.",
        ),
        QAItem(
            question="What mistake did the friends make first?",
            answer=f"They made the wrong choice at first because {scen['mistake']}",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The clue was that {scen['clue']}",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {scen['twist']}",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{scen['ending']} {scen['final_image']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a group of parts that work together to make something move, open, ring, or do a job.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means giving a warning or showing that it is wise to be careful.",
        ),
        QAItem(
            question="What is a mystery story?",
            answer="A mystery story is about a problem or puzzle that characters try to understand by finding clues.",
        ),
        QAItem(
            question="What does friendship add to a story?",
            answer="Friendship gives characters trust, help, and kind choices, which can help them solve a problem together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        bits = [f"type={ent.type}"]
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: " + ", ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
working(M) :- clue(M), careful(M), not blocked(M).
safe_end :- working(M).
twist :- clue(_), not obvious.
#show working/1.
#show safe_end/0.
#show twist/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("clue", "mechanism"),
        asp.fact("careful", "mechanism"),
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"working/1", "safe_end/0", "twist/0"}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="the old clock room", hero_name="Mina", hero_type="mouse", friend_name="Toby", friend_type="fox", keeper_name="Mrs. Vale", mechanism="a tiny wind-up gate", scenario_index=0),
    StoryParams(setting="the garden shed", hero_name="Lila", hero_type="rabbit", friend_name="Pip", friend_type="duck", keeper_name="Mr. Bell", mechanism="a pop-up drawer latch", scenario_index=1),
    StoryParams(setting="the small museum hall", hero_name="Rae", hero_type="cat", friend_name="June", friend_type="bear", keeper_name="Keeper Finch", mechanism="a rotating lantern arm", scenario_index=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        print("ASP model:", " ".join(str(a) for a in asp.one_model(asp_program())))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(20, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
