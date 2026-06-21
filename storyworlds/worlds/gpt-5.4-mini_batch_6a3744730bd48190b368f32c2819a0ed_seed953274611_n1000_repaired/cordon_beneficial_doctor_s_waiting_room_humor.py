#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cordon_beneficial_doctor_s_waiting_room_humor.py
=================================================================================

A small storyworld in a doctor's waiting room, told with a fairy-tale feel and
humorous, state-driven consequences.

Premise:
- A child visits a doctor's waiting room and gets tempted to use a harmless
  "cordon" in a silly way.
- A kind helper notices the benefit of a better choice.
- The room's state changes through patience, gentleness, and a beneficial fix.

This script follows the shared storyworld contract:
- stdlib only
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CALM_MIN = 1.0


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
    plural: bool = False
    gentle: bool = False
    beneficial: bool = False
    cordon: bool = False
    humorous: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "nurse"}
        male = {"boy", "father", "dad", "man", "doctor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "doctor": "doctor", "nurse": "nurse"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Room:
    id: str
    name: str
    seats: int
    cordoned_spot: str
    quiet_rule: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class StoryParams:
    room: str
    cordon: str
    beneficial: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    doctor: str
    doctor_type: str
    mood: str = "wobbly"
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


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
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
        clone = World(copy.deepcopy(self.room))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not hero or not helper:
        return out
    if hero.memes["wobble"] < THRESHOLD:
        return out
    sig = ("calm", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.room.memes["quiet"] += 1
    helper.memes["cheer"] += 1
    out.append("__calm__")
    return out


def _r_benefit(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    if not helper or helper.meters["benefit"] < THRESHOLD:
        return out
    sig = ("benefit", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.room.meters["order"] += 1
    out.append("__benefit__")
    return out


RULES = [Rule("calm", _r_calm), Rule("benefit", _r_benefit)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def room_requires_cordon(room: Room) -> bool:
    return bool(room.cordoned_spot)


def cordon_is_reasonable(cordon: str, room: Room) -> bool:
    return cordon in CORDONS and room_requires_cordon(room)


def beneficial_is_reasonable(beneficial: str) -> bool:
    return beneficial in BENEFICIALS and BENEFICIALS[beneficial].kind in {"kind", "funny", "calm"}


def is_resolved(world: World) -> bool:
    return world.room.meters["order"] >= THRESHOLD and world.room.memes["quiet"] >= THRESHOLD


def predict_world(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").memes["wobble"] += 1
    propagate(sim, narrate=False)
    return {
        "quiet": sim.room.memes["quiet"],
        "order": sim.room.meters["order"],
    }


def intro(world: World, hero: Entity, helper: Entity, doctor: Entity) -> None:
    world.say(
        f"In a doctor's waiting room with {world.room.seats} little chairs, {hero.id} "
        f"sat under a painted sign that said {world.room.quiet_rule}."
    )
    world.say(
        f"{hero.id} had the sort of face that said both 'I am brave' and 'I am also bored'. "
        f"{helper.id} sat nearby like a tiny guardian of manners, and {doctor.id} kept the desk tidy."
    )


def temptation(world: World, hero: Entity, cordon: str) -> None:
    hero.memes["wobble"] += 1
    world.say(
        f"Then {hero.id} noticed a little {cordon} by the chairs and thought it looked "
        f"grand enough for a coronation, or at least a very serious game."
    )
    world.say(
        f'"What a splendid ribbon of space!" {hero.id} said. "I could march around it like a knight."'
    )


def warn(world: World, helper: Entity, hero: Entity, cordon: str, doctor: Entity) -> None:
    pred = predict_world(world)
    helper.memes["care"] += 1
    world.facts["predicted_quiet"] = pred["quiet"]
    world.say(
        f'{helper.id} smiled in a helpful way. "That {cordon} is for keeping the room calm, '
        f"not for tiptoeing through. {doctor.label_word.capitalize()} likes it because it helps "
        f"everyone wait in peace."'
    )
    world.say(
        f'"If we use it properly, the whole room stays more beneficial for the little coughs, '
        f"the big sneezes, and the grumpy sighs."'
    )


def attempt(world: World, hero: Entity, cordon: str) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"Still, {hero.id} gave the {cordon} a solemn bow and tried to spin it like a royal sash."
    )


def accept_help(world: World, hero: Entity, helper: Entity, beneficial: str) -> None:
    helper.meters["benefit"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"Then {helper.id} pointed to the chair corner and suggested a {beneficial} game instead."
    )
    world.say(
        f'{hero.id} blinked, then laughed. "Why, that is better than my whole parade!"'
    )


def ending(world: World, hero: Entity, helper: Entity, doctor: Entity, beneficial: str) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.room.meters["order"] += 1
    world.say(
        f"In the end, {hero.id} sat neatly again, {helper.id} counted the chairs, and {doctor.id} nodded "
        f"as if this were exactly the sort of magic a waiting room needed."
    )
    world.say(
        f"The {beneficial} idea proved its worth: the room stayed calm, the line of patients stayed polite, "
        f"and even the clock seemed less cross."
    )


def tell(room: Room, cordon: str, beneficial: str, hero: str, hero_type: str,
         helper: str, helper_type: str, doctor: str, doctor_type: str, mood: str) -> World:
    world = World(room)
    h = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero, role="child", traits=[mood], humorous=True))
    he = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper, role="helper", gentle=True, beneficial=True))
    d = world.add(Entity(id="doctor", kind="character", type=doctor_type, label=doctor, role="doctor", gentle=True))
    intro(world, h, he, d)
    world.para()
    temptation(world, h, cordon)
    warn(world, he, h, cordon, d)
    attempt(world, h, cordon)
    world.para()
    accept_help(world, h, he, beneficial)
    propagate(world, narrate=False)
    ending(world, h, he, d, beneficial)
    world.facts.update(
        hero=h,
        helper=he,
        doctor=d,
        cordon=cordon,
        beneficial=beneficial,
        room=room,
        outcome="resolved" if is_resolved(world) else "unresolved",
        predicted_quiet=world.facts.get("predicted_quiet", 0.0),
    )
    return world


ROOMS = {
    "waiting_room": Room(
        id="waiting_room",
        name="doctor's waiting room",
        seats=5,
        cordoned_spot="a little taped-off corner by the window",
        quiet_rule="Please use whisper voices",
    ),
    "clinic_lobby": Room(
        id="clinic_lobby",
        name="clinic lobby",
        seats=4,
        cordoned_spot="a small cordon near the fish tank",
        quiet_rule="Please keep the room calm",
    ),
}

CORDONS = {
    "tape": {
        "label": "yellow tape cordon",
        "noun": "cordon",
        "reason": "it keeps people from bumping the sore ankle chair",
        "tags": {"cordon", "humor"},
    },
    "rope": {
        "label": "red rope cordon",
        "noun": "cordon",
        "reason": "it marks the quiet corner like a tiny castle wall",
        "tags": {"cordon", "humor"},
    },
    "cones": {
        "label": "two bright cones and a cordon",
        "noun": "cordon",
        "reason": "it makes a very official-looking line",
        "tags": {"cordon", "humor"},
    },
}

BENEFICIALS = {
    "whisper_game": {
        "kind": "kind",
        "label": "whisper game",
        "benefit": "helps everyone keep their voices low",
        "tags": {"beneficial", "humor"},
    },
    "chair_count": {
        "kind": "funny",
        "label": "chair-counting game",
        "benefit": "turns waiting into a game",
        "tags": {"beneficial", "humor"},
    },
    "breathing": {
        "kind": "calm",
        "label": "slow-breath game",
        "benefit": "helps a wiggly body feel settled",
        "tags": {"beneficial", "calm"},
    },
}

HEROES = ["Mina", "Owen", "Pip", "Luna", "Nico", "Ivy"]
HELPERS = ["Mara", "Toby", "Clara", "Felix", "Nell"]
DOCTORS = ["Doctor Bright", "Doctor Willow", "Doctor Quill"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room_id, room in ROOMS.items():
        for cordon in CORDONS:
            for beneficial in BENEFICIALS:
                if cordon_is_reasonable(cordon, room) and beneficial_is_reasonable(beneficial):
                    combos.append((room_id, cordon, beneficial))
    return combos


@dataclass
class StoryParams:
    room: str
    cordon: str
    beneficial: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    doctor: str
    doctor_type: str
    mood: str = "wobbly"
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale style story set in a doctor's waiting room that uses the words "{f["cordon"]}" and "{f["beneficial"]}".',
        f"Tell a humorous little tale where {f['hero'].id} notices a {f['cordon']} in the waiting room and learns a {f['beneficial']} way to wait calmly.",
        f'Write a child-friendly story in a clinic lobby about a cordon, a helpful idea, and a peaceful ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    doctor = f["doctor"]
    qa = [
        QAItem(
            question="Where does the story take place?",
            answer="It takes place in a doctor's waiting room, where the chairs are lined up and everyone is waiting their turn."
        ),
        QAItem(
            question="What did the child notice?",
            answer=f"{hero.id} noticed a {f['cordon']} and wanted to treat it like part of a royal game. That silly idea is what made the moment funny."
        ),
        QAItem(
            question="How did the helper make things better?",
            answer=f"{helper.id} suggested a {f['beneficial']} game instead. That choice helped the room stay calmer and gave the child a better way to wait."
        ),
        QAItem(
            question="Why was the doctor's waiting room more peaceful at the end?",
            answer="The child stopped fussing with the cordon and chose a calmer game. Because of that, the room stayed quiet enough for everyone to wait without trouble."
        ),
    ]
    if f.get("outcome") == "resolved":
        qa.append(
            QAItem(
                question="What proved that the new idea worked?",
                answer=f"{doctor.id} could keep the desk tidy while the room stayed orderly. The ending image shows the chairs, the voices, and the waiting all settled down."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["cordon"], world.facts["beneficial"], "humor"}
    out = []
    if "cordon" in tags:
        out.append(QAItem(
            question="What is a cordon?",
            answer="A cordon is a line or boundary that keeps people from wandering into a spot. It helps a place stay safe and orderly."
        ))
    if "beneficial" in tags:
        out.append(QAItem(
            question="What does beneficial mean?",
            answer="Beneficial means helpful or good for the situation. A beneficial idea makes things work better for people nearby."
        ))
    out.append(QAItem(
        question="Why can waiting room games be helpful?",
        answer="Waiting room games can keep children calm while they wait for the doctor. A calm game also helps the room stay quiet."
    ))
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.humorous:
            bits.append("humorous")
        if e.gentle:
            bits.append("gentle")
        if e.beneficial:
            bits.append("beneficial")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  room: {world.room.name} meters={dict(world.room.meters)} memes={dict(world.room.memes)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(room="waiting_room", cordon="tape", beneficial="whisper_game", hero="Mina", hero_type="girl", helper="Mara", helper_type="woman", doctor="Doctor Bright", doctor_type="doctor", mood="wobbly"),
    StoryParams(room="waiting_room", cordon="rope", beneficial="chair_count", hero="Owen", hero_type="boy", helper="Toby", helper_type="boy", doctor="Doctor Willow", doctor_type="doctor", mood="curious"),
    StoryParams(room="clinic_lobby", cordon="cones", beneficial="breathing", hero="Pip", hero_type="boy", helper="Clara", helper_type="girl", doctor="Doctor Quill", doctor_type="doctor", mood="silly"),
]


def explain_rejection(cordon: str, beneficial: str) -> str:
    if cordon not in CORDONS:
        return "(No story: that cordon is not known in this little world.)"
    if beneficial not in BENEFICIALS:
        return "(No story: that helpful idea is not in this little world.)"
    return "(No story: this combination does not make a reasonable waiting-room tale.)"


def outcome_of(params: StoryParams) -> str:
    return "resolved"


ASP_RULES = r"""
has_calm :- helpful(_, beneficial).
room_stays_ordered :- has_calm.
outcome(resolved) :- room_stays_ordered.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for cid in CORDONS:
        lines.append(asp.fact("cordon", cid))
    for bid in BENEFICIALS:
        lines.append(asp.fact("helpful", bid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale-like humorous waiting-room storyworld.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--cordon", choices=CORDONS)
    ap.add_argument("--beneficial", choices=BENEFICIALS)
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
              if (args.room is None or c[0] == args.room)
              and (args.cordon is None or c[1] == args.cordon)
              and (args.beneficial is None or c[2] == args.beneficial)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, cordon, beneficial = rng.choice(sorted(combos))
    hero_type = rng.choice(["girl", "boy"])
    helper_type = rng.choice(["girl", "boy", "woman"])
    doctor_type = "doctor"
    hero = rng.choice(HEROES)
    helper = rng.choice(HELPERS)
    doctor = rng.choice(DOCTORS)
    return StoryParams(
        room=room,
        cordon=cordon,
        beneficial=beneficial,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        doctor=doctor,
        doctor_type=doctor_type,
        mood=rng.choice(["wobbly", "curious", "silly"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError("unknown room")
    if params.cordon not in CORDONS:
        raise StoryError("unknown cordon")
    if params.beneficial not in BENEFICIALS:
        raise StoryError("unknown beneficial idea")
    world = tell(
        room=copy.deepcopy(ROOMS[params.room]),
        cordon=params.cordon,
        beneficial=params.beneficial,
        hero=params.hero,
        hero_type=params.hero_type,
        helper=params.helper,
        helper_type=params.helper_type,
        doctor=params.doctor,
        doctor_type=params.doctor_type,
        mood=params.mood,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} with {p.cordon} and {p.beneficial} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
