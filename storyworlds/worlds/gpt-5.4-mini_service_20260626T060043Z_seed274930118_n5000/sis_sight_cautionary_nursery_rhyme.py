#!/usr/bin/env python3
"""
storyworlds/worlds/sis_sight_cautionary_nursery_rhyme.py
=========================================================

A tiny cautionary nursery-rhyme storyworld about a little sis, a curious sight,
and a safer way home.

Premise:
- A little sis loves to wander and look at shiny sights.
- A warning arrives when the sight is beautiful but risky.
- The story turns when a caring helper offers a safer way.
- The ending image proves the child learned caution and came home safely.

The model keeps a small world state with physical meters and emotional memes,
then narrates from that state.
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


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("dust", "dark", "lost", "safe", "shine"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "joy", "caution", "fear", "trust"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "sister", "sis"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Sight:
    id: str
    noun: str
    glow: str
    danger: str
    verb: str
    path: str
    risk: str
    tag: str


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    protective: bool = True


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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lane": Setting(place="the moonlit lane", indoor=False, affords={"glow", "wander"}),
    "garden": Setting(place="the sleepy garden", indoor=False, affords={"glow", "wander"}),
    "porch": Setting(place="the front porch", indoor=False, affords={"glow", "wander"}),
}

SIGHTS = {
    "fireflies": Sight(
        id="fireflies",
        noun="fireflies",
        glow="tiny golden",
        danger="far into the dark grass",
        verb="follow the fireflies",
        path="the dark grass path",
        risk="lost",
        tag="glow",
    ),
    "lantern": Sight(
        id="lantern",
        noun="lantern light",
        glow="warm and bright",
        danger="down the muddy steps",
        verb="reach for the lantern light",
        path="the muddy steps",
        risk="dark",
        tag="glow",
    ),
    "brook": Sight(
        id="brook",
        noun="silver water",
        glow="silver",
        danger="over the little stone bridge",
        verb="stare at the silver water",
        path="the little stone bridge",
        risk="lost",
        tag="wander",
    ),
}

GEAR = [
    Gear(
        id="handhold",
        label="a grown-up hand",
        phrase="a grown-up hand",
        prep="take my hand and keep close",
        tail="held tight to the porch light and came home",
        guards={"lost", "dark"},
        covers={"path"},
    ),
    Gear(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern",
        prep="carry a little lantern",
        tail="walked with the lantern and the lane felt clear",
        guards={"dark", "lost"},
        covers={"path"},
    ),
    Gear(
        id="boots",
        label="rubber boots",
        phrase="rubber boots",
        prep="put on rubber boots",
        tail="pattered home in the boots and skipped the mud",
        guards={"dark"},
        covers={"path"},
        plural=True,
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Nora", "Ivy", "Rose", "Pippa"]
HELPER_NAMES = ["Mum", "Nan", "Aunt May", "Big Sis", "Grandpa"]
TRAITS = ["little", "curious", "brave", "sleepy", "sly"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    sight: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rule helpers
# ---------------------------------------------------------------------------
def sight_at_risk(sight: Sight) -> bool:
    return sight.risk in {"lost", "dark"}


def select_gear(sight: Sight) -> Optional[Gear]:
    for gear in GEAR:
        if sight.risk in gear.guards:
            return gear
    return None


def predict(world: World, child: Entity, sight: Sight, gear: Optional[Gear]) -> dict:
    sim = world.copy()
    child2 = sim.get(child.id)
    child2.memes["curiosity"] += 1
    child2.meters["lost"] += 1
    if sight.risk == "dark":
        child2.meters["dark"] += 1
    if gear:
        child2.meters["safe"] += 1
        child2.memes["caution"] += 1
    return {
        "lost": child2.meters["lost"] >= THRESHOLD and gear is None,
        "safe": child2.meters["safe"] >= THRESHOLD,
    }


def _r_lost(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["lost"] < THRESHOLD:
            continue
        sig = ("lost", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] += 1
        out.append(f"The lane grew long, and {actor.id} began to feel a little lost.")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["trust"] < THRESHOLD or actor.meters["safe"] < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = 0.0
        actor.memes["joy"] += 1
        out.append(f"The worry settled down once {actor.id} stayed close and safe.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_lost, _r_calm):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def introduce(world: World, child: Entity, helper: Entity, sight: Sight) -> None:
    world.say(
        f"Little {child.id} was a {next(t for t in child.traits if t != 'little')} child "
        f"who loved every bright sight."
    )
    world.say(
        f"{child.pronoun().capitalize()} liked to {sight.verb}, for {sight.glow} things made the night seem light."
    )


def begin(world: World, child: Entity, helper: Entity, sight: Sight) -> None:
    world.say(
        f"One evening, {child.id} went out with {child.pronoun('possessive')} {helper.label_word} to {world.setting.place}."
    )
    world.say(f"There, the {sight.noun} shone {sight.glow} by {sight.danger}.")


def warn(world: World, helper: Entity, child: Entity, sight: Sight) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'"Do not {sight.verb}," said {helper.id}. "It can lead you down {sight.path}."'
    )


def defy(world: World, child: Entity, sight: Sight) -> None:
    child.memes["curiosity"] += 1
    child.meters["lost"] += 1
    world.say(
        f"But {child.id} still leaned toward the sight, and {child.pronoun()} almost stepped away."
    )
    world.say(f"{child.id} tried to go after {sight.noun}.")


def offer(world: World, helper: Entity, child: Entity, sight: Sight) -> Optional[Gear]:
    gear = select_gear(sight)
    if gear is None:
        return None
    world.say(f"Then {helper.id} smiled and said, \"How about we {gear.prep}?\"")
    return gear


def accept(world: World, child: Entity, helper: Entity, sight: Sight, gear: Gear) -> None:
    child.memes["trust"] += 1
    child.memes["caution"] += 1
    child.meters["safe"] += 1
    child.meters["lost"] = 0.0
    world.say(
        f"{child.id} nodded and took the safer way."
    )
    world.say(
        f"Together they {gear.tail}, and {child.id} stayed beside {helper.id}, where the path was plain."
    )
    world.say(
        f"In the end, the bright sight was lovely, but {child.id} learned to keep close and come home again."
    )


def tell(setting: Setting, sight: Sight, hero_name: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type="girl", traits=["little", trait, "curious"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="woman", label=helper_name.lower()))
    world.facts.update(child=child, helper=helper, sight=sight, setting=setting)

    introduce(world, child, helper, sight)
    world.para()
    begin(world, child, helper, sight)
    warn(world, helper, child, sight)
    defy(world, child, sight)
    propagate(world, narrate=True)

    world.para()
    gear = offer(world, helper, child, sight)
    if gear:
        accept(world, child, helper, sight, gear)

    world.facts["gear"] = gear
    world.facts["resolved"] = gear is not None
    return world


# ---------------------------------------------------------------------------
# Reasonableness and content generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting in SETTINGS:
        for sight_id, sight in SIGHTS.items():
            if sight_at_risk(sight) and select_gear(sight):
                combos.append((setting, sight_id))
    return combos


def explain_rejection(sight: Sight) -> str:
    return (
        f"(No story: the sight '{sight.noun}' has no safe helper in this little world. "
        f"Try another sight that can be handled with a cautionary fix.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Cautionary nursery-rhyme storyworld about sis and a risky sight."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sight", choices=SIGHTS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    if args.sight:
        sight = SIGHTS[args.sight]
        if not sight_at_risk(sight) or select_gear(sight) is None:
            raise StoryError(explain_rejection(sight))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.sight is None or c[1] == args.sight)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sight = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        sight=sight,
        name=args.name or rng.choice(GIRL_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        trait=args.trait or rng.choice([t for t in TRAITS if t != "little"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, sight = f["child"], f["helper"], f["sight"]
    return [
        "Write a short cautionary nursery rhyme about sis and a tempting sight.",
        f"Tell a gentle rhyme where little {child.id} wants to {sight.verb} but {helper.id} gives a safer choice.",
        f"Write a child-friendly story that uses the words 'sis' and 'sight' and ends with a safe return home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, sight = f["child"], f["helper"], f["sight"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about little {child.id}, a curious sis who loves bright sights, and {helper.id}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do when she saw the {sight.noun}?",
            answer=f"{child.id} wanted to {sight.verb}, because the sight looked bright and sweet.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {child.id}?",
            answer=f"{helper.id} warned her because the sight could lead her down {sight.path} and make her feel lost.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did the safer plan help {child.id}?",
                answer=f"They used {gear.label}, so {child.id} could stay close and come home safely instead of chasing the sight alone.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word sight mean?",
            answer="A sight is something you can see, especially something that catches your eye.",
        ),
        QAItem(
            question="Why should a child stay close at night?",
            answer="A child should stay close at night because dark places can be hard to see and easy to get lost in.",
        ),
    ]


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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(lane). setting(garden). setting(porch).
sight(fireflies). sight(lantern). sight(brook).
risk(fireflies,lost). risk(lantern,dark). risk(brook,lost).
gear(handhold). gear(lantern). gear(boots).
guards(handhold,lost). guards(handhold,dark).
guards(lantern,lost). guards(lantern,dark).
guards(boots,dark).

safe_sight(S) :- sight(S), risk(S,R), guards(_,R).
valid(Setting,Sight) :- setting(Setting), sight(Sight), safe_sight(Sight).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for s in SIGHTS.values():
        lines.append(asp.fact("sight", s.id))
        lines.append(asp.fact("risk", s.id, s.risk))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


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


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SIGHTS[params.sight], params.name, params.helper, params.trait)
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


CURATED = [
    StoryParams(setting="lane", sight="fireflies", name="Lily", helper="Mum", trait="curious"),
    StoryParams(setting="garden", sight="brook", name="Nora", helper="Big Sis", trait="brave"),
    StoryParams(setting="porch", sight="lantern", name="Mia", helper="Nan", trait="sleepy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible (setting, sight) combos:\n")
        for item in vals:
            print(f"  {item[0]:8} {item[1]}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
