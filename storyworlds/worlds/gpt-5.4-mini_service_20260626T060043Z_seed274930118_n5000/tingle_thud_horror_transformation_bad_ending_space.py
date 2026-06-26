#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tingle_thud_horror_transformation_bad_ending_space.py
===========================================================================================================

A small space-adventure story world with a strange transformation and a bad ending.

Seed image:
- A child or young crew member on a tiny space voyage hears a tingle in the hull,
  then a thud, then feels horror as something in the air changes them.

This world models a compact space adventure with:
- physical meters: pressure, distance, damage, glow, drift
- emotional memes: curiosity, fear, horror, resolve, awe, loss

The tale is intentionally narrow: the tension is not "can we fix it?" but
"what happens when the transformation cannot be stopped?"
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    detail: str
    hazard: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Exposure:
    id: str
    noun: str
    verb: str
    trigger: str
    tingle_note: str
    thud_note: str
    transform_note: str
    fear_note: str
    bad_end_note: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    vulnerable_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Outcome:
    id: str
    final_image: str
    closing: str


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    setting: Setting
    exposure: Exposure
    prize: Prize
    outcome: Outcome
    protagonist: Entity
    companion: Entity
    artifact: Entity
    story: list[str] = field(default_factory=list)
    fired: set[str] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.story.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orbital_station": Setting(
        id="orbital_station",
        place="an orbital station",
        detail="The windows showed a blue planet hanging far below like a marble.",
        hazard="silent drift through the station corridor",
        tags={"space", "station", "orbit"},
    ),
    "moon_outpost": Setting(
        id="moon_outpost",
        place="a moon outpost",
        detail="The dust outside looked pale and soft, but the airlocks stayed sealed tight.",
        hazard="thin air and cold metal halls",
        tags={"space", "moon", "outpost"},
    ),
    "tiny_ship": Setting(
        id="tiny_ship",
        place="a tiny ship",
        detail="The little ship hummed like a sleepy bee, with one narrow hallway and one bright console.",
        hazard="a long trip with no easy turn-around",
        tags={"space", "ship"},
    ),
}

EXPOSURES = {
    "signal_shell": Exposure(
        id="signal_shell",
        noun="signal shell",
        verb="inspect the signal shell",
        trigger="a silver shell found near the hatch",
        tingle_note="A faint tingle slipped through the gloves when the shell woke up.",
        thud_note="Then came a sharp thud from the wall, as if something had answered from inside the metal.",
        transform_note="The shell flashed, and the young crew member began to change, piece by piece, into a shimmering space-creature.",
        fear_note="Horror flooded the corridor when the hands turned bright and strange.",
        bad_end_note="No alarm could pull the change backward.",
        tags={"shell", "signal", "transformation"},
    ),
    "drift_pod": Exposure(
        id="drift_pod",
        noun="drift pod",
        verb="open the drift pod",
        trigger="a small pod drifting outside the airlock window",
        tingle_note="A little tingle buzzed at the edges of the visor when the pod cracked open.",
        thud_note="A heavy thud rattled the floor as the pod bumped the hull.",
        transform_note="A pale mist rolled out, and the crew member's shadow stretched and remade itself into a long alien shape.",
        fear_note="Horror rose fast when the voice came out thin and not quite human.",
        bad_end_note="The pod's mist did not stop, and the change kept going.",
        tags={"pod", "mist", "transformation"},
    ),
    "star_egg": Exposure(
        id="star_egg",
        noun="star egg",
        verb="touch the star egg",
        trigger="a warm egg-shaped stone glowing near the cargo clamp",
        tingle_note="The warm stone gave off a tingle like tiny sparks under the skin.",
        thud_note="A thud rolled through the hatch when the stone woke and tapped the deck from the inside.",
        transform_note="Light climbed up the arms, and the crew member turned into a smooth, shining figure made for the dark.",
        fear_note="Horror pinched the chest when the face lost its old shape.",
        bad_end_note="The new shape would not fade, and the ship had no cure for it.",
        tags={"egg", "light", "transformation"},
    ),
}

