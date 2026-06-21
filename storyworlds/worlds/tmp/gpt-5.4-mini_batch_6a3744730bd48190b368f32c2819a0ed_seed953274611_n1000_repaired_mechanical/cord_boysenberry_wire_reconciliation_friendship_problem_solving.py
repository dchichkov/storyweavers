#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cord_boysenberry_wire_reconciliation_friendship_problem_solving.py
=================================================================================================

A small mystery-flavored storyworld about two friends, a tangled wire, a lost
boysenberry crate, and a careful reconciliation. The world uses typed entities
with physical meters and emotional memes, a forward causal model, a reasoned
reconciliation turn, and an inline ASP twin.

Seed words: cord, boysenberry, wire
Features: Reconciliation, Friendship, Problem Solving
Style: Mystery
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Setting:
    id: str
    place: str
    mood: str
    clue: str
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


@dataclass
class Problem:
    id: str
    description: str
    source: str
    cause: str
    clue: str
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
class Reconciliation:
    id: str
    sense: int
    power: int
    action: str
    result: str
    qa: str
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


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "role": v.role, "attrs": dict(v.attrs),
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_misread(world: World) -> list[str]:
    out = []
    case = world.facts.get("case")
    if not case:
        return out
    if case.meters["tension"] >= THRESHOLD and ("misread", case.id) not in world.fired:
        world.fired.add(("misread", case.id))
        for e in (world.get("milo"), world.get("suri")):
            e.memes["worry"] += 1
        out.append("__clue__")
    return out


def _r_discover(world: World) -> list[str]:
    out = []
    if world.get("wire").meters["pulled"] >= THRESHOLD and ("discover",) not in world.fired:
        world.fired.add(("discover",))
        world.get("crate").meters["found"] += 1
        out.append("__found__")
    return out


CAUSAL_RULES = [Rule("misread", _r_misread), Rule("discover", _r_discover)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def caution_gate(problem: Problem) -> bool:
    return "wire" in problem.tags and "boysenberry" in problem.tags


def sensible_reconciliations() -> list[Reconciliation]:
    return [r for r in RECONCILIATIONS.values() if r.sense >= SENSE_MIN]


def choose_path(problem: Problem, fix: Reconciliation) -> bool:
    return fix.power >= 1 and fix.sense >= SENSE_MIN and caution_gate(problem)


def tell_setting(world: World, setting: Setting, a: Entity, b: Entity) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"On a foggy afternoon, {a.id} and {b.id} wandered {setting.place}. "
        f"The place had {setting.mood}, and one odd clue kept catching their eyes: "
        f"{setting.clue}."
    )
    world.say(
        f"They were friends, and they liked solving little mysteries together."
    )


def introduce_problem(world: World, problem: Problem, a: Entity, b: Entity) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"Then they found the puzzle: {problem.description}. "
        f"{problem.clue} seemed to point somewhere, but nobody was sure where."
    )
    world.say(f"{a.id} said the answer felt hidden in plain sight.")


def warn(world: World, a: Entity, b: Entity, problem: Problem) -> None:
    world.say(
        f'{b.id} bit {b.pronoun("possessive")} lip. '
        f'"I think {problem.source} is tangled," {b.id} said. '
        f'"We should be careful and figure it out together."'
    )


def misread(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'{a.id} frowned. "No, look closer," {a.id} said, and reached for the wire.'
    )


def find_clue(world: World, problem: Problem) -> None:
    world.say(
        f"The wire gave a tiny tug, and the mystery shifted. The cord under the crate "
        f"was not the culprit after all; it was the loose wire beside it."
    )
    world.get("wire").meters["pulled"] += 1
    world.get("cord").meters["spotted"] += 1
    world.get("crate").meters["shaken"] += 1
    propagate(world, narrate=False)


