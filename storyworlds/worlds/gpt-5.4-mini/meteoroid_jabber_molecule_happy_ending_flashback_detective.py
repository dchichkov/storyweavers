#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/meteoroid_jabber_molecule_happy_ending_flashback_detective.py
=============================================================================================

A standalone storyworld for a tiny detective tale: a child detective hears too
much jabber, remembers a flashback about a museum model, and solves a mystery
about a missing meteoroid display by noticing a molecule-like clue. The domain
is intentionally small, state-driven, and child-facing, with a happy ending.

Seed words:
- meteoroid
- jabber
- molecule

Features:
- Happy Ending
- Flashback

Style:
- Detective Story
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

THRESHOLD = 1.0
ASP_RULES = r"""
% The declarative twin of the Python reasonableness gate.
valid_case(S) :- setting(S), clue(C), suspect(X), has_link(C, X).
solution_found :- clue(molecule), flashback(yes), happy(yes).
"""

# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    mood: str


@dataclass(frozen=True)
class Clue:
    id: str
    label: str
    phrase: str
    meaning: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Suspect:
    id: str
    label: str
    phrase: str
    motive: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Response:
    id: str
    label: str
    text: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "museum": Setting("museum", "the small museum", "quiet and echoey"),
    "school": Setting("school", "the science room", "bright and busy"),
    "library": Setting("library", "the library hallway", "still and whispery"),
}

CLUES = {
    "molecule": Clue(
        "molecule",
        "tiny model molecule",
        "a tiny model molecule with one loose bead",
        "it came from the science display",
        tags={"molecule", "science"},
    ),
    "dust": Clue(
        "dust",
        "dusty footprint",
        "a dusty footprint near the case",
        "someone had walked there recently",
        tags={"dust"},
    ),
    "tag": Clue(
        "tag",
        "name tag",
        "a bent name tag behind the bench",
        "a clue from the display case",
        tags={"tag"},
    ),
}

SUSPECTS = {
    "jabber": Suspect(
        "jabber",
        "jabbering kid",
        "a jabbering kid who talked too fast",
        "he had been near the case earlier",
        tags={"jabber", "talking"},
    ),
    "custodian": Suspect(
        "custodian",
        "kind custodian",
        "the kind custodian who had a key ring",
        "she knew where everything belonged",
        tags={"key", "help"},
    ),
}

