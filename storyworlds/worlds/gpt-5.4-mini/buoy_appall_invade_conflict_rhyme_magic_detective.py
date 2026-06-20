#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/buoy_appall_invade_conflict_rhyme_magic_detective.py
====================================================================================

A small detective-style storyworld for a child-facing mystery about a buoy,
a spooky appalling clue, and an invading problem that gets solved by rhyme and
magic. The world model tracks concrete meters and emotional memes so the prose
comes from simulated state, not a frozen paragraph.

The story shape:
- a seaside detective notices a strange problem
- a bad thing invades a place it should not be
- clues, rhyme, and magic reveal what is really happening
- the detective fixes the conflict and the ending proves the change

Words required by the seed: buoy, appall, invade.
Features required by the seed: Conflict, Rhyme, Magic.
Style required by the seed: Detective Story.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Place:
    id: str
    label: str
    setting: str
    waterside: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Trouble:
    id: str
    label: str
    invade_word: str
    effect: str
    meter: str
    scary: int = 1
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Charm:
    id: str
    label: str
    phrase: str
    rhyme_line: str
    magic_word: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["alarm"] < THRESHOLD:
            continue
        sig = ("conflict", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "dock" in world.entities:
            world.get("dock").meters["tension"] += 1
        e.memes["conflict"] += 1
        out.append("__conflict__")
    return out


def _r_magic_awake(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["magic"] < THRESHOLD:
            continue
        sig = ("magic", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["glow"] += 1
        out.append("__glow__")
    return out


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("magic", "magic", _r_magic_awake),
]


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


def detect_intrusion(world: World, intruder: Entity, place: Place) -> None:
    intruder.meters["intruding"] += 1
    world.get("dock").meters["tension"] += 1
    world.say(
        f"On a foggy morning, {intruder.id} and the little harbor were quiet, "
        f"until {place.label} felt wrong, like a clue with muddy shoes."
    )


def appall_beat(world: World, detective: Entity, trouble: Trouble) -> None:
    detective.memes["alarm"] += 1
    world.say(
        f'{detective.id} frowned. "This would appall any good detective," '
        f"{detective.pronoun()} said, staring at the {trouble.label}."
    )


def invade_beat(world: World, trouble: Trouble, place: Place) -> None:
    world.say(
        f"Then the trouble tried to invade the quiet pier, sliding in where it "
        f"did not belong and leaving a trail of {trouble.effect}."
    )


def clue_rhyme(world: World, detective: Entity, charm: Charm, trouble: Trouble) -> None:
    detective.memes["wonder"] += 1
    world.say(
        f"{detective.id} found a tiny note tied to a buoy. It read, "
        f'"{charm.rhyme_line}"'
    )
    world.say(
        f"The rhyme made the clue sparkle. {charm.magic_word.capitalize()} "
        f"{charm.phrase}, and the detective listened for the hidden pattern."
    )


def solve(world: World, detective: Entity, trouble: Trouble, charm: Charm) -> None:
    detective.meters["solved"] += 1
    trouble_meter = trouble.meter
    world.get("dock").meters["tension"] = 0.0
    world.say(
        f"{detective.id} raised a {charm.label} and spoke the magic word. "
        f"The {trouble.label} lost its hold at once."
    )
    world.say(
        f"With a bright blink, the {trouble.label} drifted back where it belonged, "
        f"and the harbor felt calm again."
    )


def ending(world: World, detective: Entity, place: Place) -> None:
    detective.memes["relief"] += 1
    world.say(
        f"By the end, the buoy bobbed peacefully in the water, the pier was "
        f"quiet, and {detective.id} smiled at the solved case."
    )
    world.say(
        f"Nothing invaded the harbor now except the gentle tide and the morning light."
    )


def tell(place: Place, trouble: Trouble, charm: Charm, detective_name: str = "Dot",
         detective_gender: str = "girl", helper_name: str = "Milo",
         helper_gender: str = "boy") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="dock", kind="thing", type="place", label="the dock"))
    world.add(Entity(id="buoy", kind="thing", type="thing", label="the buoy"))
    world.facts["place"] = place
    world.facts["trouble"] = trouble
    world.facts["charm"] = charm
    world.facts["detective"] = detective
    world.facts["helper"] = helper

    world.say(
        f"{detective.id} was a small detective with sharp eyes, and {helper.id} "
        f"carried a notebook for every clue."
    )
    world.say(
        f"They walked to {place.label}, where a bright buoy bobbed in the water."
    )
    world.say(
        f"{helper.id} pointed at the water and whispered that something strange had begun."
    )

    world.para()
    detect_intrusion(world, helper, place)
    appall_beat(world, detective, trouble)
    invade_beat(world, trouble, place)

    world.para()
    clue_rhyme(world, detective, charm, trouble)
    helper.memes["magic"] += 1
    propagate(world, narrate=False)
    solve(world, detective, trouble, charm)

    world.para()
    ending(world, detective, place)

    world.facts.update(outcome="solved")
    return world


