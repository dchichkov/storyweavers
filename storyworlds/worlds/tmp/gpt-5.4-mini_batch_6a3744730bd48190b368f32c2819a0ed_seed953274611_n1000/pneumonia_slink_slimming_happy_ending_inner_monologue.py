#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pneumonia_slink_slimming_happy_ending_inner_monologue.py
=========================================================================================

A small slice-of-life storyworld about a child recovering from pneumonia, trying
to slink past rest time, and worrying about slimming down after being sick. The
story keeps a gentle cautionary tone and ends happily with a cozy recovery turn.

Seed words:
- pneumonia
- slink
- slimming

Features:
- Happy Ending
- Inner Monologue
- Cautionary
- Slice of Life
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    cozy: bool = True
    quiet: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Worry:
    id: str
    label: str
    risk: str
    comfort: str
    sense: int = 3
    power: int = 3
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    warm: bool = False
    easy: bool = True
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_rest(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.meters["coughing"] < THRESHOLD:
        return out
    sig = ("rest",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    world.get("bed").meters["used"] += 1
    out.append("__rest__")
    return out


CAUSAL_RULES = [_r_rest]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                out.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def valid_combos() -> list[tuple[str, str]]:
    return [(s, w) for s in SETTINGS for w in WORRIES if Worries[w].sense >= SENSE_MIN]


def sensible_worries() -> list[Worry]:
    return [w for w in WORRIES.values() if w.sense >= SENSE_MIN]


def _inevitable(params: "StoryParams") -> bool:
    return params.worry == "sneak"


def would_warn(params: "StoryParams") -> bool:
    return True


def predict(world: World, worry_id: str) -> dict:
    sim = world.copy()
    _do_worry(sim, sim.get("child"), WORRIES[worry_id], narrate=False)
    return {
        "coughing": sim.get("child").meters["coughing"] >= THRESHOLD,
        "rested": sim.get("bed").meters["used"] >= THRESHOLD,
    }


def _do_worry(world: World, child: Entity, worry: Worry, narrate: bool = True) -> None:
    child.memes["temptation"] += 1
    child.meters["coughing"] += 1
    child.meters["slipping"] += 1
    child.meters["slinking"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, parent: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} had been home with pneumonia for days, and the whole apartment "
        f"felt extra quiet. {place.label.capitalize()} was the kind of place where "
        f"you could hear a spoon tap a mug."
    )
    world.say(
        f"{child.id} looked at {parent.label_word} and thought, "
        f'"Maybe I can get up for just one minute."'
    )


def inner_monologue(world: World, child: Entity) -> None:
    world.say(
        f"Inside {child.pronoun('possessive')} head, a small voice whispered, "
        f'"If I slink to the kitchen, maybe nobody will notice."'
    )
    world.say(
        f"Then another thought followed right behind it: "
        f'"I am still sick, and sick lungs need rest more than snacks."'
    )


def caution(world: World, parent: Entity, child: Entity, worry: Worry) -> None:
    pred = predict(world, worry.id)
    if pred["coughing"]:
        world.facts["predicted_coughing"] = True
    world.say(
        f"{parent.label_word.capitalize()} noticed the sneaky look and said, "
        f'"No slinking around yet. {worry.risk} is still healing, and pneumonia "
        f"makes your chest tired."'
    )
    world.say(
        f'"We want your breathing to get better, not faster and worse," '
        f"{parent.pronoun()} added softly."
    )


def turn(world: World, child: Entity, parent: Entity, treat: Treat) -> None:
    child.memes["relief"] += 1
    child.memes["love"] += 1
    world.say(
        f"{child.id} paused, then nodded. The idea of being {treat.label} sounded "
        f"much nicer than sneaking around."
    )
    world.say(
        f'"Okay," {child.id} said, "I can stay in bed."'
    )


def resolution(world: World, child: Entity, parent: Entity, treat: Treat) -> None:
    child.meters["resting"] += 1
    child.memes["safety"] += 1
    world.say(
        f"{parent.label_word.capitalize()} brought {treat.phrase}, and the room "
        f"smelled warm and calm. {child.id} drank it slowly and tucked the blanket "
        f"under {child.pronoun('possessive')} chin."
    )
    world.say(
        f"By evening, {child.id} was still slim from being sick, but not worried "
        f"anymore. {child.id} was resting, smiling, and feeling a little stronger "
        f"with every easy breath."
    )
    world.say(
        f"The whole day stayed small and gentle, and that was exactly what helped."
    )


def tell(setting: Place, worry: Worry, treat: Treat, child_name: str = "Mina",
         child_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    bed = world.add(Entity(id="bed", label="the bed"))
    world.add(Entity(id="window", label="the window"))
    world.add(Entity(id="kitchen", label="the kitchen"))

    opening(world, child, parent, setting)
    world.para()
    inner_monologue(world, child)
    caution(world, parent, child, worry)
    world.para()
    turn(world, child, parent, treat)
    resolution(world, child, parent, treat)

    world.facts.update(
        child=child, parent=parent, setting=setting, worry=worry, treat=treat,
        outcome="happy", slinked=True, coughing=child.meters["coughing"] >= THRESHOLD
    )
    return world


SETTINGS = {
    "apartment": Place(id="apartment", label="the apartment", cozy=True, quiet=True, tags={"home"}),
    "bedroom": Place(id="bedroom", label="the bedroom", cozy=True, quiet=True, tags={"home"}),
    "living_room": Place(id="living_room", label="the living room", cozy=True, quiet=False, tags={"home"}),
}

WORRIES = {
    "sneak": Worry(id="sneak", label="slink to the kitchen", risk="their breathing", comfort="rest", sense=3, power=2, tags={"slink"}),
    "scale": Worry(id="scale", label="check the bathroom scale", risk="their body", comfort="not worry", sense=2, power=1, tags={"slimming"}),
    "stair": Worry(id="stair", label="tiptoe down the stairs", risk="their chest", comfort="sit back down", sense=3, power=2, tags={"caution"}),
}

TREATMENTS = {
    "tea": Treat(id="tea", label="the child was being cozy", phrase="a mug of warm tea", warm=True, tags={"warm"}),
    "soup": Treat(id="soup", label="the child was being cared for", phrase="a bowl of chicken soup", warm=True, tags={"warm"}),
    "toast": Treat(id="toast", label="the child was being comforted", phrase="buttered toast", warm=False, tags={"home"}),
}

GIRL_NAMES = ["Mina", "Nora", "Lena", "Ivy", "Maya"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Sam"]


@dataclass
class StoryParams:
    setting: str
    worry: str
    treat: str
    child: str
    gender: str
    parent: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a slice-of-life story for a young child that includes the words "pneumonia", "slink", and "slimming".',
        f"Tell a gentle cautionary story where {f['child'].id} tries to {f['worry'].label} while recovering, but listens to {f['parent'].label_word} and chooses rest instead.",
        f"Write an inner-monologue story about a child after pneumonia who worries about slimming down, then ends happily with a cozy recovery scene.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, worry, treat = f["child"], f["parent"], f["worry"], f["treat"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who is recovering from pneumonia at home with {parent.label_word}."),
        ("What was {0} trying to do?".format(child.id),
         f"{child.id} was trying to {worry.label}, which would have meant slinking away from rest time. {parent.label_word.capitalize()} stopped that plan before it went any farther."),
        ("What changed by the end?",
         f"{child.id} chose rest, drank {treat.phrase}, and felt calmer instead of sneaking around. The day ended with {child.id} tucked in and breathing easier."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is pneumonia?",
         "Pneumonia is an illness that makes the lungs sore and makes breathing hard. It usually means a person needs rest and help from a grown-up or doctor."),
        ("What does it mean to slink?",
         "To slink means to move quietly and sneakily, as if you are trying not to be noticed."),
        ("What does slimming mean?",
         "Slimming means becoming thinner or smaller around the middle. Sometimes people use the word when talking about body shape, but being sick is not a good reason to worry about it."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="apartment", worry="sneak", treat="tea", child="Mina", gender="girl", parent="mother"),
    StoryParams(setting="bedroom", worry="scale", treat="soup", child="Eli", gender="boy", parent="father"),
    StoryParams(setting="living_room", worry="stair", treat="toast", child="Nora", gender="girl", parent="mother"),
]


def explain_rejection(worry: Worry) -> str:
    return f"(No story: {worry.label} is too weak a premise for this world.)"


def valid_story(params: StoryParams) -> bool:
    return params.worry in WORRIES and params.treat in TREATMENTS and params.setting in SETTINGS


ASP_RULES = r"""
valid(S,W,T) :- setting(S), worry(W), treat(T).
sensible(W) :- worry(W), sense(W,S), min_sense(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for wid, w in WORRIES.items():
        lines.append(asp.fact("worry", wid))
        lines.append(asp.fact("sense", wid, w.sense))
    for tid in TREATMENTS:
        lines.append(asp.fact("treat", tid))
    lines.append(asp.fact("min_sense", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(w for (w,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((s, w, t) for s in SETTINGS for w in WORRIES for t in TREATMENTS):
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:  # noqa: BLE001
        print(f"Smoke test failed: {e}")
        return 1
    print("OK: story generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life pneumonia / slink / slimming storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--worry", choices=WORRIES)
    ap.add_argument("--treat", choices=TREATMENTS)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    worry = args.worry or rng.choice(list(WORRIES))
    treat = args.treat or rng.choice(list(TREATMENTS))
    if not valid_story(StoryParams(setting=setting, worry=worry, treat=treat, child="x", gender="girl", parent="mother")):
        raise StoryError("Invalid story choices.")
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, worry=worry, treat=treat, child=child, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.worry not in WORRIES or params.treat not in TREATMENTS:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], WORRIES[params.worry], TREATMENTS[params.treat],
                 child_name=params.child, child_gender=params.gender, parent_type=params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible worries:", ", ".join(asp_sensible()))
        print("valid combos:")
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
