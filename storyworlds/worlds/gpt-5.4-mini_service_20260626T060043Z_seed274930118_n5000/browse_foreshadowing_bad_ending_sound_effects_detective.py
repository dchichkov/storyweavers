#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/browse_foreshadowing_bad_ending_sound_effects_detective.py
================================================================================================

A small detective storyworld built from the seed word "browse".

Premise:
- A young detective browses a dusty place for a missing object.
- Small clues create foreshadowing: odd sounds, hints of a wrong path, and a suspicious gap.
- The detective follows the clues, but the ending turns out bad: the lead is false, the item stays lost, and the final image proves the loss.

This world is intentionally narrow. It prefers a few strong, plausible stories over many weak ones.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class MeteredEntity:
    id: str
    kind: str
    label: str
    phrase: str
    owner: Optional[str] = None
    located_in: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Character(MeteredEntity):
    pronoun_subject: str = "they"
    pronoun_object: str = "them"
    pronoun_possessive: str = "their"


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class ObjectItem(MeteredEntity):
    breakable: bool = False
    small: bool = False


@dataclass
class StoryParams:
    place: str
    detective: str
    object: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "library": Place(
        id="library",
        label="library",
        phrase="the old library",
        affordances={"browse", "search"},
    ),
    "antique_shop": Place(
        id="antique_shop",
        label="antique shop",
        phrase="the antique shop",
        affordances={"browse", "search"},
    ),
    "station_lost_and_found": Place(
        id="station_lost_and_found",
        label="lost-and-found desk",
        phrase="the station lost-and-found desk",
        affordances={"browse", "search"},
    ),
}

DETECTIVES = {
    "Mina": {"kind": "child", "label": "Mina", "phrase": "a small detective girl"},
    "Noah": {"kind": "child", "label": "Noah", "phrase": "a small detective boy"},
    "June": {"kind": "child", "label": "June", "phrase": "a small detective"},
}

HELPERS = {
    "cat": {"kind": "animal", "label": "cat", "phrase": "a quiet tabby cat"},
    "uncle": {"kind": "adult", "label": "uncle", "phrase": "a patient uncle"},
    "clerk": {"kind": "adult", "label": "clerk", "phrase": "a kind clerk"},
}

OBJECTS = {
    "red_button": ObjectItem(
        id="red_button",
        kind="object",
        label="red button",
        phrase="a tiny red button",
        breakable=True,
        small=True,
    ),
    "brass_key": ObjectItem(
        id="brass_key",
        kind="object",
        label="brass key",
        phrase="a brass key with a bent tooth",
        breakable=False,
        small=True,
    ),
    "blue_notebook": ObjectItem(
        id="blue_notebook",
        kind="object",
        label="blue notebook",
        phrase="a blue notebook with a torn corner",
        breakable=True,
        small=False,
    ),
}

SOUND_WORDS = ["creak", "tap", "rustle", "clink", "thump", "shuffle"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, MeteredEntity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: MeteredEntity) -> MeteredEntity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> MeteredEntity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world trace ---"]
        for e in self.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            if e.located_in:
                bits.append(f"located_in={e.located_in}")
            lines.append(f"  {e.id} ({e.kind}) {' '.join(bits)}")
        lines.append(f"  facts={self.facts}")
        return "\n".join(lines)


def _pronouns(label: str) -> tuple[str, str, str]:
    if label in {"Mina", "June"}:
        return "she", "her", "her"
    if label == "Noah":
        return "he", "him", "his"
    return "they", "them", "their"


def foreshadow_sound(world: World, sound: str, source: str) -> None:
    world.say(f"{source} went {sound} in the quiet room.")
    world.facts.setdefault("sounds", []).append(sound)


def browse_for_clue(world: World, detective: Character, place: Place, obj: ObjectItem) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    world.say(
        f"{detective.label} browsed the shelves at {place.phrase} with a magnifying glass and a frown."
    )
    world.say(
        f"Every card and corner looked important, but {detective.pronoun_possessive} eyes kept returning to the missing {obj.label}."
    )


def foreshadow(world: World, detective: Character, helper: MeteredEntity, obj: ObjectItem) -> None:
    world.say(
        f"Then the floor gave a soft creak, and a loose drawer made a tiny clink."
    )
    world.say(
        f"{helper.label if helper.kind != 'animal' else 'The cat'} stared at one shelf as if it already knew something bad."
    )
    world.facts["foreshadowed"] = True
    world.facts["wrong_shelf"] = True


def investigate(world: World, detective: Character, helper: MeteredEntity, obj: ObjectItem) -> None:
    detective.meters["steps"] = detective.meters.get("steps", 0) + 3
    detective.memes["hope"] = detective.memes.get("hope", 0) + 1
    world.say(
        f"{detective.label} followed the clue, and {helper.label if helper.kind != 'animal' else 'the cat'} padded after {detective.pronoun_object}."
    )
    world.say(
        f"Tap, tap, tap went the shoes on the wooden boards while {detective.label} checked the wrong shelf first."
    )
    world.say(
        f"The clue looked shiny, but it was only an old tag, and the missing {obj.label} was not there."
    )


def bad_ending(world: World, detective: Character, helper: MeteredEntity, obj: ObjectItem) -> None:
    detective.memes["disappointment"] = detective.memes.get("disappointment", 0) + 2
    detective.memes["hope"] = 0
    world.say(
        f"At last, the last light clicked off with a dull thump, and the room felt even smaller."
    )
    world.say(
        f"{detective.label} went home with empty hands, while the missing {obj.label} stayed missing."
    )
    world.say(
        f"Outside, the wind whispered past the window, and the case was still unsolved."
    )
    world.facts["resolved"] = False


