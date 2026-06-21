#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/email_floss_foreshadowing_kindness_surprise_detective_story.py
=============================================================================================

A tiny detective-style storyworld about an email clue, a lost floss box, an act
of kindness, and a surprise reveal.

The domain is small on purpose: a child detective, a helper, a missing floss
container, and a mysterious email that foreshadows where the clue is hidden.
The story engine simulates physical state (meters) and emotional state (memes),
then renders prose from the state change.

Features baked into the world:
- Foreshadowing: the email contains a clue that later matters.
- Kindness: a character helps instead of scolding.
- Surprise: the ending reveals the missing floss was where the clue pointed.

This file is self-contained and uses only stdlib plus the shared repo modules.
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
REASONABLE_MAX_MYSTERY = 3.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Case:
    id: str
    setting: str
    detective_line: str
    missing_line: str
    email_sender: str
    email_hint: str
    clue_place: str
    clue_turn: str
    surprise_reveal: str
    clue_kind: str
    clue_strength: int = 1
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
class Comfort:
    id: str
    label: str
    phrase: str
    where: str
    hidden: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class EmailNote:
    id: str
    subject: str
    body: str
    clue_word: str
    clue_tag: str
    foreshadow: str
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
class StoryParams:
    case: str
    comfort: str
    note: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_calmer(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["worry"] >= THRESHOLD and e.memes["kindness"] >= THRESHOLD:
            sig = ("calm", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["hope"] += 1
            out.append("")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    detective = world.entities.get("detective")
    note = world.entities.get("note")
    if detective and note and note.meters["hint"] >= THRESHOLD:
        sig = ("foreshadow",)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["curiosity"] += 1
            out.append("")
    return out


CAUSAL_RULES = [
    _r_calmer,
    _r_foreshadow,
]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule(world)
            if len(world.fired) != before:
                changed = True


def _do_find(world: World, detective: Entity, note: EmailNote, comfort: Comfort) -> None:
    detective.meters["finding"] += 1
    world.get("note").meters["hint"] += note.clue_strength
    detective.memes["curiosity"] += 1
    detective.memes["worry"] += 1
    propagate(world)


def _resolve_kindness(world: World, helper: Entity, detective: Entity) -> None:
    helper.memes["kindness"] += 1
    detective.memes["worry"] = max(0.0, detective.memes["worry"] - 1)
    detective.memes["trust"] += 1


def _surprise(world: World, comfort: Comfort) -> None:
    world.get("comfort").meters["found"] += 1
    world.get("comfort").meters["open"] += 1


def _predict(world: World, note: EmailNote) -> dict:
    sim = world.copy()
    _do_find(sim, sim.get("detective"), note, COMFORTS["casefile_floss"])
    return {
        "hint": sim.get("note").meters["hint"],
        "curiosity": sim.get("detective").memes["curiosity"],
    }


def tell(case: Case, comfort: Comfort, note: EmailNote,
         detective_name: str = "Maya", detective_gender: str = "girl",
         helper_name: str = "Riley", helper_gender: str = "boy") -> World:
    world = World()
    detective = world.add(Entity(id="detective", kind="character", type=detective_gender,
                                 label=detective_name, role="detective",
                                 traits=["careful", "sharp"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender,
                              label=helper_name, role="helper", traits=["kind"]))
    email = world.add(Entity(id="note", kind="thing", type="email", label="email",
                             attrs={"subject": note.subject, "body": note.body}))
    floss = world.add(Entity(id="comfort", kind="thing", type="thing",
                             label=comfort.label, attrs={"hidden": comfort.hidden}))

    detective.memes["curiosity"] = 1.0
    detective.memes["worry"] = 0.0

    world.say(
        f"At {case.setting}, {detective.label_word} was the child detective who loved neat clues."
    )
    world.say(
        f"One morning, an {note.id} arrived with the subject '{note.subject}'. {note.body}"
    )
    world.say(
        f"{note.foreshadow}. {case.detective_line}"
    )

    world.para()
    _do_find(world, detective, note, comfort)
    world.say(
        f"{detective.label_word} followed the hint toward {case.clue_place}, because the email had pointed there first."
    )
    world.say(
        f"{case.missing_line}"
    )

    world.para()
    _resolve_kindness(world, helper, detective)
    world.say(
        f"{helper.label_word} did not laugh. Instead, {helper.label_word} knelt down and said, "
        f'"Let’s look together. Two sets of eyes are better than one."'
    )
    world.say(
        f"That gentle kindness made {detective.label_word} breathe easier and keep searching."
    )

    world.para()
    _surprise(world, comfort)
    world.say(
        f"Then came the surprise: {case.surprise_reveal}. {case.clue_turn}"
    )
    world.say(
        f"In the end, the {comfort.label} was back in the open, the email made sense, and the whole case clicked into place."
    )

    world.facts.update(
        detective=detective,
        helper=helper,
        note=email,
        comfort=floss,
        case=case,
        note_cfg=note,
        comfort_cfg=comfort,
        outcome="solved",
        foreshadowed=True,
        kindness=True,
        surprise=True,
    )
    return world


CASES = {
    "clinic": Case(
        id="clinic",
        setting="the small dental clinic",
        detective_line="The detective knew this was a case of something missing before the appointment.",
        missing_line="The floss box was gone from the little shelf, and that felt like a clue.",
        email_sender="the dentist",
        email_hint="the message mentioned a tiny blue drawer near the sink",
        clue_place="the blue drawer",
        clue_turn="The clue had been there all along.",
        surprise_reveal="the floss was tucked inside a lunch bag by mistake",
        clue_kind="drawer",
        clue_strength=2,
    ),
    "house": Case(
        id="house",
        setting="the kitchen table at home",
        detective_line="The detective stared at the email twice, because it sounded like a clue and a riddle at once.",
        missing_line="The floss packet was not on the counter, which meant someone had moved it.",
        email_sender="Grandma",
        email_hint="the note mentioned a jar near the bread box",
        clue_place="the bread box",
        clue_turn="That was the sort of clue a detective could not ignore.",
        surprise_reveal="the floss had been hidden under a teacup as a funny joke",
        clue_kind="jar",
        clue_strength=1,
    ),
    "school": Case(
        id="school",
        setting="the classroom supply corner",
        detective_line="The detective had a feeling the email was warning about a mix-up before it happened.",
        missing_line="The floss for the model teeth was missing from the supply basket.",
        email_sender="the teacher",
        email_hint="the clue pointed to the red bin by the window",
        clue_place="the red bin",
        clue_turn="Sure enough, that clue mattered later.",
        surprise_reveal="the floss was inside the puppet basket all along",
        clue_kind="bin",
        clue_strength=2,
    ),
}

COMFORTS = {
    "casefile_floss": Comfort(
        id="casefile_floss",
        label="floss",
        phrase="a little floss box",
        where="the shelf",
        hidden="inside a lunch bag",
        tags={"floss"},
    ),
    "mint_floss": Comfort(
        id="mint_floss",
        label="mint floss",
        phrase="a minty floss box",
        where="the basket",
        hidden="under a teacup",
        tags={"floss"},
    ),
    "school_floss": Comfort(
        id="school_floss",
        label="school floss",
        phrase="a school floss packet",
        where="the supply basket",
        hidden="in the puppet basket",
        tags={"floss"},
    ),
}

NOTES = {
    "drawer_hint": EmailNote(
        id="email",
        subject="A little clue for you",
        body="I think the missing floss is near the blue drawer.",
        clue_word="drawer",
        clue_tag="drawer",
        foreshadow="It sounded small, but it mattered later",
        tags={"email", "foreshadow"},
    ),
    "box_hint": EmailNote(
        id="email",
        subject="Look where the bread goes",
        body="I saw the floss near the bread box this morning.",
        clue_word="box",
        clue_tag="box",
        foreshadow="The message felt like it was hiding the answer in plain sight",
        tags={"email", "foreshadow"},
    ),
    "bin_hint": EmailNote(
        id="email",
        subject="Check the red bin",
        body="Please look by the red bin before you worry too much.",
        clue_word="bin",
        clue_tag="bin",
        foreshadow="The email seemed ordinary, but ordinary words can point to surprises",
        tags={"email", "foreshadow"},
    ),
}

CASE_TO_NOTE = {"clinic": "drawer_hint", "house": "box_hint", "school": "bin_hint"}
CASE_TO_COMFORT = {"clinic": "casefile_floss", "house": "mint_floss", "school": "school_floss"}

GIRL_NAMES = ["Maya", "Lina", "Nina", "Ava", "Ivy", "Zoe"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Milo", "Arlo", "Finn"]
HELPER_NAMES = ["Riley", "Sam", "Jules", "Alex", "Parker", "Rowan"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for cid in CASES:
        for fid in COMFORTS:
            for nid in NOTES:
                if CASE_TO_NOTE[cid] == nid and CASE_TO_COMFORT[cid] == fid:
                    out.append((cid, fid, nid))
    return out


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def explain_rejection() -> str:
    return "(No story: this small world expects the matching case, floss, and email clue to line up.)"


def explain_note(nid: str) -> str:
    return f"(Refusing note '{nid}': the email clue must match the chosen case.)"


def explain_comfort(fid: str) -> str:
    return f"(Refusing floss '{fid}': that floss box does not fit this case's surprise.)"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for fid, f in COMFORTS.items():
        lines.append(asp.fact("comfort", fid))
        if "floss" in f.tags:
            lines.append(asp.fact("has_floss", fid))
    for nid in NOTES:
        lines.append(asp.fact("note", nid))
        lines.append(asp.fact("emailish", nid))
    for cid, nid in CASE_TO_NOTE.items():
        lines.append(asp.fact("pairs_note", cid, nid))
    for cid, fid in CASE_TO_COMFORT.items():
        lines.append(asp.fact("pairs_comfort", cid, fid))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(C,F,N) :- case(C), comfort(F), note(N), pairs_note(C,N), pairs_comfort(C,F).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python combo gates differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = f["case"]
    note = f["note_cfg"]
    comfort = f["comfort_cfg"]
    return [
        f'Write a detective story for a young child that includes the words "{note.id}" and "{comfort.label}".',
        f"Tell a gentle mystery where a detective follows an email clue, finds missing floss, and ends with kindness and a surprise.",
        f"Write a story in which an email foreshadows where the floss is hiding, and a kind helper makes the ending happy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case = f["case"]
    note = f["note_cfg"]
    comfort = f["comfort_cfg"]
    detective = f["detective"]
    helper = f["helper"]
    return [
        QAItem(
            question="Why did the email matter in the story?",
            answer=f"It gave a clue that pointed toward {case.clue_place}, so the detective knew where to look next. That foreshadowing made the later surprise feel earned instead of random."
        ),
        QAItem(
            question="How did the helper show kindness?",
            answer=f"{helper.label_word} did not tease or hurry {detective.label_word}. Instead, {helper.label_word} looked together with the detective and helped keep the search calm."
        ),
        QAItem(
            question="What was the surprise at the end?",
            answer=f"The missing floss turned up in a different place than expected: {case.surprise_reveal}. The detective realized the email had been hinting at the answer all along."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is email?",
            answer="Email is a message sent on a phone or computer. People use it to share news or clues quickly."
        ),
        QAItem(
            question="What is floss?",
            answer="Floss is a thin string people use to clean between teeth. It is small, easy to lose, and useful to keep in a tidy place."
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small hint early on about something that will matter later. It helps the ending feel surprising but fair."
        ),
    ]


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective storyworld about email, floss, kindness, and surprise.")
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--note", choices=NOTES)
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
    if args.note and args.case and CASE_TO_NOTE[args.case] != args.note:
        raise StoryError(explain_note(args.note))
    if args.comfort and args.case and CASE_TO_COMFORT[args.case] != args.comfort:
        raise StoryError(explain_comfort(args.comfort))
    combos = [c for c in valid_combos()
              if (args.case is None or c[0] == args.case)
              and (args.comfort is None or c[1] == args.comfort)
              and (args.note is None or c[2] == args.note)]
    if not combos:
        raise StoryError(explain_rejection())
    case, comfort, note = rng.choice(sorted(combos))
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        case=case,
        comfort=comfort,
        note=note,
        detective=args.detective or _pick_name(rng, dg),
        detective_gender=dg,
        helper=args.helper or rng.choice(HELPER_NAMES),
        helper_gender=hg,
    )


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES or params.comfort not in COMFORTS or params.note not in NOTES:
        raise StoryError("invalid parameters")
    case = CASES[params.case]
    comfort = COMFORTS[params.comfort]
    note = NOTES[params.note]
    world = tell(case, comfort, note, params.detective, params.detective_gender, params.helper, params.helper_gender)
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
    StoryParams(case="clinic", comfort="casefile_floss", note="drawer_hint", detective="Maya", detective_gender="girl", helper="Riley", helper_gender="boy"),
    StoryParams(case="house", comfort="mint_floss", note="box_hint", detective="Noah", detective_gender="boy", helper="Jules", helper_gender="girl"),
    StoryParams(case="school", comfort="school_floss", note="bin_hint", detective="Lina", detective_gender="girl", helper="Sam", helper_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos:")
        for c in asp_valid_combos():
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
