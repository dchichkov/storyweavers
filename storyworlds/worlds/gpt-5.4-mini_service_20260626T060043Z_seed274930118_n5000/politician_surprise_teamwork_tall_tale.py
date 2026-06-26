#!/usr/bin/env python3
"""
A small Storyweavers world: a tall-tale surprise around a politician and a team
that has to work together to save a day.

Premise:
- A friendly politician visits a tiny frontier town for a fair.
- A surprise wind overturns the big banner and scatters the stage pieces.
- The townsfolk and the politician must use teamwork to finish the event.

The simulated state tracks:
- physical meters: banner_tilt, scattered_bits, carried_load, wind, stage_ready
- emotional memes: surprise, teamwork, pride, worry, relief

The story is driven by world changes rather than a fixed paragraph swap.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"woman", "girl", "mayor"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"man", "boy", "politician"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Town:
    name: str
    feature: str = ""
    place: str = "the town square"


class World:
    def __init__(self, town: Town) -> None:
        self.town = town
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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

        w = World(self.town)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    town: str
    politician: str
    helper: str
    surprise: str
    teamwork: str
    seed: Optional[int] = None


TOWNS = {
    "dusty_crossing": Town(name="Dusty Crossing", feature="a paper-thin wind"),
    "sunny_gulch": Town(name="Sunny Gulch", feature="a bell tower that rang on the hour"),
    "blue_ridge": Town(name="Blue Ridge", feature="a hill where kites loved to fly"),
}

POLITICIANS = {
    "councilman": {
        "label": "councilman",
        "phrase": "a friendly councilman in a striped vest",
        "type": "man",
    },
    "mayor": {
        "label": "mayor",
        "phrase": "a smiling mayor with a brass badge",
        "type": "mayor",
    },
    "representative": {
        "label": "representative",
        "phrase": "a quick-footed representative with rolled-up sleeves",
        "type": "man",
    },
}

HELPERS = {
    "farmer": {"label": "farmer", "phrase": "a farmer with a red handkerchief"},
    "baker": {"label": "baker", "phrase": "a baker with flour on her apron"},
    "carpenter": {"label": "carpenter", "phrase": "a carpenter with sturdy boots"},
    "teacher": {"label": "teacher", "phrase": "a teacher with chalk on his cuff"},
}

SURPRISES = {
    "wind": {
        "label": "surprise wind",
        "issue": "wind",
        "verb": "gusted",
        "effect": "knocked the banner sideways",
        "mess": "wind-swept",
    },
    "goat": {
        "label": "surprise goat",
        "issue": "goat",
        "verb": "trotted",
        "effect": "tugged the ribbon free",
        "mess": "jostled",
    },
    "carts": {
        "label": "surprise wagon cart",
        "issue": "wagon cart",
        "verb": "rolled",
        "effect": "bumped the stage steps apart",
        "mess": "shaken",
    },
}

TEAMWORKS = {
    "rope_chain": {
        "label": "rope chain",
        "method": "linked arms and held a rope chain",
        "result": "lifted the banner back into place",
    },
    "bucket_line": {
        "label": "bucket line",
        "method": "formed a bucket line to carry the boards",
        "result": "stacked the stage pieces neatly",
    },
    "hush_signal": {
        "label": "hush signal",
        "method": "shared a hush signal and worked in turns",
        "result": "fixed the ribbon and straightened the signs",
    },
}

PEOPLE_NAMES = ["Ada", "Milo", "Nell", "Jasper", "Ivy", "Rowan", "Poppy", "Otis"]


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    town = TOWNS[params.town]
    world = World(town)

    pol_cfg = POLITICIANS[params.politician]
    helper_cfg = HELPERS[params.helper]
    surprise_cfg = SURPRISES[params.surprise]
    team_cfg = TEAMWORKS[params.teamwork]

    politician = world.add(
        Entity(
            id="Politician",
            kind="character",
            type=pol_cfg["type"],
            label=pol_cfg["label"],
            phrase=pol_cfg["phrase"],
            meters={"banner_tilt": 0.0, "stage_ready": 0.0},
            memes={"surprise": 0.0, "teamwork": 0.0, "pride": 0.0, "worry": 0.0, "relief": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type="person",
            label=helper_cfg["label"],
            phrase=helper_cfg["phrase"],
            meters={"carried_load": 0.0},
            memes={"surprise": 0.0, "teamwork": 0.0, "relief": 0.0},
        )
    )
    banner = world.add(
        Entity(
            id="Banner",
            kind="thing",
            type="banner",
            label="banner",
            phrase="the long fair banner",
            meters={"banner_tilt": 0.0},
        )
    )
    stage = world.add(
        Entity(
            id="Stage",
            kind="thing",
            type="stage",
            label="stage",
            phrase="the little parade stage",
            meters={"stage_ready": 0.0, "scattered_bits": 0.0},
        )
    )

    # Act 1: setup
    world.say(
        f"At {town.name}, where {town.feature}, there lived {pol_cfg['phrase']} who came to visit the town square."
    )
    world.say(
        f"{helper_cfg['phrase']} was already there, setting out planks beside the stage, because the fair needed a grand opening."
    )
    politician.memes["pride"] += 1
    world.say(
        f"The politician smiled, waved at the crowd, and promised that the ribbon-cutting would be the tallest, brightest one the town had ever seen."
    )
    world.para()

    # Act 2: surprise
    surprise_cfg = SURPRISES[params.surprise]
    politician.memes["surprise"] += 2
    helper.memes["surprise"] += 1
    world.facts["surprise_label"] = surprise_cfg["label"]
    world.facts["team_label"] = team_cfg["label"]
    world.facts["issue"] = surprise_cfg["issue"]
    world.say(
        f"Then, just as the first drumbeat began, a {surprise_cfg['label']} came {surprise_cfg['verb']} through the square and {surprise_cfg['effect']}."
    )
    world.say(
        f"The crowd gave a little gasp. Even the politician blinked, because the sign leaned, the ropes trembled, and the stage looked busy all at once."
    )
    politician.meters["banner_tilt"] += 1
    stage.meters["scattered_bits"] += 1
    politician.memes["worry"] += 1
    world.say(
        f"{pol_cfg['label'].capitalize()} said, 'Well now, that is a bigger wobble than a windy fence post on market day.'"
    )
    world.para()

    # Act 3: teamwork fix
    politician.memes["teamwork"] += 1
    helper.memes["teamwork"] += 2
    world.say(
        f"Nobody ran away. The politician stepped down from the platform and called, 'Let's do this together.'"
    )
    world.say(
        f"{helper_cfg['label'].capitalize()} answered at once, and soon the whole square joined in {team_cfg['label']} style: {team_cfg['method']}."
    )
    if params.teamwork == "rope_chain":
        banner.meters["banner_tilt"] = 0.0
        politician.meters["stage_ready"] = 1.0
    elif params.teamwork == "bucket_line":
        stage.meters["scattered_bits"] = 0.0
        politician.meters["stage_ready"] = 1.0
    else:
        banner.meters["banner_tilt"] = 0.0
        stage.meters["scattered_bits"] = 0.0
        politician.meters["stage_ready"] = 1.0

    politician.memes["relief"] += 2
    helper.memes["relief"] += 2
    politician.memes["pride"] += 1
    world.say(
        f"Together they {team_cfg['result']}, and the crowd cheered as if the whole town had found a giant new heart."
    )
    world.say(
        f"At the end, the politician laughed, the helper grinned, and the fair began under a straight banner and a sky that looked freshly brushed."
    )

    world.facts.update(
        politician=politician,
        helper=helper,
        banner=banner,
        stage=stage,
        town=town,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
surprise(X) :- issue(X).
teamwork(Y) :- team(Y).

valid_story(Town, P, H, S, T) :- town(Town), politician(P), helper(H), surprise(S), team(T).
"""

