#!/usr/bin/env python3
"""
storyworlds/worlds/turtle_poke_proposition_conflict_rhyme_nursery_rhyme.py
===========================================================================

A tiny nursery-rhyme storyworld about a turtle, a poke, and a proposition.

Premise:
- A child meets a turtle in a small garden or pondside nook.
- The child wants to poke the turtle because curiosity is strong.
- The turtle feels wary and offers a proposition: no pokes, but a rhyme game
  instead.

Turn:
- The child ignores the first warning, causing conflict.
- A rhythm of simple rhyme and kind words slows the moment down.

Resolution:
- The child accepts the proposition, stops poking, and the turtle opens up.
- The ending image shows the turtle calm, the child pleased, and the conflict
  softened into a rhyme.

This world is built to stay small and clear, with state-driven narrative,
world-grounded QA, and a matching inline ASP twin.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    turtle: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    place: str = "the garden"
    affords: set[str] = field(default_factory=set)
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
class TurtleMood:
    shell: str
    rhyme: str
    proposition: str
    reply: str
    calm_image: str
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
    child_name: str
    child_gender: str
    turtle_name: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def mood_for_turtle() -> TurtleMood:
    return TurtleMood(
        shell="shell",
        rhyme="slow and low",
        proposition="a song for a no-poke promise",
        reply="No poke today; let's make a rhyme and play",
        calm_image="the turtle blinked, then tucked its head back out to grin",
    )


SETTINGS = {
    "garden": Setting(place="the garden", affords={"poke", "proposition", "rhyme"}),
    "pond": Setting(place="the pond", affords={"poke", "proposition", "rhyme"}),
    "lantern_path": Setting(place="the lantern-lit path", affords={"poke", "proposition", "rhyme"}),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Ben", "Luna", "Theo", "Ava", "Finn"]
TURTLE_NAMES = ["Toby", "Tilly", "Tansy", "Tucker", "Tess"]

ASP_RULES = r"""
child_wants_poke(C) :- child(C).
turtle_warns(T) :- turtle(T).
conflict(C,T) :- child_wants_poke(C), turtle_warns(T), poke_near(T).
resolved(C,T) :- conflict(C,T), accepted_proposition(C,T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_places() -> list[str]:
    return sorted(SETTINGS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme turtle storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--turtle-name", dest="turtle_name")
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
    place = getattr(args, "place", None) or rng.choice(valid_places())
    child_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    turtle_name = getattr(args, "turtle_name", None) or rng.choice(TURTLE_NAMES)
    return StoryParams(
        place=place,
        child_name=child_name,
        child_gender=child_gender,
        turtle_name=turtle_name,
    )


def child_pronoun(gender: str) -> str:
    return "she" if gender == "girl" else "he"


def child_possessive(gender: str) -> str:
    return "her" if gender == "girl" else "his"


def child_object(gender: str) -> str:
    return "her" if gender == "girl" else "him"


def generate_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender))
    turtle = world.add(Entity(id=params.turtle_name, kind="character", type="turtle"))
    world.facts.update(child=child, turtle=turtle, params=params)
    return world


def predict_conflict(world: World, child: Entity, turtle: Entity) -> bool:
    sim = world.copy()
    sim.facts["poke_attempt"] = True
    return True


