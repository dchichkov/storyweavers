#!/usr/bin/env python3
"""
A small storyworld in a detective-story style.

Premise:
A detective helps a gymnast finish a quest after a strict limit and a gloomy
setback make the case look impossible. Humor becomes the useful tool that turns
the night around.

This world is intentionally narrow:
- a gymnast is on a quest
- a limit may block the quest
- a depressing setback may lower morale
- humor can restore enough spirit to solve the case
- the detective gathers clues, tests a theory, and resolves the problem

The simulation keeps both physical state in meters and emotional state in memes.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"detective", "man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "gymnast"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Scene:
    place: str
    time_of_day: str = "night"


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    limit_kind: str
    depress_kind: str
    name: str
    gender: str
    detective_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "gym": Scene(place="the gym", time_of_day="afternoon"),
    "hall": Scene(place="the old hall", time_of_day="evening"),
    "studio": Scene(place="the practice studio", time_of_day="morning"),
    "museum": Scene(place="the quiet museum", time_of_day="night"),
}

LIMITS = {
    "time": {
        "label": "a strict time limit",
        "detail": "the clock was almost out of time",
        "effect": "time_left",
        "threshold": 1.0,
    },
    "height": {
        "label": "a low ceiling limit",
        "detail": "the ceiling was too low for big leaps",
        "effect": "height_clearance",
        "threshold": 1.0,
    },
    "noise": {
        "label": "a noise limit",
        "detail": "the room had to stay quiet",
        "effect": "noise_limit",
        "threshold": 1.0,
    },
}

DEPRESSIONS = {
    "rain": {
        "label": "a gloomy rain shower",
        "detail": "the rain kept tapping the windows",
        "meme": "depress",
    },
    "loss": {
        "label": "a lost clue",
        "detail": "one tiny clue had gone missing",
        "meme": "depress",
    },
    "mistake": {
        "label": "a bad mistake",
        "detail": "a wrong turn had made everything feel worse",
        "meme": "depress",
    },
}

GENDERS = ["girl", "boy"]
GIRL_NAMES = ["Mia", "Nina", "Luna", "Tara", "Ava"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Eli", "Theo"]
DETECTIVE_NAMES = ["Detective Rue", "Detective Quinn", "Detective Vale", "Detective Moss"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
limit_choice(time).
limit_choice(height).
limit_choice(noise).

depress_choice(rain).
depress_choice(loss).
depress_choice(mistake).

valid_story(P, L, D) :- place(P), limit_choice(L), depress_choice(D).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for l in LIMITS:
        lines.append(asp.fact("limit_choice", l))
    for d in DEPRESSIONS:
        lines.append(asp.fact("depress_choice", d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, l, d) for p in PLACES for l in LIMITS for d in DEPRESSIONS]


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_gate(limit_kind: str, depress_kind: str) -> None:
    if limit_kind not in LIMITS:
        raise StoryError(f"Unknown limit kind: {limit_kind}")
    if depress_kind not in DEPRESSIONS:
        raise StoryError(f"Unknown depress kind: {depress_kind}")


def predict_outcome(world: World, gymnast: Entity, limit_kind: str) -> dict[str, object]:
    sim = world.copy()
    g = sim.get(gymnast.id)
    limit = LIMITS[limit_kind]
    if limit_kind == "time":
        g.meters["time_left"] = 0.0
    elif limit_kind == "height":
        g.meters["height_clearance"] = 0.0
    elif limit_kind == "noise":
        g.meters["noise_limit"] = 0.0
    return {
        "blocked": any(g.meters.get(limit["effect"], 0.0) < limit["threshold"] for limit in [limit]),
        "morale": g.memes.get("morale", 0.0),
    }


def detective_intro(world: World, det: Entity) -> None:
    world.say(
        f"Detective {det.label} arrived at {world.scene.place} with a notebook, a calm voice, "
        f"and a habit of noticing small things."
    )


def setup_case(world: World, gymnast: Entity, det: Entity, limit_kind: str, depress_kind: str) -> None:
    limit = LIMITS[limit_kind]
    depress = DEPRESSIONS[depress_kind]
    world.say(
        f"{gymnast.label} was a gymnast with a quest: finish one perfect routine at {world.scene.place}."
    )
    world.say(
        f"But there was {limit['label']}, and {depress['label']} made the room feel heavier."
    )
    world.say(f"{limit['detail'].capitalize()}; {depress['detail']}.")
    gymnast.memes["hope"] = 1.0
    gymnast.memes["worry"] = 1.0
    det.memes["curiosity"] = 1.0


def gather_clues(world: World, det: Entity, gymnast: Entity, limit_kind: str) -> None:
    world.say(
        f"Detective {det.label} looked at the springboard, the chalk marks, and the path {gymnast.label} would need."
    )
    if limit_kind == "time":
        world.say("The clue was simple: there was only enough time for one careful try.")
    elif limit_kind == "height":
        world.say("The clue was simple: the leap had to stay low and precise.")
    else:
        world.say("The clue was simple: the routine had to stay quiet and smooth.")


def test_theory(world: World, gymnast: Entity, limit_kind: str) -> bool:
    limit = LIMITS[limit_kind]
    gymnast.meters[limit["effect"]] = 0.0
    world.say(
        f"{gymnast.label} tried the path once, and the limit bit back right away."
    )
    return True


def humor_turn(world: World, det: Entity, gymnast: Entity, depress_kind: str) -> None:
    depress = DEPRESSIONS[depress_kind]
    gymnast.memes["depress"] = 1.0
    world.say(
        f"Then Detective {det.label} gave a small grin and said, "
        f"\"Even hard cases can trip over a banana peel now and then.\""
    )
    world.say(
        f"The joke was tiny, but it worked; {depress['label']} stopped feeling quite so large."
    )
    gymnast.memes["humor"] = 1.0
    gymnast.memes["hope"] += 1.0
    gymnast.memes["worry"] = max(0.0, gymnast.memes.get("worry", 0.0) - 1.0)


def resolve_case(world: World, gymnast: Entity, det: Entity, limit_kind: str, depress_kind: str) -> None:
    limit = LIMITS[limit_kind]
    gymnast.meters[limit["effect"]] = 1.0
    gymnast.memes["depress"] = 0.0
    gymnast.memes["pride"] = 1.0
    world.say(
        f"With the limit understood and the gloomy mood lighter, {gymnast.label} tried again."
    )
    world.say(
        f"This time the routine fit the room, and Detective {det.label} watched the quest come together."
    )
    if limit_kind == "time":
        world.say("The final move landed just before the clock ran out.")
    elif limit_kind == "height":
        world.say("The leap stayed low, clean, and true.")
    else:
        world.say("The whole routine moved like a whisper through the room.")
    world.say(
        f"At the end, {gymnast.label} smiled, Detective {det.label} closed the case, and the room felt bright again."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    gymnast = world.add(Entity(id="gymnast", kind="character", type=params.gender, label=params.name))
    det = world.add(Entity(id="detective", kind="character", type="detective", label=params.detective_name))
    world.facts.update(
        gymnast=gymnast,
        detective=det,
        limit_kind=params.limit_kind,
        depress_kind=params.depress_kind,
        place=params.place,
    )
    detective_intro(world, det)
    setup_case(world, gymnast, det, params.limit_kind, params.depress_kind)
    world.say("")
    gather_clues(world, det, gymnast, params.limit_kind)
    test_theory(world, gymnast, params.limit_kind)
    humor_turn(world, det, gymnast, params.depress_kind)
    world.say("")
    resolve_case(world, gymnast, det, params.limit_kind, params.depress_kind)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    gymnast: Entity = f["gymnast"]  # type: ignore[assignment]
    return [
        f"Write a short detective story about a gymnast named {gymnast.label} who is chasing a quest.",
        f"Tell a child-friendly mystery where humor helps a gymnast solve a problem with a strict limit.",
        f"Write a simple detective tale in which a gloomy setback is eased by a joke and a brave try.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    gymnast: Entity = f["gymnast"]  # type: ignore[assignment]
    det: Entity = f["detective"]  # type: ignore[assignment]
    limit_kind = f["limit_kind"]
    depress_kind = f["depress_kind"]
    limit = LIMITS[limit_kind]
    depress = DEPRESSIONS[depress_kind]
    return [
        QAItem(
            question=f"Who was trying to finish the quest in the story?",
            answer=f"{gymnast.label} the gymnast was trying to finish the quest.",
        ),
        QAItem(
            question=f"What problem made the case hard at first?",
            answer=f"The hard part was {limit['label']}, and {depress['label']} made the mood feel lower.",
        ),
        QAItem(
            question=f"Who helped the gymnast think clearly?",
            answer=f"Detective {det.label} helped by noticing clues and keeping the case steady.",
        ),
        QAItem(
            question=f"What made the gymnast feel better before the final try?",
            answer="A small joke and a calm grin helped the gymnast feel better.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The gymnast made a successful final try, and Detective {det.label} closed the case with a happy ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gymnast?",
            answer="A gymnast is a person who practices jumps, balances, and careful body movements.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or mission that someone works hard to complete.",
        ),
        QAItem(
            question="What is humor for?",
            answer="Humor helps people feel lighter, laugh a little, and keep going when something is hard.",
        ),
        QAItem(
            question="What does depress mean in this storyworld?",
            answer="Depress means something gloomy or discouraging that makes a person feel lower or heavier inside.",
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues because clues help them understand what is happening and solve the case.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style gymnast quest storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--limit", dest="limit_kind", choices=LIMITS)
    ap.add_argument("--depress", dest="depress_kind", choices=DEPRESSIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--detective")
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
    place = args.place or rng.choice(list(PLACES))
    limit_kind = args.limit_kind or rng.choice(list(LIMITS))
    depress_kind = args.depress_kind or rng.choice(list(DEPRESSIONS))
    reasonableness_gate(limit_kind, depress_kind)
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or choose_name(rng, gender)
    detective_name = args.detective or rng.choice(DETECTIVE_NAMES)
    return StoryParams(
        place=place,
        limit_kind=limit_kind,
        depress_kind=depress_kind,
        name=name,
        gender=gender,
        detective_name=detective_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: type={e.type} label={e.label} meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="gym", limit_kind="time", depress_kind="rain", name="Mia", gender="girl", detective_name="Detective Rue"),
    StoryParams(place="hall", limit_kind="height", depress_kind="loss", name="Leo", gender="boy", detective_name="Detective Quinn"),
    StoryParams(place="studio", limit_kind="noise", depress_kind="mistake", name="Tara", gender="girl", detective_name="Detective Vale"),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for p, l, d in stories:
            print(f"  {p:10} {l:8} {d:8}")
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
