#!/usr/bin/env python3
"""
storyworlds/worlds/pad_vote_happy_ending_teamwork_adventure.py
===============================================================

A small adventure storyworld about a team, a vote, and a happy ending.

Premise:
- A group of children and a helper are traveling through a tricky place.
- They must vote on a plan.
- Their teamwork creates or uses pads to cross safely.
- The ending is happy because everyone helps and the chosen plan works.

The story is intended to feel like a compact adventure with a clear turn:
the group faces a risky route, argues briefly, votes for a clever plan, and
works together so the journey ends well.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    name: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pad:
    id: str
    label: str
    phrase: str
    covers: set[str]
    protects: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


@dataclass
class StoryParams:
    place: str
    route: str
    pad: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "riverbank": Setting(place="the riverbank", affords={"stones", "planks"}),
    "foresttrail": Setting(place="the forest trail", affords={"stones", "mats"}),
    "cavepath": Setting(place="the cave path", indoors=True, affords={"lamps", "mats"}),
}

ROUTES = {
    "stones": Route(
        id="stones",
        name="stones",
        verb="cross the riverbank stones",
        gerund="crossing the riverbank stones",
        rush="rush onto the wet stones",
        risk="slip in the river water",
        zone={"feet"},
        keyword="stone",
        tags={"water", "slippery"},
    ),
    "planks": Route(
        id="planks",
        name="planks",
        verb="cross the narrow planks",
        gerund="walking across the planks",
        rush="dash onto the planks",
        risk="wobble over the water",
        zone={"feet"},
        keyword="plank",
        tags={"wood", "balance"},
    ),
    "mats": Route(
        id="mats",
        name="mats",
        verb="step across the muddy trail",
        gerund="stepping across the muddy trail",
        rush="run into the mud",
        risk="sink into the mud",
        zone={"feet"},
        keyword="mud",
        tags={"mud", "soft"},
    ),
    "lamps": Route(
        id="lamps",
        name="lamps",
        verb="follow the cave lamps",
        gerund="following the cave lamps",
        rush="dart ahead in the dark",
        risk="get lost in the dark",
        zone={"eyes", "feet"},
        keyword="lamp",
        tags={"dark", "glow"},
    ),
}

PADS = {
    "bridge": Pad(
        id="bridge",
        label="a little bridge of pads",
        phrase="little stepping pads tied together with rope",
        covers={"feet"},
        protects={"water", "slippery"},
        prep="tie the pads into a little bridge",
        tail="carefully crossed the little bridge together",
    ),
    "boots": Pad(
        id="boots",
        label="dry boots",
        phrase="dry boots with sturdy soles",
        covers={"feet"},
        protects={"mud", "water", "slippery"},
        prep="put on the dry boots first",
        tail="marched on in the dry boots",
    ),
    "glowmats": Pad(
        id="glowmats",
        label="glow mats",
        phrase="soft glow mats",
        covers={"feet", "eyes"},
        protects={"dark"},
        prep="spread out the glow mats",
        tail="walked along the glow mats",
    ),
}

NAMES_GIRL = ["Mina", "Lila", "Zoe", "Nora", "Ava", "Maya"]
NAMES_BOY = ["Toby", "Leo", "Ben", "Finn", "Owen", "Theo"]
TRAITS = ["brave", "curious", "cheerful", "careful", "spirited"]


class StoryWorld:
    pass


def reasonableness_gate(route: Route, pad: Pad) -> bool:
    return bool(route.tags & pad.protects) and bool(route.zone <= pad.covers or route.zone == {"feet"} and "feet" in pad.covers)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, setting in SETTINGS.items():
        for route_id in setting.affords:
            route = ROUTES[route_id]
            for pad_id, pad in PADS.items():
                if reasonableness_gate(route, pad):
                    out.append((place_id, route_id, pad_id))
    return sorted(out)


def explain_rejection(route: Route, pad: Pad) -> str:
    return (
        f"(No story: {pad.label} does not really solve {route.gerund}. "
        f"The team needs a pad plan that protects the risky part of the route.)"
    )


def setting_detail(setting: Setting, route: Route) -> str:
    if setting.indoors:
        return f"The cave was quiet, and the walls made the lantern light look bright."
    if route.id == "stones":
        return "The river water flashed below the stones, and the path looked slippery."
    if route.id == "planks":
        return "The planks creaked over the water, and everyone had to step carefully."
    return "The trail was soft and brown, with muddy spots that begged for a careful plan."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: pad, vote, teamwork, happy ending.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--route", choices=sorted(ROUTES))
    ap.add_argument("--pad", choices=sorted(PADS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "friend", "guide"])
    ap.add_argument("--name")
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
    if args.route and args.pad:
        route = ROUTES[args.route]
        pad = PADS[args.pad]
        if not reasonableness_gate(route, pad):
            raise StoryError(explain_rejection(route, pad))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.route is None or c[1] == args.route)
        and (args.pad is None or c[2] == args.pad)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, route_id, pad_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(["mother", "father", "friend", "guide"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, route=route_id, pad=pad_id, name=name, gender=gender, helper=helper, trait=trait)


def _hero_label(hero: Entity) -> str:
    return f"little {next((t for t in hero.memes.get('traits', []) if t), 'brave')} {hero.type}"


def tell(setting: Setting, route: Route, pad: Pad, name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, memes={"joy": 0.0, "teamwork": 0.0, "vote_yes": 0.0}, meters={},))
    hero.memes["traits"] = [trait]
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}", meters={}, memes={"care": 1.0}))
    pad_ent = world.add(Entity(id=pad.id, type="thing", label=pad.label, phrase=pad.phrase, owner=hero.id, caretaker=helper.id, plural=pad.plural))

    world.say(f"{name} was a {trait} {gender} who loved adventure and liked helping the team.")
    world.say(f"On that day, {name} and {helper.label} reached {setting.place} where {setting_detail(setting, route)}")
    world.say(f"They had to {route.verb}, but the path could {route.risk}.")

    world.para()
    world.say(f"{name} wanted a safe plan, so everyone stopped to vote.")
    hero.memes["uncertainty"] = 1.0
    hero.memes["vote_yes"] = 1.0
    world.say(f"{name} voted for the {pad.label}, and {helper.label} nodded right away.")
    world.say(f"That choice felt fair, because {pad.label} could help the team with the tricky part of the journey.")

    world.para()
    hero.memes["teamwork"] += 1.0
    helper.meters["work"] = 1.0
    world.say(f"Together they used teamwork: {pad.prep}, then they held the rope and looked after one another.")
    if pad.id == "glowmats":
        world.say(f"The soft mats lit the cave path like tiny stars, so nobody felt afraid of the dark.")
    elif pad.id == "bridge":
        world.say(f"The tied pads made a little bridge, and every careful step kept feet above the slippery water.")
    elif pad.id == "boots":
        world.say(f"The dry boots kept their feet safe from mud and splash, so the team could go on without stopping.")
    world.say(f"In the end, they {pad.tail}, and the whole group reached the other side smiling.")
    world.say(f"{name} laughed, {helper.label} laughed too, and the adventure ended in a happy way.")

    world.facts.update(hero=hero, helper=helper, pad=pad_ent, route=route, setting=setting)
    world.facts["happy_end"] = True
    world.facts["teamwork"] = True
    world.facts["voted"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    route = f["route"]
    pad = f["pad"]
    return [
        f'Write a short adventure story for a child named {hero.id} who must vote on a safe plan using {pad.label}.',
        f"Tell a teamwork adventure where a group decides by vote how to cross a risky path and keep everyone safe.",
        f'Write a happy-ending story about {hero.id}, a vote, and {pad.label} on {route.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    route: Route = f["route"]
    pad: Pad = f["pad"]
    place: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the adventure story about?",
            answer=f"The story was about {hero.id}, who went on an adventure with {helper.label} at {place.place}.",
        ),
        QAItem(
            question=f"What did the team vote for to solve the problem?",
            answer=f"They voted for {pad.label}, because it was the safest plan for {route.gerund}.",
        ),
        QAItem(
            question=f"Why did they need teamwork on the trip?",
            answer=f"They needed teamwork because the path was risky and the team had to help one another cross safely.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended happily, with everyone across the tricky place and smiling at the finish.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vote?",
            answer="A vote is when people each choose what they think is the best idea.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and work together toward the same goal.",
        ),
        QAItem(
            question="What is a pad in this story?",
            answer="A pad is a helpful flat thing the team can use to make crossing a tricky place safer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


CURATED = [
    StoryParams(place="riverbank", route="stones", pad="bridge", name="Mina", gender="girl", helper="mother", trait="brave"),
    StoryParams(place="foresttrail", route="mats", pad="boots", name="Toby", gender="boy", helper="guide", trait="curious"),
    StoryParams(place="cavepath", route="lamps", pad="glowmats", name="Zoe", gender="girl", helper="father", trait="cheerful"),
]


ASP_RULES = r"""
place(P) :- setting(P).
route(R) :- route_def(R).
pad(Pa) :- pad_def(Pa).

valid(P, R, Pa) :- affords(P, R), route_tag(R, T), pad_tag(Pa, T), route_zone(R, Z), pad_cover(Pa, Z).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for r in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, r))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route_def", rid))
        for t in sorted(route.tags):
            lines.append(asp.fact("route_tag", rid, t))
        for z in sorted(route.zone):
            lines.append(asp.fact("route_zone", rid, z))
    for pid, pad in PADS.items():
        lines.append(asp.fact("pad_def", pid))
        for t in sorted(pad.protects):
            lines.append(asp.fact("pad_tag", pid, t))
        for z in sorted(pad.covers):
            lines.append(asp.fact("pad_cover", pid, z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ROUTES[params.route], PADS[params.pad], params.name, params.gender, params.helper, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid combinations:")
        for t in vals:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.route} at {p.place} (pad: {p.pad})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
