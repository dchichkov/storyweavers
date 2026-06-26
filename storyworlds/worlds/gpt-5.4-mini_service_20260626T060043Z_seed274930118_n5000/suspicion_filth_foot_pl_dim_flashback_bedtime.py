#!/usr/bin/env python3
"""
A small bedtime-story world about a sleepy child, a little bit of filth, and a
gentle suspicion that turns into a remembered flashback.

Premise:
- At bedtime, a child notices a dim little smear on the floor near a foot.
- The child feels suspicion: who or what made the mess?
- A flashback reveals the source, and the child helps clean it up.
- The ending image proves the room is calm and ready for sleep.

The domain is intentionally tiny and classical:
- One setting: a bedroom at bedtime.
- One small physical clue: filth on or near the foot path.
- One emotional arc: suspicion -> memory -> understanding -> relief.

The story is driven by world state, not by a frozen paragraph.
"""

from __future__ import annotations

import argparse
import copy
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    clue_ent: object | None = None
    parent: object | None = None
    source: object | None = None
    def __post_init__(self) -> None:
        for key in ["filth", "tidy", "sleepiness"]:
            self.meters.setdefault(key, 0.0)
        for key in ["suspicion", "comfort", "curiosity", "relief", "worry"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the bedroom"
    bedtime: bool = True
    SETTING: object | None = None
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
class Clue:
    id: str
    label: str
    smell: str
    size: str
    place: str
    source: str
    flashback_line: str
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
    clue: str
    child_name: str
    child_type: str
    parent_type: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.flashback_used: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.flashback_used = self.flashback_used
        return clone


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    clue = _safe_fact(world, world.facts, "clue")
    if child.meters["filth"] < THRESHOLD:
        return out
    sig = ("smudge", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get(clue.source).meters["filth"] += 1
    out.append(f"A little filth settled near the foot of the bed.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    clue = _safe_fact(world, world.facts, "clue")
    if clue.source == "shoe":
        return out
    if child.memes["suspicion"] < THRESHOLD:
        return out
    sig = ("worry", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append("The little clue made the child wonder what had happened earlier.")
    return out


CAUSAL_RULES = [_r_smudge, _r_worry]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting()

CLUES = {
    "shoe": Clue(
        id="shoe",
        label="a sleepy little shoe",
        smell="dusty",
        size="small",
        place="beside the rug",
        source="shoe",
        flashback_line="Earlier, the shoe had slipped under the chair while the child was getting ready for bed.",
    ),
    "paw": Clue(
        id="paw",
        label="a tiny paw-print",
        smell="warm",
        size="small",
        place="by the pillow",
        source="cat",
        flashback_line="Earlier, the cat had climbed down from the windowsill with soft paws and a curious nose.",
    ),
    "cracker": Clue(
        id="cracker",
        label="a crumb trail",
        smell="sweet",
        size="tiny",
        place="along the floorboard",
        source="snack",
        flashback_line="Earlier, a bedtime cracker had broken apart in the child’s hand and left crumbs behind.",
    ),
}

CHILD_NAMES = ["Nina", "Luca", "Mina", "Toby", "Lily", "Noah"]
PARENT_TYPES = ["mother", "father"]


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        meters={"filth": 0.0, "tidy": 0.0, "sleepiness": 1.0},
        memes={"suspicion": 0.0, "comfort": 0.0, "curiosity": 0.0, "relief": 0.0, "worry": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="the parent",
        meters={"filth": 0.0, "tidy": 0.0, "sleepiness": 0.4},
        memes={"suspicion": 0.0, "comfort": 0.0, "curiosity": 0.0, "relief": 0.0, "worry": 0.0},
    ))
    clue = _safe_lookup(CLUES, params.clue)
    clue_ent = world.add(Entity(
        id="clue",
        type="clue",
        label=clue.label,
        phrase=clue.label,
        owner=child.id,
        region="footpath",
        meters={"filth": 1.0, "tidy": 0.0},
    ))
    source = world.add(Entity(
        id=clue.source,
        type="object" if clue.source in {"shoe", "snack"} else "animal",
        label={"shoe": "the shoe", "cat": "the cat", "snack": "the snack"}[clue.source],
        phrase={"shoe": "a little shoe", "cat": "the cat", "snack": "a bedtime snack"}[clue.source],
        meters={"filth": 0.0, "tidy": 1.0},
    ))
    world.facts.update(child=child, parent=parent, clue=clue_ent, source=source, clue_def=clue)

    world.say(f"It was bedtime in the bedroom, and {child.id} was already half in a dream.")
    world.say(f"Then {child.id} noticed {clue.label} near {clue.place}, and a tiny bit of suspicion woke up.")
    child.memes["suspicion"] += 1
    child.memes["curiosity"] += 1
    child.meters["filth"] += 1
    propagate(world)

    world.para()
    world.say(f"{child.id} looked again in the dim light and wondered who had left it there.")
    if clue.source == "cat":
        world.say(f"{parent.pronoun('subject').capitalize()} smiled and said the dark shape looked familiar.")
    else:
        world.say(f"{parent.pronoun('subject').capitalize()} knelt down and helped {child.pronoun('object')} think back.")
    world.say("That gentle wondering opened a flashback.")
    world.flashback_used = True
    world.say(f"Flashback: {clue.flashback_line}")
    child.memes["curiosity"] += 1

    world.para()
    world.say(f"Now the little mystery made sense.")
    child.memes["suspicion"] = 0.0
    child.memes["comfort"] += 1
    child.memes["relief"] += 1
    world.say(f"{child.id} helped clean the spot until the floor looked neat again.")
    world.get("clue").meters["filth"] = 0.0
    world.get(clue.source).meters["filth"] = 0.0
    source.meters["tidy"] += 1
    child.meters["tidy"] += 1
    world.say(f"Then {child.id} climbed back into bed, and the room felt soft and quiet.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    clue = _safe_fact(world, f, "clue_def")
    return [
        f'Write a bedtime story for a small child named {child.id} that begins with a dim clue and a little suspicion.',
        f"Tell a gentle story about {child.id} noticing {clue.label} near the bed, then remembering a flashback that explains it.",
        f'Write a calm bedtime tale that includes the words "suspicion", "filth", and a flashback near {clue.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    clue = _safe_fact(world, f, "clue_def")
    parent = _safe_fact(world, f, "parent")
    return [
        QAItem(
            question=f"What did {child.id} notice at bedtime?",
            answer=f"{child.id} noticed {clue.label} near {clue.place} in the dim bedroom.",
        ),
        QAItem(
            question=f"Why did {child.id} feel suspicion?",
            answer=f"{child.id} felt suspicion because the little clue did not make sense at first.",
        ),
        QAItem(
            question="What helped solve the little mystery?",
            answer=f"A flashback helped, because it showed what had happened earlier and made the clue easy to understand.",
        ),
        QAItem(
            question=f"What did {child.id} and {parent.id} do at the end?",
            answer=f"They cleaned the spot together and made the room ready for sleep again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short look back at something that happened earlier.",
        ),
        QAItem(
            question="Why do people clean filth before bed?",
            answer="People clean filth before bed so the room stays neat, comfortable, and ready for rest.",
        ),
        QAItem(
            question="What does suspicion mean?",
            answer="Suspicion is a feeling that something may have happened, even before you know the answer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  flashback_used={world.flashback_used}")
    return "\n".join(lines)


CURATED = [
    StoryParams(clue="shoe", child_name="Nina", child_type="girl", parent_type="mother"),
    StoryParams(clue="paw", child_name="Toby", child_type="boy", parent_type="father"),
    StoryParams(clue="cracker", child_name="Mina", child_type="girl", parent_type="mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: suspicion, filth, and a flashback.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=PARENT_TYPES)
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
    if getattr(args, "clue", None):
        clue = _safe_lookup(CLUES, getattr(args, "clue", None))
    else:
        clue = rng.choice(list(CLUES.values()))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    parent_type = getattr(args, "parent_type", None) or rng.choice(PARENT_TYPES)
    return StoryParams(
        clue=clue.id,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
child_feels_suspicion(C) :- child(C), clue_present(C), not understood(C).
flashback_needed(C) :- child_feels_suspicion(C).
flashback_happens(C) :- flashback_needed(C), remembered_source(C).
clean_end(C) :- flashback_happens(C), cleaned(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in CHILD_NAMES:
        lines.append(asp.fact("child_name", name))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("source_of", clue_id, clue.source))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_options() -> list[tuple[str, str]]:
    return [(c.id, c.source) for c in CLUES.values()]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    # Minimal parity check against Python registry.
    py = set(valid_story_options())
    model = asp.one_model(asp_program("#show source_of/2."))
    asp_set = set(asp.atoms(model, "source_of"))
    if asp_set == py:
        print(f"OK: ASP registry parity matches ({len(py)} options).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    print("only in ASP:", sorted(asp_set - py))
    print("only in Python:", sorted(py - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show source_of/2."))
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
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
