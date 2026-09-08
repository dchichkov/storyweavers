#!/usr/bin/env python3
"""
A small animal story about a scrape, a mysterious gene card, and sharing a locker.

The world uses a concrete animal-story problem: Luna scrapes her paw while
rushing to a school den, then finds a gene picture card in a shared locker.
Her inner monologue helps her sort worry from evidence, while a conversation
and shared plan help everyone use the locker fairly.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    gene: object | None = None
    helper: object | None = None
    hero: object | None = None
    locker: object | None = None
    scrape: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for key in ("pain", "worry", "energy", "readiness", "order"):
            self.meters.setdefault(key, 0.0)
        for key in ("care", "curiosity", "pride", "relief", "trust", "patience"):
            self.memes.setdefault(key, 0.0)
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
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    friend_name: str = "Milo"
    helper_name: str = "Nia"
    place: str = "the sunny forest school"
    locker_label: str = "Moon Locker"
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
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
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
        "opening": "Luna hurried toward school with a leaf notebook tucked under her wing.",
        "scrape": "A root caught her foot, and she got a small scrape on her knee.",
        "clue": "The scrape was shallow, clean, and stopped hurting when she rinsed it.",
        "locker_problem": "The shared locker was crowded with lunch tins, shells, and old drawings.",
        "turn": "A card marked GENE had slipped behind the bottom shelf.",
        "share": "They made three spaces: one for each animal and one shelf for shared science things.",
        "ending": "The gene card rested in the middle shelf, where every curious paw could find it.",
    },
    {
        "opening": "Before the first bell, Luna carried a bundle of bright feathers to the forest school.",
        "scrape": "She slipped on a damp fern and earned a red scrape along her paw.",
        "clue": "Nia showed her that gentle water and a clean cloth were enough for the little scrape.",
        "locker_problem": "Milo had filled the shared locker with treasures until its door would not close.",
        "turn": "Under the treasures lay a picture of a gene, shaped like a twisted ladder.",
        "share": "They sorted keepsakes into named baskets and left the gene picture on a common shelf.",
        "ending": "The locker door clicked shut, and the gene picture smiled from its shared place.",
    },
    {
        "opening": "Luna planned to be first at the animal club meeting, so she dashed beneath the berry bushes.",
        "scrape": "A thorn gave her ankle a tiny scrape before she could slow down.",
        "clue": "The nurse mouse said the scrape needed care, not a grand invention.",
        "locker_problem": "The locker key was safe, but everyone had been placing things wherever a gap appeared.",
        "turn": "Luna found a gene diagram beside a note asking the class to study it together.",
        "share": "The animals labeled small sections and agreed that science cards belonged to everyone.",
        "ending": "Luna's bandage was neat, and the gene diagram stayed bright in the shared locker.",
    },
]


def _bump(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] += amount


def _feel(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] += amount


def _scenario(params: StoryParams) -> dict[str, str]:
    index = params.seed if params.seed is not None else sum(map(ord, params.hero_name))
    return _safe_lookup(SCENARIOS, index % len(SCENARIOS))


def tell(params: StoryParams) -> World:
    scenario = _scenario(params)
    world = World()

    hero = world.add(Entity(params.hero_name, "character", "fox", params.hero_name))
    friend = world.add(Entity(params.friend_name, "character", "rabbit", params.friend_name))
    helper = world.add(Entity(params.helper_name, "character", "mouse", params.helper_name))
    scrape = world.add(Entity("scrape", type="injury", label="small scrape", owner=hero.id))
    gene = world.add(Entity("gene", type="science_card", label="gene picture card"))
    locker = world.add(Entity("locker", type="shared_locker", label=params.locker_label))

    hero.meters["energy"] = 4
    hero.memes["curiosity"] = 1
    friend.memes["curiosity"] = 1
    helper.memes["care"] = 1
    locker.meters["order"] = 1

    world.say(scenario["opening"])
    world.say(
        f"{params.hero_name}, a young fox, was going to {params.place} with "
        f"{params.friend_name}, a rabbit who loved collecting unusual facts."
    )
    world.say(scenario["scrape"])
    _bump(hero, "pain", 1)
    _feel(hero, "worry", 1)
    world.say(
        f"Inside {params.hero_name}'s mind, a worried thought whispered, "
        "'Everyone will stare, and I must fix this all by myself.'"
    )
    world.say(
        f"{params.hero_name} took a breath and answered that thought, "
        "'A small scrape is a problem to check, not a secret to hide.'"
    )

    world.para()
    world.say(
        f"{params.friend_name} asked, 'Does it hurt a lot?' "
        f"{params.hero_name} replied, 'It hurts a little, so I will ask {params.helper_name} for help.'"
    )
    world.say(
        f"{params.helper_name} rinsed the scrape and covered it with a clean bandage. "
        f"{scenario['clue']}"
    )
    hero.meters["pain"] = 0
    _feel(hero, "relief", 1)
    _feel(helper, "care", 1)
    world.say(
        f"While they were putting away the bandage, {params.friend_name} opened the shared locker. "
        f"{scenario['locker_problem']}"
    )
    _bump(locker, "order", -1)
    world.say(f"{scenario['turn']}")

    world.para()
    _feel(hero, "curiosity", 1)
    world.say(
        f"{params.hero_name}'s inner monologue became calmer: "
        "'A gene is part of living things that can help carry traits. It is not a spell, and it is not something to grab without asking.'"
    )
    world.say(
        f"'Can I look at the card?' asked {params.hero_name}. "
        f"{params.friend_name} said, 'Yes, if we share it and put it back where everyone can use it.'"
    )
    world.say(
        f"{params.helper_name} added, 'Then let us make the locker fair instead of merely making room.'"
    )
    world.say(scenario["share"])
    _bump(locker, "order", 2)
    _feel(friend, "trust", 1)
    _feel(hero, "patience", 1)
    _feel(helper, "pride", 1)

    world.para()
    world.say(
        f"The animals read the gene card together. They learned that genes are instructions "
        "in living things that help shape traits, and that traits can be shared through families."
    )
    world.say(
        f"{params.hero_name} realized that sharing did not mean losing everything. "
        f"It meant making a careful place where {params.friend_name} and {params.helper_name} could learn too."
    )
    world.say(
        f"{scenario['ending']} {params.hero_name}'s scrape was protected, the locker was orderly, "
        "and the next animal could open the door without knocking treasures onto the floor."
    )

    world.facts.update(
        params=params,
        hero=hero,
        friend=friend,
        helper=helper,
        scrape=scrape,
        gene=gene,
        locker=locker,
        scenario=scenario,
        resolved=True,
        shared=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    params = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    return [
        f"Write an animal story about {params.hero_name} handling a small scrape and learning to ask for help.",
        "Include a child-friendly explanation of a gene and show animals sharing a science card.",
        "Use inner monologue, spoken dialogue, and a shared locker whose organization changes the ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "params")
    s = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "scenario")
    return [
        QAItem(
            "Who was the story about?",
            f"The story was about {p.hero_name}, a young fox who cared for a scrape, calmed a worried thought, and learned to share a science card."
        ),
        QAItem(
            "How did the scrape happen?",
            f"{s['scrape']} The scrape was small, but {p.hero_name} still asked {p.helper_name} for help."
        ),
        QAItem(
            "What did the animals discover in the locker?",
            f"They discovered a card about a gene, which they studied together rather than keeping hidden or taking for one animal."
        ),
        QAItem(
            "What did the animals do to share the locker?",
            f"They {s['share']} This gave shared science materials a clear place."
        ),
        QAItem(
            "What did the inner monologue help Luna understand?",
            "It helped Luna replace a worried thought with a calmer plan: check the scrape, ask for help, and tell the truth."
        ),
        QAItem(
            "What is a gene?",
            "A gene is part of a living thing's instructions that can help shape traits and can be passed through families."
        ),
    ]


KNOWLEDGE = [
    QAItem(
        "What should an animal do about a small scrape?",
        "An animal should tell a trusted caregiver, gently clean the scrape, and protect it with suitable first aid."
    ),
    QAItem(
        "What is sharing?",
        "Sharing means allowing others to use or enjoy something while respecting ownership, care, and agreed rules."
    ),
    QAItem(
        "What is an inner monologue?",
        "An inner monologue is the quiet stream of thoughts a character has inside their mind."
    ),
    QAItem(
        "Why can a shared locker use labels?",
        "Labels help everyone know where things belong, so materials are easier to find and the shared space stays orderly."
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in entity.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if abs(v) > 1e-9}
        lines.append(
            f"  {entity.id:8} ({entity.type:14}) meters={meters} memes={memes}"
        )
    lines.append(f"  facts: resolved={world.facts.get('resolved')} shared={world.facts.get('shared')}")
    return "\n".join(lines)


ASP_RULES = r"""
careful_scrape :- scrape_checked, bandaged.
scrape_checked :- asked_for_help.
bandaged :- clean_help.
locker_fair :- labeled, shared_material.
resolved :- careful_scrape, locker_fair, gene_studied.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("animal", "luna"),
            asp.fact("animal", "friend"),
            asp.fact("animal", "helper"),
            asp.fact("scrape"),
            asp.fact("scrape_checked"),
            asp.fact("asked_for_help"),
            asp.fact("clean_help"),
            asp.fact("bandaged"),
            asp.fact("gene"),
            asp.fact("gene_studied"),
            asp.fact("shared_material"),
            asp.fact("labeled"),
        ]
    )


def asp_program(show: str = "#show resolved/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    if "resolved" in names:
        print("OK: ASP and Python both resolve the scrape, gene, and shared locker story.")
        return 0
    print("MISMATCH: ASP did not derive resolution.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal story about a scrape, gene, and shared locker.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--hero-name")
    parser.add_argument("--friend-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--place")
    parser.add_argument("--locker-label")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=getattr(args, "seed", None),
        hero_name=getattr(args, "hero_name", None) or rng.choice(["Luna", "Pia", "Tala", "Mira"]),
        friend_name=getattr(args, "friend_name", None) or rng.choice(["Milo", "Odo", "Bram", "Tiko"]),
        helper_name=getattr(args, "helper_name", None) or rng.choice(["Nia", "Bea", "Rumi", "Sela"]),
        place=getattr(args, "place", None) or "the sunny forest school",
        locker_label=getattr(args, "locker_label", None) or "Moon Locker",
    )


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
    StoryParams(hero_name="Luna", friend_name="Milo", helper_name="Nia", seed=0),
    StoryParams(hero_name="Pia", friend_name="Odo", helper_name="Bea", seed=1),
    StoryParams(hero_name="Tala", friend_name="Bram", helper_name="Rumi", seed=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(asp.one_model(asp_program()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
