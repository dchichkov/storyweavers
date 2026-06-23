#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_service_20260622T045816Z_seed1855084837_n10/solid_trumpet_copper_sound_effects_cautionary_fable.py
===============================================================================================================================

A small, self-contained storyworld in the style of a cautionary fable.

Premise:
- A young trumpeter finds a shiny copper trumpet and wants to play it in a quiet
  meadow.
- The trumpet is solid and loud; its sound draws trouble when used carelessly.
- A wise helper warns the child, and the ending proves that a safer choice
  changes the outcome.

The world model tracks physical meters and emotional memes, and the prose is
driven by state rather than template swapping. Sound effects are folded into the
narration as child-facing onomatopoeia.
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
from typing import Optional

# Robust local imports: walk upward until we find results.py.
_HERE = os.path.abspath(os.path.dirname(__file__))
_CUR = _HERE
while True:
    if os.path.exists(os.path.join(_CUR, "results.py")):
        if _CUR not in sys.path:
            sys.path.insert(0, _CUR)
        break
    parent = os.path.dirname(_CUR)
    if parent == _CUR:
        break
    _CUR = parent

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
    owner: str = ""
    target: str = ""
    loud: bool = False
    fragile: bool = False
    protective: bool = False
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
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    quiet: bool = False
    outdoors: bool = True
    sounds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    loudness: int
    made_of: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Warning:
    id: str
    label: str
    phrase: str
    method: str
    safety_gain: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []
        self.noise: int = 0

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
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
        clone.noise = self.noise
        return clone


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    instrument: str
    warning: str
    seed: Optional[int] = None


PLACES = {
    "meadow": Place(id="meadow", label="the meadow", quiet=False, outdoors=True, sounds={"birdsong", "wind"}),
    "lane": Place(id="lane", label="the lane", quiet=False, outdoors=True, sounds={"hoofbeats", "wind"}),
    "court": Place(id="court", label="the courtyard", quiet=True, outdoors=True, sounds={"echo"}),
}

INSTRUMENTS = {
    "trumpet": Instrument(
        id="trumpet",
        label="trumpet",
        phrase="a solid copper trumpet",
        sound="PLOP-PAH!",
        loudness=3,
        made_of="copper",
        tags={"trumpet", "copper", "solid", "sound_effects", "fable"},
    ),
    "horn": Instrument(
        id="horn",
        label="horn",
        phrase="a copper horn",
        sound="TOO-RAH!",
        loudness=2,
        made_of="copper",
        tags={"copper", "sound_effects", "fable"},
    ),
}

WARNINGS = {
    "gentle": Warning(
        id="gentle",
        label="gentle warning",
        phrase="a gentle warning",
        method="play softly and away from sleeping birds",
        safety_gain=2,
        tags={"cautionary", "fable"},
    ),
    "cautious": Warning(
        id="cautious",
        label="cautious warning",
        phrase="a cautious warning",
        method="wait until the market is open and the road is busy",
        safety_gain=3,
        tags={"cautionary", "fable"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Sana", "Ivy", "Tia"]
BOY_NAMES = ["Arlo", "Pico", "Tomas", "Bram", "Kian", "Noel"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for inst in INSTRUMENTS:
            for warn in WARNINGS:
                combos.append((place, inst, warn))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary fable about a copper trumpet and a wise warning.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.instrument is None or c[1] == args.instrument)
              and (args.warning is None or c[2] == args.warning)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, inst, warn = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender)
    if helper_name == child_name:
        helper_name = _pick_name(rng, helper_gender)
        if helper_name == child_name:
            helper_name = helper_name + "a"
    return StoryParams(
        place=place,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        instrument=inst,
        warning=warn,
    )


def _setup_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.instrument not in INSTRUMENTS:
        raise StoryError(f"Unknown instrument: {params.instrument}")
    if params.warning not in WARNINGS:
        raise StoryError(f"Unknown warning: {params.warning}")

    world = World(PLACES[params.place])
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name, role="helper"))
    instrument = INSTRUMENTS[params.instrument]
    warning = WARNINGS[params.warning]
    world.add(Entity(id="instrument", kind="thing", type="instrument", label=instrument.label, phrase=instrument.phrase, loud=True, attrs={"made_of": instrument.made_of}))
    world.add(Entity(id="song", kind="thing", type="sound", label=instrument.sound, phrase=instrument.sound, fragile=False))
    world.facts.update(
        child=child,
        helper=helper,
        instrument=instrument,
        warning=warning,
        place=world.place,
        outcome="",
    )
    return world


