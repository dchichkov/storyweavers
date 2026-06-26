#!/usr/bin/env python3
"""
storyworlds/worlds/manage_conflict_ghost_story.py
==================================================

A small ghost-story world with one child, one ghost, and one honest conflict
that can be managed in a gentle, child-facing way.

Seed inspiration:
- A child learns how to manage a conflict with a ghost in an old house.
- The ghost is not evil; it is lonely, noisy, and a little dramatic.
- The turn comes when the child finds a safer way for the ghost to be seen
  and heard without scaring everyone else.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    drafty: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Haunt:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def prize_at_risk(activity: Haunt, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Haunt, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, ghost: Entity, activity: Haunt, prize_id: str) -> dict:
    sim = copy_world(world)
    do_activity(sim, sim.get(ghost.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0) >= THRESHOLD),
        "scared": sum(e.memes.get("fear", 0) for e in sim.characters()),
    }


def copy_world(world: World) -> World:
    import copy
    clone = World(world.place)
    clone.entities = copy.deepcopy(world.entities)
    clone.fired = set(world.fired)
    clone.zone = set(world.zone)
    clone.paragraphs = [[]]
    clone.facts = dict(world.facts)
    return clone


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for s in _rule_scare(world):
            if s:
                changed = True
                out.append(s)
        for s in _rule_chill(world):
            if s:
                changed = True
                out.append(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _rule_scare(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters.get("cold", 0) < THRESHOLD:
            continue
        if e.memes.get("fear", 0) < THRESHOLD:
            continue
        sig = ("scare", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["conflict"] = e.memes.get("conflict", 0) + 1
        out.append(f"{e.id} felt the room turn spooky and held very still.")
    return out


def _rule_chill(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("cold", 0) < THRESHOLD or not e.caretaker:
            continue
        sig = ("chill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(e.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0) + 1
        out.append(f"That would give {carer.label} more to worry about.")
    return out


def do_activity(world: World, actor: Entity, activity: Haunt, narrate: bool = True) -> None:
    if activity.id not in world.place.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.meters["cold"] = actor.meters.get("cold", 0) + 1
    propagate(world, narrate=narrate)


def activity_line(activity: Haunt) -> str:
    return {
        "rattle": "the tiny rattle of chains sounded like someone tapping on a secret door",
        "whisper": "the whisper drifted through the hall like a cool ribbon",
        "float": "the ghost floated with a hush that made the candles wiggle",
    }.get(activity.id, "it made the old house feel awake")


def intro(world: World, child: Entity, ghost: Entity) -> None:
    world.say(
        f"{child.id} lived in the old house and knew the ghost in the hallway by name: {ghost.id}."
    )
    world.say(
        f"{ghost.id} was not scary on purpose; {ghost.pronoun()} was just lonely and a little dramatic."
    )


def love_haunt(world: World, ghost: Entity, activity: Haunt) -> None:
    ghost.memes["longing"] = ghost.memes.get("longing", 0) + 1
    world.say(
        f"{ghost.id} loved to {activity.verb}, and {activity_line(activity)}."
    )


def setup_prize(world: World, child: Entity, prize: Entity) -> None:
    world.say(
        f"{child.id} also cared about {child.pronoun('possessive')} {prize.label}, which sat right in the same hallway."
    )
    prize.worn_by = child.id
    prize.caretaker = child.id


def warn(world: World, child: Entity, ghost: Entity, activity: Haunt, prize: Entity) -> bool:
    pred = predict(world, ghost, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_scared"] = pred["scared"]
    world.say(
        f'"If you {activity.verb}, you will get {prize.label} {activity.soil}," {child.pronoun("possessive")} mama said.'
    )
    world.say(
        f"{ghost.id} went quiet, but the ghostly wishing still tugged hard."
    )
    return True


def manage_conflict(world: World, child: Entity, ghost: Entity, activity: Haunt) -> None:
    child.memes["bravery"] = child.memes.get("bravery", 0) + 1
    child.memes["conflict"] = child.memes.get("conflict", 0) + 1
    world.say(
        f"{child.id} took a breath and decided to manage the conflict instead of shouting over it."
    )
    world.say(
        f"{ghost.id} tried to {activity.rush}, but {child.id} stepped in with a kinder idea."
    )


def offer_gear(world: World, child: Entity, ghost: Entity, activity: Haunt, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    g = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
        owner=ghost.id,
    ))
    g.worn_by = ghost.id
    if predict(world, ghost, activity, prize.id)["soiled"]:
        del world.entities[g.id]
        return None
    world.say(
        f"{child.id} pointed to {gear.label} and said, \"What if you {gear.prep} first?\""
    )
    return gear


def accept(world: World, child: Entity, ghost: Entity, activity: Haunt, prize: Entity, gear: Gear) -> None:
    ghost.memes["joy"] = ghost.memes.get("joy", 0) + 1
    ghost.memes["lonely"] = max(0.0, ghost.memes.get("lonely", 1.0) - 1.0)
    child.memes["fear"] = max(0.0, child.memes.get("fear", 0) - 1.0)
    child.memes["conflict"] = 0.0
    world.say(
        f"{ghost.id} blinked, then smiled in a silver way. \"That might work,\" {ghost.pronoun()} whispered."
    )
    world.say(
        f"Soon {ghost.id} was {activity.gerund}, {prize.label} stayed clean, and the old house felt less tense."
    )
    world.say(
        f"The hallway windows glowed, and {child.id} and {ghost.id} listened together instead of startling each other."
    )


def tell(place: Place, activity: Haunt, prize_cfg: Prize, child_name: str, child_gender: str, helper: str) -> World:
    world = World(place)
    ghost = world.add(Entity(id="Murmur", kind="character", type="ghost", label="Murmur"))
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, label=child_name))
    helper_ent = world.add(Entity(id=helper, kind="character", type="mother", label=f"{helper}"))
    prize = world.add(Entity(
        id="lantern",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=ghost.id,
        caretaker=helper_ent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    intro(world, child, ghost)
    love_haunt(world, ghost, activity)
    setup_prize(world, child, prize)

    world.para()
    if place.dark:
        world.say(f"It was night, and {place.label} looked darker than a pocket under a pillow.")
    else:
        world.say(f"Even so, {place.label} had a hush that made every little sound seem louder.")
    world.say(f"{ghost.id} wanted to {activity.verb}, but that would bother the whole hallway.")
    warn(world, child, ghost, activity, prize)
    manage_conflict(world, child, ghost, activity)

    world.para()
    gear = offer_gear(world, child, ghost, activity, prize)
    if gear:
        accept(world, child, ghost, activity, prize, gear)

    world.facts.update(
        child=child,
        ghost=ghost,
        helper=helper_ent,
        prize=prize,
        activity=activity,
        place=place,
        gear=gear,
        resolved=gear is not None,
        conflict=child.memes.get("conflict", 0) > 0,
    )
    return world


PLACES = {
    "hallway": Place(id="hallway", label="the old hallway", dark=True, drafty=True, affords={"rattle", "whisper"}),
    "attic": Place(id="attic", label="the attic", dark=True, drafty=True, affords={"float", "whisper"}),
    "porch": Place(id="porch", label="the moonlit porch", dark=True, drafty=False, affords={"rattle", "float"}),
}

ACTIONS = {
    "rattle": Haunt(
        id="rattle",
        verb="rattle chains",
        gerund="rattling chains",
        rush="clatter down the hall",
        mess="cold",
        soil="frosty and damp",
        zone={"torso"},
        keyword="manage",
        tags={"ghost", "cold"},
    ),
    "whisper": Haunt(
        id="whisper",
        verb="whisper to the walls",
        gerund="whispering to the walls",
        rush="drift closer",
        mess="cold",
        soil="chilly and damp",
        zone={"torso"},
        keyword="ghost",
        tags={"ghost", "cold"},
    ),
    "float": Haunt(
        id="float",
        verb="float through the room",
        gerund="floating through the room",
        rush="glide into the doorway",
        mess="cold",
        soil="frosty",
        zone={"torso"},
        keyword="conflict",
        tags={"ghost", "cold"},
    ),
}

PRIZES = {
    "scarf": Prize(label="scarf", phrase="a soft blue scarf", type="scarf", region="torso"),
    "blanket": Prize(label="blanket", phrase="a warm patchwork blanket", type="blanket", region="torso", plural=False),
    "pajamas": Prize(label="pajamas", phrase="fluffy bedtime pajamas", type="pajamas", region="torso", plural=True),
}

GEAR = [
    Gear(id="lantern", label="a glowing lantern", covers={"torso"}, guards={"cold"}, prep="hold the lantern instead of rattling chains in the dark", tail="kept the lantern glowing by the door"),
    Gear(id="bell", label="a little silver bell", covers={"torso"}, guards={"cold"}, prep="ring the little silver bell softly on the porch", tail="set the little silver bell on the porch rail"),
    Gear(id="quilt", label="a thick quilt", covers={"torso"}, guards={"cold"}, prep="wrap the quilt around the chilly corner first", tail="left the thick quilt by the chair"),
]

CHILD_NAMES = ["Nina", "Milo", "Ada", "June", "Owen", "Lena"]
GENDERS = ["girl", "boy"]
HELPERS = ["mother", "father"]
TRAITS = ["brave", "quiet", "curious", "gentle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story about managing conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for aid in place.affords:
            act = ACTIONS[aid]
            for pr_id, pr in PRIZES.items():
                if prize_at_risk(act, pr) and select_gear(act, pr):
                    combos.append((pid, aid, pr_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize, name, gender, helper, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIONS[params.activity], PRIZES[params.prize], params.name, params.gender, params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, ghost, act, prize = f["child"], f["ghost"], f["activity"], f["prize"]
    return [
        f'Write a gentle ghost story for a young child that includes the word "{act.keyword}".',
        f"Tell a story where {child.id} helps {ghost.id} manage a conflict in {world.place.label} without ruining {prize.label}.",
        f"Write a small, spooky-but-kind story about a ghost who wants to {act.verb} and a child who finds a safer plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, prize, act = f["child"], f["ghost"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who was the story about in {world.place.label}?",
            answer=f"It was about {child.id} and the ghost named {ghost.id}. {child.id} tried to keep everyone calm in the old house.",
        ),
        QAItem(
            question=f"What did {ghost.id} want to do?",
            answer=f"{ghost.id} wanted to {act.verb}. That sounded spooky in the hallway, so {child.id} had to manage the conflict carefully.",
        ),
        QAItem(
            question=f"Why did {child.id} warn the ghost?",
            answer=f"{child.id} warned the ghost because {prize.label} would get {act.soil} if the ghost kept going. The warning was kind, not mean.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the story end when the ghost calmed down?",
            answer=f"It ended with {ghost.id} using {f['gear'].label} and {act.gerund} in a safer way. {prize.label} stayed clean, and the house felt less tense.",
        ))
    return qa


KNOWLEDGE = {
    "ghost": [("What is a ghost in a story?", "A ghost is often shown as a spooky, floating character in old stories.")],
    "cold": [("Why can a room feel cold at night?", "A room can feel cold at night because the air cools down and there may be a draft from outside.")],
    "manage": [("What does it mean to manage a problem?", "To manage a problem means to handle it carefully and keep it from getting worse.")],
    "lantern": [("What is a lantern for?", "A lantern gives off light so people can see in the dark.")],
    "conflict": [("What is a conflict in a story?", "A conflict is a problem or disagreement that the characters have to work through.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("manage")
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    tags.add("conflict")
    out: list[QAItem] = []
    for tag in ["ghost", "cold", "manage", "lantern", "conflict"]:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hallway", "rattle", "scarf", "Nina", "girl", "mother", "quiet"),
    StoryParams("attic", "whisper", "blanket", "Milo", "boy", "father", "curious"),
    StoryParams("porch", "float", "pajamas", "Ada", "girl", "mother", "gentle"),
]


def explain_rejection(activity: Haunt, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not reach the {prize.region}, so the conflict would not be real.)"
    return f"(No story: there is no safe gear in this world that can manage {activity.verb} without affecting the {prize.label}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(P,A,Pr) :- affords(P,A), prize_at_risk(A,Pr), has_fix(A,Pr).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("haunt", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pr_id, pr in PRIZES.items():
        lines.append(asp.fact("prize", pr_id))
        lines.append(asp.fact("worn_on", pr_id, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
