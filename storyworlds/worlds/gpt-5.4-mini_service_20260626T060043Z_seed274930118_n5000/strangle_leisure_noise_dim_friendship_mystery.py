#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/strangle_leisure_noise_dim_friendship_mystery.py
================================================================================================

A small mystery-style storyworld about friendship in a leisure setting, built
from the seed words:

- strangle
- leisure
- noise-dim

The world simulates a child-friendly mystery: two friends hear a muffled,
strangely strangled sound in a place for leisure, follow clues, and discover a
simple cause. The story state tracks physical measures (sound, light, clutter,
distance) and emotional measures (curiosity, worry, trust, relief), so the prose
is driven by the simulated world rather than a fixed template.

The scripted premise:
- A child and a friend are enjoying a quiet leisure activity.
- A dim, strangled sound appears and makes the scene feel mysterious.
- The friends investigate together, compare clues, and solve the puzzle.
- The ending proves what changed: the source is found, the mood lifts, and the
  friendship feels stronger.

The script follows the Storyweavers contract:
- StoryParams and standard CLI.
- World-driven prose and Q&A.
- Inline ASP_RULES twin with parity checking through --verify.
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

PLACES = {
    "leisure_center": {
        "label": "the leisure center",
        "kind": "indoor",
        "affords": {"game", "reading", "drawing"},
    },
    "arcade_corner": {
        "label": "the arcade corner",
        "kind": "indoor",
        "affords": {"game"},
    },
    "quiet_room": {
        "label": "the quiet room",
        "kind": "indoor",
        "affords": {"reading", "drawing"},
    },
    "garden_bench": {
        "label": "the garden bench",
        "kind": "outdoor",
        "affords": {"reading", "snack"},
    },
}

ACTIVITIES = {
    "game": {
        "verb": "play a board game",
        "gerund": "playing a board game",
        "keyword": "game",
        "tags": {"game", "fun"},
    },
    "reading": {
        "verb": "read a picture book",
        "gerund": "reading picture books",
        "keyword": "book",
        "tags": {"book", "quiet"},
    },
    "drawing": {
        "verb": "draw a treasure map",
        "gerund": "drawing treasure maps",
        "keyword": "map",
        "tags": {"map", "quiet"},
    },
    "snack": {
        "verb": "share a snack",
        "gerund": "sharing a snack",
        "keyword": "snack",
        "tags": {"snack", "calm"},
    },
}

CLUES = {
    "vent": {
        "label": "a vent",
        "sound": "a thin, strangled whisper of air",
        "source": "the vent cover",
        "reason": "a loose paper edge fluttering in the vent",
    },
    "toy": {
        "label": "a toy cart",
        "sound": "a tiny, noise-dim squeak",
        "source": "the toy cart wheel",
        "reason": "a little wheel caught on a rug thread",
    },
    "door": {
        "label": "a door",
        "sound": "a strangled creak",
        "source": "the door hinge",
        "reason": "a hinge that needed a drop of oil",
    },
    "box": {
        "label": "a music box",
        "sound": "a dim, faraway tinkle",
        "source": "the music box lid",
        "reason": "the lid was only half-open",
    },
}

FRIEND_NAMES = ["Mina", "Noah", "Lina", "Owen", "Zoe", "Theo", "Iris", "Finn"]
TRIAL_NAMES = ["Pip", "Milo", "June", "Nia", "Kai", "Rae", "Elsie", "Ben"]
TRAITS = ["curious", "kind", "careful", "brave", "gentle", "clever"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: dict
    activity: dict
    clue: dict
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str
    activity: str
    clue: str
    name: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A child-friendly mystery about friendship in a leisure place."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=TRAITS)
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


def _choose(rng: random.Random, seq: list[str]) -> str:
    return rng.choice(seq)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.place:
        if args.activity not in PLACES[args.place]["affords"]:
            raise StoryError(
                f"(No story: {PLACES[args.place]['label']} does not reasonably fit "
                f"{ACTIVITIES[args.activity]['gerund']}. Pick a place that supports it.)"
            )

    viable = []
    for p in PLACES:
        for a in PLACES[p]["affords"]:
            for c in CLUES:
                viable.append((p, a, c))

    viable = [
        combo for combo in viable
        if (args.place is None or combo[0] == args.place)
        and (args.activity is None or combo[1] == args.activity)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not viable:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, clue = rng.choice(sorted(viable))
    name = args.name or _choose(rng, FRIEND_NAMES)
    friend_name = args.friend_name or _choose(rng, [n for n in FRIEND_NAMES if n != name])
    trait = args.trait or _choose(rng, TRAITS)
    return StoryParams(place=place, activity=activity, clue=clue, name=name, friend_name=friend_name, trait=trait)


def _init_world(params: StoryParams) -> World:
    world = World(PLACES[params.place], ACTIVITIES[params.activity], CLUES[params.clue])
    hero = world.add(Entity(id=params.name, kind="character", type="child", meters={}, memes={}))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="child", meters={}, memes={}))
    mystery = world.add(Entity(
        id="mystery",
        kind="thing",
        type="mystery",
        label=CLUES[params.clue]["label"],
        phrase=CLUES[params.clue]["label"],
        meters={"sound": 0.0, "clue": 0.0},
        memes={},
    ))
    world.facts.update(hero=hero, friend=friend, mystery=mystery)
    return world


