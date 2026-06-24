#!/usr/bin/env python3
"""
storyworlds/worlds/reckless_cautionary_curiosity_flashback_slice_of_life.py
===========================================================================

A small slice-of-life storyworld about a curious child, a cautionary warning,
and a safer choice after a flashback to a reckless mistake.

Premise:
- A child notices something interesting up high or behind a closed lid.
- Curiosity grows into reckless behavior unless a caregiver reminds them of a
  past slip or scare.
- The ending turns on a practical, safe compromise that satisfies curiosity
  without repeating the mistake.

The world model tracks:
- physical meters: reach, wobble, scrape, spill, dust
- emotional memes: curiosity, caution, reckless, worry, pride, relief

The story is generated from state changes, not from a frozen template.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    afford: set[str] = field(default_factory=set)


@dataclass
class Interest:
    id: str
    label: str
    verb: str
    gerund: str
    lure: str
    risk: str
    flashback: str
    zone: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    gives: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.flashback_used = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.is_character()]

    def copy(self) -> "World":
        other = World(self.setting)
        other.entities = {k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label,
            "phrase": e.phrase, "plural": e.plural, "owner": e.owner,
            "caretaker": e.caretaker, "worn_by": e.worn_by,
            "meters": dict(e.meters), "memes": dict(e.memes),
        }) for k, e in self.entities.items()}
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        other.flashback_used = self.flashback_used
        return other


def mget(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def activity_at_risk(interest: Interest, prize: Prize) -> bool:
    return prize.region == interest.zone


def compatible_helper(interest: Interest, prize: Prize) -> Optional[Helper]:
    for helper in HELPERS:
        if helper.gives == interest.mess and prize.region in helper_regions[helper.id]:
            return helper
    return None


def predict_mess(world: World, child: Entity, interest: Interest, prize: Prize) -> bool:
    sim = world.copy()
    do_peek(sim, sim.get(child.id), interest, narrate=False)
    item = sim.get(prize.id)
    return mget(item, "messy") >= THRESHOLD or mget(item, "dusty") >= THRESHOLD or mget(item, "spilled") >= THRESHOLD


def do_peek(world: World, child: Entity, interest: Interest, narrate: bool = True) -> None:
    add_meter(child, interest.mess, 1.0)
    add_meme(child, "curiosity", 1.0)
    add_meme(child, "reckless", 1.0)
    if narrate:
        world.say(f"{child.id} leaned toward {interest.lure}, even though {child.pronoun('possessive')} feet were already near the edge.")
    if interest.mess == "wobble":
        add_meter(child, "wobble", 1.0)
    if interest.mess == "dust":
        add_meter(child, "dust", 1.0)
    if interest.mess == "spill":
        add_meter(child, "spill", 1.0)


def apply_flashback(world: World, child: Entity, interest: Interest) -> None:
    if world.flashback_used:
        return
    world.flashback_used = True
    add_meme(child, "caution", 1.0)
    add_meme(child, "worry", 1.0)
    world.say(
        f"That tug of curiosity brought back a flashback: once, {child.id} had been reckless and knocked {interest.flashback} over."
    )
    world.say(
        f"{child.pronoun().capitalize()} remembered the small mess and the startled feeling that came with it."
    )


def warn(world: World, parent: Entity, child: Entity, prize: Prize, interest: Interest) -> bool:
    if not predict_mess(world, child, interest, prize):
        return False
    add_meme(parent, "caution", 1.0)
    add_meme(parent, "worry", 1.0)
    world.facts["at_risk"] = True
    world.say(
        f'"Careful," {parent.id} said. "If you pull on {interest.label}, you could bump {child.pronoun("possessive")} {prize.label}."'
    )
    return True


def offer_helper(world: World, parent: Entity, child: Entity, interest: Interest, prize: Prize) -> Optional[Helper]:
    helper = compatible_helper(interest, prize)
    if helper is None:
        return None
    add_meme(parent, "pride", 1.0)
    world.say(
        f'{parent.pronoun("possessive").capitalize()} smile softened. "How about we use {helper.label} first?"'
    )
    return helper


def accept_helper(world: World, child: Entity, helper: Helper, interest: Interest, prize: Prize) -> None:
    add_meme(child, "relief", 1.0)
    add_meme(child, "pride", 1.0)
    child.memes["reckless"] = max(0.0, child.memes.get("reckless", 0.0) - 1.0)
    world.say(
        f"{child.id}'s shoulders dropped. {child.pronoun().capitalize()} nodded and chose the safer way."
    )
    world.say(
        f"They {helper.tail}, and then {child.id} could look closely without troubling {child.pronoun('possessive')} {prize.label}."
    )


def risky_turn(world: World, child: Entity, interest: Interest) -> None:
    add_meme(child, "reckless", 1.0)
    world.say(
        f"{child.id} almost reached faster than {child.pronoun('possessive')} balance could keep up."
    )


def finish_scene(world: World, child: Entity, prize: Prize, helper: Helper) -> None:
    add_meme(child, "relief", 1.0)
    add_meme(child, "curiosity", 1.0)
    world.say(
        f"In the end, {child.id} was still curious, but {child.pronoun()} could keep both {child.pronoun('possessive')} hands safe."
    )
    world.say(
        f"{child.id} stood beside {child.pronoun('possessive')} {prize.label}, looking happy and calm while {helper.label} sat nearby."
    )


def tell(setting: Setting, interest: Interest, prize: Prize, helper: Helper,
         child_name: str = "Mina", child_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    item = world.add(Entity(
        id="Prize", kind="thing", type=prize.id, label=prize.label, phrase=prize.phrase,
        owner=child.id, region=prize.region, plural=prize.plural
    ))

    world.say(f"{child.id} was a small {child_type} who liked quiet afternoons and new little discoveries.")
    world.say(f"{child.pronoun().capitalize()} loved {interest.gerund} because {interest.lure} felt full of stories.")
    world.say(f"On the table was {item.phrase}, and {child.id} had been proud to wear it.")
    world.say(f"One ordinary day at {setting.place}, {child.id} noticed {interest.label} and paused to look.")

    world.say(" ")
    add_meme(child, "curiosity", 1.0)
    do_peek(world, child, interest)
    apply_flashback(world, child, interest)
    warn(world, parent, child, prize, interest)
    risky_turn(world, child, interest)

    world.say(" ")
    helper_obj = offer_helper(world, parent, child, interest, prize)
    if helper_obj is not None:
        accept_helper(world, child, helper_obj, interest, prize)
        world.facts["resolved"] = True
        world.facts["helper"] = helper_obj
    else:
        world.say(
            f"So {child.id} backed away on {child.pronoun('possessive')} own, deciding not to be reckless."
        )
        world.facts["resolved"] = False
        world.facts["helper"] = None

    finish_scene(world, child, prize, helper)
    world.facts.update(
        child=child,
        parent=parent,
        prize=item,
        setting=setting,
        interest=interest,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, afford={"peek", "reach"}),
    "laundry_room": Setting(place="the laundry room", indoor=True, afford={"peek", "reach"}),
    "hallway": Setting(place="the hallway", indoor=True, afford={"peek"}),
    "sunroom": Setting(place="the sunroom", indoor=True, afford={"peek", "reach"}),
}

INTERESTS = {
    "jar": Interest(
        id="jar",
        label="a glass jar on the shelf",
        verb="peek at the jar",
        gerund="peeking at jars",
        lure="the shining lid",
        risk="the jar might wobble",
        flashback="a cup of berries",
        zone="reach",
        mess="wobble",
        flashback="a cup of berries",
        tags={"glass", "shelf", "careful"},
    ),
    "drawer": Interest(
        id="drawer",
        label="the top drawer",
        verb="pull the drawer open",
        gerund="sliding drawers open",
        lure="the neat little label",
        risk="the drawer might jam",
        flashback="a pencil box",
        zone="reach",
        mess="spill",
        flashback="a pencil box",
        tags={"drawer", "careful"},
    ),
    "curtain": Interest(
        id="curtain",
        label="the dusty curtain cord",
        verb="tug the curtain cord",
        gerund="touching curtain cords",
        lure="the cord that swung like a ribbon",
        risk="the curtain might drop dust",
        flashback="a flower pot",
        zone="reach",
        mess="dust",
        flashback="a flower pot",
        tags={"dust", "curtain"},
    ),
}

PRIZES = {
    "scarf": Prize(id="scarf", label="scarf", phrase="a bright scarf", region="neck"),
    "cup": Prize(id="cup", label="cup", phrase="a little striped cup", region="hand"),
    "book": Prize(id="book", label="book", phrase="a picture book with a shiny cover", region="lap"),
}

HELPERS = [
    Helper(id="stepstool", label="the step stool", prep="slide the step stool over", tail="slid the step stool over", gives="wobble"),
    Helper(id="tray", label="a tray and a cloth", prep="use a tray and a cloth", tail="brought over a tray and a cloth", gives="dust"),
    Helper(id="mitts", label="oven mitts", prep="put on oven mitts", tail="found the oven mitts", gives="spill"),
]

helper_regions = {
    "stepstool": {"reach"},
    "tray": {"reach"},
    "mitts": {"reach"},
}

GIRL_NAMES = ["Mina", "Lena", "Tia", "Ruby", "Nina", "Sora"]
BOY_NAMES = ["Owen", "Eli", "Theo", "Finn", "Milo", "Jasper"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in INTERESTS:
            for p in PRIZES:
                if activity_at_risk(INTERESTS[i], PRIZES[p]) and compatible_helper(INTERESTS[i], PRIZES[p]):
                    combos.append((s, i, p))
    return combos


@dataclass
class StoryParams:
    place: str
    interest: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "wobble": [("What does wobble mean?", "Wobble means to move unsteadily, like something that may tip if you touch it the wrong way.")],
    "spill": [("What is a spill?", "A spill is when liquid or small things fall out of a container and make a mess.")],
    "dust": [("What is dust?", "Dust is made of tiny bits that gather on surfaces and can make things look gray or dirty.")],
    "stepstool": [("What is a step stool for?", "A step stool is a small stool that helps a person reach something a little higher up safely.")],
    "careful": [("Why should you be careful with glass?", "Glass can break if it is bumped or dropped, so careful hands help keep it safe.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    interest = f["interest"]
    prize = f["prize"]
    return [
        f'Write a short slice-of-life story for a young child about being curious about {interest.label} without being reckless.',
        f'Tell a gentle cautionary story where {child.id} wants to {interest.verb} but must keep {prize.phrase} safe.',
        f'Write a story with a flashback that helps a child make a safer choice around {interest.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    prize = f["prize"]
    interest = f["interest"]
    helper = f["helper"]
    qa = [
        QAItem(
            question=f"What made {child.id} curious at {world.setting.place}?",
            answer=f"{child.id} was curious about {interest.label} because it looked interesting and a little mysterious.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {child.id} about being reckless?",
            answer=f"{parent.label} warned {child.id} because {interest.risk}, and that could trouble {child.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"What did {child.id} remember in the flashback?",
            answer=f"{child.id} remembered the time {interest.flashback} was bumped over when {child.id} had been reckless before.",
        ),
    ]
    if f.get("helper"):
        qa.append(
            QAItem(
                question=f"How did {helper.label} help {child.id} stay safe?",
                answer=f"{helper.label} gave {child.id} a safer way to look closely, so {child.id} could be curious without risking {child.pronoun('possessive')} {prize.label}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["interest"].tags)
    if world.facts.get("helper"):
        tags.add(world.facts["helper"].id)
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(I, P) :- interest(I), prize(P), zone(I, Z), region(P, Z).
helper_ok(H, I, P) :- helper(H), at_risk(I, P), gives(H, M), mess(I, M), covers(H, Z), zone(I, Z), region(P, Z).
valid_story(S, I, P) :- setting(S), interest(I), prize(P), at_risk(I, P), helper_ok(_, I, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, i in INTERESTS.items():
        lines.append(asp.fact("interest", iid))
        lines.append(asp.fact("zone", iid, i.zone))
        lines.append(asp.fact("mess", iid, i.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        lines.append(asp.fact("gives", h.id, h.gives))
        for z in helper_regions[h.id]:
            lines.append(asp.fact("covers", h.id, z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life cautionary storyworld about curiosity and safer choices.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--interest", choices=INTERESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.interest is None or c[1] == args.interest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, interest, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, interest=interest, prize=prize, name=name, gender=gender, parent=parent)


CURATED = [
    StoryParams(place="kitchen", interest="jar", prize="cup", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="sunroom", interest="drawer", prize="book", name="Owen", gender="boy", parent="father"),
    StoryParams(place="laundry_room", interest="curtain", prize="scarf", name="Lena", gender="girl", parent="mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], INTERESTS[params.interest], PRIZES[params.prize], HELPERS[0 if params.interest == "jar" else (1 if params.interest == "curtain" else 2)], params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.interest} at {p.place} (prize: {p.prize})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
