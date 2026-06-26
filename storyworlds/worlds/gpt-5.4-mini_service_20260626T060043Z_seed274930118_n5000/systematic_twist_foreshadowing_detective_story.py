#!/usr/bin/env python3
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


@dataclass
class Character:
    id: str
    kind: str = "character"
    role: str = ""
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        pronouns = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return pronouns[case]


@dataclass
class Setting:
    place: str
    detail: str
    affordance: str


@dataclass
class Suspect:
    id: str
    label: str
    alibi: str
    habit: str
    clue: str
    hidden_truth: str


@dataclass
class Twist:
    reveal: str
    reframe: str
    proof: str


@dataclass
class StoryParams:
    setting: str
    case: str
    detective: str
    assistant: str
    suspect: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "library": Setting("the old library", "Dusty shelves leaned over a quiet reading table.", "paper trails"),
    "museum": Setting("the small museum", "Glass cases glimmered under bright lamps.", "careful footsteps"),
    "station": Setting("the train station", "Announcements echoed above the waiting benches.", "arrival times"),
}

CASES = {
    "missing cookie": "A tin of cookies vanished from the table.",
    "broken vase": "A vase on the windowsill had split into neat pieces.",
    "lost key": "A brass key was gone from the drawer.",
}

DETECTIVES = ["Mina", "Toby", "Iris", "Noah", "Ruby", "Elliot"]
ASSISTANTS = ["Pip", "Juno", "Milo", "Lark", "Nina", "Otto"]

SUSPECTS = {
    "librarian": Suspect(
        id="librarian",
        label="the librarian",
        alibi="they were stamping books in the back room",
        habit="always wore ink on their fingers",
        clue="a page corner had a blue ink smudge",
        hidden_truth="the ink came from a broken label, not from stealing anything",
    ),
    "janitor": Suspect(
        id="janitor",
        label="the janitor",
        alibi="they were polishing the floor near the stairs",
        habit="carried a bright yellow mop bucket",
        clue="a wet footprint looked suspicious near the hall",
        hidden_truth="the wet footprint came from the mop bucket",
    ),
    "traveler": Suspect(
        id="traveler",
        label="the traveler",
        alibi="they were buying a ticket at the desk",
        habit="kept a tiny compass in their coat pocket",
        clue="a compass-shaped shadow flashed under the bench",
        hidden_truth="the shadow was from a hanging sign, not a hidden tool",
    ),
}

TWISTS = {
    "librarian": Twist(
        reveal="The missing clue was not stolen at all; it had been tucked into a returned book.",
        reframe="Every careful note had pointed the detective toward the shelf, not toward a thief.",
        proof="The book's bookmark matched the torn scrap exactly.",
    ),
    "janitor": Twist(
        reveal="The broken object was not caused by clumsy hands; it had cracked from a small bump during cleaning.",
        reframe="The wet trail was a cleaning trail, not a getaway trail.",
        proof="The floor was freshly wiped, and the broken edge was clean.",
    ),
    "traveler": Twist(
        reveal="The lost item had been packed by mistake into a travel bag.",
        reframe="The strange shadow was only baggage shifting under the bench.",
        proof="The bag tag matched the missing item's label.",
    ),
}


