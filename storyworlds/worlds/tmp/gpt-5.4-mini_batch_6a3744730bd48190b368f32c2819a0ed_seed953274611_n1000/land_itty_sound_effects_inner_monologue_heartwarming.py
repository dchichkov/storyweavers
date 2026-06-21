#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/land_itty_sound_effects_inner_monologue_heartwarming.py
======================================================================================

A tiny heartwarming storyworld about a small child, a lost itty-bitty toy,
a windy landing, and a gentle rescue. The world uses sound effects and inner
monologue as narration instruments, while the simulated state determines the
story's beginning, turn, and ending image.

Seed words: land, itty
Features: Sound Effects, Inner Monologue
Style: Heartwarming
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "mom"}
        male = {"boy", "father", "man", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_type: str
    toy: str
    toy_label: str
    toy_size: str
    toy_sound: str
    weather: str
    seed: Optional[int] = None


@dataclass
class Place:
    id: str
    phrase: str
    landing_spot: str
    landing_sound: str
    landing_help: str
    safe_surf: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    phrase: str
    label: str
    size: str
    sound: str
    can_roll: bool
    can_hide: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperTool:
    id: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


PLACES = {
    "garden": Place(
        id="garden",
        phrase="the garden path",
        landing_spot="the stone edge",
        landing_sound="tap-tap",
        landing_help="soft moss",
        safe_surf=True,
        tags={"land"},
    ),
    "beach": Place(
        id="beach",
        phrase="the beach",
        landing_spot="the warm sand",
        landing_sound="shhff",
        landing_help="smooth sand",
        safe_surf=True,
        tags={"land"},
    ),
    "porch": Place(
        id="porch",
        phrase="the front porch",
        landing_spot="the little porch step",
        landing_sound="click-clack",
        landing_help="a folded towel",
        safe_surf=False,
        tags={"land"},
    ),
}

TOYS = {
    "itty_ball": Toy(
        id="itty_ball",
        phrase="an itty-bitty ball",
        label="itty ball",
        size="itty",
        sound="boing",
        can_roll=True,
        can_hide=False,
        tags={"itty"},
    ),
    "itty_cat": Toy(
        id="itty_cat",
        phrase="an itty plush cat",
        label="itty cat",
        size="itty",
        sound="mew",
        can_roll=False,
        can_hide=True,
        tags={"itty"},
    ),
    "itty_robot": Toy(
        id="itty_robot",
        phrase="an itty robot",
        label="itty robot",
        size="itty",
        sound="beep-beep",
        can_roll=True,
        can_hide=True,
        tags={"itty"},
    ),
}

TOOLS = {
    "gentle_hands": HelperTool("gentle_hands", "gentle hands", "carefully pick up the toy", {"help"}),
    "lantern": HelperTool("lantern", "a little lantern", "shine on the path", {"light"}),
    "basket": HelperTool("basket", "a small basket", "carry the toy safely", {"carry"}),
}

SOUNDWORDS = ["tap-tap", "shhh", "whoop", "plink", "boing", "beep-beep"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in PLACES.values():
        for toy in TOYS.values():
            if place.safe_surf or toy.can_roll or toy.can_hide:
                out.append((place.id, toy.id))
    return out


def make_story(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.toy not in TOYS:
        raise StoryError("Unknown toy.")
    place = PLACES[params.place]
    toy = TOYS[params.toy]
    if not toy.size == "itty":
        raise StoryError("This world only tells itty stories.")
    world = World(place)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="the parent", role="parent"))
    toy_ent = world.add(Entity(id="toy", type="toy", label=toy.label, role="lost toy"))
    child.memes["worry"] += 1
    child.memes["love"] += 1

    world.say(
        f"On a breezy day, {child.id} and {helper.id} went to {place.phrase} with {toy.phrase} in a little pocket."
    )
    world.say(
        f"{child.id} loved {toy.label}, because it was so small and dear. "
        f'In {child.id}\'s head, a tiny thought kept whispering, "Please do not lose it."'
    )

    world.para()
    world.say(
        f"Then {toy.sound}! The {toy.label} slipped from {child.id}'s hand and landed near {place.landing_spot}."
    )
    toy_ent.meters["lost"] += 1
    toy_ent.meters["distance"] += 1
    child.memes["panic"] += 1
    child.memes["worry"] += 1
    world.say(f'\"Oh no,\" {child.id} thought. \"I must get it back before the wind moves it away.\"')

    world.para()
    if place.safe_surf:
        world.say(
            f"{helper.id} stepped closer and said, \"Easy now.\" {helper.id} reached with gentle hands, "
            f"and {toy.label} came home with a soft {place.landing_sound}."
        )
        toy_ent.meters["lost"] = 0
        toy_ent.meters["found"] += 1
        child.memes["relief"] += 1
        helper.memes["pride"] += 1
        world.say(
            f"{child.id} let out a shaky laugh. \"I-itty little toy, safe with me again,\" {child.id} thought, "
            f"feeling warm and brave."
        )
    else:
        world.say(
            f"{helper.id} saw that the step was a little tricky. {helper.id} brought {TOOLS['basket'].phrase} "
            f"and {TOOLS['gentle_hands'].phrase} together, so nobody had to rush."
        )
        world.say(
            f"With a careful scoop, the {toy.label} landed safely in the basket, and {place.landing_help} kept it from sliding."
        )
        toy_ent.meters["lost"] = 0
        toy_ent.meters["found"] += 1
        child.memes["relief"] += 1
        helper.memes["care"] += 1
        world.say(
            f'{child.id} thought, "We can be slow and still be kind." Then {child.id} smiled at {helper.id}.'
        )

    world.para()
    parent.memes["love"] += 1
    world.say(
        f"That evening, {parent.label_word.capitalize()} tucked {child.id} close and said, "
        f"\"You did well asking for help. Little things matter when they are beloved.\""
    )
    world.say(
        f"{child.id} held up the {toy.label}, safe again, and listened to it go {toy.sound} in a happy little squeeze."
    )

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        toy=toy,
        toy_ent=toy_ent,
        place=place,
        weather=params.weather,
    )
    return world