def asp_facts() -> str:
    import asp

    lines = []
    for town_id in TOWNS:
        lines.append(asp.fact("town", town_id))
    for pid in POLITICIANS:
        lines.append(asp.fact("politician", pid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for sid, cfg in SURPRISES.items():
        lines.append(asp.fact("issue", cfg["issue"]))
        lines.append(asp.fact("surprise", sid))
    for tid in TEAMWORKS:
        lines.append(asp.fact("team", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Q&A and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short tall-tale story for children about a {f["politician"].label} who gets a surprise at {f["town"].name}.',
        f"Tell a playful story where a {f['politician'].label} and a {f['helper'].label} use teamwork after a {f['surprise_label']}.",
        f"Write a simple frontier-style tale that ends with the town square fixed up and everybody cheering together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pol: Entity = f["politician"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    town: Town = f["town"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who came to visit the town square?",
            answer=f"The {pol.label} came to visit the town square in {town.name}.",
        ),
        QAItem(
            question="What surprised everybody?",
            answer=f"A {f['surprise_label']} surprised everybody and made the stage wobble.",
        ),
        QAItem(
            question="What did the politician and helper do at the end?",
            answer=f"They used {f['team_label']} teamwork to fix the problem together.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The banner stood straight again, the stage was ready, and the crowd cheered while the town got its fair day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help one another and do a job together instead of all by themselves.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect, so it can make you gasp or blink for a moment.",
        ),
        QAItem(
            question="What does a politician do?",
            answer="A politician is a leader who talks with people and helps make decisions for a town, city, or country.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Verification helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for town in TOWNS:
        for pol in POLITICIANS:
            for helper in HELPERS:
                for surp in SURPRISES:
                    for team in TEAMWORKS:
                        combos.append((town, pol, helper, surp, team))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: politician, surprise, teamwork.")
    ap.add_argument("--town", choices=TOWNS)
    ap.add_argument("--politician", choices=POLITICIANS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--teamwork", choices=TEAMWORKS)
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
    choices = valid_combos()
    choices = [
        c for c in choices
        if (args.town is None or c[0] == args.town)
        and (args.politician is None or c[1] == args.politician)
        and (args.helper is None or c[2] == args.helper)
        and (args.surprise is None or c[3] == args.surprise)
        and (args.teamwork is None or c[4] == args.teamwork)
    ]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    town, politician, helper, surprise, teamwork = rng.choice(sorted(choices))
    return StoryParams(town=town, politician=politician, helper=helper, surprise=surprise, teamwork=teamwork)


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.label} {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("dusty_crossing", "councilman", "farmer", "wind", "rope_chain"),
            StoryParams("sunny_gulch", "mayor", "baker", "goat", "bucket_line"),
            StoryParams("blue_ridge", "representative", "carpenter", "carts", "hush_signal"),
        ]
        samples = [generate(p) for p in curated]
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
