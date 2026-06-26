#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/skating_spine_bit_moral_value_detective_story.py
================================================================================

A small, self-contained story world for a child-sized detective tale.

Premise:
- A young detective notices a clue at the skating rink.
- The clue points to a small hidden theft involving a missing bit.
- The answer depends on a moral value: honesty.
- The ending proves what changed in the world, not just in the wording.

Seed words woven into the world:
- skating
- spine
- bit

This script follows the Storyweavers contract:
- typed entities with meters and memes
- a story-driven simulation
- Python reasonableness gate + inline ASP twin
- generate/emit/CLI entry points
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    label: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    clue: str
    suspect_action: str
    hidden_item: str
    moral_value: str
    setting_hint: str
    outcome_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralValue:
    id: str
    label: str
    value_word: str
    teaching: str
    clue_kind: str


@dataclass
class StoryParams:
    place: str
    case: str
    value: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, case: Case, moral: MoralValue) -> None:
        self.place = place
        self.case = case
        self.moral = moral
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
    "rink": Place(label="the skating rink", indoor=True, affords={"skating"}),
    "hall": Place(label="the ice hall", indoor=True, affords={"skating"}),
    "park": Place(label="the park rink", indoor=False, affords={"skating"}),
}

CASES = {
    "lost_bit": Case(
        id="lost_bit",
        clue="a tiny missing bit of silver tape",
        suspect_action="skate too fast past the display case",
        hidden_item="the missing bit",
        moral_value="honesty",
        setting_hint="near the skate bench",
        outcome_phrase="the tiny bit was back where it belonged",
        tags={"skating", "bit"},
    ),
    "torn_spine": Case(
        id="torn_spine",
        clue="a torn spine on the book about skating",
        suspect_action="lean on the shelf too hard",
        hidden_item="the torn book",
        moral_value="carefulness",
        setting_hint="by the library corner",
        outcome_phrase="the spine was mended neatly",
        tags={"skating", "spine"},
    ),
}

