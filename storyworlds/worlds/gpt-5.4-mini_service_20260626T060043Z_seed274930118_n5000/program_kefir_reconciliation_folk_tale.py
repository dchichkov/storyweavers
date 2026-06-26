#!/usr/bin/env python3
"""
storyworlds/worlds/program_kefir_reconciliation_folk_tale.py
=============================================================

A small folk-tale story world about a village program, a cup of kefir, and a
hurt feeling that is repaired through reconciliation.

Premise:
- A child helps prepare a village program.
- A cup of kefir is meant to be shared afterward.
- A misunderstanding causes pride and hurt.
- The adults and children find a gentle way to apologize, repair trust, and
  share the kefir together.

The story is modeled as a tiny simulation with physical meters and emotional
memes. It includes a Python reasonableness gate and a matching inline ASP twin.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["broken", "spilled", "warm", "clean"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "pride", "hurt", "guilt", "love", "peace", "gratitude"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    mess: str
    risk_region: str
    guards: set[str] = field(default_factory=set)


@dataclass
class Program:
    id: str
    place: str
    purpose: str
    song: str
    crowd: str
    keyword: str = "program"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    child: str
    gender: str
    elder: str
    helper: str
    prize: str
    program: str
    seed: Optional[int] = None


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    if helper.meters["spilled"] < THRESHOLD:
        return out
    cup = world.get("kefir")
    if cup.meters["spilled"] >= THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cup.meters["spilled"] = 1.0
    cup.meters["clean"] = 0.0
    out.append("The kefir splashed onto the tablecloth.")
    return out


def _r_hurt(world: World) -> list[str]:
    helper = world.get("helper")
    elder = world.get("elder")
    if helper.meters["spilled"] < THRESHOLD:
        return []
    sig = ("hurt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder.memes["hurt"] += 1
    helper.memes["guilt"] += 1
    return ["__hurt__"]


def _r_reconcile(world: World) -> list[str]:
    helper = world.get("helper")
    elder = world.get("elder")
    child = world.get("child")
    if elder.memes["hurt"] < THRESHOLD or helper.memes["guilt"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder.memes["hurt"] = 0.0
    helper.memes["guilt"] = 0.0
    child.memes["peace"] += 1
    elder.memes["peace"] += 1
    return [
        "They spoke kindly, and the wrong feeling began to soften.",
        "__reconcile__",
    ]


CAUSAL_RULES = [_r_spill, _r_hurt, _r_reconcile]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    if s not in {"__hurt__", "__reconcile__"}:
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def program_at_risk(program: Program, item: Item) -> bool:
    return program.purpose in {"tea", "sharing", "celebration"} and item.mess == "spill"


def select_fix(program: Program, item: Item) -> bool:
    return "cloth" in item.guards or item.risk_region == "table"


SETTINGS = {
    "village_square": Setting(place="the village square", affords={"singing", "sharing"}),
    "hearth_room": Setting(place="the hearth room", indoor=True, affords={"singing", "sharing"}),
    "orchard": Setting(place="the orchard", affords={"singing", "sharing"}),
}

PROGRAMS = {
    "song_pageant": Program(
        id="song_pageant",
        place="the village square",
        purpose="celebration",
        song="a bright little song",
        crowd="the neighbors",
    ),
    "story_circle": Program(
        id="story_circle",
        place="the hearth room",
        purpose="sharing",
        song="a warm telling of old tales",
        crowd="the family",
    ),
}

PRIZES = {
    "kefir": Item(
        id="kefir",
        label="kefir",
        phrase="a clay cup of cold kefir",
        mess="spill",
        risk_region="table",
        guards={"cloth", "tray"},
    ),
    "cloth": Item(
        id="cloth",
        label="tablecloth",
        phrase="a woven tablecloth",
        mess="spill",
        risk_region="table",
        guards={"cloth"},
    ),
}

GIRL_NAMES = ["Anya", "Mila", "Nadia", "Rina", "Sofya", "Lena"]
BOY_NAMES = ["Boris", "Ilya", "Marek", "Pavel", "Yuri", "Toma"]
ELDERS = ["grandmother", "grandfather", "aunt", "uncle"]
HELPERS = ["girl", "boy"]
TRAITS = ["kind", "brave", "quiet", "cheerful", "careful", "stubborn"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for prog_id, prog in PROGRAMS.items():
            if prog.place != setting.place:
                continue
            for prize_id, prize in PRIZES.items():
                if program_at_risk(prog, prize) and select_fix(prog, prize):
                    out.append((place, prog_id, prize_id))
    return out


def explain_rejection(program: Program, prize: Item) -> str:
    return (
        f"(No story: the {program.id} cannot honestly threaten {prize.label} "
        f"well enough for a reconciliation tale, or no fitting fix exists.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about a program, kefir, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--program", choices=PROGRAMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child")
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.program and args.prize:
        prog, prize = PROGRAMS[args.program], PRIZES[args.prize]
        if not (program_at_risk(prog, prize) and select_fix(prog, prize)):
            raise StoryError(explain_rejection(prog, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.program is None or c[1] == args.program)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, program_id, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDERS)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, child=child, gender=gender, elder=elder, helper=helper, prize=prize_id, program=program_id)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.child, traits=["little", "careful"]))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder, label=f"the {params.elder}"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    kefir = world.add(Entity(id="kefir", type="thing", label="kefir", owner=child.id, caretaker=elder.id))
    cloth = world.add(Entity(id="cloth", type="thing", label="tablecloth", owner=elder.id, caretaker=elder.id))
    prog = PROGRAMS[params.program]

    child.memes["joy"] += 1
    child.memes["love"] += 1
    world.say(f"{child.label} helped prepare the village {prog.keyword}.")
    world.say(f"{child.label} loved the {prog.song} and the way {prog.crowd} would gather to listen.")
    world.say(f"Before the singing began, {child.label}'s {params.elder} set out a cup of kefir for everyone to share.")
    world.para()
    world.say(f"When the day came, the {prog.crowd} gathered at {setting.place}.")
    world.say(f"{child.label} wanted to carry the kefir proudly, but the cup was slippery from the chill.")
    helper.meters["spilled"] += 1
    propagate(world, narrate=True)
    world.say(f"{child.label} froze at the splash, and {params.elder} looked hurt for a moment.")
    world.para()
    world.say(f"Then {child.label} bowed {('her' if params.gender == 'girl' else 'his')} head and said sorry.")
    world.say(f"The {params.elder} answered with a gentle voice, and the {helper.label} wiped the table clean with the cloth.")
    world.say("The three of them made peace, and the apology felt like a small lantern warming the room.")
    child.memes["gratitude"] += 1
    elder.memes["love"] += 1
    elder.memes["peace"] += 1
    child.memes["peace"] += 1
    world.say(f"After that, they shared the kefir together, and the village program continued with smiles instead of frowns.")
    world.say(f"By the end, the cup was empty, the table was clean, and the old hurt had vanished like mist at sunrise.")
    world.facts.update(child=child, elder=elder, helper=helper, kefir=kefir, cloth=cloth, program=prog)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    prog = f["program"]
    return [
        f'Write a short folk tale about a village {prog.keyword}, a cup of kefir, and a gentle reconciliation.',
        f"Tell a child-friendly story where {child.label} helps with a {prog.keyword} and repairs a hurt feeling after a mishap.",
        f"Write a warm folk tale in which a spilled cup of kefir leads to apology, forgiveness, and shared celebration.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, elder, prog = f["child"], f["elder"], f["program"]
    return [
        QAItem(
            question=f"Who helped prepare the village {prog.keyword}?",
            answer=f"{child.label} helped prepare the village {prog.keyword}.",
        ),
        QAItem(
            question=f"What drink was meant to be shared during the story?",
            answer="A cup of kefir was set out to be shared.",
        ),
        QAItem(
            question=f"What fixed the hurt feeling after the spill?",
            answer=f"An apology, a kind reply, and the cloth wiping the table helped everyone reconcile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kefir?",
            answer="Kefir is a tangy milk drink made with friendly cultures, often served cold.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make peace after a disagreement by apologizing and forgiving.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a traditional story passed along by people, often with a simple lesson.",
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
    lines.append("== World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
program_at_risk(P, K) :- program(P), prize(K), need_sharing(P), spill_prize(K).
has_fix(P, K) :- program_at_risk(P, K), prize_fix(K).
valid(Place, Prog, Prize) :- setting(Place), program(Prog), prize(Prize), program_place(Prog, Place), has_fix(Prog, Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
    for pid, prog in PROGRAMS.items():
        lines.append(asp.fact("program", pid))
        lines.append(asp.fact("program_place", pid, "village_square" if prog.place == "the village square" else "hearth_room" if prog.place == "the hearth room" else "orchard"))
        lines.append(asp.fact("need_sharing", pid))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        if prize.mess == "spill":
            lines.append(asp.fact("spill_prize", prize_id))
        if "cloth" in prize.guards:
            lines.append(asp.fact("prize_fix", prize_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set((place, prog, prize) for place, prog, prize in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


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
    StoryParams(place="village_square", child="Anya", gender="girl", elder="grandmother", helper="girl", prize="kefir", program="song_pageant"),
    StoryParams(place="hearth_room", child="Yuri", gender="boy", elder="aunt", helper="boy", prize="kefir", program="story_circle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:\n")
        for t in vals:
            print("  ", t)
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
