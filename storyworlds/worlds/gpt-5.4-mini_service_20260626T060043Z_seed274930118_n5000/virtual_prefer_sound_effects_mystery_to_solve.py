#!/usr/bin/env python3
"""
storyworlds/worlds/virtual_prefer_sound_effects_mystery_to_solve.py
===================================================================

A tiny superhero storyworld about a hero who prefers a virtual training room
but must solve a real mystery using sound effects, clues, and brave choices.

Premise:
- A young hero prefers practicing in a virtual city because it is safe and fun.
- A neighborhood mystery appears: important lights go out, and strange sounds
  point toward where the problem began.
- The hero listens, follows clues, and solves the mystery with a helper gadget.
- The ending shows the city bright again and the hero choosing the real world.

This world uses physical meters and emotional memes in the world model, and it
includes an inline ASP twin for the reasonableness gate.
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
# World entities
# ---------------------------------------------------------------------------
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
        if self.role in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "he", "object": "him", "possessive": "his"}[case]


@dataclass
class Place:
    id: str
    label: str
    virtual: bool = False
    sound: str = ""
    hides: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    clue_sound: str
    cause: str
    solved_by: str
    risk: str


@dataclass
class Gadget:
    id: str
    label: str
    use: str
    sound: str


@dataclass
class World:
    place: Place
    mystery: Mystery
    hero: Entity
    friend: Entity
    gadget: Gadget
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Registry content
# ---------------------------------------------------------------------------
PLACES = {
    "virtual_city": Place(
        id="virtual_city",
        label="the virtual city",
        virtual=True,
        sound="BEEP! WHIRR!",
        hides={"screen_glitch", "echo_trail"},
    ),
    "rooftop": Place(
        id="rooftop",
        label="the rooftop",
        virtual=False,
        sound="WHOOSH!",
        hides={"wind_turbine", "drain_cover"},
    ),
    "museum": Place(
        id="museum",
        label="the museum hall",
        virtual=False,
        sound="TINK! TINK!",
        hides={"display_case", "broken_alarm"},
    ),
    "subway": Place(
        id="subway",
        label="the subway platform",
        virtual=False,
        sound="CLANG! RUMBLE!",
        hides={"track_switch", "speaker_box"},
    ),
}

MYSTERIES = {
    "lights_out": Mystery(
        id="lights_out",
        label="the missing power",
        clue_sound="bzzzt",
        cause="a loose wire behind a panel",
        solved_by="follow the buzzing sound",
        risk="the city stayed dark",
    ),
    "stuck_alarm": Mystery(
        id="stuck_alarm",
        label="the stuck alarm",
        clue_sound="wail-wail",
        cause="a jammed button under dust",
        solved_by="listen for the looping wail",
        risk="everyone got worried",
    ),
    "stolen_star": Mystery(
        id="stolen_star",
        label="the missing star badge",
        clue_sound="clink",
        cause="it rolled behind a vent",
        solved_by="track the tiny clink",
        risk="the parade could not begin",
    ),
}

GADGETS = {
    "sonar_gloves": Gadget(
        id="sonar_gloves",
        label="sonar gloves",
        use="tap walls and hear what is hidden",
        sound="PING!",
    ),
    "echo_mask": Gadget(
        id="echo_mask",
        label="an echo mask",
        use="listen for bouncing clues",
        sound="BOOP!",
    ),
    "flash_map": Gadget(
        id="flash_map",
        label="a flash map",
        use="draw a bright path to the answer",
        sound="SNAP!",
    ),
}

HERO_NAMES = ["Nova", "Sky", "Milo", "Zara", "Iris", "Jett"]
FRIEND_NAMES = ["Pip", "Rae", "Toby", "June"]
ROLES = ["girl", "boy"]


# ---------------------------------------------------------------------------
# Inline world model
# ---------------------------------------------------------------------------
def build_world(place: Place, mystery: Mystery, hero_name: str, hero_role: str, friend_name: str, gadget: Gadget) -> World:
    hero = Entity(
        id=hero_name,
        kind="character",
        label="hero",
        role=hero_role,
        meters={"courage": 1.0, "energy": 1.0, "attention": 1.0},
        memes={"prefer_virtual": 1.0, "curiosity": 1.0, "worry": 0.0, "joy": 0.0},
    )
    friend = Entity(
        id=friend_name,
        kind="character",
        label="sidekick",
        role="boy",
        meters={"energy": 1.0, "attention": 1.0},
        memes={"curiosity": 1.0, "worry": 0.0},
    )
    world = World(place=place, mystery=mystery, hero=hero, friend=friend, gadget=gadget)
    world.add(hero)
    world.add(friend)
    world.add(Entity(id="city", kind="thing", label=place.label))
    world.add(Entity(id="mystery", kind="thing", label=mystery.label))
    world.add(Entity(id=gadget.id, kind="thing", label=gadget.label))
    return world


def sound_effect(place: Place, mystery: Mystery) -> str:
    return f"{place.sound} {mystery.clue_sound.upper()}!"


def reasonableness_gate(place: Place, mystery: Mystery, gadget: Gadget) -> None:
    if place.virtual and mystery.id == "stolen_star" and gadget.id == "flash_map":
        return
    if not place.virtual and mystery.id == "lights_out" and gadget.id == "sonar_gloves":
        return
    if mystery.id == "stuck_alarm" and gadget.id in {"echo_mask", "sonar_gloves"}:
        return
    raise StoryError("No reasonable superhero story fits those choices.")


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def tell_story(world: World) -> None:
    h = world.hero
    f = world.friend
    p = world.place
    m = world.mystery
    g = world.gadget

    if p.virtual:
        world.say(
            f"{h.id} was a brave little hero who liked the virtual city best, "
            f"because {h.pronoun('subject')} could practice without any real bumps or bruises."
        )
    else:
        world.say(
            f"{h.id} was a brave little hero who liked the virtual city best, "
            f"but today {h.pronoun('subject')} had to leave the screen and step into {p.label}."
        )
    world.say(
        f"{f.id} hurried beside {h.id}, and the two of them carried {g.label} "
        f"because it could {g.use}."
    )

    world.para()
    world.say(
        f"Then {sound_effect(p, m)} The sound echoed once, then again, like a clue asking for help."
    )
    h.memes["worry"] += 1.0
    h.memes["curiosity"] += 1.0
    world.facts["first_sound"] = sound_effect(p, m)
    world.facts["risk"] = m.risk

    if m.id == "lights_out":
        world.say(
            f"The lights blinked low, and {h.id} whispered, \"I prefer the virtual city, "
            f"but this is a real mystery to solve.\""
        )
    elif m.id == "stuck_alarm":
        world.say(
            f"The alarm kept going, and {f.id} covered {f.pronoun('possessive')} ears. "
            f"{h.id} listened instead of panicking."
        )
    else:
        world.say(
            f"A missing badge made the hallway feel empty, and {h.id} listened for a tiny clue."
        )

    world.para()
    world.say(
        f"{h.id} used {g.label} to {g.use}, and the sound came back from the right wall."
    )
    world.say(
        f"{h.id} followed the clue with a careful step, saying, \"I think the answer is near.\""
    )
    world.facts["method"] = g.use

    if m.cause == "a loose wire behind a panel":
        world.say(
            f"Behind the panel, {h.id} found a loose wire. {h.pronoun('subject').capitalize()} "
            f"snapped it back in place, and the buzzing stopped."
        )
    elif m.cause == "a jammed button under dust":
        world.say(
            f"Under the dusty button, {h.id} found the jam. {f.id} brushed it away, and the wail stopped."
        )
    else:
        world.say(
            f"Near the vent, {h.id} found the badge. It had rolled so far away that nobody could see it."
        )
    world.facts["cause"] = m.cause

    world.para()
    h.memes["joy"] += 1.0
    h.memes["worry"] = 0.0
    f.memes["worry"] = 0.0
    world.say(
        f"At last, {p.label} shone bright again. {h.id} smiled, because solving the mystery felt better "
        f"than staying safe in a pretend world."
    )
    world.say(
        f"{f.id} laughed, {g.label} gleamed, and the last sound was a happy {g.sound}."
    )


# ---------------------------------------------------------------------------
# Parameter dataclass and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    gadget: str
    hero_name: str
    hero_role: str
    friend_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for m in MYSTERIES.values():
            for g in GADGETS.values():
                if p.virtual and m.id == "stolen_star" and g.id == "flash_map":
                    combos.append((p.id, m.id, g.id))
                elif not p.virtual and m.id == "lights_out" and g.id == "sonar_gloves":
                    combos.append((p.id, m.id, g.id))
                elif m.id == "stuck_alarm" and g.id in {"echo_mask", "sonar_gloves"}:
                    combos.append((p.id, m.id, g.id))
    return combos


# ---------------------------------------------------------------------------
# Generation helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short superhero story with a virtual place, a mystery to solve, and at least one sound effect.',
        f"Tell a child-friendly superhero story where {world.hero.id} prefers the virtual city but solves {world.mystery.label} in {world.place.label}.",
        f"Make the story include the sound effect {f['first_sound']} and end with the mystery being solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, f, p, m, g = world.hero, world.friend, world.place, world.mystery, world.gadget
    return [
        QAItem(
            question=f"Why did {h.id} go to {p.label} instead of staying in the virtual city?",
            answer=(
                f"{h.id} went because there was a real mystery to solve, and the sound clues were only happening in {p.label}. "
                f"{h.pronoun('subject').capitalize()} still preferred the virtual city, but {h.pronoun('subject')} chose to be brave."
            ),
        ),
        QAItem(
            question=f"What sound helped {h.id} notice where the mystery was hiding?",
            answer=(
                f"The clue sound was {world.facts['first_sound']}. "
                f"{h.id} heard it echo and used it to find the answer."
            ),
        ),
        QAItem(
            question=f"What did {h.id} use to solve {m.label}?",
            answer=(
                f"{h.id} used {g.label} to {g.use}. That helped {h.id} follow the clue and fix the problem."
            ),
        ),
        QAItem(
            question=f"How did the story end for {p.label}?",
            answer=(
                f"{p.label} ended bright and safe again, and {h.id} felt proud after solving the mystery."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a virtual place?",
            answer="A virtual place is a pretend or computer-made place that looks real on a screen.",
        ),
        QAItem(
            question="Why do superheroes use gadgets?",
            answer="Superheroes use gadgets to help them do brave jobs, find clues, and solve problems.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem you do not understand at first, so you have to look for clues.",
        ),
        QAItem(
            question="Why are sound effects useful in stories?",
            answer="Sound effects help a reader imagine what is happening, like a clue, a crash, or a beep.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_virtual(P) :- virtual(P).
valid(P, M, G) :- place_virtual(P), mystery(M), gadget(G), combo(P, M, G).
valid(P, M, G) :- place(P), mystery(M), gadget(G), combo(P, M, G).

combo(virtual_city, stolen_star, flash_map).
combo(rooftop, lights_out, sonar_gloves).
combo(museum, stuck_alarm, echo_mask).
combo(subway, stuck_alarm, sonar_gloves).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.virtual:
            lines.append(asp.fact("virtual", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for gid in GADGETS:
        lines.append(asp.fact("gadget", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation and CLI
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery and args.gadget:
        reasonableness_gate(PLACES[args.place], MYSTERIES[args.mystery], GADGETS[args.gadget])

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.gadget is None or c[2] == args.gadget)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, mystery, gadget = rng.choice(sorted(combos))
    hero_role = args.hero_role or rng.choice(ROLES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    return StoryParams(
        place=place,
        mystery=mystery,
        gadget=gadget,
        hero_name=hero_name,
        hero_role=hero_role,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    gadget = GADGETS[params.gadget]
    world = build_world(place, mystery, params.hero_name, params.hero_role, params.friend_name, gadget)
    tell_story(world)
    world.facts.update(place=place, mystery=mystery, gadget=gadget, hero=world.hero, friend=world.friend)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero storyworld: a virtual preference, a real mystery, and sound effects."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-role", choices=ROLES)
    ap.add_argument("--friend-name")
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


CURATED = [
    StoryParams(place="virtual_city", mystery="stolen_star", gadget="flash_map", hero_name="Nova", hero_role="girl", friend_name="Pip"),
    StoryParams(place="rooftop", mystery="lights_out", gadget="sonar_gloves", hero_name="Sky", hero_role="boy", friend_name="Rae"),
    StoryParams(place="museum", mystery="stuck_alarm", gadget="echo_mask", hero_name="Iris", hero_role="girl", friend_name="June"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