def reconcile(world: World, a: Entity, b: Entity, problem: Problem, fix: Reconciliation) -> None:
    a.memes["humility"] += 1
    b.memes["trust"] += 1
    a.memes["trust"] += 1
    world.say(
        f"{a.id} stopped. {a.id} looked at {b.id}, then at the wire, and sighed. "
        f'"You were right," {a.id} said softly. "Let\'s solve it your way."'
    )
    world.say(
        f"{b.id} smiled, and the two friends leaned close over the crate, "
        f"working side by side."
    )
    world.say(
        f"They {fix.action}, and soon {fix.result}."
    )
    world.get("wire").meters["tied"] += 1
    world.get("cord").meters["secured"] += 1
    world.get("crate").meters["opened"] += 1
    world.get("crate").meters["found"] += 1
    world.get("crate").memes["relief"] += 1


def ending(world: World, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"Inside the crate, the boysenberries were safe and bright, like tiny purple lanterns. "
        f"The friends shared a laugh, untied the cord neatly, and left the wire in a tidy coil."
    )
    world.say(
        f"By the end, {a.id} and {b.id} were not just curious anymore; they were closer friends."
    )


SETTINGS = {
    "dock": Setting(id="dock", place="along the old dock", mood="salt wind and creaking boards", clue="a short cord looped around a nail"),
    "shed": Setting(id="shed", place="beside the garden shed", mood="dusty shelves and a sleepy door", clue="a cord hanging beside a wire basket"),
    "market": Setting(id="market", place="through the quiet market lane", mood="wooden stalls and whispery footsteps", clue="a cord tied near a crate of fruit"),
}

PROBLEMS = {
    "missing_crate": Problem(
        id="missing_crate",
        description="a crate of boysenberries had gone missing",
        source="the crate",
        cause="it was snagged by a wire",
        clue="The cord ended at a mark on the floor",
        tags={"boysenberry", "wire", "cord"},
    ),
    "stuck_lid": Problem(
        id="stuck_lid",
        description="the lid of the boysenberry box would not open",
        source="the lid",
        cause="a wire latch had caught it",
        clue="A cord was wrapped around the latch",
        tags={"boysenberry", "wire", "cord"},
    ),
    "mixed_messages": Problem(
        id="mixed_messages",
        description="a note about the boysenberries had been tied to the wrong wire",
        source="the note",
        cause="the cord had been swapped by mistake",
        clue="One cord was old and frayed",
        tags={"boysenberry", "wire", "cord"},
    ),
}

RECONCILIATIONS = {
    "untangle": Reconciliation(
        id="untangle",
        sense=3,
        power=2,
        action="untangled the wire, slipped the cord free, and checked the crate latch",
        result="the box opened with a soft click and the boysenberries were found",
        qa="untangled the wire and freed the cord",
        tags={"reconcile", "problem_solving"},
    ),
    "compare_clues": Reconciliation(
        id="compare_clues",
        sense=3,
        power=2,
        action="laid the cord, the wire, and the note side by side to compare the clues",
        result="the mismatch was clear and the missing boysenberries were traced at once",
        qa="compared the clues carefully",
        tags={"reconcile", "problem_solving"},
    ),
    "apologize_then_fix": Reconciliation(
        id="apologize_then_fix",
        sense=2,
        power=1,
        action="apologized for blaming each other and then checked the wire together",
        result="the tension eased and the crate was opened without another argument",
        qa="apologized and checked the wire together",
        tags={"reconcile", "friendship", "problem_solving"},
    ),
}

GIRL_NAMES = ["Mina", "Tess", "Ivy", "June", "Nora", "Wren"]
BOY_NAMES = ["Eli", "Owen", "Finn", "Milo", "Theo", "Ari"]
TRAITS = ["careful", "curious", "thoughtful", "gentle", "patient"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    fix: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for f in RECONCILIATIONS:
                if caution_gate(PROBLEMS[p]) and choose_path(PROBLEMS[p], RECONCILIATIONS[f]):
                    combos.append((s, p, f))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery-flavored friendship storyworld with cord, boysenberry, and wire.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=RECONCILIATIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if args.fix and args.fix not in RECONCILIATIONS:
        raise StoryError("Unknown fix.")
    if args.problem and args.fix and not choose_path(PROBLEMS[args.problem], RECONCILIATIONS[args.fix]):
        raise StoryError("That solution does not fit this mystery.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, fix = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl") if args.friend is None else (args.friend_gender or rng.choice(["girl", "boy"]))
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != hero]
    friend = args.friend or rng.choice(friend_pool)
    return StoryParams(setting=setting, problem=problem, fix=fix, hero=hero, hero_gender=hero_gender, friend=friend, friend_gender=friend_gender, trait=rng.choice(TRAITS))


