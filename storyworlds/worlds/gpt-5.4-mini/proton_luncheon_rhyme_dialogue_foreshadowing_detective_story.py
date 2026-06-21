#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/proton_luncheon_rhyme_dialogue_foreshadowing_detective_story.py
==============================================================================================

A tiny detective-story world about a careful kid sleuth at a luncheon, where a
missing proton clue points to the wrong place at first, then the real culprit is
found by following small clues, dialogue, rhyme, and a foreshadowed detail.

The world is deliberately small and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model that drives the prose
- grounded Q&A sets built from world state, not by parsing rendered text
- a Python reasonableness gate with an inline ASP twin
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
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
class Setting:
    id: str
    place: str
    mood: str
    lunch_item: str
    clue_spot: str

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
class Suspect:
    id: str
    label: str
    alibi: str
    told_line: str
    rhyme_line: str
    foreshadow_line: str
    guilty: bool = False
    obvious: bool = False

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
class Clue:
    id: str
    label: str
    placed_at: str
    reveals: str
    hint_line: str

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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
    out: list[str] = []
    if world.facts.get("clue_found") and not world.facts.get("case_solved"):
        sig = ("worry", "clue")
        if sig in world.fired:
            return out
        world.fired.add(sig)
        for name in ("sleuth", "assistant"):
            if name in world.entities:
                world.get(name).memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_solution(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("case_solved") and "sleuth" in world.entities:
        sleuth = world.get("sleuth")
        if sleuth.meters["certainty"] < THRESHOLD:
            sleuth.meters["certainty"] += 1
            out.append("__certainty__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("solution", "social", _r_solution),
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


def predict(world: World, clue: Clue, suspect: Suspect) -> dict:
    sim = world.copy()
    sim.facts["clue_found"] = True
    sim.facts["case_solved"] = suspect.guilty
    propagate(sim, narrate=False)
    return {
        "solves": suspect.guilty,
        "worry": sim.get("sleuth").memes["worry"] if "sleuth" in sim.entities else 0,
    }


def rhyme_line(clue: Clue, suspect: Suspect) -> str:
    return f"At luncheon, the clues must shine and chime; {clue.hint_line} {suspect.rhyme_line}"


def intro(world: World, setting: Setting, sleuth: Entity, assistant: Entity) -> None:
    world.say(
        f"At {setting.place}, under a soft and sunny ceiling, {sleuth.id} and {assistant.id} "
        f"came to a luncheon that smelled of {setting.lunch_item}."
    )
    world.say(
        f'{assistant.id} whispered, "A tidy table, a tip-top place, but something here has a hidden face."'
    )
    world.say(
        f"{sleuth.id} smiled. \"Then we'll look with care,\" {sleuth.pronoun()} said, "
        f"\"for every small thing tells a tale.\""
    )


def foreshadow(world: World, setting: Setting, suspect: Suspect, clue: Clue) -> None:
    world.say(
        f"Before the plates were cleared, {suspect.foreshadow_line} "
        f"{clue.hint_line}"
    )


def discover_clue(world: World, clue: Clue) -> None:
    world.facts["clue_found"] = True
    world.get("clue").meters["noticed"] += 1
    world.say(
        f"{clue.placed_at.capitalize()}, {clue.label} was spotted, and it seemed to point toward {clue.reveals}."
    )


def dialogue_probe(world: World, sleuth: Entity, assistant: Entity, suspect: Suspect) -> None:
    world.say(
        f'{assistant.id} asked, "Did you see the missing proton?"'
    )
    world.say(
        f'"I did," said {suspect.id}. "{suspect.told_line}"'
    )
    world.say(
        f'"Hmm," said {sleuth.id}, "your story is neat, but neat stories can still hide a snag."'
    )


def solve_case(world: World, sleuth: Entity, assistant: Entity, suspect: Suspect, clue: Clue) -> None:
    world.facts["case_solved"] = True
    suspect_ent = world.get(suspect.id)
    suspect_ent.memes["guilt"] += 1
    sleuth.meters["certainty"] += 1
    world.say(
        f"{sleuth.id} tapped the clue and said, \"The proton wasn't stolen at all. It rolled where the silver tray leaned.\""
    )
    world.say(
        f"{assistant.id} gasped. \"So the rhyme was true! The little shine hid in plain view.\""
    )
    world.say(
        f"Then {suspect.id} admitted the truth: {suspect.alibi}."
    )


def ending(world: World, setting: Setting, sleuth: Entity, assistant: Entity, suspect: Suspect, clue: Clue) -> None:
    if world.facts.get("case_solved"):
        world.say(
            f"The luncheon ended with the proton back on its little display stand, and the table sparkled clean again."
        )
        world.say(
            f"{sleuth.id} and {assistant.id} walked out smiling, with one mystery smaller and one bright clue remembered."
        )
    else:
        world.say(
            f"The luncheon ended in a hush, and the missing proton still cast a small shadow on the table."
        )


def tell(setting: Setting, suspect: Suspect, clue: Clue, name: str, assistant_name: str,
         parent_type: str = "mother") -> World:
    world = World()
    sleuth = world.add(Entity("sleuth", kind="character", type="boy", role="detective", label=name))
    assistant = world.add(Entity("assistant", kind="character", type="girl", role="helper", label=assistant_name))
    parent = world.add(Entity("Parent", kind="character", type=parent_type, role="adult", label="the parent"))
    proton = world.add(Entity("proton", kind="thing", type="thing", label="the proton"))
    world.add(Entity("clue", kind="thing", type="thing", label=clue.label))
    world.facts.update(setting=setting, suspect=suspect, clue=clue, proton=proton, parent=parent)

    intro(world, setting, sleuth, assistant)
    world.para()
    foreshadow(world, setting, suspect, clue)
    dialogue_probe(world, sleuth, assistant, suspect)
    world.para()
    discover_clue(world, clue)
    propagate(world, narrate=True)
    if suspect.guilty:
        solve_case(world, sleuth, assistant, suspect, clue)
    else:
        world.say(
            f"{suspect.id} was only a witness, and {suspect.alibi}."
        )
    world.para()
    ending(world, setting, sleuth, assistant, suspect, clue)
    world.facts.update(case_solved=suspect.guilty, clue_found=True)
    return world


SETTINGS = {
    "museum": Setting("museum", "the museum hall", "quiet", "pea soup and rolls", "near the silver tray"),
    "garden_room": Setting("garden_room", "the garden room", "bright", "strawberry tarts", "beside the brass lamp"),
    "station": Setting("station", "the old station", "echoing", "sandwiches and juice", "under the timetable"),
}

SUSPECTS = {
    "butler": Suspect(
        "butler",
        "the butler",
        "he was polishing the cups",
        "“I was in the pantry, busy and neat.”",
        "A shiny tray, a clever lie; listen close and watch it slide.",
        "“If a tray should tilt and gleam, look where little things might stream.”",
        guilty=False,
        obvious=False,
    ),
    "guest": Suspect(
        "guest",
        "the guest",
        "she was near the tablecloth",
        "“I only helped with the napkins.”",
        "A napkin hums, a ribbon sings; clues can hide in small, bright things.",
        "“If a ribbon twirls and bends, follow where the silver ends.”",
        guilty=False,
        obvious=False,
    ),
    "chef": Suspect(
        "chef",
        "the chef",
        "he was serving the luncheon",
        "“I set the plates down one by one.”",
        "A spoon can blink, a spoon can glow; the best clues are the ones that show.",
        "“If a spoon bumps softly near, watch the tray and hold your ear.”",
        guilty=True,
        obvious=True,
    ),
}

CLUES = {
    "tray": Clue("tray", "a silver tray scratch", "On the floor", "the leaning silver tray",
                 "A tray that leans can make tiny things roll"),
    "napkin": Clue("napkin", "a folded napkin corner", "By a chair", "the guest's table",
                   "A folded corner can point where hands were busy"),
    "spoon": Clue("spoon", "a small spoon mark", "Beside the dish", "the serving line",
                  "A spoon mark can tell who moved too quickly"),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "June", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Max", "Ben", "Leo"]
TRAITS = ["curious", "careful", "brave", "patient", "sharp-eyed"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for kid in SUSPECTS:
            for cid in CLUES:
                if kid == "chef" or cid == "tray":
                    combos.append((sid, kid, cid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    suspect: str
    clue: str
    detective: str
    assistant: str
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
    ap = argparse.ArgumentParser(description="Detective luncheon storyworld with rhyme, dialogue, and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--detective")
    ap.add_argument("--assistant")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, suspect, clue = rng.choice(sorted(combos))
    detective = args.detective or rng.choice(BOY_NAMES)
    assistant = args.assistant or rng.choice(GIRL_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, suspect, clue, detective, assistant, parent, trait)


def explain_rejection(suspect: Suspect, clue: Clue) -> str:
    return (
        f"(No story: this clue would not fit a clean detective beat. "
        f"Try the tray clue with the chef so the foreshadowing can pay off.)"
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SUSPECTS[params.suspect], CLUES[params.clue],
                 params.detective, params.assistant, params.parent)
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
    setting = f["setting"]
    suspect = f["suspect"]
    clue = f["clue"]
    return [
        f'Write a detective story for a young child set at {setting.place} that includes the words "proton" and "luncheon".',
        f"Tell a rhyming mystery with dialogue where {suspect.id} gives a suspicious answer and a small clue about {clue.reveals} later proves what really happened.",
        f"Write a gentle mystery where foreshadowing at a luncheon helps solve the case, ending with the proton safely found.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    suspect: Suspect = f["suspect"]
    clue: Clue = f["clue"]
    setting: Setting = f["setting"]
    qa = [
        ("Where does the story take place?",
         f"It takes place at {setting.place}, during a luncheon with a careful detective at the table."),
        ("What mystery do they try to solve?",
         "They try to find the missing proton and figure out who moved it. The little clue at the luncheon helps them do that."),
        ("What did the clue point toward?",
         f"It pointed toward {clue.reveals}, and that made the detective look there first."),
    ]
    if world.facts.get("case_solved"):
        qa.append((
            "How did they solve the case?",
            f"They listened to the dialogue, remembered the foreshadowed hint, and followed {clue.label} to the right spot. "
            f"That led them to the truth about {suspect.id}."
        ))
        qa.append((
            "How did the story end?",
            "It ended with the proton safely back on display and the table tidy again. "
            "The mystery got smaller, and the luncheon ended in a happy, clear way."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a proton?",
         "A proton is a tiny part of an atom. Tiny things like protons are too small to see with your eyes."),
        ("What is a luncheon?",
         "A luncheon is a meal eaten around midday, a bit like a lunch gathering."),
        ("What is foreshadowing?",
         "Foreshadowing is a clue that hints at something important before it happens."),
        ("Why do detectives listen carefully?",
         "Detectives listen carefully because clues can hide in words, sounds, and small details."),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("museum", "chef", "tray", "Theo", "Mia", "mother", "curious"),
    StoryParams("garden_room", "chef", "tray", "Finn", "Lily", "father", "careful"),
    StoryParams("station", "chef", "tray", "Eli", "Nora", "mother", "sharp-eyed"),
]


def valid_story(params: StoryParams) -> bool:
    return params.suspect in SUSPECTS and params.clue in CLUES and params.setting in SETTINGS


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for kid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", kid))
        if s.guilty:
            lines.append(asp.fact("guilty", kid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, K, C) :- setting(S), suspect(K), clue(C), (K = chef; C = tray).
solved(K) :- guilty(K).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, suspect=None, clue=None, detective=None, assistant=None,
            parent=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, k, c in combos:
            print(f"  {s:12} {k:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.detective}: {p.setting} / {p.suspect} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
