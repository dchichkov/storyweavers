#!/usr/bin/env python3
"""
A small bedtime storyworld about safety and astronomic wonder.

Premise:
A child wants to chase a bright starry sight at bedtime, but the caregiver
worries about safety. The compromise keeps the child cozy, safe, and still able
to enjoy the sky.

The storyworld is intentionally narrow: a few plausible combinations, a clear
turn from wanting to a safe happy ending, and grounded Q&A.
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
    location: str = ""
    safe: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    protects_from: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"window", "telescope"}),
    "backyard": Setting(place="the backyard", affords={"window", "telescope"}),
}

ACTIVITIES = {
    "window": Activity(
        id="window",
        verb="look at the stars",
        gerund="watching the stars",
        rush="run to the window",
        risk="leaning out too far",
        keyword="astronomic",
        tags={"astronomic", "safety", "stars"},
    ),
    "telescope": Activity(
        id="telescope",
        verb="peek through the telescope",
        gerund="peeking through the telescope",
        rush="run outside for the telescope",
        risk="tripping in the dark",
        keyword="astronomic",
        tags={"astronomic", "safety", "moon"},
    ),
}

PRIZES = {
    "pajamas": Prize(
        label="pajamas",
        phrase="soft bedtime pajamas",
        type="pajamas",
        location="body",
    ),
    "slippers": Prize(
        label="slippers",
        phrase="cozy slippers",
        type="slippers",
        location="feet",
    ),
}

GEAR = {
    "window_lock": Gear(
        id="window_lock",
        label="the window lock",
        prep="close and lock the window first",
        tail="kept the window shut",
        protects_from={"leaning out too far"},
    ),
    "night_light": Gear(
        id="night_light",
        label="the little night light",
        prep="turn on the little night light",
        tail="made the room bright enough to walk safely",
        protects_from={"tripping in the dark"},
    ),
    "blanket": Gear(
        id="blanket",
        label="a warm blanket",
        prep="wrap up in a warm blanket",
        tail="stayed warm and cozy by the window",
        protects_from={"tripping in the dark", "leaning out too far"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ivy", "Ada"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Owen", "Finn"]
TRAITS = ["curious", "gentle", "sleepy", "brave"]


# ---------------------------------------------------------------------------
# Story parameterization
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for a_id in setting.affords:
            for p_id, prize in PRIZES.items():
                combos.append((s_id, a_id, p_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: this bedtime scene does not have a safe way for "
        f"{activity.keyword} play to endanger {prize.label}. Try a different pair.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if args.activity not in {"window", "telescope"}:
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, activity, prize, name, gender, parent, trait)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(window, pajamas) :- activity(window), prize(pajamas).
at_risk(window, slippers) :- activity(window), prize(slippers).
at_risk(telescope, pajamas) :- activity(telescope), prize(pajamas).
at_risk(telescope, slippers) :- activity(telescope), prize(slippers).

safe_fix(window, pajamas, window_lock) :- at_risk(window, pajamas).
safe_fix(window, slippers, blanket) :- at_risk(window, slippers).
safe_fix(telescope, pajamas, night_light) :- at_risk(telescope, pajamas).
safe_fix(telescope, slippers, blanket) :- at_risk(telescope, slippers).

valid_story(S, A, P) :- setting(S), activity(A), prize(P), at_risk(A, P), safe_fix(A, P, _).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="parent"))
    prize = world.add(Entity(
        id=params.prize,
        type=params.prize,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=parent.id,
        location=PRIZES[params.prize].location,
    ))

    act = ACTIVITIES[params.activity]
    gear = None

    world.say(f"{hero.id} was a {params.trait} little {params.gender} who loved bedtime.")
    world.say(f"{hero.pronoun().capitalize()} liked the quiet room, soft blankets, and a tiny window full of stars.")
    world.say(f"One night, {hero.id} wore {hero.pronoun('possessive')} {prize.label} and wanted to {act.verb}.")

    world.para()
    world.say(f"At {world.setting.place}, {hero.id} saw something bright and far away.")
    world.say(f"{hero.id} wanted to {act.rush}, but {hero.pronoun('possessive')} {parent.label_word} worried about {act.risk}.")
    world.say(f'"If you do that, you could get hurt," said {hero.pronoun("possessive")} {parent.label_word}.')

    world.para()
    if params.activity == "window":
        gear = GEAR["window_lock"]
    else:
        gear = GEAR["night_light"] if params.prize == "pajamas" else GEAR["blanket"]
    world.say(f"{hero.id} pouted for a moment, because {hero.id} still wanted the astronomic view.")
    world.say(f"Then {hero.pronoun('possessive')} {parent.label_word} smiled and said, \"How about we {gear.prep}?\"")
    world.say(f"{hero.id} nodded, and together they {gear.tail}.")

    world.para()
    world.say(f"Soon {hero.id} was {act.gerund}, still cozy in {hero.pronoun('possessive')} {prize.label}.")
    if params.activity == "window":
        world.say(f"The stars looked like tiny silver crumbs, and the locked window kept everything safe.")
    else:
        world.say(f"The telescope showed the moon and a few blinking stars, while the room stayed safe and calm.")
    world.say(f"{hero.id} yawned, hugged {hero.pronoun('possessive')} {parent.label_word}, and fell asleep with a happy smile.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=act,
        gear=gear,
        setting=world.setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    act = f["activity"]
    prize = f["prize"]
    return [
        'Write a cozy bedtime story about safety and astronomic wonder with a happy ending.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {parent.label_word} worries about safety and {prize.label}.",
        f'Write a bedtime story that includes the word "{act.keyword}" and ends with everyone calm, safe, and sleepy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at bedtime?",
            answer=f"{hero.id} wanted to {act.verb} and enjoy the stars.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry?",
            answer=f"{parent.label_word.capitalize()} worried because {act.risk} could be unsafe at bedtime.",
        ),
        QAItem(
            question=f"What helped the story end safely?",
            answer=f"They used {gear.label} so {hero.id} could enjoy the astronomic sight without danger.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy, cozy, and sleepy after the safe plan worked.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a telescope do?",
            answer="A telescope helps you see faraway things like the moon and stars more clearly.",
        ),
        QAItem(
            question="Why is safety important at bedtime?",
            answer="Safety helps children stay cozy and avoid getting hurt while they rest or play quietly.",
        ),
        QAItem(
            question="What is the night sky?",
            answer="The night sky is the sky you see after dark, when stars and the moon can shine.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} location={e.location} owner={e.owner}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
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
    StoryParams(setting="bedroom", activity="window", prize="pajamas", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="bedroom", activity="telescope", prize="slippers", name="Noah", gender="boy", parent="father", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld about safety and astronomic wonder.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