def _predict_outcome(world: World, place_id: str, toy_id: str) -> dict:
    sim = world.copy()
    toy = sim.get("toy")
    place = sim.place
    toy.meters["lost"] += 1
    safe = place.safe_surf
    if safe:
        toy.meters["found"] += 1
    return {"found": toy.meters["found"] >= THRESHOLD, "safe": safe}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "land" and "itty".',
        f"Tell a gentle story where {f['child'].id} loses an itty toy and gets it back with help, with a soft ending image.",
        f"Write a small heartwarming rescue story with sound effects and a worried inner thought, then a comforting ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, parent, toy, place = f["child"], f["helper"], f["parent"], f["toy"], f["place"]
    return [
        QAItem(
            question=f"What happened when the toy slipped away?",
            answer=(
                f"It landed near {place.landing_spot}, and {child.id} worried that the wind would take it farther away. "
                f"That is why the moment felt so urgent."
            ),
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=(
                f"{helper.id} moved gently and helped bring the toy back safely. "
                f"The careful way mattered because the toy was tiny and easy to lose again."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"The toy was safe again, and {child.id} felt warm and relieved. "
                f"The ending proves that asking for help turned a nervous moment into a kind one."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something lands?",
            answer="When something lands, it comes down and touches the ground or another surface. That is what happened when the little toy slipped away.",
        ),
        QAItem(
            question="Why do tiny things need careful hands?",
            answer="Tiny things can be easy to drop, hide, or lose. Careful hands help keep them safe.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word that lets you almost hear the moment, like tap-tap, boing, or beep-beep. It makes the scene feel alive.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        child_name="Mia",
        child_gender="girl",
        helper_name="Noah",
        helper_gender="boy",
        parent_type="mother",
        toy="itty_ball",
        toy_label="itty ball",
        toy_size="itty",
        toy_sound="boing",
        weather="breezy",
    ),
    StoryParams(
        place="porch",
        child_name="Leo",
        child_gender="boy",
        helper_name="Ava",
        helper_gender="girl",
        parent_type="father",
        toy="itty_cat",
        toy_label="itty cat",
        toy_size="itty",
        toy_sound="mew",
        weather="windy",
    ),
    StoryParams(
        place="beach",
        child_name="Luna",
        child_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent_type="mother",
        toy="itty_robot",
        toy_label="itty robot",
        toy_size="itty",
        toy_sound="beep-beep",
        weather="sunny",
    ),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this combination doesn't fit the tiny, heartwarming landing-and-finding premise.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny heartwarming storyworld with sound effects and inner monologue.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--toy", choices=sorted(TOYS))
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--parent", dest="parent_type", choices=["mother", "father"])
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
              and (args.toy is None or c[1] == args.toy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, toy = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if child_gender == "girl" else "girl"
    child_name = args.child_name or rng.choice(["Mia", "Leo", "Luna", "Noah", "Ari", "Ruby"])
    helper_name = args.helper_name or rng.choice(["Ava", "Ben", "Ivy", "Jules", "Nia", "Theo"])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    if child_name == helper_name:
        helper_name = helper_name + "y"
    toy_obj = TOYS[toy]
    return StoryParams(
        place=place,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent_type=parent_type,
        toy=toy,
        toy_label=toy_obj.label,
        toy_size=toy_obj.size,
        toy_sound=toy_obj.sound,
        weather="windy",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.toy not in TOYS:
        raise StoryError("Unknown toy.")
    world = make_story(params)
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


ASP_RULES = r"""
place(P) :- place_fact(P).
toy(T) :- toy_fact(T).
valid(P,T) :- place(P), toy(T), safe_surface(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_fact", p))
    for t in TOYS:
        lines.append(asp.fact("toy_fact", t))
    for p, place in PLACES.items():
        if place.safe_surf:
            lines.append(asp.fact("safe_surface", p))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAIL: generate() smoke test crashed: {e}")
        ok = False
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches valid_combos() ({len(python_set)} combos).")
    else:
        ok = False
        print("MISMATCH between ASP and Python gates.")
        if asp_set - python_set:
            print("  only in asp:", sorted(asp_set - python_set))
        if python_set - asp_set:
            print("  only in python:", sorted(python_set - asp_set))
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for p, t in asp_valid_combos():
            print(f"  {p:8} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
