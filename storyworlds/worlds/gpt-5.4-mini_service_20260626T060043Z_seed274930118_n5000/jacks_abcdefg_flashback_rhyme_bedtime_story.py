#!/usr/bin/env python3
"""
A tiny bedtime-story world about a child, a jumble of jacks, and a rhyming
flashback that helps solve a sleepy problem.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    messy: str
    zone: str
    rhyme_word: str
    flashback_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    calms: set[str]
    fits_zone: str
    prep: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


def noun_phrase(name: str, article: str = "a") -> str:
    return f"{article} {name}" if article else name


@dataclass
class StoryParams:
    place: str
    toy: str
    comfort: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


PLACES = {
    "bedroom": Place(id="bedroom", label="the bedroom", indoor=True, affords={"jacks"}),
    "nursery": Place(id="nursery", label="the nursery", indoor=True, affords={"jacks"}),
    "playroom": Place(id="playroom", label="the playroom", indoor=True, affords={"jacks"}),
}

TOYS = {
    "jacks": Toy(
        id="jacks",
        label="jacks",
        phrase="a little tin set of jacks",
        messy="tippy",
        zone="floor",
        rhyme_word="jacks",
        flashback_word="back",
        tags={"jacks", "rhythm", "toy"},
    ),
    "abcdefg": Toy(
        id="abcdefg",
        label="abcdefg cards",
        phrase="a bright card set that said abcdefg",
        messy="scattered",
        zone="bed",
        rhyme_word="abcdefg",
        flashback_word="dream",
        tags={"abc", "letters", "rhyme"},
    ),
}

COMFORTS = [
    Comfort(
        id="basket",
        label="a small basket",
        phrase="a small basket for the pieces",
        calms={"scattered", "tippy"},
        fits_zone="floor",
        prep="put the pieces in a basket",
        tail="tidied the little pieces into the basket",
    ),
    Comfort(
        id="blanket",
        label="a soft blanket",
        phrase="a soft blanket for the bed",
        calms={"scattered"},
        fits_zone="bed",
        prep="spread a soft blanket under the cards",
        tail="spread the blanket and gathered the cards onto it",
    ),
]

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ava", "Zoe", "Lily"]
BOY_NAMES = ["Theo", "Noah", "Eli", "Finn", "Leo", "Max"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_mess(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.kind != "toy":
            continue
        if ent.meters.get("played", 0.0) < THRESHOLD:
            continue
        sig = ("mess", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters[ent.messty] = ent.meters.get(ent.messty, 0.0) + 1
        out.append(f"The {ent.label} got a little messy.")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero"].id)
    toy = world.get(world.facts["toy"].id)
    if toy.meters.get("scattered", 0.0) >= THRESHOLD and hero.memes.get("worry", 0.0) < THRESHOLD:
        hero.memes["worry"] = 1.0
        out.append("That made the grown-up worry about bedtime.")
    return out


CAUSAL_RULES = [
    Rule("mess", _r_mess),
    Rule("worry", _r_worry),
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


def build_story_line(name: str, toy: Toy) -> str:
    return f"{name} loved the {toy.label}, and the room felt cozy and small."


def flashback_line(name: str, toy: Toy) -> str:
    return (
        f"Long ago, {name} had learned a gentle rhyme: "
        f"“{toy.rhyme_word}, {toy.rhyme_word}, keep the pieces near; "
        f"remember the {toy.flashback_word} from the sleepy year.”"
    )


def rhyme_line(toy: Toy) -> str:
    return f"“{toy.rhyme_word}, {toy.rhyme_word}, tidy and bright; let the room rest soft tonight.”"


def tell(place: Place, toy_cfg: Toy, comfort_cfg: Comfort, name: str, gender: str, parent: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    grownup = world.add(Entity(id="grownup", kind="character", type=parent, label="the grown-up"))
    toy = world.add(Entity(
        id=toy_cfg.id,
        kind="toy",
        type=toy_cfg.id,
        label=toy_cfg.label,
        phrase=toy_cfg.phrase,
        owner=hero.id,
    ))
    toy.messty = toy_cfg.messy

    world.facts = {"hero": hero, "grownup": grownup, "toy": toy, "comfort": comfort_cfg, "place": place, "toy_cfg": toy_cfg}

    world.say(f"{name} was sleepy and sat in {place.label}.")
    world.say(build_story_line(name, toy_cfg))
    world.say(f"{hero.pronoun().capitalize()} played with {toy_cfg.phrase} until the little pieces went every which way.")

    world.para()
    world.say(f"Then the grown-up peeked in and remembered a flashback from before bedtime.")
    world.say(flashback_line(name, toy_cfg))
    toy.meters["played"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"{name} wanted to keep playing, but the room needed to be calm again.")
    if toy_cfg.id == "jacks":
        world.say(f"The tiny jacks were all over the floor.")
    else:
        world.say(f"The letter cards had slid across the bed like drifting clouds.")
    grownup.memes["worry"] = 1.0
    world.say(f'"Let us make this neat," {parent} said softly, "and then we can rest."')

    world.para()
    comfort = world.add(Entity(
        id=comfort_cfg.id,
        kind="thing",
        type="comfort",
        label=comfort_cfg.label,
        phrase=comfort_cfg.phrase,
        owner=hero.id,
    ))
    comfort.worn_by = hero.id
    world.say(f"They used {comfort_cfg.phrase} because it fit the problem exactly.")
    world.say(f"Their plan was simple: {comfort_cfg.prep}.")
    toy.meters[toy_cfg.messy] = 0.0
    world.say(f"{name} helped with a small rhyme and then {comfort_cfg.tail}.")
    world.say(rhyme_line(toy_cfg))
    world.say(f"At last, {name} was tucked in, and the room looked quiet enough for dreams.")

    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for toy_id in place.affords:
            toy = TOYS[toy_id]
            for comfort in COMFORTS:
                if comfort.fits_zone == toy.zone and toy.messy in comfort.calms:
                    combos.append((place_id, toy_id, comfort.id))
    return combos


def explain_rejection(place_id: str, toy_id: str, comfort_id: str) -> str:
    place = PLACES[place_id]
    toy = TOYS[toy_id]
    comfort = next(c for c in COMFORTS if c.id == comfort_id)
    return (
        f"(No story: {comfort.label} does not fit the way {toy.label} gets messy "
        f"in {place.label}. The fix must match the toy's problem.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    toy = f["toy_cfg"]
    return [
        f'Write a bedtime story for a small child that includes "{toy.rhyme_word}".',
        f"Tell a gentle story about {f['hero'].id} and {toy.phrase}, with a flashback and a rhyme.",
        f"Write a cozy bedtime story where a grown-up helps make {toy.label} neat again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    toy = f["toy_cfg"]
    comfort = f["comfort"]
    place = f["place"].label
    parent = f["grownup"].label
    return [
        QAItem(
            question=f"Who wanted to keep playing with the {toy.label} in {place}?",
            answer=f"{hero.id} wanted to keep playing, but the {toy.label} needed tidying before sleep.",
        ),
        QAItem(
            question=f"What did the grown-up remember from the flashback?",
            answer=f"The grown-up remembered a gentle rhyme about keeping {toy.label} pieces near and calm.",
        ),
        QAItem(
            question=f"How did they fix the room before bedtime?",
            answer=f"They used {comfort.phrase} and helped the {toy.label} become neat again.",
        ),
        QAItem(
            question=f"Who spoke softly to help {hero.id} settle down?",
            answer=f"{parent} spoke softly and helped {hero.id} choose the calm bedtime way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    toy = f["toy_cfg"]
    if toy.id == "jacks":
        return [
            QAItem(
                question="What are jacks?",
                answer="Jacks are a small game piece toy, often tossed and scooped up in a quick game.",
            ),
            QAItem(
                question="Why do small pieces need to be picked up before bed?",
                answer="Small pieces need to be picked up so nobody steps on them and the room can stay safe and tidy.",
            ),
        ]
    return [
        QAItem(
            question="What are alphabet cards used for?",
            answer="Alphabet cards can help children look at letters, read, and play simple learning games.",
        ),
        QAItem(
            question="Why can cards spread out on a bed be messy?",
            answer="Cards spread out on a bed can get lost or bent, so it helps to gather them neatly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
toy_combo(P,T,C) :- place(P), toy(T), comfort(C), affords(P,T), fits(C,Z), toy_zone(T,Z), toy_mess(T,M), calms(C,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(p.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TOYS.items():
        lines.append(asp.fact("toy", tid))
        lines.append(asp.fact("toy_zone", tid, t.zone))
        lines.append(asp.fact("toy_mess", tid, t.messy))
    for c in COMFORTS:
        lines.append(asp.fact("comfort", c.id))
        lines.append(asp.fact("fits", c.id, c.fits_zone))
        for m in sorted(c.calms):
            lines.append(asp.fact("calms", c.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show toy_combo/3."))
    return sorted(set(asp.atoms(model, "toy_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with jacks, abcdefg, flashback, and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--comfort", choices=[c.id for c in COMFORTS])
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
    combos = valid_combos()
    if args.place or args.toy or args.comfort:
        filtered = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.toy is None or c[1] == args.toy)
            and (args.comfort is None or c[2] == args.comfort)
        ]
    else:
        filtered = combos
    if not filtered:
        raise StoryError("(No valid bedtime-story combination matches the given options.)")
    place, toy, comfort = rng.choice(sorted(filtered))
    if args.toy and args.comfort:
        toy_cfg = TOYS[toy]
        comfort_cfg = next(c for c in COMFORTS if c.id == comfort)
        if comfort_cfg.fits_zone != toy_cfg.zone or toy_cfg.messy not in comfort_cfg.calms:
            raise StoryError(explain_rejection(place, toy, comfort))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, toy=toy, comfort=comfort, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TOYS[params.toy], next(c for c in COMFORTS if c.id == params.comfort), params.name, params.gender, params.parent)
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
    StoryParams(place="bedroom", toy="jacks", comfort="basket", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="nursery", toy="abcdefg", comfort="blanket", name="Theo", gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show toy_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
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
            params = resolve_params(args, random.Random(seed))
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