ASP_RULES = r"""
setting(library).
setting(museum).
setting(station).

case("missing cookie").
case("broken vase").
case("lost key").

suspect(librarian).
suspect(janitor).
suspect(traveler).

works_in(librarian,library).
works_in(janitor,museum).
works_in(traveler,station).

twist(librarian).
twist(janitor).
twist(traveler).

has_clue(librarian,ink_smudge).
has_clue(janitor,wet_footprint).
has_clue(traveler,shadow).

systematic_case(S) :- suspect(S), has_clue(S,_), twist(S).
#show systematic_case/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("twist", sid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("has_clue", sid, s.clue.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_systematic_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show systematic_case/1."))
    return sorted(set(asp.atoms(model, "systematic_case")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A systematic detective story with foreshadowing and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--assistant", choices=ASSISTANTS)
    ap.add_argument("--suspect", choices=SUSPECTS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, cid) for sid in SETTINGS for cid in CASES for _ in [0] if sid in SETTINGS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    case = args.case or rng.choice(list(CASES))
    detective = args.detective or rng.choice(DETECTIVES)
    assistant = args.assistant or rng.choice(ASSISTANTS)
    return StoryParams(setting=setting, case=case, detective=detective, assistant=assistant, suspect=suspect)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    detective = world.add(Character(id=params.detective, role="detective", label=params.detective, traits=["systematic", "careful"]))
    assistant = world.add(Character(id=params.assistant, role="assistant", label=params.assistant, traits=["quick", "observant"]))
    suspect = SUSPECTS[params.suspect]
    world.facts.update(params=params, detective=detective, assistant=assistant, suspect=suspect, case=params.case, twist=TWISTS[params.suspect])

    intro = f"{detective.label} was a systematic detective who liked to solve every case step by step."
    clue_line = f"At {world.setting.place}, {world.setting.detail} {CASES[params.case].lower()}"
    foreshadow = f"{assistant.label} noticed {suspect.clue}, and that little detail felt important."
    suspicion = f"{detective.label} asked about {suspect.label}, because {suspect.habit} sounded like a possible clue."
    middle = f"But the clue did not fit neatly at first, and the story kept a careful, foreshadowed feeling."

    reveal = TWISTS[params.suspect]
    turn = f"Then came the twist: {reveal.reveal}"
    proof = f"{reveal.proof} {reveal.reframe}"
    ending = f"In the end, {detective.label} smiled, {assistant.label} breathed easier, and the case finally made sense."

    world.say(intro)
    world.say(clue_line)
    world.say(foreshadow)
    world.para()
    world.say(suspicion)
    world.say(middle)
    world.para()
    world.say(turn)
    world.say(proof)
    world.say(ending)

    story_qa = [
        QAItem(
            question=f"What kind of detective was {detective.label}?",
            answer=f"{detective.label} was a systematic detective who solved problems step by step.",
        ),
        QAItem(
            question=f"What clue did {assistant.label} notice?",
            answer=f"{assistant.label} noticed {suspect.clue}. That foreshadowed the twist later in the story.",
        ),
        QAItem(
            question="What was the twist in the case?",
            answer=reveal.reveal + " " + reveal.proof,
        ),
    ]
    world_qa = [
        QAItem(
            question="What does it mean to be systematic?",
            answer="Being systematic means doing things in a careful order, so you do not miss important details.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue that hints something important will happen later.",
        ),
        QAItem(
            question="What is a twist in a mystery story?",
            answer="A twist is a surprising turn that changes what the reader thought was true.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a short detective story with a systematic investigation, foreshadowing, and a twist.",
            f"Tell a child-friendly mystery set at {world.setting.place} with a careful clue and a surprise ending.",
            f"Write a simple detective tale about {params.detective} and {params.assistant} solving a {params.case}.",
        ],
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: role={getattr(e, 'role', '')} traits={getattr(e, 'traits', [])}")
    lines.append(f"setting: {world.setting.place}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    got = set(asp_systematic_cases())
    want = {("systematic_case", sid) for sid in SUSPECTS}
    if got == want:
        print(f"OK: ASP and Python agree on {len(got)} systematic cases.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(got))
    print("Python:", sorted(want))
    return 1


CURATED = [
    StoryParams(setting="library", case="missing cookie", detective="Mina", assistant="Pip", suspect="librarian"),
    StoryParams(setting="museum", case="broken vase", detective="Iris", assistant="Juno", suspect="janitor"),
    StoryParams(setting="station", case="lost key", detective="Noah", assistant="Lark", suspect="traveler"),
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
        print(asp_program("#show systematic_case/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_systematic_cases())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