RESPONSES = {
    "ask": Response(
        "ask",
        "ask kindly",
        "asked carefully and listened to the answer",
        tags={"help"},
    ),
    "check": Response(
        "check",
        "check the display",
        "checked the display and found the missing piece",
        tags={"science"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lila", "Ava", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Ben", "Finn"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    response: str
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


# ---------------------------------------------------------------------------
# Rule helpers
# ---------------------------------------------------------------------------


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for x in SUSPECTS:
                if c == "molecule" and x == "jabber":
                    combos.append((s, c, x))
    return combos


def reasonableness_ok(params: StoryParams) -> bool:
    return (params.clue in CLUES and params.suspect in SUSPECTS and
            (params.setting, params.clue, params.suspect) in valid_combos())


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for x in SUSPECTS:
        lines.append(asp.fact("suspect", x))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
    lines.append(asp.fact("flashback", "yes"))
    lines.append(asp.fact("happy", "yes"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_case/1."))
    return sorted(set(asp.atoms(model, "valid_case")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    try:
        cl = set(asp_valid_combos())
    except Exception as e:
        print(f"ASP failure: {e}")
        return 1
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("python:", sorted(py))
        print("clingo:", sorted(cl))
    # smoke test: generate a normal story
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story.strip()
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------


def tell(params: StoryParams) -> World:
    if not reasonableness_ok(params):
        raise StoryError("No story: the detective clue and suspect do not make a fair mystery.")
    w = World()
    det = w.add(Entity(params.detective, "character", params.detective_gender, role="detective"))
    helper = w.add(Entity(params.helper, "character", params.helper_gender, role="helper"))
    room = w.add(Entity("room", "room", label=SETTINGS[params.setting].place))
    clue = w.add(Entity("clue", "thing", label=CLUES[params.clue].label))
    suspect = w.add(Entity("suspect", "character", "boy" if params.suspect == "jabber" else "girl",
                           role=params.suspect))
    det.memes["curiosity"] = 1
    helper.memes["caution"] = 1
    w.say(f"On a quiet afternoon, {det.id} and {helper.id} were in {SETTINGS[params.setting].place}.")
    w.say(f"The place felt {SETTINGS[params.setting].mood}, and {det.id} was trying to solve a small mystery.")
    w.say(f"A flashback came to {det.id}: yesterday, {helper.id} had pointed at {CLUES[params.clue].phrase} and said it might matter.")
    w.para()
    w.say(f"Then {suspect.id} started to {('jabber and wave his hands' if params.suspect == 'jabber' else 'carry a key ring and look nervous')}.")
    w.say(f"{det.id} listened closely, because detective work is about hearing what other people rush past.")
    w.say(f"{det.id} asked kindly, and {helper.id} checked the display.")
    w.say("Under the glass, one tiny piece was missing, and it matched the loose bead from the model.")
    w.para()
    w.say(f"The missing piece had not been stolen at all; it had fallen behind the bench.")
    w.say(f"{suspect.id} smiled in relief when the little clue was found, and the room felt bright again.")
    w.say(f"In the end, {det.id} put the bead back where it belonged, and everyone laughed because the mystery had a happy ending.")
    w.facts.update(
        detective=det, helper=helper, setting=params.setting, clue=params.clue,
        suspect=params.suspect, response=params.response, room=room, clue_ent=clue,
        suspect_ent=suspect, flashback=True, happy=True, solved=True
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child detective story that includes the words "{f["clue"]}", "{f["suspect"]}", and "molecule".',
        f'Tell a happy mystery in which {f["detective"].id} remembers a flashback and solves a small puzzle about a science display.',
        f'Write a detective story for a young child where too much jabber hides the answer at first, but a clue brings a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, helper = f["detective"], f["helper"]
    suspect = f["suspect_ent"]
    return [
        QAItem(
            question="Who solved the mystery?",
            answer=f"{det.id} solved it by listening carefully and following the science clue. {det.id} used a flashback about yesterday to remember where the missing piece had been."
        ),
        QAItem(
            question="Why did the clue matter?",
            answer="The clue mattered because it pointed to the missing piece that had fallen behind the bench. That is what helped the detective stop guessing and find the real answer."
        ),
        QAItem(
            question=f"What did {helper.id} do?",
            answer=f"{helper.id} checked the display and helped point out the little piece that was missing. That careful help made the mystery easy to finish."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a meteoroid?",
            answer="A meteoroid is a small rock from space. It can fly through the sky before it becomes a meteor or lands on the ground."
        ),
        QAItem(
            question="What is a molecule?",
            answer="A molecule is a tiny piece that helps make up everything around us, like water and air. You cannot usually see one without special tools."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something from before the present moment. It helps the reader remember an important clue."
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


# ---------------------------------------------------------------------------
# Parser / resolution / generation
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective storyworld with a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--response", choices=RESPONSES)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")
    setting, clue, suspect = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if detective_gender == "girl" else "girl")
    detective = args.detective or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    response = args.response or "check"
    return StoryParams(setting, clue, suspect, response, detective, detective_gender, helper, helper_gender)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams("museum", "molecule", "jabber", "check", "Mia", "girl", "Noah", "boy"),
    StoryParams("school", "molecule", "jabber", "ask", "Eli", "boy", "Ava", "girl"),
    StoryParams("library", "molecule", "jabber", "check", "Nora", "girl", "Finn", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid_case/1.\n#show solution_found/0."))
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
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
