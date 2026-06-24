#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_service_20260623T073613Z_seed779406221_n50/english_nibble_manuscript_swimming_pool_sound_effects.py
=============================================================================================================

A small bedtime-story world set at a swimming pool, built from the seed words
"english", "nibble", and "manuscript". The tale uses sound effects, cautionary
beats, and repetition to tell a complete, state-driven story about a child who
must protect a precious manuscript from poolside splashes.

The premise:
- A child brings a handmade English practice manuscript to the swimming pool.
- The child wants to nibble a snack and relax beside the water.
- A careful guardian warns that splashes, drips, and wet hands can damage paper.

The turn:
- The child leans too close to the pool, and the manuscript is at risk.
- Repeated warning sounds and repeated caution phrases build gentle tension.
- A towel, a waterproof pouch, or a seat away from the edge can prevent damage.

The resolution:
- The child learns to keep the manuscript safe.
- The ending image proves the change: dry pages, a safe snack, and calm water.

This script is self-contained, uses only the stdlib at runtime, and follows the
shared Storyworld contract.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"wet": 0.0, "dirty": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "care": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the swimming pool"
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    risk: str
    safe_fix: str
    region: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    fix_line: str
    closing_line: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _r_wet(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            sig = ("wet", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["dirty"] += 1
            out.append(f"{item.label.capitalize()} got damp at the pool edge.")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    for item in world.entities.values():
        if item.meters["wet"] >= THRESHOLD and item.caretaker:
            sig = ("worry", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            carer = world.get(item.caretaker)
            carer.memes["worry"] += 1
            out.append(f"That made {carer.label} worry a little more.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_wet, _r_worry):
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk(item: Item) -> bool:
    return item.region in {"hands", "lap", "table"}


def select_helper(item: Item) -> Optional[Helper]:
    for h in HELPERS.values():
        if item.region in h.covers and item.risk in h.guards:
            return h
    return None


def predict_soggy(world: World, child: Entity, item: Entity) -> bool:
    sim = world.copy()
    _snack_and_splash(sim, sim.get(child.id), sim.get(item.id), narrate=False)
    return sim.get(item.id).meters["wet"] >= THRESHOLD


def _snack_and_splash(world: World, child: Entity, manuscript: Entity, narrate: bool = True) -> None:
    world.zone = {"hands", "lap", "table"}
    child.meters["wet"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, guardian: Entity, item: Entity) -> None:
    world.say(f"{child.id} came to the swimming pool with a tiny, careful smile.")
    world.say(
        f"Under one arm, {child.pronoun('possessive')} carried a handmade manuscript "
        f"for English practice, page by page and line by line."
    )
    world.say(
        f"{guardian.label.capitalize()} nodded and said the same gentle thing twice: "
        f"keep the paper dry, keep the paper dry."
    )


def snack(world: World, child: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} had a nibble of a crunchy cookie. Crunch, crunch. "
        f"The snack was sweet, and the pool water glittered nearby."
    )


def caution(world: World, guardian: Entity, child: Entity, item: Entity) -> None:
    guardian.memes["care"] += 1
    world.say(
        f'"Careful," {guardian.id} said. "Not near the edge. Not near the splash. '
        f'Not with the manuscript."'
    )
    if predict_soggy(world, child, item):
        world.say("Splish-splash, the warning felt true before the water even moved.")
    else:
        world.say("Still, the warning sat in the air like a soft bell.")


def temptation(world: World, child: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} leaned closer to listen to the happy sounds of the pool. "
        f"Plip-plop, plip-plop, went the water."
    )
    world.say(
        f"Then {child.id} reached for the manuscript with damp fingers and forgot, "
        f"for a moment, to be careful."
    )


def splash_turn(world: World, child: Entity, item: Entity) -> None:
    world.say("Splash! A small wave hopped over the edge.")
    _snack_and_splash(world, child, item)
    if item.meters["wet"] >= THRESHOLD:
        world.say(
            f"The manuscript shivered. One page curled at the corner, and the ink "
            f"on the English practice line looked worried."
        )


def fix(world: World, child: Entity, guardian: Entity, item: Entity) -> None:
    helper = select_helper(MANUSCRIPT)
    if helper is None:
        raise StoryError("No safe helper exists for the manuscript.")
    safe = world.add(Entity(
        id=helper.id, kind="thing", type="helper", label=helper.label,
        phrase=helper.phrase, protective=True, covers=set(helper.covers),
    ))
    safe.worn_by = child.id
    if predict_soggy(world, child, item):
        safe.worn_by = None
        del world.entities[safe.id]
        raise StoryError("The chosen helper does not actually keep the manuscript dry.")
    world.say(
        f'{guardian.id} smiled. "Let us fix this properly," {guardian.id} said, '
        f"and gave {child.id} {helper.phrase}."
    )
    world.say(helper.fix_line)
    world.say(helper.closing_line)


def ending(world: World, child: Entity, guardian: Entity, item: Entity) -> None:
    child.memes["worry"] = 0.0
    child.memes["joy"] += 1
    world.say(
        f"At last, {child.id} sat back from the water with {item.label} safe and dry."
    )
    world.say(
        f"{child.id} took another nibble, a small nibble, and turned one neat page "
        f"of English practice without a single drip."
    )
    world.say(
        f"The pool kept whispering its soft song, but the manuscript stayed clean, "
        f"and the bedtime sky felt calm and blue."
    )


def tell(setting: Setting, child_name: str = "Nia", child_type: str = "girl",
         guardian_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, label="the guardian"))
    manuscript = world.add(Entity(
        id="manuscript", type="manuscript", label="manuscript",
        phrase="a handmade English practice manuscript", owner=child.id,
        caretaker=guardian.id, region="hands", plural=False
    ))
    world.facts["child"] = child
    world.facts["guardian"] = guardian
    world.facts["manuscript"] = manuscript

    intro(world, child, guardian, manuscript)
    world.para()
    snack(world, child)
    caution(world, guardian, child, manuscript)
    temptation(world, child)
    world.para()
    splash_turn(world, child, manuscript)
    fix(world, child, guardian, manuscript)
    world.para()
    ending(world, child, guardian, manuscript)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "swimming_pool": Setting(place="the swimming pool", affords={"snack", "splash", "nibble"}),
}