def tell(world: World) -> None:
    params: StoryParams = _safe_fact(world, world.facts, "params")
    child: Entity = _safe_fact(world, world.facts, "child")
    turtle: Entity = _safe_fact(world, world.facts, "turtle")
    mood = mood_for_turtle()

    world.say(
        f"One bright day at {world.setting.place}, {child.id} met {turtle.id}, a tiny turtle with a shiny {mood.shell}."
    )
    world.say(
        f"{child.id} wanted to poke {turtle.id} just to see what would happen, because curiosity was bouncing like a marble."
    )

    world.para()
    world.say(
        f"{turtle.id} drew back a little and said, \"Please don't poke me. I like a soft hello and a gentle rhyme.\""
    )
    world.say(
        f"Then {turtle.id} made a proposition: \"If you keep your fingers still, I'll share {mood.proposition}.\""
    )
    child.memes["want_poke"] = 1.0
    turtle.memes["worry"] = 1.0
    child.memes["conflict"] = 1.0

    world.para()
    world.say(
        f"At first {child.id} forgot the warning and reached out anyway, so the air turned tight and the little turtle hid in its {mood.shell}."
    )
    world.say(
        f"{child.id} frowned, then remembered the kind words and listened to the rhythm of {mood.rhyme}."
    )

    world.para()
    child.memes["conflict"] = 0.0
    child.memes["joy"] = 1.0
    turtle.memes["worry"] = 0.0
    turtle.memes["trust"] = 1.0
    world.say(
        f"{child.id} smiled and accepted the proposition. {child.id} clapped softly, and together they sang a tiny tune: \"Slow and low, hello, hello.\""
    )
    world.say(
        f"{turtle.id} peeked out again, calmer now, and {mood.calm_image}; the poke was over, and the rhyme had won."
    )

    world.facts["resolved"] = True
    world.facts["mood"] = mood


def story_text(world: World) -> str:
    return world.render()


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = _safe_fact(world, world.facts, "params")
    child: Entity = _safe_fact(world, world.facts, "child")
    turtle: Entity = _safe_fact(world, world.facts, "turtle")
    mood: TurtleMood = _safe_fact(world, world.facts, "mood")
    return [
        QAItem(
            question=f"Who wanted to poke {turtle.id} in the story?",
            answer=f"{child.id} wanted to poke {turtle.id} because curiosity was bouncing around in {child_possessive(params.child_gender)} head.",
        ),
        QAItem(
            question=f"What proposition did {turtle.id} make?",
            answer=f"{turtle.id} offered {mood.proposition}: if {child.id} kept still, the two of them could share a rhyme instead of a poke.",
        ),
        QAItem(
            question="What happened to the conflict by the end?",
            answer=f"The conflict got small and quiet. {child.id} stopped reaching, listened to the rhyme, and the turtle came back out calm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a turtle usually do when it feels scared?",
            answer="A turtle often pulls its head and feet in close to its shell to feel safe.",
        ),
        QAItem(
            question="What is a proposition?",
            answer="A proposition is a suggestion or offer, like asking someone to choose one kind plan instead of another.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when words sound alike at the end, like 'low' and 'go' or 'me' and 'tree'.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = _safe_fact(world, world.facts, "params")
    return [
        f"Write a short nursery rhyme about {params.child_name} and a turtle in {world.setting.place}.",
        f"Tell a gentle story where a child wants to poke a turtle, but the turtle makes a proposition and the conflict ends with a rhyme.",
        "Make the ending calm, kind, and musical.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_valid_places() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show affords/2."))
    return sorted(set(asp.atoms(model, "affords")))


def asp_verify() -> int:
    import asp

    program = asp_program("#show affords/2.")
    model = asp.one_model(program)
    asp_places = sorted(set(asp.atoms(model, "affords")))
    py_places = sorted((place, act) for place, setting in SETTINGS.items() for act in setting.affords)
    if asp_places != py_places:
        print("MISMATCH between clingo and Python registry facts:")
        print("  asp:", asp_places)
        print("  py :", py_places)
        return 1
    sample = generate(StoryParams(place="garden", child_name="Mia", child_gender="girl", turtle_name="Toby"))
    if not sample.story or "proposition" not in sample.story:
        print("Story verification failed.")
        return 1
    print(f"OK: ASP parity holds and story generation works ({len(sample.story)} chars).")
    return 0


CURATED = [
    StoryParams(place="garden", child_name="Mia", child_gender="girl", turtle_name="Toby"),
    StoryParams(place="pond", child_name="Leo", child_gender="boy", turtle_name="Tilly"),
    StoryParams(place="lantern_path", child_name="Nora", child_gender="girl", turtle_name="Tansy"),
]


def resolve_invalid(args: argparse.Namespace) -> None:
    pass


def asp_program_full(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program_full("#show resolved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program_full("#show affords/2."))
        combos = sorted(set(asp.atoms(model, "affords")))
        print(f"{len(combos)} place/activity facts:")
        for place, act in combos:
            print(f"  {place} {act}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name} and {p.turtle_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
