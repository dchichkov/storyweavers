#!/usr/bin/env python3
"""
storyworlds/worlds/reckless_cautionary_curiosity_flashback_slice_of_life.py
===========================================================================

A small slice-of-life story world about a curious child, a reckless impulse,
a cautionary warning, and a flashback that changes the choice.

Premise:
- A child spots something interesting during an ordinary day.
- Curiosity invites a reckless move.
- A flashback reminds them of a past scrape or spill.
- A cautious helper suggests a safer, kinder alternative.
- The ending image shows the child choosing the safer path and feeling proud.
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
class StoryParams:
    place: str
    child_name: str
    child_type: str
    helper_type: str
    curious_about: str
    flashback_kind: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        out: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    out.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            out.append(" ".join(current))
        return "\n\n".join(out)

    def child(self) -> Entity:
        return self.entities["child"]

    def helper(self) -> Entity:
        return self.entities["helper"]


PLACES = {
    "kitchen": "the kitchen",
    "library": "the library",
    "porch": "the porch",
    "garden": "the garden",
    "bus_stop": "the bus stop",
}

CURIOSITIES = {
    "loose drawer": {
        "thing": "a loose drawer",
        "risk": "pinched fingers",
        "safer": "ask an adult to help open it slowly",
        "ending": "the drawer opened just a little, and nothing got pinched",
    },
    "rain puddle": {
        "thing": "a deep rain puddle",
        "risk": "wet socks",
        "safer": "jump over it instead of stepping straight in",
        "ending": "the child hopped cleanly over the puddle",
    },
    "glass jar": {
        "thing": "a glass jar on a shelf",
        "risk": "a broken jar and a loud mess",
        "safer": "point at it and let the grown-up reach it",
        "ending": "the jar stayed safe on the shelf",
    },
    "sleepy kitten": {
        "thing": "a sleepy kitten by a blanket",
        "risk": "startling the kitten",
        "safer": "sit quietly and let the kitten come first",
        "ending": "the kitten blinked, yawned, and stayed cozy",
    },
    "blue button": {
        "thing": "a tiny blue button in a crack",
        "risk": "a scraped knee",
        "safer": "use a stick to nudge it out gently",
        "ending": "the button slid out without any scraping",
    },
}

FLASHBACKS = {
    "spilled juice": "the time they rushed too fast and spilled juice across the table",
    "scraped elbow": "the afternoon they climbed too high and scraped an elbow on the way down",
    "muddy shoes": "the day they stomped into mud and had to sit while their shoes dried",
    "broken crayon": "the moment they squeezed a crayon too hard and it snapped in half",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with curiosity, caution, and a flashback.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "grandparent", "aunt", "uncle"])
    ap.add_argument("--curious-about", choices=sorted(CURIOSITIES))
    ap.add_argument("--flashback-kind", choices=sorted(FLASHBACKS))
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
    curious_about = args.curious_about or rng.choice(list(CURIOSITIES))
    flashback_kind = args.flashback_kind or rng.choice(list(FLASHBACKS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(
        ["Mina", "Nico", "Lena", "Toby", "Ari", "June", "Theo", "Ruby"]
    )
    helper_type = args.helper_type or rng.choice(["mother", "father", "grandparent", "aunt", "uncle"])
    return StoryParams(
        place=place,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        curious_about=curious_about,
        flashback_kind=flashback_kind,
    )


def reasonableness_check(params: StoryParams) -> None:
    if params.curious_about not in CURIOSITIES:
        raise StoryError("Unknown curiosity choice.")
    if params.flashback_kind not in FLASHBACKS:
        raise StoryError("Unknown flashback choice.")


def tell(params: StoryParams) -> World:
    reasonableness_check(params)
    w = World(params)
    child = w.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    helper = w.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_type))
    item = CURIOSITIES[params.curious_about]
    flash = FLASHBACKS[params.flashback_kind]

    child.memes["curiosity"] = 1
    child.memes["reckless"] = 1
    w.say(f"{child.label} was sitting {w.params.place.replace('_', ' ')} with {helper.label}.")
    w.say(f"On an ordinary afternoon, {child.label} noticed {item['thing']} and leaned closer.")
    w.say(f"{child.pronoun().capitalize()} wanted to poke it right away, even though that felt reckless.")

    w.say("")
    child.memes["flashback"] = 1
    w.say(f"Then {child.label} remembered {flash}.")
    w.say(f"That memory made {child.label} slow down and look again instead of rushing in.")

    helper.memes["cautionary"] = 1
    w.say(f"{helper.label.capitalize()} gave a small warning: \"Let's be careful so nobody gets {item['risk']}.\"")
    w.say(f"{helper.label.capitalize()} showed a safer way: {item['safer']}.")

    child.memes["prudence"] = 1
    child.memes["reckless"] = 0
    w.say(f"{child.label} nodded, used the safer way, and smiled when {item['ending']}.")

    w.say(f"By the end, the ordinary day still felt warm and simple, but {child.label} had learned to pause first.")
    w.facts.update(
        child=child,
        helper=helper,
        item=item,
        flash=flash,
        place=PLACES[params.place],
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.params
    item = CURIOSITIES[p.curious_about]["thing"]
    return [
        f"Write a gentle slice-of-life story about {p.child_name} in {PLACES[p.place]} who gets curious about {item}.",
        f"Tell a short story where a reckless impulse is interrupted by a flashback and a cautious helper.",
        f"Make a child-facing story about curiosity, caution, and an ordinary day going a little wiser.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    item = CURIOSITIES[p.curious_about]
    return [
        QAItem(
            question=f"Where was {p.child_name} when the curious moment happened?",
            answer=f"{p.child_name} was in {PLACES[p.place]}, just having an ordinary day with the helper.",
        ),
        QAItem(
            question=f"What was {p.child_name} curious about?",
            answer=f"{p.child_name} was curious about {item['thing']}. That made {p.child_name} want to move closer.",
        ),
        QAItem(
            question="What changed the reckless choice?",
            answer=f"A flashback to {FLASHBACKS[p.flashback_kind]} helped {p.child_name} slow down and choose the safer way.",
        ),
        QAItem(
            question="What did the helper warn about?",
            answer=f"The helper warned that rushing could lead to {item['risk']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes a person want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is reckless behavior?",
            answer="Reckless behavior is acting too fast without enough care about what might go wrong.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory that comes back into your mind from something that happened before.",
        ),
        QAItem(
            question="Why do people give cautionary warnings?",
            answer="People give cautionary warnings to help someone stay safe and avoid getting hurt or making a mess.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} memes={dict(e.memes)} meters={dict(e.meters)}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(X) :- child(X).
reckless(X) :- curious(X), near_interest(X).
safer_choice(X) :- flashback(X), cautionary_help(X).
resolved(X) :- reckless(X), safer_choice(X).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("child", "child"),
            asp.fact("near_interest", "child"),
            asp.fact("flashback", "child"),
            asp.fact("cautionary_help", "child"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    asp_set = set(asp.atoms(model, "resolved"))
    py_set = {("child",)}
    if asp_set == py_set:
        print("OK: ASP and Python parity match.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams("kitchen", "Mina", "girl", "mother", "loose drawer", "spilled juice"),
    StoryParams("library", "Nico", "boy", "father", "glass jar", "scraped elbow"),
    StoryParams("garden", "Lena", "girl", "grandparent", "sleepy kitten", "muddy shoes"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(asp.atoms(model, "resolved"))
        return

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(build_sample(p))
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(build_sample(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
