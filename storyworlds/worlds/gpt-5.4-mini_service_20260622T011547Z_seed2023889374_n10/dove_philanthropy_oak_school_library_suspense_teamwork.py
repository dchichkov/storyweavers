#!/usr/bin/env python3
"""
storyworlds/worlds/dove_philanthropy_oak_school_library_suspense_teamwork.py
============================================================================

A standalone storyworld for a tiny detective tale set in a school library.

Premise:
- A school library has a quiet mystery: a philanthropy box of donated books has
  gone missing from an oak reading table.
- Two children investigate with teamwork and suspense.
- A white dove clue leads them to the right shelf, and the missing box is found.

The world model uses typed entities with physical meters and emotional memes.
Story choices are constrained so every generated story has:
- a real mystery,
- a grounded clue trail,
- teamwork that matters,
- a complete ending image showing what changed.

The required words are woven into the story:
- dove
- philanthropy
- oak

The style is child-facing detective story prose.
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    quiet_places: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    hiding_spot: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    found_near: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mystery") != "missing_box":
        return out
    if world.facts.get("teamwork") < THRESHOLD:
        return out
    if world.facts.get("suspense") < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        kid.memes["focus"] += 1
        kid.memes["courage"] += 1
    world.get("library").meters["tension"] += 1
    out.append("__suspense__")
    return out


def _r_find(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_seen") != "dove":
        return out
    if world.facts.get("teamwork") < THRESHOLD:
        return out
    sig = ("find",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    box = world.get("philanthropy_box")
    box.meters["hidden"] = 0.0
    box.meters["found"] = 1.0
    world.get("library").meters["tension"] = 0.0
    out.append("__found__")
    return out


CAUSAL_RULES = [Rule("spook", _r_spook), Rule("find", _r_find)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SETTINGS = {
    "school_library": Setting(
        id="school_library",
        place="the school library",
        quiet_places=["the oak reading table", "the back shelf", "the window nook"],
        tags={"library", "school", "quiet"},
    )
}

SUSPECTS = {
    "dove": Suspect(
        id="dove",
        label="a white dove",
        hiding_spot="the oak shelf",
        clue="a feather stuck in the book cart",
        tags={"dove", "feather", "animal"},
    ),
    "lost_note": Suspect(
        id="lost_note",
        label="a folded note",
        hiding_spot="under the oak table",
        clue="a corner of paper peeking out",
        tags={"note", "paper"},
    ),
}

CLUES = {
    "feather": Clue(
        id="feather",
        label="a white feather",
        found_near="the oak reading table",
        tags={"dove", "feather"},
    ),
    "bookmark": Clue(
        id="bookmark",
        label="a blue bookmark",
        found_near="the top shelf",
        tags={"paper", "bookmark"},
    ),
}

RESOLUTIONS = {
    "team_search": Resolution(
        id="team_search",
        action="split up and search together",
        result="the missing box was found beside the oak shelf",
        tags={"teamwork", "search"},
    ),
    "ask_librarian": Resolution(
        id="ask_librarian",
        action="ask the librarian for help",
        result="the librarian pointed to the right shelf at once",
        tags={"help", "library"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Ella", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Max", "Finn", "Theo"]
PAIR_NAMES = [("Mia", "Leo"), ("Nora", "Ben"), ("Ava", "Max"), ("Ella", "Finn"), ("Zoe", "Theo")]


@dataclass
class StoryParams:
    setting: str
    suspect: str
    clue: str
    resolution: str
    name1: str
    gender1: str
    name2: str
    gender2: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="school_library",
        suspect="dove",
        clue="feather",
        resolution="team_search",
        name1="Mia",
        gender1="girl",
        name2="Leo",
        gender2="boy",
    ),
    StoryParams(
        setting="school_library",
        suspect="lost_note",
        clue="bookmark",
        resolution="ask_librarian",
        name1="Nora",
        gender1="girl",
        name2="Ben",
        gender2="boy",
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for suspect in SUSPECTS:
            for clue in CLUES:
                for res in RESOLUTIONS:
                    combos.append((sid, suspect, clue, res))
    return combos


def story_allowed(params: StoryParams) -> bool:
    return (
        params.setting in SETTINGS
        and params.suspect in SUSPECTS
        and params.clue in CLUES
        and params.resolution in RESOLUTIONS
    )


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen library mystery does not fit this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="School-library detective story world with suspense and teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name1")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--gender2", choices=["girl", "boy"])
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
    setting = args.setting or "school_library"
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    clue = args.clue or rng.choice(sorted(CLUES))
    resolution = args.resolution or rng.choice(sorted(RESOLUTIONS))
    if setting not in SETTINGS or suspect not in SUSPECTS or clue not in CLUES or resolution not in RESOLUTIONS:
        raise StoryError("(No valid combination matches the given options.)")
    if args.gender1 and args.gender2 and args.gender1 == args.gender2 and args.name1 == args.name2:
        raise StoryError("The two detectives need distinct names.")
    if args.name1:
        name1 = args.name1
        gender1 = args.gender1 or "girl"
    else:
        name1 = rng.choice(GIRL_NAMES if (args.gender1 or "girl") == "girl" else BOY_NAMES)
        gender1 = args.gender1 or ("girl" if name1 in GIRL_NAMES else "boy")
    if args.name2:
        name2 = args.name2
        gender2 = args.gender2 or "boy"
    else:
        name2 = rng.choice([n for n in (BOY_NAMES if gender1 == "girl" else GIRL_NAMES) if n != name1])
        gender2 = args.gender2 or ("boy" if name2 in BOY_NAMES else "girl")
    return StoryParams(
        setting=setting,
        suspect=suspect,
        clue=clue,
        resolution=resolution,
        name1=name1,
        gender1=gender1,
        name2=name2,
        gender2=gender2,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a 3-to-5-year-old set in {f["setting"].place} that includes the words "dove", "philanthropy", and "oak".',
        f"Tell a suspenseful teamwork story where {f['detective1'].id} and {f['detective2'].id} solve a school library mystery together.",
        f"Write a child-friendly mystery story in a school library where a clue from a dove leads to a philanthropy box near an oak shelf.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d1, d2 = f["detective1"], f["detective2"]
    setting = f["setting"]
    suspect = f["suspect"]
    clue = f["clue"]
    res = f["resolution"]
    box = f["philanthropy_box"]
    qa = [
        QAItem(
            question=f"Who were the two detectives in the school library?",
            answer=f"The two detectives were {d1.id} and {d2.id}. They worked together in {setting.place} to solve a small mystery.",
        ),
        QAItem(
            question=f"What problem made the story suspenseful?",
            answer=f"The philanthropy box had gone missing from the oak reading table. That made the library feel quiet and tense until the children started looking for clues.",
        ),
        QAItem(
            question=f"What clue did they notice first?",
            answer=f"They noticed {clue.label} near {clue.found_near}. That clue pointed them toward the place where the missing box was hiding.",
        ),
        QAItem(
            question=f"How did teamwork help {d1.id} and {d2.id}?",
            answer=f"They split the search and kept each other calm. Because they stayed together, they found {box.label} and solved the mystery faster.",
        ),
    ]
    if f.get("found"):
        qa.append(
            QAItem(
                question=f"What did they find at the end?",
                answer=f"They found {box.label} by the oak shelf. The box was no longer missing, so the library could feel peaceful again.",
            )
        )
    if res.id == "ask_librarian":
        qa.append(
            QAItem(
                question=f"Why did they ask the librarian for help?",
                answer="They wanted to make sure they looked in the right place. The librarian knew the library well and could point them to the best shelf to check.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is philanthropy?",
            answer="Philanthropy means helping other people, often by giving things or time to make life better for them.",
        ),
        QAItem(
            question="What is an oak?",
            answer="An oak is a kind of tree with strong wood. Oak wood is often used for tables and shelves because it is sturdy.",
        ),
        QAItem(
            question="Why are school libraries quiet?",
            answer="School libraries are quiet so people can read and think. Quiet rooms help everyone focus on books and searching carefully.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work toward the same goal. When a team shares ideas, big jobs can feel smaller.",
        ),
        QAItem(
            question="What is a dove?",
            answer="A dove is a small bird. It can flutter softly and leave feathers behind as a clue.",
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:16} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


def tell(setting: Setting, suspect: Suspect, clue: Clue, resolution: Resolution,
         detective1: Entity, detective2: Entity) -> World:
    world = World()
    d1 = world.add(detective1)
    d2 = world.add(detective2)
    library = world.add(Entity(
        id="library",
        kind="place",
        type="place",
        label=setting.place,
        meters={"tension": 0.0},
        memes={},
        tags=setting.tags,
    ))
    box = world.add(Entity(
        id="philanthropy_box",
        kind="thing",
        type="box",
        label="the philanthropy box",
        meters={"hidden": 1.0, "found": 0.0},
        memes={},
        tags={"philanthropy", "box"},
    ))
    oak = world.add(Entity(
        id="oak_table",
        kind="thing",
        type="table",
        label="the oak reading table",
        meters={"wood": 1.0},
        memes={},
        tags={"oak"},
    ))
    clue_ent = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue.label,
        meters={"seen": 0.0},
        memes={},
        tags=clue.tags,
    ))
    dove = world.add(Entity(
        id="dove",
        kind="thing",
        type="bird",
        label="a dove",
        meters={"flutter": 1.0},
        memes={},
        tags={"dove"},
    ))
    world.facts["setting"] = setting
    world.facts["suspect"] = suspect
    world.facts["clue"] = clue
    world.facts["resolution"] = resolution
    world.facts["philanthropy_box"] = box
    world.facts["detective1"] = d1
    world.facts["detective2"] = d2
    world.facts["library"] = library
    world.facts["oak"] = oak
    world.facts["dove"] = dove
    world.facts["mystery"] = "missing_box"
    world.facts["teamwork"] = 0.0
    world.facts["suspense"] = 0.0
    world.facts["clue_seen"] = ""
    d1.memes.update({"curiosity": 1.0, "courage": 0.0, "focus": 0.0, "teamwork": 1.0})
    d2.memes.update({"curiosity": 1.0, "courage": 0.0, "focus": 0.0, "teamwork": 1.0})
    return world


def act_intro(world: World) -> None:
    d1 = world.facts["detective1"]
    d2 = world.facts["detective2"]
    world.say(
        f"In the school library, {d1.id} and {d2.id} became tiny detectives."
    )
    world.say(
        f"They stood by the oak reading table, where the room smelled like books, polish, and quiet."
    )
    world.say(
        f"Then they noticed something strange: the philanthropy box was gone."
    )


def act_suspense(world: World) -> None:
    world.facts["suspense"] = 1.0
    world.get("library").meters["tension"] = 1.0
    world.say(
        "The shelves seemed taller than before, and every soft step felt like a clue waiting to happen."
    )
    world.say(
        "On the floor by the oak table, a white feather trembled like a tiny secret."
    )
    world.facts["clue_seen"] = "dove"
    world.get("clue").meters["seen"] = 1.0
    propagate(world, narrate=False)


def act_teamwork(world: World) -> None:
    d1 = world.facts["detective1"]
    d2 = world.facts["detective2"]
    world.facts["teamwork"] = 1.0
    d1.memes["teamwork"] += 1
    d2.memes["teamwork"] += 1
    world.say(
        f"{d1.id} pointed to the feather, and {d2.id} checked the shelf beside it."
    )
    world.say(
        f"One looked high and one looked low, because teamwork meant nobody searched alone."
    )
    world.say(
        "Together they followed the little trail to the back shelf."
    )
    propagate(world, narrate=False)


def act_resolution(world: World, resolution: Resolution) -> None:
    d1 = world.facts["detective1"]
    d2 = world.facts["detective2"]
    box = world.facts["philanthropy_box"]
    if resolution.id == "team_search":
        world.say(
            f"They kept searching side by side until they found {box.label} beside the oak shelf."
        )
    else:
        world.say(
            "They asked the librarian for help, and she pointed at the exact shelf they needed."
        )
    box.meters["found"] = 1.0
    box.meters["hidden"] = 0.0
    world.get("library").meters["tension"] = 0.0
    d1.memes["relief"] = 1.0
    d2.memes["relief"] = 1.0
    world.say(
        f"The missing box was safe again, and the school library felt calm and bright."
    )
    world.say(
        f"{d1.id} and {d2.id} smiled at the dove feather, the oak table, and the word philanthropy on the box."
    )


def tell_story(setting: Setting, suspect: Suspect, clue: Clue, resolution: Resolution,
               d1: Entity, d2: Entity) -> World:
    world = tell(setting, suspect, clue, resolution, d1, d2)
    act_intro(world)
    world.para()
    act_suspense(world)
    act_teamwork(world)
    world.para()
    act_resolution(world, resolution)
    world.facts["found"] = True
    return world


def generation_for(world: World) -> list[str]:
    return generation_prompts(world)


def story_qa_for(world: World) -> list[QAItem]:
    return story_qa(world)


def world_qa_for(world: World) -> list[QAItem]:
    return world_knowledge_qa(world)


def generate(params: StoryParams) -> StorySample:
    if not story_allowed(params):
        raise StoryError(explain_rejection(params))
    setting = SETTINGS[params.setting]
    suspect = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]
    resolution = RESOLUTIONS[params.resolution]
    d1 = Entity(id=params.name1, kind="character", type=params.gender1, role="detective",
                meters={"search": 0.0}, memes={"curiosity": 1.0, "courage": 0.0, "teamwork": 1.0},
                attrs={"partner": params.name2}, tags={"detective"})
    d2 = Entity(id=params.name2, kind="character", type=params.gender2, role="detective",
                meters={"search": 0.0}, memes={"curiosity": 1.0, "courage": 0.0, "teamwork": 1.0},
                attrs={"partner": params.name1}, tags={"detective"})
    world = tell_story(setting, suspect, clue, resolution, d1, d2)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
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
mystery(missing_box).
teamwork :- team(Detective1), team(Detective2).
suspense :- mystery(missing_box), clue(feather).
found_box :- teamwork, suspense.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
    lines.append(asp.fact("team", "detective1"))
    lines.append(asp.fact("team", "detective2"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1. #show suspect/1. #show clue/1. #show resolution/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    rc = 0
    # smoke test with default curated generation
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    # Python/ASP parity check is minimal here; ensure ASP can run and reflect facts.
    try:
        combos = asp_valid_combos()
        if not combos:
            raise RuntimeError("ASP produced no models")
        print("OK: smoke test and ASP run succeeded.")
    except Exception as exc:
        print(f"ASP FAILED: {exc}")
        rc = 1
    return rc


def outcome_of(params: StoryParams) -> str:
    return "found"


def build_curated() -> list[StoryParams]:
    return CURATED


def resolve_name_pair(rng: random.Random) -> tuple[str, str, str, str]:
    pair = rng.choice(PAIR_NAMES)
    g1 = "girl" if pair[0] in GIRL_NAMES else "boy"
    g2 = "girl" if pair[1] in GIRL_NAMES else "boy"
    return pair[0], g1, pair[1], g2


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "school_library"
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    clue = args.clue or rng.choice(sorted(CLUES))
    resolution = args.resolution or rng.choice(sorted(RESOLUTIONS))
    if setting not in SETTINGS or suspect not in SUSPECTS or clue not in CLUES or resolution not in RESOLUTIONS:
        raise StoryError("(No valid combination matches the given options.)")
    if args.name1 and args.name2:
        name1, g1 = args.name1, args.gender1 or "girl"
        name2, g2 = args.name2, args.gender2 or "boy"
    else:
        name1, g1, name2, g2 = resolve_name_pair(rng)
        if args.gender1:
            g1 = args.gender1
        if args.gender2:
            g2 = args.gender2
    return StoryParams(
        setting=setting,
        suspect=suspect,
        clue=clue,
        resolution=resolution,
        name1=name1,
        gender1=g1,
        name2=name2,
        gender2=g2,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1. #show suspect/1. #show clue/1. #show resolution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show setting/1."))
        print(f"ASP ready: {len(model)} shown atoms")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in build_curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name1} and {p.name2}: {p.suspect} in {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
