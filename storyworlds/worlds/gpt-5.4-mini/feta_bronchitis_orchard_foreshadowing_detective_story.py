#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/feta_bronchitis_orchard_foreshadowing_detective_story.py
========================================================================================

A standalone tiny storyworld for an orchard detective tale with foreshadowing,
a missing snack, and a cough that turns out to matter later.

Premise
-------
A child detective visits an orchard to solve a small mystery: a picnic pouch is
missing, someone is coughing, and a few early clues seem unimportant at first.
The story uses foreshadowing so that the cough, the strange smell, and a hidden
trail all matter later.

The world model tracks:
- typed entities with meters and memes,
- physical clues and emotional states,
- a forward-chained turn from curiosity to discovery,
- a sensible gate that refuses unreasonable stories,
- a Python and ASP twin for parity checks,
- three QA sets grounded in simulated world state.

This script is stdlib-only and can run directly from the repo root.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
FORESHADOW_THRESHOLD = 1.0
CARE_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
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
    detail: str
    weather: str
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
class Clue:
    id: str
    label: str
    smell: str
    where: str
    foreshadows: str
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
class MissingItem:
    id: str
    label: str
    phrase: str
    owner_role: str
    edible: bool = True
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
class Illness:
    id: str
    label: str
    symptom: str
    consequence: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.scene_clues: list[str] = []

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.scene_clues = list(self.scene_clues)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    orchard_owner: str
    missing: str
    clue: str
    illness: str
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


SETTINGS = {
    "orchard": Setting(
        "orchard",
        "the orchard",
        "Rows of apple trees stretched under soft leaves, with ladders, baskets, and a little shed by the fence.",
        "mild",
        tags={"orchard"},
    )
}

CLUES = {
    "feta": Clue(
        "feta",
        "a crumbled bit of feta",
        "salty",
        "by the base of a low tree",
        "someone had been snacking here and trying not to be seen",
        tags={"feta", "food"},
    ),
    "note": Clue(
        "note",
        "a folded note",
        "papery",
        "under a basket",
        "the answer was written down and then hidden on purpose",
        tags={"note", "paper"},
    ),
    "ladder_mark": Clue(
        "ladder_mark",
        "a ladder scuff",
        "dusty",
        "on the grass near the shed",
        "someone climbed up before the main trick was revealed",
        tags={"ladder", "mark"},
    ),
    "cough": Clue(
        "cough",
        "a rough cough",
        "scratchy",
        "in the air by the trees",
        "a small sickness was going to matter later",
        tags={"cough", "bronchitis"},
    ),
}

MISSING = {
    "picnic": MissingItem("picnic", "picnic basket", "a picnic basket", "helper"),
    "tin": MissingItem("tin", "snack tin", "a shiny snack tin", "helper"),
}

ILLNESSES = {
    "bronchitis": Illness(
        "bronchitis",
        "bronchitis",
        "a bad cough",
        "rest and warm tea",
        tags={"bronchitis", "cough"},
    )
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Maya", "Ruby"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Ben", "Max", "Noah", "Eli", "Jack"]
HELPER_NAMES = ["Aunt June", "Uncle Ray", "Mrs. Bell", "Mr. Green", "Nina"]
TRAITS = ["careful", "curious", "smart", "patient", "sharp-eyed"]


def _meters() -> dict[str, float]:
    return {"attention": 0.0, "fear": 0.0, "relief": 0.0, "suspense": 0.0, "clue": 0.0}


def _memes() -> dict[str, float]:
    return {"curiosity": 0.0, "worry": 0.0, "trust": 0.0, "hope": 0.0, "understanding": 0.0}


def sensible_clue(clue: Clue) -> bool:
    return clue.id in {"feta", "cough", "note", "ladder_mark"}


def likely_case(detective: Entity, clue: Clue, illness: Illness) -> bool:
    return detective.role == "detective" and sensible_clue(clue) and illness.id == "bronchitis"


def case_turns_on(clue: Clue) -> bool:
    return clue.foreshadows != ""


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for iid in ILLNESSES:
                if likely_case(Entity("x", role="detective"), clue, ILLNESSES[iid]):
                    combos.append((sid, cid, iid))
    return combos


