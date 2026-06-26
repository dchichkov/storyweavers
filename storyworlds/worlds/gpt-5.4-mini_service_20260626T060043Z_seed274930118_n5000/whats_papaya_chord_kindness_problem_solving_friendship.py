#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/whats_papaya_chord_kindness_problem_solving_friendship.py
=============================================================================================================

A small heartwarming story world about a child, a papaya snack, a chord puzzle,
and a kind friend who helps solve it.

The source-tale seed idea:
- A child hears "What's a papaya chord?"
- A shared papaya snack makes little hands sticky.
- A chord on a small stringed instrument seems hard at first.
- Kindness and problem solving turn the problem into friendship and music.

The world is intentionally small and constraint-checked:
- a child has a fruit snack and a music goal
- a helper friend can offer a wipe, a tune-up, or a finger map
- the ending proves the change through the simulated world state
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
    kind: str = "thing"  # character | thing
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the sunny music room"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        return clone


def propagate(world: World) -> None:
    child = world.get("child")
    friend = world.get("friend")
    ukulele = world.get("ukulele")
    snack = world.get("papaya")

    if child.meters.get("sticky", 0.0) >= THRESHOLD and ukulele.meters.get("ready", 0.0) < THRESHOLD:
        ukulele.meters["blocked"] = 1
        child.memes["frustration"] = 1
    if friend.memes.get("kindness", 0.0) >= THRESHOLD:
        child.memes["hope"] = 1
    if friend.memes.get("helping", 0.0) >= THRESHOLD:
        child.meters["sticky"] = 0
        ukulele.meters["ready"] = 1
        child.memes["calm"] = 1
        child.memes["friendship"] = child.memes.get("friendship", 0.0) + 1
        friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    if snack.meters.get("shared", 0.0) >= THRESHOLD:
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1
        friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1


def tell_story(world: World) -> None:
    child = world.get("child")
    friend = world.get("friend")
    papaya = world.get("papaya")
    ukulele = world.get("ukulele")
    note = world.get("note")

    world.say(f"{child.id} was a little {child.type} who loved the sunny music room.")
    world.say(f"{child.pronoun().capitalize()} kept hearing the question, “What’s a papaya chord?” and wondered if the answer could be a happy song.")
    world.say(f"{child.id} had a sweet papaya snack, and {papaya.label} looked bright and juicy in {child.pronoun('possessive')} hands.")
    world.say(f"Beside the table waited a small {ukulele.label}, ready for a chord.")
    world.para()

    world.say(f"One afternoon, {child.id} wanted to {world.facts['activity'].verb}, but {child.pronoun('possessive')} fingers were sticky from papaya juice.")
    child.meters["sticky"] = 1
    child.memes["worry"] = 1
    ukulele.meters["ready"] = 0
    propagate(world)
    world.say(f"{child.pronoun().capitalize()} sighed, because the chord did not sound right when sticky fingers slipped.")
    world.say(f"{friend.id} noticed right away. {friend.pronoun().capitalize()} did not laugh; instead, {friend.pronoun()} asked, “Want help solving it together?”")
    friend.memes["kindness"] = 1
    friend.memes["helping"] = 1
    propagate(world)
    world.para()

    world.say(f"First, {friend.id} offered a soft napkin and wiped the papaya juice away.")
    world.say(f"Then {friend.pronoun()} showed a finger map for the chord, like a tiny picture of where each finger should rest.")
    world.say(f"{child.id} tried again, and this time the chord rang out clean and round.")
    world.say(f"{note.label} from the ukulele sounded warm, and the little room felt full of friendship.")
    papaya.meters["shared"] = 1
    child.memes["kindness"] = 1
    child.memes["friendship"] = child.memes.get("friendship", 0.0) + 1
    propagate(world)
    world.say(f"In the end, {child.id} and {friend.id} shared the papaya, shared the music, and smiled at the same bright chord.")


def build_world(params: "StoryParams") -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender, label=params.friend_name))
    papaya = world.add(Entity(id="papaya", type="fruit", label="papaya", phrase="a ripe papaya slice", owner=child.id))
    ukulele = world.add(Entity(id="ukulele", type="instrument", label="ukulele", phrase="a small ukulele", owner=child.id))
    note = world.add(Entity(id="note", type="thing", label="one bright note"))
    world.facts.update(
        child=child,
        friend=friend,
        papaya=papaya,
        ukulele=ukulele,
        note=note,
        activity=ACTIVITIES[params.activity],
        fix=FIXES[params.fix],
        setting=world.setting,
    )
    tell_story(world)
    return world


