#!/usr/bin/env python3
"""
storyworlds/worlds/biography_moral_value_rhyme_tall_tale.py
============================================================

A tiny storyworld for tall-tale biographies with a clear moral, a little rhyme,
and a state-driven rise from nobody to somebody. The premise is simple:
someone begins small, runs into a boastful or selfish wobble, then learns a
moral value, and the ending proves the change in what they do.

The stories are deliberately exaggerated in a tall-tale style: boots stomp
like drums, hats shade a whole street, and a day of work can feel as long as a
county road. But the world model still matters: skill, pride, kindness, fame,
tiredness, and trust all change the shape of the tale.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "person"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    risk: str
    fix: str
    moral: str
    rhyme: str
    place_hint: str = ""


@dataclass
class World:
    place: Place
    hero: Entity | None = None
    helper: Entity | None = None
    rival: Entity | None = None
    challenge: Challenge | None = None
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

PLACES = {
    "riverbend": Place("Riverbend", "windy", {"help", "tell_truth"}),
    "hilltown": Place("Hilltown", "bright", {"help", "practice", "tell_truth"}),
    "copper_fair": Place("Copper Fair", "noisy", {"help", "practice", "share"}),
    "pine_crossing": Place("Pine Crossing", "wild", {"help", "share", "tell_truth"}),
}

CHALLENGES = {
    "heavy_lift": Challenge(
        id="heavy_lift",
        verb="lift the giant kettle",
        gerund="lifting the giant kettle",
        risk="strain",
        fix="ask for help and share the load",
        moral="Many small hands can lift a big trouble.",
        rhyme="When the burden is tall as a tree, two hands can do what one can't see.",
        place_hint="market",
    ),
    "lost_lunch": Challenge(
        id="lost_lunch",
        verb="find the missing lunch pail",
        gerund="finding the missing lunch pail",
        risk="worry",
        fix="tell the truth and make amends",
        moral="A clean truth beats a shiny lie.",
        rhyme="If your words go crooked and sly, a straight-up truth will make things right.",
        place_hint="road",
    ),
    "muddy_bridge": Challenge(
        id="muddy_bridge",
        verb="cross the muddy bridge",
        gerund="crossing the muddy bridge",
        risk="slip",
        fix="walk slow and listen carefully",
        moral="Careful steps keep trouble from growing.",
        rhyme="Pick your step and mind your shoe, or the mud will make a fool of you.",
        place_hint="bridge",
    ),
    "rain_song": Challenge(
        id="rain_song",
        verb="sing above the storm",
        gerund="singing above the storm",
        risk="doubt",
        fix="keep a steady heart and cheer the crowd",
        moral="A brave voice can calm a shaking room.",
        rhyme="Sing through the thunder, loud and clear, and brave little hearts will gather near.",
        place_hint="square",
    ),
}

HERO_TYPES = ["girl", "boy"]
HERO_NAMES = ["Mabel", "Ira", "Nell", "Clem", "Ruby", "Otis", "Pearl", "Jasper", "June", "Wes"]
HELPER_NAMES = ["Aunt Dot", "Uncle Ben", "Gran", "Old Sal", "Mister Pike", "Miss Fern"]
RIVAL_NAMES = ["Big Muck", "Sly Finn", "Boss Bramble", "Ned Natter", "Tess Tangle"]
TRAITS = ["small", "swift", "stubborn", "cheerful", "plainspoken", "bright-eyed"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
    gender: str
    helper_name: str
    rival_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for chal_id, chal in CHALLENGES.items():
            if chal_id == "rain_song" and place_id == "copper_fair":
                continue
            if chal.verb and ("help" in place.affords or chal_id == "lost_lunch"):
                combos.append((place_id, chal_id))
    return combos


def explain_rejection(place: Place, chal: Challenge) -> str:
    return (
        f"(No story: {chal.gerund} does not fit neatly at {place.name}. "
        f"Try a place where the crowd can plausibly answer the challenge.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    chal = CHALLENGES[params.challenge]
    world = World(place=place, challenge=chal)

    hero = Entity(
        id=params.name,
        kind="person",
        type=params.gender,
        traits=["little", params.trait],
        meters={"skill": 0.0, "tired": 0.0, "fame": 0.0},
        memes={"pride": 1.0, "kindness": 0.0, "trust": 0.0, "shame": 0.0, "resolve": 0.0},
    )
    helper = Entity(
        id=params.helper_name,
        kind="person",
        type="adult",
        label=params.helper_name,
        meters={"skill": 2.0, "tired": 0.0},
        memes={"kindness": 2.0, "trust": 1.0},
    )
    rival = Entity(
        id=params.rival_name,
        kind="person",
        type="adult",
        label=params.rival_name,
        meters={"skill": 1.0},
        memes={"pride": 2.0, "kindness": 0.0},
    )
    world.hero = hero
    world.helper = helper
    world.rival = rival
    return world


def _narrate_intro(world: World) -> None:
    h = world.hero
    p = world.place
    world.say(
        f"{h.id} was a little {h.trait[1] if h.traits else 'plain'} {h.type} from {p.name}, "
        f"small as a fence nail but lively as a jay."
    )
    world.say(
        f"{h.id} loved tall tales, and {h.pronoun('possessive')} own favorite saying was, "
        f"“A brave heart can outwalk a thunderstorm any day.”"
    )


def _narrate_growth(world: World) -> None:
    h, chal = world.hero, world.challenge
    h.meters["skill"] += 1.0
    h.memes["pride"] += 0.5
    world.say(
        f"{h.id} practiced {chal.gerund} so often that {h.pronoun('possessive')} boots "
        f"seemed to remember the steps by themselves."
    )
    world.say(
        f"Before long, the neighbors said {h.id} had a grin wide enough to shade a porch."
    )


def _narrate_problem(world: World) -> None:
    h, r, chal = world.hero, world.rival, world.challenge
    h.memes["pride"] += 1.0
    world.para()
    world.say(
        f"One windy afternoon, {r.id} sneered that {h.id} was too small to {chal.verb}."
    )
    world.say(
        f"{h.id} puffed up like a hot biscuit and said {h.pronoun('subject')} could do it alone."
    )
    h.memes["stubbornness"] = h.memes.get("stubbornness", 0.0) + 1.0
    h.meters["tired"] += 0.5
    world.facts["risk"] = chal.risk


def _narrate_turn(world: World) -> None:
    h, helper, chal = world.hero, world.helper, world.challenge
    world.say(
        f"Then {helper.id} came along and told {h.id}, “Big jobs are not a parade for one drum; "
        f"they are a song for many feet.”"
    )
    world.say(
        f"{helper.id} showed {h.id} a steadier way to {chal.fix}."
    )
    h.memes["trust"] += 1.0
    h.memes["resolve"] += 1.0
    h.memes["pride"] = max(0.0, h.memes["pride"] - 0.5)
    h.memes["kindness"] += 1.0


def _narrate_resolution(world: World) -> None:
    h, helper, rival, chal = world.hero, world.helper, world.rival, world.challenge
    h.meters["skill"] += 1.0
    h.meters["fame"] += 1.0
    h.meters["tired"] += 1.0
    h.memes["pride"] = max(0.0, h.memes["pride"] - 0.5)
    h.memes["trust"] += 1.0
    world.para()
    world.say(
        f"{h.id} looked at {rival.id}, took a breath, and chose the wiser road."
    )
    world.say(
        f"Together, {h.id} and {helper.id} did {chal.fix}, and the trouble shrank like an ice patch in noon sun."
    )
    world.say(
        f"At the end, {h.id} was still little, but now the whole town knew {h.pronoun('subject')} "
        f"could carry a good deed farther than a wagon could carry hay."
    )
    world.say(
        f"{chal.rhyme} That was the way {h.id} learned {chal.moral.lower()}"
    )


def tell_story(world: World) -> World:
    _narrate_intro(world)
    _narrate_growth(world)
    _narrate_problem(world)
    _narrate_turn(world)
    _narrate_resolution(world)
    world.facts.update(
        hero=world.hero,
        helper=world.helper,
        rival=world.rival,
        challenge=world.challenge,
        place=world.place,
        learned_moral=world.challenge.moral,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    h = world.hero
    chal = world.challenge
    return [
        f"Write a short tall-tale biography about {h.id} that teaches a moral and includes a rhyme.",
        f"Tell a child-friendly story about a small hero who learns that {chal.moral.lower()}",
        f"Write a brief biography with a folk-tale voice, a hard choice, and the line: “{chal.rhyme}”",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, helper, rival, chal = world.hero, world.helper, world.rival, world.challenge
    return [
        QAItem(
            question=f"Who is this biography about?",
            answer=(
                f"It is about {h.id}, a little {h.type} from {world.place.name} who grows "
                f"wiser by learning to {chal.fix}."
            ),
        ),
        QAItem(
            question=f"What problem made {h.id} need help?",
            answer=(
                f"{rival.id} said {h.id} was too small to {chal.verb}, so {h.id} tried to do it alone "
                f"until the wiser lesson came along."
            ),
        ),
        QAItem(
            question=f"What did {helper.id} teach {h.id}?",
            answer=(
                f"{helper.id} taught {h.id} that {chal.moral.lower()}"
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended with {h.id} choosing the safer, kinder way and succeeding with {helper.id}'s help."
            ),
        ),
    ]


KNOWLEDGE = {
    "truth": [(
        "Why is it good to tell the truth?",
        "Telling the truth helps people trust each other and fix mistakes before they grow bigger."
    )],
    "help": [(
        "Why does asking for help matter?",
        "Asking for help can make a hard job easier and safer, because more than one person can share the work."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness is doing or saying things that help someone feel cared for, safe, and respected."
    )],
    "trust": [(
        "What does trust mean?",
        "Trust means believing someone will be honest and keep their promise as best they can."
    )],
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme is when words sound alike at the ends, like 'night' and 'light' or 'tree' and 'me.'"
    )],
    "moral": [(
        "What is a moral in a story?",
        "A moral is the lesson a story wants to teach about how to act or think."
    )],
    "tall_tale": [(
        "What is a tall tale?",
        "A tall tale is a funny story that stretches the truth way past ordinary size, like a fish as big as a barn."
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["tall_tale"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["moral"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["rhyme"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["help"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["truth"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["kindness"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["trust"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.helper, world.rival]:
        if e is None:
            continue
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:12} meters={meters} memes={memes}")
    lines.append(f"  place={world.place.name}")
    lines.append(f"  challenge={world.challenge.id}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_place(P) :- place(P).
valid_challenge(C) :- challenge(C).

compatible(P, C) :- valid_place(P), valid_challenge(C), affords(P, help).
compatible(P, lost_lunch) :- place(P).
compatible(P, rain_song) :- place(P), not forbidden_rain_song(P).
valid_story(P, C) :- compatible(P, C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
        if cid == "rain_song":
            lines.append(asp.fact("forbidden_rain_song", "copper_fair"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Sample generation
# ---------------------------------------------------------------------------

def valid_story_params(place: str, challenge: str) -> bool:
    return (place, challenge) in valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale biography storyworld with moral and rhyme.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--challenge", choices=sorted(CHALLENGES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--rival-name")
    ap.add_argument("--trait", choices=sorted(TRAITS))
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
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.challenge is None or c[1] == args.challenge)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    rival_name = args.rival_name or rng.choice(RIVAL_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if not valid_story_params(place, challenge):
        raise StoryError(explain_rejection(PLACES[place], CHALLENGES[challenge]))
    return StoryParams(
        place=place,
        challenge=challenge,
        name=name,
        gender=gender,
        helper_name=helper_name,
        rival_name=rival_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="riverbend", challenge="lost_lunch", name="Mabel", gender="girl", helper_name="Gran", rival_name="Sly Finn", trait="bright-eyed"),
    StoryParams(place="hilltown", challenge="heavy_lift", name="Otis", gender="boy", helper_name="Aunt Dot", rival_name="Big Muck", trait="stubborn"),
    StoryParams(place="pine_crossing", challenge="muddy_bridge", name="June", gender="girl", helper_name="Miss Fern", rival_name="Ned Natter", trait="cheerful"),
    StoryParams(place="copper_fair", challenge="heavy_lift", name="Jasper", gender="boy", helper_name="Mister Pike", rival_name="Boss Bramble", trait="plainspoken"),
]


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for p, c in combos:
            print(f"  {p:14} {c}")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.challenge} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
