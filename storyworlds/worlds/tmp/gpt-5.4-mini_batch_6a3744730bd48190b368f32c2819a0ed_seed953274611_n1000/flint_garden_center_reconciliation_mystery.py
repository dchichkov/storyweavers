#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flint_garden_center_reconciliation_mystery.py
==============================================================================

A small standalone story world for a child-sized mystery set in a garden center:
something goes missing, clues are followed through soil and shelves, and a
misunderstanding ends in reconciliation. The seed word is flint, and the story
keeps that word visible as a tiny, odd clue inside the mystery.

The world is built from typed entities with physical meters and emotional memes.
State changes drive the prose; the ending image proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    smell: str
    features: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    where: str
    oddity: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tension:
    id: str
    label: str
    cause: str
    remedy: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    tension: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    guide: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_missing(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["missing"] < THRESHOLD:
            continue
        sig = ("missing", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in world.entities.values():
            if ent.role in {"hero", "friend"}:
                ent.memes["worry"] += 1
        out.append("__missing__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    hero = next((e for e in world.entities.values() if e.role == "hero"), None)
    friend = next((e for e in world.entities.values() if e.role == "friend"), None)
    if not hero or not friend:
        return out
    if hero.memes["misunderstanding"] < THRESHOLD:
        return out
    if hero.memes["understanding"] < THRESHOLD or friend.memes["apology"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    hero.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("missing", _r_missing), Rule("reconcile", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(clue: Clue, tension: Tension) -> bool:
    return clue.id in {"flint", "tag", "label"} and tension.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES:
            for tension in TENSIONS:
                if reasonableness_gate(CLUES[clue], TENSIONS[tension]):
                    combos.append((place, clue, tension))
    return combos


def predict(world: World, clue_id: str) -> dict:
    sim = world.copy()
    sim.get(clue_id).meters["missing"] += 1
    propagate(sim, narrate=False)
    return {
        "missing": sim.get(clue_id).meters["missing"] >= THRESHOLD,
        "worry": sum(e.memes["worry"] for e in sim.entities.values()),
    }


def setup(world: World, place: Place, hero: Entity, friend: Entity) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"At the garden center, {hero.id} and {friend.id} wandered past wet pots, seed packets, and bright labels. "
        f"The air smelled of damp earth and basil."
    )
    world.say(
        f"They were looking for a small clue hidden somewhere among the shelves."
    )
    world.say(
        f"Near a tray of stones, a tiny {place.features} made the place feel like a puzzle."
    )


def discover(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["attention"] += 1
    world.say(
        f"{hero.id} spotted {clue.phrase} near {clue.where}. It looked ordinary at first, but {clue.oddity}."
    )
    world.say(f"The clue was a little strange, and the strange thing was the point.")


def accuse(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    hero.memes["misunderstanding"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f"{hero.id} frowned and thought {friend.id} had moved it on purpose. "
        f'"Why was {clue.label} over there?" {hero.id} asked.'
    )
    world.say(
        f"{friend.id} looked down, startled, because the question sounded like blame."
    )


def clue_turn(world: World, friend: Entity, guide: Entity, clue: Clue, tension: Tension) -> None:
    friend.memes["apology"] += 1
    friend.memes["understanding"] += 1
    world.say(
        f"{friend.id} pointed to a damp spill and then to {guide.label_word}. "
        f"It turned out {clue.label} had been knocked loose when someone watered the display."
    )
    world.say(
        f"{guide.label_word.capitalize()} smiled and explained the small accident, so the mystery stopped feeling like a trick."
    )
    if tension.id == "sigh":
        world.say(f"The odd little {clue.label} still felt important, but now it had a real reason to be there.")


def reconcile(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    hero.memes["understanding"] += 1
    hero.memes["apology"] += 1
    hero.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    world.say(
        f"{hero.id} blinked, then felt their cheeks go hot. They realized they had jumped to the wrong answer."
    )
    world.say(
        f'{hero.id} said sorry, and {friend.id} said sorry too for sounding sharp. '
        f"They bumped shoulders gently, and the tension between them melted away."
    )
    world.say(
        f"Together they put {clue.phrase} back where it belonged, right beside the flowers."
    )
    world.say(
        f"In the end, the garden center was just a garden center again: rows of green things, tidy shelves, and two friends walking out side by side."
    )


def tell(place: Place, clue: Clue, tension: Tension, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str, guide_name: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    guide = world.add(Entity(id=guide_name, kind="character", type="adult", role="guide", label="the garden guide"))
    clue_ent = world.add(Entity(id=clue.id, type="thing", label=clue.label, tags=set(clue.tags)))
    place_ent = world.add(Entity(id=place.id, type="place", label=place.label))
    place_ent.meters["stillness"] += 1

    setup(world, place, hero, friend)
    world.para()
    discover(world, hero, clue)
    accuse(world, hero, friend, clue)

    world.para()
    clue_ent.meters["missing"] += 1
    pred = predict(world, clue_ent.id)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"Something about the clue made the air feel wrong, like a shelf with one missing plant tag."
    )
    if pred["missing"]:
        world.say(
            f"The missing feeling spread, and both children grew uneasy."
        )
    propagate(world, narrate=False)

    world.para()
    clue_turn(world, friend, guide, clue, tension)
    reconcile(world, hero, friend, clue)

    world.facts.update(
        hero=hero, friend=friend, guide=guide, clue=clue, clue_ent=clue_ent,
        place=place, tension=tension, reconciled=True,
    )
    return world


PLACES = {
    "garden_center": Place(
        id="garden_center",
        label="the garden center",
        smell="damp earth and leaves",
        features="tiny flint-gray pebbles tucked by the pots",
        tags={"garden", "mystery"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the greenhouse",
        smell="warm soil and water",
        features="a row of foggy panes",
        tags={"garden", "mystery"},
    ),
}

CLUES = {
    "flint": Clue(
        id="flint",
        label="flint",
        phrase="a small piece of flint",
        where="the path by the fern table",
        oddity="it had no business being in a flower display",
        tags={"flint", "mystery"},
    ),
    "tag": Clue(
        id="tag",
        label="plant tag",
        phrase="a plant tag",
        where="the rosemary shelf",
        oddity="it had been turned face-down",
        tags={"tag", "mystery"},
    ),
    "marker": Clue(
        id="marker",
        label="marker cap",
        phrase="a marker cap",
        where="the potting bench",
        oddity="it was sticky with seed dust",
        tags={"mystery"},
    ),
}

TENSIONS = {
    "sigh": Tension(
        id="sigh",
        label="a misunderstanding",
        cause="jumping to the wrong answer",
        remedy="listening and apologizing",
        sense=3,
        power=2,
        tags={"reconciliation"},
    ),
    "silence": Tension(
        id="silence",
        label="a quiet hurt",
        cause="thinking a friend had broken trust",
        remedy="finding the real reason",
        sense=2,
        power=2,
        tags={"reconciliation"},
    ),
}

NAMES = ["Maya", "Nora", "Liam", "Theo", "Ava", "Ella", "Finn", "Leo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a 3-to-5-year-old set in a garden center that includes the word "{f["clue"].label}".',
        f"Tell a gentle mystery where {f['hero'].id} thinks {f['friend'].id} caused trouble, but the grown-up explanation leads to reconciliation.",
        f"Write a story about a strange little clue in a garden center, where two friends misunderstand each other and then make up.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, guide, clue, place = f["hero"], f["friend"], f["guide"], f["clue"], f["place"]
    return [
        ("Where does the story happen?",
         f"It happens at {place.label}, where shelves of plants, labels, and watering trays make the setting feel like a puzzle."),
        (f"What strange thing did {hero.id} find?",
         f"{hero.id} found {clue.phrase} near {clue.where}. It seemed odd because {clue.oddity}."),
        (f"Why did {hero.id} and {friend.id} feel upset at first?",
         f"{hero.id} thought {friend.id} had moved the clue on purpose, so the two friends got tense and hurt each other's feelings."),
        ("How did they solve the mystery?",
         f"{friend.id} and {guide.label_word} explained the real reason the clue was there, and then {hero.id} apologized. The misunderstanding ended once everyone knew it had been a small accident."),
        ("How did the story end?",
         f"{hero.id} and {friend.id} reconciled, put the clue back, and walked out side by side. The ending shows that the friendship mattered more than the mistake."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    f = world.facts
    tags = set(f["clue"].tags) | set(f["place"].tags) | set(f["tension"].tags)
    if "flint" in tags:
        out.append(("What is flint?",
                     "Flint is a hard stone. Long ago, people used it to make sparks, and it can also be used as a small clue in a mystery story."))
    out.append(("What is a garden center?",
                 "A garden center is a store where people buy plants, soil, pots, seeds, and tools for gardening."))
    out.append(("What does reconciliation mean?",
                 "Reconciliation means people were upset or apart for a while, and then they make up and feel friendly again."))
    out.append(("Why can a misunderstanding hurt feelings?",
                 "A misunderstanding can hurt feelings because someone may think a friend did something bad when that friend did not mean to cause trouble."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(clue: Clue, tension: Tension) -> str:
    if not reasonableness_gate(clue, tension):
        return "(No story: the chosen clue or tension does not support a child-sized mystery with reconciliation.)"
    return "(No story: invalid combination.)"


ASP_RULES = r"""
supported(C) :- clue(C), clue_topic(C, flint).
reasonable(T) :- tension(T), sense(T, S), sense_min(M), S >= M.
valid(P, C, T) :- place(P), clue(C), tension(T), supported(C), reasonable(T).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for t in clue.tags:
            lines.append(asp.fact("clue_topic", cid, t))
    for tid, tension in TENSIONS.items():
        lines.append(asp.fact("tension", tid))
        lines.append(asp.fact("sense", tid, tension.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, tension=None, hero=None, hero_gender=None, friend=None, friend_gender=None, guide=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Garden-center mystery storyworld with reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tension", choices=TENSIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", dest="hero_gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
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
    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice(list(CLUES))
    tension = args.tension or rng.choice(list(TENSIONS))
    if args.clue and args.tension and not reasonableness_gate(CLUES[args.clue], TENSIONS[args.tension]):
        raise StoryError(explain_rejection(CLUES[args.clue], TENSIONS[args.tension]))
    if not reasonableness_gate(CLUES[clue], TENSIONS[tension]):
        raise StoryError(explain_rejection(CLUES[clue], TENSIONS[tension]))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != hero])
    guide = args.guide or "Mrs. Green"
    return StoryParams(place=place, clue=clue, tension=tension, hero=hero, hero_gender=hero_gender, friend=friend, friend_gender=friend_gender, guide=guide)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.tension not in TENSIONS:
        raise StoryError("Invalid params.")
    world = tell(PLACES[params.place], CLUES[params.clue], TENSIONS[params.tension],
                 params.hero, params.hero_gender, params.friend, params.friend_gender, params.guide)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


CURATED = [
    StoryParams(place="garden_center", clue="flint", tension="sigh", hero="Maya", hero_gender="girl", friend="Liam", friend_gender="boy", guide="Mrs. Green"),
    StoryParams(place="greenhouse", clue="tag", tension="silence", hero="Ava", hero_gender="girl", friend="Nora", friend_gender="girl", guide="Mr. Reed"),
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