PRIZES = {
    "visor": Prize(
        id="visor",
        label="visor",
        phrase="a clear helmet visor",
        region="head",
        vulnerable_to={"mist", "signal", "light"},
        tags={"helmet", "gear"},
    ),
    "gloves": Prize(
        id="gloves",
        label="gloves",
        phrase="soft white gloves",
        region="hands",
        vulnerable_to={"signal", "light"},
        tags={"gloves", "gear"},
    ),
    "badge": Prize(
        id="badge",
        label="badge",
        phrase="a little silver badge",
        region="chest",
        vulnerable_to={"signal", "mist", "light"},
        tags={"badge", "gear"},
    ),
}

OUTCOMES = {
    "lost": Outcome(
        id="lost",
        final_image="By the end, the crew member floated in the corridor as a changed shape of light, and the ship sailed on without a way to bring the old self back.",
        closing="The adventure ended with the station quiet and the new shape alone under the blue glow.",
    )
}


# ---------------------------------------------------------------------------
# Parameters and helpers
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    exposure: str
    prize: str
    name: str
    role: str
    seed: Optional[int] = None


NAMES = ["Milo", "Nia", "Arin", "Luna", "Kai", "Tess", "Pip", "Rin"]
ROLES = ["boy", "girl"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for eid, exposure in EXPOSURES.items():
            for pid, prize in PRIZES.items():
                if prize.region in {"head", "hands", "chest"} and (
                    any(tag in exposure.tags for tag in prize.vulnerable_to)
                ):
                    combos.append((sid, eid, pid))
    return combos


def explain_invalid(setting: str, exposure: str, prize: str) -> str:
    return (
        f"(No story: {EXPOSURES[exposure].noun} would not reasonably threaten {PRIZES[prize].phrase} "
        f"in {SETTINGS[setting].place} for this transformation tale.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space adventure storyworld: a tingle, a thud, horror, and a bad transformation ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--exposure", choices=EXPOSURES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    if args.setting and args.exposure and args.prize:
        if (args.setting, args.exposure, args.prize) not in valid_combos():
            raise StoryError(explain_invalid(args.setting, args.exposure, args.prize))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.exposure is None or c[1] == args.exposure)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid space-transformation combination matches the given options.)")

    setting, exposure, prize = rng.choice(sorted(combos))
    role = args.role or rng.choice(ROLES)
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, exposure=exposure, prize=prize, name=name, role=role)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    exposure = EXPOSURES[params.exposure]
    prize = PRIZES[params.prize]
    outcome = OUTCOMES["lost"]

    protagonist = Entity(
        id=params.name,
        kind="character",
        type=params.role,
        label=params.name,
        meters={"distance": 0.0, "damage": 0.0, "drift": 0.0, "glow": 0.0},
        memes={"curiosity": 1.0, "fear": 0.0, "horror": 0.0, "resolve": 0.0, "loss": 0.0},
    )
    companion = Entity(
        id="Captain",
        kind="character",
        type="adult",
        label="the captain",
        meters={"distance": 0.0},
        memes={"worry": 0.0},
    )
    artifact = Entity(
        id=exposure.id,
        kind="thing",
        type="artifact",
        label=exposure.noun,
        phrase=exposure.trigger,
    )

    world = World(
        setting=setting,
        exposure=exposure,
        prize=prize,
        outcome=outcome,
        protagonist=protagonist,
        companion=companion,
        artifact=artifact,
    )

    # Setup
    world.say(f"{params.name} was a small {params.role} on {setting.place}.")
    world.say(setting.detail)
    world.say(f"{params.name} loved the quiet hum of the ship and the bright blink of the panels.")

    # Tension
    world.say(f"One shift, {params.name} found {exposure.trigger}.")
    world.say(exposure.tingle_note)
    protagonist.meters["distance"] += 1.0
    protagonist.memes["curiosity"] += 1.0
    world.say(f"{params.name} reached closer, and then {exposure.thud_note.lower()}")

    # Transformation
    protagonist.memes["fear"] += 1.0
    protagonist.memes["horror"] += 2.0
    protagonist.meters["damage"] += 1.0
    protagonist.meters["glow"] += 1.0
    world.say(exposure.transform_note)
    world.say(exposure.fear_note)
    world.say(
        f"{params.name} tried to pull back, but the change had already caught {protagonist.pronoun('object')} "
        f"in the middle of the corridor."
    )

    # Bad ending
    protagonist.meters["drift"] += 1.0
    protagonist.memes["loss"] += 2.0
    world.say(exposure.bad_end_note)
    world.say(outcome.final_image)
    world.say(outcome.closing)

    world.facts.update(
        setting=setting,
        exposure=exposure,
        prize=prize,
        outcome=outcome,
        protagonist=protagonist,
        companion=companion,
        artifact=artifact,
        transformed=True,
        bad_ending=True,
        had_tingle=True,
        had_thud=True,
        had_horror=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure for a young child including the words "tingle", "thud", and "horror".',
        f"Tell a compact story set in {f['setting'].place} where {f['protagonist'].label} discovers {f['exposure'].noun} and cannot stop the transformation.",
        f"Write a kid-facing sci-fi tale with a strange change, a bad ending, and a final image that shows the new shape left behind.",
    ]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["protagonist"]
    s = f["setting"]
    e = f["exposure"]
    pr = f["prize"]
    return [
        QAItem(
            question=f"Where was {p.label} when the strange change started?",
            answer=f"{p.label} was in {s.place}. The place was quiet at first, but it held the weird thing that started the trouble.",
        ),
        QAItem(
            question=f"What happened after the tingle and the thud?",
            answer=f"After the tingle and the thud, {e.transform_note.lower()} That is when the story turned into a transformation and the bad ending began.",
        ),
        QAItem(
            question=f"Why did {p.label} feel horror in the story?",
            answer=f"{p.label} felt horror because the change could not be stopped, and the old self was slipping away while the body became something new and strange.",
        ),
        QAItem(
            question=f"What was the prize or special item in the story?",
            answer=f"The special item was {pr.phrase}. It mattered because the strange force was dangerous around gear like that.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: {f['outcome'].closing}",
        ),
    ]


