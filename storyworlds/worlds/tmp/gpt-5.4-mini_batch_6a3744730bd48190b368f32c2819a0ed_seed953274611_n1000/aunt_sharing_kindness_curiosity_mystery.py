#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/aunt_sharing_kindness_curiosity_mystery.py
===========================================================================

A small mystery storyworld about a child, an aunt, and a puzzling missing item
that is found through curiosity, sharing, and kindness.

The story premise:
- A child notices something missing or odd.
- An aunt invites careful curiosity instead of guessing.
- The child shares clues and kindness helps someone else.
- The mystery is solved with a concrete ending image that proves what changed.

This is a standalone, stdlib-only script using the shared Storyweavers result
containers and the shared ASP helper.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CURIOSITY_MIN = 1.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    detail: str
    hiding_spot: str
    hush: str


@dataclass
class Mystery:
    id: str
    missing: str
    clue: str
    found_in: str
    found_under: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpAct:
    id: str
    kind: str
    text: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


@dataclass
class StoryParams:
    setting: str
    mystery: str
    help_act: str
    child_name: str
    child_gender: str
    aunt_name: str
    aunt_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        place="the bedroom",
        detail="The room was quiet except for the soft tick of a small clock.",
        hiding_spot="under the bed",
        hush="the little rug by the bed",
    ),
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        detail="The kitchen smelled like warm toast and had bright window light.",
        hiding_spot="inside the bread box",
        hush="the sugar jar",
    ),
    "porch": Setting(
        id="porch",
        place="the porch",
        detail="The porch had two creaky chairs and a little shelf of odds and ends.",
        hiding_spot="behind the watering can",
        hush="the flower pot",
    ),
}

MYSTERIES = {
    "missing_note": Mystery(
        id="missing_note",
        missing="a folded note",
        clue="a trail of little pencil dots",
        found_in="the book basket",
        found_under="a stack of picture books",
        ending_image="The folded note was back on the table, opened flat beside a cup of tea.",
        tags={"note", "paper", "mystery"},
    ),
    "lost_key": Mystery(
        id="lost_key",
        missing="a brass key",
        clue="a shiny scratch mark on the floor",
        found_in="the tin box",
        found_under="a dish towel",
        ending_image="The brass key was hanging on a ribbon by the hook, safe and easy to find.",
        tags={"key", "metal", "mystery"},
    ),
    "vanished_cookie": Mystery(
        id="vanished_cookie",
        missing="a round cookie",
        clue="a few crumbs in a neat line",
        found_in="the cookie jar",
        found_under="a folded napkin",
        ending_image="The cookie jar sat open, and a fresh plate of shared cookies waited on the counter.",
        tags={"cookie", "crumbs", "mystery"},
    ),
}

