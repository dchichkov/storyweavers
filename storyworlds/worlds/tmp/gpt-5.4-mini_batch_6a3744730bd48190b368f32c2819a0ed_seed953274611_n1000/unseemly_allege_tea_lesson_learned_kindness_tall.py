#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/unseemly_allege_tea_lesson_learned_kindness_tall.py
====================================================================================

A small tall-tale storyworld about a child, a too-earnest accusation, a tea
mess, and a kindness-based lesson learned.

Premise
-------
A boastful child notices an "unseemly" tea mishap and rushes to allege who did
it. A calmer helper slows the moment down, the truth becomes plain, and the
story ends with kindness, apologies, and a warm replacement cup.

This world is deliberately tiny and classical:
- typed entities with physical meters and emotional memes
- forward-chained causal rules
- a reasonableness gate
- an inline ASP twin
- three Q&A sets grounded in simulated state
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    scene: str
    place_sentence: str
    tea_spot: str
    style_note: str


@dataclass
class Misstep:
    id: str
    label: str
    allegation: str
    action: str
    damage: str
    makes_mess: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    label: str
    clue: str
    kindness_line: str
    learned_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    if world.get("teapot").meters["spilled"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["mess"] += 1
    world.get("Child").memes["mortification"] += 1
    world.get("Witness").memes["alarm"] += 1
    out.append("__spill__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    if world.get("Witness").memes["kindness"] < THRESHOLD:
        return out
    sig = ("soften",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("Child").memes["shame"] = max(0.0, world.get("Child").memes["shame"] - 1.0)
    world.get("Child").memes["hope"] += 1
    out.append("__soften__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("soften", _r_soften)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def reasonableness_gate(misstep: Misstep, setting: Setting) -> bool:
    return misstep.makes_mess and "tea" in misstep.tags and setting.id in SETTINGS


def spill_risk(misstep: Misstep) -> bool:
    return misstep.makes_mess


def repair_works(repair: Repair, spill: Misstep) -> bool:
    return repair.power >= 1 and spill.makes_mess


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("Child").meters["accuse"] += 1
    propagate(sim, narrate=False)
    return {
        "spill": sim.get("teapot").meters["spilled"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
        "shame": sim.get("Child").memes["mortification"],
    }


def setup(world: World, child: Entity, witness: Entity, setting: Setting) -> None:
    world.say(
        f"On a windy afternoon, {child.id} and {witness.id} came to "
        f"{setting.scene}. {setting.place_sentence}"
    )
    world.say(
        f"The place had a {setting.tea_spot}, and the whole scene had the sort of "
        f"{setting.style_note} tall-tale sparkle that makes even a teacup seem like a legend."
    )


def discover(world: World, child: Entity, misstep: Misstep) -> None:
    child.memes["pride"] += 1
    world.say(
        f"Then {child.id} saw something {misstep.label} on the table: {misstep.damage}. "
        f'{child.id} gasped, "That is unseemly tea!"'
    )


def allege(world: World, child: Entity, witness: Entity, misstep: Misstep) -> None:
    child.memes["accuse"] += 1
    world.say(
        f'"I allege that {misstep.allegation}," {child.id} declared, pointing straight at '
        f'{witness.id}. "It had to be somebody, and I mean to find out!"'
    )


def calm(world: World, witness: Entity, child: Entity) -> None:
    witness.memes["kindness"] += 1
    world.say(
        f'But {witness.id} only set a hand on {child.id}\'s shoulder and said, '
        f'"Let\'s look closely before we point a finger."'
    )


def reveal(world: World, misstep: Misstep) -> None:
    world.say(
        f"They did look closely. The truth was plain: {misstep.action}. "
        f"Nobody had been naughty on purpose; the trouble came from a bumped cup and a hurried step."
    )


def fix(world: World, witness: Entity, repair: Repair, misstep: Misstep) -> None:
    world.get("teapot").meters["spilled"] = 0.0
    world.get("room").meters["mess"] = 0.0
    world.say(
        f"{witness.id} came with a towel and {repair.text.replace('{damage}', misstep.damage)}."
    )
    world.say(
        f"The tea was set right again, and the table looked less like a storm had passed through it."
    )


def lesson(world: World, child: Entity, witness: Entity, teach: Lesson) -> None:
    child.memes["shame"] = 0.0
    child.memes["kindness"] += 1
    child.memes["lesson"] += 1
    witness.memes["kindness"] += 1
    world.say(
        f"Then {witness.id} smiled and gave the lesson: {teach.clue} "
        f"{teach.kindness_line} {teach.learned_line}"
    )
    world.say(
        f'{child.id} rubbed {child.pronoun("possessive")} chin and promised to ask kindly next time instead of alleging too fast.'
    )


def ending(world: World, child: Entity, witness: Entity, setting: Setting) -> None:
    world.say(
        f"In the end, {child.id} and {witness.id} shared a fresh cup of tea by {setting.tea_spot}, "
        f"and the room shone bright as a polished spoon."
    )


def tell(setting: Setting, misstep: Misstep, repair: Repair, teach: Lesson,
         child_name: str = "Mabel", child_gender: str = "girl",
         witness_name: str = "Uncle", witness_gender: str = "man") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    witness = world.add(Entity(id=witness_name, kind="character", type=witness_gender, role="witness"))
    teapot = world.add(Entity(id="teapot", type="thing", label="teapot"))
    room = world.add(Entity(id="room", type="room", label="parlor"))
    teapot.meters["spilled"] = 0.0
    room.meters["mess"] = 0.0

    setup(world, child, witness, setting)
    world.para()
    discover(world, child, misstep)
    allege(world, child, witness, misstep)
    calm(world, witness, child)
    propagate(world, narrate=True)
    reveal(world, misstep)

    world.para()
    fix(world, witness, repair, misstep)
    lesson(world, child, witness, teach)
    ending(world, child, witness, setting)

    world.facts.update(
        child=child,
        witness=witness,
        teapot=teapot,
        room=room,
        setting=setting,
        misstep=misstep,
        repair=repair,
        lesson=teach,
        outcome="learned",
    )
    return world


SETTINGS = {
    "porch": Setting(
        id="porch",
        scene="the creaky front porch",
        place_sentence="A brass kettle sat on a little round table, and the wind kept trying to sniff the steam.",
        tea_spot="the railing",
        style_note="big-voiced",
    ),
    "parlor": Setting(
        id="parlor",
        scene="the parlor",
        place_sentence="A striped rug lay under the chairs, and a blue teapot waited like a tiny king.",
        tea_spot="the window seat",
        style_note="moonbright",
    ),
    "garden": Setting(
        id="garden",
        scene="the garden tea table",
        place_sentence="Mason jars held flowers, and a silver tray flashed in the sun.",
        tea_spot="the rose arbor",
        style_note="wide-roaming",
    ),
}

MISSTEPS = {
    "spill": Misstep(
        id="spill",
        label="unseemly",
        allegation="someone spilled the tea",
        action="a sugar bowl tipped when the table got bumped",
        damage="tea was sloshed across the cloth",
        makes_mess=True,
        tags={"tea", "spill"},
    ),
    "stain": Misstep(
        id="stain",
        label="unseemly",
        allegation="the saucer was knocked crooked",
        action="a clumsy elbow slid the cup sideways",
        damage="tea stained the lace edge",
        makes_mess=True,
        tags={"tea", "stain"},
    ),
    "drip": Misstep(
        id="drip",
        label="unseemly",
        allegation="the teapot dripped on the floor",
        action="a lid that was not quite set right let tea run down the side",
        damage="tea dripped in a dark line",
        makes_mess=True,
        tags={"tea", "drip"},
    ),
}

REPAIRS = {
    "towel": Repair(
        id="towel",
        label="towel",
        sense=3,
        power=2,
        text="wiped the spill neat as a ribbon with a clean towel",
        fail="tried to mop the mess with a napkin, but the tea still spread",
        tags={"tea", "kindness"},
    ),
    "tray": Repair(
        id="tray",
        label="tray",
        sense=2,
        power=2,
        text="carried in a fresh tray and set the cups straight again",
        fail="straightened the cups, but the wet cloth still needed more help",
        tags={"tea", "kindness"},
    ),
    "cloth": Repair(
        id="cloth",
        label="tablecloth",
        sense=2,
        power=1,
        text="smoothed a dry tablecloth over the damp spot and made it look fit for a feast",
        fail="covered the stain, but only for a moment",
        tags={"tea", "kindness"},
    ),
}

LESSONS = {
    "kindness": Lesson(
        id="kindness",
        label="kindness",
        clue="The best detective tool is kindness.",
        kindness_line="A gentle voice helps the truth stand up straight.",
        learned_line="The child learned that alleging too fast can sting, but kindness can fix the mood and the table together.",
        tags={"lesson", "kindness"},
    ),
    "listen": Lesson(
        id="listen",
        label="listening",
        clue="A listener sees more than a blamer.",
        kindness_line="When somebody stays calm, the whole room gets calmer too.",
        learned_line="The child learned to listen first and point later, which is the proper way to tell a tall tale from a true one.",
        tags={"lesson", "kindness"},
    ),
}

CURATED = [
    StoryParams(
        setting="porch", misstep="spill", repair="towel", lesson="kindness",
        child_name="Mabel", child_gender="girl", witness_name="Uncle Harlan", witness_gender="man"
    ),
    StoryParams(
        setting="parlor", misstep="stain", repair="tray", lesson="listen",
        child_name="Jo", child_gender="boy", witness_name="Aunt Daisy", witness_gender="woman"
    ),
    StoryParams(
        setting="garden", misstep="drip", repair="cloth", lesson="kindness",
        child_name="Ivy", child_gender="girl", witness_name="Bess", witness_gender="girl"
    ),
]


@dataclass
class StoryParams:
    setting: str
    misstep: str
    repair: str
    lesson: str
    child_name: str = "Mabel"
    child_gender: str = "girl"
    witness_name: str = "Uncle"
    witness_gender: str = "man"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MISSTEPS:
            for r in REPAIRS:
                for l in LESSONS:
                    if reasonableness_gate(MISSTEPS[m], SETTINGS[s]) and repair_works(REPAIRS[r], MISSTEPS[m]):
                        combos.append((s, m, r, l))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the words "unseemly", "allege", and "tea".',
        f"Tell a story where {f['child'].id} notices an unseemly tea mishap, alleges too quickly, and learns kindness from {f['witness'].id}.",
        f"Write a gentle story with a lesson learned about kindness, starting with a tea mess and ending with a calmer truth.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    witness = f["witness"]
    setting = f["setting"]
    misstep = f["misstep"]
    repair = f["repair"]
    teach = f["lesson"]
    return [
        (
            "What did the child accuse at first?",
            f"{child.id} accused {witness.id} too quickly, saying that someone had made the tea mess. It was an unseemly guess, because the truth had not been checked yet.",
        ),
        (
            "Why did the witness calm the child down?",
            f"{witness.id} wanted {child.id} to look closely before speaking again. That kindness kept the story from turning into a bigger quarrel and helped the truth come out plainly.",
        ),
        (
            "How was the tea mess fixed?",
            f"{witness.id} used {repair.label} to clean up the tea at {setting.tea_spot}. The wet spot vanished, and the room looked ready for another round of tea.",
        ),
        (
            "What lesson did the child learn?",
            f"{teach.learned_line} The child learned that kindness and careful listening are better than alleging too fast.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["misstep"].tags) | set(f["repair"].tags) | set(f["lesson"].tags) | {"tea"}
    out: list[tuple[str, str]] = []
    if "tea" in tags:
        out.append(("What is tea?", "Tea is a warm drink made by soaking leaves in hot water. People often share it in cups and teapots."))
    if "kindness" in tags:
        out.append(("What is kindness?", "Kindness is being gentle, helpful, and caring to someone else. A kind person tries to make things better instead of meaner."))
    if "lesson" in tags:
        out.append(("What does it mean to learn a lesson?", "It means the story teaches someone a better way to act next time. The lesson stays with them after the trouble is over."))
    return out


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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
spill :- teapot_spilled.
kindness_boost :- witness_kind.
outcome(learned) :- spill, kindness_boost.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MISSTEPS.items():
        lines.append(asp.fact("misstep", mid))
        if m.makes_mess:
            lines.append(asp.fact("makes_mess", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in ASP parity:")
        rc = 1
        print(" python-only:", sorted(py - cl))
        print(" clingo-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, misstep=None, repair=None, lesson=None, child_name=None, child_gender=None, witness_name=None, witness_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale tea lesson storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--misstep", choices=MISSTEPS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--witness-name")
    ap.add_argument("--witness-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def explain_rejection(setting: Setting, misstep: Misstep, repair: Repair) -> str:
    if not reasonableness_gate(misstep, setting):
        return "(No story: this setting and mishap do not make a convincing tea problem.)"
    if not repair_works(repair, misstep):
        return f"(No story: {repair.label} would not sensibly fix this tea mess.)"
    return "(No story: invalid combination.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(f"(Refusing repair '{args.repair}': too weak for a clear lesson.)")
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.misstep is None or c[1] == args.misstep)
        and (args.repair is None or c[2] == args.repair)
        and (args.lesson is None or c[3] == args.lesson)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, misstep, repair, lesson = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    witness_gender = args.witness_gender or rng.choice(["girl", "boy", "woman", "man"])
    child_name = args.child_name or rng.choice(["Mabel", "Jo", "Ivy", "Nell", "Toby"])
    witness_name = args.witness_name or rng.choice(["Uncle Harlan", "Aunt Daisy", "Bess", "Mister Long", "Grandma Ruth"])
    return StoryParams(
        setting=setting,
        misstep=misstep,
        repair=repair,
        lesson=lesson,
        child_name=child_name,
        child_gender=child_gender,
        witness_name=witness_name,
        witness_gender=witness_gender,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("misstep", MISSTEPS), ("repair", REPAIRS), ("lesson", LESSONS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Unknown {key}: {getattr(params, key)}")
    world = tell(
        SETTINGS[params.setting],
        MISSTEPS[params.misstep],
        REPAIRS[params.repair],
        LESSONS[params.lesson],
        child_name=params.child_name,
        child_gender=params.child_gender,
        witness_name=params.witness_name,
        witness_gender=params.witness_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/4."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.child_name}: {p.misstep} / {p.repair} / {p.lesson}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
