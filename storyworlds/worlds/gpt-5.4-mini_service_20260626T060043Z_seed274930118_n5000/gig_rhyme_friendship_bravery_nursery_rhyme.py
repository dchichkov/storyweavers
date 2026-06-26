#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gig_rhyme_friendship_bravery_nursery_rhyme.py
==============================================================================================================

A tiny nursery-rhyme story world about a gig, a rhyme, a friendship, and a brave
little turn. The world is constraint-checked: the gig needs a song partner, the
song can wobble, and bravery changes the ending from shy to shining.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    partner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Venue:
    place: str = "the little green"
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Gig:
    id: str
    name: str
    song: str
    rhyme: str
    beat: str
    charm: str
    risk: str
    fixes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str


class World:
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        w = World(self.venue)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_shy(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes.get("shy", 0) < THRESHOLD:
            continue
        if ent.memes.get("brave", 0) >= THRESHOLD:
            continue
        sig = ("shy", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["wobble"] = ent.memes.get("wobble", 0) + 1
        out.append(f"{ent.id}'s voice went small as a mouse in a shoe.")
    return out


def _r_bravery_turn(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes.get("brave", 0) < THRESHOLD:
            continue
        sig = ("brave", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["shine"] = ent.memes.get("shine", 0) + 1
        out.append(f"Then {ent.id} stood up straight, and the little crowd listened.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes.get("friendship", 0) < THRESHOLD:
            continue
        if ent.memes.get("lonely", 0) <= 0:
            continue
        sig = ("friendship", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["lonely"] = 0
        out.append(f"A friend came near, and the lonely feeling hopped away.")
    return out


CAUSAL_RULES = [Rule("shy", _r_shy), Rule("bravery", _r_bravery_turn), Rule("friendship", _r_friendship)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def gig_risk(gig: Gig) -> bool:
    return "rhyme" in gig.tags or gig.charm == "song"


def select_fix(gig: Gig) -> Optional[str]:
    for fix in sorted(gig.fixes):
        return fix
    return None


def predict_turn(world: World, child: Entity, gig: Gig) -> dict:
    sim = world.copy()
    perform_gig(sim, sim.get(child.id), gig, narrate=False)
    return {
        "shy": sim.get(child.id).memes.get("shy", 0),
        "brave": sim.get(child.id).memes.get("brave", 0),
        "shine": sim.get(child.id).memes.get("shine", 0),
    }


def perform_gig(world: World, child: Entity, gig: Gig, narrate: bool = True) -> None:
    child.meters["gig_steps"] = child.meters.get("gig_steps", 0) + 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["shy"] = child.memes.get("shy", 0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, friend: Entity, gig: Gig) -> None:
    world.say(
        f"{child.id} was a little {child.type} with a heart like a bright bead. "
        f"{child.id} loved {gig.song} and the merry little {gig.name} gig."
    )
    world.say(
        f"{friend.id} was a true friend, and together they liked to hum a soft {gig.rhyme} rhyme."
    )


def set_scene(world: World) -> None:
    if world.venue.outdoor:
        world.say(f"In {world.venue.place}, the grass was green, and the breezes went thin and keen.")
    else:
        world.say(f"In {world.venue.place}, the room was snug, with a tap-tap beat like a friendly mug.")


def want_to_play(world: World, child: Entity, gig: Gig) -> None:
    child.memes["desire"] = child.memes.get("desire", 0) + 1
    world.say(f"{child.id} wanted to sing the {gig.rhyme} rhyme, but the first note felt a little high.")


def worry(world: World, friend: Entity, child: Entity, gig: Gig) -> None:
    child.memes["shy"] = child.memes.get("shy", 0) + 1
    world.say(
        f"{friend.id} saw the wobble and said, 'No need to hurry; little songs can wait and still be lovely.'"
    )
    world.say(f"But {child.id} held the tiny drum and wondered if the gig would go awry.")


def brave_step(world: World, child: Entity, gig: Gig) -> None:
    child.memes["brave"] = child.memes.get("brave", 0) + 1
    world.say(
        f"Then {child.id} took one brave breath and tried again, tapping the {gig.beat} beat with both feet."
    )


def friendship_help(world: World, child: Entity, friend: Entity, gig: Gig) -> None:
    child.memes["friendship"] = child.memes.get("friendship", 0) + 1
    child.partner = friend.id
    friend.partner = child.id
    propagate(world, narrate=False)
    world.say(
        f"{friend.id} stood beside {child.id} and sang the second line, and the rhyme grew round and sweet."
    )


def ending(world: World, child: Entity, friend: Entity, gig: Gig, prize: Prize) -> None:
    if child.memes.get("brave", 0) >= THRESHOLD:
        world.say(
            f"At the end, {child.id} sang the whole {gig.rhyme} rhyme, {friend.id} clapped, "
            f"and the little {prize.label} shone like morning."
        )
    else:
        world.say(
            f"At the end, {child.id} still hummed softly, and {friend.id} kept the tune warm beside {child.id}."
        )


def tell(venue: Venue, gig: Gig, prize_cfg: Prize, child_name: str = "Mina", child_type: str = "girl",
         friend_name: str = "Pip", friend_type: str = "boy") -> World:
    world = World(venue)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, traits=["little", "gentle"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["little", "kind"]))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=child.id))

    introduce(world, child, friend, gig)
    set_scene(world)
    world.say(f"{child.id} carried {prize.phrase} for the little gig.")
    want_to_play(world, child, gig)

    world.para()
    worry(world, friend, child, gig)
    if gig_risk(gig):
        world.say(f"The {gig.name} gig needed a clear voice and a brave heart.")
    brave_step(world, child, gig)
    friendship_help(world, child, friend, gig)

    world.para()
    ending(world, child, friend, gig, prize)

    world.facts.update(child=child, friend=friend, prize=prize, gig=gig, venue=venue)
    return world


VENUES = {
    "green": Venue(place="the little green", outdoor=True, affords={"gig"}),
    "garden": Venue(place="the moonlit garden", outdoor=True, affords={"gig"}),
    "hall": Venue(place="the snug little hall", outdoor=False, affords={"gig"}),
}

GIGS = {
    "gig": Gig(
        id="gig",
        name="gig",
        song="a skipping song",
        rhyme="tiddle-tum",
        beat="tap-tap",
        charm="song",
        risk="shy",
        fixes={"friend"},
        tags={"gig", "rhyme", "friendship", "bravery"},
    ),
    "rhyme": Gig(
        id="rhyme",
        name="rhyme gig",
        song="a rhyme song",
        rhyme="hush-a-bye",
        beat="tap-tap",
        charm="song",
        risk="wobble",
        fixes={"friend"},
        tags={"rhyme", "friendship", "bravery"},
    ),
}

PRIZES = {
    "bell": Prize(label="bell", phrase="a tiny silver bell", type="bell"),
    "lantern": Prize(label="lantern", phrase="a little paper lantern", type="lantern"),
}

NAMES = ["Mina", "Pip", "Tilly", "Ned", "Luna", "Ollie"]
TRAITS = ["gentle", "cheery", "spry", "small", "bright"]


@dataclass
class StoryParams:
    place: str
    gig: str
    prize: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, venue in VENUES.items():
        for gid, gig in GIGS.items():
            if "gig" not in venue.affords:
                continue
            if not gig_risk(gig):
                continue
            for prize_id in PRIZES:
                out.append((place, gid, prize_id))
    return out


KNOWLEDGE = {
    "gig": [("What is a gig?", "A gig is a little performance or show, often with music.")],
    "rhyme": [("What is a rhyme?", "A rhyme is a pair of words or lines that sound alike at the end.")],
    "friendship": [("What is friendship?", "Friendship is when people care about each other and help each other.")],
    "bravery": [("What is bravery?", "Bravery is doing something a little scary even when your heart feels wobbly.")],
    "bell": [("What does a bell do?", "A bell makes a ringing sound when it is shaken or struck.")],
    "lantern": [("What is a lantern for?", "A lantern can hold a light and help a place glow softly.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, friend, gig = f["child"], f["friend"], f["gig"]
    return [
        f'Write a short nursery-rhyme story about a gig, a rhyme, friendship, and bravery.',
        f"Tell a child-friendly story where {child.id} and {friend.id} share the {gig.name} gig and become braver together.",
        f'Write a soft, musical story that includes the word "gig" and ends with a cheerful friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, gig, prize = f["child"], f["friend"], f["gig"], f["prize"]
    return [
        QAItem(
            question=f"Who took part in the little {gig.name} gig?",
            answer=f"{child.id} and {friend.id} took part together, and their friendship helped the song go well.",
        ),
        QAItem(
            question=f"What did {child.id} feel before the {gig.rhyme} rhyme started to sound brave?",
            answer=f"{child.id} felt shy at first, because the first note seemed high and the little heart wobbled.",
        ),
        QAItem(
            question=f"What helped {child.id} finish the song at the end?",
            answer=f"Friendship helped, because {friend.id} stood beside {child.id} and sang the second line.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and the {prize.label}?",
            answer=f"{child.id} sang with bravery, {friend.id} clapped, and the {prize.label} shone at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["gig"].tags)
    tags.add(world.facts["prize"].label)
    out: list[QAItem] = []
    for tag in ["gig", "rhyme", "friendship", "bravery", "bell", "lantern"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="green", gig="gig", prize="bell", child_name="Mina", child_type="girl", friend_name="Pip", friend_type="boy", trait="gentle"),
    StoryParams(place="garden", gig="rhyme", prize="lantern", child_name="Tilly", child_type="girl", friend_name="Ned", friend_type="boy", trait="cheery"),
]


def explain_rejection(place: str, gig: Gig, prize: Prize) -> str:
    return f"(No story: the {gig.name} gig at {place} is too thin to make a proper nursery-rhyme turn with {prize.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in VENUES:
        raise StoryError("(Unknown place.)")
    if args.gig and args.gig not in GIGS:
        raise StoryError("(Unknown gig.)")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("(Unknown prize.)")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.gig is None or c[1] == args.gig)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, gid, prize_id = rng.choice(sorted(combos))
    child_type = rng.choice(["girl", "boy"])
    friend_type = "boy" if child_type == "girl" else "girl"
    return StoryParams(
        place=place,
        gig=gid,
        prize=prize_id,
        child_name=args.name or rng.choice(NAMES),
        child_type=child_type,
        friend_name=args.friend or rng.choice([n for n in NAMES if n != (args.name or "")]),
        friend_type=friend_type,
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(VENUES[params.place], GIGS[params.gig], PRIZES[params.prize],
                 params.child_name, params.child_type, params.friend_name, params.friend_type)
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
gig_story(P,G,R) :- venue(P), gig(G), prize(R), affords(P,gig).
rhyme_story(P,G,R) :- gig_story(P,G,R), tags(G,rhyme).
brave_story(P,G,R) :- rhyme_story(P,G,R), tags(G,bravery).
friendly_story(P,G,R) :- brave_story(P,G,R), tags(G,friendship).
#show gig_story/3.
#show rhyme_story/3.
#show brave_story/3.
#show friendly_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, v in VENUES.items():
        lines.append(asp.fact("venue", pid))
        if v.outdoor:
            lines.append(asp.fact("outdoor", pid))
        for a in sorted(v.affords):
            lines.append(asp.fact("affords", pid, a))
    for gid, g in GIGS.items():
        lines.append(asp.fact("gig", gid))
        for t in sorted(g.tags):
            lines.append(asp.fact("tags", gid, t))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show gig_story/3.\n"))
    asp_set = set(asp.atoms(model, "gig_story"))
    py_set = set(valid_combos())
    py_trip = set((p, g, r) for p, g, r in py_set)
    if asp_set == py_trip:
        print(f"OK: clingo gate matches valid_combos() ({len(py_trip)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_trip:
        print("  only in clingo:", sorted(asp_set - py_trip))
    if py_trip - asp_set:
        print("  only in python:", sorted(py_trip - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about a gig, rhyme, friendship, and bravery.")
    ap.add_argument("--place", choices=VENUES)
    ap.add_argument("--gig", choices=GIGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show gig_story/3.\n#show rhyme_story/3.\n#show brave_story/3.\n#show friendly_story/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show gig_story/3.\n#show rhyme_story/3.\n#show brave_story/3.\n#show friendly_story/3.\n"))
        print(asp.atoms(model, "gig_story"))
        print(asp.atoms(model, "rhyme_story"))
        print(asp.atoms(model, "brave_story"))
        print(asp.atoms(model, "friendly_story"))
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
            header = f"### {p.child_name}: {p.gig} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
