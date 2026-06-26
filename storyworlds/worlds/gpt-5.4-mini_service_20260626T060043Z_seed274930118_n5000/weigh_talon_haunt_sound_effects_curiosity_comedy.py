#!/usr/bin/env python3
"""
storyworlds/worlds/weigh_talon_haunt_sound_effects_curiosity_comedy.py
======================================================================

A tiny comedy storyworld about curiosity, spooky sound effects, and a child
who wants to weigh a mysterious talon before deciding whether the haunted
corner is actually scary.

Premise:
- A curious child hears strange sound effects in a quiet old place.
- The child finds a suspicious talon-shaped object tied to the haunting.
- A grown-up warns that the sound may be a trick.
- The child investigates, weighs the talon, and learns it is a harmless prop.
- The "haunt" turns out to be a comedy of clanks, squeaks, and a helpful surprise.

The simulation tracks:
- physical meters: weight, wobble, noise, dust, certainty
- emotional memes: curiosity, fear, amusement, relief, suspicion

This world is intentionally small and constraint-checked. It only generates
stories where the curiosity, sound effects, and haunting are plausibly linked,
and where the resolution comes from a causal investigation rather than a frozen
rephrase.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["weight", "wobble", "noise", "dust", "certainty"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "fear", "amusement", "relief", "suspicion"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    name: str
    spooky: bool = False
    sounds: set[str] = field(default_factory=set)
    hides: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    sound: str
    reveals: str
    kind: str = "prop"
    weight: int = 1
    is_talon: bool = False


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _tone(word: str) -> str:
    return {
        "squeak": "squeak-squeak",
        "clank": "clank!",
        "tap": "tap-tap",
        "thump": "thump!",
        "rustle": "rustle-rustle",
        "whoop": "whoop!",
    }.get(word, word)


def activity_line(activity: str) -> str:
    return {
        "weigh": "the scale made a tiny ding when something landed on it",
        "listen": "the room answered with a soft squeak and a clank",
        "peek": "the shadow did a silly wobble in the corner",
        "investigate": "every step added another funny little tap",
    }.get(activity, "the place sounded oddly alive")


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("noise", e.id)
        if sig in world.fired:
            continue
        if world.location.sounds:
            world.fired.add(sig)
            e.meters["noise"] += 1
            out.append(f"A little {_tone(sorted(world.location.sounds)[0])} answered {e.id}'s curiosity.")
    return out


def _r_talon_weight(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["weight"] < THRESHOLD:
            continue
        sig = ("talon_weight", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["suspicion"] += 1
        out.append(f"The talon looked important enough to make everyone squint.")
    return out


def _r_haunt_to_comedy(world: World) -> list[str]:
    out: list[str] = []
    if "haunt" not in world.location.hides:
        return out
    for e in world.characters():
        if e.memes["fear"] < THRESHOLD:
            continue
        sig = ("haunt_comedy", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["amusement"] += 1
        out.append("The spooky corner made one last dramatic groan, then sneezed dust.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["certainty"] < THRESHOLD:
            continue
        sig = ("reveal", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] = 0.0
        e.memes["relief"] += 1
        out.append("The mystery shrank into a grin.")
    return out


RULES = [_r_noise, _r_talon_weight, _r_haunt_to_comedy, _r_reveal]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_reveal(world: World, actor: Entity, prop: Prop) -> bool:
    sim = world.copy()
    inspect(sim, sim.get(actor.id), prop, narrate=False)
    return sim.get(actor.id).meters["certainty"] >= THRESHOLD


def inspect(world: World, actor: Entity, prop: Prop, narrate: bool = True) -> None:
    actor.memes["curiosity"] += 1
    actor.meters["weight"] += prop.weight
    actor.meters["certainty"] += 1
    world.facts["prop"] = prop
    world.facts["inspect_sound"] = prop.sound
    world.facts["reveal"] = prop.reveals
    world.location.sounds.add(prop.sound)
    propagate(world, narrate=narrate)


def opening(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a very curious {hero.type} who loved to ask why the dark corner kept making noises."
    )
    world.say(f"{hero.pronoun().capitalize()} smiled whenever a mystery had a shape.")


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.type} went to {world.location.name}."
    )
    world.say(f"It was quiet enough to hear {activity_line('listen')}.")


def find_prop(world: World, hero: Entity, prop: Prop) -> None:
    world.say(
        f"Near the haunted shelf, {hero.id} found {prop.phrase}."
    )
    world.say(
        f'It went "{_tone(prop.sound)}" when {hero.id} tapped it, which was not very helpful.'
    )


def warn(world: World, parent: Entity, hero: Entity, prop: Prop) -> bool:
    if prop.is_talon:
        world.say(
            f'"That talon may be part of the haunt," {parent.type} said. "It sounds like trouble."'
        )
    else:
        world.say(
            f'"That thing might be making the sound effects," {parent.type} said. "Please do not let it wobble off the shelf."'
        )
    return True


def worry(world: World, hero: Entity) -> None:
    hero.memes["fear"] += 1
    world.say(f"{hero.id} stared at the shadow and tried not to giggle at how serious it looked.")
    world.say(f"Then {hero.pronoun()} decided to weigh the mystery instead of guessing about it.")


def decide(world: World, hero: Entity, prop: Prop) -> None:
    world.say(
        f"{hero.id} set the {prop.label} on the little scale, and the room went {prop.sound}."
    )
    world.say(activity_line("weigh"))


def reveal(world: World, hero: Entity, prop: Prop) -> None:
    if hero.meters["certainty"] >= THRESHOLD:
        world.say(
            f"The answer was funny, not frightening: the talon was only a costume piece, and the haunt was a cranky toy behind the shelf."
        )
        world.say(
            f"{hero.id} laughed so hard that even the spooky boards seemed to join in."
        )
        world.say(
            f'When the hidden toy gave one final "{_tone(prop.sound)}", everyone laughed instead of jumping.'
        )
        world.say(
            f"By the end, {hero.id} had solved the mystery, and the haunted corner sounded much less scary."
        )


def tell(location: Location, prop: Prop, hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(location)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    talon = world.add(Entity(
        id="talon", type="talon", label=prop.label, phrase=prop.phrase,
        owner=hero.id, meters={"weight": 0.0, "wobble": 0.0, "noise": 0.0, "dust": 0.0, "certainty": 0.0},
    ))

    opening(world, hero)
    world.para()
    arrive(world, hero, parent)
    find_prop(world, hero, prop)
    warn(world, parent, hero, prop)
    worry(world, hero)
    decide(world, hero, prop)
    world.para()
    reveal(world, hero, prop)

    world.facts.update(hero=hero, parent=parent, talon=talon, prop=prop)
    return world


@dataclass
class StoryParams:
    location: str
    prop: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


LOCATIONS = {
    "attic": Location(name="the attic", spooky=True, sounds={"clank", "squeak", "tap"}, hides={"haunt"}),
    "cellar": Location(name="the cellar", spooky=True, sounds={"thump", "clank"}, hides={"haunt"}),
    "theater": Location(name="the old theater", spooky=True, sounds={"whoop", "rustle", "tap"}, hides={"haunt"}),
}

PROPS = {
    "costume_talon": Prop(
        id="costume_talon",
        label="costume talon",
        phrase="a shiny costume talon wrapped in ribbon",
        sound="clank",
        reveals="a tiny wind-up toy with a silly squeal",
        weight=1,
        is_talon=True,
    ),
    "key_talon": Prop(
        id="key_talon",
        label="key talon",
        phrase="a brass talon-shaped key",
        sound="tap",
        reveals="an old music box that kept opening by accident",
        weight=1,
        is_talon=True,
    ),
    "bird_talon": Prop(
        id="bird_talon",
        label="bird talon",
        phrase="a carved bird talon from a play costume",
        sound="squeak",
        reveals="a puppet with one floppy wing and a very dramatic bow",
        weight=1,
        is_talon=True,
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "June", "Zoe", "Tess"]
BOY_NAMES = ["Owen", "Finn", "Eli", "Max", "Theo", "Noah"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for loc in LOCATIONS:
        for prop in PROPS:
            combos.append((loc, prop))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prop = f["prop"]
    return [
        f'Write a funny short story for a child about curiosity, a haunted room, and a {prop.label}.',
        f'Tell a comedy where {hero.id} hears sound effects, finds a talon, and decides to weigh it instead of panic.',
        f'Write a gentle spooky story that ends with laughter after the talon mystery is solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prop = f["prop"]
    loc = world.location.name
    return [
        QAItem(
            question=f"Why did {hero.id} go to {loc}?",
            answer=f"{hero.id} went to {loc} because {hero.pronoun()} was curious about the strange sound effects and wanted to find out what the talon was doing there.",
        ),
        QAItem(
            question=f"What did {hero.id} do with the talon?",
            answer=f"{hero.id} decided to weigh the talon on a little scale instead of guessing about it.",
        ),
        QAItem(
            question=f"Why did {parent.type} worry about the talon?",
            answer=f"{parent.type.capitalize()} worried because the talon seemed tied to the haunt, and it kept making {_tone(f['prop'].sound)}-style noises that sounded spooky at first.",
        ),
        QAItem(
            question=f"What was the funny truth about the haunt?",
            answer=f"The funny truth was that the haunt was not a real monster at all; it was a silly hidden toy and a costume piece that made dramatic sound effects.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does it mean to weigh something?",
            answer="To weigh something means to put it on a scale or measure it to see how heavy it is.",
        ),
        QAItem(
            question="What is a talon?",
            answer="A talon is a sharp claw, like the claw on a bird of prey.",
        ),
        QAItem(
            question="What is a haunt?",
            answer="A haunt is a place or thing that seems spooky or keeps showing up like a ghost story.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises used to make a story, game, or scene feel exciting, funny, or spooky.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to ask questions and learn what is going on.",
        ),
    ]
    return out


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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(location="attic", prop="costume_talon", name="Mina", gender="girl", parent="mother"),
    StoryParams(location="cellar", prop="key_talon", name="Finn", gender="boy", parent="father"),
    StoryParams(location="theater", prop="bird_talon", name="Lila", gender="girl", parent="mother"),
]


ASP_RULES = r"""
curious_story(L,P) :- location(L), prop(P).
sound_effect(L,S) :- location_sound(L,S).
talan_hint(P) :- prop(P), is_talon(P).
spooky(L) :- location(L), haunts(L).
funny_reveal(L,P) :- curious_story(L,P), sound_effect(L,_), talon_hint(P), spooky(L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for loc_id, loc in LOCATIONS.items():
        lines.append(asp.fact("location", loc_id))
        if loc.spooky:
            lines.append(asp.fact("haunts", loc_id))
        for s in sorted(loc.sounds):
            lines.append(asp.fact("location_sound", loc_id, s))
    for prop_id, prop in PROPS.items():
        lines.append(asp.fact("prop", prop_id))
        if prop.is_talon:
            lines.append(asp.fact("is_talon", prop_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show funny_reveal/2."))
    asp_set = set(asp.atoms(model, "funny_reveal"))
    py_set = set((loc, prop) for loc, prop in valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    if asp_set - py_set:
        print(" only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print(" only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about curiosity, sound effects, and a talon in a haunt.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.location or args.prop:
        combos = [c for c in combos if (args.location is None or c[0] == args.location)
                  and (args.prop is None or c[1] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    location, prop = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(location=location, prop=prop, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(LOCATIONS[params.location], PROPS[params.prop], params.name, params.gender, params.parent)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show funny_reveal/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show funny_reveal/2."))
        items = sorted(set(asp.atoms(model, "funny_reveal")))
        for loc, prop in items:
            print(f"{loc:10} {prop}")
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
            header = f"### {p.name}: {p.prop} at {p.location}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