@dataclass
class StoryParams:
    setting: str
    activity: str
    fix: str
    name: str
    gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "music_room": Setting(place="the sunny music room", affords={"learn_chord", "practice"},
                          ),
    "porch": Setting(place="the porch with a wooden chair", affords={"learn_chord", "practice"}),
    "library_corner": Setting(place="the quiet library corner", affords={"learn_chord", "practice"}),
}

ACTIVITIES = {
    "learn_chord": Activity(
        id="learn_chord",
        verb="learn the chord",
        gerund="learning the chord",
        rush="reach for the strings",
        mess="sticky",
        soil="too sticky",
        keyword="chord",
        tags={"chord", "music", "problem_solving", "friendship"},
    ),
    "practice": Activity(
        id="practice",
        verb="practice the song",
        gerund="practicing the song",
        rush="tap the strings",
        mess="sticky",
        soil="too sticky",
        keyword="chord",
        tags={"chord", "music", "kindness"},
    ),
}

FIXES = {
    "napkin_map": Fix(
        id="napkin_map",
        label="a napkin and a finger map",
        prep="wipe the papaya juice away and show a finger map",
        tail="smiled because the problem was solved together",
        helps={"sticky", "chord"},
    ),
    "clean_hands": Fix(
        id="clean_hands",
        label="clean hands and a slow count",
        prep="wash up and count the fingers slowly",
        tail="smiled because the chord finally fit",
        helps={"sticky", "chord"},
    ),
}


GIVEN_NAMES = ["Mia", "Noah", "Lina", "Owen", "Zoe", "Eli", "Nora", "Theo"]
FRIEND_NAMES = ["Jun", "Pia", "Sage", "Ari", "Bea", "Tess", "Milo", "Rae"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for f in FIXES:
                out.append((s, a, f))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming story world about papaya, chord, kindness, problem solving, and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    fix = args.fix or rng.choice(list(FIXES))
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(GIVEN_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != name])
    return StoryParams(setting=setting, activity=activity, fix=fix, name=name, gender=gender,
                       friend_name=friend_name, friend_gender=friend_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming story where a child wonders, "What’s a papaya chord?" and learns it with a friend.',
        f"Tell a gentle story about {f['child'].label}, papaya juice, and a chord that needs kindness and problem solving.",
        f"Write a short friendship story in {world.setting.place} that includes papaya, chord, and a helpful fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    fr = world.facts["friend"]
    activity = world.facts["activity"]
    return [
        QAItem(
            question=f"Why did {c.label} have trouble with the chord at first?",
            answer=f"{c.label} had trouble because papaya juice made {c.pronoun('possessive')} fingers sticky, so the strings did not feel easy to press.",
        ),
        QAItem(
            question=f"How did {fr.label} help {c.label} solve the problem?",
            answer=f"{fr.label} helped by being kind, wiping the juice away, and showing a finger map so {c.label} could learn the chord step by step.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, {c.label} could {activity.verb}, the chord rang clearly, and the two friends shared the papaya and smiled together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is papaya?",
            answer="Papaya is a sweet tropical fruit with soft orange flesh. People can eat it as a snack or in fruit bowls.",
        ),
        QAItem(
            question="What is a chord?",
            answer="A chord is when two or more notes are played together in music, so the sound feels full and warm.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring with someone else.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means noticing a problem and trying smart, calm steps to fix it.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, sharing with them, and helping them feel happy and safe.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,F) :- setting(S), activity(A), fix(F).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
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
    StoryParams(setting="music_room", activity="learn_chord", fix="napkin_map", name="Mia", gender="girl",
                friend_name="Jun", friend_gender="boy"),
    StoryParams(setting="porch", activity="practice", fix="clean_hands", name="Noah", gender="boy",
                friend_name="Bea", friend_gender="girl"),
    StoryParams(setting="library_corner", activity="learn_chord", fix="napkin_map", name="Lina", gender="girl",
                friend_name="Ari", friend_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} and {p.friend_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
