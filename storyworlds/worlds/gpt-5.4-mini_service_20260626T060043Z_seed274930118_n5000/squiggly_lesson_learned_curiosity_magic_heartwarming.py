#!/usr/bin/env python3
"""
A small heartwarming storyworld about curiosity, a squiggly magic trail, and a
lesson learned.

Premise:
- A child notices a squiggly magical trail in a cozy setting.
- Curiosity pulls the child toward a small mystery.
- A gentle helper or magic object turns the mystery into a kind act.
- The child learns that careful looking and respectful asking lead to a happy fix.

The simulated world tracks both physical meters and emotional memes so the
story text is driven by state changes rather than a frozen template.
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
# Domain registries
# ---------------------------------------------------------------------------

PLACES = {
    "garden": {
        "label": "the garden",
        "cozy": True,
        "features": {"path", "bench", "flowers"},
    },
    "library": {
        "label": "the little library",
        "cozy": True,
        "features": {"shelves", "table", "lamp"},
    },
    "kitchen": {
        "label": "the sunny kitchen",
        "cozy": True,
        "features": {"table", "window", "jar"},
    },
    "yard": {
        "label": "the backyard",
        "cozy": False,
        "features": {"grass", "fence", "stone"},
    },
}

MAGICS = {
    "glow": {
        "label": "a warm glow",
        "effect": "glowed softly",
        "gift": "a tiny lantern",
        "lesson": "small lights can guide the way",
    },
    "bloom": {
        "label": "a blooming spell",
        "effect": "opened into bright flowers",
        "gift": "a sprig of seeds",
        "lesson": "gentle care helps things grow",
    },
    "sparkle": {
        "label": "a sparkle charm",
        "effect": "sparkled like starlight",
        "gift": "a little silver key",
        "lesson": "careful looking can reveal a hidden clue",
    },
}

LESSONS = {
    "listen": "asking kindly can help when something is puzzling",
    "share": "sharing a good idea can make a problem smaller",
    "care": "being gentle with small things helps everyone feel safe",
}

# ---------------------------------------------------------------------------
# Shared entities
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    with_actor: Optional[str] = None
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
    place: str
    magic: str
    lesson: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    magic: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    lesson: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate / story logic
# ---------------------------------------------------------------------------

def choose_premise(place: str, magic: str, lesson: str) -> None:
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")
    if magic not in MAGICS:
        raise StoryError(f"Unknown magic: {magic}")
    if lesson not in LESSONS:
        raise StoryError(f"Unknown lesson: {lesson}")


def valid_combo(place: str, magic: str, lesson: str) -> bool:
    # Heartwarming constraint: cozy settings are preferred for this world.
    return PLACES[place]["cozy"] and magic in MAGICS and lesson in LESSONS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for m in MAGICS:
            for l in LESSONS:
                if valid_combo(p, m, l):
                    combos.append((p, m, l))
    return combos


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_fact(P).
magic(M) :- magic_fact(M).
lesson(L) :- lesson_fact(L).

cozy(P) :- cozy_fact(P).
valid(P,M,L) :- place(P), magic(M), lesson(L), cozy(P).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p, data in PLACES.items():
        lines.append(asp.fact("place_fact", p))
        if data["cozy"]:
            lines.append(asp.fact("cozy_fact", p))
    for m in MAGICS:
        lines.append(asp.fact("magic_fact", m))
    for l in LESSONS:
        lines.append(asp.fact("lesson_fact", l))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - asp_set:
        print(" only in python:", sorted(py - asp_set))
    if asp_set - py:
        print(" only in asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def name_for(type_: str, rng: random.Random) -> str:
    if type_ == "girl":
        return rng.choice(["Mia", "Lena", "Noa", "Ruby", "Ivy"])
    return rng.choice(["Ben", "Theo", "Eli", "Noah", "Finn"])


def build_world(params: StoryParams) -> World:
    choose_premise(params.place, params.magic, params.lesson)
    if not valid_combo(params.place, params.magic, params.lesson):
        raise StoryError("This storyworld only makes sense in cozy places with gentle magic.")

    world = World(place=params.place, magic=params.magic, lesson=params.lesson)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.child_name,
        meters={"steps": 0.0, "curiosity": 0.0, "care": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "lesson": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        meters={"steps": 0.0, "gentleness": 0.0},
        memes={"warmth": 0.0, "joy": 0.0},
    ))
    trail = world.add(Entity(
        id="trail",
        kind="thing",
        type="trail",
        label="squiggly trail",
        phrase="a squiggly little trail",
        meters={"glow": 0.0, "length": 3.0},
    ))
    lost = world.add(Entity(
        id="lost",
        kind="thing",
        type="creature",
        label="tiny lost firefly",
        phrase="a tiny lost firefly",
        owner=None,
        with_actor=None,
        meters={"tired": 0.0, "bright": 0.0},
        memes={"hope": 0.0},
    ))
    gift = world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=MAGICS[params.magic]["gift"],
        phrase=MAGICS[params.magic]["gift"],
        owner=helper.id,
    ))

    # Act 1: noticing the mystery.
    world.say(f"{child.label} was in {PLACES[params.place]['label']}.")
    world.say(f"One afternoon, {child.label} spotted {trail.phrase} near the path.")
    child.memes["curiosity"] += 1
    child.meters["curiosity"] += 1
    trail.meters["glow"] += 1
    world.say(f"It {MAGICS[params.magic]['effect']}, and that made {child.label} look closer.")
    world.say(f"{child.label} felt curious instead of scared.")

    # Act 2: follow the trail.
    world.para()
    child.meters["steps"] += 4
    helper.meters["steps"] += 1
    world.say(f"{child.label} followed the squiggly line past the {random.choice(list(PLACES[params.place]['features']))}.")
    child.memes["worry"] += 0.5
    lost.meters["tired"] += 1
    lost.meters["bright"] += 0.5
    world.say(f"At the end, {child.label} found {lost.phrase}, blinking sadly.")
    world.say(f"{child.label} learned that curiosity works best when it is gentle.")

    # Act 3: heartwarming help.
    world.para()
    helper.memes["warmth"] += 1
    helper.meters["gentleness"] += 1
    world.say(f"{helper.label} came over with {gift.phrase}.")
    world.say(f"{helper.label} said, 'Let's help softly and see what {MAGICS[params.magic]['label']} can do.'")
    child.meters["care"] += 1
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    lost.meters["tired"] = 0.0
    lost.meters["bright"] = 2.0
    world.say(f"{child.label} held still while the little magic did its work.")
    world.say(f"Then {lost.phrase} buzzed happily into the warm light, and the garden felt brighter than before.")
    world.say(f"{child.label} smiled, because {LESSONS[params.lesson]}.")

    world.facts.update(
        child=child,
        helper=helper,
        trail=trail,
        lost=lost,
        gift=gift,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a heartwarming story set in {PLACES[p.place]['label']} about a child who notices something squiggly and magical.",
        f"Tell a gentle tale where {p.child_name} follows a squiggly trail and learns {LESSONS[p.lesson]}.",
        f"Write a short story for children that includes curiosity, magic, and a happy ending in {PLACES[p.place]['label']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    lost: Entity = world.facts["lost"]
    mag = MAGICS[p.magic]["label"]
    return [
        QAItem(
            question=f"What did {child.label} notice in {PLACES[p.place]['label']}?",
            answer=f"{child.label} noticed a squiggly little trail with {mag}.",
        ),
        QAItem(
            question=f"What was at the end of the squiggly trail?",
            answer=f"At the end, {child.label} found {lost.phrase}, and it looked tired and sad.",
        ),
        QAItem(
            question=f"How did the story end for {child.label}?",
            answer=f"{helper.label} helped kindly, {child.label} felt happy, and the little lost creature was safe again.",
        ),
        QAItem(
            question=f"What lesson did {child.label} learn?",
            answer=f"{child.label} learned that {LESSONS[p.lesson]}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question="What does curious mean?",
            answer="Curious means wanting to look, learn, or find out more about something new.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special and unusual that can do things people cannot do in ordinary life.",
        ),
        QAItem(
            question="Why can a squiggly line be interesting?",
            answer="A squiggly line can be interesting because it looks unusual and can make someone wonder where it goes.",
        ),
        QAItem(
            question=f"Why is {PLACES[p.place]['label']} a nice place for this story?",
            answer=f"{PLACES[p.place]['label']} is nice for this story because it feels cozy, calm, and safe for a gentle mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming squiggly-magic storyworld.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--magic", choices=sorted(MAGICS))
    ap.add_argument("--lesson", choices=sorted(LESSONS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.magic is None or c[1] == args.magic)
        and (args.lesson is None or c[2] == args.lesson)
    ]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")

    place, magic, lesson = rng.choice(filtered)
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = args.name or name_for(child_gender, rng)
    helper_name = args.helper_name or name_for(helper_gender, rng)
    return StoryParams(
        place=place,
        magic=magic,
        child_name=child_name,
        child_type=child_gender,
        helper_name=helper_name,
        helper_type=helper_gender,
        lesson=lesson,
    )


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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} valid combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        for p, m, l in valid_combos():
            params = StoryParams(
                place=p,
                magic=m,
                lesson=l,
                child_name="Mia",
                child_type="girl",
                helper_name="Ben",
                helper_type="boy",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            local_rng = random.Random(seed)
            params = resolve_params(args, local_rng)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
