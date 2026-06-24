#!/usr/bin/env python3
"""
Storyworld: ghost-story reconciliation with curiosity and a ratio clue.

A small simulated domain:
- A child hears a soft ghostly rattle in an old room.
- Curiosity pulls the child toward the mystery.
- The ghost is lonely and a little frightened of being forgotten.
- A careful revelation of a ratio clue helps them find the lost keepsake.
- Reconciliation turns the room from chilly and tense into warm and calm.

The story is driven by world state:
- physical meters: chill, dust, glow, sound, wear, foundness
- emotional memes: curiosity, fear, loneliness, trust, relief, reconciliation

The "ratio" seed word appears as a concrete clue in the world:
- the child notices a ratio of candles to footsteps / clues to doors,
  and that clue becomes part of the resolution.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    adjective: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    clue: str
    weather: str = ""


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    location: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    weather: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "attic": Setting(place="the attic", adjective="dusty", affords={"search", "listen"}),
    "library": Setting(place="the old library", adjective="quiet", affords={"read", "search"}),
    "garden_shed": Setting(place="the garden shed", adjective="damp", affords={"search", "listen"}),
}

ACTIVITIES = {
    "search": Activity(
        id="search",
        verb="search for the lost thing",
        gerund="searching for the lost thing",
        rush="rush toward the dark corner",
        clue="ratio",
        weather="foggy",
    ),
    "listen": Activity(
        id="listen",
        verb="listen for the ghost",
        gerund="listening for the ghost",
        rush="tiptoe toward the sound",
        clue="whisper",
        weather="night",
    ),
    "read": Activity(
        id="read",
        verb="read the old labels",
        gerund="reading the old labels",
        rush="hurry to the lamp",
        clue="ratio",
        weather="rainy",
    ),
}

RELICS = {
    "photo": Keepsake(id="photo", label="photo", phrase="an old family photo", location="bookshelf"),
    "bell": Keepsake(id="bell", label="bell", phrase="a little silver bell", location="beam"),
    "scarf": Keepsake(id="scarf", label="scarf", phrase="a blue wool scarf", location="chest"),
}

NAMES = ["Maya", "Leo", "Nora", "Finn", "Ivy", "Owen"]
TRAITS = ["curious", "gentle", "brave", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    relic: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the setting supports the activity and the relic fits
% the place well enough to be found there.
valid_story(P, A, R) :- setting(P), activity(A), relic(R),
                        affords(P, A), found_in(R, P), can_reconcile(A, R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("found_in", rid, next(k for k, v in SETTINGS.items() if v.place == SETTINGS[next(iter(SETTINGS))].place if False else True)))
    # Replace the above with explicit mapping below; kept separate for clarity.
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    found_map = {"photo": "attic", "bell": "library", "scarf": "garden_shed"}
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("found_in", rid, found_map[rid]))
    lines.append(asp.fact("can_reconcile", "search", "photo"))
    lines.append(asp.fact("can_reconcile", "listen", "bell"))
    lines.append(asp.fact("can_reconcile", "read", "scarf"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def score_ratio(world: World) -> str:
    candles = int(world.facts.get("candles", 0))
    clues = int(world.facts.get("clues", 0))
    return f"{candles}:{clues}"


def predict_reveal(world: World, activity: Activity, relic: Keepsake) -> dict:
    sim = world.copy()
    sim.facts["candles"] = 2
    sim.facts["clues"] = 1 if activity.id in {"search", "read"} else 0
    found = relic.location in {"bookshelf", "beam", "chest"}
    return {"found": found, "ratio": score_ratio(sim)}


def introduce(world: World, child: Entity, trait: str) -> None:
    world.say(f"{child.id} was a {trait} child who liked quiet places and tiny mysteries.")


def haunt(world: World, ghost: Entity) -> None:
    ghost.meters["chill"] += 1
    ghost.memes["loneliness"] += 1
    world.say(f"At {world.setting.place}, a soft ghost drifted by, and the air felt chilly.")


def curiosity(world: World, child: Entity, activity: Activity) -> None:
    child.memes["curiosity"] += 1
    world.say(f"{child.id} wanted to {activity.verb}, because the sound felt like a clue.")


def warning(world: World, ghost: Entity, child: Entity, relic: Keepsake, activity: Activity) -> None:
    ghost.memes["fear"] += 1
    world.say(
        f"The ghost whispered that {relic.phrase} was missing, and the room seemed even colder."
    )
    world.say(
        f"{child.id} noticed a strange ratio: two candles near the lamp, but only one clear clue."
    )


def search_state(world: World, child: Entity, activity: Activity, relic: Keepsake) -> None:
    child.meters["care"] += 1
    world.facts["candles"] = 2
    world.facts["clues"] = 1
    world.say(
        f"{child.id} followed the clue slowly, using the ratio of candles to clues to keep calm."
    )
    world.say(f"{child.id} {activity.rush}, and {child.pronoun('possessive')} shoes barely made a sound.")


def reveal(world: World, child: Entity, ghost: Entity, relic: Keepsake) -> None:
    child.meters["foundness"] += 1
    ghost.memes["hope"] += 1
    world.say(
        f"Behind a stack of boxes, {child.id} found {relic.phrase}. The ghost trembled with hope."
    )


def reconcile(world: World, child: Entity, ghost: Entity, relic: Keepsake) -> None:
    child.memes["trust"] += 1
    ghost.memes["trust"] += 1
    child.memes["reconciliation"] += 1
    ghost.memes["reconciliation"] += 1
    ghost.memes["loneliness"] = 0
    world.say(
        f"{child.id} held up {relic.phrase} and smiled. The ghost smiled back, no longer lonely."
    )
    world.say(
        f"They thanked each other, and the chilly room grew warm enough to feel like a home again."
    )


def tell(setting: Setting, activity: Activity, relic: Keepsake, name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child"))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost"))

    world.weather = activity.weather
    world.facts["activity"] = activity
    world.facts["relic"] = relic
    world.facts["setting"] = setting

    introduce(world, child, trait)
    haunt(world, ghost)
    world.para()
    curiosity(world, child, activity)
    warning(world, ghost, child, relic, activity)
    search_state(world, child, activity, relic)
    reveal(world, child, ghost, relic)
    world.para()
    reconcile(world, child, ghost, relic)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Question / answer generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    activity: Activity = f["activity"]
    relic: Keepsake = f["relic"]
    setting: Setting = f["setting"]
    return [
        f'Write a gentle ghost story for young children that includes the word "{activity.clue}" and a helpful ratio clue.',
        f"Tell a story in {setting.place} where a curious child follows a small mystery and helps a lonely ghost find {relic.phrase}.",
        f"Write a short story about curiosity, a ghost, and reconciliation, with the ratio of candles to clues helping the ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    activity: Activity = f["activity"]
    relic: Keepsake = f["relic"]
    child: Entity = world.get(next(eid for eid, e in world.entities.items() if e.type == "child"))
    ghost: Entity = world.get("Ghost")
    return [
        QAItem(
            question=f"Why did {child.id} go exploring in {world.setting.place}?",
            answer=f"{child.id} went exploring because {child.pronoun('subject')} was curious and wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"What clue helped {child.id} keep calm while looking for {relic.label}?",
            answer=f"{child.id} noticed a ratio of two candles to one clue, and that little pattern helped {child.pronoun('object')} stay calm.",
        ),
        QAItem(
            question=f"How did the ghost feel before the {relic.label} was found?",
            answer=f"The ghost felt lonely and a little afraid because {relic.phrase} was missing.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{child.id} found {relic.phrase}, and the ghost and child reconciled so the room felt warm instead of chilly.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is curiosity?",
        answer="Curiosity is the feeling that makes you want to look, ask, and learn about something new.",
    ),
    QAItem(
        question="What is a ratio?",
        answer="A ratio is a way to compare how many of one thing there are with how many of another thing there are.",
    ),
    QAItem(
        question="Why can a ghost story be gentle?",
        answer="A ghost story can be gentle when the ghost is more lonely than scary and the ending is kind.",
    ),
    QAItem(
        question="What is reconciliation?",
        answer="Reconciliation is when people who felt upset make peace again and feel okay with each other.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with curiosity and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--relic", choices=RELICS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    found_map = {"photo": "attic", "bell": "library", "scarf": "garden_shed"}
    for place in SETTINGS:
        for activity in ACTIVITIES:
            for relic in RELICS:
                if SETTINGS[place].affords and activity in SETTINGS[place].affords and found_map[relic] == place:
                    combos.append((place, activity, relic))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if args.place is None or c[0] == args.place
              if False else True]
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")
    place, activity, relic = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, relic=relic, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], RELICS[params.relic], params.name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def asp_verify() -> int:
    import storyworlds.asp as asp
    clingo_set = set(asp_valid_stories())
    python_set = set()
    found_map = {"photo": "attic", "bell": "library", "scarf": "garden_shed"}
    for p, a, r in valid_combos():
        python_set.add((p, a, r))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        items = asp_valid_stories()
        print(f"{len(items)} compatible (place, activity, relic) combos:\n")
        for place, activity, relic in items:
            print(f"  {place:12} {activity:8} {relic:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p, a, r in valid_combos():
            params = StoryParams(place=p, activity=a, relic=r, name=NAMES[0], trait=TRAITS[0])
            samples.append(generate(params))
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