PLACES = {
    "harbor": Place("harbor", "the harbor", "a sleepy harbor"),
    "pier": Place("pier", "the pier", "a wooden pier"),
    "bay": Place("bay", "the bay", "a small bay"),
}

TROUBLES = {
    "foggy_sign": Trouble("foggy_sign", "fog sign", "invade", "foggy words", "fog"),
    "sour_note": Trouble("sour_note", "sour note", "invade", "mean whispers", "sound"),
    "knotty_riddle": Trouble("knotty_riddle", "knotty riddle", "invade", "twisted clues", "puzzle"),
}

CHARMS = {
    "belltune": Charm("belltune", "bell tune", "a little bell tune", "tap and clap", "sparkle", 2, tags={"rhyme", "magic"}),
    "moonverse": Charm("moonverse", "moon verse", "a moon verse", "glow and know", "shine", 2, tags={"rhyme", "magic"}),
    "shellspell": Charm("shellspell", "shell spell", "a shell spell", "hail and sail", "listen", 2, tags={"rhyme", "magic"}),
}

GIRL_NAMES = ["Dot", "Mina", "Ivy", "Nell", "June", "Ruby"]
BOY_NAMES = ["Milo", "Finn", "Otto", "Theo", "Levi", "Pip"]


@dataclass
@dataclass
class StoryParams:
    place: str
    trouble: str
    charm: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, c) for p in PLACES for t in TROUBLES for c in CHARMS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with buoy, appall, invade, conflict, rhyme, and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combo = rng.choice(sorted(valid_combos()))
    place = args.place or combo[0]
    trouble = args.trouble or combo[1]
    charm = args.charm or combo[2]
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or ("boy" if dg == "girl" else "girl")
    detective = args.detective or rng.choice(GIRL_NAMES if dg == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if hg == "girl" else BOY_NAMES) if n != detective]
    helper = args.helper or rng.choice(helper_pool)
    return StoryParams(place, trouble, charm, detective, dg, helper, hg)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TROUBLES[params.trouble], CHARMS[params.charm],
                 params.detective, params.detective_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a detective story for a young child that uses the words buoy, appall, and invade.",
        f"Tell a seaside mystery where {f['detective'].id} and {f['helper'].id} notice a trouble that tries to invade the harbor.",
        f"Write a rhyme-filled magical detective story where a buoy helps solve a conflict at the water's edge.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    h = f["helper"]
    t = f["trouble"]
    c = f["charm"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {d.id}, a little detective, and {h.id}, who helped with the clues. Together they solved a seaside case."),
        QAItem(question="What made the detective appall?", answer=f"The detective was appalled by the way the {t.label} tried to invade the harbor. It did not belong there, so it felt wrong and troubling."),
        QAItem(question="How was the problem solved?", answer=f"{d.id} used {c.label} and spoke the magic word after hearing the rhyme. That calm, magical clue broke the trouble's hold and ended the conflict."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a buoy?", answer="A buoy is a floating marker in the water. It helps people notice where the safe waterway is."),
        QAItem(question="What does appall mean?", answer="To appall someone means to shock or disgust them. It is a strong feeling that something is very wrong."),
        QAItem(question="What does invade mean?", answer="To invade means to move into a place where you do not belong. It is often used for trouble or enemies entering a safe place."),
        QAItem(question="What is rhyme?", answer="Rhyme is when words sound alike at the end, like tune and moon. Rhymes can make a clue easy to remember."),
        QAItem(question="What is magic in stories?", answer="Magic is a special power that can do impossible things in a story. It can help solve problems in a surprising way."),
    ]


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
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines += ["", "== (2) Story questions -- answerable from the story text ==", ""]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines += ["", "== (3) World-knowledge questions -- child level, no story needed ==", ""]
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams("harbor", "foggy_sign", "belltune", "Dot", "girl", "Milo", "boy"),
    StoryParams("pier", "sour_note", "moonverse", "Ivy", "girl", "Theo", "boy"),
    StoryParams("bay", "knotty_riddle", "shellspell", "Nell", "girl", "Pip", "boy"),
]


ASP_RULES = r"""
valid(P, T, C) :- place(P), trouble(T), charm(C).
conflict(D) :- detective(D), alarmed(D).
magic_on(C) :- charm(C), magic(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
        lines.append(asp.fact("magic", c))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: generation smoke test passed.")
    return rc


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
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
