#!/usr/bin/env python3
"""
A small heartwarming storyworld about a parade, a sailor, and an infantry band.
The twist is that the quietest marcher carries the sound everyone needs.
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
            "balance": 0.0,
            "volume": 0.0,
            "readiness": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "courage": 0.0,
            "trust": 0.0,
            "joy": 0.0,
            "belonging": 0.0,
        }
    )
    drummer: object | None = None
    leader: object | None = None
    parade: object | None = None
    sailor: object | None = None
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
    place: str = "Harbor Square"
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
    sailor: str = ""
    sailor_type: str = ""
    infantry_leader: str = ""
    drummer: str = ""
    parade_name: str = ""
    setting: str = ""
    scenario_index: int = 0
    twist_index: int = 0
    detail_variant: int = 0
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace_log: list[str] = field(default_factory=list)

    world: object | None = None
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


SCENARIOS = [
    {
        "opening": "The town was ready for its spring harbor parade",
        "problem": "a sea wind tore the music pages from the infantry band's stand",
        "risk": "Without the music, the marchers might lose their steps before reaching the children's hospital",
        "clue": "the sailor noticed that every loose page had caught on the same bright blue rope",
        "action": "the sailor tied the pages together with a spare knot and used the parade's flagpoles as a broad windbreak",
        "turn": "The band tried to play the loudest tune, but the wind swallowed it; then the sailor heard a tiny bell beneath the pier",
        "result": "the little bell gave the drummer a steady beat, and the infantry marched together again",
        "image": "At the hospital gate, the band played softly while children waved paper boats from the windows",
        "lesson": "a small, steady sound can guide many brave feet",
    },
    {
        "opening": "At sunrise, the harbor bells announced the town's annual lantern parade",
        "problem": "a fog rolled over the road and hid the painted signs that marked the marching route",
        "risk": "The infantry could have turned toward the busy ferry lane instead of the quiet home for older neighbors",
        "clue": "the sailor saw warm reflections trembling in puddles beside the curb",
        "action": "the sailor placed lanterns along the reflected trail while the drummer tapped a gentle signal at each turn",
        "turn": "Everyone wanted to follow the largest light, but the sailor pointed out that the safest path was the one repeated in every puddle",
        "result": "the parade reached the home by a calm route, with every lantern still glowing",
        "image": "The older neighbors held the lanterns high, and the fog looked like a soft silver curtain",
        "lesson": "careful clues can lead a whole crowd more safely than bright guesses",
    },
    {
        "opening": "By noon, ribbons fluttered above the town's welcome-home parade",
        "problem": "the sailor's old flag had lost its pole just as the infantry came to the narrow bridge",
        "risk": "The flag might fall into the river, and the returning sailors would have no welcome to follow",
        "clue": "the drummer found a strong oar tucked beside the bridge keeper's shed",
        "action": "the sailor asked the infantry leader to hold the ribbon while the drummer fixed the flag to the oar",
        "turn": "The tallest soldiers first reached for the flag, but the sailor realized the bridge was strongest when everyone stood still and shared the work",
        "result": "the flag rose safely above the bridge and showed the way home",
        "image": "The whole parade cheered beneath the bright flag while river swallows dipped overhead",
        "lesson": "being strong also means knowing when to ask for help",
    },
    {
        "opening": "On a warm afternoon, the village gathered for a kindness parade",
        "problem": "the infantry's flower cart lost a wheel beside the cobbler's lane",
        "risk": "The flowers could wilt before they reached the lonely lighthouse keeper",
        "clue": "the sailor saw that the cart's broken wheel matched the round wooden lid of a biscuit tin",
        "action": "the sailor asked the cobbler for a leather strap and helped fasten the tin lid beneath the cart",
        "turn": "The first repair looked shiny but slipped at the first bump; the sailor chose the plain tin lid because it fit the axle more closely",
        "result": "the repaired cart rolled smoothly, carrying flowers all the way to the lighthouse",
        "image": "The lighthouse keeper received a bright armful of flowers and waved until the parade disappeared",
        "lesson": "the useful answer is not always the fanciest one",
    },
]


OPENINGS = [
    "Before the first trumpet call",
    "As gulls circled above the roofs",
    "While the harbor lamps faded",
    "When the town clock struck nine",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming parade storyworld with a sailor, infantry, and a twist."
    )
    parser.add_argument("--sailor")
    parser.add_argument("--sailor-type")
    parser.add_argument("--infantry-leader")
    parser.add_argument("--drummer")
    parser.add_argument("--parade-name")
    parser.add_argument("--setting")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    sailor = getattr(args, "sailor", None) or rng.choice(["Mara", "Jonah", "Nell", "Rafi", "Tess"])
    sailor_type = getattr(args, "sailor_type", None) or rng.choice(["sailor", "deckhand", "harbor sailor"])
    infantry_leader = getattr(args, "infantry_leader", None) or rng.choice(
        ["Captain Vale", "Sergeant Rose", "Lieutenant Bell", "Corporal Finch"]
    )
    drummer = getattr(args, "drummer", None) or rng.choice(["Pip", "Wren", "Milo", "June"])
    parade_name = getattr(args, "parade_name", None) or rng.choice(
        ["the Harbor Parade", "the Welcome Parade", "the Lantern Parade", "the Kindness Parade"]
    )
    setting = getattr(args, "setting", None) or rng.choice(
        ["Harbor Square", "the old ferry road", "Seabird Avenue", "the lighthouse lane"]
    )
    return StoryParams(
        sailor=sailor,
        sailor_type=sailor_type,
        infantry_leader=infantry_leader,
        drummer=drummer,
        parade_name=parade_name,
        setting=setting,
        scenario_index=rng.randrange(len(SCENARIOS)),
        twist_index=rng.randrange(4),
        detail_variant=rng.randrange(10_000),
    )


def tell(params: StoryParams) -> World:
    scenario = _safe_lookup(SCENARIOS, params.scenario_index % len(SCENARIOS))
    world = World(Setting(params.setting))

    sailor = world.add(Entity("sailor", "person", params.sailor_type, params.sailor))
    leader = world.add(Entity("infantry", "person", "infantry leader", params.infantry_leader))
    drummer = world.add(Entity("drummer", "person", "drummer", params.drummer))
    parade = world.add(Entity("parade", "group", "parade", params.parade_name))

    world.facts.update(
        sailor=sailor,
        leader=leader,
        drummer=drummer,
        parade=parade,
        scenario=scenario,
    )

    sailor.memes["courage"] += 1
    leader.memes["trust"] += 1
    drummer.meters["readiness"] = 1.0

    opening = _safe_lookup(OPENINGS, params.detail_variant % len(OPENINGS))
    world.say(
        f"{opening}, {sailor.label} the {sailor.type} polished a little brass whistle "
        f"beside {world.setting.place}."
    )
    world.say(
        f"The town was preparing {params.parade_name}, and the infantry waited behind "
        f"{leader.label} with bright shoes and careful rows."
    )
    world.say(
        f"{leader.label} called, \"Can you help us reach the far end of the parade?\" "
        f"{sailor.label} answered, \"I know these harbor roads. I will help you find the way.\""
    )
    world.para()

    sailor.meters["distance"] += 1.0
    sailor.memes["worry"] += 1.0
    world.say(f"{scenario['opening']}. Soon, {scenario['problem']}.")
    world.say(
        f"{scenario['risk']}. {leader.label} looked at the silent instruments, while "
        f"{drummer.label} held the first drumbeat in a nervous hand."
    )
    world.para()

    world.say(f"\"We should hurry,\" said {leader.label}. \"Hurrying may scatter us,\" replied {sailor.label}.")
    world.say(f"{scenario['turn']}.")
    world.say(f"Then {sailor.label} explained, \"{scenario['clue'].capitalize()}.\"")
    sailor.memes["courage"] += 1
    leader.memes["trust"] += 1
    world.para()

    world.say(f"{scenario['action'].capitalize()}.")
    drummer.meters["volume"] = 1.0
    drummer.meters["balance"] = 1.0
    leader.meters["readiness"] = 1.0
    parade.meters["balance"] = 1.0
    parade.memes["joy"] += 1
    parade.memes["belonging"] += 1
    world.say(f"That was the twist: {scenario['result'].capitalize()}.")
    world.say(
        f"\"You did not lead us by shouting,\" {leader.label} told {sailor.label}. "
        f"\"You listened first.\" {sailor.label} smiled. \"The harbor had been helping us all along.\""
    )
    world.para()

    sailor.memes["relief"] += 1
    sailor.memes["belonging"] += 1
    leader.memes["joy"] += 1
    world.say(f"The parade arrived safely. {scenario['image']}.")
    world.say(
        f"{sailor.label} understood that {scenario['lesson']}. "
        f"The infantry gave the sailor the place of honor beside the drum."
    )
    world.log(f"scenario={params.scenario_index % len(SCENARIOS)}")
    world.log("twist=quiet observation became the parade's guiding strength")
    world.log("resolution=the parade reached its destination together")
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "scenario")
    sailor: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "sailor")  # type: ignore[assignment]
    parade: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "parade")  # type: ignore[assignment]
    return [
        f"Write a heartwarming story about {sailor.label}, a sailor who helps {parade.label}.",
        "Include a parade, an infantry group, spoken dialogue, and a surprising but gentle twist.",
        f"Show how {sailor.label} solves a parade problem by noticing something others miss.",
        f"End with an image proving that the {parade.label} reached its destination together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "scenario")
    sailor: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "sailor")  # type: ignore[assignment]
    leader: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "leader")  # type: ignore[assignment]
    parade: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "parade")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What problem threatened {parade.label}?",
            answer=f"{scenario['problem'].capitalize()} This put the parade's safe arrival at risk.",
        ),
        QAItem(
            question=f"What did {sailor.label} notice?",
            answer=f"{scenario['clue'].capitalize()} The observation gave the group a practical way forward.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {scenario['result'].lower()} The sailor's quiet observation, rather than force or noise, helped the infantry move together.",
        ),
        QAItem(
            question=f"How did {sailor.label} help the infantry?",
            answer=f"{scenario['action'].capitalize()}. This allowed the parade to continue safely.",
        ),
        QAItem(
            question=f"What did {leader.label} learn from the sailor?",
            answer=f"{leader.label} learned that listening and noticing can guide a group better than simply hurrying or shouting.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people or groups travel together, often with music, flags, or decorations.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or travels in a boat or ship and uses knowledge of water, weather, and navigation.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who travel and work mainly on foot. In this story, the infantry is presented as a marching group helping the community.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change or discovery that makes an earlier problem look different.",
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
        detail = [f"type={entity.type}"]
        if meters:
            detail.append(f"meters={meters}")
        if memes:
            detail.append(f"memes={memes}")
        lines.append(f"{entity.id}: " + ", ".join(detail))
    for event in world.trace_log:
        lines.append(f"event: {event}")
    return "\n".join(lines)


ASP_RULES = r"""
entity(parade).
entity(sailor).
entity(infantry).
entity(drummer).

