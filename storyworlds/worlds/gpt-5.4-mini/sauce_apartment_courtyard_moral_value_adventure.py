#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sauce_apartment_courtyard_moral_value_adventure.py
===================================================================================

A standalone tiny storyworld for an apartment-courtyard adventure about sauce,
a moral choice, and a small ending that proves something changed.

The core pattern is:
- a child goes on a courtyard adventure,
- they discover a tempting jar of sauce or sauce-related plan,
- a moral value beat pulls them toward honesty / kindness / responsibility,
- a caretaker or neighbor helps resolve the situation,
- the ending image shows the moral choice made the day better.

This script follows the shared storyworld contract:
- imports storyworlds/results.py eagerly for QAItem, StoryError, StorySample
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate plus an inline ASP twin
- produces world-driven prose and QA grounded in simulated state
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
MORAL_MIN = 1.0


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
class Adventure:
    id: str
    scene: str
    goal: str
    route: str
    danger: str
    treasure: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SauceItem:
    id: str
    label: str
    phrase: str
    kind: str
    spillable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralChoice:
    id: str
    value: str
    prompt: str
    good: str
    bad: str
    lesson: str
    power: int
    sense: int
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
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                out.extend(r for r in res if not r.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    sauce = world.get("sauce")
    if kid.meters["sauce"] < THRESHOLD:
        return out
    sig = ("spill", kid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sauce.meters["messy"] += 1
    kid.memes["worry"] += 1
    out.append("__spill__")
    return out


def _r_moral_tug(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    if kid.memes["temptation"] < THRESHOLD or kid.memes["value"] < MORAL_MIN:
        return out
    sig = ("tug", kid.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["resolve"] += 1
    out.append("__tug__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("sauce").meters["returned"] < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("courtyard").meters["peace"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("moral_tug", _r_moral_tug), Rule("calm", _r_calm)]


def reasonableness_gate(adventure: Adventure, sauce: SauceItem, choice: MoralChoice) -> bool:
    return sauce.spillable and choice.sense >= 1 and choice.power >= 1 and adventure.id in ADVENTURES


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for adv_id in ADVENTURES:
        for sauce_id, sauce in SAUCES.items():
            for choice_id, choice in CHOICES.items():
                if reasonableness_gate(ADVENTURES[adv_id], sauce, choice):
                    combos.append((adv_id, sauce_id, choice_id))
    return combos


def predict(world: World, sauce: SauceItem) -> dict:
    sim = world.copy()
    sim.get("kid").meters["sauce"] += 1
    propagate(sim, narrate=False)
    return {
        "spill": sim.get("sauce").meters["messy"] >= THRESHOLD,
        "peace": sim.get("courtyard").meters["peace"],
    }


def setup(world: World, adv: Adventure, kid: Entity, friend: Entity, adult: Entity, sauce: Entity) -> None:
    kid.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the apartment courtyard, {kid.id} and {friend.id} turned the day into {adv.scene}. "
        f"{adv.goal} waited beyond the flower pots, and every balcony looked like part of the route."
    )
    world.say(
        f'They whispered, "{adv.route}," because it sounded like the beginning of a real adventure.'
    )
    world.say(
        f"Near the benches, they found {sauce.label} tucked beside a snack basket."
    )


def tempt(world: World, kid: Entity, sauce: Entity, choice: MoralChoice) -> None:
    kid.memes["temptation"] += 1
    world.say(
        f'{kid.id} grinned. "I could use the {sauce.label} for our quest," {kid.pronoun()} said. '
        f'{choice.prompt}'
    )


def warn(world: World, friend: Entity, kid: Entity, choice: MoralChoice, sauce: Entity, adult: Entity) -> None:
    pred = predict(world, sauce)
    friend.memes["value"] += 1
    world.facts["predicted_spill"] = pred["spill"]
    world.say(
        f"{friend.id} shook {friend.pronoun('possessive')} head. "
        f'"{choice.value} matters," {friend.pronoun()} said. '
        f'"If we use it the wrong way, {choice.bad}."'
    )
    world.say(
        f"They could already imagine {adult.label_word} having to clean the sticky mess."
    )


def do_bad(world: World, kid: Entity, sauce: Entity, choice: MoralChoice) -> None:
    kid.meters["sauce"] += 1
    kid.memes["reckless"] += 1
    world.say(
        f"{kid.id} reached for the {sauce.label} anyway, and a smear splashed onto the courtyard stones."
    )
    propagate(world, narrate=False)
    world.say(
        f"The sweet smell drifted under the bikes, and the trail of sauce made the path slippery."
    )


def intervene(world: World, adult: Entity, sauce: Entity, choice: MoralChoice) -> None:
    sauce.meters["returned"] += 1
    sauce.meters["messy"] = 0
    world.get("courtyard").meters["peace"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came over with a cloth and smiled. "
        f'In a calm voice, {adult.pronoun()} helped them fix the spill and said, '
        f'"{choice.lesson}"'
    )


def finish(world: World, kid: Entity, friend: Entity, adult: Entity, adv: Adventure, sauce: Entity) -> None:
    kid.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"For a moment, everyone was quiet."
    )
    world.say(
        f"Then {kid.id} carried the {sauce.label} back where it belonged, and the courtyard felt open and bright again."
    )
    world.say(
        f"At the end, {kid.id} and {friend.id} raced past the fountain, "
        f"{adv.ending}, with {adult.label_word} watching proudly from the doorway."
    )


def tell(adv: Adventure, sauce: SauceItem, choice: MoralChoice, kid_name: str = "Mia",
         kid_gender: str = "girl", friend_name: str = "Noah", friend_gender: str = "boy",
         adult_type: str = "mother", take_bad_turn: bool = True) -> World:
    world = World()
    kid = world.add(Entity("kid", kind="character", type=kid_gender, role="hero", traits=["curious"]))
    friend = world.add(Entity("friend", kind="character", type=friend_gender, role="companion", traits=["careful"]))
    adult = world.add(Entity("adult", kind="character", type=adult_type, role="caretaker", label="the grown-up"))
    sauce_ent = world.add(Entity("sauce", kind="thing", type="jar", label=sauce.label))
    courtyard = world.add(Entity("courtyard", kind="place", type="courtyard", label="the courtyard"))
    kid.id = kid_name
    friend.id = friend_name

    kid.memes["value"] = 1.0
    world.facts["adventure"] = adv
    world.facts["sauce_cfg"] = sauce
    world.facts["choice"] = choice
    world.facts["take_bad_turn"] = take_bad_turn

    setup(world, adv, kid, friend, adult, sauce_ent)
    world.para()
    tempt(world, kid, sauce_ent, choice)
    warn(world, friend, kid, choice, sauce_ent, adult)
    if take_bad_turn:
        do_bad(world, kid, sauce_ent, choice)
    world.para()
    intervene(world, adult, sauce_ent, choice)
    finish(world, kid, friend, adult, adv, sauce_ent)

    world.facts.update(kid=kid, friend=friend, adult=adult, sauce=sauce_ent, courtyard=courtyard)
    return world


ADVENTURES = {
    "fountain": Adventure("fountain", "a secret fountain expedition", "the fountain gate", "follow the tiled path", "the sticky spill", "a shiny blue marker", "their route ended safely", {"courtyard"}),
    "parcel": Adventure("parcel", "a treasure hunt among the flower pots", "the far bench", "tiptoe between the planters", "the sauce smear", "a hidden ribbon", "their map stayed dry", {"courtyard"}),
    "elevator": Adventure("elevator", "a rescue mission to the courtyard gate", "the mailbox corner", "cross like spies", "the slippery steps", "a silver key", "the little mission worked", {"courtyard"}),
}

SAUCES = {
    "tomato": SauceItem("tomato", "tomato sauce", "a small jar of tomato sauce", "sauce", True, {"sauce"}),
    "sweet": SauceItem("sweet", "sweet sauce", "a little cup of sweet sauce", "sauce", True, {"sauce"}),
    "green": SauceItem("green", "herb sauce", "a jar of green herb sauce", "sauce", True, {"sauce"}),
}

CHOICES = {
    "honesty": MoralChoice("honesty", "honesty", "It looked tempting, but the honest thing would be to ask first.", "the grown-up would not know where it went", "the sauce would go missing", "honesty is braver than hiding", 2, 2, {"moral"}),
    "responsibility": MoralChoice("responsibility", "responsibility", "It was tempting to leave it there, but responsible kids put things back.", "someone else might slip later", "the courtyard would stay messy", "responsibility keeps places safe", 2, 2, {"moral"}),
    "kindness": MoralChoice("kindness", "kindness", "It would be kind to help clean it instead of laughing.", "the mess would hurt someone else's day", "the sticky spot would stay for others", "kindness helps everyone", 2, 2, {"moral"}),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Theo", "Finn", "Leo", "Ben", "Max"]


@dataclass
class StoryParams:
    adventure: str
    sauce: str
    moral: str
    kid_name: str
    kid_gender: str
    friend_name: str
    friend_gender: str
    adult: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    adv = f["adventure"]
    sauce = f["sauce_cfg"]
    choice = f["choice"]
    kid = f["kid"]
    return [
        f'Write an apartment-courtyard adventure story for a young child that includes the word "{sauce.label}" and teaches {choice.value}.',
        f"Tell a small adventure where {kid.id} finds {sauce.phrase} in the courtyard, makes a risky choice, and learns {choice.lesson}.",
        f"Write a gentle story in a courtyard where a child wants to take sauce on a quest, but kindness and responsibility lead to a better ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, friend, adult = f["kid"], f["friend"], f["adult"]
    sauce = f["sauce_cfg"]
    choice = f["choice"]
    adv = f["adventure"]
    qa = [
        ("Who is the story about?",
         f"It is about {kid.id} and {friend.id}, two children on a courtyard adventure, with {adult.label_word} nearby to help."),
        ("What did the children find?",
         f"They found {sauce.phrase} near the benches in the apartment courtyard. It became the tempting thing at the center of their quest."),
        ("What did {0} want to do with the sauce?".format(kid.id),
         f"{kid.id} wanted to use the {sauce.label} for the adventure, but that was the wrong choice. {choice.value.capitalize()} was the better idea because it kept the courtyard safe and fair."),
    ]
    if world.facts.get("take_bad_turn"):
        qa.append((
            "Why did the grown-up help them clean up?",
            f"Because the sauce spilled and made the stones sticky and slippery. {adult.label_word.capitalize()} helped so the courtyard would be safe again and the children could learn from the mistake."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with {kid.id} carrying the {sauce.label} back where it belonged and the courtyard feeling bright again. The adventure continued, but now it was a better, more responsible adventure."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["sauce_cfg"].tags) | set(f["choice"].tags) | {"courtyard"}
    out = []
    KNOWLEDGE = {
        "sauce": [("What is sauce?",
                  "Sauce is a tasty liquid or thick topping that people add to food. It can also make a sticky mess if it spills.")],
        "courtyard": [("What is an apartment courtyard?",
                       "An apartment courtyard is an open shared space inside or beside an apartment building where people can walk, play, and rest.")],
        "honesty": [("What does honesty mean?",
                     "Honesty means telling the truth and not hiding what really happened. It helps people trust each other.")],
        "responsibility": [("What does responsibility mean?",
                            "Responsibility means taking care of your things and fixing mistakes when you can. It helps keep places safe and neat.")],
        "kindness": [("What does kindness mean?",
                      "Kindness means helping others, being gentle, and thinking about how your actions affect them.")],
    }
    for key in ["courtyard", "sauce", "honesty", "responsibility", "kindness"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("fountain", "tomato", "honesty", "Mia", "girl", "Noah", "boy", "mother"),
    StoryParams("parcel", "sweet", "responsibility", "Leo", "boy", "Ava", "girl", "father"),
    StoryParams("elevator", "green", "kindness", "Nora", "girl", "Theo", "boy", "mother"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not fit the courtyard adventure or moral-value constraint.)"


def valid_choice(choice: MoralChoice) -> bool:
    return choice.sense >= 1 and choice.power >= 1


def asp_facts() -> str:
    import asp
    lines = []
    for aid in ADVENTURES:
        lines.append(asp.fact("adventure", aid))
    for sid, s in SAUCES.items():
        lines.append(asp.fact("sauce", sid))
        if s.spillable:
            lines.append(asp.fact("spillable", sid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        lines.append(asp.fact("power", cid, c.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(A,S,C) :- adventure(A), sauce(S), spillable(S), choice(C), sense(C,M), M >= 1.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small apartment-courtyard adventure about sauce and moral choice."
    )
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--sauce", choices=SAUCES)
    ap.add_argument("--moral", choices=CHOICES)
    ap.add_argument("--kid-name")
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    combos = [(a, s, c) for a, s, c in valid_combos()
              if (args.adventure is None or a == args.adventure)
              and (args.sauce is None or s == args.sauce)
              and (args.moral is None or c == args.moral)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    adv, sauce, moral = rng.choice(sorted(combos))
    kid_gender = args.kid_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if kid_gender == "girl" else "girl")
    kid_name = args.kid_name or rng.choice(GIRL_NAMES if kid_gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != kid_name])
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(adv, sauce, moral, kid_name, kid_gender, friend_name, friend_gender, adult)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ADVENTURES[params.adventure],
        SAUCES[params.sauce],
        CHOICES[params.moral],
        params.kid_name,
        params.kid_gender,
        params.friend_name,
        params.friend_gender,
        params.adult,
    )
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid (adventure, sauce, moral) combos:")
        for adv, sauce, moral in asp_valid_combos():
            print(f"  {adv:10} {sauce:8} {moral}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.kid_name}: {p.adventure} with {p.sauce} ({p.moral})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
