#!/usr/bin/env python3
"""
storyworlds/worlds/lamb_dim_discard_repetition_whodunit.py
===========================================================

A tiny whodunit storyworld about a dim barn, a lamb-shaped clue, and a repeated
question that finally points to the culprit.

Seed inspiration:
- lamb-dim
- discard
- repetition
- whodunit

The world is intentionally small: one detective, a few suspects, one missing
object, a repeated clue pattern, and one clear reveal.
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
    carried_by: Optional[str] = None
    hidden: bool = False
    suspicious: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the barn"
    dimness: str = "dim"


@dataclass
class Clue:
    label: str
    phrase: str
    place: str
    smell: str
    color: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    habit: str
    reason: str
    clue_trace: str
    guilty: bool = False


@dataclass
class StoryParams:
    setting: str
    clue: str
    culprit: str
    detective_name: str
    detective_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


DETECTIVE_NAMES = ["Mina", "June", "Pip", "Nell", "Otis", "Ivy", "Ruby", "Tess"]
SUSPECT_NAMES = ["Moss", "Bram", "Wren", "Sage", "Clove", "Milo"]
CLAUSE_REPEAT = [
    "Who took it?",
    "Who hid it?",
    "Who tossed it away?",
]


SETTINGS = {
    "barn": Setting(place="the barn", dimness="dim"),
    "loft": Setting(place="the hay loft", dimness="dim"),
    "shed": Setting(place="the tool shed", dimness="dim"),
}


CLUES = {
    "lamb": Clue(
        label="lamb",
        phrase="a little lamb-shaped charm",
        place="under the straw",
        smell="like wool",
        color="white",
    ),
    "bell": Clue(
        label="bell",
        phrase="a small brass bell",
        place="near the door",
        smell="like dust",
        color="gold",
    ),
    "ribbon": Clue(
        label="ribbon",
        phrase="a red ribbon",
        place="by the feed bin",
        smell="like hay",
        color="red",
    ),
}

SUSPECTS = {
    "owl": Suspect(
        id="owl",
        label="the owl",
        type="animal",
        habit="sat high and watched everything",
        reason="it liked shiny things",
        clue_trace="feathers",
    ),
    "mule": Suspect(
        id="mule",
        label="the mule",
        type="animal",
        habit="kicked the stall door when nervous",
        reason="it wanted the room quiet",
        clue_trace="hoof marks",
    ),
    "child": Suspect(
        id="child",
        label="the child",
        type="child",
        habit="ran around asking the same question again and again",
        reason="it wanted to play detective",
        clue_trace="small footprints",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for u in SUSPECTS:
                combos.append((s, c, u))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld with repeated clues.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--name", choices=DETECTIVE_NAMES)
    ap.add_argument("--detective-type", choices=["girl", "boy"])
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
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if args.culprit:
        combos = [c for c in combos if c[2] == args.culprit]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")

    setting, clue, culprit = rng.choice(sorted(combos))
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    detective_name = args.name or rng.choice(DETECTIVE_NAMES)
    return StoryParams(
        setting=setting,
        clue=clue,
        culprit=culprit,
        detective_name=detective_name,
        detective_type=detective_type,
    )


def _intro(world: World, detective: Entity, clue: Clue) -> None:
    world.say(
        f"It was a dim evening at {world.setting.place}, and {detective.id} was the sort of detective who noticed little things."
    )
    world.say(
        f"On the floor, there was {clue.phrase}. It looked out of place, like a thing someone had meant to discard."
    )


def _repeat_question(world: World, detective: Entity) -> None:
    world.para()
    world.say(
        f"{detective.id} asked the same question three times, because some mysteries only opened after a repeat."
    )
    for line in CLAUSE_REPEAT:
        world.say(f'"{line}" {detective.id} whispered.')
    world.say("Each time, the barn seemed to answer with silence.")


def _investigate(world: World, detective: Entity, culprit: Suspect, clue: Clue) -> None:
    world.para()
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    world.say(
        f"{detective.id} looked at the {clue.label}, then at the floor, then at the door."
    )
    world.say(
        f"There were {culprit.clue_trace}, and they led back to {culprit.label}."
    )
    world.say(
        f"{culprit.label.capitalize()} had been near the spot where the clue was found, and that made {culprit.label} seem suspicious."
    )


def _reveal(world: World, detective: Entity, culprit: Suspect, clue: Clue) -> None:
    world.para()
    culprit_ent = world.get(culprit.id)
    culprit_ent.suspicious = False
    world.say(
        f"At last, {detective.id} said, \"You did it.\""
    )
    world.say(
        f"{culprit.label.capitalize()} dropped {clue.phrase} from {culprit_ent.pronoun('possessive')} mouth, and the room went still."
    )
    if culprit.id == "child":
        world.say(
            f"It had not meant to be cruel; it had only wanted to discard the charm and play the mystery game again."
        )
    else:
        world.say(
            f"It had moved the clue away and then discarded it in a hurry, hoping nobody would ask twice."
        )
    world.say(
        f"Now the answer was plain: {culprit.label} was the one who had hidden the clue in the dim barn."
    )


def generate_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
    ))
    clue = CLUES[params.clue]
    clue_ent = world.add(Entity(
        id=clue.label,
        type="clue",
        label=clue.label,
        phrase=clue.phrase,
        hidden=True,
    ))
    culprit = SUSPECTS[params.culprit]
    culprit_ent = world.add(Entity(
        id=culprit.id,
        kind="character",
        type=culprit.type,
        label=culprit.label,
        suspicious=True,
    ))
    culprit_ent.meters["guilt"] = 1.0
    culprit_ent.memes["nervous"] = 1.0
    world.facts.update(
        detective=detective,
        clue=clue_ent,
        culprit=culprit,
        culprit_ent=culprit_ent,
        setting=setting,
    )

    _intro(world, detective, clue)
    _repeat_question(world, detective)
    _investigate(world, detective, culprit, clue)
    _reveal(world, detective, culprit, clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    culprit = f["culprit"]
    clue = f["clue"]
    return [
        f'Write a short whodunit for a child where {detective.id} keeps asking "Who took it?" in a dim place.',
        f"Tell a simple mystery with repetition, a missing {clue.label}, and a reveal that points to {culprit.label}.",
        f"Write a gentle detective story about someone who notices a clue, repeats the question, and learns who discarded it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    culprit = f["culprit"]
    clue = f["clue"]
    return [
        QAItem(
            question=f"What was the mystery about in {world.setting.place}?",
            answer=f"It was about {clue.phrase} that had been discarded and then hidden in the dim room.",
        ),
        QAItem(
            question=f"Why did {detective.id} keep repeating the question?",
            answer=f"{detective.id} repeated the question because the detective was looking for the answer and knew the clue might only make sense after being asked about more than once.",
        ),
        QAItem(
            question=f"Who turned out to be the one who hid the clue?",
            answer=f"{culprit.label} turned out to be the one who hid the clue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and tries to figure out who did something.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means saying or doing something again and again.",
        ),
        QAItem(
            question="What does discard mean?",
            answer="To discard something means to throw it away or set it aside because you do not want it anymore.",
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
        if e.hidden:
            bits.append("hidden=True")
        if e.suspicious:
            bits.append("suspicious=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is suspicious if it is hidden and the culprit is the one linked to it.
suspicious(C) :- culprit(C), hidden_clue(C).

% Repetition increases certainty in a whodunit.
repetition_boost(D) :- asked_again(D), repeated_question(D).

% A valid mystery needs one hidden clue, one culprit, and a repeatable question.
valid_story(S, C, U) :- setting(S), clue(C), culprit(U),
                        hidden_clue(C), repeatable(C), suspicious(U).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("hidden_clue", cid))
        lines.append(asp.fact("repeatable", cid))
    for uid in SUSPECTS:
        lines.append(asp.fact("culprit", uid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(s, c, u) for s, c, u in valid_combos()}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python combos:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
    StoryParams(setting="barn", clue="lamb", culprit="owl", detective_name="Mina", detective_type="girl"),
    StoryParams(setting="loft", clue="bell", culprit="mule", detective_name="Pip", detective_type="boy"),
    StoryParams(setting="shed", clue="ribbon", culprit="child", detective_name="Ivy", detective_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible mysteries:\n")
        for s, c, u in combos:
            print(f"  {s:6} {c:6} {u}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [build_story(p) for p in CURATED]
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
            sample = build_story(params)
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
            header = f"### {p.detective_name}: {p.clue} in {p.setting} (culprit: {p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
