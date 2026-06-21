#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/festival_rave_sharing_nursery_rhyme.py
======================================================================

A standalone storyworld about a little festival-rave night where two children
learn to share glow toys, snacks, and the last good listening spot. The prose
leans nursery-rhyme simple: rhythmic, concrete, and child-facing, while the
world model keeps the story state-driven.

The domain is intentionally small:
- a festival with a dance circle and a snack table
- a rave-like light show with glow bands and lanterns
- a sharing turn: one child wants everything, then learns to share so the fun
  gets bigger for both

The story engine includes:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate and inline ASP twin
- prompts, grounded story Q&A, and world-knowledge Q&A
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
    role: str = ""
    owns: set[str] = field(default_factory=set)
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
        return self.label or self.type


@dataclass
class Venue:
    id: str
    label: str
    scene: str
    music: str
    snack_spot: str
    dance_spot: str
    afford: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class GlowToy:
    id: str
    label: str
    phrase: str
    glows: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    sweet: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SharingChoice:
    id: str
    sense: int
    warmth: int
    text: str
    fail: str
    qa_text: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_happy(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.characters():
        if kid.memes["shared"] < THRESHOLD:
            continue
        sig = ("shared", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["joy"] += 1
        out.append("__shared__")
    return out


def _r_spread_joy(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("shared_well"):
        sig = ("joy_spread",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.characters():
                kid.memes["joy"] += 1
                kid.meters["glow"] += 1
            out.append("The music felt brighter when everyone shared.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("happy", "social", _r_happy),
    Rule("joy_spread", "social", _r_spread_joy),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(venue: Venue, toy: GlowToy, treat: Treat) -> bool:
    return "festival" in venue.tags and "rave" in venue.tags and "sharing" in venue.tags and bool(toy.tags & venue.tags) and bool(treat.tags & venue.tags)


def can_share(toy: GlowToy, treat: Treat) -> bool:
    return toy.id in {"glow_band", "lantern", "tambourine"} and treat.id in {"berry_cup", "cookie_plate", "pretzel_bowl"}


def good_choice(choice: SharingChoice) -> bool:
    return choice.sense >= 2


def story_turn(world: World, chooser: Entity, friend: Entity, toy: GlowToy, treat: Treat, choice: SharingChoice) -> None:
    chooser.memes["want"] += 1
    world.say(
        f"At the little festival rave, {chooser.id} loved the bright beat and the merry light. "
        f"{chooser.id} held the {toy.label} close and peeked at the {treat.label}."
    )
    world.say(
        f'"Mine, mine," {chooser.id} sang, but {friend.id} tipped a gentle chin and said, '
        f'"A share can make the cheer grow wide."'
    )
    if choice.id == "share":
        chooser.memes["share"] += 1
        friend.memes["share"] += 1
        world.say(
            f"{chooser.id} looked again, then smiled. {chooser.id} gave half the {toy.label} to {friend.id} "
            f"and passed the {treat.label} around."
        )
        propagate(world)
    else:
        chooser.memes["stingy"] += 1
        world.say(
            f"{chooser.id} kept it all too tight, and the song felt small in {chooser.pronoun('possessive')} hands."
        )


def ending(world: World, chooser: Entity, friend: Entity, venue: Venue, toy: GlowToy, treat: Treat, choice: SharingChoice) -> None:
    if choice.id == "share":
        world.say(
            f"Then the lanterns leaned low and the little festival rave went round and round. "
            f"{chooser.id} and {friend.id} shared the last glow, the last sweet bite, and the last laugh, "
            f"and the night shone soft and bright."
        )
    else:
        world.say(
            f"Then the lanterns blinked low and the little festival rave grew plain. "
            f"{chooser.id} held the glow too tight, so the fun did not bloom wide, and both children knew "
            f"the song was better when it was shared."
        )


def tell(venue: Venue, toy: GlowToy, treat: Treat, choice: SharingChoice,
         chooser_name: str = "Mia", chooser_gender: str = "girl",
         friend_name: str = "Noah", friend_gender: str = "boy") -> World:
    world = World()
    chooser = world.add(Entity(id=chooser_name, kind="character", type=chooser_gender, role="chooser"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    stage = world.add(Entity(id="stage", type="place", label=venue.label))
    glow = world.add(Entity(id=toy.id, type="toy", label=toy.label))
    sweet = world.add(Entity(id=treat.id, type="treat", label=treat.label))

    world.facts.update(chooser=chooser, friend=friend, venue=venue, toy=toy, treat=treat, choice=choice)

    world.say(
        f"In the festival glow, little {chooser.id} and {friend.id} went round the bright dance way. "
        f"{venue.scene} {venue.music}."
    )
    world.say(
        f"They found a {toy.label} and a {treat.label} by the snack table, near {venue.snack_spot}."
    )
    world.para()
    story_turn(world, chooser, friend, toy, treat, choice)
    world.para()
    ending(world, chooser, friend, venue, toy, treat, choice)
    world.facts["shared_well"] = choice.id == "share"
    world.facts["stage"] = stage
    world.facts["glow"] = glow
    world.facts["sweet"] = sweet
    return world


VENUES = {
    "festival": Venue(
        id="festival",
        label="the festival",
        scene="The festival bells rang, the paper stars swayed,",
        music="and the drums went bum-bum-bum.",
        snack_spot="the lantern table",
        dance_spot="the ribbon circle",
        afford={"festival", "rave"},
        tags={"festival", "sharing"},
    ),
    "rave": Venue(
        id="rave",
        label="the rave",
        scene="The rave lights twinkled, the bunting bobbed,",
        music="and the beat went thump-a-thump.",
        snack_spot="the glowing snack cart",
        dance_spot="the spinning floor",
        afford={"festival", "rave"},
        tags={"rave", "sharing"},
    ),
    "fair": Venue(
        id="fair",
        label="the fair",
        scene="The fair flags fluttered, the little lamps winked,",
        music="and the tune went tra-la-la.",
        snack_spot="the sweet cart",
        dance_spot="the merry ring",
        afford={"festival"},
        tags={"festival", "sharing"},
    ),
}

TOOLS = {
    "glow_band": GlowToy(
        id="glow_band",
        label="glow band",
        phrase="a glow band",
        glows="shines green and gold",
        tags={"festival", "rave", "sharing"},
    ),
    "lantern": GlowToy(
        id="lantern",
        label="lantern",
        phrase="a tiny lantern",
        glows="glows warm and bright",
        tags={"festival", "rave", "sharing"},
    ),
    "tambourine": GlowToy(
        id="tambourine",
        label="tambourine",
        phrase="a jingling tambourine",
        glows="rings with a happy shake",
        tags={"festival", "sharing"},
    ),
}

TREATS = {
    "berry_cup": Treat(id="berry_cup", label="berry cup", phrase="a berry cup", sweet="tastes like summer", tags={"festival", "sharing"}),
    "cookie_plate": Treat(id="cookie_plate", label="cookie plate", phrase="a cookie plate", sweet="crunches sweetly", tags={"festival", "rave", "sharing"}),
    "pretzel_bowl": Treat(id="pretzel_bowl", label="pretzel bowl", phrase="a pretzel bowl", sweet="is salty and fun", tags={"festival", "rave", "sharing"}),
}

CHOICES = {
    "share": SharingChoice(id="share", sense=3, warmth=3, text="shared the goodies kindly", fail="kept it all too tight", qa_text="shared the glow toy and the snacks kindly"),
    "split": SharingChoice(id="split", sense=2, warmth=2, text="split them into two neat piles", fail="split the fun too late", qa_text="split the toys and treats fairly"),
    "keep": SharingChoice(id="keep", sense=1, warmth=0, text="kept everything for one pair of hands", fail="kept everything for one pair of hands", qa_text="kept everything for themselves"),
}

CURATED = [
    StoryParams(
        venue="festival",
        toy="glow_band",
        treat="cookie_plate",
        choice="share",
        chooser_name="Mia",
        chooser_gender="girl",
        friend_name="Noah",
        friend_gender="boy",
        seed=1,
    ),
    StoryParams(
        venue="rave",
        toy="lantern",
        treat="pretzel_bowl",
        choice="split",
        chooser_name="Lily",
        chooser_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        seed=2,
    ),
]


@dataclass
class StoryParams:
    venue: str
    toy: str
    treat: str
    choice: str
    chooser_name: str
    chooser_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for vid, venue in VENUES.items():
        for toy_id, toy in TOOLS.items():
            for treat_id, treat in TREATS.items():
                for choice_id, choice in CHOICES.items():
                    if not good_choice(choice):
                        continue
                    if not reasonableness_gate(venue, toy, treat):
                        continue
                    if not can_share(toy, treat):
                        continue
                    combos.append((vid, toy_id, treat_id, choice_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld of a festival rave and sharing.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--toy", choices=TOOLS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--chooser-name")
    ap.add_argument("--chooser-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.choice and not good_choice(CHOICES[args.choice]):
        raise StoryError("The chosen sharing move is too weak for this storyworld.")
    combos = [c for c in valid_combos()
              if (args.venue is None or c[0] == args.venue)
              and (args.toy is None or c[1] == args.toy)
              and (args.treat is None or c[2] == args.treat)
              and (args.choice is None or c[3] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    venue, toy, treat, choice = rng.choice(sorted(combos))
    toy_obj = TOOLS[toy]
    treat_obj = TREATS[treat]
    chooser_gender = args.chooser_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if chooser_gender == "girl" else "girl")
    chooser_name = args.chooser_name or rng.choice(["Mia", "Lily", "Ava", "Zoe", "Nia"])
    friend_name = args.friend_name or rng.choice(["Noah", "Ben", "Theo", "Max", "Finn"])
    return StoryParams(
        venue=venue,
        toy=toy,
        treat=treat,
        choice=choice,
        chooser_name=chooser_name,
        chooser_gender=chooser_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"Unknown venue: {params.venue}")
    if params.toy not in TOOLS:
        raise StoryError(f"Unknown toy: {params.toy}")
    if params.treat not in TREATS:
        raise StoryError(f"Unknown treat: {params.treat}")
    if params.choice not in CHOICES:
        raise StoryError(f"Unknown choice: {params.choice}")
    world = tell(VENUES[params.venue], TOOLS[params.toy], TREATS[params.treat], CHOICES[params.choice],
                 chooser_name=params.chooser_name, chooser_gender=params.chooser_gender,
                 friend_name=params.friend_name, friend_gender=params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a nursery-rhyme style story with the words "festival" and "rave" about sharing glow toys and treats.',
        f"Tell a little story where {f['chooser'].id} and {f['friend'].id} meet at the {f['venue'].label} and learn to share.",
        f"Write a child-friendly rhyme about a {f['toy'].label} and a {f['treat'].label} at a festival rave.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    chooser, friend, venue, toy, treat, choice = f["chooser"], f["friend"], f["venue"], f["toy"], f["treat"], f["choice"]
    qa = [
        ("Who is the story about?", f"It is about {chooser.id} and {friend.id}, two small children at {venue.label}. They spend the night learning how sharing makes the fun grow."),
        ("What did they find?", f"They found {toy.phrase} and {treat.phrase} near the snack table. Those little things became the heart of their game."),
    ]
    if choice.id == "share":
        qa.append(("What did {0} do with the toys and treats?".format(chooser.id),
                   f"{chooser.id} shared the glow toy and the snacks kindly. That is why the festival rave ended in a bright, happy circle for both children."))
        qa.append(("How did the story end?", "It ended with both children laughing together while the lights shone soft and bright. Sharing made the night feel bigger than one pair of hands."))
    else:
        qa.append(("What went wrong?", f"{chooser.id} kept the best things close and did not share at first. The music still played, but the cheer stayed small until the children learned better."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["toy"].tags) | set(f["treat"].tags) | set(f["venue"].tags)
    out = []
    knowledge = {
        "festival": [("What is a festival?", "A festival is a happy event where people gather to listen, dance, and enjoy treats together.")],
        "rave": [("What is a rave?", "A rave is a loud music party with bright lights and a strong beat that makes people want to dance.")],
        "sharing": [("What does sharing mean?", "Sharing means letting someone else use or enjoy part of what you have, so more than one person can be happy.")],
    }
    for key in ["festival", "rave", "sharing"]:
        if key in tags:
            out.extend(knowledge[key])
    return out


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for vid, venue in VENUES.items():
        lines.append(asp.fact("venue", vid))
        if "festival" in venue.tags:
            lines.append(asp.fact("festival", vid))
        if "rave" in venue.tags:
            lines.append(asp.fact("rave", vid))
        if "sharing" in venue.tags:
            lines.append(asp.fact("sharing", vid))
    for tid, toy in TOOLS.items():
        lines.append(asp.fact("toy", tid))
    for sid, treat in TREATS.items():
        lines.append(asp.fact("treat", sid))
    for cid, choice in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, choice.sense))
    return "\n".join(lines)


ASP_RULES = r"""
valid(V,T,S,C) :- venue(V), toy(T), treat(S), choice(C), sense(C, N), N >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            venue=None, toy=None, treat=None, choice=None,
            chooser_name=None, chooser_gender=None, friend_name=None, friend_gender=None
        ), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def _pick(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
