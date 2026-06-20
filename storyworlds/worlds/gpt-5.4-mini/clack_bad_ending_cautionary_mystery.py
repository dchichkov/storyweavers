#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clack_bad_ending_cautionary_mystery.py
======================================================================

A small standalone storyworld about a curious child, a mysterious clack,
and a cautionary choice that leads to a bad ending.

The world is built around a tiny mystery domain:
- a child hears a clack in an old house or school-like place,
- they follow clues and ignore a warning,
- the search turns into trouble,
- the ending is unsettling and sad,
- the story remains child-facing and concrete.

This world intentionally supports a cautionary, mystery-flavored bad ending.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
    dark_spot: str
    clue_spot: str
    echo: str
    hazard: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    where: str
    reveals: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Warning:
    id: str
    text: str
    sense: int
    weight: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    consequence: str
    bad_end: str
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["mystery"] < THRESHOLD:
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "child" in world.entities:
            world.get("child").memes["worry"] += 1
        out.append("__fear__")
    return out


def _r_trouble(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["ignore"] >= THRESHOLD and world.get("place").meters["danger"] >= THRESHOLD:
        sig = ("trouble", "place")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("place").meters["trouble"] += 1
            out.append("__trouble__")
    return out


CAUSAL_RULES = [
    Rule("fear", "social", _r_fear),
    Rule("trouble", "physical", _r_trouble),
]


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


def clue_risk(place: Place, clue: Clue) -> bool:
    return clue.reveals == place.dark_spot or clue.reveals == place.clue_spot


def valid_combo(place: Place, clue: Clue, warning: Warning, trouble: Trouble) -> bool:
    return clue_risk(place, clue) and warning.sense >= 2 and trouble.label


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, p in PLACES.items():
        for cid, c in CLUES.items():
            for wid, w in WARNINGS.items():
                for tid, t in TROUBLES.items():
                    if valid_combo(p, c, w, t):
                        combos.append((pid, cid, wid, tid))
    return combos


def predict(world: World, place_id: str) -> dict:
    sim = world.copy()
    sim.get("place").meters["mystery"] += 1
    sim.get("child").memes["ignore"] += 1
    propagate(sim, narrate=False)
    return {
        "trouble": sim.get("place").meters["trouble"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"],
    }


def setup(world: World, child: Entity, friend: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    friend.memes["caution"] += 1
    world.say(
        f"On a gray afternoon, {child.id} and {friend.id} were exploring {place.label}. "
        f"The hallway was quiet, and every little sound seemed bigger than usual."
    )


def clack_beats(world: World, place: Place, clue: Clue) -> None:
    world.say(
        f"Then came a sharp clack from {place.clue_spot}. {place.echo} "
        f"{clue.phrase} lay there like a secret waiting to be found."
    )


def warn(world: World, friend: Entity, child: Entity, place: Place, warning: Warning) -> None:
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} frowned and touched {friend.pronoun("possessive")} lip. '
        f'"{warning.text}," {friend.pronoun()} said. "We should leave that alone."'
    )


def ignore_warning(world: World, child: Entity) -> None:
    child.memes["ignore"] += 1
    world.say(
        f'But {child.id} did not stop. {child.pronoun().capitalize()} followed the clack '
        f"toward the dark spot, hoping the mystery would turn into a treasure."
    )


def open_dark(world: World, place: Place, child: Entity) -> None:
    world.get("place").meters["mystery"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} pulled open the hidden door. The room on the other side was colder "
        f"than before, and the air felt wrong."
    )


def bad_end(world: World, trouble: Trouble, child: Entity, friend: Entity, place: Place) -> None:
    place_entity = world.get("place")
    place_entity.meters["danger"] += 1
    place_entity.meters["trouble"] += 1
    for ent in (child, friend):
        ent.memes["worry"] += 1
        ent.memes["sad"] += 1
    world.say(
        f"Something heavy shifted with a second clack, and {trouble.consequence}."
    )
    world.say(
        f"{trouble.bad_end} {child.id} and {friend.id} backed away, but the secret was no longer harmless."
    )
    world.say(
        f"By the time a grown-up came, the clue was ruined and the old {place.label} felt empty."
    )


def tell(place: Place, clue: Clue, warning: Warning, trouble: Trouble,
         child_name: str = "Mia", child_gender: str = "girl",
         friend_name: str = "Noah", friend_gender: str = "boy",
         adult_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the grown-up"))
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="clue", type="clue", label=clue.label))
    world.add(Entity(id="warning", type="warning", label=warning.id))
    world.add(Entity(id="trouble", type="trouble", label=trouble.label))

    setup(world, child, friend, place)
    world.para()
    clack_beats(world, place, clue)
    warn(world, friend, child, place, warning)
    ignore_warning(world, child)
    open_dark(world, place, child)
    world.para()
    bad_end(world, trouble, child, friend, place)

    world.facts.update(
        child=child,
        friend=friend,
        adult=adult,
        place=place,
        clue=clue,
        warning=warning,
        trouble=trouble,
        outcome="bad",
        ignored=True,
    )
    return world


