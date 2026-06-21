#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/helmet_repertoire_dialogue_conflict_lesson_learned_tall.py
=========================================================================================

A standalone storyworld for a tall-tale style story about a child performer,
a treasured helmet, a growing repertoire of tricks, a conflict over unsafe
showmanship, and a lesson learned through dialogue.

The world is intentionally small: one child wants to add a grand new stunt to
a performance, another character objects, and a calmer choice turns the show
into a safer, brighter ending. The prose is state-driven rather than templated:
meters track physical setup and performance risk; memes track feelings, pride,
frustration, and relief.

Supported modes:
- default / -n / --all / --seed
- --trace / --qa / --json
- --asp / --verify / --show-asp
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
RISK_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Place:
    id: str
    label: str
    stage: str
    audience: str
    open_air: bool = True


@dataclass
class Performer:
    id: str
    title: str
    noun: str
    repertoire: tuple[str, ...]
    flair: str


@dataclass
class Helmet:
    id: str
    label: str
    phrase: str
    kind: str
    protects: str
    shine: str


@dataclass
class ConflictBeat:
    id: str
    concern: str
    danger: str
    dialogue: str
    remedy: str
    lesson: str
    risk: int
    calm: int


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
class StoryParams:
    place: str
    performer: str
    helmet: str
    conflict: str
    seed: Optional[int] = None


