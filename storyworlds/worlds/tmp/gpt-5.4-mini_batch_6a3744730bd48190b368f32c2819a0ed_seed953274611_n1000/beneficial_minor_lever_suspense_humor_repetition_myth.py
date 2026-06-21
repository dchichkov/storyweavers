#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/beneficial_minor_lever_suspense_humor_repetition_myth.py
========================================================================================

A tiny myth-like storyworld about a small temple task: a child, a harmless but
mysterious lever, a tense chamber, a comedic repetition beat, and a beneficial
ending where a minor act helps the whole village.

Seed words: beneficial, minor, lever
Style: Myth
Features: Suspense, Humor, Repetition
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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Chamber:
    id: str
    label: str
    mood: str
    shimmer: str
    echoes: str
    lever_name: str
    lever_phrase: str
    lever_kind: str
    lever_marks: list[str] = field(default_factory=list)


@dataclass
class Outcome:
    id: str
    kind: str
    sense: int
    power: int
    text: str
    fail: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["alarm"] < THRESHOLD:
            continue
        sig = ("alarm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("guardian").memes["worry"] += 1
        world.get("child").memes["suspense"] += 1
        out.append("__alarm__")
    return out


def _r_beneficial(world: World) -> list[str]:
    out: list[str] = []
    if world.get("door").meters["open"] < THRESHOLD:
        return out
    sig = ("beneficial",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("village").meters["safe_water"] += 1
    world.get("child").memes["pride"] += 1
    out.append("__beneficial__")
    return out


CAUSAL_RULES = [Rule("alarm", _r_alarm), Rule("beneficial", _r_beneficial)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def sensible_outcomes() -> list[Outcome]:
    return [o for o in OUTCOMES.values() if o.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for chamber in CHAMBERS:
        for lever in LEVERS:
            for outcome in OUTCOMES:
                if lever == "minor_lever" or outcome != "panic":
                    combos.append((chamber, lever, outcome))
    return combos


@dataclass
class StoryParams:
    chamber: str
    lever: str
    outcome: str
    child_name: str
    child_gender: str
    guardian_name: str
    guardian_gender: str
    seed: Optional[int] = None


CHAMBERS = {
    "well_room": Chamber(
        id="well_room",
        label="the well room",
        mood="old and echoing",
        shimmer="a silver drip on the stones",
        echoes="the walls answered every footstep twice",
        lever_name="lever",
        lever_phrase="a small bronze lever",
        lever_kind="minor lever",
        lever_marks=["bronze", "small", "minor"],
    ),
    "sun_gate": Chamber(
        id="sun_gate",
        label="the sun gate",
        mood="bright but watchful",
        shimmer="one bright beam on a carved arch",
        echoes="the gate clicked whenever the wind breathed",
        lever_name="lever",
        lever_phrase="a narrow brass lever",
        lever_kind="minor lever",
        lever_marks=["brass", "narrow", "minor"],
    ),
}

LEVERS = {
    "minor_lever": "minor lever",
    "hidden_lever": "lever",
}

OUTCOMES = {
    "panic": Outcome(
        id="panic",
        kind="scary",
        sense=1,
        power=1,
        text="pulled the lever and a harmless bell rang, then the gate opened with a sigh",
        fail="pulled the lever too late to save the floodwater",
        tags={"lever", "suspense"},
    ),
    "guide": Outcome(
        id="guide",
        kind="wise",
        sense=3,
        power=3,
        text="lifted the lever and a hidden channel began to sing, guiding water to the fields",
        fail="lifted the lever, but nothing moved",
        tags={"lever", "beneficial"},
    ),
    "laugh": Outcome(
        id="laugh",
        kind="humor",
        sense=2,
        power=2,
        text="nudged the lever and a cheeky little bell tizzed three times: ting, ting, ting",
        fail="nudged the lever and only dust sneezed out",
        tags={"lever", "humor"},
    ),
}

GIRL_NAMES = ["Mira", "Ila", "Nora", "Sera", "Lina"]
BOY_NAMES = ["Oren", "Tavi", "Doro", "Ari", "Pax"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic lever storyworld.")
    ap.add_argument("--chamber", choices=CHAMBERS)
    ap.add_argument("--lever", choices=LEVERS)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def explain_rejection(chamber: Chamber, lever: str) -> str:
    return (
        f"(No story: the requested lever choice does not fit the mythic chamber. "
        f"Try the minor lever in {chamber.label}.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lever and args.lever != "minor_lever":
        raise StoryError("(No story: this world needs a minor lever; a grand lever breaks the tiny myth.)")
    combos = [c for c in valid_combos()
              if (args.chamber is None or c[0] == args.chamber)
              and (args.lever is None or c[1] == args.lever)
              and (args.outcome is None or c[2] == args.outcome)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    chamber, lever, outcome = rng.choice(sorted(combos))
    if args.chamber and args.lever == "minor_lever" and chamber not in CHAMBERS:
        raise StoryError(explain_rejection(CHAMBERS[args.chamber], args.lever))
    gender = rng.choice(["girl", "boy"])
    child_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian_gender = rng.choice(["girl", "boy"])
    guardian_name = rng.choice(GIRL_NAMES if guardian_gender == "girl" else BOY_NAMES)
    return StoryParams(
        chamber=chamber,
        lever=lever,
        outcome=outcome,
        child_name=child_name,
        child_gender=gender,
        guardian_name=guardian_name,
        guardian_gender=guardian_gender,
    )


def tell(params: StoryParams) -> World:
    world = World()
    chamber = CHAMBERS[params.chamber]
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    guardian = world.add(Entity(id=params.guardian_name, kind="character", type=params.guardian_gender, role="guardian"))
    lever = world.add(Entity(id="lever", label=chamber.lever_phrase, role="lever"))
    door = world.add(Entity(id="door", label="door", meters=defaultdict(float)))
    village = world.add(Entity(id="village", label="village", meters=defaultdict(float)))

    child.memes["wonder"] += 1
    guardian.memes["patience"] += 1

    world.say(
        f"In the old days, when {chamber.label} was young, {child.id} and {guardian.id} came by "
        f"{chamber.shimmer}. {chamber.echoes}."
    )
    world.say(
        f'Their guide pointed at {lever.label}. "It is only a {params.lever.replace("_", " ")}," '
        f"the guide said, and that made it seem both strange and harmless."
    )

    world.para()
    world.say(
        f"{child.id} leaned closer. The lever looked small enough to be a joke, yet the room grew quiet."
    )
    world.say(
        f'"Minor lever," {child.id} whispered. "Minor lever." The words repeated like a drum in a shell.'
    )

    if params.outcome == "panic":
        child.memes["fear"] += 1
        world.say(
            f"Then {child.id} pulled it, and for one breath everyone waited."
        )
        world.say(
            f"The lever answered with a bell, a sigh, and a long pause that felt bigger than the room."
        )
        door.meters["open"] += 1
        lever.meters["alarm"] += 1
        propagate(world, narrate=False)
        world.para()
        world.say(
            f"{guardian.id} laughed in surprise and clapped {child.id} on the shoulder. "
            f'The bell had been only a warning, and the warning was a kindness.'
        )
        world.say(
            f"At last the open door let the floodwater out toward the thirsty path, so the village would drink."
        )
    elif params.outcome == "guide":
        world.say(
            f"Still, the lever would not be ignored. {child.id} pulled once, then once more, then a third time, "
            f"because myths like to test patience."
        )
        world.say(
            f"At the third pull, the hidden channel woke and began to sing."
        )
        door.meters["open"] += 1
        lever.meters["alarm"] += 1
        propagate(world, narrate=False)
        world.para()
        world.say(
            f"{guardian.id} gasped, then grinned. The water ran where it should, and the dry fields grew hopeful."
        )
        world.say(
            f"It was a tiny act, yet a beneficial one: a minor lever moved, and a whole village changed its luck."
        )
    else:
        world.say(
            f"{child.id} nudged the lever, then nudged it again, because the lever seemed to enjoy suspense."
        )
        world.say(
            f"On the third nudge, it made a ridiculous tizz and flicked dust onto {child.id}'s nose."
        )
        world.say(
            f'"Again?" said {guardian.id}. "Again," said {child.id}, and the lever, being only a lever, obeyed.'
        )
        world.para()
        world.say(
            f"This time the gate opened just enough for a breeze, and everyone laughed at the serious look on the tiny lever."
        )
        lever.meters["alarm"] += 1
        propagate(world, narrate=False)

    world.facts.update(
        child=child,
        guardian=guardian,
        chamber=chamber,
        lever=lever,
        door=door,
        village=village,
        outcome=params.outcome,
        lever_kind=params.lever,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    chamber = f["chamber"]
    return [
        f'Write a short myth for a child that includes the words "beneficial", "minor", and "lever".',
        f"Tell a suspenseful, slightly funny myth about {f['child'].id} in {chamber.label} and a minor lever that changes the village.",
        f"Write a repeating, legendary story where someone says minor lever three times before the ending image arrives.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    chamber = f["chamber"]
    outcome = f["outcome"]
    answers = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {guardian.id}, who came to {chamber.label} and faced a small mythic test together."
        ),
        QAItem(
            question="What made the moment suspenseful?",
            answer=f"The lever looked tiny, but everyone had to wait to see what would happen after it was pulled. That pause made the room feel hushed and important."
        ),
        QAItem(
            question="What repeated in the story?",
            answer=f"The words minor lever were repeated like a little chant. The repetition made the scene feel both funny and solemn."
        ),
    ]
    if outcome == "guide":
        answers.append(
            QAItem(
                question="How did the story end?",
                answer="The lever opened the hidden channel and helped the fields. It was a beneficial ending because the village got water where it needed it."
            )
        )
    elif outcome == "panic":
        answers.append(
            QAItem(
                question="How did the story end?",
                answer="The lever only rang a bell and opened the gate with a sigh. The ending still helped, because the warning kept the village safe."
            )
        )
    else:
        answers.append(
            QAItem(
                question="How did the story end?",
                answer="The lever made everyone laugh and the gate opened just a little. Nothing grand happened, but the small change still gave the scene a cheerful ending."
            )
        )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lever?",
            answer="A lever is a simple tool that helps move or open something when you push or pull it."
        ),
        QAItem(
            question="What does beneficial mean?",
            answer="Beneficial means helpful. A beneficial thing makes life better in some way."
        ),
        QAItem(
            question="Why can a minor thing matter in a myth?",
            answer="A minor thing can matter because small actions can change what happens next. In a myth, even a tiny lever can lead to a big outcome."
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for cid, chamber in CHAMBERS.items():
        lines.append(asp.fact("chamber", cid))
    for lid in LEVERS:
        lines.append(asp.fact("lever", lid))
    for oid, out in OUTCOMES.items():
        lines.append(asp.fact("outcome", oid))
        lines.append(asp.fact("sense", oid, out.sense))
        lines.append(asp.fact("power", oid, out.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(O) :- outcome(O), sense(O, S), sense_min(M), S >= M.
valid(C, L, O) :- chamber(C), lever(L), outcome(O).
beneficial(O) :- outcome(O), power(O, P), P >= 2.
#show valid/3.
#show sensible/1.
#show beneficial/1.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP gate differs from Python.")
        rc = 1
    if set(asp_sensible()) == {o.id for o in sensible_outcomes()}:
        print("OK: sensible outcomes match.")
    else:
        print("MISMATCH: sensible outcomes differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def explain_response(outcome: Outcome) -> str:
    return f"(Refusing outcome '{outcome.id}': it is not sensible enough for this mythic story.)"


def generate(params: StoryParams) -> StorySample:
    if params.chamber not in CHAMBERS or params.lever not in LEVERS or params.outcome not in OUTCOMES:
        raise StoryError("(Invalid params for this world.)")
    if params.outcome and OUTCOMES[params.outcome].sense < 2:
        raise StoryError(explain_response(OUTCOMES[params.outcome]))
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible outcomes: {', '.join(asp_sensible())}")
        print(f"combos: {len(asp_valid_combos())}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(chamber="well_room", lever="minor_lever", outcome="guide", child_name="Mira", child_gender="girl", guardian_name="Oren", guardian_gender="boy"),
            StoryParams(chamber="sun_gate", lever="minor_lever", outcome="laugh", child_name="Ari", child_gender="boy", guardian_name="Lina", guardian_gender="girl"),
            StoryParams(chamber="well_room", lever="minor_lever", outcome="panic", child_name="Nora", child_gender="girl", guardian_name="Doro", guardian_gender="boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
