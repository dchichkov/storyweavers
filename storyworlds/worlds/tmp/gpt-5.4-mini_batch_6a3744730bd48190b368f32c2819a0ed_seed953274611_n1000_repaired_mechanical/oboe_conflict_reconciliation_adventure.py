#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/oboe_conflict_reconciliation_adventure.py
=========================================================================

A small storyworld about an adventurous child, a borrowed oboe, a conflict in a
stormy cave, and a reconciliation that ends with music again.

The domain is intentionally tiny: one explorer, one helper, one instrument, one
problem, and one safe resolution. Stories are generated from live world state
rather than by swapping nouns into a frozen paragraph.

Run:
    python storyworlds/worlds/gpt-5.4-mini/oboe_conflict_reconciliation_adventure.py
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    dark_feature: str
    adventure_hook: str
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
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    delicate: bool = True
    playable_in_rain: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class ConflictBeat:
    id: str
    tension: int
    text: str
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
class ReconciliationPlan:
    id: str
    wisdom: int
    text: str
    qa_text: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    instrument: str
    conflict: str
    reconciliation: str
    storm: int = 0
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
    "cave": Setting(id="cave", place="a sea cave", dark_feature="the black tunnel", adventure_hook="to find the hidden map"),
    "forest": Setting(id="forest", place="a pine forest", dark_feature="the shadow path", adventure_hook="to find the silver bridge"),
    "harbor": Setting(id="harbor", place="a windy harbor trail", dark_feature="the cliff path", adventure_hook="to reach the old lighthouse"),
}

INSTRUMENTS = {
    "oboe": Instrument(id="oboe", label="oboe", phrase="a polished oboe", sound="soft and bright at once", delicate=True, playable_in_rain=False),
    "flute": Instrument(id="flute", label="flute", phrase="a small flute", sound="clear as water", delicate=True, playable_in_rain=True),
    "drum": Instrument(id="drum", label="drum", phrase="a travel drum", sound="steady as footsteps", delicate=False, playable_in_rain=True),
}

CONFLICTS = {
    "argument": ConflictBeat(id="argument", tension=2, text="a sharp argument about the best path"),
    "fear": ConflictBeat(id="fear", tension=1, text="a scared hush when the wind rose"),
    "lost_note": ConflictBeat(id="lost_note", tension=2, text="a broken note that made both travelers frown"),
}

RECONCILIATIONS = {
    "apology": ReconciliationPlan(id="apology", wisdom=2, text="the hero apologized and offered the instrument carefully to the companion", qa_text="apologized and shared the oboe carefully"),
    "listen": ReconciliationPlan(id="listen", wisdom=3, text="they slowed down, listened to each other, and found a safer route together", qa_text="slowed down and found a safer route together"),
    "duet": ReconciliationPlan(id="duet", wisdom=3, text="they played a tiny duet after making peace, and the tune pointed them onward", qa_text="played a tiny duet after making peace"),
}

HERO_NAMES = [("Maya", "girl"), ("Leo", "boy"), ("Nina", "girl"), ("Finn", "boy")]
COMPANION_NAMES = [("Ari", "boy"), ("Zoe", "girl"), ("Tess", "girl"), ("Owen", "boy")]


def hazard_ok(setting: Setting, instrument: Instrument, storm: int) -> bool:
    return bool(setting.place) and bool(instrument.label) and storm >= 0


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in INSTRUMENTS:
            for c in CONFLICTS:
                combos.append((s, i, c))
    return combos