def _build_state(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    mystery = world.facts["mystery"]

    hero.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0
    hero.memes["trust"] = 1.0
    friend.memes["trust"] = 1.0

    world.say(
        f"{hero.id} and {friend.id} were enjoying some leisure time at {world.place['label']}."
    )
    world.say(
        f"They were {world.activity['gerund']} when {mystery.label} gave off {world.clue['sound']}."
    )
    world.say(
        f"The sound felt strange, as if it had been { 'strangled' if world.clue['sound'].startswith('a thin') else 'dimmed' } by the room itself."
    )
    world.para()

    hero.memes["curiosity"] = 1.0
    friend.memes["curiosity"] = 1.0
    hero.memes["worry"] = 1.0
    world.say(
        f"{hero.id} frowned and listened closely, while {friend.id} stayed beside {hero.id} like a good friend."
    )
    world.say(
        f"Together they followed the clue toward {world.clue['source']} and looked under the nearest thing."
    )

    mystery.meters["sound"] = 1.0
    mystery.meters["clue"] = 1.0
    world.para()

    world.say(
        f"They found the reason: {world.clue['reason']}."
    )
    world.say(
        f"{friend.id} fixed it at once, and the mystery stopped sounding so noise-dim."
    )

    hero.memes["relief"] = 1.0
    friend.memes["relief"] = 1.0
    hero.memes["trust"] = 2.0
    friend.memes["trust"] = 2.0
    hero.memes["worry"] = 0.0
    mystery.meters["sound"] = 0.0
    world.para()
    world.say(
        f"{hero.id} smiled at {friend.id}, and the two friends laughed because the big mystery had turned into a small fix."
    )
    world.say(
        f"By the end, {world.place['label']} felt calm again, and their friendship felt even stronger than before."
    )

    world.facts.update(
        solver=friend.id,
        sound_kind=world.clue["sound"],
        resolved=True,
        place_label=world.place["label"],
        activity_verb=world.activity["verb"],
        clue_label=world.clue["label"],
    )


def generate(params: StoryParams) -> StorySample:
    world = _init_world(params)
    _build_state(world)
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
        f'Write a short mystery story for a young child about friendship, leisure, and a "{world.clue["sound"]}" sound.',
        f"Tell a gentle story where {f['hero'].id} and {f['friend'].id} hear a strange sound at {world.place['label']} and solve it together.",
        f"Write a child-friendly mystery that uses the word 'strangled' in a safe, sound-related way and ends with friends smiling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        QAItem(
            question=f"Who were the story's two friends?",
            answer=f"The story was about {hero.id} and {friend.id}, who spent leisure time together and worked on the mystery as friends.",
        ),
        QAItem(
            question=f"What kind of sound did they hear at {world.place['label']}?",
            answer=f"They heard {world.clue['sound']}, which made the room feel quiet and mysterious.",
        ),
        QAItem(
            question=f"What solved the mystery in the end?",
            answer=f"The mystery was solved when they found {world.clue['reason']}. That small cause explained the strange sound right away.",
        ),
        QAItem(
            question=f"How did the friendship change by the end?",
            answer=f"At the end, {hero.id} and {friend.id} felt closer, calmer, and proud because they solved the mystery together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is leisure?",
            answer="Leisure means free time when someone can rest, play, read, or enjoy a calm activity.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story about a puzzling problem that people try to understand by looking for clues.",
        ),
        QAItem(
            question="Why can a sound seem dim or strangled?",
            answer="A sound can seem dim or strangled when something soft, narrow, or blocked makes it hard to hear clearly.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between people who help each other, listen, and spend time together.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="leisure_center", activity="game", clue="toy", name="Mina", friend_name="Noah", trait="curious"),
    StoryParams(place="quiet_room", activity="reading", clue="vent", name="Lina", friend_name="Theo", trait="kind"),
    StoryParams(place="arcade_corner", activity="game", clue="door", name="Pip", friend_name="June", trait="brave"),
    StoryParams(place="garden_bench", activity="snack", clue="box", name="Iris", friend_name="Finn", trait="clever"),
]


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- act(A).
clue(C) :- clue_kind(C).

valid(P,A,C) :- setting(P), act(A), clue_kind(C), affords(P,A).

friendship_story(P,A,C) :- valid(P,A,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(p["affords"]):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("act", aid))
    for cid in CLUES:
        lines.append(asp.fact("clue_kind", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show friendship_story/3."))
    return sorted(set(asp.atoms(model, "friendship_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p, pdata in PLACES.items():
        for a in pdata["affords"]:
            for c in CLUES:
                combos.append((p, a, c))
    return combos


def explain_rejection(place: str, activity: str) -> str:
    return (
        f"(No story: {PLACES[place]['label']} does not reasonably fit "
        f"{ACTIVITIES[activity]['gerund']}. Choose a place that affords that leisure activity.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.activity and args.activity not in PLACES[args.place]["affords"]:
        raise StoryError(explain_rejection(args.place, args.activity))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.clue is None or c[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, clue = rng.choice(sorted(combos))
    name = args.name or _choose(rng, FRIEND_NAMES)
    friend_name = args.friend_name or _choose(rng, [n for n in FRIEND_NAMES if n != name])
    trait = args.trait or _choose(rng, TRAITS)
    return StoryParams(place=place, activity=activity, clue=clue, name=name, friend_name=friend_name, trait=trait)


def _choose(rng: random.Random, seq: list[str]) -> str:
    return rng.choice(seq)


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
        print(asp_program("#show friendship_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, clue) combos:\n")
        for p, a, c in triples:
            print(f"  {p:15} {a:10} {c}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (clue: {p.clue})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
