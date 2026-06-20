#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/attic_shepherd_grain_splash_pad_bravery_tall.py
================================================================================

A standalone story world for a tall-tale style, child-facing simulation set at a
splash pad. The seed words are folded into a small, coherent domain: an attic
stores a shepherd's grain, a windy prank spills it into the splash pad, and
bravery helps turn the mishap into a memorable rescue.

The story beats are world-driven:
- premise: a tall-tale day at the splash pad, with an attic, a shepherd, and grain
- tension: the grain is at risk of getting soaked and lost
- turn: a brave child or helper chooses a sensible fix
- resolution: the grain is saved, or the story ends with a meaningful recovery

This file is self-contained and uses only the standard library plus the shared
result containers in storyworlds/results.py.
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
        female = {"girl", "mother", "mom", "woman", "shepherdess"}
        male = {"boy", "father", "dad", "man", "shepherd"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"shepherd": "shepherd", "shepherdess": "shepherdess", "child": "child"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    indoors: bool = False


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    where: str
    spill_word: str
    makes_mess: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    vulnerable: str
    region: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    grain = world.entities.get("grain")
    if grain and grain.meters["soaked"] >= THRESHOLD:
        sig = ("soak", grain.id)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in world.entities.values():
                if e.role in {"shepherd", "helper"}:
                    e.memes["worry"] += 1
            out.append("__soaked__")
    return out


CAUSAL_RULES = [Rule("soak", "physical", _r_soak)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for sid in SETTINGS:
        for src_id, src in SOURCES.items():
            for pid, prize in PRIZES.items():
                if src.makes_mess and prize.vulnerable == "grain":
                    combos.append((sid, src_id, pid))
    return combos


@dataclass
class StoryParams:
    setting: str
    source: str
    prize: str
    response: str
    child: str
    child_gender: str
    shepherd: str
    shepherd_gender: str
    helper: str
    helper_gender: str
    bravery: int = 6
    delay: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "splash_pad": Setting(
        "splash_pad",
        "the splash pad",
        "The water danced up from the tiles like a hundred silver fiddles.",
        indoors=False,
    ),
    "park_splash_pad": Setting(
        "park_splash_pad",
        "the city splash pad",
        "The fountains spun and sparkled, and the whole place rang with laughter.",
        indoors=False,
    ),
}

SOURCES = {
    "attic_gust": Source(
        "attic_gust",
        "attic door",
        "the attic door under the eaves",
        "from the attic",
        "a long grain sack",
        True,
        {"attic", "grain"},
    ),
    "grain_bag": Source(
        "grain_bag",
        "grain sack",
        "a burlap grain sack",
        "from the attic loft",
        "a trail of grain",
        True,
        {"grain"},
    ),
}

PRIZES = {
    "grain": Prize(
        "grain",
        "grain",
        "the shepherd's grain",
        "grain",
        "grain",
        {"grain", "attic"},
    ),
    "feed": Prize(
        "feed",
        "feed sack",
        "the sheep feed",
        "grain",
        "bag",
        {"grain"},
    ),
}

RESPONSES = {
    "scoop": Response(
        "scoop",
        3,
        4,
        "scooped the grain into a dry bucket and carried it up under a canvas awning",
        "tried to scoop the grain, but the water had already swirled through it",
        "scooped the grain into a dry bucket and saved it",
        {"bravery", "grain"},
    ),
    "cover": Response(
        "cover",
        3,
        3,
        "covered the sack with a big tarp and tucked it under the bench",
        "covered the sack, but the splash still soaked the grain through",
        "covered the sack with a tarp and tucked it safely away",
        {"bravery", "grain"},
    ),
    "roll": Response(
        "roll",
        2,
        2,
        "rolled the sack onto a dry wagon and hurried it out of the spray",
        "rolled the sack, but the water had already won the race",
        "rolled the sack out of the spray and kept it dry",
        {"bravery", "grain"},
    ),
    "bucket": Response(
        "bucket",
        1,
        1,
        "used a bucket, but it was too small and too late",
        "used a bucket, but it could not outpace the splash",
        "used a bucket",
        {"grain"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Elsie", "June", "Ada", "Willa", "Ruby"]
BOY_NAMES = ["Owen", "Finn", "Ezra", "Theo", "Miles", "Ben", "Jasper", "Hugo"]


def bravery_gate(bravery: int) -> bool:
    return bravery >= 5


def could_soak(source: Source, prize: Prize) -> bool:
    return source.makes_mess and prize.vulnerable == "grain"


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= (2 + delay)


def outcome_of(params: StoryParams) -> str:
    if not bravery_gate(params.bravery):
        return "timid"
    return "contained" if is_contained(RESPONSES[params.response], params.delay) else "soaked"


def tell(
    setting: Setting,
    source: Source,
    prize: Prize,
    response: Response,
    child_name: str = "Lina",
    child_gender: str = "girl",
    shepherd_name: str = "Hugo",
    shepherd_gender: str = "boy",
    helper_name: str = "Mira",
    helper_gender: str = "girl",
    bravery: int = 6,
    delay: int = 0,
) -> World:
    world = World(setting)
    child = world.add(Entity(child_name, "character", child_gender, role="child", traits=["brave"]))
    shepherd = world.add(Entity(shepherd_name, "character", shepherd_gender, role="shepherd", traits=["steady"]))
    helper = world.add(Entity(helper_name, "character", helper_gender, role="helper", traits=["quick"]))
    attic = world.add(Entity("attic", "place", "attic", label="the attic"))
    pad = world.add(Entity("pad", "place", "place", label=setting.place))
    grain = world.add(Entity("grain", "thing", "grain", label=prize.label))
    child.memes["bravery"] = float(bravery)
    shepherd.memes["care"] = 5
    helper.memes["helpfulness"] = 5
    world.facts.update(setting=setting, source=source, prize=prize, response=response)

    world.say(
        f"On a bright day at {setting.place}, {child_name} went with {shepherd_name} the shepherd and {helper_name} to mind the grain."
    )
    world.say(
        f"Above the laughter and the sprays, there was an attic door where {source.phrase} had been kept for safekeeping."
    )
    world.say(
        f"{setting.detail} {child_name} spotted {prize.phrase} and said the sight of it made the day feel like a tall tale."
    )

    world.para()
    world.say(
        f"Then a gust from {source.where} caught the sack, and {source.spill_word} spilled down by the splash pad."
    )
    grain.meters["soaked"] += 1
    child.memes["alarm"] += 1
    shepherd.memes["alarm"] += 1
    propagate(world, narrate=False)

    if not bravery_gate(bravery):
        world.say(
            f"{child_name} froze, but {shepherd_name} put a hand on {child_name}'s shoulder and whispered that bravery begins by calling for help."
        )
        world.say(
            f"They ran for a dry basket together, yet the grain had already washed away in the spray, and the shepherd had to gather what little remained."
        )
        world.para()
        world.say(
            f"In the end, the splash pad still glittered, but the shepherd's heart was heavy, and {child_name} learned that a brave mind must speak up before trouble grows."
        )
        outcome = "timid"
    else:
        world.say(
            f"{child_name} did not flinch. With brave feet and a steady voice, {child_name} called, 'We can save it!'"
        )
        if is_contained(response, delay):
            body = response.text
            world.say(
                f"{shepherd_name} nodded like a barn door in a storm and {body}."
            )
            world.say(
                f"Before the splash could claim the whole sack, the grain stayed dry enough to be counted and carried back to the attic loft."
            )
            world.para()
            world.say(
                f"By sunset the splash pad still sang, but the shepherd's grain sat safe again in the attic, and everyone told the tale with wide eyes and happy sighs."
            )
            outcome = "contained"
        else:
            body = response.fail
            world.say(
                f"{helper_name} tried to help, but {body}."
            )
            world.say(
                f"The grain took on water, and the shepherd had to scoop up what could be saved while the rest drifted away like lost cornflakes on a river."
            )
            world.para()
            world.say(
                f"So the day ended with wet sleeves and a stern lesson: bravery is fine, but a brave heart still needs a strong plan."
            )
            outcome = "soaked"

    world.facts.update(
        child=child,
        shepherd=shepherd,
        helper=helper,
        attic=attic,
        pad=pad,
        grain=grain,
        outcome=outcome,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"].id
    shepherd = f["shepherd"].id
    return [
        f'Write a tall tale for a young child that includes the words "attic", "shepherd", and "grain" at the splash pad.',
        f"Tell a brave splash-pad story where {child} helps {shepherd} save grain that spilled from the attic.",
        f"Write a child-friendly tall tale about bravery, an attic, a shepherd, and grain getting splashed at a water play place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    shepherd = f["shepherd"]
    helper = f["helper"]
    outcome = f["outcome"]
    qa = [
        QAItem(
            question="Who was trying to save the grain?",
            answer=f"{child.id} was trying to help {shepherd.id} save the grain. {child.id} used bravery instead of giving up when the spill started."
        ),
        QAItem(
            question="Why was the shepherd worried?",
            answer="The grain had spilled near the splash pad, where the water could soak it fast. The shepherd knew wet grain would be hard to gather up again."
        ),
    ]
    if outcome == "contained":
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended safely, with the grain carried back to the attic and kept dry enough to use later. The splash pad still sparkled, but the shepherd's grain was saved."
        ))
    elif outcome == "soaked":
        qa.append(QAItem(
            question="How did the story end?",
            answer="It ended with some grain saved and some grain lost to the water. The brave helpers did their best, but the splash had already done too much damage."
        ))
    else:
        qa.append(QAItem(
            question="How did bravery matter in the story?",
            answer=f"{child.id} wanted to act, but fear slowed the rescue. The shepherd taught that bravery starts by asking for help right away."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an attic?",
            answer="An attic is a room near the roof of a house. People often keep stored things there."
        ),
        QAItem(
            question="What is a shepherd?",
            answer="A shepherd is a person who takes care of sheep. A shepherd keeps the flock together and looks after what it needs."
        ),
        QAItem(
            question="What is grain?",
            answer="Grain is a tiny seed people and animals can eat. It must be kept dry so it does not spoil."
        ),
        QAItem(
            question="What is a splash pad?",
            answer="A splash pad is a play place with water sprays and fountains. Children use it to cool off and play safely."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel scared. It can mean speaking up, asking for help, or trying again."
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("splash_pad", "attic_gust", "grain", "scoop", "Lina", "girl", "Hugo", "boy", "Mira", "girl", bravery=7, delay=0),
    StoryParams("park_splash_pad", "grain_bag", "feed", "cover", "Owen", "boy", "Mila", "girl", "Jasper", "boy", bravery=6, delay=1),
]


def explain_rejection(source: Source, prize: Prize) -> str:
    return "(No story: this setup does not create a real grain spill at the splash pad.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


ASP_RULES = r"""
spill(S) :- source(S), makes_mess(S).
at_risk(P) :- prize(P), vulnerable(P, grain).
valid(Set, S, P) :- setting(Set), source(S), prize(P), spill(S), at_risk(P).
brave(C) :- bravery(C, B), B >= 5.
contained(R) :- response(R), power(R, P), delay(D), P >= 2 + D.
outcome(told) :- not brave(_).
outcome(contained) :- brave(_), contained(_).
outcome(lost) :- brave(_), not contained(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SOURCES.items():
        lines.append(asp.fact("source", sid))
        if s.makes_mess:
            lines.append(asp.fact("makes_mess", sid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("vulnerable", pid, p.vulnerable))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("bravery", params.child, params.bravery),
        asp.fact("delay", params.delay),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, source=None, prize=None, response=None, child=None,
            child_gender=None, shepherd=None, shepherd_gender=None, helper=None,
            helper_gender=None, bravery=None, delay=None, seed=None
        ), random.Random(777)))
        _ = sample.story
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {exc}")
    cases = [p for p in CURATED]
    for s in range(20):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale splash-pad story world with bravery, attic, shepherd, and grain.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--shepherd")
    ap.add_argument("--shepherd-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--bravery", type=int, choices=list(range(0, 11)))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.source is None or c[1] == args.source)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, source, prize = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    shepherd_gender = args.shepherd_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    shepherd = args.shepherd or rng.choice(GIRL_NAMES if shepherd_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    bravery = args.bravery if args.bravery is not None else rng.randint(4, 9)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, source, prize, response, child, child_gender, shepherd, shepherd_gender, helper, helper_gender, bravery, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SOURCES[params.source],
        PRIZES[params.prize],
        RESPONSES[params.response],
        params.child,
        params.child_gender,
        params.shepherd,
        params.shepherd_gender,
        params.helper,
        params.helper_gender,
        params.bravery,
        params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in [(x.question, x.answer) for x in story_qa(world)]],
        world_qa=[QAItem(question=q, answer=a) for q, a in [(x.question, x.answer) for x in world_knowledge_qa(world)]],
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