def _sound_line(sound: str, place: Place) -> str:
    if place.quiet:
        return f"The trumpet went {sound} and the courtyard answered with a soft echo."
    if "wind" in place.sounds:
        return f"The trumpet went {sound}, and the wind seemed to carry it far away."
    return f"The trumpet went {sound}, bright as a bell."


def _warn(world: World, helper: Entity, child: Entity, warning: Warning) -> None:
    helper.memes["caution"] += 1
    world.say(f"{helper.label} gave {warning.phrase} and said, \"Use it only when it is wise.\"")
    world.say(f"{helper.label} wanted {child.label} to choose {warning.method}.")
    child.memes["attention"] += 1


def _tempt(world: World, child: Entity, instrument: Instrument) -> None:
    child.memes["desire"] += 1
    child.meters["holding"] += 1
    world.say(f"{child.label} found {instrument.phrase}. It felt solid and cool in {child.pronoun('possessive')} hands.")
    world.say(f"{child.label} smiled at the copper shine and lifted it high.")


def _unwise_blow(world: World, child: Entity, instrument: Instrument) -> None:
    world.noise += instrument.loudness
    child.memes["boldness"] += 1
    child.meters["blown"] += 1
    world.say(f"Then came {instrument.sound} {instrument.sound} from the trumpet.")
    world.say(_sound_line(instrument.sound, world.place))


def _consequence(world: World, child: Entity, helper: Entity, warning: Warning, instrument: Instrument) -> None:
    if world.noise >= instrument.loudness:
        child.memes["startle"] += 1
        helper.memes["worry"] += 1
        world.say(f"The birds burst from the hedge, fluttering away in a rush of wings.")
        world.say(f"{helper.label} called, \"Too loud, and too soon! That is why we wait and watch.\"")
    else:
        world.say(f"Nothing bad happened, and the day stayed calm.")
    world.say(f"{helper.label} showed how patience could be brighter than noise.")


def _resolution(world: World, child: Entity, helper: Entity, instrument: Instrument) -> None:
    child.memes["learned"] += 1
    helper.memes["pride"] += 1
    child.meters["careful"] += 1
    world.say(f"{child.label} lowered the trumpet and listened.")
    world.say(f"At last {child.label} chose a softer tune, and the copper trumpet sounded kind instead of wild.")
    world.say(f"Together they walked away from the meadow, wiser than before.")


