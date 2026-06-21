#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bubble_glide_surprise_transformation_animal_story.py
====================================================================================

A tiny animal story world about a little creature making a bubble glide through a
calm place, then surprising everyone with a transformation. The world is small on
purpose: a bubble needs a helper, a gliding path, a surprise, and a changed form
at the end.

The story variations are constraint-checked rather than free-form. The simulated
world state drives the prose, Q&A, and the ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"cat", "rabbit", "bird", "fox", "squirrel", "mouse", "bear"}
        masculine = {"dog", "frog", "duck"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Creature:
    id: str
    type: str
    label: str
    habitat: str
    movement: str
    transformation: str
    surprise: str
    bubble_need: str
    bubble_safe: bool = True
    can_glide: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Place:
    id: str
    label: str
    scene: str
    glide_path: str
    can_hold_bubble: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    use: str
    gives_bubble: bool = False
    helps_glide: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_bubble(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("bubble", 0.0) < THRESHOLD:
            continue
        sig = ("bubble", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["wonder"] = ent.memes.get("wonder", 0.0) + 1
        out.append("")
    return out


def _r_glide(world: World) -> list[str]:
    out: list[str] = []
    mover = world.entities.get("hero")
    place = world.entities.get("place")
    if not mover or not place:
        return out
    if mover.meters.get("gliding", 0.0) < THRESHOLD:
        return out
    sig = ("glide", mover.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mover.meters["near"] = mover.meters.get("near", 0.0) + 1
    place.memes["calm"] = place.memes.get("calm", 0.0) + 1
    return out


CAUSAL_RULES = [Rule("bubble", "wonder", _r_bubble), Rule("glide", "motion", _r_glide)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def bubble_needed(creature: Creature, place: Place) -> bool:
    return creature.bubble_safe and place.can_hold_bubble


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for cid, creature in CREATURES.items():
        for pid, place in PLACES.items():
            for aid, aid_obj in AIDS.items():
                if creature.can_glide and place.can_hold_bubble and aid_obj.gives_bubble and aid_obj.helps_glide:
                    combos.append((cid, pid, aid, creature.transformation))
    return combos


def _choose_name(rng: random.Random, pool: list[str]) -> str:
    return rng.choice(pool)


def reason_rejection(creature: Creature, place: Place, aid: Aid) -> str:
    return "(No story: this world needs a bubble that can safely glide through a place, and the chosen pieces do not fit.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story about bubble, glide, surprise, and transformation.")
    ap.add_argument("--animal", choices=CREATURES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--aid", choices=AIDS)
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


@dataclass
class StoryParams:
    animal: str
    place: str
    aid: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CREATURES = {
    "cat": Creature(
        id="cat",
        type="cat",
        label="cat",
        habitat="window sill",
        movement="glide",
        transformation="butterfly",
        surprise="tiny wings appeared",
        bubble_need="bubble",
        tags={"animal", "bubble", "glide", "surprise", "transformation"},
    ),
    "rabbit": Creature(
        id="rabbit",
        type="rabbit",
        label="rabbit",
        habitat="garden patch",
        movement="glide",
        transformation="kite",
        surprise="a long ribbon tail unfurled",
        bubble_need="bubble",
        tags={"animal", "bubble", "glide", "surprise", "transformation"},
    ),
    "bird": Creature(
        id="bird",
        type="bird",
        label="bird",
        habitat="tree branch",
        movement="glide",
        transformation="lantern",
        surprise="its feathers shone like paper stars",
        bubble_need="bubble",
        tags={"animal", "bubble", "glide", "surprise", "transformation"},
    ),
}

PLACES = {
    "pond": Place(id="pond", label="pond", scene="a quiet pond", glide_path="over the water"),
    "meadow": Place(id="meadow", label="meadow", scene="a soft meadow", glide_path="over the grass"),
    "garden": Place(id="garden", label="garden", scene="a sleepy garden", glide_path="between the flowers"),
}

AIDS = {
    "leaf": Aid(id="leaf", label="leaf boat", phrase="a shiny leaf boat", use="carry a bubble", gives_bubble=True, helps_glide=True),
    "shell": Aid(id="shell", label="shell cradle", phrase="a little shell cradle", use="hold a bubble", gives_bubble=True, helps_glide=True),
    "feather": Aid(id="feather", label="feather fan", phrase="a soft feather fan", use="help a glide", gives_bubble=False, helps_glide=True),
}

CURATED = [
    StoryParams(animal="cat", place="pond", aid="leaf"),
    StoryParams(animal="rabbit", place="meadow", aid="shell"),
    StoryParams(animal="bird", place="garden", aid="leaf"),
]

GIRLISH = ["Mina", "Lumi", "Pippa", "Tia"]
BOYISH = ["Nico", "Ollie", "Polo", "Toto"]


def tell(params: StoryParams) -> World:
    creature = CREATURES.get(params.animal)
    place = PLACES.get(params.place)
    aid = AIDS.get(params.aid)
    if creature is None or place is None or aid is None:
        raise StoryError("(Invalid parameters for this animal story.)")
    if not (bubble_needed(creature, place) and aid.gives_bubble and aid.helps_glide):
        raise StoryError(reason_rejection(creature, place, aid))

    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=creature.type, label=creature.label))
    place_ent = world.add(Entity(id="place", kind="place", type="place", label=place.label))
    tool = world.add(Entity(id="aid", kind="thing", type="thing", label=aid.label))
    world.facts.update(creature=creature, place=place, aid=aid, hero=hero, place_ent=place_ent, tool=tool)

    hero.meters["bubble"] = 1.0
    hero.memes["hope"] = 1.0
    world.say(f"In {place.scene}, a little {creature.label} found {aid.phrase}.")
    world.say(f"It was made for a {creature.bubble_need}, and the path was perfect for a glide {place.glide_path}.")
    world.para()
    world.say(f"The {creature.label} gave the bubble a gentle push and watched it glide.")
    hero.meters["gliding"] = 1.0
    propagate(world)
    world.para()
    world.say(f"Then came a surprise: {creature.surprise}.")
    hero.memes["surprise"] = 1.0
    hero.meters["transformed"] = 1.0
    world.say(f"The bubble popped, and the little {creature.label} transformed into a {creature.transformation}.")
    world.say(f"It looked new and bright, and the whole {place.label} seemed to smile.")
    world.facts["outcome"] = "transformed"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    creature: Creature = f["creature"]
    place: Place = f["place"]
    aid: Aid = f["aid"]
    return [
        f'Write an animal story that uses the words "bubble" and "glide" in {place.scene}.',
        f"Tell a short story about a {creature.label} with {aid.phrase} and a surprise transformation.",
        f"Write a gentle animal story where a {creature.label} makes a bubble glide and then changes into something new.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    creature: Creature = f["creature"]
    place: Place = f["place"]
    aid: Aid = f["aid"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about a little {creature.label} who spent time in the {place.label}. The creature was the one that made the story's bubble glide and then changed.",
        ),
        QAItem(
            question="What helped the bubble move?",
            answer=f"{aid.phrase} helped the bubble glide. It fit the scene because it was a safe helper for the bubble and the path through the {place.label}.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"The bubble popped, and the {creature.label} transformed into a {creature.transformation}. The ending shows the surprise by proving the creature was no longer the same.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bubble?",
            answer="A bubble is a light round skin of air or soap that floats for a little while and can pop when touched.",
        ),
        QAItem(
            question="What does glide mean?",
            answer="To glide means to move smoothly and gently, almost like sliding through the air or over water without bumping much.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form. It means something becomes new and different.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
bubble(hero) :- hero_animal(hero), has_bubble(hero).
glide(hero) :- bubble(hero), glide_path(place), chosen(place).
surprise(hero) :- glide(hero), surprise_event(hero).
transformed(hero) :- surprise(hero), changed(hero).
outcome(transformed) :- transformed(hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CREATURES:
        lines.append(asp.fact("hero_animal", cid))
    for pid in PLACES:
        lines.append(asp.fact("chosen", pid))
        lines.append(asp.fact("glide_path", pid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
        if AIDS[aid].gives_bubble:
            lines.append(asp.fact("has_bubble", "hero"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(show="#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    ok = bool(atoms)
    smoke = False
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        smoke = bool(sample.story)
    except Exception:
        smoke = False
    if ok and smoke:
        print("OK: ASP model and story generation smoke test passed.")
        return 0
    print("MISMATCH: verification failed.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show bubble/1.\n#show glide/1.\n#show surprise/1.\n#show transformed/1."))
    return sorted(set(asp.atoms(model, "bubble")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.animal not in CREATURES:
        raise StoryError("(Unknown animal.)")
    if args.place and args.place not in PLACES:
        raise StoryError("(Unknown place.)")
    if args.aid and args.aid not in AIDS:
        raise StoryError("(Unknown aid.)")
    animal = args.animal or rng.choice(list(CREATURES))
    place = args.place or rng.choice(list(PLACES))
    aid = args.aid or rng.choice(list(AIDS))
    creature = CREATURES[animal]
    if not (bubble_needed(creature, PLACES[place]) and AIDS[aid].gives_bubble and AIDS[aid].helps_glide):
        raise StoryError(reason_rejection(creature, PLACES[place], AIDS[aid]))
    return StoryParams(animal=animal, place=place, aid=aid)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show bubble/1.\n#show glide/1.\n#show surprise/1.\n#show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin is available; this tiny world always expects a transformed ending.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