def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    det_name = params.detective
    det_role = DETECTIVES[det_name]
    subj, objp, poss = _pronouns(det_name)
    detective = world.add(
        Character(
            id="detective",
            kind=det_role["kind"],
            label=det_name,
            phrase=det_role["phrase"],
            pronoun_subject=subj,
            pronoun_object=objp,
            pronoun_possessive=poss,
        )
    )
    helper_cfg = HELPERS[params.helper]
    helper = world.add(
        MeteredEntity(
            id="helper",
            kind=helper_cfg["kind"],
            label=params.helper,
            phrase=helper_cfg["phrase"],
        )
    )
    obj_cfg = OBJECTS[params.object]
    obj = world.add(
        ObjectItem(
            id="object",
            kind="object",
            label=obj_cfg.label,
            phrase=obj_cfg.phrase,
            breakable=obj_cfg.breakable,
            small=obj_cfg.small,
        )
    )

    world.facts.update(
        place=place.id,
        detective=det_name,
        helper=params.helper,
        object=params.object,
        browse="browse",
    )

    world.say(
        f"{detective.label} was {det_role['phrase']} who liked to browse for clues in quiet places."
    )
    world.say(
        f"{detective.label} was trying to find {obj.phrase}, which had gone missing that morning."
    )
    world.say(
        f"{helper_cfg['label'].capitalize()} stayed close, because the room had a strange feeling."
    )

    world.para()
    browse_for_clue(world, detective, place, obj)
    foreshadow_sound(world, "creak", "A back shelf")
    foreshadow_sound(world, "clink", "A loose drawer")
    foreshadow(world, detective, helper, obj)

    world.para()
    investigate(world, detective, helper, obj)
    foreshadow_sound(world, "tap", "The detective's shoes")
    foreshadow_sound(world, "rustle", "A stack of papers")
    world.say(
        f"{detective.label} lifted a box, but it held only old receipts and dust."
    )

    world.para()
    bad_ending(world, detective, helper, obj)

    world.facts["detective_label"] = detective.label
    world.facts["helper_label"] = helper.label
    world.facts["object_label"] = obj.label
    world.facts["place_phrase"] = place.phrase
    return world


def tell_story(params: StoryParams) -> StorySample:
    world = make_world(params)
    story = world.render()
    prompts = [
        f"Write a short detective story where someone browses {world.place.phrase} for a missing object.",
        f"Tell a child-friendly mystery with foreshadowing, sound effects, and a bad ending.",
        f"Write a tiny story about a detective who keeps browsing for clues but never solves the case.",
    ]
    story_qa = [
        QAItem(
            question=f"What was {world.facts['detective_label']} doing at {world.place.phrase}?",
            answer=f"{world.facts['detective_label']} was browsing for clues and searching for {world.facts['object_label']}.",
        ),
        QAItem(
            question=f"What sound first hinted that something was wrong?",
            answer="A soft creak and a small clink hinted that the place was hiding something important.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended badly, because the detective went home without finding the missing object.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does it mean to browse?",
            answer="To browse means to look through things carefully, often by moving from one item or shelf to the next.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints something important may happen later.",
        ),
        QAItem(
            question="Why can sound effects make a mystery feel stronger?",
            answer="Sound effects like creak, tap, and clink help a reader imagine the place and feel the tension in the scene.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_story(params)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld about browsing, foreshadowing, sound effects, and a bad ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--detective", choices=sorted(DETECTIVES))
    ap.add_argument("--object", choices=sorted(OBJECTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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
    place = args.place or rng.choice(sorted(PLACES))
    detective = args.detective or rng.choice(sorted(DETECTIVES))
    obj = args.object or rng.choice(sorted(OBJECTS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(place=place, detective=detective, object=obj, helper=helper)


ASP_RULES = r"""
place(P) :- setting(P).
detective(D) :- character(D).
object(O) :- item(O).
helper(H) :- companion(H).

browse_scene(P,D,O,H) :- setting(P), detective(D), object(O), helper(H).
foreshadowing(P,D,O) :- browse_scene(P,D,O,_), clue_sound(P), missing(O).
bad_ending(P,D,O) :- foreshadowing(P,D,O), unsolved(P,D,O).

#show browse_scene/4.
#show foreshadowing/3.
#show bad_ending/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(p.affordances):
            lines.append(asp.fact("affords", pid, a))
    for d in DETECTIVES:
        lines.append(asp.fact("character", d))
    for h in HELPERS:
        lines.append(asp.fact("companion", h))
    for o in OBJECTS:
        lines.append(asp.fact("item", o))
        lines.append(asp.fact("missing", o))
    for s in SOUND_WORDS:
        lines.append(asp.fact("clue_sound", s))
    lines.append(asp.fact("unsolved", "library", "Mina", "red_button"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    ok = any(a == ("browse_scene", 4) for a in atoms) and any(a == ("foreshadowing", 3) for a in atoms)
    if ok:
        print("OK: ASP twin produces the expected detective shapes.")
        return 0
    print("MISMATCH: ASP twin did not produce expected atoms.")
    return 1


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="library", detective="Mina", object="red_button", helper="cat"),
    StoryParams(place="antique_shop", detective="Noah", object="brass_key", helper="uncle"),
    StoryParams(place="station_lost_and_found", detective="June", object="blue_notebook", helper="clerk"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import storyworlds.asp as asp
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
