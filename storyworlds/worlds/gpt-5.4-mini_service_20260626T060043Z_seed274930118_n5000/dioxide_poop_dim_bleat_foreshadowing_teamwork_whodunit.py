#!/usr/bin/env python3
"""
storyworlds/worlds/dioxide_poop_dim_bleat_foreshadowing_teamwork_whodunit.py
============================================================================

A tiny whodunit story world about a dim lantern, a suspicious bleat, and a
team that solves the mystery together.

The seed image:
- Something in a small place goes dim because dioxide builds up.
- A "poop-dim" clue shows up as a smudgy, darkened mark.
- A bleat draws attention to the real cause.
- Foreshadowing plants the clue early.
- Teamwork helps the characters test their theories and solve the case.

This world stays small on purpose: one setting, a handful of entities, and a
single satisfying reveal.
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    has_hay: bool = True
    has_lanterns: bool = True
    has_pen: bool = True
    has_compost: bool = True


@dataclass
class Suspect:
    id: str
    label: str
    clue: str
    can_bleat: bool = False
    can_make_dioxide: bool = False
    can_make_poop_dim: bool = False
    innocent_reason: str = ""


@dataclass
class StoryParams:
    place: str
    suspect: str
    detective: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}
        self.trace_notes: list[str] = []

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

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.trace_notes = list(self.trace_notes)
        w.paragraphs = [[]]
        return w


def _r_dioxide_dims(world: World) -> list[str]:
    out: list[str] = []
    smoke = world.facts.get("dioxide_level", 0.0)
    if smoke < THRESHOLD:
        return out
    for ent in world.entities.values():
        if ent.kind != "light":
            continue
        sig = ("dim", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["dim"] = ent.meters.get("dim", 0.0) + 1.0
        out.append(f"The lamp dimmed as dioxide hung low in the room.")
    return out


def _r_poop_dim(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("poop_dim", 0.0) < THRESHOLD:
        return out
    clue = world.entities.get("clue")
    if clue:
        sig = ("clue", clue.id)
        if sig not in world.fired:
            world.fired.add(sig)
            clue.memes["mystery"] = clue.memes.get("mystery", 0.0) + 1.0
            out.append("A poop-dim smudge on the wall made the case feel stranger.")
    return out


def _r_bleat(world: World) -> list[str]:
    out: list[str] = []
    suspect = world.facts.get("suspect_entity")
    if not suspect:
        return out
    if suspect.memes.get("bleat", 0.0) < THRESHOLD:
        return out
    sig = ("bleat_seen", suspect.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"A sharp bleat came from {suspect.label}, right where the clue pointed.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    helper = world.get("helper")
    if detective.memes.get("doubt", 0.0) < THRESHOLD or helper.memes.get("brave", 0.0) < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["confidence"] = detective.memes.get("confidence", 0.0) + 1.0
    helper.memes["confidence"] = helper.memes.get("confidence", 0.0) + 1.0
    out.append("The two friends worked together to follow the clues instead of arguing about them.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_dioxide_dims, _r_poop_dim, _r_bleat, _r_teamwork):
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def reason_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("That setting is not available in this story world.")
    if params.suspect not in SUSPECTS:
        raise StoryError("That suspect is not available in this story world.")
    if params.detective not in NAMES:
        raise StoryError("That detective name is not available in this story world.")
    if params.helper not in NAMES:
        raise StoryError("That helper name is not available in this story world.")
    if params.detective == params.helper:
        raise StoryError("The detective and helper must be different characters.")


def foreshadow(world: World, suspect: Entity, clue: Entity) -> None:
    world.say(
        f"Before anyone knew what was wrong, {clue.label} had already been left near the shed."
    )
    world.say(
        f"{suspect.label} stood nearby and gave a tiny bleat, but nobody understood why yet."
    )


def scene_setup(world: World, detective: Entity, helper: Entity, suspect: Entity) -> None:
    world.say(
        f"At {world.setting.place}, {detective.label} noticed the lantern glowing weakly."
    )
    world.say(
        f"{helper.label} saw a poop-dim mark by the door and frowned at the strange stain."
    )
    world.say(
        f"{detective.label} wondered if the trouble came from the hay, the air, or the animals."
    )
    world.facts["dioxide_level"] = 1.0
    world.facts["poop_dim"] = 1.0
    world.facts["suspect_entity"] = suspect
    propagate(world)


def investigation(world: World, detective: Entity, helper: Entity, suspect: Entity) -> None:
    detective.memes["doubt"] = detective.memes.get("doubt", 0.0) + 1.0
    helper.memes["brave"] = helper.memes.get("brave", 0.0) + 1.0
    world.say(
        f"{detective.label} wanted to blame the first thing in sight, but {helper.label} held up a hand."
    )
    world.say(
        f'"Let us look together," {helper.label} said, and they checked the marks near the pen.'
    )
    suspect.memes["bleat"] = suspect.memes.get("bleat", 0.0) + 1.0
    propagate(world)


def reveal(world: World, detective: Entity, helper: Entity, suspect: Entity) -> None:
    world.say(
        f"Then {detective.label} noticed the air was stale, and the lantern was dim because dioxide had built up."
    )
    world.say(
        f"The poop-dim clue was not the culprit; it only showed that the animal had brushed past the wall."
    )
    world.say(
        f"{helper.label} opened the door, let fresh air in, and the light grew bright again."
    )
    world.say(
        f"{detective.label} laughed. '{suspect.label} was only warning us with that bleat!'"
    )
    world.say(
        f"Together they cleaned the smudge, aired out the room, and solved the mystery without another scare."
    )
    world.facts["solved"] = True


def tell_story(params: StoryParams) -> World:
    reason_gate(params)
    world = World(SETTINGS[params.place])

    detective = world.add(Entity(id="detective", kind="character", type="girl", label=params.detective))
    helper = world.add(Entity(id="helper", kind="character", type="boy", label=params.helper))
    suspect_cfg = SUSPECTS[params.suspect]
    suspect = world.add(Entity(id="suspect", kind="animal", type="goat", label=suspect_cfg.label))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label="the poop-dim clue"))

    world.facts["setting"] = world.setting
    world.facts["suspect_cfg"] = suspect_cfg
    world.facts["detective"] = detective
    world.facts["helper"] = helper
    world.facts["suspect_entity"] = suspect
    world.facts["clue"] = clue

    world.say(
        f"At {params.place}, {detective.label} and {helper.label} found a mystery in the small shed."
    )
    foreshadow(world, suspect, clue)
    world.para()
    scene_setup(world, detective, helper, suspect)
    world.para()
    investigation(world, detective, helper, suspect)
    world.para()
    reveal(world, detective, helper, suspect)

    return world


SETTINGS = {
    "shed": Setting(place="the shed", indoor=True),
    "barn": Setting(place="the barn", indoor=True),
    "coop": Setting(place="the coop", indoor=True),
}

SUSPECTS = {
    "goat": Suspect(
        id="goat",
        label="the goat",
        clue="bleat",
        can_bleat=True,
        can_make_dioxide=False,
        can_make_poop_dim=True,
        innocent_reason="It had only wandered by, and its bleat was a warning, not a crime.",
    ),
    "sheep": Suspect(
        id="sheep",
        label="the sheep",
        clue="bleat",
        can_bleat=True,
        can_make_dioxide=False,
        can_make_poop_dim=False,
        innocent_reason="It stayed in the pen and only sounded loud when it got nervous.",
    ),
    "calf": Suspect(
        id="calf",
        label="the calf",
        clue="bleat",
        can_bleat=True,
        can_make_dioxide=False,
        can_make_poop_dim=False,
        innocent_reason="It was too small to cause the dim light, though it did call out for help.",
    ),
}

NAMES = ["Mina", "Jasper", "Tara", "Owen", "Lila", "Eli"]


@dataclass
class ASPThing:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit about dioxide, a poop-dim clue, and a bleat.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective", choices=NAMES)
    ap.add_argument("--helper", choices=NAMES)
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
    place = args.place or rng.choice(sorted(SETTINGS))
    suspect = args.suspect or rng.choice(sorted(SUSPECTS))
    detective = args.detective or rng.choice(sorted(NAMES))
    helper = args.helper or rng.choice(sorted([n for n in NAMES if n != detective]))
    params = StoryParams(place=place, suspect=suspect, detective=detective, helper=helper)
    reason_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"].label
    helper = f["helper"].label
    suspect = f["suspect_entity"].label
    return [
        f"Write a child-friendly whodunit set in {world.setting.place} with a dim lantern, a poop-dim clue, and a bleat.",
        f"Tell a short mystery where {det} and {helper} use teamwork to figure out why the room went dim.",
        f"Make the clue feel like foreshadowing, then reveal that {suspect} was not the culprit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    det = world.get("detective").label
    helper = world.get("helper").label
    suspect = world.get("suspect").label
    return [
        QAItem(
            question=f"Why did the lantern go dim in {world.setting.place}?",
            answer="The lantern went dim because dioxide built up in the small space and the air got stale.",
        ),
        QAItem(
            question=f"What was the poop-dim clue supposed to help {det} and {helper} notice?",
            answer="It was a foreshadowing clue that showed an animal had been nearby and that they should look carefully before guessing.",
        ),
        QAItem(
            question=f"How did {det} and {helper} solve the mystery?",
            answer=f"They used teamwork, checked the clues together, opened the door for fresh air, and found that {suspect} was only warning them with a bleat.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    suspect = world.get("suspect")
    return [
        QAItem(
            question="What is dioxide in this story?",
            answer="Dioxide is the stale air trouble that made the lantern dim in the small room.",
        ),
        QAItem(
            question="What does a bleat sound like?",
            answer="A bleat is a sheep-like animal sound, sharp and a little worried.",
        ),
        QAItem(
            question="Why does teamwork help in a mystery?",
            answer="Teamwork helps because two people can look at the clues together and notice more than one person might notice alone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when a small indoor setting has a suspect that can bleat and
% the plot includes a dimming air clue plus teamwork.
valid_story(P, S) :- place(P), suspect(S), indoor(P), can_bleat(S), has_teamwork.

% The mystery clue is reasoned about as foreshadowing.
foreshadows(clue, suspect) :- clue_type(poopo_dim), suspect(S), can_bleat(S).

has_teamwork :- teamwork.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        if s.can_bleat:
            lines.append(asp.fact("can_bleat", sid))
        if s.can_make_dioxide:
            lines.append(asp.fact("can_make_dioxide", sid))
        if s.can_make_poop_dim:
            lines.append(asp.fact("can_make_poop_dim", sid))
    lines.append(asp.fact("clue_type", "poopo_dim"))
    lines.append(asp.fact("teamwork"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in [
            StoryParams(place="shed", suspect="goat", detective="Mina", helper="Jasper"),
            StoryParams(place="barn", suspect="sheep", detective="Tara", helper="Owen"),
            StoryParams(place="coop", suspect="calf", detective="Lila", helper="Eli"),
        ]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
