#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/suffice_ultra_storage_closet_kindness_detective_story.py
================================================================================================

A small standalone storyworld for a child-friendly detective story set in a
storage closet. The seed words "suffice" and "ultra" are woven into the world
as a case object, a clue, and a closing turn. The core premise is a gentle
mystery: something important goes missing in the storage closet, the little
detective follows physical clues and social traces, and Kindness becomes the
key that solves the case.

World premise:
- A child detective searches a storage closet.
- A prized item vanishes from a neat shelf.
- Clues involve labels, dust, a step stool, and hidden compartments.
- The investigation can end in accusation or in a kinder reveal, but the
  generated story always resolves with the truth and a concrete change in the
  closet state.

The prose is driven by world state rather than a frozen template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    movable: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the storage closet"
    shelves: list[str] = field(default_factory=lambda: ["top shelf", "middle shelf", "bottom shelf"])


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    effect: str
    place: str
    reveals: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    hides: str
    truthful: bool = False


@dataclass
class CaseObject:
    id: str
    label: str
    phrase: str
    location: str
    value: str
    prize: bool = True


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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _inc(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _mood(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    suspect: str
    clue: str
    treasure: str
    seed: Optional[int] = None


NAMES_GIRL = ["Maya", "Lena", "Iris", "Nora", "Ruby", "Ada"]
NAMES_BOY = ["Noah", "Eli", "Owen", "Theo", "Finn", "Milo"]
HELPERS = ["cat", "dog", "little brother", "big sister"]
SUSPECTS = ["teddy bear", "laundry basket", "storage bin", "toy truck"]
TREASURES = [
    CaseObject(id="ultra_box", label="ultra box", phrase="an ultra little blue box", location="behind the mop", value="ultra"),
    CaseObject(id="suffice_note", label="suffice note", phrase="a note that said 'suffice'", location="on the middle shelf", value="suffice"),
    CaseObject(id="kindness_pin", label="Kindness pin", phrase="a shiny Kindness pin", location="inside a basket", value="Kindness"),
]
CLUES = [
    Clue(id="dust_line", label="dust line", kind="dust", effect="a clean line in the dust", place="the floor", reveals="someone slid the box recently"),
    Clue(id="tape_mark", label="tape mark", kind="tape", effect="a strip of tape curled at one corner", place="the shelf edge", reveals="a label had been peeled away"),
    Clue(id="footprint", label="small footprint", kind="print", effect="a tiny footprint beside the step stool", place="the mat", reveals="a helper climbed up to reach the top shelf"),
]
SETTING = Setting()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly detective story set in a storage closet.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=sorted(set(HELPERS)))
    ap.add_argument("--suspect", choices=sorted(set(SUSPECTS)))
    ap.add_argument("--clue", choices=[c.id for c in CLUES])
    ap.add_argument("--treasure", choices=[t.id for t in TREASURES])
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


def valid_combo(clue: Clue, treasure: CaseObject, suspect: str) -> bool:
    if clue.id == "dust_line" and treasure.location != "behind the mop":
        return False
    if clue.id == "tape_mark" and treasure.id != "ultra_box":
        return False
    if clue.id == "footprint" and suspect not in {"teddy bear", "toy truck"}:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for clue in CLUES:
        for treasure in TREASURES:
            for suspect in SUSPECTS:
                if valid_combo(clue, treasure, suspect):
                    out.append((clue.id, treasure.id, suspect))
    return out


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for c in CLUES:
        lines.append(asp.fact("clue", c.id))
        lines.append(asp.fact("reveals", c.id, c.reveals))
        lines.append(asp.fact("place", c.id, c.place))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t.id))
        lines.append(asp.fact("located", t.id, t.location))
        lines.append(asp.fact("value", t.id, t.value))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    return "\n".join(lines)


