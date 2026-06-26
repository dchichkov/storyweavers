#!/usr/bin/env python3
"""
A small whodunit storyworld with a stiff twist and sound effects.

Seed premise:
- A tidy little mystery in one room
- A detective hears clues as sound effects
- The case turns on a stiff clue that only fits one culprit
- The ending reveals the twist and proves what changed
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    in_room: bool = False
    plural: bool = False
    stiff: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little library"
    tone: str = "quiet"
    echoes: bool = True


@dataclass
class Clue:
    label: str
    phrase: str
    sound: str
    reveals: str
    stiff: bool = False


@dataclass
class Suspect:
    id: str
    type: str
    label: str
    motive: str
    tells: str


@dataclass
class StoryParams:
    setting: str
    detective: str
    culprit: str
    clue: str
    sound: str
    twist: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "library": Setting(place="the little library", tone="quiet", echoes=True),
    "kitchen": Setting(place="the kitchen", tone="busy", echoes=False),
    "museum": Setting(place="the museum hall", tone="hushed", echoes=True),
}

DETECTIVES = {
    "mira": ("girl", "Mira"),
    "noah": ("boy", "Noah"),
    "ivy": ("girl", "Ivy"),
    "sam": ("boy", "Sam"),
}

CULPRITS = {
    "cat": Suspect(id="cat", type="cat", label="the cat", motive="wanted the shiny fish-shaped key", tells="a soft purr"),
    "janitor": Suspect(id="janitor", type="man", label="the janitor", motive="was trying to tidy the hall", tells="dust on his sleeves"),
    "sibling": Suspect(id="sibling", type="girl", label="the older sister", motive="wanted to hide the surprise gift", tells="a ribbon in a pocket"),
}

CLUES = {
    "key": Clue(label="key", phrase="a small brass key", sound="clink", reveals="a locked case"),
    "book": Clue(label="book", phrase="a stiff old book", sound="thump", reveals="a hidden page", stiff=True),
    "box": Clue(label="box", phrase="a narrow cardboard box", sound="tap-tap", reveals="a toy inside"),
}

SOUNDS = {
    "clink": "clink",
    "thump": "thump",
    "tap-tap": "tap-tap",
    "creak": "creak",
    "rustle": "rustle",
}

TWISTS = {
    "stiff": "The stiff clue was not a mistake at all; it was the hidden sign that the object had been swapped earlier.",
    "swap": "The real culprit had swapped one thing for another to cover up the surprise.",
    "lock": "The locked case was opened by the smallest key, not the biggest one.",
}

GENTLE_NAMES = ["Mira", "Noah", "Ivy", "Sam", "Lena", "Finn"]


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------
def valid_story(setting: str, culprit: str, clue: str) -> bool:
    if setting not in SETTINGS or culprit not in CULPRITS or clue not in CLUES:
        return False
    if setting == "kitchen" and clue == "book":
        return False
    if culprit == "cat" and clue == "box":
        return False
    return True


def explain_rejection(setting: str, culprit: str, clue: str) -> str:
    return (
        f"(No story: the combination of {setting!r}, {culprit!r}, and {clue!r} "
        f"does not make a convincing whodunit.)"
    )


# ---------------------------------------------------------------------------
# World narration
# ---------------------------------------------------------------------------
def intro(world: World, detective: Entity, setting: Setting) -> None:
    world.say(
        f"{detective.id} was a little detective who liked quiet rooms and neat clues."
    )
    world.say(
        f"That afternoon, {detective.pronoun('subject')} stepped into {setting.place} "
        f"where every sound seemed to matter."
    )


def scene_of_crime(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["curious"] = detective.memes.get("curious", 0) + 1
    world.say(
        f"Near the front shelf sat {clue.phrase}. When {detective.id} touched it, "
        f"it made a small {clue.sound}."
    )
    if clue.stiff:
        world.say(
            f"It felt stiff in {detective.pronoun('possessive')} hands, like it was hiding a secret."
        )


def hear_sound(world: World, clue: Clue) -> None:
    world.say(
        f"Then another sound answered it: {SOUNDS.get(clue.sound, clue.sound)}."
    )


def question_suspect(world: World, detective: Entity, suspect: Suspect) -> None:
    world.say(
        f"{detective.id} watched {suspect.label} carefully. {suspect.label.capitalize()} had {suspect.tells}, "
        f"but that did not explain the clue."
    )


def twist_turn(world: World, clue: Clue, suspect: Suspect, twist: str) -> None:
    world.say(
        f"At last, {clue.phrase} fit {clue.reveals}. That was the twist: {twist}"
    )
    if clue.stiff:
        world.say(
            f"The stiff edge meant the object had been handled twice, once before the case was opened and once after."
        )


def reveal(world: World, detective: Entity, suspect: Suspect, clue: Clue) -> None:
    detective.memes["certainty"] = 1
    world.say(
        f"{detective.id} solved it. It was {suspect.label} all along, and {detective.pronoun('subject')} had moved the clue to hide the surprise."
    )
    world.say(
        f"In the end, the room was quiet again, and the {clue.label} lay right where it belonged."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    det_type, det_name = DETECTIVES[params.detective]
    detective = world.add(Entity(id=det_name, kind="character", type=det_type, label="detective"))
    suspect = CULPRITS[params.culprit]
    clue = CLUES[params.clue]
    clue_ent = world.add(
        Entity(
            id=clue.label,
            kind="thing",
            type=clue.label,
            label=clue.label,
            phrase=clue.phrase,
            stiff=clue.stiff,
            in_room=True,
        )
    )

    world.facts.update(
        detective=detective,
        suspect=suspect,
        clue=clue_ent,
        clue_spec=clue,
        twist=params.twist,
        setting=setting,
    )

    intro(world, detective, setting)
    world.para()
    scene_of_crime(world, detective, clue)
    hear_sound(world, clue)
    question_suspect(world, detective, suspect)
    world.para()
    twist_turn(world, clue, suspect, TWISTS[params.twist])
    reveal(world, detective, suspect, clue)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S,C,L) :- setting(S), culprit(C), clue(L), ok(S,C,L).
story(S,C,L) :- valid(S,C,L).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CULPRITS:
        lines.append(asp.fact("culprit", cid))
    for lid, clue in CLUES.items():
        lines.append(asp.fact("clue", lid))
        if clue.stiff:
            lines.append(asp.fact("stiff_clue", lid))
    for sid in SETTINGS:
        for cid in CULPRITS:
            for lid in CLUES:
                if valid_story(sid, cid, lid):
                    lines.append(asp.fact("ok", sid, cid, lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((s, c, l) for s in SETTINGS for c in CULPRITS for l in CLUES if valid_story(s, c, l))
    asp_set = asp_valid_combos()
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python only:", sorted(set(py) - set(asp_set)))
    print("asp only:", sorted(set(asp_set) - set(py)))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective: Entity = f["detective"]  # type: ignore[assignment]
    suspect: Suspect = f["suspect"]  # type: ignore[assignment]
    clue: Clue = f["clue_spec"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        f'Write a short whodunit story for a child that includes the word "stiff" and a sound like "{clue.sound}".',
        f"Tell a mystery in {setting.place} where {detective.id} hears {clue.phrase} and notices that {clue.sound} matters.",
        f"Write a simple detective story where {suspect.label} is part of the puzzle and the ending reveals a twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]  # type: ignore[assignment]
    suspect: Suspect = f["suspect"]  # type: ignore[assignment]
    clue: Clue = f["clue_spec"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {detective.id} find {clue.phrase}?",
            answer=f"{detective.id} found {clue.phrase} in {setting.place}, where the clue made a tiny sound.",
        ),
        QAItem(
            question=f"What sound did the clue make?",
            answer=f"The clue made a {clue.sound} sound.",
        ),
        QAItem(
            question=f"Who turned out to be the answer to the mystery?",
            answer=f"It was {suspect.label} all along.",
        ),
        QAItem(
            question=f"Why was the clue important?",
            answer=(
                f"It was important because it revealed {clue.reveals}, and the stiff part showed the clue had been moved before."
                if clue.stiff
                else f"It was important because it revealed {clue.reveals}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = f["clue_spec"]  # type: ignore[assignment]
    suspect: Suspect = f["suspect"]  # type: ignore[assignment]
    items = [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks carefully for clues and tries to figure out what happened.",
        ),
        QAItem(
            question="What does it mean when something is stiff?",
            answer="Something stiff is hard and not bendy.",
        ),
        QAItem(
            question="Why can sound effects help in a mystery story?",
            answer="Sound effects help because they can make clues feel more alive and noticeable.",
        ),
    ]
    if clue.stiff:
        items.append(QAItem(
            question="Why might a stiff object matter in a mystery?",
            answer="A stiff object can be a clue that something was handled, hidden, or swapped.",
        ))
    if suspect.id == "cat":
        items.append(QAItem(
            question="What does a cat often do when it is quiet?",
            answer="A cat may purr or move softly when it is quiet.",
        ))
    return items


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


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with stiff clues and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--detective", choices=DETECTIVES.keys())
    ap.add_argument("--culprit", choices=CULPRITS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--sound", choices=SOUNDS.keys())
    ap.add_argument("--twist", choices=TWISTS.keys())
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
    setting = args.setting or rng.choice(list(SETTINGS))
    detective = args.detective or rng.choice(list(DETECTIVES))
    culprit = args.culprit or rng.choice(list(CULPRITS))
    clue = args.clue or rng.choice(list(CLUES))
    sound = args.sound or CLUES[clue].sound
    twist = args.twist or rng.choice(list(TWISTS))
    if sound != CLUES[clue].sound:
        raise StoryError("The chosen sound must match the chosen clue.")
    if not valid_story(setting, culprit, clue):
        raise StoryError(explain_rejection(setting, culprit, clue))
    return StoryParams(setting=setting, detective=detective, culprit=culprit, clue=clue, sound=sound, twist=twist)


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
        print("--- world trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.stiff:
                bits.append("stiff")
            if e.in_room:
                bits.append("in_room")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="library", detective="mira", culprit="cat", clue="book", sound="thump", twist="stiff"),
    StoryParams(setting="museum", detective="ivy", culprit="sibling", clue="key", sound="clink", twist="swap"),
    StoryParams(setting="kitchen", detective="sam", culprit="janitor", clue="key", sound="clink", twist="lock"),
]


def asp_show_program() -> str:
    return asp_program("#show valid/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combinations:")
        for row in combos:
            print(" ", row)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### story {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
