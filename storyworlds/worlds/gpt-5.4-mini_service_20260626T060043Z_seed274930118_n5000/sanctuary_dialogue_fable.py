#!/usr/bin/env python3
"""
storyworlds/worlds/sanctuary_dialogue_fable.py
==============================================

A small fable-like story world about a sanctuary, a visitor, and a choice to
welcome someone in the rain.

The world is deliberately compact: one setting, one visitor, one keeper, one
need, and one turn in the dialogue. The story is driven by physical meters
(hunger, cold, shelter, rain) and emotional memes (fear, trust, kindness,
pride). The ending image proves what changed: the visitor is safe, and the
sanctuary has become warmer by being shared.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["cold", "rain", "hunger", "shelter", "fullness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "trust", "kindness", "pride", "relief", "welcome"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hare", "fox", "owl", "mouse", "badger"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.kind == "group" else "it"


@dataclass
class Place:
    id: str
    label: str
    shelter: float
    warmth: float
    sacred: bool = False
    open_to_all: bool = True


@dataclass
class Need:
    id: str
    label: str
    weather: str
    harms: set[str]
    asks_for: str
    risk_text: str
    blessing_text: str


@dataclass
class StoryParams:
    place: str
    need: str
    visitor: str
    keeper: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    visitor: Entity
    keeper: Entity
    need: Need
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "sanctuary": Place(
        id="sanctuary",
        label="the sanctuary",
        shelter=2.0,
        warmth=1.0,
        sacred=True,
        open_to_all=False,
    ),
    "grove": Place(
        id="grove",
        label="the quiet grove",
        shelter=1.0,
        warmth=0.5,
        sacred=False,
        open_to_all=True,
    ),
    "barn": Place(
        id="barn",
        label="the old barn",
        shelter=1.5,
        warmth=1.5,
        sacred=False,
        open_to_all=True,
    ),
}

NEEDS = {
    "storm": Need(
        id="storm",
        label="the storm",
        weather="rain",
        harms={"cold", "fear"},
        asks_for="shelter",
        risk_text="the rain can chill a small traveler to the bone",
        blessing_text="dry straw and a warm beam can steady even a frightened heart",
    ),
    "night": Need(
        id="night",
        label="the long night",
        weather="dark",
        harms={"fear"},
        asks_for="light",
        risk_text="the dark can make a lonely path feel much larger",
        blessing_text="a lantern and a quiet room can make the dark feel smaller",
    ),
}

ANIMALS = {
    "hare": {"kind": "animal", "traits": ["small", "swift", "shy"]},
    "fox": {"kind": "animal", "traits": ["bright-eyed", "careful", "proud"]},
    "owl": {"kind": "animal", "traits": ["old", "watchful", "calm"]},
    "badger": {"kind": "animal", "traits": ["sturdy", "stern", "fair"]},
    "mouse": {"kind": "animal", "traits": ["tiny", "polite", "soft"]},
}

KEEPERS = {
    "owl": {"label": "the owl keeper", "type": "owl"},
    "badger": {"label": "the badger keeper", "type": "badger"},
    "fox": {"label": "the fox keeper", "type": "fox"},
}

VISITORS = {
    "hare": {"label": "a little hare", "type": "hare"},
    "mouse": {"label": "a small mouse", "type": "mouse"},
    "fox": {"label": "a young fox", "type": "fox"},
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like sanctuary dialogue story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    need = args.need or rng.choice(list(NEEDS))
    visitor = args.visitor or rng.choice(list(VISITORS))
    keeper = args.keeper or rng.choice(list(KEEPERS))
    if visitor == keeper:
        raise StoryError("The visitor and keeper must be different characters.")
    if place == "sanctuary" and not SETTINGS[place].open_to_all and visitor == "fox":
        # still allowed; the story is about opening the door, but avoid a fixed mismatch.
        pass
    return StoryParams(place=place, need=need, visitor=visitor, keeper=keeper)


def _entity_from(spec: dict, eid: str) -> Entity:
    return Entity(
        id=eid,
        kind=spec.get("kind", "animal"),
        type=spec["type"],
        label=spec["label"],
        traits=list(spec.get("traits", [])),
    )


def tell(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    need = NEEDS[params.need]
    visitor = _entity_from(VISITORS[params.visitor], "visitor")
    keeper = _entity_from(KEEPERS[params.keeper], "keeper")
    world = World(place=place, visitor=visitor, keeper=keeper, need=need)

    visitor.meters["cold"] += 1.0 if need.id == "storm" else 0.2
    visitor.memes["fear"] += 1.0
    keeper.memes["pride"] += 0.5
    keeper.memes["kindness"] += 0.3

    world.say(f"At {place.label}, the {need.label} rolled across the trees like a gray drum.")
    world.say(
        f"A little {visitor.type} stood at the gate and whispered, "
        f'"Please, may I come in? {need.risk_text.capitalize()}."'
    )
    world.say(
        f"The {keeper.type} keeper looked at the wet path and said, "
        f'"This is a sanctuary. But sanctuary is not a word for one creature alone."'
    )

    world.para()
    world.say(
        f'The {visitor.type} bowed his head. "{world.place.label.capitalize()} sounds warm," he said, '
        f'"but I have only my tired feet and a shivering heart."'
    )
    world.say(
        f'The {keeper.type} keeper listened, then answered, '
        f'"A sanctuary should shelter the cold, the scared, and the weary. '
        f'What is it you ask for?"'
    )
    visitor.memes["trust"] += 1.0
    visitor.memes["fear"] += 0.5
    world.say(
        f'"{need.asks_for}," said the {visitor.type}, and rain tapped softly on the stones.'
    )

    world.para()
    if not place.open_to_all and need.id == "storm":
        world.say(
            f'The keeper frowned for a moment, because dry space was small and the shelter was precious.'
        )
        world.say(
            f'Then the keeper remembered that a sanctuary loses its heart if it refuses a true need.'
        )
    world.say(
        f'"Come in," said the {keeper.type} keeper at last. "We can make room."'
    )
    keeper.memes["kindness"] += 1.0
    keeper.memes["pride"] += 0.2
    visitor.meters["shelter"] += place.shelter
    visitor.meters["cold"] = max(0.0, visitor.meters["cold"] - place.warmth)
    visitor.memes["relief"] += 1.0
    visitor.memes["trust"] += 1.0

    world.say(
        f"The {visitor.type} stepped under the roof, and the rain stayed outside where it belonged."
    )
    world.say(
        f"The {keeper.type} keeper shared a dry corner and a quiet word, and the little traveler stopped shaking."
    )

    world.para()
    world.say(
        f'By the time the storm passed, the sanctuary felt warmer, not because the weather had changed, '
        f'but because the hearts inside had.'
    )
    world.say(
        f'The {visitor.type} slept safely beneath the beams, and the {keeper.type} keeper learned that a welcome can be its own lamp.'
    )

    world.facts.update(
        place=place,
        need=need,
        visitor=visitor,
        keeper=keeper,
        welcomed=True,
    )
    return world


def generate_story_text(world: World) -> str:
    return world.render() + "\n\nMoral: A sanctuary grows by sharing its shelter."


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable about {f['visitor'].label} seeking safety in {f['place'].label} during {f['need'].label}.",
        f"Tell a dialogue-driven story where the keeper of {f['place'].label} must decide whether to welcome a traveler.",
        "Write a gentle fable with a sanctuary, a question at the gate, and a kind answer at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    visitor = f["visitor"]
    keeper = f["keeper"]
    place = f["place"]
    need = f["need"]
    return [
        QAItem(
            question=f"Who came to {place.label} asking for help?",
            answer=f"A little {visitor.type} came to {place.label} asking for {need.asks_for}.",
        ),
        QAItem(
            question=f"What did the {keeper.type} keeper finally say?",
            answer=f"The {keeper.type} keeper said, \"Come in, we can make room.\"",
        ),
        QAItem(
            question="Why did the visitor feel better by the end?",
            answer=(
                f"The visitor felt better because the keeper welcomed him inside, "
                f"so the rain stayed out and the sanctuary gave him shelter."
            ),
        ),
        QAItem(
            question="What made the sanctuary feel warmer?",
            answer=(
                f"It felt warmer because kindness filled the room after the keeper chose to share the shelter."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sanctuary?",
            answer="A sanctuary is a safe place where someone can be protected, rested, and cared for.",
        ),
        QAItem(
            question="Why can rain make a small animal uncomfortable?",
            answer="Rain can make a small animal cold and wet, which can be tiring and unpleasant.",
        ),
        QAItem(
            question="What does kindness do in a story like this?",
            answer="Kindness helps one creature make room for another, so both can be safe.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.visitor, world.keeper]:
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: meters={meters} memes={memes}")
    lines.append(f"  place={world.place.id} need={world.need.id}")
    return "\n".join(lines)


ASP_RULES = r"""
visitor_needs_shelter(V) :- visitor(V), cold(V, C), C > 0.
sanctuary_ready(P) :- place(P), sacred(P).
may_welcome(P,V) :- sanctuary_ready(P), visitor(V), visitor_needs_shelter(V).
story_ok(P,N,V,K) :- place(P), need(N), visitor(V), keeper(K), V != K, may_welcome(P,V).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.sacred:
            lines.append(asp.fact("sacred", pid))
        if p.open_to_all:
            lines.append(asp.fact("open_to_all", pid))
    for nid, n in NEEDS.items():
        lines.append(asp.fact("need", nid))
        for harm in sorted(n.harms):
            lines.append(asp.fact("harms", nid, harm))
    for vid in VISITORS:
        lines.append(asp.fact("visitor", vid))
    for kid in KEEPERS:
        lines.append(asp.fact("keeper", kid))
    # world-independent relational facts
    lines.append(asp.fact("cold", "visitor", 1))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/4."))
    clingo_set = set(asp.atoms(model, "story_ok"))
    python_set = set()
    for p in SETTINGS:
        for n in NEEDS:
            for v in VISITORS:
                for k in KEEPERS:
                    if v != k and SETTINGS[p].sacred:
                        python_set.add((p, n, v, k))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate")
    if clingo_set - python_set:
        print("only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="sanctuary", need="storm", visitor="hare", keeper="owl"),
    StoryParams(place="sanctuary", need="storm", visitor="mouse", keeper="badger"),
    StoryParams(place="grove", need="night", visitor="fox", keeper="owl"),
    StoryParams(place="barn", need="storm", visitor="hare", keeper="fox"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = generate_story_text(world)
    return StorySample(
        params=params,
        story=story,
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


def resolve_combos(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        return list(CURATED)
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    out: list[StoryParams] = []
    seen: set[tuple] = set()
    limit = max(args.n * 50, 50)
    i = 0
    while len(out) < args.n and i < limit:
        i += 1
        p = resolve_params(args, rng)
        key = (p.place, p.need, p.visitor, p.keeper)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    if not out:
        raise StoryError("No valid story combinations available.")
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/4."))
        combos = sorted(set(asp.atoms(model, "story_ok")))
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
        return

    try:
        params_list = resolve_combos(args)
    except StoryError as e:
        print(e)
        return

    samples = [generate(p) for p in params_list]

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
            header = f"### {p.visitor} / {p.need} / {p.place} / {p.keeper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