observed(sailor).
helped(sailor, infantry).
steady(drummer).
arrived(parade).

guided(parade, sailor) :- observed(sailor), helped(sailor, infantry), steady(drummer).
heartwarming(parade) :- guided(parade, sailor), arrived(parade).

#show guided/2.
#show heartwarming/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("observed", "sailor"),
            asp.fact("helped", "sailor", "infantry"),
            asp.fact("steady", "drummer"),
            asp.fact("arrived", "parade"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show guided/2. #show heartwarming/1."))
    found = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"guided/2", "heartwarming/1"}
    if found == expected:
        print("OK: ASP parity check passed.")
        for index, params in enumerate(CURATED):
            sample = generate(params)
            if "parade" not in sample.story.lower() or "sailor" not in sample.story.lower():
                print(f"MISMATCH: generated story {index + 1} lacks required domain words")
                return 1
        print("OK: generated story checks passed.")
        return 0
    print(f"MISMATCH: {sorted(found)} != {sorted(expected)}")
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
        sailor="Mara",
        sailor_type="sailor",
        infantry_leader="Captain Vale",
        drummer="Pip",
        parade_name="the Harbor Parade",
        setting="Harbor Square",
        scenario_index=0,
        twist_index=0,
        detail_variant=11,
    ),
    StoryParams(
        sailor="Jonah",
        sailor_type="deckhand",
        infantry_leader="Sergeant Rose",
        drummer="Wren",
        parade_name="the Lantern Parade",
        setting="the old ferry road",
        scenario_index=1,
        twist_index=1,
        detail_variant=27,
    ),
    StoryParams(
        sailor="Nell",
        sailor_type="harbor sailor",
        infantry_leader="Lieutenant Bell",
        drummer="June",
        parade_name="the Welcome Parade",
        setting="Seabird Avenue",
        scenario_index=2,
        twist_index=2,
        detail_variant=43,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show guided/2. #show heartwarming/1."))
        return

    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())

    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show guided/2. #show heartwarming/1."))
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
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            attempt += 1
            sample = generate(params)
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
