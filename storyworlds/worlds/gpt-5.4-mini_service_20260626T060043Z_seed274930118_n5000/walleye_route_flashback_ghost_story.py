#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/walleye_route_flashback_ghost_story.py
====================================================================================================================

A small standalone storyworld for a ghost-story style tale with a flashback,
built from the seed words "walleye" and "route".

Premise:
- A child travels a route near dark water at dusk.
- A friendly ghostly walleye appears when the route becomes hard to read.
- A flashback reveals an older memory that helps the child finish the trip.

The world is modeled as a tiny simulation:
- typed entities with physical meters and emotional memes
- state changes drive the prose
- a reasonableness gate ensures only plausible story combinations are generated
- an inline ASP twin mirrors the Python gate for verification
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

# -----------------------------------------------------------------------------
# World model
# -----------------------------------------------------------------------------

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

    def __post_init__(self) -> None:
        for k in ["tired", "wet", "lost", "safe", "glow", "memory"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "fear", "wonder", "relief", "missing", "love", "memory"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    atmosphere: str
    route: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class GhostGuide:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    appears_when: set[str] = field(default_factory=set)
    flashback_key: str = "memory"
    glow_word: str = "glow"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.route_clear: bool = False
        self.flashback_seen: bool = False
        self.ghost_seen: bool = False

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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.route_clear = self.route_clear
        clone.flashback_seen = self.flashback_seen
        clone.ghost_seen = self.ghost_seen
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------

SETTINGS = {
    "foggy_lake_route": Setting(
        place="the foggy lake route",
        atmosphere="foggy",
        route="the narrow path along the lake",
        afford={"walk"},
    ),
    "marsh_path": Setting(
        place="the marsh path",
        atmosphere="misty",
        route="the boardwalk over reeds",
        afford={"walk"},
    ),
    "woodland_lane": Setting(
        place="the woodland lane",
        atmosphere="dusky",
        route="the curve between tall trees",
        afford={"walk"},
    ),
}

TOKENS = {
    "lantern": Token(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        region="hand",
    ),
    "map": Token(
        id="map",
        label="map",
        phrase="a folded paper map",
        region="hand",
    ),
    "coat": Token(
        id="coat",
        label="coat",
        phrase="a warm red coat",
        region="torso",
    ),
}

GHOSTS = {
    "walleye": GhostGuide(
        id="walleye",
        label="walleye",
        phrase="a pale walleye with a silver eye",
        helps={"find_route", "remember", "calm"},
        appears_when={"fog", "lost"},
        flashback_key="memory",
        glow_word="glimmer",
    ),
}

GIRL_NAMES = ["Mina", "June", "Ellie", "Ada", "Nora"]
BOY_NAMES = ["Owen", "Ira", "Theo", "Finn", "Eli"]
TRAITS = ["careful", "curious", "quiet", "brave", "small"]

CURATED = [
    ("foggy_lake_route", "lantern", "Mina", "girl", "mother", "careful"),
    ("marsh_path", "map", "Owen", "boy", "father", "curious"),
    ("woodland_lane", "coat", "Nora", "girl", "mother", "quiet"),
]


# -----------------------------------------------------------------------------
# Parameters
# -----------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    token: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# -----------------------------------------------------------------------------
# Reasonableness gate
# -----------------------------------------------------------------------------

def route_at_risk(setting: Setting, token: Token) -> bool:
    return setting.place in {"the foggy lake route", "the marsh path", "the woodland lane"} and token.region == "hand"


def select_ghost(setting: Setting, token: Token) -> Optional[GhostGuide]:
    if token.id in {"lantern", "map"} and setting.atmosphere in {"foggy", "misty", "dusky"}:
        return GHOSTS["walleye"]
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for token_id, token in TOKENS.items():
            if route_at_risk(setting, token) and select_ghost(setting, token):
                combos.append((place, token_id))
    return combos


def explain_rejection(setting: Setting, token: Token) -> str:
    if not route_at_risk(setting, token):
        return (
            f"(No story: the {token.label} does not matter much on {setting.place}, "
            f"so there is no honest route problem to solve.)"
        )
    return (
        f"(No story: nothing in this setup gives the walleye a believable way to help "
        f"with the {token.label} on {setting.place}.)"
    )


# -----------------------------------------------------------------------------
# World logic
# -----------------------------------------------------------------------------

def _do_walk(world: World, child: Entity) -> None:
    child.meters["tired"] += 1
    child.memes["wonder"] += 1
    if world.setting.atmosphere in {"foggy", "misty", "dusky"}:
        child.memes["fear"] += 1
        child.meters["lost"] += 1


def _ghost_appears(world: World, child: Entity, ghost: GhostGuide) -> bool:
    if child.meters["lost"] < THRESHOLD:
        return False
    sig = ("ghost", ghost.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.ghost_seen = True
    child.meters["glow"] += 1
    child.memes["wonder"] += 1
    return True


def _flashback(world: World, child: Entity, ghost: GhostGuide) -> bool:
    if not world.ghost_seen or world.flashback_seen:
        return False
    sig = ("flashback", child.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.flashback_seen = True
    child.meters["memory"] += 1
    child.memes["memory"] += 1
    return True


def _find_route(world: World, child: Entity, token: Entity) -> bool:
    if not world.flashback_seen or world.route_clear:
        return False
    sig = ("route", child.id, token.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.route_clear = True
    child.meters["safe"] += 1
    child.memes["relief"] += 1
    token.meters["safe"] += 1
    return True


def propagate(world: World, child: Entity, ghost: GhostGuide, token: Entity) -> list[str]:
    out: list[str] = []
    if _ghost_appears(world, child, ghost):
        out.append(f"A pale walleye shimmered near the water, as if it knew the route.")
    if _flashback(world, child, ghost):
        out.append("The sight sent a flashback through the child's mind.")
    if _find_route(world, child, token):
        out.append("The memory made the route feel clear again.")
    return out


def tell(setting: Setting, token_cfg: Token, hero_name: str, hero_type: str, parent: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait],
    ))
    grownup = world.add(Entity(
        id="parent",
        kind="character",
        type=parent,
        label=f"the {parent}",
    ))
    token = world.add(Entity(
        id=token_cfg.id,
        type=token_cfg.label,
        label=token_cfg.label,
        phrase=token_cfg.phrase,
        owner=child.id,
        caretaker=grownup.id,
    ))
    ghost = GHOSTS["walleye"]

    world.say(
        f"{child.id} was a little {trait} {hero_type} who knew {setting.route} by heart."
    )
    world.say(
        f"One evening, {child.id} carried {token_cfg.phrase} and followed the {setting.atmosphere} route."
    )
    token.worn_by = child.id
    child.memes["love"] += 1

    world.para()
    _do_walk(world, child)
    world.say(
        f"The water and the trees grew dim, and {child.id} started to feel a little lost."
    )
    if world.setting.atmosphere == "foggy":
        world.say("The fog hid the stones and the bend in the path.")
    else:
        world.say("The dim light hid the safest turn in the route.")

    world.para()
    if _ghost_appears(world, child, ghost):
        world.say(
            f"Then a friendly ghostly walleye floated beside the bank, shining with a quiet {ghost.glow_word}."
        )
    if _flashback(world, child, ghost):
        world.say(
            f"At once, {child.id} had a flashback: {child.pronoun('possessive')} {parent} once said to "
            f"follow the bright stones and keep the lake on the left."
        )
    if _find_route(world, child, token):
        world.say(
            f"{child.id} looked at the stones, found the turn, and walked on without fear."
        )
        world.say(
            f"At the end of the route, {child.id} still had {token_cfg.phrase}, and the walleye was only a soft glow behind {child.pronoun('object')}."
        )

    world.facts.update(
        child=child,
        parent=grownup,
        token=token,
        token_cfg=token_cfg,
        ghost=ghost,
        setting=setting,
        resolved=world.route_clear,
    )
    return world


# -----------------------------------------------------------------------------
# QA
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    token = f["token_cfg"]
    return [
        f'Write a gentle ghost story for a young child that includes the word "walleye" and the word "route".',
        f"Tell a small story about {child.id} carrying {token.phrase} along a dark route, with a friendly ghost helping by memory.",
        f"Write a child-facing flashback story where a walleye leads a worried traveler back to the right route.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    token = f["token_cfg"]
    ghost = f["ghost"]
    setting = f["setting"]

    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {child.id}, a little {child.traits[1]} {child.type}, and the {parent.type} with them.",
        ),
        QAItem(
            question=f"What made the route feel scary?",
            answer=f"The {setting.atmosphere} air hid the route, so {child.id} started to feel lost before the walleye appeared.",
        ),
        QAItem(
            question=f"What did the ghostly walleye help with?",
            answer=f"The friendly ghostly walleye helped {child.id} remember the route and keep going safely.",
        ),
        QAItem(
            question=f"What did {child.id} carry on the walk?",
            answer=f"{child.id} carried {token.phrase} while following the route.",
        ),
    ]
    if world.flashback_seen:
        qa.append(
            QAItem(
                question="What happened in the flashback?",
                answer=(
                    f"In the flashback, {child.id} remembered the {parent.type}'s advice to follow the bright stones "
                    f"and keep the lake on the left."
                ),
            )
        )
    if world.route_clear:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=(
                    f"The route became clear again, {child.id} walked on with relief, and the walleye was left as a soft {ghost.glow_word} near the water."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a walleye?",
            answer="A walleye is a kind of fish that lives in water.",
        ),
        QAItem(
            question="What is a route?",
            answer="A route is a way to go from one place to another.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened before the main moment.",
        ),
        QAItem(
            question="Why can fog make a route hard to follow?",
            answer="Fog can make things look blurry and hide paths, signs, and turns.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  route_clear={world.route_clear}")
    lines.append(f"  flashback_seen={world.flashback_seen}")
    lines.append(f"  ghost_seen={world.ghost_seen}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------

ASP_RULES = r"""
route_at_risk(S, T) :- setting(S), token(T), route_region(T, hand), eerie(S).
has_guide(S, T) :- route_at_risk(S, T), ghost(walleye), helps(walleye, find_route), helps(walleye, remember).
valid_story(S, T) :- route_at_risk(S, T), has_guide(S, T).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.atmosphere in {"foggy", "misty", "dusky"}:
            lines.append(asp.fact("eerie", sid))
    for tid, t in TOKENS.items():
        lines.append(asp.fact("token", tid))
        lines.append(asp.fact("route_region", tid, t.region))
    for gid, g in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", gid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with a walleye, a route, and a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.token:
        setting = SETTINGS[args.place]
        token = TOKENS[args.token]
        if not route_at_risk(setting, token) or not select_ghost(setting, token):
            raise StoryError(explain_rejection(setting, token))

    combos = [
        (place, token)
        for place, token in valid_combos()
        if (args.place is None or place == args.place)
        and (args.token is None or token == args.token)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, token = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, token=token, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        TOKENS[params.token],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, token) combos:\n")
        for place, token in combos:
            print(f"  {place:18} {token}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(place=p, token=t, name=n, gender=g, parent=par, trait=tr))
            for (p, t), (n, g, par, tr) in zip(valid_combos(), CURATED)
        ]
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
            header = f"### {p.name}: {p.token} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