def tell(place: Place, instrument: Instrument, warning: Warning, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    instr = world.add(Entity(id="instrument", kind="thing", type="instrument", label=instrument.label, phrase=instrument.phrase, loud=True, attrs={"made_of": instrument.made_of}))
    world.facts.update(child=child, helper=helper, instrument=instrument, warning=warning, place=place)

    world.say(f"{child.label} was a little {child_gender} who loved music and shiny things.")
    world.say(f"One day {child.label} found {instrument.phrase}.")
    world.say(f"The trumpet was made of {instrument.made_of}, and it looked solid enough to last forever.")
    world.para()
    world.say(f"{child.label} wanted to play it in {place.label}.")
    _tempt(world, child, instrument)
    _warn(world, helper, child, warning)
    world.para()
    _unwise_blow(world, child, instrument)
    _consequence(world, child, helper, warning, instrument)
    world.para()
    _resolution(world, child, helper, instrument)
    world.say(f"In the end, {child.label} learned that a strong thing is not always a wise thing.")
    world.say(f"The copper trumpet still shone, but now it was used with care.")
    world.facts["outcome"] = "learned"
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], INSTRUMENTS[params.instrument], WARNINGS[params.warning],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    inst: Instrument = f["instrument"]
    warn: Warning = f["warning"]
    place: Place = f["place"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    return [
        f'Write a short cautionary fable for a young child about a solid {inst.made_of} trumpet and a wise warning in {place.label}.',
        f"Tell a story where {child.label} wants to blow a {inst.label} in {place.label}, but {helper.label} helps {child.label} choose a safer way.",
        f'Write a fable that includes the sound "{inst.sound}" and ends with a lesson about patience and caution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    inst: Instrument = f["instrument"]
    warn: Warning = f["warning"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"What did {child.label} find in {place.label}?",
            answer=f"{child.label} found {inst.phrase}. It was a solid trumpet made of copper, and it looked exciting to play.",
        ),
        QAItem(
            question=f"Why did {helper.label} warn {child.label} about the trumpet?",
            answer=f"{helper.label} warned {child.label} because the trumpet was loud and could disturb the quiet place. {helper.label} wanted {child.label} to choose {warn.method} instead.",
        ),
        QAItem(
            question=f"What sound did the trumpet make when {child.label} blew it?",
            answer=f"It made {inst.sound}. The sound bounced around the meadow, so everyone could hear it at once.",
        ),
        QAItem(
            question=f"What did {child.label} learn by the end of the story?",
            answer=f"{child.label} learned that strong things are not always wise to use in every place. Careful choices keep the day calm and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    inst: Instrument = f["instrument"]
    warn: Warning = f["warning"]
    qa = [
        QAItem(
            question="What is copper?",
            answer="Copper is a reddish metal that can be shaped into tools, pots, or instruments. It shines warmly when it is polished.",
        ),
        QAItem(
            question="What does solid mean?",
            answer="Solid means something is hard and keeps its shape. A solid object does not spill or flow like water.",
        ),
        QAItem(
            question="What is a trumpet?",
            answer="A trumpet is a brass instrument that makes bright, strong notes when someone blows into it.",
        ),
    ]
    if "cautionary" in warn.tags:
        qa.append(QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story is a tale that warns about a mistake and shows a better choice. It helps the listener learn to be careful.",
        ))
    if "sound_effects" in inst.tags:
        qa.append(QAItem(
            question="Why do stories use sound effects?",
            answer="Sound effects help readers hear the action in their minds. They make a story feel lively and easy to picture.",
        ))
    return qa


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


ASP_RULES = r"""
kind(place).
kind(instrument).
kind(warning).

solid_inst(I) :- instrument(I), made_of(I,copper).
cautionary(W) :- warning(W).
sound_effects(I) :- instrument(I), loudness(I,N), N >= 2.
valid(P,I,W) :- place(P), instrument(I), warning(W), solid_inst(I), cautionary(W), sound_effects(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.quiet:
            lines.append(asp.fact("quiet", pid))
    for iid, inst in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        lines.append(asp.fact("made_of", iid, inst.made_of))
        lines.append(asp.fact("loudness", iid, inst.loudness))
    for wid in WARNINGS:
        lines.append(asp.fact("warning", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    sample_ok = True
    try:
        sample = generate(StoryParams(
            place="meadow",
            child_name="Lina",
            child_gender="girl",
            helper_name="Bram",
            helper_gender="boy",
            instrument="trumpet",
            warning="gentle",
        ))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        sample_ok = False

    py_set = set(valid_combos())
    try:
        asp_set = set(asp_valid_combos())
    except Exception as err:
        print(f"ASP FAILED: {err}")
        return 1

    ok = sample_ok and py_set == asp_set
    if ok:
        print(f"OK: generate smoke test passed; ASP matches Python ({len(py_set)} combos).")
        return 0
    print("Mismatch or smoke-test failure.")
    if py_set != asp_set:
        print("only python:", sorted(py_set - asp_set))
        print("only asp:", sorted(asp_set - py_set))
    return 1


def explain_invalid(params: StoryParams) -> str:
    return f"(No story: invalid parameters {params}.)"


def _emit_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(_emit_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="meadow", child_name="Lina", child_gender="girl", helper_name="Bram", helper_gender="boy", instrument="trumpet", warning="gentle"),
            StoryParams(place="lane", child_name="Pico", child_gender="boy", helper_name="Mira", helper_gender="girl", instrument="horn", warning="cautious"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
