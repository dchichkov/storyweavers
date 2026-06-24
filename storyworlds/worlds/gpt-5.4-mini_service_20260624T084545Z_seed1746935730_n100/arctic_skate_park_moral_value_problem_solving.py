#!/usr/bin/env python3
"""
A small storyworld: an arctic skate park ghost story about moral value,
problem solving, and bravery.

Premise:
- A child visits a skate park in the arctic.
- A strange ghostly problem blocks the fun.
- Bravery and kindness lead to a safe solution.

The world is intentionally tiny and classical: a single premise, a tension,
and a resolution driven by physical meters and emotional memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    lantern: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
        if not hasattr(self, "_tags"):
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
    place: str = "the skate park"
    arctic: bool = True
    world: object | None = None
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Challenge:
    id: str
    danger: str
    obstacle: str
    clue: str
    fix: str
    tags: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

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
class Aid:
    id: str
    label: str
    effect: str
    covers: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def tell_world(hero_name: str, hero_type: str, parent_type: str, trait: str, challenge: Challenge) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    lantern = world.add(Entity(id="Lantern", type="lantern", label="lantern", phrase="a small lantern"))
    hero.memes["bravery"] = 0.0
    hero.memes["kindness"] = 0.0
    hero.memes["worry"] = 0.0
    hero.meters["cold"] = 0.0
    lantern.owner = hero.id

    world.say(
        f"{hero.id} was a {trait} {hero.type} who loved the {world.setting.place} on snowy days."
    )
    world.say(
        f"The air was arctic and sharp, and the ramps looked like pale fish bones under the sky."
    )
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {lantern.label} because the afternoon could turn ghostly fast."
    )
    world.para()

    hero.memes["curiosity"] = 1.0
    hero.memes["worry"] += 1.0
    world.say(
        f"At the park, {hero.id} noticed a strange chill near the tallest ramp."
    )
    world.say(
        f"A white whisper drifted over the rails, and the boards squeaked as if somebody unseen was skating."
    )
    world.say(
        f"Then the problem showed itself: {challenge.obstacle}."
    )
    world.say(
        f"The cold trouble was {challenge.danger}, and even brave children had to think carefully."
    )
    world.para()

    hero.memes["desire"] += 1.0
    world.say(
        f"{hero.id} wanted to help, but {hero.pronoun('possessive')} knees felt wobbly."
    )
    world.say(
        f"{hero.pronoun().capitalize()} remembered {challenge.clue} and took one careful breath."
    )
    hero.memes["bravery"] += 1.0
    world.say(
        f"With a brave step, {hero.id} skated closer instead of running away."
    )

    # Problem-solving beat
    world.say(
        f"{hero.id} looked around and solved the problem by using {challenge.fix}."
    )
    hero.memes["kindness"] += 1.0
    parent.memes["pride"] = 1.0
    world.say(
        f"{hero.id} shared the answer with {parent.label_word if hasattr(parent, 'label_word') else 'the parent'}, and the cold place felt less lonely."
    )

    # Resolution
    world.para()
    hero.meters["cold"] = 0.0
    world.say(
        f"The ghostly hush faded, and the skate park was just a skate park again."
    )
    world.say(
        f"{hero.id} rolled down the ramp with steady courage, and the lantern cast a warm circle on the snow."
    )
    world.say(
        f"{hero.id} had learned that moral value means doing the kind thing, even when the air feels spooky."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        lantern=lantern,
        challenge=challenge,
        setting=world.setting,
    )
    return world


CHALLENGES = {
    "frozen_ramp": Challenge(
        id="frozen_ramp",
        danger="a slick patch of ice that could make anyone fall",
        obstacle="the top ramp was glazed with hidden ice",
        clue="kindness and careful thinking could help",
        fix="sprinkling sand from a bucket and warning the others",
        tags={"arctic", "ice", "problem_solving", "bravery"},
    ),
    "lost_glove": Challenge(
        id="lost_glove",
        danger="a freezing wind that stole warmth from bare hands",
        obstacle="a glove had blown under the bench, and the child could not reach it",
        clue="small tools can solve big problems",
        fix="using a long skate stick to pull the glove back",
        tags={"arctic", "wind", "problem_solving"},
    ),
    "ghost_light": Challenge(
        id="ghost_light",
        danger="a trembling light that made the park seem haunted",
        obstacle="the lantern flickered and the path looked full of shadows",
        clue="bravery grows when you face the dark together",
        fix="standing beside the parent and holding the lantern steady",
        tags={"ghost", "bravery", "moral_value"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Owen"]
TRAITS = ["gentle", "curious", "brave", "kind", "thoughtful"]


@dataclass
class StoryParams:
    challenge: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Arctic skate park ghost storyworld.")
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    challenge = getattr(args, "challenge", None) or rng.choice(list(CHALLENGES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(challenge=challenge, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params.name, params.gender, params.parent, params.trait, _safe_lookup(CHALLENGES, params.challenge))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ch = f["challenge"]
    hero = f["hero"]
    return [
        f'Write a short ghost story for children set at {world.setting.place} in the arctic, featuring {hero.id} and a problem about {ch.id}.',
        f"Tell a gentle story about bravery and problem solving where {hero.id} faces something spooky at the skate park.",
        f'Write a story that includes the word "arctic" and ends with a warm, moral choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ch = f["challenge"]
    return [
        QAItem(
            question=f"Where does {hero.id} go in the story?",
            answer=f"{hero.id} goes to the skate park in the arctic.",
        ),
        QAItem(
            question=f"What spooky problem does {hero.id} face?",
            answer=f"{hero.id} faces {ch.obstacle}. It feels ghostly and cold.",
        ),
        QAItem(
            question=f"How does {hero.id} solve the problem?",
            answer=f"{hero.id} solves it by {ch.fix}. That shows problem solving and bravery.",
        ),
        QAItem(
            question=f"What moral value does {hero.id} show?",
            answer=f"{hero.id} shows kindness and courage by helping instead of hiding away.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does arctic mean?",
            answer="Arctic means very cold, like a place with snow, ice, and sharp wind.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel scared.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully and finding a useful way to fix a trouble.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of treating others, like kindness, honesty, or courage.",
        ),
    ]


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
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = []
    out.append("== Prompts ==")
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
challenge(arctic).
feature(moral_value).
feature(problem_solving).
feature(bravery).

valid_story(Place, Challenge) :- place(Place), challenge(Challenge), arctic_place(Place), feature(moral_value), feature(problem_solving), feature(bravery).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("place", "skate_park"),
        asp.fact("arctic_place", "skate_park"),
        asp.fact("challenge", "frozen_ramp"),
        asp.fact("challenge", "lost_glove"),
        asp.fact("challenge", "ghost_light"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("skate_park", cid) for cid in CHALLENGES}
    if atoms == py:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(py))
    return 1


CURATED = [
    StoryParams(challenge="frozen_ramp", name="Mia", gender="girl", parent="mother", trait="brave"),
    StoryParams(challenge="lost_glove", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(challenge="ghost_light", name="Nora", gender="girl", parent="mother", trait="thoughtful"),
]


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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1

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