ASP_RULES = r"""
valid(C,T,S) :- clue(C), treasure(T), suspect(S), reveals(C,"someone slid the box recently"), located(T,"behind the mop").
valid(C,T,S) :- clue(C), treasure(T), suspect(S), reveals(C,"a label had been peeled away"), T = ultra_box.
valid(C,T,S) :- clue(C), treasure(T), suspect(S), reveals(C,"a helper climbed up to reach the top shelf"), S = teddy_bear; S = toy_truck.
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    clue = args.clue or rng.choice([c.id for c in CLUES])
    treasure = args.treasure or rng.choice([t.id for t in TREASURES])
    suspect = args.suspect or rng.choice(SUSPECTS)
    clue_obj = next(c for c in CLUES if c.id == clue)
    treasure_obj = next(t for t in TREASURES if t.id == treasure)
    if not valid_combo(clue_obj, treasure_obj, suspect):
        raise StoryError("That clue, treasure, and suspect do not make a fair detective case.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, gender=gender, helper=helper, suspect=suspect, clue=clue, treasure=treasure)


def generate_world(params: StoryParams) -> World:
    w = World(SETTING)
    hero = w.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", "curious", "brave"]))
    helper = w.add(Entity(id="helper", kind="character", type=params.helper, traits=["quiet", "loyal"]))
    suspect = w.add(Entity(id="suspect", kind="thing", type=params.suspect, label=params.suspect))
    clue = next(c for c in CLUES if c.id == params.clue)
    treasure = next(t for t in TREASURES if t.id == params.treasure)
    prize = w.add(Entity(id=treasure.id, kind="thing", type="treasure", label=treasure.label, phrase=treasure.phrase, owner=hero.id))
    clue_ent = w.add(Entity(id=clue.id, kind="thing", type=clue.kind, label=clue.label))
    witness = w.add(Entity(id="kindness", kind="thing", type="virtue", label="Kindness", phrase="Kindness itself"))
    w.facts.update(hero=hero, helper=helper, suspect=suspect, clue=clue, treasure=treasure, prize=prize, clue_ent=clue_ent, witness=witness)
    return w


def tell_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    clue: Clue = f["clue"]
    treasure: CaseObject = f["treasure"]
    prize: Entity = f["prize"]

    _mood(hero, "curiosity", 1)
    world.say(f"{hero.id} was a little detective who loved quiet clues and big questions.")
    world.say(f"One afternoon, {hero.id} searched {SETTING.place} after noticing that {treasure.phrase} was missing from its spot.")
    world.say(f"On the middle shelf, {hero.id} found {clue.effect}, and that felt like a clue that might suffice.")

    world.para()
    _inc(hero, "attention", 1)
    _mood(hero, "worry", 1)
    world.say(f"{hero.id} looked under a stack of boxes and saw {suspect.label}.")
    world.say(f"{hero.id} wondered if {suspect.label} had taken the {treasure.label}, but the clue did not fit just yet.")
    world.say(f"Then {helper.id} nudged a broom aside and pointed at the shelf edge, where an ultra-small mark showed someone had been careful, not cruel.")

    world.para()
    _mood(hero, "kindness", 1)
    world.say(f"{hero.id} took a slow breath and chose Kindness instead of a loud accusation.")
    world.say(f"{hero.id} asked gentle questions, and {helper.id} helped by moving a bin aside.")
    if clue.id == "footprint":
        world.say(f"Under the step stool, the tiny print showed that a helper had reached high, not a thief sneaking low.")
    elif clue.id == "tape_mark":
        world.say(f"The peeled label made the case clearer: the {treasure.label} had been tucked behind a moved sign, not stolen away.")
    else:
        world.say(f"The dust line led straight to the back wall, where something had slid behind the mop handle.")

    world.para()
    _inc(prize, "found", 1)
    _mood(hero, "relief", 1)
    world.say(f"At last, {hero.id} found the {treasure.label} in {treasure.location}.")
    world.say(f"It had not been lost forever at all; it had simply been put in a clever hiding place, and the clue had been enough to find it.")
    world.say(f"{hero.id} smiled, because Kindness had solved the case better than blame.")
    world.say(f"By the end, the storage closet was neat again, the {treasure.label} was back where it belonged, and the little detective knew that being gentle could be ultra-smart.")
    world.facts["resolved"] = True


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Clue = f["clue"]
    treasure: CaseObject = f["treasure"]
    suspect: Entity = f["suspect"]
    return [
        QAItem(
            question=f"What kind of story is this about {hero.id} in {SETTING.place}?",
            answer=f"It is a detective story about {hero.id}, who looks carefully for clues in the storage closet.",
        ),
        QAItem(
            question=f"What was missing from the storage closet at the start?",
            answer=f"The missing thing was {treasure.phrase}, which belonged to {hero.id}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} find while searching?",
            answer=f"{hero.id} found {clue.effect}, which helped point the detective toward the truth.",
        ),
        QAItem(
            question=f"Why did {hero.id} avoid blaming {suspect.label} right away?",
            answer=f"{hero.id} stayed kind and looked at the evidence first, because the clue did not prove that {suspect.label} had taken anything.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The {treasure.label} was found and put back, and the storage closet ended neat and calm again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is Kindness?",
            answer="Kindness means speaking gently, helping others, and choosing care instead of being mean.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues and uses careful thinking to solve a mystery.",
        ),
        QAItem(
            question="What is a storage closet?",
            answer="A storage closet is a small room or cupboard where people keep boxes, tools, and other things they want to store.",
        ),
        QAItem(
            question="Why can a clue be useful?",
            answer="A clue can be useful because it helps show what happened, so a person can find the truth.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Clue = f["clue"]
    treasure: CaseObject = f["treasure"]
    return [
        f'Write a short detective story for a child set in a storage closet that includes the words "suffice" and "ultra".',
        f"Tell a gentle mystery where {hero.id} uses Kindness to solve the missing {treasure.label} case after finding {clue.label}.",
        "Write a calm clue-based story where a child detective looks in the storage closet, follows evidence, and ends with the lost item found.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    tell_story(world)
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


CURATED = [
    StoryParams(name="Maya", gender="girl", helper="cat", suspect="laundry basket", clue="dust_line", treasure="suffice_note"),
    StoryParams(name="Noah", gender="boy", helper="dog", suspect="toy truck", clue="footprint", treasure="kindness_pin"),
    StoryParams(name="Iris", gender="girl", helper="big sister", suspect="storage bin", clue="tape_mark", treasure="ultra_box"),
]


def explain_rejection() -> str:
    return "That combination does not make a fair or readable detective mystery in the storage closet."


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.treasure and args.suspect:
        clue = next(c for c in CLUES if c.id == args.clue)
        treasure = next(t for t in TREASURES if t.id == args.treasure)
        if not valid_combo(clue, treasure, args.suspect):
            raise StoryError(explain_rejection())
    if args.treasure == "ultra_box" and args.clue == "footprint" and args.suspect not in {"teddy bear", "toy truck"}:
        raise StoryError(explain_rejection())
    return StoryParams(
        name=args.name or rng.choice(NAMES_GIRL if (args.gender or rng.choice(["girl", "boy"])) == "girl" else NAMES_BOY),
        gender=args.gender or rng.choice(["girl", "boy"]),
        helper=args.helper or rng.choice(HELPERS),
        suspect=args.suspect or rng.choice(SUSPECTS),
        clue=args.clue or rng.choice([c.id for c in CLUES]),
        treasure=args.treasure or rng.choice([t.id for t in TREASURES]),
    )


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_asp_program() -> str:
    return asp_program()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (clue, treasure, suspect) combos:\n")
        for c, t, s in stories:
            print(f"  {c:10} {t:12} {s}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.clue} / {p.treasure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