def ASP_RULES() -> str:
    return r"""
case_valid(S,C,I) :- setting(S), clue(C), illness(I), clue_ok(C), illness_ok(I).
clue_ok(feta).
clue_ok(note).
clue_ok(ladder_mark).
clue_ok(cough).
illness_ok(bronchitis).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for iid in ILLNESSES:
        lines.append(asp.fact("illness", iid))
    for cid in CLUES:
        if sensible_clue(CLUES[cid]):
            lines.append(asp.fact("clue_ok", cid))
    lines.append(asp.fact("illness_ok", "bronchitis"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show case_valid/3."))
    return sorted(set(asp.atoms(model, "case_valid")))


def reasonableness_gate(setting: Setting, clue: Clue, illness: Illness) -> None:
    if setting.id != "orchard":
        raise StoryError("This tiny world only knows an orchard setting.")
    if clue.id not in CLUES:
        raise StoryError("Unknown clue.")
    if illness.id not in ILLNESSES:
        raise StoryError("Unknown illness.")
    if clue.id == "feta" and illness.id != "bronchitis":
        raise StoryError("The feta clue is only meaningful in this orchard mystery.")
    if clue.id not in {"feta", "cough"}:
        raise StoryError("This storyworld wants foreshadowing clues that point forward.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Orchard detective story with foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS, default="orchard")
    ap.add_argument("--detective", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--orchard-owner", default="the orchard owner")
    ap.add_argument("--missing", choices=MISSING, default="picnic")
    ap.add_argument("--clue", choices=CLUES, default="feta")
    ap.add_argument("--illness", choices=ILLNESSES, default="bronchitis")
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
    setting = SETTINGS[args.setting]
    clue = CLUES[args.clue]
    illness = ILLNESSES[args.illness]
    reasonableness_gate(setting, clue, illness)
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    detective = args.detective or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper = args.helper or rng.choice(HELPER_NAMES)
    missing = args.missing
    return StoryParams(setting.id, detective, detective_gender, helper, helper_gender, args.orchard_owner, missing, clue.id, illness.id)


def _make_entity(world: World, eid: str, kind: str, type_: str, label: str = "", role: str = "") -> Entity:
    return world.add(Entity(eid, kind=kind, type=type_, label=label, role=role, meters=_meters(), memes=_memes()))


def _propagate(world: World) -> None:
    detective = world.get("detective")
    clue = world.get("clue")
    if detective.meters["attention"] >= THRESHOLD and clue.id not in world.fired:
        world.fired.add((clue.id, "noticed"))
        detective.meters["clue"] += 1
        detective.memes["curiosity"] += 1


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    detective = _make_entity(world, "detective", "character", params.detective_gender, params.detective, "detective")
    helper = _make_entity(world, "helper", "character", params.helper_gender, params.helper, "helper")
    owner = _make_entity(world, "owner", "character", "person", params.orchard_owner, "owner")
    clue = _make_entity(world, "clue", "thing", "clue", CLUES[params.clue].label)
    illness = _make_entity(world, "illness", "thing", "illness", ILLNESSES[params.illness].label)

    detective.memes["trust"] = 1.0
    helper.memes["worry"] = 1.0
    detective.meters["attention"] = 1.0

    world.say(
        f"{detective.id} was a sharp little detective who loved solving mysteries. "
        f"On a mild day, {detective.id} and {helper.id} walked into {world.setting.place}."
    )
    world.say(
        f"The trees stood in neat rows, and {world.setting.detail}"
    )

    world.para()
    world.say(
        f"{detective.id} spotted {clue.label} first. It seemed small, but it looked as if it had been left there on purpose."
    )
    world.say(
        f"Near the same path, {helper.id} gave a tiny cough and said it was only a little scratch in the throat."
    )
    detective.memes["curiosity"] += 1
    detective.meters["attention"] += 1
    detective.meters["suspense"] += 1
    world.scene_clues.append(params.clue)
    world.scene_clues.append("cough")
    _propagate(world)

    world.para()
    if params.clue == "feta":
        world.say(
            f"{detective.id} noticed the salty smell and bent closer. The crumb of feta pointed toward the shed."
        )
        detective.memes["understanding"] += 1
        detective.meters["clue"] += 1
        world.scene_clues.append("feta")
    else:
        world.say(
            f"{detective.id} noticed {clue.label} and began to wonder what it meant."
        )

    world.say(
        f"Then {detective.id} remembered the cough. The clue and the cough fit together like puzzle pieces."
    )
    detective.memes["hope"] += 1
    world.get("illness").meters["symptom"] = 1.0

    world.para()
    world.say(
        f"{detective.id} followed the trail to the shed by the fence. Inside, the missing {params.missing} was tucked under a basket."
    )
    world.say(
        f"The orchard owner had hidden it there, and {helper.id}'s bronchitis explained why {helper.id} had been moving slowly."
    )
    detective.memes["worry"] += 1
    detective.memes["understanding"] += 1
    world.get("illness").meters["consequence"] = 1.0

    world.para()
    world.say(
        f"{detective.id} smiled and handed over warm tea, then told everyone what the clues had meant."
    )
    world.say(
        f"{helper.id} coughed less after resting, and the orchard felt calm again under the leaves."
    )
    world.say(
        f"By the end, the small feta crumb, the cough, and the hidden basket had all done their part in the case."
    )

    outcome = "solved"
    world.facts.update(
        detective=detective,
        helper=helper,
        owner=owner,
        clue=clue,
        illness=illness,
        outcome=outcome,
        setting=world.setting,
        missing=params.missing,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a child-friendly detective story set in an orchard, and make one small clue foreshadow a later reveal.",
        f"Tell a mystery story where {f['detective'].id} notices {f['clue'].label} in the orchard and later realizes it matters.",
        "Write a detective tale with a gentle ending, using foreshadowing to connect an early cough with the final answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    clue = f["clue"]
    illness = f["illness"]
    return [
        QAItem(
            question=f"What kind of story is this?",
            answer="It is a small detective story. The mystery is solved by noticing early clues and understanding what they point to later.",
        ),
        QAItem(
            question=f"Why did the crumb of feta matter?",
            answer=f"It mattered because it was an early clue. It foreshadowed that someone had been snacking near the trees and helped {detective.id} know where to look next.",
        ),
        QAItem(
            question=f"Why was {helper.id} coughing?",
            answer=f"{helper.id} had bronchitis, so the cough was not part of the trick. It was a real symptom that made the story’s later explanation fit the earlier clue.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{detective.id} followed the clue trail from the feta crumb to the shed and then understood the cough too. That is why the ending feels complete instead of random.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["clue"].tags) | set(world.facts["illness"].tags) | {"orchard"}
    items = []
    if "feta" in tags:
        items.append(QAItem("What is feta?", "Feta is a crumbly cheese. It has a salty taste and can leave a small white crumb behind."))
    if "bronchitis" in tags:
        items.append(QAItem("What is bronchitis?", "Bronchitis is a sickness that can cause a cough. Rest and warm drinks can help someone feel better."))
    if "orchard" in tags:
        items.append(QAItem("What is an orchard?", "An orchard is a place where fruit trees grow in rows. People can walk there and pick fruit when it is ready."))
    return items


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orchard", "Mia", "girl", "Aunt June", "woman", "the orchard owner", "picnic", "feta", "bronchitis"),
    StoryParams("orchard", "Theo", "boy", "Mr. Green", "man", "the orchard owner", "tin", "cough", "bronchitis"),
]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    ok = py == clingo
    print("OK: ASP matches Python valid_combos()." if ok else "MISMATCH: ASP and Python differ.")
    if not ok:
        print("python:", sorted(py))
        print("asp:", sorted(clingo))
        return 1
    # Smoke test normal generation.
    sample = generate(CURATED[0])
    _ = sample.story
    return 0


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        setting=args.setting or "orchard",
        detective=args.detective or rng.choice(GIRL_NAMES + BOY_NAMES),
        detective_gender=args.detective_gender or rng.choice(["girl", "boy"]),
        helper=args.helper or rng.choice(HELPER_NAMES),
        helper_gender=args.helper_gender or rng.choice(["woman", "man"]),
        orchard_owner=args.orchard_owner or "the orchard owner",
        missing=args.missing or "picnic",
        clue=args.clue or "feta",
        illness=args.illness or "bronchitis",
    )
    reasonableness_gate(SETTINGS[params.setting], CLUES[params.clue], ILLNESSES[params.illness])
    return params


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show case_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible cases:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective} in the orchard: {p.clue} / {p.illness}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