MANUSCRIPT = Item(
    id="manuscript",
    label="manuscript",
    phrase="a handmade English practice manuscript",
    risk="wet",
    safe_fix="dry",
    region="hands",
    tags={"english", "manuscript"},
)

HELPERS = {
    "dry_bag": Helper(
        id="dry_bag",
        label="waterproof pouch",
        phrase="a waterproof pouch",
        covers={"hands", "lap", "table"},
        guards={"wet"},
        fix_line="It zipped up with a tiny zip-zip, and the paper sat dry inside.",
        closing_line="Zip-zip, safe and snug, the manuscript stayed out of the splash.",
        tags={"wet"},
    ),
    "towel": Helper(
        id="towel",
        label="dry towel",
        phrase="a dry towel",
        covers={"hands", "lap", "table"},
        guards={"wet"},
        fix_line="It wrapped around the pages like a warm blanket, keeping every sheet dry.",
        closing_line="Fluff-fluff, the towel made a dry nest for the words.",
        tags={"wet"},
    ),
}

CURATED = [
    StoryParams = None
]
# Replace placeholder list with real curated params below.
CURATED = [
    dataclass(type("StoryParams", (), {}))
]

@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    guardian_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str]]:
    return [("swimming_pool",)]


def explain_rejection() -> str:
    return "(No story: this world only takes place at the swimming pool.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: english, nibble, manuscript at the swimming pool.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--guardian-type", choices=["mother", "father"])
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
    return StoryParams(
        place=args.place or "swimming_pool",
        child_name=args.child_name or rng.choice(["Nia", "Milo", "Tia", "Owen"]),
        child_type=args.child_type or rng.choice(["girl", "boy"]),
        guardian_type=args.guardian_type or rng.choice(["mother", "father"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    return [
        'Write a bedtime story for a young child using the words "english", "nibble", and "manuscript".',
        f"Tell a gentle cautionary story where {c.id} brings a manuscript to the swimming pool and learns to keep it dry.",
        "Write a calm poolside story with sound effects, repetition, and a safe ending for a paper manuscript.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    g = world.facts["guardian"]
    m = world.facts["manuscript"]
    return [
        QAItem(
            question=f"What did {c.id} bring to the swimming pool?",
            answer=f"{c.id} brought a handmade English practice manuscript to the swimming pool. It was something special to keep dry.",
        ),
        QAItem(
            question=f"Why did {g.label} keep warning {c.id}?",
            answer=f"{g.label} kept warning {c.id} because wet hands and splashes could damage the manuscript. The repeated warning helped {c.id} remember to be careful.",
        ),
        QAItem(
            question=f"How did the story end for the manuscript?",
            answer=f"The manuscript ended the story safe and dry. {c.id} could keep practicing English without the pages getting ruined.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a manuscript?", "A manuscript is a page or set of pages with writing on them, like a draft or a practice book."),
        QAItem("What does nibble mean?", "To nibble means to take small bites, usually of a snack."),
        QAItem("What are sound effects in a story?", "Sound effects are words like splash or crunch that help you hear the scene in your mind."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"  {e.id:10} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


ASP_RULES = r"""
place(swimming_pool).
child_name(nia).
safe_place(P) :- place(P).
story_ok(P) :- safe_place(P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([asp.fact("place", "swimming_pool"), asp.fact("seed_word", "english"), asp.fact("seed_word", "nibble"), asp.fact("seed_word", "manuscript")])

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/1."))
    ok = bool(asp.atoms(model, "story_ok"))
    py = True
    if ok == py:
        print("OK: ASP and Python agree on the swimming pool world.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.child_name, params.child_type, params.guardian_type)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show story_ok/1."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(place="swimming_pool", child_name="Nia", child_type="girl", guardian_type="mother", seed=base_seed)
        samples = [generate(params)]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
