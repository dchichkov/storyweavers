#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/encompass_doctor_dialogue_fairy_tale.py
==============================================================================================

A small fairy-tale storyworld where a doctor helps a tiny enchanted friend
through a spoken worry, a careful checkup, and a fitting remedy.

Seed image:
- A gentle doctor in a mossy cottage hears a fairy's trouble.
- Their dialogue reveals a problem that can be safely encompassed by the right
  magical treatment.
- The ending proves what changed: the fairy feels better, and the village is
  calm again.

This world is constraint-checked and deterministic from its sampled params.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "fairy"}
        masculine = {"boy", "man", "father", "doctor"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Condition:
    id: str
    sign: str
    discomfort: str
    whisper: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    softening: str
    covers: set[str] = field(default_factory=set)
    eases: set[str] = field(default_factory=set)
    prep: str = ""
    finish: str = ""


@dataclass
class StoryParams:
    place: str
    condition: str
    remedy: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_bits.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "cottage": Setting("the mossy cottage", indoors=True, affords={"checkup", "rest"}),
    "glade": Setting("the moonlit glade", indoors=False, affords={"checkup", "rest"}),
    "bridge": Setting("the little stone bridge", indoors=False, affords={"checkup"}),
}

CONDITIONS = {
    "cough": Condition(
        id="cough",
        sign="a cough",
        discomfort="hoarse and tired",
        whisper="kept coughing into a tiny sleeve",
        tags={"sick", "breath"},
    ),
    "sprain": Condition(
        id="sprain",
        sign="a sore wing",
        discomfort="wincing and lopsided",
        whisper="held one wing very still",
        tags={"hurt", "wing"},
    ),
    "fever": Condition(
        id="fever",
        sign="a fever",
        discomfort="hot and sleepy",
        whisper="burned with a moon-sick warmth",
        tags={"sick", "warm"},
    ),
}

REMEDIES = {
    "tea": Remedy(
        id="tea",
        label="herbal tea",
        phrase="a steaming cup of herbal tea",
        softening="the warm tea soothed the throat",
        eases={"cough", "fever"},
        prep="brew a cup of herbal tea",
        finish="sipped the tea until the tightness faded",
    ),
    "wrap": Remedy(
        id="wrap",
        label="a wing wrap",
        phrase="a soft wing wrap with silver thread",
        softening="the wrap held the wing steady and safe",
        covers={"wing"},
        eases={"sprain"},
        prep="fetch a soft wing wrap",
        finish="rested beneath the wrap as if tucked into a cradle",
    ),
    "honey": Remedy(
        id="honey",
        label="honey spoon",
        phrase="a spoonful of honey",
        softening="the honey made the cough gentler",
        eases={"cough"},
        prep="stir a spoonful of honey",
        finish="licked the sweet honey and smiled",
    ),
    "blanket": Remedy(
        id="blanket",
        label="a warm blanket",
        phrase="a warm blanket woven with stars",
        softening="the blanket kept the fever from biting so hard",
        eases={"fever"},
        covers={"body"},
        prep="bring a warm blanket",
        finish="rested under the stars-patterned blanket",
    ),
}

NAMES = ["Mira", "Elsa", "Nell", "Ivy", "Lina", "Rose", "Pip", "Wren", "Tobin", "Hugo"]
HELPER_NAMES = ["Doctor Alder", "Doctor Rowan", "Doctor Fern", "Doctor Hazel"]
TYPES = ["girl", "boy", "fairy", "fox"]
HELPER_TYPES = ["doctor", "doctor", "doctor", "doctor"]
TRAITS = ["gentle", "brave", "curious", "merry", "soft-spoken"]

CURATED = [
    StoryParams("cottage", "cough", "tea", "Mira", "fairy", "Doctor Alder", "doctor"),
    StoryParams("glade", "sprain", "wrap", "Pip", "fairy", "Doctor Rowan", "doctor"),
    StoryParams("bridge", "fever", "blanket", "Nell", "girl", "Doctor Fern", "doctor"),
]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A remedy is reasonable if it eases the condition.
reasonable(R,C) :- eases(R,C).

% A remedy can be chosen in a place if the place affords the needed care.
available(P,C,R) :- affords(P,care), reasonable(R,C).

