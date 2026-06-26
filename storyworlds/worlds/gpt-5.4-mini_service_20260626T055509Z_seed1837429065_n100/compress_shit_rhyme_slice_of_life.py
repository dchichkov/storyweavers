#!/usr/bin/env python3
"""
storyworlds/worlds/compress_shit_rhyme_slice_of_life.py
=======================================================

A small slice-of-life story world about an ordinary afternoon, a little
embarrassing mess, a warm compress, and a rhyme that helps everyone settle
down again.

The seed tale behind this world is simple:
- a child feels unwell after a long day,
- a tiny accident makes the room tense,
- a parent brings a warm compress and a gentle rhyme,
- the child calms down, gets cleaned up, and the day ends softly.

The world is built as a compact simulation:
- entities have physical meters and emotional memes,
- the story is driven by state changes rather than a frozen paragraph,
- the compromise is only offered when it actually solves the problem.

The story text stays child-facing and concrete. The word "shit" is treated as
a seed-word and appears in world metadata, prompts, and ASP facts, while the
narrated story uses gentler slice-of-life wording.
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
REGIONS = {"head", "torso", "hands", "legs", "feet"}


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

    def __post_init__(self) -> None:
        for k in ["mess", "wet", "dirty", "warmth", "tidy", "comfort"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "embarrassment", "care", "calm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mess:
    id: str
    noun: str
    verb: str
    mess_kind: str
    soil: str
    zone: set[str]
    rhyme_word: str
    keyword: str = "rhyme"


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    covers: set[str]
    fixes: set[str]
    protective: bool = True
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"snack", "rest", "rhyme"}),
    "living_room": Setting(place="the living room", affords={"rest", "rhyme"}),
    "bedroom": Setting(place="the bedroom", affords={"rest", "rhyme"}),
    "porch": Setting(place="the porch", affords={"air", "rhyme"}),
}

MESS_TYPES = {
    "spill": Mess(
        id="spill",
        noun="spill",
        verb="spill",
        mess_kind="wet",
        soil="damp and sticky",
        zone={"hands", "torso"},
        rhyme_word="drip",
        keyword="rhyme",
    ),
    "crumbs": Mess(
        id="crumbs",
        noun="crumbs",
        verb="drop crumbs from a snack",
        mess_kind="crumbly",
        soil="full of crumbs",
        zone={"hands", "legs"},
        rhyme_word="munch",
        keyword="rhyme",
    ),
    "bathroom": Mess(
        id="bathroom",
        noun="an urgent bathroom need",
        verb="have a bathroom accident",
        mess_kind="dirty",
        soil="all messy",
        zone={"legs"},
        rhyme_word="whoosh",
        keyword="rhyme",
    ),
}

AIDS = [
    Aid(
        id="warm_compress",
        label="warm compress",
        phrase="a warm compress in a soft towel",
        prep="bring the warm compress",
        tail="held the warm compress there until the worry melted away",
        covers={"torso"},
        fixes={"dirty", "wet"},
    ),
    Aid(
        id="clean_clothes",
        label="clean clothes",
        phrase="clean clothes from the laundry basket",
        prep="find clean clothes",
        tail="helped the child change into clean clothes",
        covers={"torso", "legs"},
        fixes={"dirty", "wet"},
        plural=True,
    ),
    Aid(
        id="towel",
        label="big towel",
        phrase="a big towel",
        prep="hand over a big towel",
        tail="wrapped the child in the towel",
        covers={"torso", "legs"},
        fixes={"wet"},
    ),
]

NAMES = ["Mina", "Noah", "Ivy", "Sam", "Lena", "Owen", "Zoe", "Leo"]
GROWNUPS = ["mother", "father"]
TRAITS = ["quiet", "sleepy", "small", "tender", "shy", "bright"]


@dataclass
class StoryParams:
    place: str
    mess: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def mess_risks_clothes(mess: Mess) -> bool:
    return True


def select_aid(mess: Mess) -> Optional[Aid]:
    for aid in AIDS:
        if mess.mess_kind in aid.fixes:
            return aid
    return None


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mid) for place, s in SETTINGS.items() for mid in s.affords if mid in {"rhyme", "rest", "snack", "air"}]


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mess = MESS_TYPES[params.mess]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Ivy", "Lena", "Zoe"} else "boy"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    item = world.add(Entity(
        id="outfit",
        type="clothes",
        label="outfit",
        phrase="a favorite outfit",
        owner=child.id,
        caretaker=parent.id,
        worn_by=child.id,
        region="torso",
    ))
    world.facts.update(child=child, parent=parent, item=item, mess=mess, place=setting)
    return world


def narrate_setup(world: World, params: StoryParams) -> None:
    c: Entity = world.facts["child"]
    p: Entity = world.facts["parent"]
    mess: Mess = world.facts["mess"]
    world.say(f"{c.id} was a {params.trait} little child who liked quiet afternoons in {world.setting.place}.")
    world.say(f"{c.pronoun().capitalize()} loved little rhymes, especially ones that bounced like {mess.rhyme_word} and giggled like {mess.keyword}.")
    world.say(f"That day, {c.id} wore {c.pronoun('possessive')} favorite outfit, and {p.label} was nearby with a calm smile.")


def trigger_mess(world: World) -> None:
    c: Entity = world.facts["child"]
    mess: Mess = world.facts["mess"]
    c.meters["mess"] += 1
    c.memes["worry"] += 1
    c.memes["embarrassment"] += 1
    world.zone = set(mess.zone)
    world.say(f"At {world.setting.place}, {c.id} tried to move too fast and made a small {mess.noun}.")
    if mess.id == "bathroom":
        world.say(f"It was the kind of accident that made the room feel very quiet all at once.")
    elif mess.id == "spill":
        world.say(f"The splash landed on {c.pronoun('possessive')} outfit and left a damp patch.")
    else:
        world.say(f"Crumbs skittered everywhere and clung to the front of {c.pronoun('possessive')} clothes.")


def parent_notices(world: World) -> None:
    c: Entity = world.facts["child"]
    p: Entity = world.facts["parent"]
    mess: Mess = world.facts["mess"]
    p.memes["care"] += 1
    p.memes["worry"] += 1 if mess.id == "bathroom" else 0.5
    world.say(f"{p.label.capitalize()} noticed right away and knelt beside {c.id}.")
    world.say(f'"It is okay," {p.label} said. "We can clean this up gently."')


def offer_compress(world: World) -> Optional[Aid]:
    c: Entity = world.facts["child"]
    p: Entity = world.facts["parent"]
    mess: Mess = world.facts["mess"]
    aid = select_aid(mess)
    if aid is None:
        raise StoryError("No reasonable aid exists for this mess.")
    tool = world.add(Entity(
        id=aid.id,
        type="aid",
        label=aid.label,
        phrase=aid.phrase,
        owner=c.id,
        caretaker=p.id,
        protective=aid.protective,
        covers=set(aid.covers),
        plural=aid.plural,
    ))
    tool.worn_by = c.id if aid.id != "clean_clothes" else None
    if aid.id == "warm_compress":
        c.memes["calm"] += 1
        c.meters["comfort"] += 1
    world.say(f"{p.label.capitalize()} brought {aid.phrase} and said it would help {c.id} settle.")
    return aid


def rhyme_and_settle(world: World, aid: Aid) -> None:
    c: Entity = world.facts["child"]
    p: Entity = world.facts["parent"]
    mess: Mess = world.facts["mess"]
    c.memes["joy"] += 1
    c.memes["worry"] = max(0.0, c.memes["worry"] - 1.0)
    c.memes["embarrassment"] = max(0.0, c.memes["embarrassment"] - 1.0)
    c.meters["mess"] = 0.0
    world.say(f"{p.label.capitalize()} hummed a tiny rhyme: '{mess.rhyme_word} and hush, {mess.rhyme_word} and hush.'")
    world.say(f"Then {p.label} {aid.tail}.")
    if aid.id == "warm_compress":
        world.say(f"After a little while, {c.id} felt warmer, calmer, and ready to breathe again.")
    elif aid.id == "clean_clothes":
        world.say(f"Soon {c.id} was back in clean clothes and looked like {c.pronoun('subject')} could start over.")
    else:
        world.say(f"At last, {c.id} stopped fidgeting and the room felt easy again.")


def tell(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world, params)
    world.para()
    trigger_mess(world)
    parent_notices(world)
    world.para()
    aid = offer_compress(world)
    rhyme_and_settle(world, aid)
    world.facts["aid"] = aid
    return world


def generation_prompts(world: World) -> list[str]:
    c: Entity = world.facts["child"]
    mess: Mess = world.facts["mess"]
    return [
        f"Write a short slice-of-life story about {c.id}, a small {mess.noun}, and a gentle rhyme.",
        f"Tell a child-friendly story where a parent uses a warm compress and a rhyme to help after a messy little accident.",
        f"Write an ordinary afternoon story that includes the words compress and shit as seed words, but keeps the tone soft and caring.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c: Entity = world.facts["child"]
    p: Entity = world.facts["parent"]
    mess: Mess = world.facts["mess"]
    aid: Aid = world.facts["aid"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {c.id}, a small child having an ordinary afternoon at {world.setting.place}, with {p.label} helping out.",
        ),
        QAItem(
            question=f"What small trouble happened to {c.id}?",
            answer=f"{c.id} made a small {mess.noun}, which left {c.pronoun('possessive')} clothes or the room needing a little clean-up.",
        ),
        QAItem(
            question=f"How did {p.label} help?",
            answer=f"{p.label.capitalize()} brought {aid.label} and used a gentle rhyme so {c.id} could settle down and feel better.",
        ),
        QAItem(
            question=f"How did the child feel at the end?",
            answer=f"{c.id} felt calmer and more comfortable after the cleanup and the rhyme.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a compress?",
            answer="A compress is a folded cloth or pad that can be warmed or cooled and placed on the body to help someone feel better.",
        ),
        QAItem(
            question="Why do people use a warm compress?",
            answer="People use a warm compress to make sore or tense places feel calmer and more comfortable.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little piece of language where sounds match at the end of words, which makes it pleasant and fun to say.",
        ),
        QAItem(
            question="What should you do after a mess happens at home?",
            answer="After a mess happens at home, people usually clean it up, change clothes if needed, and help everyone feel settled again.",
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
    lines.append("== World knowledge questions ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  zone={sorted(world.zone)}")
    return "\n".join(lines)


ASP_RULES = r"""
mess(m1). mess_kind(m1,wet). zone(m1,torso). zone(m1,hands).
mess(m2). mess_kind(m2,dirty). zone(m2,legs).

