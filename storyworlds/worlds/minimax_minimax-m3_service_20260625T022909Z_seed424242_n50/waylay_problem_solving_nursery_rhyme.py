#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/waylay_problem_solving_nursery_rhyme.py
==============================================================================================================

A standalone *story world* sketch for the "Waylay the Wolf" nursery-rhyme
domain. A small flock of nursery-rhyme characters run into a Wolf at the
crooked stile, and the small ones must **waylay** him (stall, redirect, or
outfox him) until help arrives.

Initial rhyme (the source tale we built the world model from):
---
    Down by the stile where the cowslips grow,
    Mary and her lambs set out to row.
    Jack and Jill with bucket bright,
    Wee Boy Blue asleep in the light.
    The Wolf came sneaky round the bend —
    he would not play, he would not bend.
    Mary held her ground and said, "Not so!
    If you want us, friend, first answer three — "
    A riddle, a trade, a kind little test,
    Waylay the Wolf with the very best!
    Wolf scratched his ear, he could not win.
    Down the lane came Bold Robín.
    Robín blew his horn — the Wolf was out of luck —
    And the small folk laughed and danced the whole night through.

World model:
---
    The world tracks the cast (Mary, Jack, Jill, Boy Blue, the Wolf,
    a Helper), a small Problem they are waylaying (the Wolf's arrival),
    and a sequence of Problem-Solving steps the small folk try in order
    (a riddle, a trade, a test) until a Helper arrives and resolves it.

    meter keys  :   wolf_threat, found, waylaid, free
    meme  keys  :   panic, clever, helper, joy, win

    do attempt       ->  hero.clever += 1; wolf.waylaid += 1
    do attempt fail  ->  hero.panic += 1
    helper arrives   ->  wolf.threat -> 0, all.free += 1, joy += 1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses as dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Body regions kept consistent with the rest of the storyworlds
REGIONS = {"feet", "legs", "torso"}

# ---- The small Problem-Solving "ways" the small folk try to waylay the Wolf.
# Each has a kind: riddle (outfox the mind), trade (offer something else),
# test (a kind, gentle act that confuses the Wolf). One MUST be the kind that
# actually beats the Wolf for that cast; the others fail.
ATTEMPT_KINDS = {"riddle", "trade", "test"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # mary, jack, jill, boy_blue, wolf, robin, ...
    label: str = ""                # short reference
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"mary", "jill", "mother", "mom", "woman", "girl"}
        male = {"jack", "boy_blue", "robin", "father", "dad", "man", "boy"}
        wolf_kinds = {"wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in wolf_kinds:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"boy_blue": "boy"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the crooked stile"
    afford: str = "waylay"          # what the setting is good for


@dataclass
class Cast:
    """The little cast of small folk who face the Wolf together."""
    names: list[str]                # mary, jack, jill, boy_blue (subset)
    leader: str = "mary"            # who holds the line and tries to waylay the Wolf


@dataclass
class Trick:
    """One Problem-Solving move the leader tries on the Wolf."""
    id: str                          # riddle | trade | test
    ask: str                         # the question/offer/test the leader makes
    beat: str                        # what the Wolf must do (and can't) to win
    flourish: str                    # closing nursery flourish
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str                          # robin
    name: str                        # Bold Robin
    horn: str                        # "blew his horn loud and clear"
    chase: str                       # "The Wolf went running down the lane"


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules (forward chained)
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_attempt(world: World) -> list[str]:
    """A leader attempts a waylay trick -> clever++, wolf.waylaid++"""
    out: list[str] = []
    for actor in world.characters():
        for kind in ATTEMPT_KINDS:
            if actor.meters.get(f"attempt_{kind}", 0) < THRESHOLD:
                continue
            wolf = next((e for e in world.characters() if e.type == "wolf"), None)
            if wolf is None:
                continue
            sig = ("attempt", actor.id, kind)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["clever"] += 1
            wolf.meters["waylaid"] += 1
            out.append(
                f"{actor.id} tried the {kind} on the Wolf."
            )
    return out


def _r_fail(world: World) -> list[str]:
    """A failed attempt -> leader panic++"""
    out: list[str] = []
    for actor in world.characters():
        for kind in ATTEMPT_KINDS:
            if actor.meters.get(f"fail_{kind}", 0) < THRESHOLD:
                continue
            sig = ("fail", actor.id, kind)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["panic"] += 1
            out.append(f"The {kind} didn't quite waylay the Wolf.")
    return out


def _r_helper(world: World) -> list[str]:
    """When helper arrives -> wolf.threat -> 0, all free, all joy."""
    helper = next((e for e in world.characters() if e.type == "robin"), None)
    if helper is None:
        return []
    if helper.meters.get("arrived", 0) < THRESHOLD:
        return []
    wolf = next((e for e in world.characters() if e.type == "wolf"), None)
    if wolf is None:
        return []
    sig = ("helper", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    wolf.meters["threat"] = 0.0
    for actor in world.characters():
        if actor.type in ("wolf",):
            continue
        actor.meters["free"] += 1
        actor.memes["joy"] += 1
        actor.memes["win"] += 1
    return []  # narrated directly by the screenplay beat


CAUSAL_RULES: list[Rule] = [
    Rule(name="attempt", apply=_r_attempt),
    Rule(name="fail", apply=_r_fail),
    Rule(name="helper", apply=_r_helper),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Verb screenplays
# ---------------------------------------------------------------------------
def introduce(world: World, cast: Cast) -> None:
    leader = world.get(cast.leader)
    friends = [world.get(n) for n in cast.names if n != cast.leader]
    friend_names = ", ".join(f.id for f in friends)
    world.say(
        f"Down by {world.setting.place} where the cowslips grow, "
        f"{leader.id} and her {friend_names} set out for a small adventure."
    )


def wolf_appears(world: World) -> None:
    wolf = world.add(Entity(
        id="Wolf", kind="character", type="wolf", label="the Wolf",
        traits=["sneaky", "hungry"],
    ))
    wolf.meters["threat"] += 1
    world.say(
        "But round the bend came creeping the Wolf, low and grey, "
        "with a quick black nose and a long, lean way."
    )


def freeze(world: World, cast: Cast) -> None:
    leader = world.get(cast.leader)
    world.say(
        f"The little ones all looked at {leader.id}; {leader.pronoun()} "
        f"looked back at them and said, 'Stay close, dear friends. "
        f"We will waylay the Wolf together.'"
    )


def try_trick(world: World, cast: Cast, trick: Trick, success: bool) -> None:
    """The leader makes an attempt on the Wolf."""
    leader = world.get(cast.leader)
    if success:
        leader.meters[f"attempt_{trick.id}"] += 1
    else:
        leader.meters[f"fail_{trick.id}"] += 1
    world.say(
        f'{leader.id} held her ground and said, "Not so! If you want us, '
        f'friend, first {trick.ask}."'
    )
    if not success:
        world.say(
            f"The Wolf twitched his tail and crept a little closer, "
            f"and the small folk's hearts went thump, thump, thump."
        )
    propagate(world, narrate=False)


def hold_the_line(world: World, cast: Cast) -> None:
    """A short beat between failed attempts: the small folk keep their nerve."""
    friends = [world.get(n) for n in cast.names if n != cast.leader]
    a = friends[0] if friends else world.get(cast.leader)
    b = friends[1] if len(friends) > 1 else a
    world.say(
        f'{a.id} whispered to {b.id}, "We can try another way." '
        f'{b.id} nodded bravely back.'
    )


def helper_appears(world: World, helper: Helper) -> None:
    h = world.add(Entity(
        id=helper.id, kind="character", type="robin", label=helper.name,
        traits=["brave", "kind"],
    ))
    h.meters["arrived"] += 1
    world.say(
        f"Just then down the lane came {helper.name}, "
        f"with a bright red cap and a steady tread."
    )


def helper_resolves(world: World, cast: Cast, helper: Helper) -> None:
    h = world.get(helper.id)
    propagate(world, narrate=False)
    world.say(
        f'{helper.name} {helper.horn}, and the Wolf stopped in his tracks.'
    )
    world.say(f"{helper.chase}, and the meadow was safe once more.")


def celebrate(world: World, cast: Cast) -> None:
    leader = world.get(cast.leader)
    friends = [world.get(n) for n in cast.names if n != cast.leader]
    all_names = " and ".join([leader.id] + [f.id for f in friends])
    world.say(
        f"The small folk clapped and twirled and laughed the long day through, "
        f"and {all_names} promised to come back tomorrow too."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, cast: Cast, helper: Helper,
         trick_order: list[Trick], winner: str) -> World:
    world = World(setting)
    # Register cast
    for name in cast.names:
        world.add(Entity(
            id=name, kind="character", type=name,
            traits=["little", "playful"],
        ))
    # Act 1
    introduce(world, cast)
    # Act 2 -- the small folk meet the Wolf and try to waylay him
    world.para()
    wolf_appears(world)
    freeze(world, cast)
    for i, trick in enumerate(trick_order):
        world.para()
        success = (trick.id == winner)
        try_trick(world, cast, trick, success)
        if not success and i < len(trick_order) - 1:
            hold_the_line(world, cast)
    # Act 3 -- the helper shows up and resolves the small problem
    world.para()
    helper_appears(world, helper)
    helper_resolves(world, cast, helper)
    # A last small flourish
    world.para()
    celebrate(world, cast)

    world.facts.update(
        cast=cast, helper=helper, setting=setting,
        trick_order=trick_order, winner=winner,
        leader=world.get(cast.leader),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "stile": Setting(place="the crooked stile", afford="waylay"),
    "lane": Setting(place="the winding lane", afford="waylay"),
    "green": Setting(place="the buttercup green", afford="waylay"),
    "bridge": Setting(place="the old stone bridge", afford="waylay"),
}

CASTS = {
    "mary_leads": Cast(names=["mary", "jack", "jill", "boy_blue"], leader="mary"),
    "jack_leads": Cast(names=["jack", "mary", "jill", "boy_blue"], leader="jack"),
    "jill_leads": Cast(names=["jill", "mary", "jack", "boy_blue"], leader="jill"),
    "small_pair": Cast(names=["mary", "jill", "boy_blue"], leader="mary"),
    "full_flock": Cast(names=["mary", "jack", "jill", "boy_blue"], leader="mary"),
}

TRICKS = [
    Trick(
        id="riddle",
        ask="answer this riddle: 'what is soft, and runs, and has no feet?'",
        beat="the Wolf cannot think of the right word",
        flourish="And the Wolf scratched his ear.",
        tags={"riddle", "mind"},
    ),
    Trick(
        id="trade",
        ask="trade us three eggs from the hayloft for the path home",
        beat="the Wolf does not know where the hayloft is",
        flourish="And the Wolf sniffed the air.",
        tags={"trade", "kind"},
    ),
    Trick(
        id="test",
        ask="pass the kind test: bring water to the smallest one",
        beat="the Wolf does not know how to be kind",
        flourish="And the Wolf looked away.",
        tags={"test", "heart"},
    ),
]

HELPERS = [
    Helper(
        id="robin",
        name="Bold Robín",
        horn="blew his horn loud and clear",
        chase="The Wolf went running down the lane",
    ),
    Helper(
        id="piper",
        name="the merry Piper",
        horn="played a skipping, tripping tune",
        chase="The Wolf danced off on his tippy-toes",
    ),
    Helper(
        id="shepherd",
        name="the kind Shepherd",
        horn="called out in a steady, singing voice",
        chase="The Wolf trotted off through the dewy grass",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, cast, helper) triples that pass the reasonableness gate.

    Trick order is randomized; the winner is always one of the three kinds
    and is treated as a domain-level constraint. There is always at least
    one trick that successfully waylays the Wolf, so every combo is valid.
    """
    return [(p, c, h) for p in SETTINGS for c in CASTS for h in HELPERS]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single rhyme (deterministic given these)."""
    place: str
    cast: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cast, helper, setting, winner = f["cast"], f["helper"], f["setting"], f["winner"]
    return [
        f'Write a short nursery-rhyme for ages 3-5 on the theme "small folk '
        f'waylay a Wolf until help comes" that includes the words "waylay" and '
        f'"{winner}".',
        f'Tell a gentle, rhyming story where {cast.leader} leads {", ".join(cast.names)} '
        f'against a sneaky Wolf, and they try a riddle, a trade, and a test '
        f'before {helper.name} arrives at {setting.place}.',
        f'Write a simple nursery rhyme that ends with the small folk safe and '
        f'dancing, after they waylay the Wolf at {setting.place} with a {winner}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cast, helper, setting, winner = f["cast"], f["helper"], f["setting"], f["winner"]
    leader = world.get(cast.leader)
    failed = [t.id for t in f["trick_order"] if t.id != winner]
    failed_text = ", ".join(failed) if failed else "none"
    return [
        QAItem(
            question=(
                f'Who tried to waylay the Wolf when the small folk met him at '
                f'{setting.place}?'
            ),
            answer=(
                f'{leader.id.capitalize()} led the small folk and tried to waylay '
                f'the Wolf. She tried a riddle, a trade, and a kind test, but '
                f'only the {winner} made the Wolf stop and think.'
            ),
        ),
        QAItem(
            question=(
                f'Which of the three ways — riddle, trade, or test — actually '
                f'waylaid the Wolf for {leader.id} and friends?'
            ),
            answer=(
                f'The {winner} waylaid the Wolf. The {failed_text} made him creep '
                f'closer, but the {winner} made him pause long enough for help '
                f'to come.'
            ),
        ),
        QAItem(
            question=(
                f'Who came down the lane to help {leader.id} when the small '
                f'folk were still waylaying the Wolf?'
            ),
            answer=(
                f'{helper.name} came down the lane. {helper.name.capitalize()} '
                f'{helper.horn}, and {helper.chase.lower()}, so the meadow was '
                f'safe once more.'
            ),
        ),
        QAItem(
            question=(
                f'Where did the small folk go after the Wolf ran off and they '
                f'had waylaid him at {setting.place}?'
            ),
            answer=(
                f'They clapped and twirled and laughed the long day through, '
                f'and promised to come back to {setting.place} tomorrow too.'
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to waylay someone?",
            answer=(
                "To waylay someone is to stop them, slow them down, or hold "
                "their attention with a clever question, a kind offer, or a "
                "small test, so they cannot get to where they were heading."
            ),
        ),
        QAItem(
            question="What is Problem Solving?",
            answer=(
                "Problem Solving is trying one idea, then another, until you "
                "find the one that works. If the first try does not fix the "
                "trouble, you stop, think, and try a different way."
            ),
        ),
        QAItem(
            question="Why is a riddle a good way to waylay a Wolf?",
            answer=(
                "A riddle is a good way to waylay a Wolf because it makes him "
                "stop and think. While he is scratching his ear, the small "
                "folk have time to gather their courage and call for help."
            ),
        ),
        QAItem(
            question="Why might a kind test waylay a Wolf?",
            answer=(
                "A kind test waylays a Wolf because it asks him to do something "
                "soft, like bringing water to a small friend. He does not know "
                "how to be kind, and so he hesitates long enough for help to "
                "come."
            ),
        ),
        QAItem(
            question="What is a nursery rhyme?",
            answer=(
                "A nursery rhyme is a short, rhyming poem for very young "
                "children. It often has a steady beat and repeats small, "
                "playful words so the story is easy to say and remember."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this rhyme =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from this rhyme ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no rhyme needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated set used by --all
CURATED = [
    StoryParams(place="stile", cast="mary_leads", helper="robin"),
    StoryParams(place="lane", cast="jack_leads", helper="piper"),
    StoryParams(place="green", cast="jill_leads", helper="shepherd"),
    StoryParams(place="bridge", cast="small_pair", helper="robin"),
    StoryParams(place="stile", cast="full_flock", helper="shepherd"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A cast can meet a Wolf at a setting if the cast is nonempty and there is
% a helper who can be called.  Every (place, cast, helper) triple is
% reasonable in this domain -- the trick order is randomized at narrative
% time, and one of the three trick kinds is always declared the winner.
valid(P, C, H) :- place(P), cast(C), helper(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for cid, c in CASTS.items():
        lines.append(asp.fact("cast", cid))
        for n in c.names:
            lines.append(asp.fact("member", cid, n))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
    for t in TRICKS:
        lines.append(asp.fact("trick", t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small folk waylay a Wolf in a "
                    "nursery-rhyme setting. Unspecified choices are picked at "
                    "random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cast", choices=CASTS)
    ap.add_argument("--helper", choices=[h.id for h in HELPERS])
    ap.add_argument("-n", type=int, default=1, help="number of rhymes to generate")
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
              and (args.cast is None or c[1] == args.cast)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, cast_id, helper_id = rng.choice(sorted(combos))
    return StoryParams(place=place, cast=cast_id, helper=helper_id)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random((params.seed or 0) ^ hash(params.cast) ^ hash(params.helper))
    setting = SETTINGS[params.place]
    cast = CASTS[params.cast]
    helper = next(h for h in HELPERS if h.id == params.helper)
    # The three tricks are tried in a random order; one of them wins.
    trick_order = list(TRICKS)
    rng.shuffle(trick_order)
    winner = rng.choice([t.id for t in trick_order])
    world = tell(setting, cast, helper, trick_order, winner)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, cast, helper) combos:\n")
        for place, cast_id, helper_id in triples:
            print(f"  {place:9} {cast_id:14} {helper_id}")
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
            header = f"### {p.cast} at {p.place} (helper: {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
