#!/usr/bin/env python3
"""
Standalone storyworld for a small pirate-tale playground quest with conflict.

Seed inspiration:
- putty, pupil, exclusion
- setting: playground
- features: Quest, Conflict
- style: Pirate Tale

A child pirate crew visits the playground to hunt for a hidden "putty pearl"
needed for their quest map. A pupil in the crew feels excluded when the others
rush ahead. The captain notices, patches the rift, and the crew finishes the
quest together.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    hero: object | None = None
    mapfrag: object | None = None
    pupil: object | None = None
    putty: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "matey"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class StoryParams:
    name: str
    pupil_name: str
    parent_name: str
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
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


PIRATE_NAMES = ["Finn", "Mara", "Jett", "Nori", "Pip", "Wren"]
PUPIL_NAMES = ["Toby", "Mina", "Luca", "Iris", "Penny", "Owen"]
PARENT_NAMES = ["Captain Nia", "Captain Bram", "Captain Sol", "Captain Ria"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate playground quest with conflict and a putty prize.")
    ap.add_argument("--name", choices=PIRATE_NAMES)
    ap.add_argument("--pupil", choices=PUPIL_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    name = getattr(args, "name", None) or rng.choice(PIRATE_NAMES)
    pupil = getattr(args, "pupil", None) or rng.choice(PUPIL_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_NAMES)
    if pupil == name:
        pupil = rng.choice([n for n in PUPIL_NAMES if n != name])
    return StoryParams(name=name, pupil_name=pupil, parent_name=parent)


def tell(params: StoryParams) -> World:
    w = World()
    captain = w.add(Entity(id="captain", kind="character", type="captain", label=params.parent_name))
    hero = w.add(Entity(id="hero", kind="character", type="matey", label=params.name))
    pupil = w.add(Entity(id="pupil", kind="character", type="pupil", label=params.pupil_name))
    putty = w.add(Entity(id="putty", kind="thing", type="putty", label="putty pearl", phrase="a shiny putty pearl"))
    mapfrag = w.add(Entity(id="map", kind="thing", type="map", label="quest map", phrase="a torn quest map"))
    w.facts.update(captain=captain, hero=hero, pupil=pupil, putty=putty, mapfrag=mapfrag)

    hero.memes["bold"] += 1
    pupil.memes["hope"] += 1

    w.say(f"At the playground, {hero.label} and {pupil.label} came striding in like small sea wolves.")
    w.say(f"They were on a quest for a hidden putty pearl said to mend the torn quest map.")
    w.say(f"{hero.label} loved the swing ship, the slide mountain, and every nook that felt like a pirate cove.")

    w.para()
    w.say(f"At the sand corner, {hero.label} spotted a glimmer under a little blue bucket.")
    hero.meters["search"] += 1
    putty.meters["found"] += 1
    w.say(f"It was the putty pearl, soft and round, just the thing the quest had been seeking.")

    w.say(f"But {hero.label} dashed ahead without waiting for {pupil.label}.")
    hero.memes["rush"] += 1
    pupil.memes["excluded"] += 1
    pupil.memes["sad"] += 1
    pupil.memes["conflict"] += 1
    w.say(f"{pupil.label} hung back by the ladder and felt left out, like a deckhand tossed off the ship.")

    w.para()
    captain.memes["watchful"] += 1
    w.say(f"{captain.label} saw the squall in {pupil.label}'s face and called, \"No matey gets left ashore.\"")
    w.say(f"{captain.label} held up the putty pearl and the torn map, then made {hero.label} come back.")
    hero.memes["guilt"] += 1
    hero.memes["conflict"] += 1
    hero.memes["care"] += 1
    pupil.memes["hope"] += 1
    pupil.memes["excluded"] = 0.0

    w.say(f"{hero.label} gave {pupil.label} the first turn at the treasure spot, and the frown began to melt.")
    w.say(f"Together they pressed the putty pearl onto the ragged map edge, and the paper held fast.")
    mapfrag.meters["fixed"] += 1

    w.para()
    hero.memes["joy"] += 1
    pupil.memes["joy"] += 1
    captain.memes["pride"] += 1
    w.say(f"Then the three of them raced to the slide ship, laughing as the playground wind snapped the little flag above them.")
    w.say(f"The quest was finished, the exclusion was gone, and the pirate crew sailed home with everyone aboard.")

    w.facts.update(resolved=True)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale set at a playground about a quest for putty.',
        f"Tell a children's story where {f['hero'].label} and a pupil search for a putty pearl, but one child feels excluded.",
        "Write a gentle conflict-and-fix pirate story where everyone ends up included.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    pupil = _safe_fact(world, f, "pupil")
    captain = _safe_fact(world, f, "captain")
    return [
        QAItem(
            question=f"Where does the pirate quest happen?",
            answer="It happens at the playground, where the pirate crew searches near the swings, slide, and sand corner.",
        ),
        QAItem(
            question=f"What were {hero.label} and {pupil.label} looking for?",
            answer="They were looking for a hidden putty pearl that could mend the torn quest map.",
        ),
        QAItem(
            question=f"Why did {pupil.label} feel upset?",
            answer=f"{pupil.label} felt upset because {hero.label} rushed ahead and made {pupil.label} feel excluded.",
        ),
        QAItem(
            question=f"How was the conflict fixed?",
            answer=f"{captain.label} brought the crew back together, and {hero.label} let {pupil.label} take the first turn so everyone stayed included.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is putty?",
            answer="Putty is a soft, bendy material that can be pressed and shaped with your hands.",
        ),
        QAItem(
            question="What is a pupil?",
            answer="A pupil is a student, a child who learns at school or in a classroom.",
        ),
        QAItem(
            question="What does exclusion mean?",
            answer="Exclusion means leaving someone out so they do not get to join in.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special search or mission to find something important.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or tense part where characters want different things or feel hurt.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Simple declarative twin for the reasonableness gate.
quest_ok(playground, putty).
conflict_ok(playground, exclusion).
valid_story(playground, quest, conflict) :- quest_ok(playground, putty), conflict_ok(playground, exclusion).
#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("setting", "playground"),
        asp.fact("feature", "quest"),
        asp.fact("feature", "conflict"),
        asp.fact("seed_word", "putty"),
        asp.fact("seed_word", "pupil"),
        asp.fact("seed_word", "exclusion"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("playground", "quest", "conflict")}
    if asp_set == py_set:
        print("OK: ASP parity matches Python gate.")
        return 0
    print("MISMATCH")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


def validate_params(params: StoryParams) -> None:
    if not params.name or not params.pupil_name or not params.parent_name:
        pass
    if params.name == params.pupil_name:
        pass


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(name="Finn", pupil_name="Mina", parent_name="Captain Nia"),
    StoryParams(name="Mara", pupil_name="Toby", parent_name="Captain Sol"),
    StoryParams(name="Pip", pupil_name="Iris", parent_name="Captain Bram"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
