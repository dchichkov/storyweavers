#!/usr/bin/env python3
"""
storyworlds/worlds/frank_spy_repel_humor_pirate_tale.py
======================================================

A small pirate-tale story world about a frank sailor, a sneaky spy, and a
humorous way to repel trouble.

The seed premise:
- A frank pirate notices a spy aboard ship.
- The spy tries to steal a chart or compass.
- The crew uses humor, a bright trick, or a funny noise to repel the spy.
- The ending proves the ship is safer and the mood is lighter.

This world keeps the prose concrete and state-driven:
physical state: distance, stolen items, doors, deck, disguises, lanterns
emotional state: fear, suspicion, trust, laughter, relief

The inline ASP twin mirrors the Python reasonableness gate:
- a spy must be able to reach a guarded treasure
- a repelling gag must match the spy's weakness
- a valid story requires a workable setup, a tense middle, and a plausible fix
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    guarded: bool = False
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "sailor", "spy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class ShipSetting:
    place: str = "the deck of the Black Gull"
    holds: set[str] = field(default_factory=lambda: {"map", "compass"})
    has_hatch: bool = True
    has_lanterns: bool = True


@dataclass
class Goal:
    target: str
    lure: str
    stolen: str
    weakness: str
    risk: str
    repeller: str
    repeller_label: str
    repeller_action: str
    repeller_result: str
    humor_style: str
    keyword: str = "frank"
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: ShipSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "deck": ShipSetting(place="the deck of the Black Gull", holds={"map", "compass"}),
    "cabin": ShipSetting(place="the captain's cabin", holds={"map"}),
    "harbor": ShipSetting(place="the harbor pier", holds={"map", "coin"}),
}

GOALS = {
    "map": Goal(
        target="map",
        lure="the folded treasure map",
        stolen="the map",
        weakness="laughter",
        risk="the map could vanish into the spy's sleeve",
        repeller="parrot-joke",
        repeller_label="a parrot joke",
        repeller_action="squawk a joke about parrots wearing boots",
        repeller_result="the spy laughed so hard they dropped the map",
        humor_style="silly parrot joke",
        tags={"map", "spy", "humor"},
    ),
    "compass": Goal(
        target="compass",
        lure="the brass compass",
        stolen="the compass",
        weakness="mockery",
        risk="the compass could be hidden under a coat",
        repeller="wiggle-dance",
        repeller_label="a wiggly dance",
        repeller_action="do a wobbling captain's dance and make funny faces",
        repeller_result="the spy snorted and backed away from the compass",
        humor_style="wobbly dance",
        tags={"compass", "spy", "humor"},
    ),
}

HEROES = [
    ("Frank", "pirate", ["frank", "brave", "quick-eyed"]),
    ("Mara", "pirate", ["frank", "cheerful", "steady"]),
    ("Jeb", "sailor", ["frank", "kind", "sharp"]),
]
SPY_NAMES = ["Moth", "Silk", "Rook", "Tarn", "Vex"]


@dataclass
class StoryParams:
    setting: str
    goal: str
    hero: str
    hero_type: str
    spy: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def can_repel(goal: Goal) -> bool:
    return goal.weakness in {"laughter", "mockery"} and bool(goal.repeller_action)


def story_is_valid(setting: ShipSetting, goal: Goal) -> bool:
    return goal.target in setting.holds and can_repel(goal)


def explain_rejection(setting: ShipSetting, goal: Goal) -> str:
    if goal.target not in setting.holds:
        return f"(No story: {setting.place} does not naturally hold {goal.stolen}, so the spy has nothing good to steal there.)"
    return f"(No story: there is no believable humorous way to repel that threat.)"


# ---------------------------------------------------------------------------
# Narrative beats
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    goal = GOALS[params.goal]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=params.hero_type,
        traits=["frank", "brave"],
        meters={"attention": 1.0},
        memes={"trust": 1.0, "suspicion": 0.0, "humor": 0.5, "relief": 0.0},
    ))
    spy = world.add(Entity(
        id=params.spy,
        kind="character",
        type="spy",
        traits=["sly", "quiet"],
        meters={"distance": 1.0},
        memes={"secret": 1.0, "greed": 1.0, "nervous": 0.2},
    ))
    treasure = world.add(Entity(
        id=goal.target,
        kind="thing",
        type=goal.target,
        label=goal.target,
        phrase=goal.lure,
        owner=hero.id,
        guarded=True,
        meters={"safe": 1.0},
    ))

    world.facts.update(hero=hero, spy=spy, treasure=treasure, goal=goal, setting=setting)

    # Setup
    world.say(
        f"Frank {hero.id} was a frank {hero.type} aboard {setting.place}, and {hero.id} "
        f"noticed every odd creak in the boards."
    )
    world.say(
        f"{hero.id} guarded {goal.lure}, because a pirate ship with a good chart felt "
        f"twice as lively and twice as safe."
    )
    world.say(
        f"Near dusk, the spy {spy.id} slipped along the rails with a quiet grin, hoping to snatch {goal.stolen}."
    )

    # Tension
    world.para()
    hero.memes["suspicion"] += 1.0
    spy.meters["distance"] = 0.0
    world.say(
        f"{hero.id} pointed at {spy.id} and said, 'That one smells of secrets.' "
        f"The crew chuckled, but their hands tightened on the rope."
    )
    world.say(
        f"{spy.id} reached for {goal.stolen}, and the air went tense, because {goal.risk}."
    )

    # Turn
    world.para()
    hero.memes["humor"] += 1.0
    world.say(
        f"Then {hero.id} chose a frank sort of trick: {goal.repeller_action}."
    )
    spy.memes["nervous"] += 1.0
    spy.meters["focus"] = 0.0
    if goal.weakness == "laughter":
        spy.memes["laughter"] = 1.0
    else:
        spy.memes["mocked"] = 1.0
    world.say(
        f"The joke landed squarely, and {goal.repeller_result}."
    )

    # Resolution
    world.para()
    treasure.meters["safe"] = 1.0
    spy.meters["distance"] = 2.0
    hero.memes["relief"] += 1.0
    hero.memes["trust"] += 0.5
    world.say(
        f"{spy.id} fled with an embarrassed hop, and {goal.stolen} stayed with the crew."
    )
    world.say(
        f"By the last gull cry, {hero.id} was laughing with the sailors, and the Black Gull "
        f"sailed on with a safer deck and a happier wind."
    )

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    goal = f["goal"]
    return [
        f'Write a short pirate tale for a child where a frank sailor named {hero.id} uses {goal.humor_style} to repel a spy.',
        f"Tell a funny sea story in which {hero.id} protects {goal.lure} from a spy and the trouble ends in laughter.",
        f'Write a pirate story that includes the word "{goal.keyword}" and ends with the crew feeling safer after a silly trick.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    spy = f["spy"]
    goal = f["goal"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who was the frank pirate who noticed the spy on {setting.place}?",
            answer=f"{hero.id} was the frank {hero.type} who noticed {spy.id} sneaking aboard {setting.place}.",
        ),
        QAItem(
            question=f"What did the spy want to steal in the story?",
            answer=f"The spy wanted to steal {goal.stolen}, which is why the deck felt tense.",
        ),
        QAItem(
            question=f"How did {hero.id} use humor to solve the problem?",
            answer=f"{hero.id} used {goal.humor_style} to make the spy laugh or flinch, and that repelled the spy before {goal.stolen} could be taken.",
        ),
        QAItem(
            question=f"What changed by the end of the pirate tale?",
            answer=f"By the end, {goal.stolen} stayed with the crew, the spy ran off embarrassed, and everyone felt lighter and safer.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    goal = f["goal"]
    out = [
        QAItem(
            question="What is a spy?",
            answer="A spy is someone who tries to learn secrets without being noticed.",
        ),
        QAItem(
            question="What does it mean to repel someone?",
            answer="To repel someone means to drive them away or stop them from coming closer.",
        ),
        QAItem(
            question="Why can humor help in a tense moment?",
            answer="Humor can make people laugh, lower the tension, and break a sneaky plan before it succeeds.",
        ),
    ]
    if goal.target == "map":
        out.append(QAItem(
            question="Why is a treasure map important on a pirate ship?",
            answer="A treasure map shows where to sail, so pirates can keep their course and find what they are searching for.",
        ))
    if goal.target == "compass":
        out.append(QAItem(
            question="What does a compass do on a ship?",
            answer="A compass helps sailors know which direction they are heading when the sea is wide and confusing.",
        ))
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the setting holds the treasure, the spy can reach it,
% and a humorous repeller exists for the spy's weakness.
valid_story(S, G) :- setting(S), goal(G), holds(S, T), target(G, T),
                      weakness(G, W), can_repel(G, W).

can_repel(G, laughter) :- repeller(G, R), humorous(R).
can_repel(G, mockery) :- repeller(G, R), humorous(R).

% The spy is actually a threat if the target can be reached.
threat(S, G) :- valid_story(S, G), reach(S, G).

% Show the compatible story pairs.
#show valid_story/2.
#show threat/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hold in sorted(s.holds):
            lines.append(asp.fact("holds", sid, hold))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("target", gid, g.target))
        lines.append(asp.fact("weakness", gid, g.weakness))
        lines.append(asp.fact("repeller", gid, g.repeller))
        lines.append(asp.fact("humorous", g.repeller))
        lines.append(asp.fact("reach", "deck", gid))
        lines.append(asp.fact("reach", "cabin", gid))
        lines.append(asp.fact("reach", "harbor", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(sid, gid) for sid, s in SETTINGS.items() for gid, g in GOALS.items() if story_is_valid(s, g)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} valid story pairs).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous pirate tale about a frank sailor repelling a spy.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["pirate", "sailor"])
    ap.add_argument("--spy")
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
    goal = args.goal or rng.choice(list(GOALS))
    g = GOALS[goal]
    if not story_is_valid(SETTINGS[setting], g):
        raise StoryError(explain_rejection(SETTINGS[setting], g))

    hero_name, hero_type, _ = rng.choice(HEROES)
    if args.hero:
        hero_name = args.hero
    if args.hero_type:
        hero_type = args.hero_type
    spy = args.spy or rng.choice(SPY_NAMES)
    return StoryParams(setting=setting, goal=goal, hero=hero_name, hero_type=hero_type, spy=spy)


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.guarded:
            bits.append("guarded=True")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
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
    StoryParams(setting="deck", goal="map", hero="Frank", hero_type="pirate", spy="Moth"),
    StoryParams(setting="cabin", goal="map", hero="Mara", hero_type="pirate", spy="Silk"),
    StoryParams(setting="harbor", goal="compass", hero="Jeb", hero_type="sailor", spy="Rook"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid()
        print(f"{len(combos)} valid story pairs:\n")
        for setting, goal in combos:
            print(f"  {setting:6} {goal}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.goal} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