% A story is valid if the chosen remedy fits the condition.
valid_story(P,C,R) :- available(P,C,R), reasonable(R,C).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    out: list[str] = []
    for pid, setting in SETTINGS.items():
        out.append(asp.fact("place", pid))
        if setting.indoors:
            out.append(asp.fact("indoors", pid))
        for a in sorted(setting.affords):
            out.append(asp.fact("affords", pid, a))
    for cid, c in CONDITIONS.items():
        out.append(asp.fact("condition", cid))
        for t in sorted(c.tags):
            out.append(asp.fact("tagged", cid, t))
    for rid, r in REMEDIES.items():
        out.append(asp.fact("remedy", rid))
        for c in sorted(r.eases):
            out.append(asp.fact("eases", rid, c))
        for cov in sorted(r.covers):
            out.append(asp.fact("covers", rid, cov))
    return "\n".join(out)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def asp_valid_triples() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_triples() -> list[tuple[str, str, str]]:
    out = []
    for p in SETTINGS:
        for c in CONDITIONS:
            for r in REMEDIES:
                if c in REMEDIES[r].eases and p in SETTINGS and "checkup" in SETTINGS[p].affords:
                    out.append((p, c, r))
    return out


def asp_verify() -> int:
    a = set(asp_valid_triples())
    b = set(valid_triples())
    if a == b:
        print(f"OK: clingo gate matches valid_triples() ({len(a)} triples).")
        return 0
    print("MISMATCH between clingo and Python:")
    print(" only in clingo:", sorted(a - b))
    print(" only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_check(place: str, condition: str, remedy: str) -> None:
    if condition not in CONDITIONS:
        raise StoryError("Unknown condition.")
    if remedy not in REMEDIES:
        raise StoryError("Unknown remedy.")
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if condition not in REMEDIES[remedy].eases:
        raise StoryError(f"No story: {REMEDIES[remedy].label} does not honestly ease {condition}.")
    if "checkup" not in SETTINGS[place].affords:
        raise StoryError("No story: this place cannot host the doctor's careful checkup.")


def choose_from_registry(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.condition and args.condition not in CONDITIONS:
        raise StoryError("Unknown condition.")
    if args.remedy and args.remedy not in REMEDIES:
        raise StoryError("Unknown remedy.")

    candidates = []
    for p, c, r in valid_triples():
        if args.place and p != args.place:
            continue
        if args.condition and c != args.condition:
            continue
        if args.remedy and r != args.remedy:
            continue
        candidates.append((p, c, r))
    if not candidates:
        raise StoryError("No valid combination matches the given options.")

    place, condition, remedy = rng.choice(sorted(candidates))
    hero_type = args.hero_type or rng.choice(["fairy", "girl", "boy", "fox"])
    hero_name = args.hero_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or "doctor"
    return StoryParams(place, condition, remedy, hero_name, hero_type, helper_name, helper_type)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        traits=[rng_trait(params.hero_name)],
        meters={"health": 1.0, "comfort": 1.0},
        memes={"worry": 0.0, "hope": 0.0, "trust": 0.0},
    ))
    doctor = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="doctor",
        label=params.helper_name,
        meters={"skill": 1.0, "care": 1.0},
        memes={"calm": 1.0, "kindness": 1.0},
    ))
    condition = CONDITIONS[params.condition]
    remedy = REMEDIES[params.remedy]
    ailment = world.add(Entity(
        id="condition",
        type=params.condition,
        label=condition.sign,
        phrase=condition.whisper,
        meters={"severity": 1.0},
        memes={"trouble": 1.0},
    ))
    tool = world.add(Entity(
        id="remedy",
        type=params.remedy,
        label=remedy.label,
        phrase=remedy.phrase,
        owner=doctor.id,
    ))
    world.facts.update(hero=hero, doctor=doctor, ailment=ailment, remedy=tool, params=params)
    return world


def rng_trait(name: str) -> str:
    return random.choice(TRAITS)


def diagnose(world: World) -> None:
    h = world.facts["hero"]
    d = world.facts["doctor"]
    c = world.facts["ailment"]
    h.memes["worry"] += 1
    h.memes["hope"] += 0.5
    world.say(f'In {world.setting.place}, {h.id} said, "Doctor, I feel {CONDITIONS[c.type].discomfort}."')
    world.say(f'{d.id} listened closely and replied, "Let me look. Your trouble is {c.label}."')