ASP_RULES = r"""
valid(S,I,C) :- setting(S), instrument(I), conflict(C).
safe(I) :- instrument(I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for i in INSTRUMENTS:
        lines.append(asp.fact("instrument", i))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH:")
        print(" only in python:", sorted(py - cl))
        print(" only in clingo:", sorted(cl - py))
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about an oboe, conflict, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--reconciliation", choices=RECONCILIATIONS)
    ap.add_argument("--storm", type=int, choices=[0, 1, 2])
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
    if args.instrument == "oboe" and args.storm == 2:
        pass
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid adventure story combinations.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    instrument = args.instrument or rng.choice(sorted(INSTRUMENTS))
    conflict = args.conflict or rng.choice(sorted(CONFLICTS))
    reconciliation = args.reconciliation or rng.choice(sorted(RECONCILIATIONS))
    storm = args.storm if args.storm is not None else rng.randint(0, 2)
    if not hazard_ok(SETTINGS[setting], INSTRUMENTS[instrument], storm):
        raise StoryError("Invalid parameters for this adventure.")
    hero = args.hero or rng.choice([n for n, g in HERO_NAMES])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    companion = args.companion or rng.choice([n for n, g in COMPANION_NAMES if n != hero])
    companion_gender = args.companion_gender or rng.choice(["girl", "boy"])
    return StoryParams(setting=setting, hero=hero, hero_gender=hero_gender, companion=companion, companion_gender=companion_gender, instrument=instrument, conflict=conflict, reconciliation=reconciliation, storm=storm)


def _pick_entity(name: str, gender: str, role: str) -> Entity:
    return Entity(id=name, kind="character", type=gender, role=role, traits=["adventurous"], attrs={"role": role})


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    instrument = INSTRUMENTS[params.instrument]
    conflict = CONFLICTS[params.conflict]
    plan = RECONCILIATIONS[params.reconciliation]
    world = World()
    hero = world.add(_pick_entity(params.hero, params.hero_gender, "hero"))
    companion = world.add(_pick_entity(params.companion, params.companion_gender, "companion"))
    hero.memes["curiosity"] += 1
    companion.memes["trust"] += 1
    world.say(f"{hero.id} and {companion.id} set out through {setting.place} {setting.adventure_hook}.")
    world.say(f"{hero.id} carried {instrument.phrase}, because {instrument.label} was {hero.pronoun('possessive')} favorite adventure instrument.")
    world.para()
    if params.storm > 0:
        hero.memes["worry"] += params.storm
        companion.memes["worry"] += 1
        world.say(f"Then the wind snapped through {setting.dark_feature}, and the travelers met {conflict.text}.")
    else:
        world.say(f"Even so, {conflict.text} still grew between them when they disagreed about the way forward.")
    if instrument.id == "oboe":
        world.say(f"{hero.id} tried to blow the oboe, but the wet air made the tone tremble.")
        hero.meters["effort"] += 1
    world.para()
    if plan.id == "apology":
        hero.memes["regret"] += 1
        companion.memes["relief"] += 1
        world.say(f"{hero.id} looked down, said sorry, and {plan.text}.")
        world.say(f"The companion nodded, and the path felt less like a fight and more like a shared quest.")
    elif plan.id == "listen":
        hero.memes["calm"] += 1
        companion.memes["calm"] += 1
        world.say(f"After a deep breath, they {plan.text}.")
        world.say(f"That choice brought them closer, and the map details finally made sense.")
    else:
        hero.memes["joy"] += 1
        companion.memes["joy"] += 1
        world.say(f"They made peace, then {plan.text}.")
        world.say(f"The little tune echoed ahead, and the cave path seemed to answer back.")
    world.say(f"In the end, {hero.id} held the oboe steady, {companion.id} smiled, and the adventure went on together.")
    world.facts.update(setting=setting, instrument=instrument, conflict=conflict, plan=plan, hero=hero, companion=companion, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write an adventure story that includes the word oboe and ends with reconciliation.",
        f"Tell a child-friendly adventure about {world.facts['hero'].id} and {world.facts['companion'].id} in {world.facts['setting'].place}.",
        "Write a story where a conflict over an oboe turns into a peaceful reunion.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    comp = f["companion"]
    instrument = f["instrument"]
    plan = f["plan"]
    return [
        QAItem(question="Who went on the adventure?", answer=f"{hero.id} and {comp.id} went on the adventure together."),
        QAItem(question="What instrument was in the story?", answer=f"The story included an oboe, and {hero.id} carried {instrument.phrase}."),
        QAItem(question="How did the conflict end?", answer=f"It ended when they reconciled: they {plan.qa_text}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an oboe?", answer="An oboe is a woodwind instrument that makes a bright, reedy sound when you blow into it."),
        QAItem(question="Why can a storm make travel harder?", answer="A storm can make the path wet, noisy, and harder to see, so travelers need to slow down and stay careful."),
        QAItem(question="What does reconciliation mean?", answer="Reconciliation means people stop fighting, make peace, and choose to work together again."),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.instrument not in INSTRUMENTS or params.conflict not in CONFLICTS or params.reconciliation not in RECONCILIATIONS:
        raise StoryError("Unknown story parameter.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="cave", hero="Maya", hero_gender="girl", companion="Ari", companion_gender="boy", instrument="oboe", conflict="argument", reconciliation="apology", storm=1),
    StoryParams(setting="forest", hero="Leo", hero_gender="boy", companion="Zoe", companion_gender="girl", instrument="oboe", conflict="fear", reconciliation="listen", storm=2),
    StoryParams(setting="harbor", hero="Nina", hero_gender="girl", companion="Owen", companion_gender="boy", instrument="oboe", conflict="lost_note", reconciliation="duet", storm=0),
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
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos:")
        for s, i, c in asp_valid_combos():
            print(f"  {s:8} {i:8} {c:12}")
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
            params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