HELP_ACTS = {
    "share_lamp": HelpAct(
        id="share_lamp",
        kind="sharing",
        text="she shared a little lamp so they could look without bumping into things",
        result="The lamp made a soft gold pool of light.",
        tags={"light", "sharing"},
    ),
    "share_cookie": HelpAct(
        id="share_cookie",
        kind="sharing",
        text="she shared a cookie with the child to keep the search kind and calm",
        result="The child smiled and kept looking carefully.",
        tags={"sharing", "kindness"},
    ),
    "tidy_together": HelpAct(
        id="tidy_together",
        kind="kindness",
        text="they tidied the area together so the missing thing would be easier to spot",
        result="The clutter moved aside, and the clue could finally be seen.",
        tags={"kindness", "help"},
    ),
    "ask_gently": HelpAct(
        id="ask_gently",
        kind="curiosity",
        text="she asked gentle questions and listened to every answer",
        result="Each answer made the mystery a little clearer.",
        tags={"curiosity", "listening"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Sam", "Eli"]
AUNT_NAMES = ["Aunt June", "Aunt Marla", "Aunt Tessa", "Aunt Bea"]
CHILD_TRAITS = ["curious", "kind", "careful", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for h in HELP_ACTS:
                out.append((s, m, h))
    return out


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the requested mystery setup could not be built.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: aunt, sharing, kindness, curiosity, and a small mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--help-act", choices=HELP_ACTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--aunt-name")
    ap.add_argument("--aunt-gender", choices=["aunt"])
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
              and (args.mystery is None or c[1] == args.mystery)
              and (args.help_act is None or c[2] == args.help_act)]
    if not combos:
        raise StoryError(explain_rejection(StoryParams(setting="", mystery="", help_act="", child_name="", child_gender="", aunt_name="", aunt_gender="")))
    setting, mystery, help_act = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    aunt_name = args.aunt_name or rng.choice(AUNT_NAMES)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        help_act=help_act,
        child_name=child_name,
        child_gender=gender,
        aunt_name=aunt_name,
        aunt_gender="aunt",
    )


def tell(setting: Setting, mystery: Mystery, help_act: HelpAct,
         child_name: str, child_gender: str, aunt_name: str) -> World:
    world = World(setting=setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child",
                              traits=["curious", "kind"], attrs={"relation": "aunt"}))
    aunt = world.add(Entity(id=aunt_name, kind="character", type="aunt", role="aunt",
                             traits=["kind", "patient"]))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=mystery.clue))
    missing = world.add(Entity(id="missing", kind="thing", type="thing", label=mystery.missing))

    child.memes["curiosity"] = 2.0
    child.memes["kindness"] = 1.0
    aunt.memes["kindness"] = 2.0
    world.facts.update(setting=setting, mystery=mystery, help_act=help_act,
                       child=child, aunt=aunt, clue=clue, missing=missing)

    world.say(
        f"On a quiet afternoon in {setting.place}, {child_name} noticed something odd. "
        f"{setting.detail} But {mystery.missing} was gone."
    )
    world.say(
        f'"{mystery.missing}?" {child_name} whispered. '
        f"Then {child_name} looked closer and saw {mystery.clue}."
    )

    world.para()
    child.memes["curiosity"] += 1
    world.say(
        f"{aunt_name} came over and did not laugh at the worry. "
        f'Instead, {aunt_name} said, "Let us look gently and share what we see."'
    )
    world.say(help_act.text + ".")
    world.say(help_act.result)

    world.para()
    world.say(
        f"{child_name} checked {setting.hiding_spot}, while {aunt_name} looked near {setting.hush}. "
        f"That was where the clue made sense."
    )
    world.say(
        f"At last, they found the missing thing {mystery.found_in}, tucked {mystery.found_under}."
    )
    world.say(
        f"{aunt_name} smiled and praised the careful searching. "
        f"{child_name} smiled back, because curiosity had turned into a real answer."
    )

    world.para()
    world.say(mystery.ending_image)
    world.say(
        f"{child_name} kept one clue in mind, but not as a secret this time -- "
        f"{child_name} had shared it with {aunt_name}, and kindness helped solve the mystery."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = f["setting"]
    mystery: Mystery = f["mystery"]
    child: Entity = f["child"]
    aunt: Entity = f["aunt"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old in {setting.place} that includes the word "aunt".',
        f"Tell a gentle mystery where {child.id} notices {mystery.missing}, shares a clue with {aunt.id}, and kindness helps solve it.",
        f'Write a child-sized mystery about curiosity and sharing that ends with {mystery.ending_image.lower()}',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    mystery: Mystery = f["mystery"]
    child: Entity = f["child"]
    aunt: Entity = f["aunt"]
    help_act: HelpAct = f["help_act"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {aunt.id}. They work together to solve a small mystery in {setting.place}.",
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"{mystery.missing} was missing, and that made the room feel puzzling. The child noticed it first and then looked for a clue.",
        ),
        QAItem(
            question="How did the aunt help?",
            answer=f"{aunt.id} helped by being kind and {help_act.kind}. That made the search calm, and calm searching led them to the answer.",
        ),
    ]
    qa.append(
        QAItem(
            question="Why did the clue matter?",
            answer=f"The clue mattered because it gave {child.id} and {aunt.id} a place to look next. Curiosity became useful when they shared what they saw.",
        )
    )
    qa.append(
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {mystery.ending_image.lower()} That ending proves the mystery was solved and the missing thing was found.",
        )
    )
    return qa


WORLD_KNOWLEDGE = {
    "aunt": QAItem(
        question="What is an aunt?",
        answer="An aunt is your mom's or dad's sister, or another grown-up who is part of your family and can be very kind.",
    ),
    "sharing": QAItem(
        question="What is sharing?",
        answer="Sharing means letting someone else use or enjoy something with you. It can make a hard moment feel easier.",
    ),
    "kindness": QAItem(
        question="What is kindness?",
        answer="Kindness is when you help, comfort, or include someone in a caring way. It often makes people feel safe and brave.",
    ),
    "curiosity": QAItem(
        question="What is curiosity?",
        answer="Curiosity is the feeling that makes you want to look, ask, and learn. It helps people find answers.",
    ),
    "mystery": QAItem(
        question="What is a mystery?",
        answer="A mystery is something puzzling that you have to figure out by looking carefully and noticing clues.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [WORLD_KNOWLEDGE[k] for k in ["aunt", "sharing", "kindness", "curiosity", "mystery"]]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,H) :- setting(S), mystery(M), help_act(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for h in HELP_ACTS:
        lines.append(asp.fact("help_act", h))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def explain_response(params: StoryParams) -> str:
    return "(No story: the requested mystery setup could not be built.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.help_act is None or c[2] == args.help_act)]
    if not combos:
        raise StoryError(explain_response(StoryParams(setting="", mystery="", help_act="", child_name="", child_gender="", aunt_name="", aunt_gender="")))
    setting, mystery, help_act = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        help_act=help_act,
        child_name=name,
        child_gender=gender,
        aunt_name=args.aunt_name or rng.choice(AUNT_NAMES),
        aunt_gender="aunt",
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.help_act not in HELP_ACTS:
        raise StoryError("(Invalid parameters.)")
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        HELP_ACTS[params.help_act],
        params.child_name,
        params.child_gender,
        params.aunt_name,
    )
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
    StoryParams(setting="bedroom", mystery="missing_note", help_act="ask_gently", child_name="Mia", child_gender="girl", aunt_name="Aunt June", aunt_gender="aunt"),
    StoryParams(setting="kitchen", mystery="lost_key", help_act="share_lamp", child_name="Leo", child_gender="boy", aunt_name="Aunt Tessa", aunt_gender="aunt"),
    StoryParams(setting="porch", mystery="vanished_cookie", help_act="tidy_together", child_name="Nora", child_gender="girl", aunt_name="Aunt Bea", aunt_gender="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, m, h in combos:
            print(f"  {s:8} {m:14} {h}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