VALUES = {
    "honesty": MoralValue(
        id="honesty",
        label="honesty",
        value_word="honesty",
        teaching="to tell the truth even when a mistake feels small",
        clue_kind="truth",
    ),
    "carefulness": MoralValue(
        id="carefulness",
        label="carefulness",
        value_word="carefulness",
        teaching="to handle things gently so they do not break",
        clue_kind="care",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ivy", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Max", "Eli", "Noah", "Finn", "Owen"]
TRAITS = ["curious", "quiet", "bright", "careful", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in SETTINGS.items():
        for case_id, case in CASES.items():
            for value_id, val in VALUES.items():
                if case.moral_value == value_id and "skating" in place.affords:
                    combos.append((place_id, case_id, value_id))
    return combos


def reasonableness_check(place: Place, case: Case, value: MoralValue) -> None:
    if case.moral_value != value.id:
        raise StoryError(
            f"(No story: the case '{case.id}' belongs with {case.moral_value}, "
            f"not with {value.id}.)"
        )
    if "skating" not in place.affords:
        raise StoryError("(No story: this place cannot host the skating scene.)")


def seed_facts() -> dict:
    return {
        "place": SETTINGS,
        "case": CASES,
        "value": VALUES,
    }


class DetectiveWorld(World):
    pass


def _say_intro(world: World, detective: Entity, parent: Entity, case: Case, value: MoralValue) -> None:
    world.say(
        f"{detective.id} was a little {next(t for t in detective.memes if False) if False else detective.type} detective "
        f"who liked {world.case.setting_hint} and {value.value_word}."
    )


def _do_skating(world: World, detective: Entity) -> None:
    detective.meters["skating"] = detective.meters.get("skating", 0) + 1
    detective.memes["joy"] = detective.memes.get("joy", 0) + 1


def tell(place: Place, case: Case, moral: MoralValue, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = DetectiveWorld(place, case, moral)

    detective = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"skating": 0.0},
        memes={"curiosity": 1.0, "resolve": 1.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=f"the {parent_type}",
        meters={"worry": 0.0},
        memes={"care": 1.0},
    ))
    clue = world.add(Entity(
        id="Clue",
        type="thing",
        label=case.clue,
        phrase=case.clue,
        location="bench",
    ))
    missing = world.add(Entity(
        id="Missing",
        type="thing",
        label=case.hidden_item,
        phrase=case.hidden_item,
        caretaker=parent.id,
        location="hidden",
        meters={"lost": 1.0},
    ))

    world.facts.update(detective=detective, parent=parent, clue=clue, missing=missing)

    world.say(
        f"At {place.label}, {detective.id} was known as a small detective with a sharp eye."
    )
    world.say(
        f"{detective.id} loved {moral.teaching}, and {moral.label} was the rule {detective.pronoun('subject')} tried to keep."
    )
    world.say(
        f"One afternoon, {detective.id} went {world.case.setting_hint} to watch the {case.suspect_action}."
    )
    world.para()
    _do_skating(world, detective)
    world.say(
        f"The air smelled cold and clean, and {detective.id}'s skates made a soft scrape on the floor."
    )
    world.say(
        f"Then {detective.id} found {case.clue}."
    )

    # Investigation
    world.para()
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} looked at the clue, then at the bench, and then at the shiny racks by the wall."
    )
    if case.id == "lost_bit":
        world.say(
            f"A tiny piece of silver tape had peeled away from a sign, and that was the missing bit."
        )
    else:
        world.say(
            f"The book about skating had a torn spine, and the loose page matched the tear exactly."
        )

    # Moral turn: someone confesses.
    world.para()
    suspect = world.add(Entity(
        id="Suspect",
        kind="character",
        type="boy",
        label="the skater",
        meters={"nervous": 0.0},
        memes={"guilt": 1.0, "relief": 0.0},
    ))
    suspect.memes["guilt"] += 1
    world.say(
        f"The skater came back slowly and looked down. {suspect.pronoun('subject').capitalize()} said, "
        f'"I did it. I was rushing, and I knocked it loose."'
    )
    if moral.id == "honesty":
        detective.memes["respect"] = detective.memes.get("respect", 0) + 1
        world.say(
            f"{detective.id} did not scold {suspect.pronoun('object')}. {detective.id} said that telling the truth was the brave part."
        )
    else:
        world.say(
            f"{detective.id} asked {suspect.pronoun('object')} to hold the book with both hands and be careful next time."
        )

    # Resolution
    world.para()
    suspect.memes["relief"] += 1
    missing.meters["lost"] = 0.0
    missing.location = "fixed"
    world.say(
        f"Together they put things right, and {world.case.outcome_phrase}."
    )
    world.say(
        f"{detective.id} skated one last slow circle, and the rink felt calm again."
    )
    world.say(
        f"It was a small case, but it left a big mark: {moral.value_word} made the answer feel clean."
    )

    world.facts.update(
        detective=detective,
        parent=parent,
        clue=clue,
        missing=missing,
        suspect=suspect,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    case: Case = world.case
    moral = world.moral
    return [
        f'Write a short detective story for a child that includes "{case.clue}" and the word "skating".',
        f"Tell a gentle mystery where {detective.id} notices a clue, asks one careful question, and learns about {moral.value_word}.",
        f"Create a tiny detective tale set at {world.place.label} with a missing bit and a truthful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    suspect: Entity = f["suspect"]
    moral = world.moral
    case = world.case
    return [
        QAItem(
            question=f"What kind of story is this about {detective.id} at {world.place.label}?",
            answer=f"It is a detective story about {detective.id} solving a small mystery while skating at {world.place.label}.",
        ),
        QAItem(
            question=f"What clue did {detective.id} find?",
            answer=f"{detective.id} found {case.clue}, which helped point to the truth.",
        ),
        QAItem(
            question=f"What did the skater admit?",
            answer=f"The skater admitted that {detective.id} was right and said, 'I did it. I was rushing, and I knocked it loose.'",
        ),
        QAItem(
            question=f"What moral value mattered most in the story?",
            answer=f"{moral.value_word} mattered most, because the truth helped fix the problem and made the ending calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is skating?",
            answer="Skating is moving smoothly on skates or wheels, often across ice or a smooth floor.",
        ),
        QAItem(
            question="What is a spine on a book?",
            answer="A book spine is the narrow edge that holds the pages together and shows the book's title.",
        ),
        QAItem(
            question="What is a bit?",
            answer="A bit is a small piece of something, like a tiny bit of tape or a tiny bit of paper.",
        ),
    ]
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
case(C) :- mystery(C).
value(V) :- moral(V).

compatible(P,C,V) :- place(P), case(C), value(V),
                     case_value(C,V), affords(P, skating).

resolved(C) :- compatible(_,C,_).
#show compatible/3.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CASES.items():
        lines.append(asp.fact("mystery", cid))
        lines.append(asp.fact("case_value", cid, c.moral_value))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for vid, v in VALUES.items():
        lines.append(asp.fact("moral", vid))
        lines.append(asp.fact("teaches", vid, v.clue_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective story world about skating, a spine, a bit, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.case is None or c[1] == args.case)
        and (args.value is None or c[2] == args.value)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, case, value = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, case=case, value=value, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS[params.place]
    case = CASES[params.case]
    moral = VALUES[params.value]
    reasonableness_check(place, case, moral)
    world = tell(place, case, moral, params.name, params.gender, params.parent)
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
    StoryParams(place="rink", case="lost_bit", value="honesty", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="hall", case="torn_spine", value="carefulness", name="Leo", gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible combos:\n")
        for p, c, v in combos:
            print(f"  {p:8} {c:12} {v}")
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
