#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/parasol_calamine_behave_conflict_mystery_to_solve.py
====================================================================================

A standalone story world for a small space-adventure tale about a child crew,
a puzzling red rash, a stubborn quarrel, and a calm reconciliation.

Seed words:
- parasol
- calamine
- behave

Features:
- Conflict
- Mystery to Solve
- Reconciliation

This world keeps the action small and concrete: two young space travelers
explore a bright station garden dome, one gets itchy red spots after a misty
workbench spill, the other wants to rush the fix, and the grown-up helps them
solve the mystery, clean up safely, and make peace.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    view: str
    afford: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Object:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Mystery:
    id: str
    symptom: str
    source: str
    cause: str
    fix: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_worry(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in list(world.entities.values()):
            if other.kind == "character" and other.id != ent.id:
                other.memes["tension"] += 1
        out.append("__tension__")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    if world.facts.get("mystery_solved") and not world.facts.get("reconciled"):
        sig = ("relief")
        if sig not in world.fired:
            world.fired.add(sig)
            for ent in list(world.entities.values()):
                if ent.kind == "character":
                    ent.memes["relief"] += 1
                    ent.memes["tension"] = 0.0
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def suspicious_mist(world: World, mystery: Mystery, culprit: Object) -> dict:
    sim = world.copy()
    sim.get("mysterious_spot").meters["itch"] += 1
    sim.get("mysterious_spot").meters["red"] += 1
    return {
        "itch": sim.get("mysterious_spot").meters["itch"],
        "red": sim.get("mysterious_spot").meters["red"],
    }


def _do_mystery(world: World, site: Entity, mystery: Mystery, narrate: bool = True) -> None:
    site.meters["itch"] += 1
    site.meters["red"] += 1
    world.facts["symptom_seen"] = True
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, friend: Entity, setting: Setting, mystery: Mystery) -> None:
    child.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"On a bright day in {setting.place}, {child.id} and {friend.id} floated "
        f"through {setting.view} in their little ship like a pair of space explorers."
    )
    world.say(
        f"They had a {OBJECTS['parasol'].label} strapped by the hatch, a tin of "
        f"{OBJECTS['calamine'].label} in the kit, and a promise to {mystery.fix} if they could."
    )


def find_symptom(world: World, child: Entity, mystery: Mystery) -> None:
    world.say(
        f"Near the workbench, {child.id} noticed a strange {mystery.symptom}. "
        f"It looked like a tiny red map on {child.pronoun('possessive')} arm."
    )


def argue(world: World, child: Entity, friend: Entity, mystery: Mystery) -> None:
    child.memes["fear"] += 1
    friend.memes["defiance"] += 1
    world.say(
        f'"This is bad," {child.id} said. "We need to stay still and behave." '
        f'"No, we need to move fast," {friend.id} said, and their voices bounced off the dome.'
    )


def warn(world: World, parent: Entity, child: Entity, friend: Entity, mystery: Mystery) -> None:
    pred = suspicious_mist(world, mystery, OBJECTS["calamine"])
    world.facts["predicted_itch"] = pred["itch"]
    world.say(
        f"{parent.label_word.capitalize()} came over and peered at the red spots. "
        f'"Let’s solve the mystery first," {parent.pronoun()} said. '
        f'"Something in the mist probably made {child.id} itchy, and rubbing it will not help."'
    )


def open_parasol(world: World, parent: Entity) -> None:
    world.say(
        f"{parent.label_word.capitalize()} opened the {OBJECTS['parasol'].label} like a tiny shield "
        f"so the bright station lights would not sting the skin while they worked."
    )


def explain_calamine(world: World, parent: Entity, child: Entity, mystery: Mystery) -> None:
    world.say(
        f"Then {parent.label_word.capitalize()} dabbed on {OBJECTS['calamine'].label} from the kit. "
        f"It cooled the itch and helped the red spots settle down."
    )
    world.say(
        f'"That feels better," {child.id} said. "{child.id} can behave now."'
    )


def reconcile(world: World, parent: Entity, child: Entity, friend: Entity) -> None:
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.facts["reconciled"] = True
    world.say(
        f"After that, {child.id} and {friend.id} looked at each other, sighed, and smiled. "
        f"{parent.label_word.capitalize()} reminded them that friends can disagree and still be kind."
    )
    world.say(
        f'{friend.id} said sorry for hurrying. {child.id} said sorry for snapping back. '
        f"Then they bumped gloves and let the adventure continue."
    )


def ending(world: World, child: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"By the time they left {setting.place}, the red spots were smaller, the air was calm, "
        f"and the {OBJECTS['parasol'].label} folded shut beside the hatch like a safe little moon."
    )
    world.say(
        f"{child.id} and {friend.id} flew home together, quieter, kinder, and ready to behave."
    )


