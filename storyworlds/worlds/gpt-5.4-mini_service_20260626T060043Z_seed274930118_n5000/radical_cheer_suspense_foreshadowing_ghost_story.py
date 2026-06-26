#!/usr/bin/env python3
"""
storyworlds/worlds/radical_cheer_suspense_foreshadowing_ghost_story.py
=======================================================================

A small, standalone ghost-story world with suspense and foreshadowing.

Premise:
A brave child goes into a spooky place to find a missing keepsake.
The place seems haunted, but the clues keep hinting that the "ghost"
is really lonely and trying to lead the child toward the truth.

Turn:
Creaks, whispers, and cold spots build suspense. Foreshadowing shows
up as soft light, a half-seen ribbon, and a repeated tune that matters
later.

Resolution:
The child uses a radical cheer -- a bold, silly, heartening chant --
to break the fear spell, help the ghost feel seen, and recover the lost
item.

The story stays child-facing and concrete, with a state-driven simulation
that changes meters and memes as the tale unfolds.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    hidden: bool = False

    def __post_init__(self) -> None:
        for k in ("dust", "cold", "moved", "found"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "curiosity", "hope", "loneliness", "cheer", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    eerie: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    location: str
    sound: str
    glow: str
    cherished: bool = True


@dataclass
class Ghost:
    id: str
    label: str
    style: str
    clue: str
    tune: str
    reason: str
    can_help: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.ambient: dict[str, float] = {"suspense": 0.0, "foreshadowing": 0.0}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.ambient = dict(self.ambient)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_cold_spot(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["fear"] < THRESHOLD:
            continue
        sig = ("cold", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["cold"] += 1
        world.ambient["suspense"] += 0.5
        out.append(f"A cold breeze curled around {ent.id}'s ankles.")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    relic = world.facts.get("relic")
    ghost = world.facts.get("ghost")
    if not relic or not ghost:
        return out
    sig = ("foreshadow", relic.id, ghost.id)
    if sig in world.fired:
        return out
    if world.ambient["suspense"] < 1.0:
        return out
    world.fired.add(sig)
    world.ambient["foreshadowing"] += 1.0
    out.append(
        f"Somewhere in the dark, a tiny tune drifted by -- the same tune {ghost.label} "
        f"had hummed when nobody was looking."
    )
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    relic = world.facts.get("relic")
    ghost = world.facts.get("ghost")
    if not child or not relic or not ghost:
        return out
    sig = ("reveal", relic.id)
    if sig in world.fired:
        return out
    if child.memes["cheer"] < THRESHOLD or world.ambient["foreshadowing"] < 1.0:
        return out
    world.fired.add(sig)
    relic.hidden = False
    child.memes["relief"] += 1
    ghost.memes["loneliness"] = 0.0
    out.append(f"The little glow showed where {relic.label} had been tucked away all along.")
    return out


RULES = [Rule("cold_spot", _r_cold_spot), Rule("foreshadow", _r_foreshadow), Rule("reveal", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_haunt(world: World, child: Entity, ghost: Entity, relic: Relic, narrate: bool = True) -> None:
    if world.setting.place not in world.setting.affords:
        return
    child.memes["fear"] += 1
    ghost.meters["moved"] += 1
    world.ambient["suspense"] += 1.0
    world.say(f"The floor creaked, and {child.id} froze in place.")
    if narrate:
        propagate(world, narrate=True)


def child_name_pronoun(name: str) -> str:
    return name


def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "curious")
    world.say(f"{child.id} was a little {trait} {child.type} who liked brave mysteries.")


def setting_intro(world: World, relic: Relic) -> None:
    world.say(
        f"That evening, the old {world.setting.place} was quiet, and {relic.phrase} was nowhere to be found."
    )


def suspense_hint(world: World, ghost: Ghost) -> None:
    world.say(
        f"Then came a whisper from the rafters, soft as a leaf: {ghost.clue}."
    )
    world.ambient["suspense"] += 0.5


def foreshadow_hint(world: World, ghost: Ghost) -> None:
    world.say(
        f"A thin blue glow blinked once near the stairs, and {ghost.label}'s tune floated back again."
    )
    world.ambient["foreshadowing"] += 0.5


def radical_cheer(world: World, child: Entity, ghost: Ghost, relic: Relic) -> None:
    child.memes["cheer"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    world.say(
        f"{child.id} took a breath and shouted a radical cheer: "
        f"\"Bright room, kind moon, we will find you soon!\""
    )
    world.say(
        f"The silly words bounced through the dark, and {ghost.label} stopped hiding."
    )


def resolve(world: World, child: Entity, ghost: Ghost, relic: Relic) -> None:
    child.memes["relief"] += 1
    ghost.memes["cheer"] += 1
    world.say(
        f"{ghost.label} drifted down with a shy smile and pointed to the place where {relic.label} was tucked."
    )
    world.say(
        f"{child.id} found {relic.label}, and the old {world.setting.place} felt warm instead of spooky."
    )


def tell(world: World, child: Entity, ghost: Ghost, relic: Relic) -> None:
    introduce(world, child)
    setting_intro(world, relic)
    world.para()
    world.say(f"{child.id} had come to look for {relic.phrase}.")
    suspense_hint(world, ghost)
    _do_haunt(world, child, ghost, relic)
    foreshadow_hint(world, ghost)
    world.para()
    radical_cheer(world, child, ghost, relic)
    propagate(world, narrate=True)
    resolve(world, child, ghost, relic)


SETTINGS = {
    "attic": Setting(place="attic", eerie=True, affords={"haunt"}),
    "hallway": Setting(place="hallway", eerie=True, affords={"haunt"}),
    "cellar": Setting(place="cellar", eerie=True, affords={"haunt"}),
}

RELICS = {
    "lantern": Relic(
        id="lantern",
        label="the lantern",
        phrase="a brass lantern with a red ribbon",
        location="behind an old trunk",
        sound="a tiny clink",
        glow="a small blue glow",
    ),
    "book": Relic(
        id="book",
        label="the storybook",
        phrase="a storybook with a torn moon on the cover",
        location="under a folded curtain",
        sound="a papery rustle",
        glow="a silver blink",
    ),
    "bell": Relic(
        id="bell",
        label="the bell",
        phrase="a little bell with a cracked handle",
        location="by a dusty shelf",
        sound="a faint ring",
        glow="a pale shine",
    ),
}

GHOSTS = {
    "murmur": Ghost(
        id="murmur",
        label="Murmur",
        style="gentle",
        clue="follow the tune, not the shadow",
        tune="la-la-lin",
        reason="wanted the child to notice the hidden relic",
    ),
    "paleone": Ghost(
        id="paleone",
        label="Pale One",
        style="wistful",
        clue="the bright thing is near",
        tune="hmm-hum",
        reason="had been lonely and hoped for company",
    ),
    "tangle": Ghost(
        id="tangle",
        label="Tangle",
        style="sly",
        clue="look where the blue glow rests",
        tune="do-do-dim",
        reason="was trying to protect the relic from the damp floor",
    ),
}

NAMES = ["Mina", "Noah", "Luna", "Eli", "Ivy", "Theo", "Pia", "Nora"]
TRAITS = ["brave", "curious", "cheerful", "spunky", "lively", "fearless"]


@dataclass
class StoryParams:
    place: str
    relic: str
    ghost: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world with suspense and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--ghost", choices=GHOSTS)
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
    combos = [(p, r, g) for p in SETTINGS for r in RELICS for g in GHOSTS]
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.relic is None or c[1] == args.relic)
              and (args.ghost is None or c[2] == args.ghost)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, relic, ghost = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, relic=relic, ghost=ghost, name=name, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child featuring the words "radical" and "cheer".',
        f"Tell a spooky-but-kind story where {f['child'].id} enters the {f['setting'].place} to find {f['relic'].phrase}.",
        f"Write a suspenseful story with foreshadowing, a hidden clue, and a radical cheer that turns fear into relief.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, relic = f["child"], f["ghost"], f["relic"]
    return [
        QAItem(
            question=f"What was {child.id} looking for in the {world.setting.place}?",
            answer=f"{child.id} was looking for {relic.phrase}.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful before the ending?",
            answer=f"The dark {world.setting.place}, the whisper, and the creaking floor made the search feel suspenseful.",
        ),
        QAItem(
            question=f"What clue was foreshadowed before {relic.label} was found?",
            answer=f"The repeated tune and the blue glow hinted that {ghost.label} was leading {child.id} to {relic.label}.",
        ),
        QAItem(
            question=f"What did {child.id} shout to change the mood?",
            answer=f"{child.id} shouted a radical cheer: \"Bright room, kind moon, we will find you soon!\"",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{child.id} found {relic.label}, and the spooky place felt warm and calm at the end.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something seems tense or mysterious.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue in the story that hints at something important before it happens.",
        ),
        QAItem(
            question="What does a ghost story do?",
            answer="A ghost story usually uses mystery, spooky details, and a hidden truth to make the reader curious and a little scared.",
        ),
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} ({e.type:8}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"  ambient={world.ambient}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
suspense(X) :- fear(X).
foreshadowing :- suspense(_), clue(_).
reveal(R) :- cheer(_), clue(R), foreshadowing.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    for g in GHOSTS:
        lines.append(asp.fact("ghost", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for relic in RELICS:
            for ghost in GHOSTS:
                combos.append((place, relic, ghost))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    clingo_set, python_set = set(valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP parity placeholder matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH")
    return 1


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type="child", traits=["little", params.trait]))
    ghost = world.add(Entity(id=params.ghost, kind="character", type="ghost", label=GHOSTS[params.ghost].label))
    relic = Relic(**{**RELICS[params.relic].__dict__})
    world.facts.update(child=child, ghost=ghost, relic=relic, setting=SETTINGS[params.place])
    child.memes["curiosity"] += 1
    ghost.memes["loneliness"] += 1
    child.memes["fear"] += 1
    world.say(f"{child.id} was a little {params.trait} child who loved brave mysteries.")
    world.say(f"That night, {child.id} went into the {world.setting.place} to find {relic.phrase}.")
    world.para()
    world.say(f"The shadows seemed to lean closer, and {ghost.label} stayed out of sight.")
    world.say(f"Then {ghost.label}'s clue drifted through the dark: \"{GHOSTS[params.ghost].clue}.\"")
    world.say("A tiny glow blinked once near the stairs.")
    world.para()
    child.memes["cheer"] += 1
    child.memes["fear"] = 0.0
    world.say(f"{child.id} smiled and shouted a radical cheer to the empty room.")
    world.say(f"At once, the whisper softened, and the hidden tune made sense.")
    world.say(f"{ghost.label} floated down, pointed to the spot, and helped reveal {relic.label}.")
    world.say(f"{child.id} held {relic.label} tightly as the {world.setting.place} felt warm and safe again.")
    world.facts["resolved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="attic", relic="lantern", ghost="murmur", name="Mina", trait="brave"),
    StoryParams(place="hallway", relic="book", ghost="paleone", name="Noah", trait="curious"),
    StoryParams(place="cellar", relic="bell", ghost="tangle", name="Ivy", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible story combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