WORLD_KNOWLEDGE = {
    "space": [
        QAItem(
            question="What is space?",
            answer="Space is the huge dark area beyond Earth where planets, stars, and ships can travel.",
        )
    ],
    "station": [
        QAItem(
            question="What is a space station?",
            answer="A space station is a place people can live and work in while they orbit above a planet.",
        )
    ],
    "ship": [
        QAItem(
            question="What does a spaceship do?",
            answer="A spaceship carries people or tools through space from one place to another.",
        )
    ],
    "shell": [
        QAItem(
            question="What is a shell?",
            answer="A shell is a hard outer cover that protects something inside.",
        )
    ],
    "pod": [
        QAItem(
            question="What is a pod?",
            answer="A pod is a small enclosed container or craft, often used to carry something safely.",
        )
    ],
    "egg": [
        QAItem(
            question="What is an egg-shaped thing?",
            answer="An egg-shaped thing is round and smooth, with a shape like a real egg.",
        )
    ],
    "transformation": [
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["setting"].tags) | set(world.facts["exposure"].tags)
    out: list[QAItem] = []
    for key in ["space", "station", "ship", "shell", "pod", "egg", "transformation"]:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
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
    p = world.protagonist
    lines = ["--- world model state ---"]
    lines.append(f"setting: {world.setting.id}")
    lines.append(f"exposure: {world.exposure.id}")
    lines.append(f"prize: {world.prize.id}")
    lines.append(f"protagonist meters: {p.meters}")
    lines.append(f"protagonist memes: {p.memes}")
    lines.append(f"fired: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting_fact(S).
exposure(E) :- exposure_fact(E).
prize(P) :- prize_fact(P).

valid(S,E,P) :- setting(S), exposure(E), prize(P), risk(E,P).

risk(E,P) :- exposure_tag(E,T), prize_tag(P,T).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("setting_tag", sid, t))
    for eid, e in EXPOSURES.items():
        lines.append(asp.fact("exposure_fact", eid))
        for t in sorted(e.tags):
            lines.append(asp.fact("exposure_tag", eid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize_fact", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("prize_tag", pid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="orbital_station", exposure="signal_shell", prize="visor", name="Milo", role="boy"),
    StoryParams(setting="moon_outpost", exposure="drift_pod", prize="gloves", name="Nia", role="girl"),
    StoryParams(setting="tiny_ship", exposure="star_egg", prize="badge", name="Kai", role="boy"),
]


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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            i += 1
            seed = base_seed + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.exposure} in {p.setting} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
