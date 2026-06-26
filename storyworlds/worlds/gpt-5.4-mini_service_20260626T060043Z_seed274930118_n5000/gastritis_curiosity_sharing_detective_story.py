#!/usr/bin/env python3
"""
A standalone story world for a tiny detective tale about gastritis, curiosity,
and sharing.

A child detective notices that a friend keeps holding a hand to their belly and
refusing a snack. The detective follows clues, asks gentle questions, and learns
that gastritis is making the stomach hurt. The resolution comes when the child
shares a soft, safe snack and a warm drink, and the friend feels better.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little library"
    indoors: bool = True


@dataclass
class StoryParams:
    setting: str
    detective_name: str
    detective_gender: str
    friend_name: str
    friend_gender: str
    caretaker_name: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


SETTINGS = {
    "library": Setting(place="the little library", indoors=True),
    "cafe": Setting(place="the corner cafe", indoors=True),
    "classroom": Setting(place="the classroom", indoors=True),
}

CLUES = {
    "empty_plate": "an empty plate",
    "warm_tea": "a warm cup of tea",
    "tummy_hold": "a hand pressed to the tummy",
    "slow_steps": "slow, careful steps",
    "half_finished_note": "a half-finished note about a sore stomach",
}

NAMES = {
    "girl": ["Mia", "Luna", "Zoe", "Nora", "Ivy"],
    "boy": ["Leo", "Ben", "Theo", "Max", "Finn"],
}

TRAITS = ["curious", "sharp-eyed", "patient", "brave", "gentle"]


def gender_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    if gender == "boy":
        return "he", "him", "his"
    return "they", "them", "their"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-style story world about gastritis, curiosity, and sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker-name")
    ap.add_argument("--clue", choices=CLUES.keys())
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


def _rand_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES[gender])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _rand_name(rng, detective_gender)
    friend_name = args.friend_name or _rand_name(rng, friend_gender)
    caretaker_name = args.caretaker_name or rng.choice(["Mom", "Dad", "Aunt Rose", "Grandma"])
    clue = args.clue or rng.choice(list(CLUES))
    return StoryParams(
        setting=setting,
        detective_name=detective_name,
        detective_gender=detective_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        caretaker_name=caretaker_name,
        clue=clue,
    )


def _make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    d = world.add(Entity(
        id="detective",
        kind="character",
        type=params.detective_gender,
        label=params.detective_name,
        meters={"attention": 1.0},
        memes={"curiosity": 1.0, "care": 0.5},
    ))
    f = world.add(Entity(
        id="friend",
        kind="character",
        type=params.friend_gender,
        label=params.friend_name,
        meters={"tummy_pain": 0.0},
        memes={"worry": 0.2, "relief": 0.0},
    ))
    c = world.add(Entity(
        id="caretaker",
        kind="character",
        type="adult",
        label=params.caretaker_name,
        meters={"kitchen_kindness": 1.0},
        memes={"care": 1.0},
    ))
    snack = world.add(Entity(
        id="snack",
        type="thing",
        label="a plain cracker",
        phrase="a plain cracker and a little cup of warm tea",
        owner=d.id,
    ))
    notebook = world.add(Entity(
        id="notebook",
        type="thing",
        label="a tiny notebook",
        phrase="a tiny notebook with a pencil tucked in",
        owner=d.id,
    ))
    tummy_note = world.add(Entity(
        id="note",
        type="thing",
        label="a half-finished note",
        phrase="a half-finished note with the word gastritis written on it",
        owner=c.id,
    ))
    gastritis = world.add(Entity(
        id="gastritis",
        type="thing",
        label="gastritis",
        phrase="a sore stomach problem",
        owner=f.id,
    ))
    f.meters["tummy_pain"] = 2.0
    f.memes["worry"] = 1.5
    world.facts.update(
        detective=d, friend=f, caretaker=c, snack=snack, notebook=notebook,
        note=tummy_note, gastritis=gastritis, clue=params.clue,
    )
    return world


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    d = world.get("detective")
    f = world.get("friend")
    c = world.get("caretaker")
    snack = world.get("snack")
    notebook = world.get("notebook")
    note = world.get("note")
    clue_word = CLUES[params.clue]

    world.say(
        f"{d.label} was a {random.choice(TRAITS)} little detective who loved clues. "
        f"At {world.setting.place}, {d.pronoun()} noticed {f.label} sitting very still."
    )
    world.say(
        f"{f.label} kept {clue_word} close and said {f.pronoun('subject')} did not feel like playing."
    )
    world.para()
    world.say(
        f"{d.label} looked carefully, wrote in {notebook.label}, and asked gentle questions."
    )
    world.say(
        f"{f.label} pointed to {f.pronoun('possessive')} belly. "
        f"The tummy felt tight, and the worry meter went up."
    )
    world.say(
        f"Then {c.label} came over with {note.label} and explained that it was gastritis, "
        f"which can make a stomach sore and fussy."
    )
    world.para()
    world.say(
        f"{d.label}'s curiosity turned into a kind plan. {d.pronoun().capitalize()} shared "
        f"{snack.label} and helped set out the warm tea."
    )
    f.meters["tummy_pain"] = 0.5
    f.memes["worry"] = 0.2
    f.memes["relief"] = 1.5
    d.memes["curiosity"] = 2.0
    d.memes["care"] = 1.5
    world.say(
        f"{f.label} took a small bite, sipped the tea, and smiled. "
        f"By the end, the detective had solved the mystery: gastritis, not a missing treasure, "
        f"was the reason for the frown."
    )
    world.say(
        f"{f.label} could sit up straighter, and {d.label} wrote the final note: "
        f"sharing helped, and the room felt warm again."
    )
    world.facts["resolved"] = True
    world.facts["shared_snack"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = f["detective"]
    fr = f["friend"]
    return [
        "Write a short detective story for a young child about gastritis, curiosity, and sharing.",
        f"Tell a gentle mystery where {d.label} notices that {fr.label} has a sore tummy and helps by sharing something safe.",
        f"Write a story with clues, a careful question, and a kind ending at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    fr = f["friend"]
    c = f["caretaker"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {d.label}, who loved clues and kept asking careful questions.",
        ),
        QAItem(
            question=f"Why did {fr.label} look uncomfortable?",
            answer=f"{fr.label} had gastritis, so {fr.label.lower()}'s tummy felt sore and tight.",
        ),
        QAItem(
            question=f"What helped {fr.label} feel better at the end?",
            answer=f"Sharing a plain cracker and a little cup of warm tea helped {fr.label} calm down and feel better.",
        ),
        QAItem(
            question=f"Who explained what was wrong with the tummy?",
            answer=f"{c.label} explained that it was gastritis and that it could make a stomach hurt.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gastritis?",
            answer="Gastritis is when the lining of the stomach gets irritated or sore, which can make a tummy hurt.",
        ),
        QAItem(
            question="What does curiosity help a detective do?",
            answer="Curiosity helps a detective notice clues, ask questions, and find out what is really going on.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or have something with you, like offering food or a toy.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}/{e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


ASP_RULES = r"""
setting(S) :- setting_name(S).
curiosity(C) :- character(C), curious(C).
sharing_action(A) :- action(A), shares(A).

