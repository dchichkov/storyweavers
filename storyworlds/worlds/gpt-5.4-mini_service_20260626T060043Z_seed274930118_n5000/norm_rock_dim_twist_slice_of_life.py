#!/usr/bin/env python3
"""
storyworlds/worlds/norm_rock_dim_twist_slice_of_life.py
=======================================================

A small slice-of-life storyworld about a child, a little rock, a home norm,
and a gentle twist.

Premise:
- A child finds a rock or small stone outside.
- The child wants to keep it close, maybe on a shelf or in a pocket.
- A parent has a simple home norm: dirty things stay out until they are cleaned.
- The child is disappointed, but the parent offers a small compromise.
- The twist: after washing, the rock reveals something lovely and unexpected.

This world is intentionally modest and concrete:
- meters track physical conditions like dirt, wetness, polish, and display-worthiness.
- memes track simple feelings like joy, disappointment, curiosity, and pride.
- the narration is state-driven, not a fixed template with swapped nouns.
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
    portable: bool = True
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("dirt", "wet", "polish", "display", "weight"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "curiosity", "disappointment", "pride", "calm"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    norms: list[str] = field(default_factory=list)
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    reveal_kind: str
    location: str
    needs_wash: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
    covers_norm: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


def _narrate(world: World, msg: str, narrate: bool = True) -> None:
    if narrate:
        world.say(msg)
    world.trace.append(msg)


def _child(world: World) -> Entity:
    return world.facts["child"]


def _parent(world: World) -> Entity:
    return world.facts["parent"]


def _rock(world: World) -> Entity:
    return world.facts["rock"]


def _gear(world: World) -> Optional[Entity]:
    return world.facts.get("gear")


def _activity(world: World) -> Activity:
    return world.facts["activity"]


def _apply_play(world: World, narrate: bool = True) -> None:
    child = _child(world)
    act = _activity(world)
    rock = _rock(world)
    child.meters[act.mess] += 1
    child.memes["joy"] += 1
    rock.meters[act.mess] += 1
    if act.mess == "dirt":
        rock.meters["dirt"] += 1
    if act.mess == "wet":
        rock.meters["wet"] += 1
    _narrate(world, f"{child.id} did not just hold the rock; {child.pronoun()} gave it a careful little turn in the hand.", narrate)
    _narrate(world, f"The rock felt more interesting after that, like it was waiting to be noticed.", narrate)


def _apply_wash(world: World, narrate: bool = True) -> None:
    rock = _rock(world)
    child = _child(world)
    gear = _gear(world)
    if gear is not None:
        child.memes["calm"] += 1
    rock.meters["dirt"] = max(0.0, rock.meters["dirt"] - 1.0)
    rock.meters["wet"] += 1.0
    rock.meters["polish"] += 1.0
    child.memes["curiosity"] += 1
    _narrate(world, f"{child.id} washed the rock in the bowl until the dark dust slid away.", narrate)
    _narrate(world, f"After the rinse, the stone looked smoother and brighter in the window light.", narrate)


def _apply_twist(world: World, narrate: bool = True) -> None:
    rock = _rock(world)
    child = _child(world)
    if rock.meters["polish"] < THRESHOLD:
        return
    if world.fired and ("twist", rock.id) in world.fired:
        return
    world.fired.add(("twist", rock.id))
    rock.meters["display"] += 1.0
    child.memes["joy"] += 1.0
    child.memes["pride"] += 1.0
    _narrate(world, f"Then came the twist: a faint stripe shone on the rock, like a secret smile waking up.", narrate)
    _narrate(world, f"It was not just a dull pebble anymore; it was a little treasure for the shelf.", narrate)


def _apply_norm(world: World, narrate: bool = True) -> None:
    child = _child(world)
    parent = _parent(world)
    rock = _rock(world)
    if rock.meters["dirt"] < THRESHOLD:
        return
    if ("norm", child.id) in world.fired:
        return
    world.fired.add(("norm", child.id))
    child.memes["disappointment"] += 1.0
    _narrate(world, f"{parent.id} smiled, but still held up the home norm: dirty things stayed outside until they were cleaned.", narrate)
    _narrate(world, f"{child.id} wanted to keep the rock close right away, and that made the rule feel extra hard.", narrate)


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        before = len(world.fired)
        _apply_norm(world, narrate)
        if world.fired and len(world.fired) > before:
            changed = True
        before = len(world.fired)
        _apply_wash(world, narrate)
        if len(world.fired) > before:
            changed = True
        before = len(world.fired)
        _apply_twist(world, narrate)
        if len(world.fired) > before:
            changed = True


SETTINGS = {
    "yard": Setting(
        place="the backyard",
        indoor=False,
        norms=["dirty things stay outside until they are cleaned"],
        affords={"find", "wash", "display"},
    ),
    "kitchen": Setting(
        place="the kitchen table",
        indoor=True,
        norms=["muddy hands get washed before snacks"],
        affords={"find", "wash", "display"},
    ),
    "porch": Setting(
        place="the porch step",
        indoor=False,
        norms=["wet things dry on the mat first"],
        affords={"find", "wash", "display"},
    ),
}

ACTIVITIES = {
    "find": Activity(
        id="find",
        verb="find a rock",
        gerund="finding rocks",
        rush="run to the fence line and scoop one up",
        mess="dirt",
        reveal="the rock was ordinary-looking at first",
        tags={"rock", "norm", "slice"},
    ),
    "wash": Activity(
        id="wash",
        verb="wash the rock",
        gerund="rinsing rocks",
        rush="bring it to the bowl and splash water over it",
        mess="wet",
        reveal="the water made the stone shine",
        tags={"rock", "twist", "slice"},
    ),
    "display": Activity(
        id="display",
        verb="put the rock on the shelf",
        gerund="arranging little treasures",
        rush="carry it to the shelf by the window",
        mess="clean",
        reveal="the shelf was bright enough to show its stripe",
        tags={"rock", "home", "slice"},
    ),
}

PRIZES = {
    "pebble": Prize(
        id="pebble",
        label="pebble",
        phrase="a smooth gray pebble",
        reveal_kind="stripe",
        location="palm",
        needs_wash=True,
        tags={"rock"},
    ),
    "riverstone": Prize(
        id="riverstone",
        label="river stone",
        phrase="a round river stone with a flat side",
        reveal_kind="stripe",
        location="pocket",
        needs_wash=True,
        tags={"rock"},
    ),
    "keeper": Prize(
        id="keeper",
        label="keepsake rock",
        phrase="a little rock to keep on the shelf",
        reveal_kind="shine",
        location="shelf",
        needs_wash=True,
        tags={"rock", "home"},
    ),
}

GEAR = [
    Gear(
        id="bowl",
        label="the blue washing bowl",
        prep="set the rock in the blue bowl",
        tail="rinsed it in the blue bowl",
        helps={"wet", "dirt"},
    ),
    Gear(
        id="towel",
        label="a soft towel",
        prep="lay out a soft towel first",
        tail="dried the rock on the soft towel",
        helps={"wet"},
    ),
    Gear(
        id="shelf",
        label="the window shelf",
        prep="make space on the window shelf",
        tail="placed the rock on the window shelf",
        helps={"display"},
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Ada", "Iris", "Nora", "Ruby"]
BOY_NAMES = ["Eli", "Theo", "Milo", "Finn", "Owen", "Ben"]
PARENT_NAMES = ["Mom", "Dad", "Grandma", "Grandpa"]
TRAITS = ["careful", "curious", "gentle", "patient", "quiet"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld about a rock, a norm, and a gentle twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["Mom", "Dad", "Grandma", "Grandpa"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def select_gear(activity: Activity) -> Optional[Gear]:
    for g in GEAR:
        if activity.id == "wash" and "wet" in g.helps:
            return g
        if activity.id == "display" and "display" in g.helps:
            return g
        if activity.id == "find" and "dirt" in g.helps:
            return g
    return None


def tell(setting: Setting, activity: Activity, prize: Prize, name: str, gender: str, parent_name: str, trait: str) -> World:
    w = World(setting)
    child = w.add(Entity(id=name, kind="character", type=gender, label=name))
    parent = w.add(Entity(id=parent_name, kind="character", type="parent", label=parent_name))
    rock = w.add(Entity(id="rock", kind="thing", type="rock", label=prize.label, phrase=prize.phrase))
    gear = select_gear(activity)
    w.facts.update(child=child, parent=parent, rock=rock, gear=gear, activity=activity, prize=prize, setting=setting, trait=trait)
    child.memes["curiosity"] += 1.0
    rock.meters["weight"] = 1.0
    w.say(f"{child.id} was a {trait} little {gender} who liked quiet things they could hold in one hand.")
    w.say(f"On an ordinary day, {child.id} found {prize.phrase} near {setting.place}.")
    w.say(f"{child.id} wanted to {activity.verb}, because small rocks felt special when they fit in the palm just right.")
    w.para()
    w.say(f"{parent.id} looked over and reminded {child.id} of the home norm: {setting.norms[0]}.")
    w.say(f"That meant the rock had to wait before it could come inside.")
    child.memes["disappointment"] += 1.0
    w.para()
    if gear is not None:
        w.say(f"{child.id} frowned for a moment, then {parent.id} found a simple way to help: {gear.prep}.")
        w.say(f"Together they {gear.tail}.")
        child.memes["calm"] += 1.0
    if activity.id == "find":
        rock.meters["dirt"] += 1.0
    elif activity.id == "wash":
        rock.meters["dirt"] += 1.0
        rock.meters["wet"] += 1.0
    elif activity.id == "display":
        rock.meters["polish"] += 1.0
    propagate(w, narrate=True)
    if activity.id == "find":
        w.para()
        w.say(f"After the rinse, {child.id} carried the rock to the kitchen light and noticed it had a tiny bright stripe.")
        w.say(f"The boring-looking stone had been a little treasure all along.")
        rock.meters["polish"] += 1.0
        propagate(w, narrate=True)
    elif activity.id == "wash":
        w.para()
        w.say(f"When the rock dried, its face caught the light and showed a neat little stripe that nobody had seen before.")
    else:
        w.para()
        w.say(f"Once it sat on the shelf, the rock glowed softly by the window, and the stripe made it look proud.")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, p, a, r = f["child"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short slice-of-life story for a young child using the word "norm" and the phrase "{r.phrase}".',
        f"Tell a gentle story where {c.id} wants to {a.verb}, but {p.id} reminds them of a home norm.",
        f'Write a small everyday story with a twist about a rock, a rule, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, p, a, r = f["child"], f["parent"], f["activity"], f["prize"]
    return [
        QAItem(
            question=f"Why did {p.id} stop {c.id} from keeping the rock right away?",
            answer=f"{p.id} was following the home norm that dirty things stayed outside until they were cleaned.",
        ),
        QAItem(
            question=f"What did {c.id} want to do with the rock at first?",
            answer=f"{c.id} wanted to {a.verb} and keep the little stone close.",
        ),
        QAItem(
            question=f"What changed after the rock was washed?",
            answer=f"After it was washed, the rock looked smoother and brighter, and a small hidden stripe showed up in the light.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a norm?",
            answer="A norm is a usual rule or habit that people follow because it helps life go smoothly.",
        ),
        QAItem(
            question="What is a rock?",
            answer="A rock is a hard piece of natural stone. Rocks can be rough, smooth, small, or big.",
        ),
        QAItem(
            question="Why do people wash dirty things?",
            answer="People wash dirty things so the dirt comes off and the thing can be used, carried, or displayed more neatly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: round(v, 2) for k, v in e.meters.items() if v}
        s = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={m} memes={s}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(P) :- setting(P).
valid_act(A) :- activity(A).
valid_prize(R) :- prize(R).
valid_story(P,A,R) :- valid_place(P), affords(P,A), valid_prize(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for n in s.norms:
            lines.append(asp.fact("norm", pid, n))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess", aid, a.mess))
    for rid, r in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("reveals", rid, r.reveal_kind))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", g.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH:")
    print("only in asp:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible combos:")
        for v in vals:
            print(" ", v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, act, prize in valid_combos():
            params = StoryParams(place=place, activity=act, prize=prize, name="Mina", gender="girl", parent="Mom", trait="curious")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
