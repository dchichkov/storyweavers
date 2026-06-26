#!/usr/bin/env python3
"""
storyworlds/worlds/faring_nine_dialogue_bad_ending_rhyming_story.py
====================================================================

A small standalone story world for a rhyming, dialogue-heavy tale with a bad ending.

Seed idea:
- "faring"
- "nine"
- Dialogue
- Bad Ending
- Style: Rhyming Story

Premise:
A child and a helper are carrying nine delicate things through a windy place.
The helper worries, the child tries anyway, and the wind wins.
The ending is sad but complete: the nine delicate things do not all make it home.

The world model tracks:
- physical meters: wind, carry, lost, torn, soaked
- emotional memes: worry, brave, upset, regret, care

The generated story is not a frozen paragraph; it follows simulated state:
setup -> warning -> reckless choice -> loss -> final image.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    windy: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False
    risky: bool = True


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.weather = "windy" if setting.windy else "calm"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        chunk: list[str] = []
        for line in self.lines:
            if line == "":
                if chunk:
                    out.append(" ".join(chunk))
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            out.append(" ".join(chunk))
        return "\n\n".join(out)


SETTINGS = {
    "fair": Setting(place="the fair", windy=True, affords={"carry"}),
    "pier": Setting(place="the pier", windy=True, affords={"carry"}),
    "hill": Setting(place="the hill", windy=True, affords={"carry"}),
    "porch": Setting(place="the porch", windy=False, affords={"carry"}),
}

ACTIONS = {
    "carry": Activity(
        id="carry",
        verb="carry the nine lanterns",
        gerund="carrying the nine lanterns",
        rush="run ahead with the lanterns",
        risk="the wind could snatch them away",
        weather="windy",
        zone={"hands", "air"},
        keyword="nine",
        tags={"wind", "light", "nine"},
    ),
}

PRIZES = {
    "lanterns": Prize(
        label="lanterns",
        phrase="nine little lanterns",
        region="hands",
        plural=True,
        risky=True,
    ),
    "cups": Prize(
        label="cups",
        phrase="nine paper cups",
        region="hands",
        plural=True,
        risky=True,
    ),
}

HELPERS = ["mother", "father", "grandma", "grandpa"]
NAMES = {
    "girl": ["Mina", "Lily", "Nora", "Tess"],
    "boy": ["Finn", "Leo", "Milo", "Sam"],
}
TRAITS = ["brave", "busy", "proud", "quick", "small", "cheery"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.risky and prize.region in activity.zone


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_name, s in SETTINGS.items():
        for a_name, a in ACTIONS.items():
            for p_name, p in PRIZES.items():
                if s.windy and prize_at_risk(a, p):
                    combos.append((s_name, a_name, p_name))
                elif not s.windy and prize_at_risk(a, p):
                    combos.append((s_name, a_name, p_name))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world with dialogue and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        if not prize_at_risk(ACTIONS[args.activity], PRIZES[args.prize]):
            raise StoryError("That prize is not in danger from that activity.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    setting, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, activity=activity, prize=prize, name=name, gender=gender, helper=helper)


def _meter_add(ent: Entity, key: str, val: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + val


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    act = ACTIONS[params.activity]
    prize_cfg = PRIZES[params.prize]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper_type = params.helper
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_type))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        plural=prize_cfg.plural,
        owner=hero.id,
        caretaker=helper.id,
    ))

    hero.memes["care"] = 1.0
    helper.memes["care"] = 1.0
    hero.memes["brave"] = 1.0
    world.facts.update(hero=hero, helper=helper, prize=prize, act=act, setting=setting)

    world.say(f"{hero.id} went out to the {setting.place}, with a skip and a sway.")
    world.say(f"{hero.pronoun().capitalize()} was {act.gerund}, in a bright little way.")
    world.say(f"'{helper_type.capitalize()}, am I {('faring')} okay?' {hero.id} asked with a grin.")
    world.say(f"'{NotImplemented.__name__ if False else 'I worry the wind will win'},' {helper_type} said, 'for there are nine to bring in.'")
    world.para()

    world.say(f"The {helper_type} pointed up high and said, 'See how the clouds race by?'")
    world.say(f"'If you run too fast with the {prize.label}, the gusts may sigh.'")
    _meter_add(helper, "worry")
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1.0
    world.say(f"'{I_like := 'I know'},' said {hero.id}, 'but I can be quick as a kite.'")
    world.say(f"'{I_like},' the helper replied, 'but quick can be not quite right.'")
    world.para()

    _meter_add(hero, "carry")
    _meter_add(world.get("prize"), "carry")
    world.say(f"So {hero.id} lifted the {prize.phrase}; {hero.pronoun()} did not take the long, safe road.")
    world.say(f"{hero.pronoun().capitalize()} dashed toward the gate as the west wind growled and rode.")
    _meter_add(hero, "wind")
    _meter_add(world.get("prize"), "wind")
    hero.memes["brave"] = hero.memes.get("brave", 0.0) + 1.0
    world.para()

    world.say(f"Then came a snap and a flutter; the string gave a sore little twist.")
    world.say(f"The wind stole three, then four, then two; the nine were no longer in the list.")
    _meter_add(world.get("prize"), "lost", 1.0)
    _meter_add(world.get("prize"), "torn", 1.0)
    hero.memes["upset"] = 1.0
    hero.memes["regret"] = 1.0
    helper.memes["upset"] = 1.0
    helper.memes["regret"] = 1.0
    world.para()

    world.say(f"'{Oh_no := 'Oh no'},' said {hero.id}, 'the sky took more than I could hold.'")
    world.say(f"'{I_told_you := 'I told you'},' said the helper, 'the wind can be bold and cold.'")
    world.say(f"{hero.id} looked up at the empty string and felt very small indeed.")
    world.say(f"The last lost lantern blinked in the dark, then vanished from sight and speed.")
    world.facts["lost_count"] = 9
    world.facts["bad_ending"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    act: Activity = f["act"]  # type: ignore[assignment]
    prize: Entity = f["prize"]  # type: ignore[assignment]
    return [
        f"Write a rhyming story for a child about {hero.id}, {helper.type}, and {prize.phrase}.",
        f"Tell a dialogue-heavy story where {hero.id} tries to {act.verb} but the wind causes a bad ending.",
        f"Write a short, sad rhyming story that includes the word 'faring' and the number nine.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    prize: Entity = f["prize"]  # type: ignore[assignment]
    act: Activity = f["act"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was trying to carry the nine lanterns at the {world.setting.place}?",
            answer=f"{hero.id} was trying to carry the nine lanterns, while {helper.type} watched and worried."
        ),
        QAItem(
            question=f"What did {helper.type} warn about before {hero.id} rushed ahead?",
            answer=f"{helper.type.capitalize()} warned that the wind might snatch the {prize.label} away."
        ),
        QAItem(
            question=f"What went wrong when {hero.id} tried to {act.verb}?",
            answer="The wind tore the string and carried the lanterns away, so the story ended sadly."
        ),
        QAItem(
            question=f"How was {hero.id} faring at the end?",
            answer=f"{hero.id} was faring poorly at the end, because the nine were lost and the day turned sad."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does wind do on a very windy day?",
            answer="Wind is moving air. On a windy day, it can push, tug, and blow light things around."
        ),
        QAItem(
            question="Why are lanterns delicate?",
            answer="Lanterns can be delicate because their paper or thin parts can tear or break when they are handled roughly."
        ),
        QAItem(
            question="What does the number nine mean?",
            answer="Nine is one more than eight and one less than ten."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


ASP_RULES = r"""
setting(fair). setting(pier). setting(hill). setting(porch).
activity(carry).
prize(lanterns). prize(cups).
windy(fair). windy(pier). windy(hill).
calm(porch).

risk(carry, lanterns).
risk(carry, cups).

valid(S, A, P) :- setting(S), activity(A), prize(P), windy(S), risk(A, P).
valid(S, A, P) :- setting(S), activity(A), prize(P), calm(S), risk(A, P).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        if SETTINGS[s].windy:
            lines.append(asp.fact("windy", s))
        else:
            lines.append(asp.fact("calm", s))
    for a in ACTIONS:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
        lines.append(asp.fact("risk", "carry", p))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(setting="fair", activity="carry", prize="lanterns", name="Mina", gender="girl", helper="mother"),
    StoryParams(setting="pier", activity="carry", prize="cups", name="Finn", gender="boy", helper="father"),
    StoryParams(setting="hill", activity="carry", prize="lanterns", name="Nora", gender="girl", helper="grandma"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
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
            except StoryError as e:
                print(e)
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
