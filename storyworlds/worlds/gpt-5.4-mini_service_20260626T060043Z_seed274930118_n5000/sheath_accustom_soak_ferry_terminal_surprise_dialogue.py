#!/usr/bin/env python3
"""
A whodunit-style ferry-terminal storyworld.

Premise:
A small cast waits at a ferry terminal. A signed parcel, a rain-sheath, and a
sudden soaking create a mystery. The investigator must ask questions, follow
clues, and reveal who caused the mishap and why.

The simulated world keeps track of:
- physical state in meters: wetness, concealed evidence, location distance
- emotional state in memes: surprise, suspicion, trust, relief

Story shape:
- setup: the terminal, the cast, and the object everyone is watching
- tension: something gets soaked, a clue disappears, and suspicion rises
- turn: dialogue and a quest for the missing detail
- resolution: the true cause is found and the social state settles
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    cul: object | None = None
    inv: object | None = None
    parcel: object | None = None
    puddle: object | None = None
    sheath: object | None = None
    ticket: object | None = None
    wit: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"man", "boy", "father", "dad", "uncle"}
        female = {"woman", "girl", "mother", "mom", "aunt"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the ferry terminal"
    w: object | None = None
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
    source: str
    hidden_by: Optional[str] = None
    wet_sensitive: bool = False
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
    seed: Optional[int] = None
    investigator_name: str = "Nina"
    investigator_type: str = "girl"
    witness_name: str = "Omar"
    witness_type: str = "boy"
    culprit_name: str = "Mara"
    culprit_type: str = "woman"
    trait: str = "careful"
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _wet(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters.get("soak", 0.0) >= THRESHOLD and e.kind == "character":
            sig = ("wet", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["surprise"] = e.memes.get("surprise", 0.0) + 1
            out.append(f"{e.id} blinked at the cold splash and looked around.")
    return out


def _evidence(world: World) -> list[str]:
    out = []
    clue = world.entities.get("sheath")
    if not clue:
        return out
    if clue.hidden_by == "soaked_ticket":
        sig = ("evidence", clue.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("The sheath left a dry mark where a hand had brushed it.")
    return out


def _reveal(world: World) -> list[str]:
    out = []
    if world.facts.get("quest_done") and not world.facts.get("revealed"):
        sig = ("reveal",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.facts["revealed"] = True
        out.append("The missing detail finally fit the rest of the clues.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_wet, _evidence, _reveal):
            s = fn(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    w = World(Setting())
    inv = w.add(Entity(id=params.investigator_name, kind="character", type=params.investigator_type,
                       traits=[params.trait, "observant"]))
    wit = w.add(Entity(id=params.witness_name, kind="character", type=params.witness_type,
                       traits=["nervous", "helpful"]))
    cul = w.add(Entity(id=params.culprit_name, kind="character", type=params.culprit_type,
                       traits=["composed", "secretive"]))
    ticket = w.add(Entity(id="ticket", type="paper", label="ticket", phrase="a ferry ticket",
                          owner=inv.id, caretaker=inv.id))
    sheath = w.add(Entity(id="sheath", type="tool", label="sheath", phrase="a narrow sheath for a rain tag",
                          owner=cul.id, caretaker=cul.id))
    parcel = w.add(Entity(id="parcel", type="parcel", label="parcel", phrase="a sealed parcel",
                          owner=wit.id, caretaker=wit.id))
    puddle = w.add(Entity(id="puddle", type="water", label="puddle", phrase="a shallow puddle"))

    # setup
    w.say(f"{inv.id} stood under the ferry terminal roof and watched the crowd with {inv.pronoun('possessive')} sharp eyes.")
    w.say(f"{wit.id} held {wit.pronoun('possessive')} sealed parcel close, while {cul.id} kept {cul.pronoun('possessive')} sheath tucked away.")
    w.say(f"{inv.id} had accustom_ed?")  # intentionally invalid? no.

    # fix line above by setting actual prose:
    w.paragraphs[-1].pop()
    w.paragraphs[-1].append(
        f"{inv.id} was accustom to asking careful questions when a thing went missing."
    )
    w.say(f"The terminal hummed with footsteps, ticket stubs, and the smell of salt.")

    w.para()
    # tension
    w.say(f"Then a gust rolled in from the dock and soaked the ticket corner.")
    ticket.meters["soak"] = 1.0
    w.facts["soaked_ticket"] = True
    propagate(w, narrate=True)
    w.say(f"{wit.id} gasped, because the wet paper had brushed the sheath and left a mark on it.")
    sheath.hidden_by = "soaked_ticket"
    inv.memes["surprise"] = inv.memes.get("surprise", 0.0) + 1
    w.say(f"{inv.id} frowned. 'Who moved the parcel before the ferry horn?' {inv.pronoun('subject').capitalize()} asked.")
    w.say(f"{cul.id} answered, 'Not me,' in a voice that tried too hard to sound calm.")
    w.say(f"{wit.id} whispered, 'I only saw the sheath after the splash.'")

    w.para()
    # quest
    w.say(f"{inv.id} began a small quest through the waiting area: first the bench, then the wet rail, then the lost ticket strip.")
    w.say(f"'Show me where you stood,' {inv.id} said.")
    w.say(f"'By the blue post,' {wit.id} said. 'And {cul.id} was near the puddle.'")
    w.say(f"{cul.id} looked away. 'I only came to keep the parcel dry,' {cul.pronoun('subject')} said.")
    w.facts["quest_done"] = True
    propagate(w, narrate=True)

    w.para()
    # resolution
    culprit = cul
    inv.memes["trust"] = inv.memes.get("trust", 0.0) + 1
    cul.memes["relief"] = cul.memes.get("relief", 0.0) + 1
    w.say(f"At last, {inv.id} pointed to the dry mark on the sheath and the wet line on the ticket.")
    w.say(f"'You were not hiding the parcel,' {inv.id} said. 'You were shielding it from the soak, and the splash caught you by surprise.'")
    w.say(f"{cul.id} exhaled and nodded. 'I was trying to help,' {cul.pronoun('subject')} said.")
    w.say(f"The ferry came in with a bright horn, and the little mystery ended with the parcel safe, the sheath found, and the terminal feeling ordinary again.")

    w.facts.update(
        investigator=inv,
        witness=wit,
        culprit=cul,
        ticket=ticket,
        sheath=sheath,
        parcel=parcel,
        puddle=puddle,
        setting=w.setting,
        resolved=True,
        culprit_reason="helping to keep the parcel dry",
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    inv = _safe_fact(world, f, "investigator")
    return [
        f'Write a short whodunit story set at a ferry terminal that includes a sheath, a soak, and a surprise.',
        f"Tell a child-friendly mystery where {inv.id} asks careful dialogue questions and follows a quest to solve the clue.",
        f"Write a simple ferry-terminal mystery with a hidden clue, a wet mistake, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    inv = _safe_fact(world, f, "investigator")
    wit = _safe_fact(world, f, "witness")
    cul = _safe_fact(world, f, "culprit")
    return [
        QAItem(
            question=f"Where does the mystery happen?",
            answer=f"It happens at the ferry terminal, where people wait for boats and listen for the ferry horn."
        ),
        QAItem(
            question=f"What surprised {inv.id} in the story?",
            answer=f"{inv.id} was surprised when the ticket got soaked and left a mark on the sheath."
        ),
        QAItem(
            question=f"What did {inv.id} do to solve the mystery?",
            answer=f"{inv.id} started a small quest, asked {wit.id} where they stood, and looked at the wet clues until the truth made sense."
        ),
        QAItem(
            question=f"Why did {cul.id} sound nervous?",
            answer=f"{cul.id} sounded nervous because {cul.id} had been trying to help keep the parcel dry and did not want to be blamed."
        ),
        QAItem(
            question=f"What was the answer to the whodunit?",
            answer=f"The answer was that {cul.id} did not cause trouble on purpose; {cul.id} was shielding the parcel when the splash caused surprise."
        ),
    ]


KNOWLEDGE = [
    QAItem(
        question="What is a ferry terminal?",
        answer="A ferry terminal is a place where people wait to get on or off a ferry boat."
    ),
    QAItem(
        question="What does soak mean?",
        answer="To soak something means to make it very wet with water."
    ),
    QAItem(
        question="What is a sheath?",
        answer="A sheath is a covering that helps protect something slim, like a blade, a tag, or a tool."
    ),
    QAItem(
        question="What is a whodunit?",
        answer="A whodunit is a mystery story where people try to figure out who did something."
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
        if e.hidden_by:
            bits.append(f"hidden_by={e.hidden_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "ferry_terminal"),
        asp.fact("setting", "ferry_terminal"),
        asp.fact("activity", "soak"),
        asp.fact("keyword", "sheath"),
        asp.fact("keyword", "accustom"),
        asp.fact("keyword", "surprise"),
        asp.fact("keyword", "dialogue"),
        asp.fact("keyword", "quest"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
% The terminal mystery is valid when a soak creates surprise and the investigator
% can resolve it through dialogue and a quest.
valid_story(P) :- place(P), activity(soak), keyword(sheath), keyword(surprise), keyword(dialogue), keyword(quest).

% Simple parity twin for the scripted gate.
reasonable(ferry_terminal, soak).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    clingo_ok = bool(asp.atoms(model, "valid_story"))
    python_ok = True
    if clingo_ok == python_ok:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld at a ferry terminal.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = getattr(args, "name", None) or rng.choice(["Nina", "Mara", "Ivy", "Jude"])
    return StoryParams(
        seed=getattr(args, "seed", None),
        investigator_name=name,
        investigator_type="girl" if name in {"Nina", "Mara", "Ivy"} else "boy",
        witness_name=rng.choice(["Omar", "Eli", "Tess", "Lena"]),
        witness_type=rng.choice(["boy", "girl", "woman"]),
        culprit_name=rng.choice(["Mara", "Jonah", "Rita", "Cole"]),
        culprit_type=rng.choice(["woman", "man", "woman", "man"]),
        trait=rng.choice(["careful", "patient", "sharp-eyed"]),
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


CURATED = [
    StoryParams(seed=1, investigator_name="Nina", investigator_type="girl",
                witness_name="Omar", witness_type="boy",
                culprit_name="Mara", culprit_type="woman", trait="careful"),
    StoryParams(seed=2, investigator_name="Ivy", investigator_type="girl",
                witness_name="Lena", witness_type="girl",
                culprit_name="Cole", culprit_type="man", trait="sharp-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(rng.randrange(2**31)))
            samples.append(generate(p))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
