#!/usr/bin/env python3
"""
storyworlds/worlds/budget_document_attention_twist_sound_effects_mystery.py
===========================================================================

A small mystery storyworld about a missing budget document, sharpened by
attention, sound effects, and a twist.

Premise:
- A child notices that a school budget document has gone missing.
- The room is full of odd sound effects from a practice mystery show.
- Careful attention to the sounds reveals a hidden clue.
- The twist is that the "mystery noise" is not a ghost at all; it is a prop
  cart, and the document was tucked inside by mistake.

The world model tracks:
- physical state: where the document is, whether props are open, whether
  sound-makers are active, and whether a room has been searched
- emotional state: curiosity, worry, attention, relief

The story is generated from the simulation, not from a fixed paragraph.
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
# World data
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    place: str
    indoors: bool = True
    background_sound: str = "soft humming"


@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["attention", "curiosity", "worry", "relief"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Item:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("moved", 0.0)
        self.meters.setdefault("opened", 0.0)


@dataclass
class World:
    setting: Setting
    entities: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "classroom": Setting(place="the classroom", background_sound="the tiny buzz of lights"),
    "library": Setting(place="the library", background_sound="the hush of pages"),
    "office": Setting(place="the office nook", background_sound="the click of a fan"),
}

NAMES = ["Mina", "Noah", "Ruby", "Eli", "Iris", "Theo", "Zara", "Maya"]
TRAITS = ["careful", "curious", "quiet", "sharp-eyed", "brave"]

@dataclass
class StoryParams:
    place: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    child = world.add(Character(
        id=params.name,
        type="child",
        label=params.name,
        traits=["little", params.trait],
    ))
    teacher = world.add(Character(
        id="teacher",
        type="adult",
        label="the teacher",
        traits=["patient", "helpful"],
    ))
    budget = world.add(Item(
        id="budget_doc",
        type="document",
        label="budget document",
        phrase="the school budget document",
        owner=teacher.id,
        hidden_in="prop_cart",
    ))
    cart = world.add(Item(
        id="prop_cart",
        type="cart",
        label="prop cart",
        phrase="the cart of mystery props",
    ))
    recorder = world.add(Item(
        id="sound_box",
        type="device",
        label="sound-effects box",
        phrase="the sound-effects box",
    ))

    world.facts.update(
        child=child, teacher=teacher, budget=budget, cart=cart, recorder=recorder
    )
    return world


def _bump(world: World, who: Character, meter: str, amt: float = 1.0) -> None:
    who.meters[meter] = who.meters.get(meter, 0.0) + amt


def _set(world: World, item: Item, meter: str, amt: float = 1.0) -> None:
    item.meters[meter] = item.meters.get(meter, 0.0) + amt


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []

    child: Character = world.facts["child"]
    budget: Item = world.facts["budget"]
    cart: Item = world.facts["cart"]
    recorder: Item = world.facts["recorder"]

    # Missing document -> worry.
    if budget.hidden_in == "prop_cart" and ("missing", budget.id) not in world.fired:
        if child.meters["attention"] >= 1.0:
            world.fired.add(("missing", budget.id))
            child.meters["worry"] += 1
            out.append(f"{child.label} noticed the budget document was gone.")

    # Attention + sound effects -> clue from the cart.
    if child.meters["attention"] >= 1.0 and recorder.meters["moved"] >= 1.0:
        if ("clue", cart.id) not in world.fired:
            world.fired.add(("clue", cart.id))
            cart.meters["opened"] = 1.0
            out.append("A clatter from the prop cart sounded too round and too close.")

    # Cart opened -> document found.
    if cart.meters["opened"] >= 1.0 and budget.hidden_in == "prop_cart":
        if ("found", budget.id) not in world.fired:
            world.fired.add(("found", budget.id))
            budget.hidden_in = None
            budget.found = True
            child.meters["relief"] += 1
            out.append("Inside the cart, the budget document was tucked behind a fake curtain.")

    if narrate:
        for s in out:
            world.say(s)
    return out


def intro(world: World) -> None:
    child: Character = world.facts["child"]
    world.say(
        f"{child.label} was a {child.traits[-1]} child who noticed little things right away."
    )
    world.say(
        f"At {world.setting.place}, the air carried {world.setting.background_sound}, "
        f"and that made every tiny noise feel important."
    )


def inciting_event(world: World) -> None:
    child: Character = world.facts["child"]
    teacher: Character = world.facts["teacher"]
    budget: Item = world.facts["budget"]

    _bump(world, child, "curiosity", 1.0)
    _bump(world, child, "attention", 1.0)
    world.say(
        f"{child.label} saw {teacher.label} looking through papers and noticed the budget document was missing."
    )
    world.say(
        f"{child.label} leaned in and tried to pay extra attention, because missing papers always felt like a mystery."
    )


def sound_effects_scene(world: World) -> None:
    child: Character = world.facts["child"]
    recorder: Item = world.facts["recorder"]
    cart: Item = world.facts["cart"]

    _set(world, recorder, "moved", 1.0)
    world.say(
        "From the other corner came a strange whoosh-clack-rattle, like a storm trying to whisper."
    )
    world.say(
        f"{child.label} listened closely and thought, 'That sound is trying to tell me something.'"
    )
    propagate(world)


def twist_scene(world: World) -> None:
    child: Character = world.facts["child"]
    cart: Item = world.facts["cart"]
    budget: Item = world.facts["budget"]

    if not cart.meters.get("opened"):
        cart.meters["opened"] = 1.0
    propagate(world)

    if budget.found:
        world.say(
            "Then came the twist: the noisy mystery was not a ghost at all."
        )
        world.say(
            f"The budget document had slipped into the prop cart when someone rushed to pack up the sound effects."
        )
        world.say(
            f"{child.label} laughed softly, because the scary noise had been only a clumsy mistake."
        )


def ending(world: World) -> None:
    child: Character = world.facts["child"]
    teacher: Character = world.facts["teacher"]
    budget: Item = world.facts["budget"]

    if budget.found:
        world.say(
            f"{teacher.label} thanked {child.label}, and together they set the budget document back on the desk."
        )
        world.say(
            f"By the end, {child.label} felt proud, and the room sounded calm again."
        )


def tell(world: World) -> World:
    intro(world)
    world.para()
    inciting_event(world)
    sound_effects_scene(world)
    world.para()
    twist_scene(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% If the child pays attention, a missing document can become noticeable.
noticed_missing(C, D) :- attention(C), document(D), missing(D).

% If a sound effect clue is heard and the cart is searched, the document is found.
found(D) :- clue(cart), document(D), hidden_in(D, cart).

% The twist is that the noisy thing is a prop cart, not a ghost.
twist(cart) :- clue(cart), not ghost(cart).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
    lines.append("document(budget_doc).")
    lines.append("cart(prop_cart).")
    lines.append("clue(prop_cart).")
    lines.append("hidden_in(budget_doc,prop_cart).")
    lines.append("attention(child).")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show found/1. #show twist/1."))
    found_atoms = set(asp.atoms(model, "found"))
    twist_atoms = set(asp.atoms(model, "twist"))
    if found_atoms == {("budget_doc",)} and twist_atoms == {("cart",)}:
        print("OK: ASP twin matches the storyworld's core mystery logic.")
        return 0
    print("MISMATCH in ASP twin.")
    print("found:", sorted(found_atoms))
    print("twist:", sorted(twist_atoms))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Character = f["child"]
    return [
        f'Write a short mystery for a young child about a missing budget document, a little attention, and a twist.',
        f"Tell a gentle mystery where {child.label} listens for sound effects and finds the budget document.",
        f'Write a child-friendly story that uses the words "budget", "document", and "attention".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Character = f["child"]
    teacher: Character = f["teacher"]
    budget: Item = f["budget"]
    qa = [
        QAItem(
            question=f"What was missing in the story?",
            answer="The budget document was missing, and that is what made the room feel mysterious.",
        ),
        QAItem(
            question=f"Who noticed the missing document first?",
            answer=f"{child.label} noticed it first by paying close attention to what was happening around the desk.",
        ),
        QAItem(
            question=f"What did the strange sound effects help reveal?",
            answer="They helped reveal that the budget document was hidden in the prop cart.",
        ),
        QAItem(
            question=f"What was the twist?",
            answer="The twist was that the spooky noise was not a ghost at all. It was just the prop cart and the sound-effects setup making a clumsy racket.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{teacher.label} and {child.label} found the budget document, put it back where it belonged, and the room grew calm again.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a budget?",
            answer="A budget is a plan for how money will be used. It helps people decide what they can pay for and what they should save.",
        ),
        QAItem(
            question="What is a document?",
            answer="A document is a paper or file that holds information, instructions, or a message.",
        ),
        QAItem(
            question="What does attention mean?",
            answer="Attention means focusing your mind on one thing so you can notice details and understand what is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params, generation, emission, CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery about budget, document, attention, twist, and sound effects.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--name", choices=NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(make_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        if isinstance(e, Character):
            lines.append(
                f"{e.id}: attention={e.meters['attention']} curiosity={e.meters['curiosity']} "
                f"worry={e.meters['worry']} relief={e.meters['relief']}"
            )
        else:
            lines.append(
                f"{e.id}: hidden_in={getattr(e, 'hidden_in', None)} found={getattr(e, 'found', None)} "
                f"meters={dict(e.meters)}"
            )
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
    StoryParams(place="classroom", name="Mina", trait="sharp-eyed"),
    StoryParams(place="library", name="Iris", trait="curious"),
    StoryParams(place="office", name="Theo", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show found/1. #show twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show found/1. #show twist/1."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