PLACES = {
    "attic": Place("attic", "the old attic", "the far corner", "the trunk", "A dusty thump echoed above them.", "the floorboards creaked", tags={"attic", "house"}),
    "library": Place("library", "the small library", "the back shelf", "the card catalog", "A hush seemed to answer every breath.", "the ladder wobbled", tags={"library", "quiet"}),
    "basement": Place("basement", "the basement", "the dark corner", "the pipe room", "The sound bounced off the walls.", "the light flickered", tags={"basement", "house"}),
}

CLUES = {
    "key": Clue("key", "a brass key", "A brass key gleamed there", "on the floor", "the trunk", tags={"key", "metal"}),
    "box": Clue("box", "a small box", "A small box sat there", "by the wall", "the card catalog", tags={"box", "wood"}),
    "map": Clue("map", "a torn map", "A torn map fluttered there", "under a book", "the pipe room", tags={"map", "paper"}),
}

WARNINGS = {
    "dont_touch": Warning("dont_touch", "Don't touch it", 3, 1, tags={"warning"}),
    "too_dark": Warning("too_dark", "It looks too dark in there", 3, 1, tags={"warning", "dark"}),
    "strange_sound": Warning("strange_sound", "That sound is strange", 2, 1, tags={"warning", "sound"}),
}

TROUBLES = {
    "locked": Trouble("locked", "locked door", "the door jammed shut with a thud", "The search stopped feeling brave.", tags={"door"}),
    "spill": Trouble("spill", "spill", "a box tipped over and spilled papers everywhere", "The clue slid under the dust and was lost.", tags={"mess"}),
    "fall": Trouble("fall", "fall", "a loose step gave way and made a hard drop", "The mystery turned into a scary scramble.", tags={"stairs"}),
}

GIRL_NAMES = ["Mia", "Luna", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Max", "Finn", "Leo"]
TRAITS = ["curious", "quiet", "careful", "brave", "shy"]


@dataclass
class StoryParams:
    place: str
    clue: str
    warning: str
    trouble: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    adult_type: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the word "clack" and ends badly because the child ignores a warning.',
        f"Tell a cautionary mystery where {f['child'].id} hears a clack in {f['place'].label} and keeps going even after {f['friend'].id} warns {f['child'].pronoun('object')}.",
        f"Write a small, spooky-but-gentle story about a clue in {f['place'].label}, a warning, and a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, place, clue, warning, trouble = (
        f["child"], f["friend"], f["place"], f["clue"], f["warning"], f["trouble"]
    )
    return [
        QAItem(
            question="What kind of story is this?",
            answer=f"It is a mystery story about {child.id} and {friend.id} exploring {place.label}. It turns cautionary because the warning is ignored and the ending goes badly."
        ),
        QAItem(
            question=f"What did {friend.id} warn {child.id} about?",
            answer=f"{friend.id} warned {child.id} not to touch the clue and not to keep following the clack. {friend.id} could tell the dark spot was not safe."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly. {trouble.bad_end} The clue was ruined, and the old place felt empty instead of exciting."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that can help solve a mystery. It might be a key, a note, a track, or another little hint."
        ),
        QAItem(
            question="What does clack mean?",
            answer="Clack is a sharp, hard sound. It can happen when something wooden, metal, or loose clicks against something else."
        ),
        QAItem(
            question="What should you do if a place seems too strange or dark?",
            answer="Stop and call a grown-up. In a mystery, being careful is better than rushing into trouble."
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("attic", "key", "dont_touch", "locked", "Mia", "girl", "Noah", "boy", "mother", "curious"),
    StoryParams("library", "box", "too_dark", "spill", "Ava", "girl", "Eli", "boy", "father", "careful"),
    StoryParams("basement", "map", "strange_sound", "fall", "Theo", "boy", "Luna", "girl", "mother", "shy"),
]


def explain_rejection(place: Place, clue: Clue, warning: Warning, trouble: Trouble) -> str:
    return "(No story: this mystery setup does not create a clear clue-and-warning chain.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for wid in WARNINGS:
        lines.append(asp.fact("warning", wid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,W,T) :- place(P), clue(C), warning(W), trouble(T), clue_ok(P,C), warning_ok(W), trouble_ok(T).
clue_ok(attic,key).
clue_ok(library,box).
clue_ok(basement,map).
warning_ok(dont_touch).
warning_ok(too_dark).
warning_ok(strange_sound).
trouble_ok(locked).
trouble_ok(spill).
trouble_ok(fall).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python gate.")
        rc = 1
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: generation produced empty story.")
        rc = 1
    else:
        print("OK: smoke test story generated.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with a clack and a cautionary bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--adult", choices=["mother", "father"])
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
              and (args.clue is None or c[1] == args.clue)
              and (args.warning is None or c[2] == args.warning)
              and (args.trouble is None or c[3] == args.trouble)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, warning, trouble = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if child_gender == "girl" else "girl"
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend_name = args.friend or rng.choice(BOY_NAMES if friend_gender == "boy" else GIRL_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, clue, warning, trouble, child_name, child_gender, friend_name, friend_gender, adult, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CLUES[params.clue], WARNINGS[params.warning], TROUBLES[params.trouble],
                 params.child_name, params.child_gender, params.friend_name, params.friend_gender, params.adult_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) if isinstance(q, QAItem) else q for q in story_qa(world)],
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible mystery combos:\n")
        for combo in asp_valid_combos():
            print("  ", combo)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child_name}: {p.place} / {p.clue} / {p.trouble}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
