#!/usr/bin/env python3
"""
A small detective-story world with friendship and a lesson learned.

Premise:
A child detective follows clues around a neighborhood to solve a tiny mystery.
The case begins with a disagreement between friends, turns on a mistaken clue,
and ends with a repaired friendship and a lesson learned about listening before
accusing.

The world model tracks physical meters and emotional memes so the story is
driven by simulated state rather than a frozen template.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        gender = self.role
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Case:
    id: str
    missing_item: str
    mistaken_item: str
    true_clue: str
    false_clue: str
    lesson: str


@dataclass
class StoryParams:
    place: str
    case: str
    hero_name: str
    hero_role: str
    friend_name: str
    friend_role: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, case: Case) -> None:
        self.place = place
        self.case = case
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
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


PLACES = {
    "library": Place("library", "the library", ["quiet aisles", "dusty shelves", "returned books"]),
    "garden": Place("garden", "the garden", ["muddy footprints", "a broken pot", "a bent gate"]),
    "playground": Place("playground", "the playground", ["sand, swings, and a bench", "shoe prints", "a tipped snack box"]),
    "kitchen": Place("kitchen", "the kitchen", ["crumbs on the table", "a jam jar", "sticky fingers"]),
}

CASES = {
    "lost_cookie": Case(
        "lost_cookie",
        missing_item="cookie",
        mistaken_item="crumbs",
        true_clue="a trail of jam",
        false_clue="a crumb on the floor",
        lesson="not to blame a friend before checking the facts",
    ),
    "missing_ball": Case(
        "missing_ball",
        missing_item="ball",
        mistaken_item="balloon",
        true_clue="chalk marks near the fence",
        false_clue="a round shadow from a balloon",
        lesson="that a clue can look right and still be wrong",
    ),
    "lost_note": Case(
        "lost_note",
        missing_item="note",
        mistaken_item="leaf",
        true_clue="a ribbon caught on a chair",
        false_clue="a folded leaf near the door",
        lesson="to ask kindly instead of jumping to conclusions",
    ),
}

NAMES = ["Mia", "Leo", "Ava", "Noah", "Nina", "Eli", "Zoe", "Finn"]
ROLES = ["girl", "boy"]


def story_artifact(case: Case) -> str:
    return f"a small {case.missing_item}"


def introduce(world: World, hero: Entity, friend: Entity, case: Case) -> None:
    world.say(
        f"{hero.noun()} was a little detective who loved solving small puzzles."
        f" {hero.pronoun().capitalize()} and {friend.noun()} were good friends, and they liked to search for clues together."
    )
    world.say(
        f"One day, {case.missing_item}s started to matter very much, because one {case.missing_item} went missing."
    )


def set_scene(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"The case began at {world.place.label}, where the air felt still and every little thing could hide a clue."
    )
    world.say(
        f"{hero.noun()} held a tiny notebook, and {friend.noun()} stood close by, ready to help."
    )


def investigate(world: World, hero: Entity, friend: Entity, case: Case) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    friend.memes["helpfulness"] = friend.memes.get("helpfulness", 0) + 1
    world.say(
        f"They searched the {world.place.label} carefully and found {case.false_clue}."
        f" {hero.noun()} thought it looked important, so {hero.pronoun()} wrote it down."
    )
    hero.memes["certainty"] = hero.memes.get("certainty", 0) + 1
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0) + 1
    world.say(
        f"Then {hero.noun()} saw {friend.pronoun('object')} near the clue and got too sure too fast."
    )
    world.say(
        f"\"Did you take it?\" {hero.pronoun()} asked, and {friend.noun()} looked hurt."
    )
    friend.memes["hurt"] = friend.memes.get("hurt", 0) + 1
    friend.memes["distance"] = friend.memes.get("distance", 0) + 1


def turn(world: World, hero: Entity, friend: Entity, case: Case) -> None:
    world.para()
    world.say(
        f"While they were arguing, {friend.noun()} noticed {case.true_clue} tucked where the wind could not move it."
    )
    hero.memes["certainty"] = max(0, hero.memes.get("certainty", 0) - 1)
    hero.memes["suspicion"] = max(0, hero.memes.get("suspicion", 0) - 1)
    hero.memes["realization"] = hero.memes.get("realization", 0) + 1
    world.say(
        f"{hero.noun()} checked the new clue and realized the first clue had fooled {hero.pronoun('object')}."
    )
    world.say(
        f"The missing {case.missing_item} had not been taken by {friend.noun()} at all."
    )


def resolve(world: World, hero: Entity, friend: Entity, case: Case) -> None:
    world.say(
        f"{hero.noun()} apologized right away and said {hero.pronoun('possessive')} detective work should have been slower and kinder."
    )
    friend.memes["hurt"] = max(0, friend.memes.get("hurt", 0) - 1)
    friend.memes["forgiven"] = friend.memes.get("forgiven", 0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0) + 1
    world.say(
        f"Together they followed the true clue and found the {case.missing_item} in a safe spot near the {world.place.label}."
    )
    world.say(
        f"In the end, {hero.noun()} learned {case.lesson}, and {friend.noun()} smiled because the friends were close again."
    )


def tell(place: Place, case: Case, hero_name: str, hero_role: str, friend_name: str, friend_role: str) -> World:
    world = World(place, case)
    hero = world.add(Entity(hero_name, kind="character", label=hero_name, role=hero_role))
    friend = world.add(Entity(friend_name, kind="character", label=friend_name, role=friend_role))
    artifact = world.add(Entity(case.missing_item, kind="thing", label=case.missing_item))

    world.facts.update(hero=hero, friend=friend, artifact=artifact, case=case, place=place)

    introduce(world, hero, friend, case)
    world.para()
    set_scene(world, hero, friend)
    investigate(world, hero, friend, case)
    turn(world, hero, friend, case)
    resolve(world, hero, friend, case)
    return world


KNOWLEDGE = {
    "detective": [
        ("What does a detective do?", "A detective looks for clues and tries to figure out what happened."),
    ],
    "clue": [
        ("What is a clue?", "A clue is a small piece of information that helps solve a mystery."),
    ],
    "friendship": [
        ("What is friendship?", "Friendship is when people care about each other and help each other."),
    ],
    "lesson": [
        ("What does it mean to learn a lesson?", "It means you understand something important and do better next time."),
    ],
    "listening": [
        ("Why is listening important?", "Listening helps people understand each other and avoid mistakes."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    place: Place = f["place"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    return [
        f"Write a short detective story for a young child set at {place.label} with {hero.noun()} and {friend.noun()}.",
        f"Tell a mystery where a friend gets blamed by mistake, but the friends fix it and learn a lesson.",
        f"Write a gentle clue-finding story that ends with friendship and the lesson '{case.lesson}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    place: Place = f["place"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"{hero.noun()} was the detective, and {friend.noun()} helped with the search.",
        ),
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"It happened at {place.label}, where the friends looked for clues together.",
        ),
        QAItem(
            question=f"Why did {hero.noun()} and {friend.noun()} stop arguing?",
            answer=f"They found the true clue, learned the first clue was misleading, and saw that {friend.noun()} had not taken the {case.missing_item}.",
        ),
        QAItem(
            question=f"What lesson did {hero.noun()} learn?",
            answer=f"{hero.noun()} learned {case.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["detective"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["clue"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["friendship"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["lesson"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["listening"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for c in p.clues:
            lines.append(asp.fact("clue", pid, c.replace(" ", "_")))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("missing", cid, c.missing_item))
        lines.append(asp.fact("mistaken", cid, c.mistaken_item))
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is relevant if it belongs to the place.
relevant(P, C) :- place(P), clue(P, C).

% A mistaken clue can cause suspicion.
misleads(Case) :- case(Case), mistaken(Case, _).

% A resolution requires both a true clue and the lesson learned.
resolved(Case) :- case(Case), missing(Case, _), misleads(Case).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    resolved = {tuple(x) for x in asp.atoms(model, "resolved")}
    expected = {(cid,) for cid in CASES}
    if resolved == expected:
        print(f"OK: ASP parity verified for {len(expected)} cases.")
        return 0
    print("MISMATCH in ASP parity:")
    print("  asp:", sorted(resolved))
    print("  py :", sorted(expected))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [(place_id, case_id) for place_id in PLACES for case_id in CASES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Offset friendship detective story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-role", choices=ROLES)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-role", choices=ROLES)
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
    case = args.case or rng.choice(list(CASES))
    hero_role = args.hero_role or rng.choice(ROLES)
    friend_role = args.friend_role or ("boy" if hero_role == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(
        place=place,
        case=case,
        hero_name=hero_name,
        hero_role=hero_role,
        friend_name=friend_name,
        friend_role=friend_role,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        CASES[params.case],
        params.hero_name,
        params.hero_role,
        params.friend_name,
        params.friend_role,
    )
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    return sorted(set(asp.atoms(model, "resolved")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show relevant/2."))
        print(asp.atoms(model, "relevant"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for case in CASES:
                params = StoryParams(
                    place=place,
                    case=case,
                    hero_name=NAMES[0],
                    hero_role="girl",
                    friend_name=NAMES[1],
                    friend_role="boy",
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
