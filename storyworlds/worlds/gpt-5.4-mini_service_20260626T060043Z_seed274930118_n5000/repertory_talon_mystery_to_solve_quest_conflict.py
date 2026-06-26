#!/usr/bin/env python3
"""
A standalone story world for a tiny rhyming mystery tale.

Domain premise:
- A little repertory troupe is preparing a night show.
- A missing silver talon prop turns the rehearsal into a mystery.
- The hero follows a quest through a conflict between suspicion and trust.
- The ending resolves when the talon is found and the show can begin.

The world is deliberately small and constraint-checked: the mystery only
appears when there is a believable missing object, a witness trail, and a
satisfying final reveal.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
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
    wearer: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    partner: object | None = None
    prop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
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
class Setting:
    place: str
    indoors: bool = True
    moods: set[str] = field(default_factory=set)
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
class Prop:
    id: str
    label: str
    phrase: str
    clue: str
    hidden_in: str
    shiny: bool = False
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
    hero: str
    hero_type: str
    partner: str
    partner_type: str
    prop: str
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


SETTINGS = {
    "repertory_hall": Setting(place="the repertory hall", indoors=True, moods={"echo", "curtain", "spotlight"}),
    "backstage": Setting(place="the backstage room", indoors=True, moods={"boxes", "costumes", "echo"}),
    "dress_room": Setting(place="the dress room", indoors=True, moods={"mirror", "ribbon", "lace"}),
}

PROPS = {
    "talon": Prop(
        id="talon",
        label="silver talon",
        phrase="a little silver talon prop",
        clue="a bright scratch mark",
        hidden_in="curtain loop",
        shiny=True,
    ),
    "bell": Prop(
        id="bell",
        label="tiny bell",
        phrase="a tiny bell prop",
        clue="a soft ringing sound",
        hidden_in="costume basket",
        shiny=False,
    ),
}

HERO_NAMES = ["Mina", "Rory", "Lina", "Tess", "Nico", "Pia", "Jules", "Milo"]
PARTNER_NAMES = ["Aunt June", "Uncle Theo", "Ms. Star", "Mr. Lane"]

TRAITS = ["brave", "curious", "gentle", "spry", "cheery", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for prop in PROPS:
            out.append((place, prop))
    return out


def rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def atmosphere(setting: Setting) -> str:
    if "curtain" in setting.moods:
        return "The curtains hung like clouds, soft and deep."
    if "mirror" in setting.moods:
        return "The mirrors gleamed, and tiny bows sat in a heap."
    return "The hall was warm, with a hush that made feet tip-toe."


def prop_line(prop: Prop) -> str:
    return f"{prop.phrase} waited on a shelf, all neat and sweet."


def intro(world: World, hero: Entity, partner: Entity, prop: Entity, setting: Setting) -> None:
    world.say(
        f"{hero.id} was a little {hero.type}, quick to smile and quick to sing. "
        f"{partner.label} led the repertory, ready for the spring."
    )
    world.say(
        f"They kept a stage with rhymes and games, with songs that softly flowed, "
        f"and {prop.label} was the best bright prop along the actor's road."
    )


def missing_prop(world: World, prop: Entity) -> None:
    prop.meters["missing"] = 1
    world.say(
        f"But when the room grew hushed that night, the {prop.label} was not in sight. "
        f"The show could start, or stumble hard, if clues did not feel right."
    )


def witness_clue(world: World, setting: Setting, prop: Entity) -> None:
    clue = world.facts.get("clue", prop.phrase)
    world.say(
        f"A sparkle near the {setting.place.replace('the ', '')} gave a clue, "
        f"and {clue} blinked back through."
    )


def quest(world: World, hero: Entity, partner: Entity, prop: Entity) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    world.say(
        f"{hero.id} said, 'I'll seek it out, no need to pout. "
        f"I'll follow crumbs and traces, and I'll find it thereabouts.'"
    )
    world.say(
        f"So {hero.id} searched behind the boxes, where the costume ribbons lay, "
        f"for a path that would reveal where the bright prop hid away."
    )


def conflict(world: World, hero: Entity, partner: Entity, prop: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    hero.memes["doubt"] = hero.memes.get("doubt", 0) + 1
    world.say(
        f"Some folks suspected someone else, and words began to jostle. "
        f"{hero.id} felt the room grow prickly, like a thistle in a bustle."
    )
    world.say(
        f"But {partner.label} said, 'A mystery is not a blame parade. "
        f"We solve it with a careful mind and not a crossly trade.'"
    )


def reveal(world: World, hero: Entity, partner: Entity, prop: Entity, setting: Setting) -> None:
    prop.meters["missing"] = 0
    prop.meters["found"] = 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["worry"] = 0
    world.say(
        f"At last, {hero.id} peeped by the curtains' hem and saw a shiny gleam: "
        f"the {prop.label} had slipped to {prop.hidden_in}, tucked in a silver seam."
    )
    world.say(
        f"{hero.id} brought it back, and laughter leapt from row to row like light. "
        f"The repertory rang with rhymes, and all the stage felt bright."
    )
    world.say(
        f"So the mystery was solved, the quest was done, the conflict turned to cheer. "
        f"The show went on in happy time, with music loud and clear."
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting.place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    partner = world.add(Entity(id="partner", kind="character", type=params.partner_type, label=params.partner))
    prop_cfg = _safe_lookup(PROPS, params.prop)
    prop = world.add(Entity(id=prop_cfg.id, type="prop", label=prop_cfg.label, phrase=prop_cfg.phrase))
    world.facts.update(hero=hero, partner=partner, prop=prop, prop_cfg=prop_cfg, setting=setting, clue=prop_cfg.clue)

    intro(world, hero, partner, prop, setting)
    world.para()
    world.say(atmosphere(setting))
    world.say(prop_line(prop_cfg))
    missing_prop(world, prop)
    conflict(world, hero, partner, prop)
    quest(world, hero, partner, prop)
    witness_clue(world, setting, prop)
    reveal(world, hero, partner, prop, setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prop_cfg = _safe_fact(world, f, "prop_cfg")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a rhyming mystery story for a child about a {hero.type} named {hero.id} in {setting.place}.',
        f'Tell a gentle quest tale where a repertory show loses the {prop_cfg.label} and must solve the clue.',
        f'Write a simple rhyming story with a conflict, a clue, and a happy ending about the missing talon prop.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    partner = _safe_fact(world, f, "partner")
    prop_cfg = _safe_fact(world, f, "prop_cfg")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who went on the quest to find the missing {prop_cfg.label}?",
            answer=f"{hero.id} went on the quest, with {partner.label} helping and guiding the search.",
        ),
        QAItem(
            question=f"What mystery had to be solved in {setting.place}?",
            answer=f"They had to solve the mystery of the missing {prop_cfg.label} before the repertory show could begin.",
        ),
        QAItem(
            question=f"How did the conflict get calmed?",
            answer="The conflict calmed when the hero searched carefully, followed the clue, and found the hidden prop instead of blaming anyone.",
        ),
        QAItem(
            question=f"Where was the {prop_cfg.label} found at the end?",
            answer=f"It was found tucked in {prop_cfg.hidden_in}, where it had slipped out of sight.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a repertory?",
            answer="A repertory is a group that performs many plays or shows, often with actors who rehearse and act together.",
        ),
        QAItem(
            question="What is a talon?",
            answer="A talon is a sharp claw on a bird or other animal, and people can also use the word for a claw-shaped prop or decoration.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not explained at first, so someone has to look for clues and solve it.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, usually with a goal and a few clues along the way.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} {e.type:10} meters={m} memes={mm}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
prop(X) :- prop_kind(X).
quest_ready(P, X) :- place(P), prop(X).
mystery_to_solve(P, X) :- quest_ready(P, X).
conflict(P, X) :- mystery_to_solve(P, X).
show_story(P, X) :- mystery_to_solve(P, X), conflict(P, X).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for x in PROPS:
        lines.append(asp.fact("prop_kind", x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show show_story/2."))
    return sorted(set(asp.atoms(model, "show_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming mystery story world with a quest and conflict.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--prop", choices=sorted(PROPS))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--partner", choices=PARTNER_NAMES)
    ap.add_argument("--partner-type", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    prop = getattr(args, "prop", None) or rng.choice(sorted(PROPS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    partner_type = getattr(args, "partner_type", None) or ("woman" if hero_type == "girl" else "man")
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    partner = getattr(args, "partner", None) or rng.choice(PARTNER_NAMES)
    return StoryParams(place=place, hero=name, hero_type=hero_type, partner=partner, partner_type=partner_type, prop=prop)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


CURATED = [
    StoryParams(place="repertory_hall", hero="Mina", hero_type="girl", partner="Ms. Star", partner_type="woman", prop="talon"),
    StoryParams(place="backstage", hero="Rory", hero_type="boy", partner="Uncle Theo", partner_type="man", prop="talon"),
    StoryParams(place="dress_room", hero="Lina", hero_type="girl", partner="Aunt June", partner_type="woman", prop="bell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show show_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(f"{a} {b}" for a, b in asp_valid_combos()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