class Rule:
    def __init__(self, name: str, tag: str, apply: Callable[[World], list[str]]) -> None:
        self.name = name
        self.tag = tag
        self.apply = apply


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    perf = world.get("child")
    beat = world.facts["beat"]
    if perf.meters["showboating"] >= THRESHOLD and perf.meters["helmet_on"] < THRESHOLD:
        sig = ("risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            perf.meters["risk"] += beat.risk
            perf.memes["alarm"] += 1
            out.append("__risk__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    perf = world.get("child")
    if perf.memes["frustration"] >= THRESHOLD and perf.memes["relief"] < THRESHOLD:
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            perf.memes["frustration"] = max(0.0, perf.memes["frustration"] - 1.0)
            perf.memes["listening"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule("risk", "physical", _r_risk),
    Rule("calm", "social", _r_calm),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def performance_could_turn_bad(beat: ConflictBeat, has_helmet: bool) -> bool:
    return beat.risk >= RISK_MIN and not has_helmet


def chosen_helmet(helmet: Helmet) -> bool:
    return helmet.protects == "head"


def reasonableness_gate(beat: ConflictBeat, helmet: Helmet) -> bool:
    return performance_could_turn_bad(beat, False) and chosen_helmet(helmet)


def predict(world: World, with_helmet: bool) -> dict:
    sim = world.copy()
    child = sim.get("child")
    if with_helmet:
        child.meters["helmet_on"] = 1.0
    child.meters["showboating"] = 1.0
    propagate(sim, narrate=False)
    return {
        "risk": child.meters["risk"],
        "alarm": child.memes["alarm"],
    }


def introduce(world: World, child: Entity, place: Place, performer: Performer) -> None:
    child.memes["joy"] += 1
    world.say(
        f"At {place.label}, {child.id} was a small storm in boots, ready to "
        f"try {performer.noun} tricks from {len(performer.repertoire)} brave pages of "
        f"{performer.title.lower()}'s repertoire."
    )
    world.say(
        f"The stage was {place.stage}, and the crowd was {place.audience}, all "
        f"waiting for a tale with dust on its boots."
    )


def dialogue_world(world: World, child: Entity, guardian: Entity, beat: ConflictBeat) -> None:
    world.say(
        f'"{beat.dialogue}" asked {guardian.id}. "{beat.concern}," said {guardian.id}, '
        f"glancing at {child.id}'s bare head and the wobbly ladder."
    )
    child.memes["pride"] += 1
    child.memes["frustration"] += 1
    world.say(
        f'"I can do the stunt," said {child.id}. "I know the whole repertoire."'
    )


def conflict_turn(world: World, child: Entity, beat: ConflictBeat) -> None:
    child.meters["showboating"] += 1
    child.memes["defiance"] += 1
    world.say(
        f"But the more the crowd cheered, the taller {child.id} stood. "
        f"{beat.danger} made the ladder feel like a skinny string in a thunderstorm."
    )


def helmet_offer(world: World, child: Entity, helmet: Helmet, beat: ConflictBeat) -> None:
    child.meters["helmet_on"] += 1
    child.memes["relief"] += 1
    world.say(
        f'"Then wear the {helmet.label}," said the guardian. "{beat.remedy}." '
        f"The {helmet.label} shone {helmet.shine}, stout as an iron moon."
    )


def lesson_learned(world: World, child: Entity, guardian: Entity, beat: ConflictBeat, helmet: Helmet) -> None:
    child.memes["lesson"] += 1
    child.memes["joy"] += 1
    world.say(
        f'"You were right," said {child.id}. "A big repertoire is worth more when '
        f"you live to perform it again."'
    )
    world.say(
        f'{guardian.id} smiled. "{beat.lesson}"'
    )
    world.say(
        f"So {child.id} kept the {helmet.label} on, bowed to the crowd, and made "
        f"the smallest stunt look taller than a barn roof."
    )


def tell(place: Place, performer: Performer, helmet: Helmet, beat: ConflictBeat,
         child_name: str = "Nell", child_gender: str = "girl",
         guardian_name: str = "Aunt June", guardian_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="performer"))
    guardian = world.add(Entity(id=guardian_name, kind="character", type=guardian_gender, role="guardian"))
    world.facts["beat"] = beat
    world.facts["helmet"] = helmet
    world.facts["performer"] = performer
    world.facts["place"] = place

    introduce(world, child, place, performer)
    world.para()
    dialogue_world(world, child, guardian, beat)
    conflict_turn(world, child, beat)

    if reasonableness_gate(beat, helmet):
        pred = predict(world, with_helmet=True)
        world.facts["pred"] = pred
        world.para()
        helmet_offer(world, child, helmet, beat)
        propagate(world, narrate=False)
        lesson_learned(world, child, guardian, beat, helmet)
        child.meters["helmet_on"] = 1.0
    else:
        raise StoryError("This storyworld only tells tales where the helmet choice matters.")

    world.facts["child"] = child
    world.facts["guardian"] = guardian
    return world


PLACES = {
    "fair": Place(id="fair", label="the county fair", stage="high as a wagon wheel", audience="a ring of farmers and children"),
    "rodeo": Place(id="rodeo", label="the rodeo grounds", stage="wide and dusty", audience="cowhands, cousins, and curious hens"),
    "parade": Place(id="parade", label="the town parade", stage="long as a river road", audience="a mile of waving hats"),
}

PERFORMERS = {
    "juggler": Performer(id="juggler", title="Juggler", noun="juggling", repertoire=("apples", "pins", "beans", "bells"), flair="quick"),
    "rider": Performer(id="rider", title="Rider", noun="riding", repertoire=("spins", "salutes", "backward turns", "one-handed waves"), flair="daring"),
    "dancer": Performer(id="dancer", title="Dancer", noun="dancing", repertoire=("kicks", "twirls", "skips", "claps"), flair="bright"),
}

HELMETS = {
    "brass": Helmet(id="brass", label="brass helmet", phrase="a brass helmet", kind="helmet", protects="head", shine="like a sunrise"),
    "painted": Helmet(id="painted", label="painted helmet", phrase="a painted helmet", kind="helmet", protects="head", shine="like a circus trumpet"),
}

CONFLICTS = {
    "ladder": ConflictBeat(id="ladder", concern="That ladder is too tall for bare heads", danger="One wrong wobble could tumble the whole trick", dialogue="Do you hear me, daredevil?", remedy="A helmet makes a tumble less mean", lesson="The clever performer protects the head before the applause", risk=2, calm=2),
    "horse": ConflictBeat(id="horse", concern="That horse tosses its tail like a thundercloud", danger="The arena has no patience for a foolish bump", dialogue="Will you listen before you leap?", remedy="A helmet belongs in every brave performance", lesson="A wise showman keeps the head safe and the crowd cheering", risk=3, calm=3),
    "tightrope": ConflictBeat(id="tightrope", concern="That rope is thin enough to floss a moonbeam", danger="A slip would send sparks across the stage", dialogue="Are you listening to me now?", remedy="A helmet keeps courage from turning careless", lesson="Big bragging needs a small helmet and a bigger brain", risk=2, calm=2),
}

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for perf in PERFORMERS:
            for hb in HELMETS:
                for cf in CONFLICTS:
                    combos.append((p, perf, hb, cf))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a helmet, a repertoire, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--performer", choices=PERFORMERS)
    ap.add_argument("--helmet", choices=HELMETS)
    ap.add_argument("--conflict", choices=CONFLICTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.performer is None or c[1] == args.performer)
              and (args.helmet is None or c[2] == args.helmet)
              and (args.conflict is None or c[3] == args.conflict)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, performer, helmet, conflict = rng.choice(sorted(combos))
    return StoryParams(place=place, performer=performer, helmet=helmet, conflict=conflict)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.performer not in PERFORMERS or params.helmet not in HELMETS or params.conflict not in CONFLICTS:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], PERFORMERS[params.performer], HELMETS[params.helmet], CONFLICTS[params.conflict])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    perf: Performer = f["performer"]
    helmet: Helmet = f["helmet"]
    beat: ConflictBeat = f["beat"]
    return [
        f'Write a tall-tale story for a young child that uses the words "{helmet.label}" and "{perf.title.lower()}" and includes a spoken warning.',
        f"Tell a story where a child brags about a {perf.title.lower()} repertoire, another character raises a conflict about safety, and a helmet solves the problem.",
        f'Write a barn-bright tall tale where dialogue leads to a lesson learned about wearing a helmet before a daring performance.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    guardian: Entity = f["guardian"]
    helmet: Helmet = f["helmet"]
    beat: ConflictBeat = f["beat"]
    perf: Performer = f["performer"]
    return [
        ("What did the child want to do?",
         f"{child.id} wanted to use the whole {perf.title.lower()} repertoire and show the crowd a daring trick."),
        ("Why did the guardian worry?",
         f"{guardian.id} worried because {beat.concern.lower()}. The trick felt grand, but it also sounded risky without a helmet."),
        ("How was the conflict solved?",
         f"The guardian suggested the {helmet.label}. That turned the argument into a safer plan and let the performance go on."),
        ("What lesson was learned?",
         f"{beat.lesson}. The child learned that bravery lasts longer when the head is protected."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a helmet?",
         "A helmet is a hard hat that helps protect your head. People wear one for riding, biking, or other risky play."),
        ("What is a repertoire?",
         "A repertoire is a collection of songs, tricks, or skills someone knows how to do. A performer with a big repertoire can choose many different acts."),
        ("Why do performers practice?",
         "Performers practice so their tricks look smooth and so they can stay safe. Practice helps them remember what to do next."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="fair", performer="juggler", helmet="brass", conflict="ladder"),
    StoryParams(place="rodeo", performer="rider", helmet="painted", conflict="horse"),
    StoryParams(place="parade", performer="dancer", helmet="brass", conflict="tightrope"),
]


ASP_RULES = r"""
valid(P, Pe, H, C) :- place(P), performer(Pe), helmet(H), conflict(C).
helmet_ok(H) :- helmet(H), protects_head(H).
risk(C) :- conflict(C), risk_level(C, R), R >= 1.
compatible(P, Pe, H, C) :- valid(P, Pe, H, C), helmet_ok(H), risk(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for pe in PERFORMERS:
        lines.append(asp.fact("performer", pe))
    for h, obj in HELMETS.items():
        lines.append(asp.fact("helmet", h))
        if obj.protects == "head":
            lines.append(asp.fact("protects_head", h))
    for c, obj in CONFLICTS.items():
        lines.append(asp.fact("conflict", c))
        lines.append(asp.fact("risk_level", c, obj.risk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


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
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    perf: Performer = f["performer"]
    helmet: Helmet = f["helmet"]
    return [
        f'Write a tall-tale story for a young child that uses the words "{helmet.label}" and "{perf.title.lower()}" and includes a spoken warning.',
        f"Tell a story where a child brags about a {perf.title.lower()} repertoire, another character raises a conflict about safety, and a helmet solves the problem.",
        f'Write a barn-bright tall tale where dialogue leads to a lesson learned about wearing a helmet before a daring performance.',
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a helmet?",
         "A helmet is a hard hat that helps protect your head. People wear one for riding, biking, or other risky play."),
        ("What is a repertoire?",
         "A repertoire is a collection of songs, tricks, or skills someone knows how to do. A performer with a big repertoire can choose many different acts."),
        ("Why do performers practice?",
         "Performers practice so their tricks look smooth and so they can stay safe. Practice helps them remember what to do next."),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    guardian: Entity = f["guardian"]
    helmet: Helmet = f["helmet"]
    beat: ConflictBeat = f["beat"]
    perf: Performer = f["performer"]
    return [
        ("What did the child want to do?",
         f"{child.id} wanted to use the whole {perf.title.lower()} repertoire and show the crowd a daring trick."),
        ("Why did the guardian worry?",
         f"{guardian.id} worried because {beat.concern.lower()}. The trick felt grand, but it also sounded risky without a helmet."),
        ("How was the conflict solved?",
         f"The guardian suggested the {helmet.label}. That turned the argument into a safer plan and let the performance go on."),
        ("What lesson was learned?",
         f"{beat.lesson}. The child learned that bravery lasts longer when the head is protected."),
    ]


if __name__ == "__main__":
    main()
