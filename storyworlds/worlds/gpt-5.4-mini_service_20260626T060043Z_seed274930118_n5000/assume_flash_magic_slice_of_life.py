#!/usr/bin/env python3
"""
storyworlds/worlds/assume_flash_magic_slice_of_life.py
======================================================

A small slice-of-life story world about a child who makes an assumption after a
flash of magic, then discovers the ordinary, helpful truth underneath it.

Seed premise:
- A child sees a flash and assumes something has gone wrong.
- The flash is actually a tiny piece of everyday magic.
- The family uses that magic to make a small home moment easier, kinder, or
  tidier.

The world is deliberately modest: one cozy setting, a few gentle activities,
and a small magical helper object. The story turns on mistaken assumption,
clarification, and a quiet resolution that changes the room's state.
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    magical: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    surprise: str
    risk: str
    resolution: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    helps: set[str]
    shines: str
    outcome: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_flash(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.magical and e.meters.get("spark", 0.0) >= THRESHOLD:
            sig = ("flash", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["glow"] = e.meters.get("glow", 0.0) + 1
            out.append(f"A small flash of light danced from {e.label}.")
    return out


def _r_tidy_magic(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.magical and e.meters.get("glow", 0.0) < THRESHOLD:
            continue
        if e.kind != "thing":
            continue
        if e.meters.get("messy", 0.0) < THRESHOLD:
            continue
        sig = ("tidy", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["messy"] = 0.0
        e.meters["clean"] = 1.0
        out.append(f"The little magic whisked {e.label} clean again.")
    return out


def _r_reassure(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    helper = next((e for e in world.characters() if e.type in {"mother", "father", "grandmother", "grandfather"}), None)
    if not child or not helper:
        return out
    if child.memes.get("worry", 0.0) < THRESHOLD or helper.memes.get("calm", 0.0) < THRESHOLD:
        return out
    sig = ("reassure", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    out.append(f"{helper.label} smiled and explained that the flash was only helpful magic.")
    return out


CAUSAL_RULES = [
    Rule("flash", _r_flash),
    Rule("tidy_magic", _r_tidy_magic),
    Rule("reassure", _r_reassure),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "kitchen": Setting(place="the kitchen", mood="cozy", affords={"tea", "breakfast", "tidy"}),
    "living_room": Setting(place="the living room", mood="quiet", affords={"tidy", "reading"}),
    "laundry": Setting(place="the laundry room", mood="busy", affords={"folding", "tidy"}),
}

ACTIVITIES = {
    "tea": Activity(
        id="tea",
        verb="make tea",
        gerund="making tea",
        surprise="the kettle gave a bright flash",
        risk="the child assumed something had broken",
        resolution="they found the flash was just magic warming the water",
        effect="the cups filled with steam",
        tags={"steam", "kitchen"},
    ),
    "breakfast": Activity(
        id="breakfast",
        verb="set the breakfast table",
        gerund="setting the breakfast table",
        surprise="the spoon gave a tiny flash",
        risk="the child assumed the spoon had vanished",
        resolution="the flash was magic finding the missing spoon",
        effect="the table looked ready and neat",
        tags={"food", "table"},
    ),
    "tidy": Activity(
        id="tidy",
        verb="tidy the room",
        gerund="tidying the room",
        surprise="the broom gave a bright flash",
        risk="the child assumed the room would stay messy forever",
        resolution="the flash was magic gathering crumbs and ribbons",
        effect="the floor turned clear and calm",
        tags={"clean", "home"},
    ),
    "reading": Activity(
        id="reading",
        verb="read a story nook by nook",
        gerund="reading quietly",
        surprise="the lamp gave a soft flash",
        risk="the child assumed the lamp was broken",
        resolution="the flash was magic making the page glow",
        effect="the corner looked warm and bright",
        tags={"book", "lamp"},
    ),
    "folding": Activity(
        id="folding",
        verb="fold laundry",
        gerund="folding laundry",
        surprise="the basket gave a silver flash",
        risk="the child assumed the socks had disappeared again",
        resolution="the flash was magic pairing the socks together",
        effect="the basket felt less full",
        tags={"cloth", "socks"},
    ),
}

CHARMS = {
    "sparkle_spoon": Charm(
        id="sparkle_spoon",
        label="a little sparkle spoon",
        phrase="a tiny silver spoon that liked to shine",
        helps={"breakfast"},
        shines="It flashed when it found lost things.",
        outcome="the spoon showed where the missing thing was hiding",
    ),
    "steam_kettle": Charm(
        id="steam_kettle",
        label="the old tea kettle",
        phrase="an old kettle with a warm humming lid",
        helps={"tea"},
        shines="It flashed when the water was ready.",
        outcome="the kettle turned the room cozy and bright",
    ),
    "dust_broom": Charm(
        id="dust_broom",
        label="the broom with a blue ribbon",
        phrase="a broom tied with a blue ribbon",
        helps={"tidy"},
        shines="It flashed when it gathered crumbs.",
        outcome="the broom swept the mess into one neat little pile",
    ),
    "glow_lamp": Charm(
        id="glow_lamp",
        label="the reading lamp",
        phrase="a lamp with a glass shade",
        helps={"reading"},
        shines="It flashed when a page needed light.",
        outcome="the lamp made the book corner glow",
    ),
    "pairing_basket": Charm(
        id="pairing_basket",
        label="the laundry basket",
        phrase="a woven basket with a patient handle",
        helps={"folding"},
        shines="It flashed when socks wanted a partner.",
        outcome="the basket helped the socks find their matches",
    ),
}

CHILD_NAMES = ["Mina", "Owen", "Tia", "Jun", "Ivy", "Sam"]
HELPER_NAMES = ["Mom", "Dad", "Nana", "Papa"]
TRAITS = ["curious", "gentle", "sleepy", "helpful", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    charm: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for charm_id, charm in CHARMS.items():
                if act in charm.helps:
                    out.append((place, act, charm_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with a tiny flash of magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, charm = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        charm=charm,
        name=args.name or rng.choice(CHILD_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        trait=rng.choice(TRAITS),
    )


def _build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    charm = CHARMS[params.charm]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Tia", "Ivy"} else "boy", label=params.name))
    helper = world.add(Entity(id=params.helper, kind="character", type="mother" if params.helper == "Mom" else "father" if params.helper == "Dad" else "grandmother" if params.helper == "Nana" else "grandfather", label=params.helper))
    item = world.add(Entity(id="charm", type="thing", label=charm.label, phrase=charm.phrase, owner=helper.id, magical=True))
    item.meters["spark"] = 1.0
    child.memes["worry"] = 1.0
    helper.memes["calm"] = 1.0
    world.facts.update(child=child, helper=helper, item=item, activity=activity, charm=charm, params=params)
    return world


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    item: Entity = f["item"]
    activity: Activity = f["activity"]
    charm: Charm = f["charm"]

    world.say(f"{child.label} was a {f['params'].trait} child who liked small, quiet mornings in {world.setting.place}.")
    world.say(f"One day, {child.label} and {helper.label} were {activity.gerund}.")
    world.say(f"Then {activity.surprise}, and {child.label} assumed {activity.risk}.")
    world.say(f"{helper.label} looked over and gently held up {item.label}.")
    world.say(f"{charm.shines} {charm.outcome}.")

    world.para()
    child.memes["worry"] += 1
    helper.memes["calm"] += 1
    world.say(f"{child.label} blinked at the flash, then listened while {helper.label} explained, \"It was only magic helping us {activity.verb}.\"")
    propagate(world)
    world.say(f"So they kept going, and {activity.effect}.")

    if activity.id == "tea":
        world.say(f"At the end, the warm cups sat on the table, and the kitchen smelled sweet and calm.")
    elif activity.id == "breakfast":
        world.say(f"At the end, the spoons were ready, and breakfast looked simple and bright.")
    elif activity.id == "tidy":
        world.say(f"At the end, the floor shone softly, and the room felt easier to breathe in.")
    elif activity.id == "reading":
        world.say(f"At the end, the page glowed in the corner, and the story felt cozy.")
    elif activity.id == "folding":
        world.say(f"At the end, the socks were paired up, and the basket looked much friendlier.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    activity: Activity = f["activity"]
    return [
        f'Write a gentle slice-of-life story for young children that includes the word "flash" and a tiny bit of magic.',
        f"Tell a cozy story where {params.name} assumes the flash means trouble, but {params.helper} explains it during {activity.gerund}.",
        f'Write a short home story about a child, an assumption, and a helpful magic flash while {activity.verb}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    activity: Activity = f["activity"]
    helper: Entity = f["helper"]
    child: Entity = f["child"]
    charm: Charm = f["charm"]
    return [
        QAItem(
            question=f"What did {params.name} assume when the flash happened?",
            answer=f"{params.name} assumed {activity.risk}. That is why {params.name} looked worried at first.",
        ),
        QAItem(
            question=f"Who explained the flash to {params.name}?",
            answer=f"{helper.label} explained that the flash was helpful magic, not a problem.",
        ),
        QAItem(
            question=f"What was the magical object in the story?",
            answer=f"It was {charm.phrase}. {charm.shines}",
        ),
        QAItem(
            question=f"How did {params.name} feel after the explanation?",
            answer=f"{params.name} felt relieved and kept helping with {activity.gerund}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The room became calmer and {activity.effect.lower()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flash?",
            answer="A flash is a very quick burst of light that you notice in a moment and then it is gone.",
        ),
        QAItem(
            question="What does magic mean in a story like this?",
            answer="In a story like this, magic is a special helpful thing that can make ordinary moments feel a little brighter or easier.",
        ),
        QAItem(
            question="What is a slice-of-life story?",
            answer="A slice-of-life story is about a small everyday moment, like making tea, folding clothes, or tidying a room.",
        ),
    ]


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


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    tell(world)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.magical:
            bits.append("magical=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="tea", charm="steam_kettle", name="Mina", helper="Mom", trait="curious"),
    StoryParams(place="kitchen", activity="breakfast", charm="sparkle_spoon", name="Jun", helper="Dad", trait="thoughtful"),
    StoryParams(place="living_room", activity="reading", charm="glow_lamp", name="Ivy", helper="Nana", trait="gentle"),
    StoryParams(place="living_room", activity="tidy", charm="dust_broom", name="Sam", helper="Papa", trait="helpful"),
    StoryParams(place="laundry", activity="folding", charm="pairing_basket", name="Tia", helper="Mom", trait="sleepy"),
]


ASP_RULES = r"""
% A tiny story is valid when the activity is supported by the place and the charm helps it.
valid(Place, Activity, Charm) :- affords(Place, Activity), helps(Charm, Activity).

% Magic flash is a visible cue when the charm is activated.
flash(Charm) :- charm(Charm).

% The assumption-turn exists in every valid story world.
assume_turn(Place, Activity, Charm) :- valid(Place, Activity, Charm), flash(Charm).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for a in sorted(c.helps):
            lines.append(asp.fact("helps", cid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_assume_turns() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show assume_turn/3."))
    return sorted(set(asp.atoms(model, "assume_turn")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between ASP and Python valid_combos():")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        return 1
    print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    return 0


def explain_rejection(place: str, activity: str, charm: str) -> str:
    return f"(No story: {charm} does not help with {activity} in {place}, so the flash would not make a believable slice-of-life turn.)"


def explain_combo(args: argparse.Namespace) -> None:
    if args.place and args.activity and args.charm:
        if (args.place, args.activity, args.charm) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.activity, args.charm))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show assume_turn/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                explain_combo(args)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
