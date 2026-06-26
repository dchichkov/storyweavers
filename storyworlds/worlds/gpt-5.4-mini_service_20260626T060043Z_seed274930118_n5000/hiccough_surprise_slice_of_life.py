#!/usr/bin/env python3
"""
A small slice-of-life story world built around a hiccough surprise.

Premise:
- A child is having an ordinary day at home or at a small nearby place.
- A tiny hiccough keeps interrupting what they are doing.
- A gentle surprise gives everyone a practical way to help.
- The story ends with the hiccough easing and the room feeling calmer.

This world is intentionally compact and constraint-checked: the surprise must be
reasonable for the current setting and must plausibly help with the hiccough.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoor: bool
    affords: set[str] = field(default_factory=set)
    quiet: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    small_sound: str
    focus: str
    can_trigger: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    verb: str
    effect: str
    helps: set[str] = field(default_factory=set)
    places: set[str] = field(default_factory=set)
    mood_shift: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    activity: str
    surprise: str
    child_name: str
    child_gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", True, {"snack", "tea", "cookies"}, quiet=True),
    "living_room": Place("living_room", "the living room", True, {"story", "puzzle", "snack"}),
    "porch": Place("porch", "the porch", False, {"birdwatch", "bubbles", "snack"}),
    "garden": Place("garden", "the garden", False, {"watering", "snack", "flowers"}),
}

ACTIVITIES = {
    "snack": Activity("snack", "eat a snack", "eating a snack", "tiny crunches", "small bites", {"crumbs"}),
    "tea": Activity("tea", "sip warm tea", "sipping warm tea", "soft slurps", "warm cup", {"warmth"}),
    "story": Activity("story", "look at a storybook", "looking at a storybook", "page flutters", "pictures", set()),
    "puzzle": Activity("puzzle", "finish a puzzle", "finishing a puzzle", "cardboard clicks", "pieces", set()),
    "bubbles": Activity("bubbles", "blow bubbles", "blowing bubbles", "little pops", "soap wand", set()),
    "watering": Activity("watering", "water the plants", "watering the plants", "water drips", "plants", set()),
}

SURPRISES = {
    "note": Surprise(
        "note",
        "a folded note",
        "a folded note under the cup",
        "unfold",
        "a kind message from the companion",
        helps={"comfort", "slow_down"},
        places={"kitchen", "living_room", "porch", "garden"},
        mood_shift="smile",
    ),
    "song": Surprise(
        "song",
        "a little song",
        "a little song hummed by the companion",
        "hum",
        "a slow, friendly rhythm",
        helps={"breath", "comfort"},
        places={"kitchen", "living_room", "porch", "garden"},
        mood_shift="soften",
    ),
    "biscuit": Surprise(
        "biscuit",
        "a cinnamon biscuit",
        "a cinnamon biscuit on a small plate",
        "offer",
        "a cozy treat shared at the table",
        helps={"comfort", "slow_down"},
        places={"kitchen", "living_room"},
        mood_shift="brighten",
    ),
    "sticker": Surprise(
        "sticker",
        "a shiny sticker",
        "a shiny sticker from a pocket",
        "show",
        "a tiny prize that made the child grin",
        helps={"comfort"},
        places={"living_room", "porch", "garden"},
        mood_shift="cheer",
    ),
}

GIRL_NAMES = ["Maya", "Lena", "Ivy", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Max", "Leo"]
TRAITS = ["thoughtful", "curious", "gentle", "bright", "restless", "cheerful"]


def reasonableness_gate(place: Place, activity: Activity, surprise: Surprise) -> bool:
    return activity.id in place.affords and place.id in surprise.places and (
        ("tea" == activity.id and "comfort" in surprise.helps)
        or ("snack" == activity.id and "slow_down" in surprise.helps)
        or activity.id in {"story", "puzzle", "bubbles", "watering"} and "comfort" in surprise.helps
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for aid, activity in ACTIVITIES.items():
            for sid, surprise in SURPRISES.items():
                if reasonableness_gate(place, activity, surprise):
                    out.append((pid, aid, sid))
    return out


def _do_activity(world: World, child: Entity, activity: Activity) -> None:
    child.memes["busy"] = child.meme("busy") + 1
    child.meters["ordinary"] = child.meter("ordinary") + 1
    if activity.id == "snack":
        child.meters["crumbs"] = child.meter("crumbs") + 1
    if activity.id == "tea":
        child.meters["warm"] = child.meter("warm") + 1
    if activity.id == "watering":
        child.meters["wet"] = child.meter("wet") + 1
    if activity.id == "puzzle":
        child.meters["focus"] = child.meter("focus") + 1


def predict_hiccough(world: World, child: Entity, activity: Activity, surprise: Surprise) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(child.id), activity)
    sim.get(child.id).memes["hiccough"] = sim.get(child.id).meme("hiccough") + 1
    helped = surprise.effect in {"slow", "gentle", "warm", "soft"} or "comfort" in surprise.helps
    return {"helps": helped, "mood": sim.get(child.id).meme("mood")}


def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "ordinary")
    world.say(f"{child.id} was a little {trait} {child.type} who liked ordinary days.")


def setup_activity(world: World, child: Entity, companion: Entity, activity: Activity) -> None:
    world.say(
        f"Most mornings, {child.id} and {companion.label} spent time together in {world.place.label}."
    )
    world.say(
        f"{child.pronoun().capitalize()} liked {activity.gerund}, because it made the day feel calm and familiar."
    )


def hiccough_event(world: World, child: Entity, activity: Activity) -> None:
    child.memes["hiccough"] = child.meme("hiccough") + 1
    child.memes["surprise"] = child.meme("surprise") + 1
    world.say(f"Then came a hiccough, small but sudden, right in the middle of {activity.focus}.")
    world.say(f"{child.id} blinked and laughed a little at the tiny noise.")


def surprise_offer(world: World, companion: Entity, child: Entity, surprise: Surprise, activity: Activity) -> None:
    world.say(
        f"{companion.label} had a surprise: {surprise.phrase}. "
        f"{companion.pronoun().capitalize()} {surprise.verb} it with a grin."
    )
    world.say(
        f"It was not a grand surprise, just a gentle one that fit the moment."
    )


def accept_help(world: World, child: Entity, companion: Entity, surprise: Surprise) -> None:
    child.memes["mood"] = child.meme("mood") + 1
    child.memes["comfort"] = child.meme("comfort") + 1
    child.memes["hiccough"] = 0.0
    world.say(f"{child.id} took a slow breath, and the hiccough began to settle.")
    world.say(
        f"{child.id} smiled at {companion.label}, and the surprise made the whole room feel softer."
    )


def conclude(world: World, child: Entity, activity: Activity) -> None:
    ending = {
        "snack": f"At the end, {child.id} kept eating the snack without another hiccough, and the table stayed neat enough.",
        "tea": f"At the end, {child.id} sipped the warm tea calmly, and the cup felt like a small comfort in the quiet room.",
        "story": f"At the end, {child.id} turned one more page, and the book seemed to wait patiently for the next day.",
        "puzzle": f"At the end, {child.id} found the last piece, and the finished picture looked extra nice beside the surprise.",
        "bubbles": f"At the end, {child.id} blew one last bubble, and it drifted away like a tiny silver moon.",
        "watering": f"At the end, {child.id} watered the last pot, and the garden looked bright and freshly washed.",
    }[activity.id]
    world.say(ending)


def tell(place: Place, activity: Activity, surprise: Surprise,
         child_name: str = "Mina", child_type: str = "girl",
         companion_label: str = "the companion", trait: str = "thoughtful") -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        traits=["little", trait],
    ))
    companion = world.add(Entity(
        id="Companion",
        kind="character",
        type="adult",
        label=companion_label,
    ))
    surprise_ent = world.add(Entity(
        id=surprise.id,
        type="thing",
        label=surprise.label,
        phrase=surprise.phrase,
        owner=companion.id,
    ))

    introduce(world, child)
    setup_activity(world, child, companion, activity)
    world.para()
    _do_activity(world, child, activity)
    hiccough_event(world, child, activity)
    surprise_offer(world, companion, child, surprise, activity)
    world.para()
    if predict_hiccough(world, child, activity, surprise)["helps"]:
        accept_help(world, child, companion, surprise)
        conclude(world, child, activity)
    else:
        raise StoryError("The chosen surprise does not reasonably help with the hiccough.")
    world.facts.update(
        child=child,
        companion=companion,
        activity=activity,
        surprise=surprise_ent,
        place=place,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    surprise = f["surprise"]
    return [
        f'Write a short slice-of-life story for a young child that includes the word "hiccough".',
        f"Tell a gentle story where {child.id} is doing {activity.gerund} and a small surprise helps with a hiccough.",
        f'Write a cozy everyday story with a surprise {surprise.label} that makes a hiccough easier to manage.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    companion = f["companion"]
    activity = f["activity"]
    surprise = f["surprise"]
    return [
        QAItem(
            question=f"What was {child.id} doing before the hiccough showed up?",
            answer=f"{child.id} was {activity.gerund}, which was the ordinary part of the morning before the hiccough interrupted it.",
        ),
        QAItem(
            question=f"Who brought the surprise in the story?",
            answer=f"{companion.label} brought the surprise, and it was {surprise.phrase}.",
        ),
        QAItem(
            question=f"How did the surprise help {child.id}?",
            answer=f"The surprise helped {child.id} slow down and feel comfortable again, so the hiccough could settle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hiccough?",
            answer="A hiccough is a sudden little sound or movement that can pop out when someone is eating, laughing, or breathing oddly.",
        ),
        QAItem(
            question="Why can a gentle surprise feel nice?",
            answer="A gentle surprise can feel nice because it is kind, small, and friendly instead of loud or scary.",
        ),
        QAItem(
            question="What makes a slice-of-life story feel cozy?",
            answer="A slice-of-life story feels cozy when it focuses on ordinary moments, simple feelings, and small changes that make the day better.",
        ),
    ]


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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="tea", surprise="note", child_name="Mina", child_gender="girl", companion="mother", trait="thoughtful"),
    StoryParams(place="living_room", activity="story", surprise="song", child_name="Owen", child_gender="boy", companion="father", trait="curious"),
    StoryParams(place="porch", activity="bubbles", surprise="sticker", child_name="Ivy", child_gender="girl", companion="grandparent", trait="cheerful"),
    StoryParams(place="garden", activity="watering", surprise="note", child_name="Leo", child_gender="boy", companion="mother", trait="gentle"),
]


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- act(A).
surprise(S) :- gift(S).

combo(P,A,S) :- setting(P), act(A), gift(S), affords(P,A), fits(P,S), helps(S,A).

% A surprise fits when it can happen in the place and it helps the activity.
fits(P,S) :- place_surprise(P,S).
helps(S,A) :- aid(S,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        if p.quiet:
            lines.append(asp.fact("quiet", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
        for s in sorted(SURPRISES):
            if pid in SURPRISES[s].places:
                lines.append(asp.fact("place_surprise", pid, s))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("act", aid))
        for c in sorted(a.can_trigger):
            lines.append(asp.fact("can_trigger", aid, c))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("gift", sid))
        for h in sorted(s.helps):
            lines.append(asp.fact("aid", sid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with a hiccough surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, surprise = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(["mother", "father", "grandparent"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, surprise=surprise, child_name=name, child_gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIVITIES[params.activity], SURPRISES[params.surprise],
                 params.child_name, params.child_gender, params.companion, params.trait)
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
        print(asp_program("#show combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, surprise) combos:\n")
        for c in combos:
            print("  ", c)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.activity} at {p.place} (surprise: {p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
