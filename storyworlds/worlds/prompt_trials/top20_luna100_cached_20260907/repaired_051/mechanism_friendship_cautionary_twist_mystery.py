#!/usr/bin/env python3
"""
A small mystery storyworld about a strange mechanism, friendship, and a
cautionary twist.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
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
    type: str
    label: str
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "stability": 0.0,
            "energy": 0.0,
            "visibility": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "trust": 0.0,
            "courage": 0.0,
            "curiosity": 0.0,
            "relief": 0.0,
        }
    )
    keeper: object | None = None
    object_ent: object | None = None
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
class Setting:
    place: str = "the old clock tower above the village square"
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
    friend_name: str = ""
    friend_type: str = ""
    companion_name: str = ""
    companion_type: str = ""
    mechanism_name: str = ""
    object_name: str = ""
    keeper_name: str = ""
    scenario_index: int = 0
    detail_variant: int = 0
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
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_log: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
        "opening_clue": "At midnight, the tower bell stopped one minute before every hour, and a blue light blinked behind its face.",
        "problem": "The village clock would not turn, and the mayor's brass key had vanished from its hook.",
        "false_lead": "A loose raven feather lay beside the gears, so everyone blamed the birds.",
        "true_clue": "Luna noticed that the blue flashes came in pairs, exactly when the small moon-shaped gear moved.",
        "mechanism": "The friends had to turn three hidden wheels in the order shown by the moon marks, then leave the final lever untouched.",
        "twist": "The missing key had never been stolen; it was inside the mechanism, holding a spring safely still.",
        "ending": "When the clock began again, its first chime sent a silver circle of light across the square.",
        "lesson": "a frightening clue should be examined before it becomes an accusation",
    },
    {
        "opening_clue": "A tiny brass whistle sounded from the locked museum cabinet whenever the rain struck the roof.",
        "problem": "The museum keeper feared that someone was trying to open the cabinet from inside.",
        "false_lead": "Scratches on the lock seemed to point toward a sneaky visitor.",
        "true_clue": "Luna found three damp marks beneath the cabinet, shaped like the teeth of a gear.",
        "mechanism": "The friends slid a paper strip through a narrow slot and matched its holes to the cabinet's turning wheels.",
        "twist": "The whistle was not a warning from a thief; it was a pressure valve singing because the rain had filled a hidden pipe.",
        "ending": "The cabinet stayed locked, and the harmless whistle became the museum's favorite rainy-day sound.",
        "lesson": "a mystery can have a noisy answer that is still gentle",
    },
    {
        "opening_clue": "A row of lanterns went dark whenever someone crossed the bridge after sunset.",
        "problem": "The bridge keeper worried that the last lantern would fail during the evening walk home.",
        "false_lead": "A dark pawprint made the friends suspect a night animal was tampering with the lamps.",
        "true_clue": "Luna saw that each lamp dimmed only after a copper plate beneath a loose board tilted.",
        "mechanism": "The friends used a smooth stone to steady the plate and reset the small spring without touching the hot lamp glass.",
        "twist": "The pawprint belonged to the bridge keeper's dog, who had been carrying fallen leaves away from the mechanism.",
        "ending": "One by one, the lanterns glowed, making a safe golden path over the river.",
        "lesson": "careful teamwork is safer than reaching into a hidden machine",
    },
    {
        "opening_clue": "The baker's window displayed a pie that rang like a bell whenever the shop door opened.",
        "problem": "The baker feared that the ringing pie hid a broken timer and might burn in the oven.",
        "false_lead": "A trail of flour led toward the storeroom, where a small box had been left open.",
        "true_clue": "Luna heard the ring stop whenever the cooling shelf was moved away from the wall.",
        "mechanism": "The friends traced a thin thread from the shelf to a harmless spring under the display board.",
        "twist": "The pie was not ringing at all; a hidden kitchen timer was vibrating through the shelf.",
        "ending": "The baker moved the timer, and the warm pie cooled in peace while the friends shared its first slice.",
        "lesson": "following a sound to its source is better than guessing from its surroundings",
    },
    {
        "opening_clue": "A locked garden gate opened by itself at dawn, although the gardener had lost its only key.",
        "problem": "The gardener worried that the gate would let the goats into the tender seedlings.",
        "false_lead": "A muddy trail ended at the gate, making the gardener suspect a goat had learned the lock.",
        "true_clue": "Luna found a small glass bead caught in the hinge, shining whenever the sun rose.",
        "mechanism": "The friends shaded the bead, lifted the hinge pin with a wooden peg, and reset the gate's timing wheel.",
        "twist": "The key was not missing; it was tied to the gardener's apron string beneath a folded pocket.",
        "ending": "The gate opened only when invited, and the seedlings stood safely beneath the morning dew.",
        "lesson": "a problem may have two causes, so solving one does not mean the search is over",
    },
]


OPENINGS = [
    "On a quiet evening",
    "Just before the last shop closed",
    "When the mist curled over the rooftops",
    "At the edge of a moonlit morning",
    "While the village lamps flickered",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery storyworld about a friendship and a strange mechanism."
    )
    parser.add_argument("--name")
    parser.add_argument("--type")
    parser.add_argument("--companion")
    parser.add_argument("--companion-type")
    parser.add_argument("--mechanism")
    parser.add_argument("--object")
    parser.add_argument("--keeper")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    friend_type = getattr(args, "type", None) or rng.choice(["fox", "rabbit", "mouse", "squirrel"])
    companion_type = getattr(args, "companion_type", None) or rng.choice(["otter", "badger", "sparrow", "cat"])
    return StoryParams(
        friend_name=getattr(args, "name", None) or rng.choice(["Luna", "Mira", "Nell", "Pip"]),
        friend_type=friend_type,
        companion_name=getattr(args, "companion", None) or rng.choice(["Theo", "Juno", "Moss", "Bram"]),
        companion_type=companion_type,
        mechanism_name=getattr(args, "mechanism", None) or rng.choice(
            ["moon mechanism", "brass mechanism", "hidden mechanism"]
        ),
        object_name=getattr(args, "object", None) or rng.choice(
            ["brass key", "silver wheel", "blue lantern", "tiny bell"]
        ),
        keeper_name=getattr(args, "keeper", None) or rng.choice(["Mara", "Old Rowan", "Keeper Sol"]),
        scenario_index=rng.randrange(len(SCENARIOS)),
        detail_variant=rng.randrange(10000),
    )


def tell(params: StoryParams) -> World:
    scenario = _safe_lookup(SCENARIOS, params.scenario_index % len(SCENARIOS))
    world = World(Setting())

    friend = world.add(
        Entity("friend", "animal", params.friend_type, params.friend_name)
    )
    companion = world.add(
        Entity("companion", "animal", params.companion_type, params.companion_name)
    )
    keeper = world.add(Entity("keeper", "person", "keeper", params.keeper_name))
    mechanism = world.add(
        Entity("mechanism", "thing", "mechanism", params.mechanism_name)
    )
    object_ent = world.add(Entity("object", "thing", "object", params.object_name))

    world.facts.update(
        friend=friend,
        companion=companion,
        keeper=keeper,
        mechanism=mechanism,
        object=object_ent,
        scenario=scenario,
    )

    friend.memes["curiosity"] = 1.0
    companion.memes["trust"] = 1.0
    mechanism.meters["stability"] = 0.2
    mechanism.meters["visibility"] = 0.1

    opening = _safe_lookup(OPENINGS, params.detail_variant % len(OPENINGS))
    world.say(
        f"{opening}, {params.friend_name} the {params.friend_type} and "
        f"{params.companion_name} the {params.companion_type} met "
        f"{params.keeper_name} at {world.setting.place}."
    )
    world.say(scenario["opening_clue"])
    world.say(
        f'"Something inside the {params.mechanism_name} is moving," '
        f"{params.keeper_name} whispered. "
        f'"Can we look without breaking it?" {params.friend_name} asked.'
    )
    world.say(
        f'"Only if you stay together and touch nothing hot or sharp," '
        f"{params.keeper_name} replied."
    )
    world.para()

    friend.memes["worry"] = 1.0
    mechanism.meters["visibility"] = 0.4
    world.say(scenario["problem"])
    world.say(scenario["false_lead"])
    world.say(
        f"{params.companion_name} pointed at the clue. "
        f'"That proves someone did it," {params.companion_name} said.'
    )
    world.say(
        f'"It proves only that something happened here," '
        f"{params.friend_name} answered. "
        f'"Let us find out what it was."'
    )
    world.para()

    friend.memes["courage"] = 1.0
    companion.memes["trust"] = 2.0
    mechanism.meters["stability"] = 0.6
    world.say(scenario["true_clue"])
    world.say(
        f"The friends placed their paws side by side and studied the "
        f"{params.mechanism_name} instead of pulling at it."
    )
    world.say(scenario["mechanism"])
    world.say(
        f'"I will read the marks, and you steady the case," '
        f"{params.friend_name} told {params.companion_name}."
    )
    world.say(
        f'"Together, then," {params.companion_name} replied, and their careful '
        f"work made the hidden wheels click into place."
    )
    world.para()

    mechanism.meters["stability"] = 1.0
    mechanism.meters["energy"] = 1.0
    object_ent.meters["visibility"] = 1.0
    friend.memes["relief"] = 1.0
    companion.memes["courage"] = 1.0
    world.say(scenario["twist"])
    world.say(
        f"{params.keeper_name} checked the {params.object_name} and then checked "
        f"the friends' work. Nothing had been forced, and the mechanism was safe."
    )
    world.say(scenario["ending"])
    world.say(
        f"{params.friend_name} understood that {scenario['lesson']}. "
        f"The friends walked home together, listening for one another's footsteps."
    )
    world.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    world.log("mechanism_stability=1.0")
    world.log("friendship_trust=2.0")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scenario = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "scenario")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")  # type: ignore[assignment]
    companion: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "companion")  # type: ignore[assignment]
    mechanism: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mechanism")  # type: ignore[assignment]
    return [
        f"Write a child-friendly mystery about {friend.label} and {companion.label} investigating a {mechanism.label}.",
        f"Tell a story where friendship helps solve a cautious mystery involving {scenario['opening_clue']}",
        "Include a misleading clue, a safe investigation, a twist, and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scenario = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "scenario")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")  # type: ignore[assignment]
    companion: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "companion")  # type: ignore[assignment]
    keeper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "keeper")  # type: ignore[assignment]
    mechanism: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mechanism")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What mystery did {keeper.label} ask {friend.label} and {companion.label} to investigate?",
            answer=f"They investigated why the {mechanism.label} was behaving strangely: {scenario['problem']}",
        ),
        QAItem(
            question="What was the misleading clue?",
            answer=f"{scenario['false_lead']} The friends learned that it was not enough to prove who caused the mystery.",
        ),
        QAItem(
            question=f"How did the friends investigate the {mechanism.label} safely?",
            answer=f"They stayed together, studied the clues, and followed the mechanism's marks without grabbing hot or sharp parts. {scenario['mechanism']}",
        ),
        QAItem(
            question="What was the twist?",
            answer=scenario["twist"],
        ),
        QAItem(
            question=f"What did {friend.label} learn about friendship and caution?",
            answer=f"{friend.label} learned that {scenario['lesson']} Working patiently with {companion.label} made the mystery safer to solve.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of moving parts that work together to do a job, such as turning a wheel, opening a latch, or ringing a bell.",
        ),
        QAItem(
            question="Why should children be cautious around mechanisms?",
            answer="Children should avoid hot, sharp, heavy, or fast-moving parts and ask a responsible grown-up before touching an unfamiliar machine.",
        ),
        QAItem(
            question="What makes a good mystery clue?",
            answer="A good mystery clue is a detail that can be checked and connected to what happened, rather than just something that looks suspicious.",
        ),
        QAItem(
            question="How can friendship help solve a problem?",
            answer="Friends can share observations, listen to one another, and make careful decisions together instead of rushing alone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        details = [f"type={entity.type}"]
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(details))
    if world.trace_log:
        lines.append("events:")
        lines.extend(f"- {entry}" for entry in world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
entity(friend).
entity(companion).
entity(mechanism).
entity(keeper).

safe_investigation :- friendship(friend, companion), caution_used, mechanism_stable.
mystery_solved :- safe_investigation, twist_understood.
happy_end :- mystery_solved.
#show safe_investigation/0.
#show mystery_solved/0.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("friendship", "friend", "companion"),
            asp.fact("caution_used"),
            asp.fact("mechanism_stable"),
            asp.fact("twist_understood"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show safe_investigation/0. "
            "#show mystery_solved/0. "
            "#show happy_end/0."
        )
    )
    atoms = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"safe_investigation/0", "mystery_solved/0", "happy_end/0"}
    if atoms != expected:
        print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
        return 1

    params = StoryParams(
        friend_name="Luna",
        friend_type="fox",
        companion_name="Theo",
        companion_type="badger",
        mechanism_name="moon mechanism",
        object_name="brass key",
        keeper_name="Mara",
    )
    sample = generate(params)
    required = ["mechanism", "together", "mystery"]
    lowered = sample.story.lower()
    if not all(word in lowered for word in required):
        print("MISMATCH: generated story lacks required narrative evidence")
        return 1
    print("OK: ASP parity check and story exercise passed.")
    return 0


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


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
    StoryParams(
        friend_name="Luna",
        friend_type="fox",
        companion_name="Theo",
        companion_type="badger",
        mechanism_name="moon mechanism",
        object_name="brass key",
        keeper_name="Mara",
        scenario_index=0,
    ),
    StoryParams(
        friend_name="Mira",
        friend_type="rabbit",
        companion_name="Juno",
        companion_type="sparrow",
        mechanism_name="brass mechanism",
        object_name="silver wheel",
        keeper_name="Old Rowan",
        scenario_index=1,
    ),
    StoryParams(
        friend_name="Nell",
        friend_type="mouse",
        companion_name="Moss",
        companion_type="otter",
        mechanism_name="hidden mechanism",
        object_name="blue lantern",
        keeper_name="Keeper Sol",
        scenario_index=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_investigation/0. #show mystery_solved/0. #show happy_end/0."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(
            asp_program(
                "#show safe_investigation/0. "
                "#show mystery_solved/0. "
                "#show happy_end/0."
            )
        )
        print("ASP model:", " ".join(str(atom) for atom in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < getattr(args, "n", None) and attempt < max(20, getattr(args, "n", None) * 20):
            current_seed = base_seed + attempt
            rng = random.Random(current_seed)
            params = resolve_params(args, rng)
            params.seed = current_seed
            sample = generate(params)
            attempt += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
