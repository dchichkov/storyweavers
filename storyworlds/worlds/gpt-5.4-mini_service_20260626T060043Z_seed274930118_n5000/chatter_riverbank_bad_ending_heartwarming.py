#!/usr/bin/env python3
"""
A small storyworld set on a riverbank, built from a seed tale about chatter,
a warm little bond, and a bad ending that still feels tender in the moment.

The domain:
- a child and a caregiver visit a riverbank
- a talkative animal or toy can become the chatter source
- the child wants to keep a found treasure
- the river is gentle, but the ending is bad: the treasure is lost
- the emotional style stays heartwarming, even as the ending hurts
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

    caregiver: object | None = None
    child: object | None = None
    creature: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
    name: str
    gender: str
    caregiver: str
    creature: str
    treasure: str
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


CHARACTER_REGISTRY = {
    "girl": ["Mina", "Luna", "Ivy", "Nora", "Elsie"],
    "boy": ["Finn", "Owen", "Toby", "Eli", "Noah"],
}
CAREGIVER_REGISTRY = {
    "mother": "mom",
    "father": "dad",
}
CREATURES = {
    "duck": "a small duck with bright eyes",
    "frog": "a little frog with a soft voice",
    "sparrow": "a tiny sparrow that liked to gossip",
    "cricket": "a cricket that chirped like it had secrets",
}
TREASURES = {
    "red stone": "a smooth red stone",
    "shell": "a shiny shell",
    "feather": "a pale feather",
    "button": "a round blue button",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming riverbank storyworld with a bad ending.")
    ap.add_argument("--name", choices=sum(CHARACTER_REGISTRY.values(), []))
    ap.add_argument("--gender", choices=list(CHARACTER_REGISTRY))
    ap.add_argument("--caregiver", choices=list(CAREGIVER_REGISTRY))
    ap.add_argument("--creature", choices=list(CREATURES))
    ap.add_argument("--treasure", choices=list(TREASURES))
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHARACTER_REGISTRY[gender])
    caregiver = getattr(args, "caregiver", None) or rng.choice(list(CAREGIVER_REGISTRY))
    creature = getattr(args, "creature", None) or rng.choice(list(CREATURES))
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    return StoryParams(name=name, gender=gender, caregiver=caregiver, creature=creature, treasure=treasure)


def riverbank_scene(world: World) -> None:
    child = world.get("child")
    caregiver = world.get("caregiver")
    creature = world.get("creature")
    treasure = world.get("treasure")

    world.say(f"On the riverbank, {child.id} walked beside {caregiver.label_word}, listening to the water and the reeds.")
    world.say(f"A little {creature.type} kept up a soft chatter, as if the banks were a place for sharing tiny secrets.")
    world.say(f"{child.id} found {treasure.phrase} near a flat stone and lifted {treasure.it()} with careful fingers.")
    child.memes["love"] = child.memes.get("love", 0.0) + 1
    child.memes["hope"] = child.memes.get("hope", 0.0) + 1


def tension(world: World) -> None:
    child = world.get("child")
    caregiver = world.get("caregiver")
    treasure = world.get("treasure")
    creature = world.get("creature")

    world.para()
    world.say(f'The {creature.type} chattered again, and {child.id} smiled, but {child.id} kept stepping closer to the water with {treasure.it()}.')
    world.say(f'{caregiver.label_word.capitalize()} called softly, "Keep your shoes on the dry stones, and don’t lean over too far."')
    child.memes["want"] = child.memes.get("want", 0.0) + 1
    child.memes["reckless"] = child.memes.get("reckless", 0.0) + 0.5
    caregiver.memes["worry"] = caregiver.memes.get("worry", 0.0) + 1


def bad_ending(world: World) -> None:
    child = world.get("child")
    caregiver = world.get("caregiver")
    treasure = world.get("treasure")
    creature = world.get("creature")

    world.para()
    world.say(f"{child.id} turned to listen to one more line of chatter from the little {creature.type}.")
    world.say(f"Then {child.id} slipped on the wet edge of the bank, and {treasure.it()} tumbled into the river.")
    world.say(f'{caregiver.label_word.capitalize()} caught {child.pronoun("object")} before the water did, and held {child.pronoun("object")} close.')
    world.say(f"They watched the treasure spin away under the bright surface, and the river kept carrying it until it was gone.")
    child.memes["sadness"] = child.memes.get("sadness", 0.0) + 2
    child.memes["loss"] = child.memes.get("loss", 0.0) + 2
    caregiver.memes["comfort"] = caregiver.memes.get("comfort", 0.0) + 1
    world.facts["lost"] = True


def warm_close(world: World) -> None:
    child = world.get("child")
    caregiver = world.get("caregiver")
    treasure = world.get("treasure")
    creature = world.get("creature")

    world.say(f"{caregiver.label_word.capitalize()} kissed the top of {child.pronoun('possessive')} head and said they could remember the treasure together.")
    world.say(f"The little {creature.type} went quiet at last, as if it understood that some losses were too big for chatter.")
    world.say(f"{child.id} still felt sad, but {child.id} held {caregiver.pronoun('object')} hand on the walk home, and that made the evening feel soft around the edges.")
    world.say(f"Even without {treasure.it()}, {child.id} had a warm hand to hold and a story to keep.")


def tell(params: StoryParams) -> World:
    world = World(place="the riverbank")
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=params.caregiver, label=CAREGIVER_REGISTRY[params.caregiver]))
    creature = world.add(Entity(id="creature", kind="character", type=params.creature, label=params.creature))
    treasure = world.add(Entity(id="treasure", type="thing", label=params.treasure, phrase=_safe_lookup(TREASURES, params.treasure), owner=child.id, caretaker=caregiver.id))
    world.facts.update(child=child, caregiver=caregiver, creature=creature, treasure=treasure)
    riverbank_scene(world)
    tension(world)
    bad_ending(world)
    warm_close(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    treasure = _safe_fact(world, f, "treasure")
    return [
        'Write a short heartwarming story for a young child set on a riverbank that includes chatter and ends badly.',
        f"Tell a gentle story about {child.id} on a riverbank who finds {treasure.phrase} and loses {treasure.it()} in the river.",
        "Write a child-friendly story where a small chatty creature, a parent, and a found treasure lead to a sad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    caregiver = _safe_fact(world, f, "caregiver")
    treasure = _safe_fact(world, f, "treasure")
    creature = _safe_fact(world, f, "creature")
    return [
        QAItem(
            question=f"Where did {child.id} find {treasure.it()}?",
            answer=f"{child.id} found {treasure.it()} on the riverbank near a flat stone.",
        ),
        QAItem(
            question=f"Who kept chattering in the story?",
            answer=f"The little {creature.type} kept chattering and made the moment feel busy and alive.",
        ),
        QAItem(
            question=f"What did {caregiver.label_word} do when {child.id} slipped?",
            answer=f"{caregiver.label_word.capitalize()} caught {child.pronoun('object')} before {child.pronoun('subject')} could fall into the river.",
        ),
        QAItem(
            question=f"What happened to {treasure.it()} at the end?",
            answer=f"{treasure.it().capitalize()} slipped into the river and was carried away, so it was lost.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a riverbank?", answer="A riverbank is the land right beside a river."),
        QAItem(question="Why can riverbanks be slippery?", answer="Riverbanks can be slippery because the ground near water can be wet and muddy."),
        QAItem(question="What does chatter mean?", answer="Chatter means quick, busy talking, often in little bits and pieces."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
child(X) :- hero(X).
treasure(T) :- found(T).
bad_ending :- lost(treasure).
heartwarming :- comforted(child).
valid_story :- child(_), treasure(_), bad_ending, heartwarming.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    return "\n".join([
        asp.fact("hero", "child"),
        asp.fact("found", "treasure"),
        asp.fact("lost", "treasure"),
        asp.fact("comforted", "child"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP twin recognizes the story shape.")
        return 0
    print("MISMATCH: ASP twin did not derive valid_story.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:9} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(g, c, t) for g in CHARACTER_REGISTRY for c in CREATURES for t in TREASURES]


CURATED = [
    StoryParams(name="Mina", gender="girl", caregiver="mother", creature="duck", treasure="shell"),
    StoryParams(name="Finn", gender="boy", caregiver="father", creature="cricket", treasure="red stone"),
    StoryParams(name="Ivy", gender="girl", caregiver="mother", creature="sparrow", treasure="feather"),
]


def resolve_restrictions(args: argparse.Namespace) -> None:
    if getattr(args, "name", None) and getattr(args, "gender", None):
        if getattr(args, "name", None) not in CHARACTER_REGISTRY[getattr(args, "gender", None)]:
            pass


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


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    resolve_restrictions(args)
    gender = getattr(args, "gender", None) or rng.choice(list(CHARACTER_REGISTRY))
    name = getattr(args, "name", None) or rng.choice(CHARACTER_REGISTRY[gender])
    caregiver = getattr(args, "caregiver", None) or rng.choice(list(CAREGIVER_REGISTRY))
    creature = getattr(args, "creature", None) or rng.choice(list(CREATURES))
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    return StoryParams(name=name, gender=gender, caregiver=caregiver, creature=creature, treasure=treasure)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = build_story_params(args, random.Random(seed))
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