needs_care(F) :- gastritis(F), tummy_pain(F), tummy_pain(F) > 0.
good_fix(F,S) :- needs_care(F), safe_snack(S), shareable(S).

resolved(F) :- needs_care(F), good_fix(F,_).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting_name", k) for k in SETTINGS]
    lines += [asp.fact("character", "detective"), asp.fact("character", "friend"), asp.fact("character", "caretaker")]
    lines += [asp.fact("curious", "detective"), asp.fact("shares", "share")]
    lines += [asp.fact("gastritis", "friend"), asp.fact("tummy_pain", "friend", 2)]
    lines += [asp.fact("safe_snack", "cracker"), asp.fact("shareable", "cracker")]
    lines += [asp.fact("action", "share")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_params(args: argparse.Namespace) -> None:
    if args.detective_name and args.friend_name and args.detective_name == args.friend_name:
        raise StoryError("The detective and the friend should be different characters.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity structure, but this tiny world uses a simple gate.")
        return

    valid_params(args)
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = [
            StoryParams(setting="library", detective_name="Mia", detective_gender="girl",
                        friend_name="Leo", friend_gender="boy", caretaker_name="Mom", clue="tummy_hold"),
            StoryParams(setting="cafe", detective_name="Noah", detective_gender="boy",
                        friend_name="Luna", friend_gender="girl", caretaker_name="Aunt Rose", clue="warm_tea"),
        ]
        samples = [generate(p) for p in cur]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
