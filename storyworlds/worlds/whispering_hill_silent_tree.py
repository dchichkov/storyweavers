#!/usr/bin/env python3
"""
storyworlds/worlds/whispering_hill_silent_tree.py
=================================================

A standalone storyworld from the seed:

    Words: whispering hill, silent tree
    Features: Lesson Learned
    Style: Animal Story

Source tale written for this world
----------------------------------
Pip the rabbit lived near a whispering hill. Whenever the wind ran through the
grass it went hush-hush-hush, and Pip was sure the hill was telling secrets.
At the top stood a silent tree. It never rustled or waved, even when the other
trees danced.

One day Pip wanted shade for the small animals' picnic. The hill whispered, and
Pip decided the silent tree was being unkind. Old Owl asked Pip to look closer.
The tree's roots were dry and tight under the dusty soil; it was silent because
it needed help, not because it was rude.

Pip carried water in an acorn cup. Drip, drip, drip. The roots softened, the
leaves trembled, and the silent tree gave one gentle rustle. Pip learned that
listening means noticing what someone needs, not only what someone says.

Model shape
-----------
The hill, tree, animal, and help are carriers of physical and emotional state.
Wind embeds "whisper" on the hill; an unmet tree need embeds silence on the
tree; a hurried animal can convert that whisper into misunderstanding. The
story is only valid when the chosen help actually addresses the tree's need.
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "squirrel", "fox"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"mouse", "badger"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Hill:
    id: str
    name: str
    ground: str
    wind: int
    rumor_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TreeNeed:
    id: str
    label: str
    sign: str
    meter: str
    relief: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Help:
    id: str
    label: str
    action: str
    sound: str
    fixes: set[str]
    effort: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Animal:
    id: str
    species: str
    picnic_job: str
    carries: set[str]
    trait: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hill_whispers(world: World) -> list[str]:
    hill = world.get("hill")
    if hill.meters["wind"] < THRESHOLD:
        return []
    sig = ("whisper", hill.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hill.memes["rumor"] += 1
    return ["__whisper__"]


def _r_tree_silent(world: World) -> list[str]:
    tree = world.get("tree")
    if tree.meters["need"] < THRESHOLD:
        return []
    sig = ("silent", tree.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tree.memes["silence"] += 1
    return ["__silent__"]


def _r_misunderstanding(world: World) -> list[str]:
    hill = world.get("hill")
    tree = world.get("tree")
    animal = world.get("animal")
    if hill.memes["rumor"] < THRESHOLD or tree.memes["silence"] < THRESHOLD:
        return []
    if animal.memes["patience"] >= THRESHOLD:
        return []
    sig = ("misunderstanding", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["wrong_focus"] += 1
    return ["__misunderstanding__"]


def _r_recovery(world: World) -> list[str]:
    tree = world.get("tree")
    animal = world.get("animal")
    if tree.meters["helped"] < THRESHOLD:
        return []
    sig = ("recover", tree.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tree.meters["need"] = 0.0
    tree.memes["silence"] = 0.0
    tree.memes["rustle"] += 1
    animal.memes["lesson"] += 1
    animal.memes["kindness"] += 1
    return ["__recover__"]


CAUSAL_RULES = [
    Rule("hill_whispers", "physical", _r_hill_whispers),
    Rule("tree_silent", "physical", _r_tree_silent),
    Rule("misunderstanding", "social", _r_misunderstanding),
    Rule("recovery", "physical", _r_recovery),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def can_help(animal: Animal, need: TreeNeed, help_: Help) -> bool:
    return need.id in help_.fixes and need.id in animal.carries


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for hill_id in HILLS:
        for animal_id, animal in ANIMALS.items():
            for need_id, need in NEEDS.items():
                for help_id, help_ in HELPS.items():
                    if can_help(animal, need, help_):
                        out.append((hill_id, animal_id, need_id, help_id))
    return sorted(out)


def outcome_of(params: "StoryParams") -> str:
    animal, need, help_ = ANIMALS[params.animal], NEEDS[params.need], HELPS[params.help]
    return "learned" if can_help(animal, need, help_) else "unhelped"


def set_scene_state(world: World, hill: Hill, need: TreeNeed) -> None:
    world.get("hill").meters["wind"] = float(hill.wind)
    tree = world.get("tree")
    tree.meters["need"] = 1.0
    tree.meters[need.meter] = 1.0
    propagate(world)


def predict_help(world: World, animal: Animal, need: TreeNeed, help_: Help) -> dict:
    sim = world.copy()
    apply_help(sim, animal, need, help_, narrate=False)
    return {
        "recovers": sim.get("tree").memes["rustle"] >= THRESHOLD,
        "silence": sim.get("tree").memes["silence"],
        "lesson": sim.get("animal").memes["lesson"] >= THRESHOLD,
    }


def apply_help(world: World, animal: Animal, need: TreeNeed, help_: Help,
               narrate: bool = True) -> None:
    if can_help(animal, need, help_):
        world.get("tree").meters["helped"] += 1
    world.get("animal").memes["patience"] += 1
    propagate(world)
    if narrate:
        world.say(f"{help_.sound} {help_.action.format(name=world.get('animal').label)}")


def introduce(world: World, animal: Animal, hill: Hill) -> None:
    a = world.get("animal")
    world.say(
        f"{a.label} the {animal.species} lived near {hill.name}. "
        f"Whenever the wind ran through {hill.ground}, it went hush-hush-hush, "
        f"and {a.label} thought the hill was telling secrets."
    )
    world.say(
        f"At the top stood a silent tree. It never rustled or waved, even when "
        f"the other trees danced."
    )


def desire_and_error(world: World, animal: Animal, hill: Hill, need: TreeNeed) -> None:
    a = world.get("animal")
    tree = world.get("tree")
    if tree.memes["silence"] >= THRESHOLD:
        world.say(
            f"One day {a.label} needed shade for {animal.picnic_job}. "
            f"{hill.rumor_text}, and {a.label} decided the silent tree was being unkind."
        )
    if a.memes["wrong_focus"] >= THRESHOLD:
        world.say(
            f"{a.label} stamped one paw. "
            f'"If you will not talk, maybe you do not care!"'
        )
    world.say(f"Old Owl blinked slowly. \"Look closer,\" she said. \"What does the tree show you?\"")
    a.memes["patience"] += 1
    world.say(f"{a.label} looked at the bark, the roots, and the leaves. {need.sign}")


def help_and_finish(world: World, animal: Animal, need: TreeNeed, help_: Help) -> None:
    a = world.get("animal")
    pred = predict_help(world, animal, need, help_)
    world.facts["prediction"] = pred
    if not pred["recovers"]:
        world.say(
            f"Old Owl shook her head. \"{help_.label.capitalize()} is kind, "
            f"but it does not answer this need.\""
        )
        return
    apply_help(world, animal, need, help_)
    if world.get("tree").memes["rustle"] >= THRESHOLD:
        world.say(
            f"{need.relief}. The silent tree gave one gentle rustle, not loud, "
            f"but grateful."
        )
        world.say(
            f"{a.label} sat in the new shade with the other small animals and "
            "learned that listening means noticing what someone needs, not only "
            "what someone says."
        )


def tell(hill: Hill, animal: Animal, need: TreeNeed, help_: Help,
         name: str) -> World:
    world = World()
    world.add(Entity("animal", "character", animal.species, name, [animal.trait]))
    world.add(Entity("hill", "place", "hill", hill.name))
    world.add(Entity("tree", "thing", "tree", "the silent tree"))
    introduce(world, animal, hill)
    set_scene_state(world, hill, need)
    world.para()
    desire_and_error(world, animal, hill, need)
    world.para()
    help_and_finish(world, animal, need, help_)
    world.facts.update(animal=world.get("animal"), animal_cfg=animal, hill=hill,
                       need=need, help=help_, outcome=outcome_of(
                           StoryParams(hill.id, animal.id, need.id, help_.id, name)))
    return world


HILLS = {
    "whispering_hill": Hill("whispering_hill", "a whispering hill",
                            "the silver grass", 1,
                            "The whispering hill breathed hush-hush through the grass",
                            {"whispering_hill", "wind"}),
    "mossy_hill": Hill("mossy_hill", "the mossy whispering hill",
                       "soft moss and fern", 1,
                       "The mossy hill murmured under the wind",
                       {"whispering_hill", "moss"}),
    "thistle_hill": Hill("thistle_hill", "the thistle hill",
                         "the dry thistles", 1,
                         "The thistles whispered like tiny brooms",
                         {"whispering_hill", "wind"}),
}

NEEDS = {
    "water": TreeNeed("water", "dry roots",
                      "The roots were dry and tight under dusty soil.",
                      "dry", "The roots softened and drank", {"tree", "water"}),
    "untangle": TreeNeed("untangle", "tangled vine",
                         "A scratchy vine had wrapped around the small branches.",
                         "tangled", "The freed branches lifted into the sun",
                         {"tree", "vine"}),
    "mulch": TreeNeed("mulch", "cold roots",
                      "The roots were bare where the chilly wind had scraped the soil away.",
                      "cold", "The covered roots warmed under the soft leaves",
                      {"tree", "soil"}),
}

HELPS = {
    "water_cup": Help("water_cup", "water in an acorn cup",
                      "{name} carried water in an acorn cup and tipped it around the roots.",
                      "Drip, drip, drip.", {"water"}, 1, {"water"}),
    "snip_vine": Help("snip_vine", "careful nibbling",
                      "{name} nibbled the vine loose one tiny bite at a time.",
                      "Nibble, snap, sigh.", {"untangle"}, 1, {"vine"}),
    "leaf_blanket": Help("leaf_blanket", "a blanket of leaves",
                         "{name} tucked a blanket of warm brown leaves over the bare roots.",
                         "Swish, pat, pat.", {"mulch"}, 1, {"leaves", "soil"}),
    "song": Help("song", "a cheerful song",
                 "{name} sang a bright little song to the trunk.",
                 "La-la-la!", {"lonely"}, 1, {"song"}),
}

ANIMALS = {
    "rabbit": Animal("rabbit", "rabbit", "the small animals' picnic",
                     {"water", "mulch"}, "quick", {"rabbit"}),
    "squirrel": Animal("squirrel", "squirrel", "the nut-sharing picnic",
                       {"untangle", "mulch"}, "busy", {"squirrel"}),
    "mouse": Animal("mouse", "mouse", "the berry picnic",
                    {"water", "untangle"}, "careful", {"mouse"}),
    "badger": Animal("badger", "badger", "the moonrise picnic",
                     {"mulch", "water"}, "steady", {"badger"}),
}

NAMES = {
    "rabbit": ["Pip", "Nico", "Bram"],
    "squirrel": ["Tilly", "Hazel", "Nip"],
    "mouse": ["Mina", "Poppy", "Tess"],
    "badger": ["Bessa", "Moss", "Darla"],
}


@dataclass
class StoryParams:
    hill: str
    animal: str
    need: str
    help: str
    name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "whispering_hill": [("Can a hill really whisper?",
                         "A hill cannot talk like a person, but wind moving through grass can make a whispering sound.")],
    "wind": [("What makes grass rustle?",
              "Grass rustles when moving air pushes the blades against each other.")],
    "tree": [("Why might a tree look silent?",
              "A tree may look still when it is dry, tangled, cold, or when there is not enough wind to move its leaves.")],
    "water": [("Why do trees need water?",
               "Trees use water to keep their roots, trunk, and leaves alive. Without enough water, their leaves can droop or stop moving much.")],
    "vine": [("Can vines hurt a small tree?",
              "A heavy vine can wrap around branches and block light, so freeing the branches can help the tree grow.")],
    "soil": [("Why does soil help roots?",
              "Soil covers and protects roots. It can hold water and warmth close to the tree.")],
    "rabbit": [("What do rabbits notice well?",
                "Rabbits often notice small movements and sounds because they have sharp hearing.")],
    "squirrel": [("Why are squirrels good climbers?",
                  "Squirrels have strong claws and quick bodies that help them climb trees and branches.")],
    "mouse": [("Why can a mouse help with tiny problems?",
               "A mouse is small, so it can squeeze close to roots and branches to notice little details.")],
    "badger": [("Why are badgers good diggers?",
                "Badgers have strong paws for moving soil, so they can help cover roots or clear dirt.")],
}
KNOWLEDGE_ORDER = ["whispering_hill", "wind", "tree", "water", "vine", "soil",
                   "rabbit", "squirrel", "mouse", "badger"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["animal"]
    return [
        'Write an animal story that includes "whispering hill" and "silent tree" and ends with a lesson learned.',
        f"Tell a gentle story where {a.label} the {a.type} misunderstands a quiet tree, then helps it with {f['help'].label}.",
        "Write a story about learning to listen for needs instead of believing every whisper.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, hill, need, help_ = f["animal"], f["hill"], f["need"], f["help"]
    pred = f.get("prediction", {})
    recovery = "the tree recovered and rustled again" if pred.get("recovers") else "the tree stayed silent"
    return [
        ("Who is the story about?",
         f"The story is about {a.label}, a {a.traits[0]} {a.type}, Old Owl, and the silent tree on {hill.name}."),
        ("Why did the hill seem to whisper?",
         f"The wind moved through the grass on {hill.name}, making hush-hush sounds. {a.label} mistook that sound for secret talk."),
        ("Why was the tree silent?",
         f"The tree was silent because of {need.label}. {need.sign}"),
        ("How did the animal help?",
         f"{a.label} used {help_.label}. Because that help matched {need.label}, {recovery}."),
        ("What lesson did the animal learn?",
         "The animal learned that listening means noticing what someone needs, not only what someone says. The tree's rustle showed the lesson had changed the world."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["hill"].tags) | set(f["animal_cfg"].tags) | set(f["need"].tags) | set(f["help"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("whispering_hill", "rabbit", "water", "water_cup", "Pip"),
    StoryParams("mossy_hill", "squirrel", "untangle", "snip_vine", "Hazel"),
    StoryParams("thistle_hill", "badger", "mulch", "leaf_blanket", "Bessa"),
]


def explain_rejection(animal: Animal, need: TreeNeed, help_: Help) -> str:
    if need.id not in help_.fixes:
        return f"(No story: {help_.label} does not solve {need.label}; the lesson must come from meeting the tree's real need.)"
    if need.id not in animal.carries:
        return f"(No story: this {animal.species} is not prepared to help with {need.label}; choose an animal whose abilities fit the need.)"
    return "(No story: the animal, need, and help do not form a grounded lesson.)"


ASP_RULES = r"""
can_do(A,N) :- carries(A,N).
fixes_need(H,N) :- fixes(H,N).
valid(Hill,A,N,H) :- hill(Hill), animal(A), need(N), help(H), can_do(A,N), fixes_need(H,N).
outcome(learned) :- chosen_animal(A), chosen_need(N), chosen_help(H), can_do(A,N), fixes_need(H,N).
outcome(unhelped) :- not outcome(learned).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for hid in HILLS:
        lines.append(asp.fact("hill", hid))
    for aid, animal in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        for need in sorted(animal.carries):
            lines.append(asp.fact("carries", aid, need))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    for hid, help_ in HELPS.items():
        lines.append(asp.fact("help", hid))
        for need in sorted(help_.fixes):
            lines.append(asp.fact("fixes", hid, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_animal", params.animal),
        asp.fact("chosen_need", params.need),
        asp.fact("chosen_help", params.help),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: clingo gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("  only clingo:", sorted(cset - pset))
        print("  only python:", sorted(pset - cset))
    cases = list(CURATED)
    parser = build_parser()
    for seed in range(150):
        cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcome cases differ.")
    return rc


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: a whispering hill, a silent tree, and an animal's learned lesson.")
    ap.add_argument("--hill", choices=HILLS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--care", dest="help", choices=HELPS)
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
    if args.animal and args.need and args.help:
        animal, need, help_ = ANIMALS[args.animal], NEEDS[args.need], HELPS[args.help]
        if not can_help(animal, need, help_):
            raise StoryError(explain_rejection(animal, need, help_))
    combos = [c for c in valid_combos()
              if (args.hill is None or c[0] == args.hill)
              and (args.animal is None or c[1] == args.animal)
              and (args.need is None or c[2] == args.need)
              and (args.help is None or c[3] == args.help)]
    if not combos:
        raise StoryError("(No valid whispering-hill story matches the given options.)")
    hill, animal, need, help_ = rng.choice(combos)
    name = args.name or rng.choice(NAMES[ANIMALS[animal].species])
    return StoryParams(hill, animal, need, help_, name)


def generate(params: StoryParams) -> StorySample:
    world = tell(HILLS[params.hill], ANIMALS[params.animal],
                 NEEDS[params.need], HELPS[params.help], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hill, animal, need, help) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:18}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.animal} helps with {p.need} on {p.hill}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