def tell(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    friend = w.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend"))
    cord = w.add(Entity(id="cord", label="cord"))
    wire = w.add(Entity(id="wire", label="wire"))
    crate = w.add(Entity(id="crate", label="boysenberry crate"))
    w.facts.update(hero=hero, friend=friend, cord=cord, wire=wire, crate=crate,
                   setting=SETTINGS[params.setting], problem=PROBLEMS[params.problem],
                   fix=RECONCILIATIONS[params.fix], params=params)
    tell_setting(w, SETTINGS[params.setting], hero, friend)
    w.para()
    introduce_problem(w, PROBLEMS[params.problem], hero, friend)
    warn(w, hero, friend, PROBLEMS[params.problem])
    misread(w, hero, friend)
    find_clue(w, PROBLEMS[params.problem])
    w.para()
    reconcile(w, hero, friend, PROBLEMS[params.problem], RECONCILIATIONS[params.fix])
    ending(w, hero, friend)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a 3-to-5-year-old that includes the words "{f["setting"].clue.split()[0].lower()}", "cord", and "wire".',
        f"Tell a friendship story where {f['hero'].id} and {f['friend'].id} solve a boysenberry mystery together and make up after disagreeing.",
        "Write a gentle problem-solving mystery with a hidden boysenberry crate, a cord, and a wire, ending in reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, problem, fix = f["hero"], f["friend"], f["problem"], f["fix"]
    return [
        QAItem(question="Who are the story about?", answer=f"It is about {hero.id} and {friend.id}, two friends who work together to solve a mystery."),
        QAItem(question="What was the mystery?", answer=f"{problem.description.capitalize()}. The clues pointed to {problem.cause}, so they had to look carefully and solve it together."),
        QAItem(question="How did they make up?", answer=f"They used {fix.qa} and chose to work side by side again. That turned the disagreement into a friendship moment."),
        QAItem(question="What did they find at the end?", answer="They found the boysenberries and the story ended with the wire and cord neatly put away."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a cord?", answer="A cord is a thin, flexible length of material. People use cords to tie, pull, or hold things in place."),
        QAItem(question="What is a wire?", answer="A wire is a thin metal line. It can bend a little, but it is stronger and stiffer than a cord."),
        QAItem(question="What are boysenberries?", answer="Boysenberries are dark purple berries. They are small, juicy, and can be eaten as fruit."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,F) :- setting(S), problem(P), fix(F), caution_gate(P), fit(P,F).
fit(P,F) :- problem(P), fix(F).
outcome(reconciled) :- fit(P,F).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", p))
        for t in sorted(prob.tags):
            lines.append(asp.fact("tag", p, t))
    for f, fix in RECONCILIATIONS.items():
        lines.append(asp.fact("fix", f))
        lines.append(asp.fact("sense", f, fix.sense))
        lines.append(asp.fact("power", f, fix.power))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program("#show valid/3.")), "valid")))

def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, fix=None, hero=None, hero_gender=None, friend=None, friend_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams(setting="dock", problem="missing_crate", fix="untangle", hero="Milo", hero_gender="boy", friend="Nora", friend_gender="girl", trait="careful"),
    StoryParams(setting="shed", problem="stuck_lid", fix="compare_clues", hero="Ivy", hero_gender="girl", friend="Eli", friend_gender="boy", trait="curious"),
    StoryParams(setting="market", problem="mixed_messages", fix="apologize_then_fix", hero="Theo", hero_gender="boy", friend="June", friend_gender="girl", trait="gentle"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.fix not in RECONCILIATIONS:
        raise StoryError("Invalid params.")
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection() -> str:
    return "(No story: this combination does not support a believable mystery or reconciliation.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combinations:")
        for t in asp_valid_combos():
            print("  ", t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