aid(a1). fixes(a1,wet). covers(a1,torso).
aid(a2). fixes(a2,wet). fixes(a2,dirty). covers(a2,torso). covers(a2,legs).

compatible(M,A) :- mess(M), aid(A), mess_kind(M,K), fixes(A,K), zone(M,R), covers(A,R).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, act))
    for mid, mess in MESS_TYPES.items():
        lines.append(asp.fact("mess", mid))
        lines.append(asp.fact("mess_kind", mid, mess.mess_kind))
        for r in sorted(mess.zone):
            lines.append(asp.fact("zone", mid, r))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for k in sorted(aid.fixes):
            lines.append(asp.fact("fixes", aid.id, k))
        for r in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/2."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = set()
    for mid, mess in MESS_TYPES.items():
        for aid in AIDS:
            if mess.mess_kind in aid.fixes and any(r in aid.covers for r in mess.zone):
                py_set.add((mid, aid.id))
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python gate ({len(asp_set)} pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in ASP:", sorted(asp_set - py_set))
    print(" only in Python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a small mess, a warm compress, and a rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mess", choices=MESS_TYPES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=GROWNUPS)
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
    place = args.place or rng.choice(list(SETTINGS))
    mess = args.mess or rng.choice(list(MESS_TYPES))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(GROWNUPS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mess=mess, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="kitchen", mess="spill", name="Mina", parent="mother", trait="small"),
    StoryParams(place="living_room", mess="crumbs", name="Owen", parent="father", trait="quiet"),
    StoryParams(place="bedroom", mess="bathroom", name="Ivy", parent="mother", trait="shy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible/2."))
        pairs = sorted(set(asp.atoms(model, "compatible")))
        for m, a in pairs:
            print(f"{m} {a}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