def choose_remedy(world: World) -> None:
    h = world.facts["hero"]
    d = world.facts["doctor"]
    r = world.facts["remedy"]
    world.say(f'{d.id} smiled. "Then I will {REMEDIES[r.type].prep}," {d.id} said.')
    world.say(f'{h.id} answered, "Will it help me?"')
    world.say(f'"Yes," said {d.id}, "because it can encompass the whole worry that is making you feel bad."')
    h.memes["trust"] += 1


def apply_remedy(world: World) -> None:
    h = world.facts["hero"]
    d = world.facts["doctor"]
    c = world.facts["ailment"]
    r = world.facts["remedy"]
    c.meters["severity"] = 0.0
    h.meters["health"] = 1.0
    h.memes["worry"] = 0.0
    h.memes["hope"] = 1.0
    world.say(f"{d.id} gave the care with steady hands. {REMEDIES[r.type].softening.capitalize()}.")
    if "wing" in REMEDIES[r.type].covers:
        world.say(f'The wrap could encompass both wings without hurting the sore one.')
    world.say(f'{h.id} said, "Oh! That feels much better."')


def ending(world: World) -> None:
    h = world.facts["hero"]
    d = world.facts["doctor"]
    r = world.facts["remedy"]
    world.say(
        f"By evening, {h.id} was bright-eyed again, and {REMEDIES[r.type].finish}. "
        f'{d.id} said, "A small hurt needs a careful heart."'
    )
    world.say(f'{h.id} laughed, and the little place felt peaceful once more.')


def tell(params: StoryParams) -> World:
    world = build_world(params)
    diagnose(world)
    world.para()
    choose_remedy(world)
    apply_remedy(world)
    world.para()
    ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    h = world.facts["hero"]
    d = world.facts["doctor"]
    c = world.facts["ailment"]
    r = world.facts["remedy"]
    return [
        f'Write a fairy-tale story with dialogue where {d.id} helps {h.id} with {c.label}.',
        f'Write a short child-friendly tale that uses the word "encompass" and ends with {h.id} feeling better.',
        f'Write a story set at {p.place} where a doctor chooses {r.label} for a careful checkup.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    h = world.facts["hero"]
    d = world.facts["doctor"]
    c = world.facts["ailment"]
    r = world.facts["remedy"]
    return [
        QAItem(
            question=f"Who went to the doctor at {p.place}?",
            answer=f"{h.id} went to {d.id} at {p.place} because {h.id} had {c.label}.",
        ),
        QAItem(
            question=f"What did the doctor choose to help {h.id}?",
            answer=f"{d.id} chose {r.label}, which was a gentle remedy for {c.label}.",
        ),
        QAItem(
            question='What word did the doctor use about the worry?',
            answer='The doctor said the care could "encompass the whole worry," meaning it could cover the problem well.',
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is a doctor for?",
        answer="A doctor helps look after sick or hurt people and gives careful treatment to help them feel better.",
    ),
    QAItem(
        question="What does encompass mean?",
        answer="To encompass something means to include it fully or cover it all the way around.",
    ),
    QAItem(
        question="Why do people rest when they are sick?",
        answer="Rest gives the body time and energy to heal, so the person can get better more safely.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"facts={list(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale doctor dialogue storyworld.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--condition", choices=sorted(CONDITIONS))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy", "fairy", "fox"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["doctor"])
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
    return choose_from_registry(args, rng)


def generate(params: StoryParams) -> StorySample:
    reasonableness_check(params.place, params.condition, params.remedy)
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


def valid_story_triples() -> list[tuple[str, str, str]]:
    out = []
    for p in SETTINGS:
        for c in CONDITIONS:
            for r in REMEDIES:
                if c in REMEDIES[r].eases and "checkup" in SETTINGS[p].affords:
                    out.append((p, c, r))
    return out


def asp_verify_world() -> int:
    a = set(asp_valid_triples())
    b = set(valid_story_triples())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} triples).")
        return 0
    print("MISMATCH")
    print("only in ASP:", sorted(a - b))
    print("only in Python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify_world())
    if args.asp:
        triples = asp_valid_triples()
        for t in triples:
            print(t)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.hero_name} at {p.place} ({p.condition} -> {p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
