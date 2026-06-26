#!/usr/bin/env python3
"""
Detective-story world: a small mystery with a special davenport, a conflict,
teamwork, and a bad ending that still resolves the immediate case.

This script models a tiny, child-facing detective domain. The hero follows
clues, interviews helpers, and investigates a suspicious davenport. The story
tension comes from a locked-room disagreement: two suspects want different
things, the team must cooperate to look inside the furniture, and the ending
reveals that the missing item was found but the larger plan went wrong.
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
    kind: str = "thing"  # character | thing | location
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    in_room: str = ""
    locked: bool = False
    opened: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    room: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
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
        import copy as _copy
        return World(
            room=self.room,
            entities=_copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
            fired=set(self.fired),
        )


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    vibe: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Object:
    id: str
    label: str
    phrase: str
    room: str
    clue: str
    secret: str
    suspicious: bool = False


@dataclass
class Tool:
    id: str
    label: str
    use: str
    helps: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    title: str
    missing: str
    culprit: str
    twist: str
    ending: str
    clue_tag: str


SETTINGS = {
    "manor": Setting(
        place="the old manor",
        vibe="quiet and echoing",
        afford={"investigate", "listen", "search"},
    ),
    "station": Setting(
        place="the little train station",
        vibe="busy but hushed",
        afford={"investigate", "question", "search"},
    ),
    "library": Setting(
        place="the town library",
        vibe="soft and careful",
        afford={"investigate", "read", "search"},
    ),
}

OBJECTS = {
    "davenport": Object(
        id="davenport",
        label="davenport",
        phrase="a special davenport with brass handles",
        room="study",
        clue="There was a narrow scratch along one drawer.",
        secret="A folded ticket stub was hidden inside the middle drawer.",
        suspicious=True,
    ),
    "clock": Object(
        id="clock",
        label="clock",
        phrase="an old clock with a blue face",
        room="hall",
        clue="Its hands were stopped at nine.",
        secret="A tiny map was taped behind the clock.",
    ),
    "umbrella": Object(
        id="umbrella",
        label="umbrella stand",
        phrase="a tall umbrella stand",
        room="foyer",
        clue="One umbrella was muddy even though it had not rained.",
        secret="A key ring sat at the bottom of the stand.",
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        use="shine a bright beam into dark corners",
        helps={"search", "investigate"},
    ),
    "notebook": Tool(
        id="notebook",
        label="notebook",
        use="write down clues",
        helps={"question", "investigate"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        use="look closely at tiny marks",
        helps={"search", "investigate"},
    ),
}

CASES = {
    "special_davenport": Case(
        id="special_davenport",
        title="The Special Davenport",
        missing="a silver key",
        culprit="the butler",
        twist="the key was moved to keep it safe, but nobody told the others",
        ending="the key was found, yet the honest plan collapsed into a bad ending",
        clue_tag="special",
    ),
    "midnight_note": Case(
        id="midnight_note",
        title="The Midnight Note",
        missing="a torn note",
        culprit="the secretary",
        twist="the note was split in two, and each half was hidden in a different room",
        ending="the note was found, but the argument ruined the surprise",
        clue_tag="conflict",
    ),
}

HERO_NAMES = ["Mina", "Owen", "Tara", "Jules", "Nina", "Ezra"]
HELPER_NAMES = ["Ada", "Sam", "Rin", "Bea", "Tom"]
SUSPECT_NAMES = ["Mr. Vale", "Ms. Finch", "Mr. Reed", "Mrs. Cole"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    case: str
    hero_name: str
    helper_name: str
    suspect_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def valid_cases() -> list[tuple[str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for cid, c in CASES.items():
            if c.clue_tag in {"special", "conflict"} and "investigate" in s.afford:
                out.append((sid, cid))
    return out


def explain_rejection(setting: Setting, case: Case) -> str:
    return f"(No story: {setting.place} cannot support a detective case like {case.title!r}.)"


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    case = CASES[params.case]
    w = World(room=setting.place)

    hero = w.add(Entity(id="hero", kind="character", type="girl", label=params.hero_name))
    helper = w.add(Entity(id="helper", kind="character", type="boy", label=params.helper_name))
    suspect = w.add(Entity(id="suspect", kind="character", type="man", label=params.suspect_name))
    davenport = w.add(Entity(
        id="davenport",
        kind="thing",
        type="thing",
        label="davenport",
        phrase=OBJECTS["davenport"].phrase,
        in_room="study",
        locked=True,
    ))
    key = w.add(Entity(
        id="key",
        kind="thing",
        type="thing",
        label="silver key",
        phrase="a small silver key",
        owner="unknown",
        in_room="davenport",
    ))

    hero.memes["curiosity"] = 1
    helper.memes["helpfulness"] = 1
    suspect.memes["worry"] = 1
    davenport.meters["mystery"] = 1
    davenport.meters["special"] = 1

    # Act 1
    w.say(
        f"{hero.label} was a small detective who loved quiet clues and neat answers. "
        f"{hero.pronoun().capitalize()} had a helper named {helper.label}, and together "
        f"they went to {setting.place}, which felt {setting.vibe}."
    )
    w.say(
        f"In the study stood {OBJECTS['davenport'].phrase}. Everyone called it special, "
        f"because it sat by the wall like it had secrets."
    )

    # Act 2
    w.para()
    w.say(
        f"{hero.label} found a scratch on the drawer and a dusty mark on the floor. "
        f"{OBJECTS['davenport'].clue}"
    )
    w.say(
        f"Then {suspect.label} came in and said the davenport should be left alone, "
        f"but {helper.label} wanted to search it at once."
    )
    hero.memes["conflict"] = 1
    helper.memes["conflict"] = 1
    w.facts["conflict"] = True
    w.say(
        f"The room went tense. {hero.label} wanted truth, {suspect.label} wanted silence, "
        f"and the team had to work together before the trail vanished."
    )

    # teamwork and search
    w.para()
    w.say(
        f"{helper.label} held up a flashlight while {hero.label} used a magnifying glass. "
        f"That teamwork let them open the locked drawer without breaking it."
    )
    davenport.opened = True
    key.in_room = "hero"

    # resolution with bad ending
    w.say(OBJECTS["davenport"].secret)
    w.say(
        f"At last they found {case.missing} inside the middle drawer. "
        f"{suspect.label} admitted the truth: {case.twist}."
    )
    w.say(
        f"The mystery was solved, but the ending was a bad one for the room. "
        f"People argued about the secret, the special davenport was moved away, "
        f"and the warm feeling of teamwork faded too soon."
    )
    w.say(
        f"Still, {hero.label} closed {hero.pronoun('possessive')} notebook and said "
        f"that even a bad ending can teach a detective to look carefully next time."
    )

    w.facts.update(
        hero=hero,
        helper=helper,
        suspect=suspect,
        davenport=davenport,
        key=key,
        case=case,
        setting=setting,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a detective story for a young child that features a special davenport and the word "special".',
        f"Tell a short mystery where {hero.label} and a helper solve a conflict by using teamwork around a davenport.",
        f"Write a child-friendly detective tale with a bad ending, but make the clue chase feel clear and concrete.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, suspect, case = f["hero"], f["helper"], f["suspect"], f["case"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {hero.label}, who looked for clues in {world.room}.",
        ),
        QAItem(
            question=f"What special piece of furniture was important in the mystery?",
            answer=f"The special piece of furniture was the davenport, and it hid the clue in a drawer.",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} solve the problem?",
            answer=(
                f"They solved it by teamwork: {helper.label} held a flashlight while "
                f"{hero.label} used a magnifying glass to search the davenport."
            ),
        ),
        QAItem(
            question=f"Why did the story have a conflict?",
            answer=(
                f"There was conflict because {suspect.label} wanted the davenport left alone, "
                f"but the detective team wanted to search it for the missing {case.missing}."
            ),
        ),
        QAItem(
            question=f"What made the ending a bad ending?",
            answer=(
                f"The missing item was found, but the truth caused arguing and the special "
                f"davenport had to be moved away, so the happy feeling did not last."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="Why do detectives use a magnifying glass?",
            answer="Detectives use a magnifying glass to look closely at tiny marks and details.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do different jobs to reach the same goal.",
        ),
        QAItem(
            question="What is a davenport?",
            answer="A davenport is a kind of sofa or writing desk in older stories, and it can hide things in its drawers.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.in_room:
            bits.append(f"in_room={e.in_room}")
        if e.locked:
            bits.append("locked=True")
        if e.opened:
            bits.append("opened=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A case is valid if the setting supports investigation and the case is one of
% the detective-style stories in this tiny domain.
valid_case(S, C) :- setting(S), case(C), affords(S, investigate).

% The story has conflict when the suspect resists the search.
has_conflict(C) :- case(C), clue_tag(C, conflict).

% Teamwork is available when the case involves a search and a helper tool exists.
has_teamwork(C) :- case(C), tool(magnifier), tool(flashlight).

% A bad ending is allowed when the mystery is solved but the social outcome is
% still unhappy.
bad_ending(C) :- case(C), ending_tag(C, bad).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("clue_tag", cid, c.clue_tag))
        lines.append(asp.fact("ending_tag", cid, "bad"))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_case/2."))
    return sorted(set(asp.atoms(model, "valid_case")))


def asp_verify() -> int:
    py = set(valid_cases())
    cl = set(asp_valid_cases())
    if py == cl:
        print(f"OK: clingo gate matches valid_cases() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Sampling / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with a special davenport.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
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
    combos = valid_cases()
    combos = [
        (s, c)
        for (s, c) in combos
        if (args.setting is None or args.setting == s)
        and (args.case is None or args.case == c)
    ]
    if not combos:
        raise StoryError("(No valid story matches the requested options.)")
    setting, case = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        case=case,
        hero_name=args.name or rng.choice(HERO_NAMES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        suspect_name=args.suspect or rng.choice(SUSPECT_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="manor", case="special_davenport", hero_name="Mina", helper_name="Sam", suspect_name="Mr. Vale"),
    StoryParams(setting="library", case="midnight_note", hero_name="Jules", helper_name="Ada", suspect_name="Ms. Finch"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_case/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show valid_case/2."))
        print(f"{len(asp_valid_cases())} valid cases")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                p = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
