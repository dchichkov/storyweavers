#!/usr/bin/env python3
"""
storyworlds/worlds/rubbage_rhyme_twist_reconciliation_pirate_tale.py
====================================================================

A small pirate-tale storyworld about a tidy ship, a heap of rubbage, a tricky
twist, and a reconciliation that makes room for rhyme.

Seed tale:
---
On the Little Gull, Captain Mina loved neat decks and sing-song shanties.
One windy morning, a barrel burst open and rubbage rolled across the planks.
Old Jeb wanted to toss the whole heap into the sea, but Mina saw that the
rubbage was tied around a rolled-up rhyme chart.

Then the chart's rope gave a sudden twist and jammed the hatch.
The crew had to work together, sort the rubbage, free the chart, and make a
new tidy pile for the scraps.

In the end, Mina and Jeb laughed, shared the chart, and sang a rhyme while the
deck shone clear again.

World model:
---
    rubbage on deck -> deck.clutter += 1, crew.irritation += 1
    clustered rubbage near a twistable line -> line.twisted += 1
    a jammed hatch    -> ship.blocked += 1
    careful sorting   -> deck.clutter -= 1, chart.revealed += 1
    reconciliation   -> crew.annoyance -> 0, crew.warmth += 1

The world supports a small family of story variants:
- different pirate pairs
- different ship places
- different rubbage kinds
- different twisty problems
- different reconciliation helpers
- always ending with a clear physical image that proves the change
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
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owners: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain-female"}
        male = {"boy", "father", "dad", "man", "captain-male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str
    feature: str
    affordance: str


@dataclass
class Rubbage:
    id: str
    label: str
    phrase: str
    kind: str
    mess: str
    clue: str
    fits: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    label: str
    phrase: str
    jam: str
    object_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reconciliation:
    id: str
    label: str
    phrase: str
    method: str
    end_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        c = World(self.scene)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_rubbage_clutter(world: World) -> list[str]:
    out = []
    deck = world.get("deck")
    chart = world.get("chart")
    for actor in world.characters():
        if actor.meters["rubbage"] < THRESHOLD:
            continue
        sig = ("clutter", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        deck.meters["clutter"] += 1
        actor.memes["irritation"] += 1
        if chart.attrs.get("tied_to_rubbage"):
            chart.meters["hidden"] += 1
        out.append(f"The deck grew cluttered with rubbage.")
    return out


def _r_twist_jam(world: World) -> list[str]:
    ship = world.get("ship")
    line = world.get("line")
    for actor in world.characters():
        if actor.meters["rubbage"] < THRESHOLD or world.get("line").meters["twist"] < THRESHOLD:
            continue
        sig = ("jam", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ship.meters["blocked"] += 1
        line.meters["jammed"] += 1
        return ["__jam__"]
    return []


def _r_sort_reveal(world: World) -> list[str]:
    chart = world.get("chart")
    deck = world.get("deck")
    if deck.meters["sorting"] < THRESHOLD:
        return []
    sig = ("reveal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    deck.meters["clutter"] = max(0.0, deck.meters["clutter"] - 1)
    chart.meters["revealed"] += 1
    chart.attrs["found"] = True
    return ["The rhyme chart showed itself again."]


CAUSAL_RULES = [
    Rule("clutter", "physical", _r_rubbage_clutter),
    Rule("twist_jam", "physical", _r_twist_jam),
    Rule("sort_reveal", "physical", _r_sort_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                out.extend([s for s in items if s != "__jam__"])
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_blockage(world: World, actor_id: str) -> dict:
    sim = world.copy()
    sim.get(actor_id).meters["rubbage"] += 1
    propagate(sim, narrate=False)
    return {"blocked": sim.get("ship").meters["blocked"] >= THRESHOLD,
            "chart_hidden": sim.get("chart").meters["hidden"] >= THRESHOLD}


def valid_combo(scene: str, rubbage: str, twist: str, reconcile: str) -> bool:
    return scene in SCENES and rubbage in RUBBAGE and twist in TWISTS and reconcile in RECONCILE


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SCENES:
        for r in RUBBAGE:
            for t in TWISTS:
                for x in RECONCILE:
                    if r.fits & t.blocks and t.twistable and x.can_fix:
                        combos.append((s, r.id, t.id, x.id))
    return combos


@dataclass
class StoryParams:
    scene: str
    rubbage: str
    twist: str
    reconcile: str
    captain: str
    mate: str
    captain_type: str
    mate_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate storyworld about rubbage, rhyme, twist, and reconciliation.")
    ap.add_argument("--scene", choices=SCENES.keys())
    ap.add_argument("--rubbage", choices=RUBBAGE.keys())
    ap.add_argument("--twist", choices=TWISTS.keys())
    ap.add_argument("--reconcile", choices=RECONCILE.keys())
    ap.add_argument("--captain")
    ap.add_argument("--mate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.scene is None or c[0] == args.scene)
              and (args.rubbage is None or c[1] == args.rubbage)
              and (args.twist is None or c[2] == args.twist)
              and (args.reconcile is None or c[3] == args.reconcile)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, rubbage, twist, reconcile = rng.choice(sorted(combos))
    cap = args.captain or rng.choice(CAPTAIN_NAMES)
    mate = args.mate or rng.choice(MATE_NAMES)
    cap_type = rng.choice(["captain-female", "captain-male"])
    mate_type = rng.choice(["boy", "girl"])
    return StoryParams(scene=scene, rubbage=rubbage, twist=twist, reconcile=reconcile,
                       captain=cap, mate=mate, captain_type=cap_type, mate_type=mate_type)


def tell(params: StoryParams) -> World:
    scene = SCENES[params.scene]
    rubbage = RUBBAGE[params.rubbage]
    twist = TWISTS[params.twist]
    recon = RECONCILE[params.reconcile]
    world = World(scene)
    captain = world.add(Entity(id=params.captain, kind="character", type=params.captain_type, role="captain"))
    mate = world.add(Entity(id=params.mate, kind="character", type=params.mate_type, role="mate"))
    ship = world.add(Entity(id="ship", type="ship", label="the ship"))
    deck = world.add(Entity(id="deck", type="deck", label="the deck"))
    line = world.add(Entity(id="line", type="line", label=twist.label))
    chart = world.add(Entity(id="chart", type="chart", label="the rhyme chart", attrs={"tied_to_rubbage": True}))
    world.facts = {
        "captain": captain, "mate": mate, "rubbage": rubbage, "twist": twist,
        "reconcile": recon, "scene": scene, "ship": ship, "deck": deck,
        "line": line, "chart": chart
    }
    captain.meters["rubbage"] = 1
    mate.meters["sorting"] = 1
    world.say(f"On {scene.place}, {captain.id} loved clean decks and bright rhyme.")
    world.say(f"But one morning, {rubbage.phrase} spilled across {scene.affordance}, making a messy heap.")
    world.para()
    if predict_blockage(world, captain.id)["blocked"]:
        world.say(f"{mate.id} frowned at the heap. \"That rubbage is a pirate-sized bother,\" {mate.id} said.")
    world.say(f"{captain.id} wanted to sweep it away at once, but {mate.id} pointed to {chart.clue}.")
    world.say(f"Then {twist.phrase} gave a tricky twist, and {twist.jam} happened.")
    captain.meters["rubbage"] += 1
    world.get("line").meters["twist"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"So the crew slowed down, sorted the {rubbage.kind}, and loosened the twist with care.")
    deck.meters["sorting"] = 1
    propagate(world, narrate=True)
    world.say(f"{recon.phrase}. {captain.id} and {mate.id} smiled, shared the chart, and made peace over a rhyme.")
    captain.memes["warmth"] += 1
    mate.memes["warmth"] += 1
    captain.memes["irritation"] = 0
    mate.memes["irritation"] = 0
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate story for a young child that includes the word "{f["rubbage"].label}" and ends with a rhyme.',
        f'Tell a gentle ship story where {f["captain"].id} and {f["mate"].id} handle messy {f["rubbage"].kind}, a tricky twist, and then reconcile.',
        f'Write a short tale about a pirate deck, a hidden rhyme chart, and a way to fix the rubbage without losing the song.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cap = f["captain"]
    mate = f["mate"]
    rub = f["rubbage"]
    twist = f["twist"]
    recon = f["reconcile"]
    return [
        QAItem(question=f"Who is the pirate story about?", answer=f"It is about {cap.id} and {mate.id}, two pirates on {f['scene'].place}. They try to keep the ship neat while the rubbage causes trouble."),
        QAItem(question=f"Why did {mate.id} worry about the rubbage?", answer=f"{mate.id} worried because the {rub.kind} spread across the deck and could hide the rhyme chart. It also made the ship feel cluttered instead of ready for singing."),
        QAItem(question=f"What twist caused extra trouble?", answer=f"{twist.phrase} caused a jam, and that jam blocked the ship for a while. The crew had to slow down and untwist the line with care."),
        QAItem(question=f"How did {cap.id} and {mate.id} fix the problem?", answer=f"They sorted the {rub.kind}, loosened the twist, and shared the chart again. After that, they reconciled and the deck became neat and ready for a rhyme."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["rubbage"].tags) | set(world.facts["twist"].tags) | set(world.facts["reconcile"].tags)
    out = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(QAItem(q, a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.rubbage not in RUBBAGE or params.twist not in TWISTS or params.reconcile not in RECONCILE:
        raise StoryError("Invalid params.")
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
rubbage_on_deck(D) :- actor_rubbage(D).
twist_jams_ship :- actor_rubbage(_), twistable_line.
reconcile_ok :- sorting_done, twist_unjammed.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in SCENES:
        lines.append(asp.fact("scene", k))
    for k, r in RUBBAGE.items():
        lines.append(asp.fact("rubbage", k))
        for t in sorted(r.fits):
            lines.append(asp.fact("fits", k, t))
    for k, t in TWISTS.items():
        lines.append(asp.fact("twist", k))
        for b in sorted(t.blocks):
            lines.append(asp.fact("blocks", k, b))
        if t.twistable:
            lines.append(asp.fact("twistable", k))
    for k, r in RECONCILE.items():
        lines.append(asp.fact("reconcile", k))
        if r.can_fix:
            lines.append(asp.fact("can_fix", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import sys as _sys
    import io
    combos_ok = set(valid_combos()) == set(asp_valid_combos())
    if not combos_ok:
        print("ASP mismatch")
        return 1
    # smoke test ordinary generation
    sample = generate(resolve_params(argparse.Namespace(scene=None, rubbage=None, twist=None, reconcile=None, captain=None, mate=None), random.Random(777)))
    if not sample.story or not sample.prompts:
        print("Smoke test failed")
        return 1
    print("OK")
    return 0


SCENES = {
    "deck": Scene(place="the Little Gull's deck", feature="the deck shone in the salt wind", affordance="the planks"),
    "hold": Scene(place="the cargo hold", feature="the hold smelled of rope and tar", affordance="the floorboards"),
    "cabin": Scene(place="the captain's cabin", feature="the cabin had a small round window", affordance="the table"),
    "harbor": Scene(place="the harbor pier", feature="the pier creaked beside the waves", affordance="the boards"),
}

RUBBAGE = {
    "scraps": Rubbage(id="scraps", label="rubbage", phrase="A burst barrel dropped rubbage", kind="scraps", mess="clutter", clue="a rolled-up rhyme chart hid beneath the scraps", fits={"line", "chart"}, tags={"rubbage", "clutter"}),
    "nets": Rubbage(id="nets", label="rubbage", phrase="A knot of old nets tangled into rubbage", kind="nets", mess="snarl", clue="a rhyme chart was tied into the nets", fits={"line", "chart"}, tags={"rubbage"}),
    "shells": Rubbage(id="shells", label="rubbage", phrase="A crate of broken shells spilled rubbage everywhere", kind="shells", mess="shards", clue="a rhyme chart was tucked under the shells", fits={"chart"}, tags={"rubbage"}),
    "ropebits": Rubbage(id="ropebits", label="rubbage", phrase="Tiny ropebits skittered from a torn sack and became rubbage", kind="ropebits", mess="tangle", clue="a rhyme chart was looped to the ropebits", fits={"line", "chart"}, tags={"rubbage"}),
}

TWISTS = {
    "rope": Twist(id="rope", label="rope twist", phrase="A rope twist", jam="the hatch stuck fast", object_kind="line", tags={"twist"}),
    "line": Twist(id="line", label="line twist", phrase="A line twist", jam="the line bound the latch", object_kind="line", tags={"twist"}),
    "hook": Twist(id="hook", label="hook twist", phrase="A hook twist", jam="the hook caught the hatch", object_kind="hook", tags={"twist"}),
    "knot": Twist(id="knot", label="knot twist", phrase="A knot twist", jam="the knot jammed the crate lid", object_kind="knot", tags={"twist"}),
}
for t in TWISTS.values():
    t.twistable = True
    t.blocks = {"line", "chart"}

RECONCILE = {
    "share": Reconciliation(id="share", label="sharing", phrase="They shared the rhyme chart at last", method="shared the chart", end_image="the chart lay flat on the clean deck", tags={"reconcile"}),
    "laugh": Reconciliation(id="laugh", label="laughing it off", phrase="They laughed, then set their worries aside", method="laughed together", end_image="the deck gleamed under a bright laugh", tags={"reconcile"}),
    "tidy": Reconciliation(id="tidy", label="tidying together", phrase="They tidied together and made peace", method="tidied together", end_image="the deck was neat again", tags={"reconcile"}),
    "sing": Reconciliation(id="sing", label="singing together", phrase="They sang a new rhyme and made up", method="sang the same tune", end_image="the rhyme chart hung clear and dry", tags={"reconcile"}),
}
for r in RECONCILE.values():
    r.can_fix = True

CAPTAIN_NAMES = ["Mina", "Tess", "Rae", "June", "Nell", "Ivy"]
MATE_NAMES = ["Jeb", "Pip", "Owen", "Bea", "Finn", "Lark"]


def explain_rejection() -> str:
    return "(No story: the chosen rubbage, twist, and reconciliation do not fit together.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        curated = [
            StoryParams(scene="deck", rubbage="scraps", twist="rope", reconcile="share", captain="Mina", mate="Jeb", captain_type="captain-female", mate_type="boy"),
            StoryParams(scene="hold", rubbage="nets", twist="line", reconcile="tidy", captain="Tess", mate="Pip", captain_type="captain-female", mate_type="boy"),
            StoryParams(scene="cabin", rubbage="shells", twist="hook", reconcile="laugh", captain="Rae", mate="Bea", captain_type="captain-male", mate_type="girl"),
            StoryParams(scene="harbor", rubbage="ropebits", twist="knot", reconcile="sing", captain="June", mate="Lark", captain_type="captain-female", mate_type="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        header = ""
        if args.all:
            p = s.params
            header = f"### {p.captain} and {p.mate} on {p.scene} ({p.rubbage}, {p.twist}, {p.reconcile})"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