def tell(setting: Setting, mystery: Mystery, child_name: str = "Mina", child_gender: str = "girl",
         friend_name: str = "Jules", friend_gender: str = "boy", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the pilot"))
    spot = world.add(Entity(id="mysterious_spot", type="body", label="the red spot"))
    world.facts["mystery"] = mystery
    world.facts["setting"] = setting
    world.facts["child"] = child
    world.facts["friend"] = friend
    world.facts["parent"] = parent

    setup(world, child, friend, setting, mystery)
    world.para()
    find_symptom(world, child, mystery)
    argue(world, child, friend, mystery)
    warn(world, parent, child, friend, mystery)
    world.para()
    _do_mystery(world, spot, mystery, narrate=False)
    world.say(
        f"As soon as the itch showed up, everyone paused. They looked near the bench, the mist pipe, "
        f"and the little spill tray until the cause made sense."
    )
    explain_calamine(world, parent, child, mystery)
    reconcile(world, parent, child, friend)
    world.para()
    open_parasol(world, parent)
    ending(world, child, friend, setting)

    world.facts.update(
        symptom_seen=True,
        mystery_solved=True,
        reconciled=True,
        spot=spot,
    )
    return world


SETTINGS = {
    "dome": Setting("dome", "the station garden dome", "green vines under glass", {"mystery", "reconcile"}),
    "bay": Setting("bay", "the cargo bay", "bright crates and blinking tools", {"mystery", "reconcile"}),
    "deck": Setting("deck", "the observation deck", "wide windows and drifting stars", {"mystery", "reconcile"}),
}

OBJECTS = {
    "parasol": Object("parasol", "parasol", "a folded parasol"),
    "calamine": Object("calamine", "calamine", "a tin of calamine"),
}

MYSTERIES = {
    "mist": Mystery(
        "mist",
        symptom="itchy red spots",
        source="mist pipe",
        cause="a tickly garden mist",
        fix="find what made the itch and soothe it",
        tags={"mystery", "calamine"},
    ),
    "dust": Mystery(
        "dust",
        symptom="scratchy red specks",
        source="air vent",
        cause="dust from a repair tube",
        fix="find the dusty vent and calm the skin",
        tags={"mystery", "calamine"},
    ),
    "sap": Mystery(
        "sap",
        symptom="sticky red patches",
        source="moon-vine",
        cause="sweet sap from a moon-vine",
        fix="wash the sap and soothe the skin",
        tags={"mystery", "calamine"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Ari", "Lia", "Zia", "Tess"]
BOY_NAMES = ["Jules", "Pico", "Theo", "Ren", "Ollie", "Finn"]
TRAITS = ["careful", "curious", "gentle", "brave"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid in setting.afford:
            combos.append((sid, mid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure mystery story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child")
    ap.add_argument("--friend")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend_pool = [n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != child]
    friend = args.friend or rng.choice(friend_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, mystery, child, child_gender, friend, friend_gender, parent, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    c: Entity = f["child"]
    return [
        f'Write a space-adventure story for a 3-to-5-year-old that includes the words "parasol", "calamine", and "behave".',
        f"Tell a story where {c.id} and a friend find a mystery on a space station, argue a little, and then behave after a grown-up helps with {m.fix}.",
        f"Write a calm science-fiction story with conflict, a mystery to solve, and reconciliation, ending with the friends flying home together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c: Entity = f["child"]
    fr: Entity = f["friend"]
    parent: Entity = f["parent"]
    m: Mystery = f["mystery"]
    qa = [
        QAItem(
            question="What was the mystery in the story?",
            answer=f"It was a case of itchy red spots on {c.id}'s arm. The grown-up thought the mist pipe or something nearby might have caused it, so they looked carefully before guessing."
        ),
        QAItem(
            question="Why did the children argue?",
            answer=f"{c.id} wanted to slow down and behave, but {fr.id} wanted to rush. They were both worried, and that made their voices sharp for a moment."
        ),
        QAItem(
            question="How did the grown-up help?",
            answer=f"{parent.id} opened the parasol, checked the spot, and put on calamine to calm the itch. That helped them solve the mystery and made the upset feeling go away."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with reconciliation. {c.id} and {fr.id} apologized, felt better, and left the station calm and friendly."
        ),
    ]
    if f.get("mystery_solved"):
        qa.append(
            QAItem(
                question="What clue helped solve the mystery?",
                answer=f"The clue was that the red spots appeared right after the misty work area. That made the grown-up think the source was near the mist pipe rather than something the children had done on purpose."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parasol?",
            answer="A parasol is a light umbrella made for shade. People use it to block bright sun or soft lights."
        ),
        QAItem(
            question="What is calamine?",
            answer="Calamine is a soothing lotion for itchy skin. Grown-ups put it on small rashes or bug bites to help them feel better."
        ),
        QAItem(
            question="What does it mean to behave?",
            answer="To behave means to act in a kind, safe, and sensible way. It often means listening, using gentle hands, and following the rules."
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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("dome", "mist", "Mina", "girl", "Jules", "boy", "mother", "careful"),
    StoryParams("bay", "dust", "Theo", "boy", "Lia", "girl", "father", "gentle"),
    StoryParams("deck", "sap", "Ari", "girl", "Ren", "boy", "mother", "curious"),
]


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = tell(setting, mystery, params.child, params.child_gender, params.friend, params.friend_gender, params.parent)
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
mystery_solved :- symptom_seen.
reconciled :- mystery_solved.
valid(S, M) :- setting(S), mystery(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, parent=None, child=None, friend=None, child_gender=None, friend_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: default story generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def explain_rejection() -> str:
    return "(No story: this setting does not support the mystery, or the parts do not fit the small space-adventure domain.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, m in asp_valid_combos():
            print(f"  {s:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
