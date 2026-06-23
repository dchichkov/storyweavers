#!/usr/bin/env python3
"""
storyworlds/worlds/spray_pronunciation_slump_reconciliation_pirate_tale.py
=========================================================================

A tiny pirate-story world about a child crew member, a tricky pronunciation,
a low morale slump, and a reconciliation that brings the crew back together.

Seed inspiration:
- Pirate tale style
- Required words: spray, pronunciation, slump
- Feature: reconciliation
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
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)
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
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: set[str] = field(default_factory=set)
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


@dataclass
class Signal:
    id: str
    label: str
    phrase: str
    type: str
    helps_with: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    setting: Setting
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    apply: Callable[[World], list[str]]
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


def _r_spray(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("spray", 0.0) < THRESHOLD:
            continue
        sig = ("spray", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for item in list(world.entities.values()):
            if item.kind == "thing" and item.id.startswith("deck"):
                item.meters["wet"] = item.meters.get("wet", 0.0) + 1
        out.append("The deck got wet from the spray.")
    return out


def _r_slump(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("misunderstanding") and not world.facts.get("reconciled"):
        for actor in world.characters():
            actor.memes["slump"] = actor.memes.get("slump", 0.0) + 1
        out.append("The crew's hearts sank into a slump.")
    return out


CAUSAL_RULES = [Rule("spray", _r_spray), Rule("slump", _r_slump)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affordances:
            for sig in SIGNALS:
                if act_id == "spray" and sig == "pronunciation":
                    combos.append((place, act_id, sig))
    return combos


@dataclass
class StoryParams:
    place: str = ""
    activity: str = ""
    signal: str = ""
    captain: str = ""
    mate: str = ""
    child: str = ""
    child_gender: str = ""
    parent: str = ""
    trait: str = ""
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


SETTINGS = {
    "ship": Setting(place="the pirate ship", affordances={"spray", "practice"}),
    "harbor": Setting(place="the harbor", affordances={"spray", "practice"}),
}

ACTIVITIES = {
    "spray": Activity(
        id="spray",
        verb="watch the waves spray the deck",
        gerund="watching the waves spray the deck",
        risk="wet wood and a shaky mood",
        zone={"deck"},
        tags={"spray", "sea"},
    ),
}

SIGNALS = {
    "pronunciation": Signal(
        id="pronunciation",
        label="pronunciation",
        phrase="the pronunciation of the pirate word",
        type="lesson",
        helps_with={"slump"},
        tags={"pronunciation"},
    )
}

GIRL_NAMES = ["Mira", "Luna", "Nina", "Ivy", "Rosa"]
BOY_NAMES = ["Finn", "Toby", "Jett", "Owen", "Pip"]
TRAITS = ["brave", "curious", "cheery", "stubborn", "gentle"]


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale that uses the words "spray", "pronunciation", and "slump".',
        f"Tell a story where {f['child'].id} hears the sea spray, struggles with pronunciation, and learns to speak kindly again.",
        f"Write a gentle pirate story with a misunderstanding, a slump in morale, and a reconciliation at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    mate = f["mate"]
    captain = f["captain"]
    sig = f["signal"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What made the deck wet in the story?",
            answer=f"The sea spray made the deck wet. That happened while the crew was out on {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {child.id} struggle with pronunciation?",
            answer=f"{child.id} was trying to say the pirate word clearly, but the pronunciation was tricky. {mate.id} helped by saying it slowly and kindly.",
        ),
        QAItem(
            question=f"Why did the crew's mood slump?",
            answer=f"The mood slumped because the crew misunderstood one another and felt cross for a little while. The slump did not last because they talked it through.",
        ),
        QAItem(
            question=f"How did the reconciliation happen?",
            answer=f"{captain.id} listened, {mate.id} apologized, and {child.id} tried the pronunciation again. That reconciled the crew and brought back their cheer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is spray?",
            answer="Spray is a fine spray of water that flies through the air in tiny drops. On a pirate ship, spray from the sea can make the deck wet.",
        ),
        QAItem(
            question="What does pronunciation mean?",
            answer="Pronunciation is how you say a word out loud. A clear pronunciation helps other people understand you.",
        ),
        QAItem(
            question="What is a slump?",
            answer="A slump is a drop downward, or a low spell in how someone feels. In a story, a mood slump means the crew feels less cheerful for a while.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


def tell(setting: Setting, activity: Activity, signal: Signal,
         child_name: str, child_gender: str, mate_name: str,
         mate_gender: str, captain_gender: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", meters={"spray": 0.0}, memes={"joy": 0.0, "slump": 0.0}))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender,
                            role="mate", meters={"spray": 0.0}, memes={"joy": 0.0, "slump": 0.0}))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_gender,
                               role="captain", label="the captain", meters={}, memes={}))
    deck = world.add(Entity(id="deck", kind="thing", label="deck", meters={"wet": 0.0}, memes={}))

    world.facts.update(child=child, mate=mate, captain=captain, signal=signal, activity=activity)
    child.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(f"{child.id} and {mate.id} stood on the pirate ship with {trait} hearts.")
    world.say(f"They watched the sea spray leap over the rail and tap the deck.")

    world.para()
    child.meters["spray"] += 1
    propagate(world, narrate=True)
    world.say(f"{child.id} tried to copy the crew's pronunciation of a hard pirate word.")
    world.say(f"{mate.id} laughed too sharply, and the friendly moment turned into a slump.")

    world.para()
    world.facts["misunderstanding"] = True
    propagate(world, narrate=True)
    world.say(f"The captain noticed the slump and called the crew together.")
    world.say(f'{captain.id} said, "We can fix this with patience, not pride."')
    world.say(f"{mate.id} apologized, and {child.id} tried the pronunciation again, slowly and clearly.")

    world.para()
    world.facts["reconciled"] = True
    child.memes["slump"] = 0.0
    mate.memes["slump"] = 0.0
    child.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(f"The apology landed gently, and the whole crew felt the reconciliation warm them up.")
    world.say(f"By the end, the spray still glittered on the rails, but the deck felt bright again.")
    return world


CURATED = [
    StoryParams(place="ship", activity="spray", signal="pronunciation", captain="Captain", mate="Mina",
                child="Pip", child_gender="boy", parent="mother", trait="gentle", seed=1),
    StoryParams(place="harbor", activity="spray", signal="pronunciation", captain="Captain", mate="Rosa",
                child="Mira", child_gender="girl", parent="father", trait="cheery", seed=2),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "spray"
    signal = args.signal or "pronunciation"
    if (place, activity, signal) not in valid_combos():
        raise StoryError("(No valid combination matches the given options.)")
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    mate_gender = "girl" if child_gender == "boy" else "boy"
    mate = args.mate or rng.choice(GIRL_NAMES if mate_gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    captain = "Captain"
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, signal=signal, captain=captain, mate=mate,
                       child=child, child_gender=child_gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.activity not in ACTIVITIES or params.signal not in SIGNALS:
        raise StoryError("invalid story parameters")
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], SIGNALS[params.signal],
                 params.child, params.child_gender, params.mate,
                 "girl" if params.mate and params.mate[0] in "AEIOU" else "boy",
                 "boy", params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with spray, pronunciation, and slump.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child")
    ap.add_argument("--mate")
    ap.add_argument("--parent", choices=["mother", "father"])
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


ASP_RULES = r"""
valid(P,A,S) :- place(P), activity(A), signal(S), combo(P,A,S).
reconciled :- misunderstanding, apology, listening.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for s in SIGNALS:
        lines.append(asp.fact("signal", s))
    lines.append(asp.fact("combo", "ship", "spray", "pronunciation"))
    lines.append(asp.fact("combo", "harbor", "spray", "pronunciation"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("ASP/Python mismatch")
    sample = generate(CURATED[0])
    _ = sample.story
    _ = sample.to_json()
    if ok:
        print("OK")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
