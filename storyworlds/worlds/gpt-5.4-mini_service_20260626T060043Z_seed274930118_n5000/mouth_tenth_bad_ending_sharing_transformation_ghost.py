#!/usr/bin/env python3
"""
A standalone storyworld for a small ghost-story domain.

Premise:
- A child on their tenth night hears a ghost near an old house.
- The ghost cannot keep its form unless it shares something small and kind.
- The child learns that sharing can transform fear into trust.
- The ending stays spooky and a little bad: something is lost, but the loss changes the room, and the new shape of the night is gentler.

This world includes the seed words "mouth" and "tenth" in its core vocabulary and narration.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"ghost"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    time_word: str = "the tenth night"
    indoors: bool = True
    hush: str = "the air felt hushed"
    affordances: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    type: str
    touch: str
    fragile: bool = False
    kinds: set[str] = field(default_factory=set)
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class GhostDef:
    id: str
    name: str
    mouth_state: str
    hunger: str
    transform_word: str
    shadow_color: str
    can_share: str
    ending_phrase: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_ghost_hunger(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    snack = world.entities.get("snack")
    if not ghost or not snack:
        return out
    if ghost.memes.get("hunger", 0.0) < THRESHOLD:
        return out
    sig = ("hunger",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if snack.meters.get("shared", 0.0) < THRESHOLD:
        world.say("The ghost drifted closer because its mouth looked empty and cold.")
    else:
        world.say("The ghost drifted closer, but the shared crumbs made its hunger quieter.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    if not ghost:
        return out
    if ghost.memes.get("shared", 0.0) < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["calm"] = ghost.memes.get("calm", 0.0) + 1
    ghost.memes["fear"] = max(0.0, ghost.memes.get("fear", 0.0) - 1)
    ghost.type = "ghost"
    out.append("The ghost changed shape, and its thin shadow became softer at the edges.")
    return out


RULES = [
    Rule("ghost_hunger", _r_ghost_hunger),
    Rule("transformation", _r_transformation),
]


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


SETTING = Setting(
    place="the old house",
    time_word="the tenth night",
    indoors=True,
    hush="the hall held its breath",
    affordances={"listen", "share", "whisper"},
)

GHOSTS = {
    "lantern": GhostDef(
        id="ghost",
        name="Mara",
        mouth_state="open like a cold door",
        hunger="hungry for a kind word",
        transform_word="transform",
        shadow_color="blue-gray",
        can_share="a little warmth",
        ending_phrase="the room felt less lonely",
    ),
}

OBJECTS = {
    "candies": ObjectDef(
        id="candies",
        label="candies",
        phrase="a tin of sweet candies",
        type="candies",
        touch="sticky and sweet",
        fragile=False,
        kinds={"share", "sweet"},
        genders={"girl", "boy"},
    ),
    "lantern": ObjectDef(
        id="lantern",
        label="lantern",
        phrase="a small lantern with a glass mouth",
        type="lantern",
        touch="warm light",
        fragile=True,
        kinds={"light", "share"},
        genders={"girl", "boy"},
    ),
    "blanket": ObjectDef(
        id="blanket",
        label="blanket",
        phrase="a soft blanket",
        type="blanket",
        touch="warm cloth",
        fragile=False,
        kinds={"share", "warm"},
        genders={"girl", "boy"},
    ),
    "mirror": ObjectDef(
        id="mirror",
        label="mirror",
        phrase="a narrow mirror",
        type="mirror",
        touch="cold glass",
        fragile=True,
        kinds={"reflect"},
        genders={"girl", "boy"},
    ),
}

CHILD_NAMES = ["Mina", "Eli", "Nora", "Jun", "Lia", "Sage", "Toby", "Iris"]
TRAITS = ["quiet", "curious", "brave", "small", "careful"]


@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    item: str
    seed: Optional[int] = None


def valid_items() -> list[str]:
    return ["candies", "lantern", "blanket"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with sharing and transformation.")
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--item", choices=valid_items())
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    item = args.item or rng.choice(valid_items())
    return StoryParams(name=name, gender=gender, trait=trait, item=item)


def child_pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "girl":
        return "she", "her", "her"
    return "he", "him", "his"


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    subj, obj, pos = child_pronouns(params.gender)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
        traits=[params.trait, "tenth"],
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=GHOSTS["lantern"].name,
        traits=["ghostly", "thin"],
    ))
    item_def = OBJECTS[params.item]
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=item_def.type,
        label=item_def.label,
        phrase=item_def.phrase,
        owner=child.id,
        caretaker=child.id,
    ))

    world.say(f"On the tenth night, {params.name} stood in the old house and listened to the hush.")
    world.say(f"The hallway was so still that even a whisper felt loud.")
    world.say(f"{params.name} had brought {item_def.phrase}, because {pos} wanted something small to hold.")
    world.say(f"Then a ghost rose from the corner. Its mouth looked {GHOSTS['lantern'].mouth_state}, and its shadow was {GHOSTS['lantern'].shadow_color}.")
    world.para()
    world.say(f"{params.name} did not run. {subj.capitalize()} stared at the ghost and noticed that it looked hungry.")
    world.say(f"The ghost said it was {GHOSTS['lantern'].hunger}, and that it could only stay steady if someone would share.")
    world.say(f"{params.name} looked at {item.label} and thought about what to do with {obj} hands.")
    if params.item == "mirror":
        world.say("The mirror made the ghost look longer and stranger, which frightened both of them.")
    elif params.item == "lantern":
        world.say("The lantern glowed through the dark and made the ghost's edges blink like a slow breath.")
    else:
        world.say("The candies made a tiny sweet smell that drifted toward the ghost's empty mouth.")
    world.para()
    item.meters["shared"] = 1.0
    ghost.memes["hunger"] = 1.0
    world.say(f"At last, {params.name} shared the {item.label}.")
    world.say(f"It was only a little thing, but the ghost leaned close as if the kindness had weight.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"After that, the ghost changed.")
    world.say(f"Its mouth no longer looked like a cold door; it looked almost like a smile that had learned how to stay.")
    world.say(f"{params.name} kept the last small piece and felt the room become different around {pos}.")
    world.say(f"It was a bad ending for the lost treat, but a gentler ending for the house: the ghost stayed, and the dark did not feel quite so sharp.")
    world.facts.update(
        child=child,
        ghost=ghost,
        item=item,
        params=params,
        subject=subj,
        object=obj,
        possessive=pos,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    subj, obj, pos = f["subject"], f["object"], f["possessive"]
    item = f["item"]
    ghost = f["ghost"]
    return [
        QAItem(
            question=f"What happened on the tenth night at the old house?",
            answer=f"On the tenth night, {p.name} met a ghost in the old house and shared {pos} {item.label}.",
        ),
        QAItem(
            question=f"Why did the ghost come closer to {p.name}?",
            answer=f"The ghost came closer because it was hungry for a kind share, and its mouth looked empty and cold.",
        ),
        QAItem(
            question=f"What did {p.name} do to help the ghost?",
            answer=f"{p.name} shared {pos} {item.label}, and that small act helped the ghost settle down.",
        ),
        QAItem(
            question=f"What changed after the sharing?",
            answer=f"The ghost transformed and became softer and calmer, so the room felt less lonely.",
        ),
        QAItem(
            question=f"Why was the ending a bad ending for the lost item?",
            answer=f"It was a bad ending for the item because it was given away, but it was a kinder ending for the house and the ghost.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost?",
            answer="A ghost is a spooky imagined figure from a story, often shown as pale, quiet, and able to drift through a room.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving some of what you have to someone else, so both people can use, taste, or enjoy it in some way.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another, like a frightened thing becoming calmer.",
        ),
        QAItem(
            question="What is a mouth for?",
            answer="A mouth is used for talking, eating, and tasting; in stories, a mouth can also help show a character's feelings.",
        ),
        QAItem(
            question="What does tenth mean?",
            answer="Tenth means number ten in order, after ninth and before eleventh.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a ghost story for children about the tenth night in an old house where {p.name} shares something small.",
        f"Tell a spooky but gentle story about a ghost's mouth, a child named {p.name}, and a transformation brought on by sharing.",
        f"Write a short ghost story that uses the words 'mouth' and 'tenth' and ends with a strange but softer room.",
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
    lines.append("== (3) World knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}/{e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mina", gender="girl", trait="curious", item="candies"),
    StoryParams(name="Eli", gender="boy", trait="quiet", item="blanket"),
    StoryParams(name="Nora", gender="girl", trait="brave", item="lantern"),
]


ASP_RULES = r"""
item_shared(I) :- shared(I).
ghost_ready :- item_shared(I).
transformed(g) :- ghost(g), ghost_ready.
valid_story(N, G, T, I) :- name(N), gender(G), trait(T), item(I), valid_item(I), wears(G, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in CHILD_NAMES:
        lines.append(asp.fact("name", n))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    for t in TRAITS:
        lines.append(asp.fact("trait", t))
    for iid in OBJECTS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("valid_item", iid))
    lines.append(asp.fact("ghost", "ghost"))
    for g in ["girl", "boy"]:
        for iid in OBJECTS:
            lines.append(asp.fact("wears", g, iid))
    lines.append(asp.fact("shared", "candies"))
    lines.append(asp.fact("shared", "lantern"))
    lines.append(asp.fact("shared", "blanket"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def resolve_reasonable(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(CHILD_NAMES),
        gender=args.gender or rng.choice(["girl", "boy"]),
        trait=args.trait or rng.choice(TRAITS),
        item=args.item or rng.choice(valid_items()),
    )


def valid_items() -> list[str]:
    return list(OBJECTS.keys())


def build_all_samples() -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = build_all_samples()
        samples = [generate(p) for p in params_list]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} / {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
