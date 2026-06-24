#!/usr/bin/env python3
"""
storyworlds/worlds/reindeer_delicious_minimize_twist_cautionary_folk_tale.py
=============================================================================

A small standalone story world in the folk-tale mode: a hungry reindeer, a
delicious treat, a plan to minimize waste, and a cautionary twist. The world is
typed, state-driven, and emits prose that changes with the simulated outcome.

Seeded premise:
- A reindeer wants something delicious.
- A cautious helper suggests minimizing a risky shortcut.
- A twist turns a simple errand into a lesson about sharing, patience, and care.

This script follows the Storyweavers contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Small world model
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fullness": 0.0, "risk": 0.0, "distance": 0.0}
        if not self.memes:
            self.memes = {"hunger": 0.0, "joy": 0.0, "worry": 0.0, "care": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return copy.deepcopy(self)


@dataclass
class Rule:
    name: str
    apply: callable


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def _rule_spill(world: World) -> bool:
    sweet = world.get("treat")
    if sweet.meters["spilled"] < THRESHOLD:
        return False
    sig = ("spill",)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    bowl = world.get("bowl")
    bowl.meters["empty"] = 1.0
    world.get("scene").memes["worry"] += 1
    world.get("reindeer").memes["worry"] += 1
    return True


def _rule_share(world: World) -> bool:
    if world.get("reindeer").memes["care"] < THRESHOLD:
        return False
    sig = ("share",)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.get("reindeer").memes["joy"] += 1
    world.get("child").memes["joy"] += 1
    return True


CAUSAL_RULES = [Rule("spill", _rule_spill), Rule("share", _rule_share)]


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    id: str
    place: str
    song: str
    weather: str
    shelter: str


@dataclass
class Treat:
    id: str
    name: str
    adjective: str
    place: str
    sweet_need: str


@dataclass
class Twist:
    id: str
    reveal: str
    lesson: str
    change: str


@dataclass
class Caution:
    id: str
    warning: str
    safer_way: str
    reason: str


SETTINGS = {
    "pine_clearing": Setting(
        id="pine_clearing",
        place="a pine clearing beside a tiny stream",
        song="the pines sang softly in the wind",
        weather="cold and bright",
        shelter="a little hut of logs",
    ),
    "snow_path": Setting(
        id="snow_path",
        place="a snowy path under silver moonlight",
        song="the snow glittered like spilled sugar",
        weather="quiet and blue",
        shelter="a warm cottage at the hill",
    ),
}

TREATS = {
    "berry_tart": Treat(
        id="berry_tart",
        name="berry tart",
        adjective="delicious",
        place="on a blue plate",
        sweet_need="something sweet to fill the hungry belly",
    ),
    "honey_bread": Treat(
        id="honey_bread",
        name="honey bread",
        adjective="delicious",
        place="in a cloth wrap by the basket",
        sweet_need="a warm bite after the long walk",
    ),
    "apple_cake": Treat(
        id="apple_cake",
        name="apple cake",
        adjective="delicious",
        place="on the sill by the window",
        sweet_need="a soft snack for sharing",
    ),
}

TWISTS = {
    "lost_tail": Twist(
        id="lost_tail",
        reveal="The reindeer's little bell had fallen into the snow, and the shiny trail was not treasure at all.",
        lesson="A careful look can save a long search.",
        change="the hunt became a lesson in noticing small things",
    ),
    "hungry_helper": Twist(
        id="hungry_helper",
        reveal="A hungry fox had been sniffing the crumbs, hoping to sneak the treat away.",
        lesson="Sharing early can keep a good thing from turning into trouble.",
        change="the feast became a story about watching over what mattered",
    ),
    "gift_returned": Twist(
        id="gift_returned",
        reveal="The treat had been meant for a tired neighbor, and the reindeer had nearly eaten it first.",
        lesson="A gift is sweeter when it reaches the right hands.",
        change="the answer changed from grabbing to giving",
    ),
}

CAUTIONS = {
    "minimize_spills": Caution(
        id="minimize_spills",
        warning="Use the small spoon and keep the bowl steady, so there is less to spill.",
        safer_way="nudge the treat onto a tray and walk it slowly home",
        reason="less spilling means less waste and less worry",
    ),
    "share_first": Caution(
        id="share_first",
        warning="Take only a little at first and save the rest for the others.",
        safer_way="divide the treat before anyone gets too excited",
        reason="sharing early keeps the feast peaceful",
    ),
    "ask_first": Caution(
        id="ask_first",
        warning="Ask the elder before touching the sweet thing, because some treats are not for wandering paws.",
        safer_way="wait beside the door and call politely",
        reason="asking first keeps trouble out of the doorway",
    ),
}

REINDEER_NAMES = ["Runa", "Mika", "Soren", "Tavi", "Nella", "Orin"]
CHILD_NAMES = ["Pip", "Lina", "Mara", "Finn", "June", "Owen"]


@dataclass
class StoryParams:
    setting: str
    treat: str
    twist: str
    caution: str
    reindeer: str
    child: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, t, tw, c) for s in SETTINGS for t in TREATS for tw in TWISTS for c in CAUTIONS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a reindeer, a delicious treat, and a cautionary twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--caution", choices=CAUTIONS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    s = args.setting or rng.choice(list(SETTINGS))
    t = args.treat or rng.choice(list(TREATS))
    tw = args.twist or rng.choice(list(TWISTS))
    c = args.caution or rng.choice(list(CAUTIONS))
    if args.setting and args.treat and args.twist and args.caution:
        return StoryParams(s, t, tw, c, rng.choice(REINDEER_NAMES), rng.choice(CHILD_NAMES))
    return StoryParams(
        setting=s,
        treat=t,
        twist=tw,
        caution=c,
        reindeer=rng.choice(REINDEER_NAMES),
        child=rng.choice(CHILD_NAMES),
    )


def _add_characters(world: World, p: StoryParams) -> None:
    world.add(Entity("reindeer", kind="character", type="reindeer", label=p.reindeer, role="hero"))
    world.add(Entity("child", kind="character", type="child", label=p.child, role="helper"))
    world.add(Entity("scene", kind="thing", type="place", label=SETTINGS[p.setting].place))
    world.add(Entity("treat", kind="thing", type="food", label=TREATS[p.treat].name))
    world.add(Entity("bowl", kind="thing", type="thing", label="bowl"))
    world.add(Entity("tray", kind="thing", type="thing", label="tray"))


def tell(p: StoryParams) -> World:
    world = World()
    _add_characters(world, p)
    setting = SETTINGS[p.setting]
    treat = TREATS[p.treat]
    twist = TWISTS[p.twist]
    caution = CAUTIONS[p.caution]
    reindeer = world.get("reindeer")
    child = world.get("child")
    sweet = world.get("treat")

    reindeer.memes["hunger"] = 2.0
    child.memes["care"] = 2.0

    world.say(f"In {setting.place}, where {setting.song}, {reindeer.label} the reindeer came trotting with {child.label}.")
    world.say(f"They found {treat.place}, and it looked {treat.adjective} enough to make any mouth water.")

    world.para()
    world.say(f'{reindeer.label} sniffed the air. "{treat.name}!" {reindeer.label} cried. "{caution.warning}"')
    child.memes["care"] += 1
    child.memes["worry"] += 1
    world.say(f'{child.label} nodded. "We should {caution.safer_way}," {child.label} said, because {caution.reason}.')

    # Twist: a sudden reveal changes the middle of the story.
    world.para()
    world.say(twist.reveal)

    if p.twist == "hungry_helper":
        # The treat is at risk unless minimized carefully.
        sweet.meters["spilled"] = 0.0
        reindeer.memes["worry"] += 1
        world.say(f"The crumbs were close enough to tempt a sneaky nose, so the two hurried to minimize the mess.")
        sweet.meters["spilled"] += 1.0
        propagate(world)
        world.say(f'With the tray held flat, they managed to minimize the spill and keep the {treat.name} safe.')
    elif p.twist == "lost_tail":
        reindeer.memes["worry"] += 1
        world.say(f"They searched the snow, and the child helped the reindeer minimize the search by looking for one bright bell at a time.")
        world.say(f"At last, the little bell glittered under a fern, and the mistake turned into a laugh.")
        child.memes["joy"] += 1
    else:
        world.say(f'The child stopped the reindeer from taking a bite too soon, so they could share it the right way.')
        reindeer.memes["care"] += 1
        child.memes["joy"] += 1

    world.para()
    world.say(f"At last they followed the cautious way: {caution.safer_way}.")
    world.say(f"So the {treat.name} was carried home with less waste, less fuss, and more kindness.")
    reindeer.memes["joy"] += 1
    child.memes["joy"] += 1
    reindeer.memes["care"] += 1

    world.para()
    world.say(f"In the end, the lesson was plain: {twist.lesson}")
    world.say(f"And that is how the little folk tale turned: {twist.change}, while the {treat.name} stayed {treat.adjective} to the end.")

    world.facts.update(
        setting=setting,
        treat=treat,
        twist=twist,
        caution=caution,
        reindeer=reindeer,
        child=child,
        outcome="shared",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk tale about {f['reindeer'].label} the reindeer and {f['child'].label} finding a {f['treat'].adjective} {f['treat'].name} in {f['setting'].place}. Include a cautionary twist and the word 'minimize'.",
        f"Tell a gentle story where a reindeer learns to minimize waste while protecting a delicious treat, and the ending feels like an old folk tale.",
        f"Write a child-friendly cautionary folktale with a twist: {f['reindeer'].label} wants the {f['treat'].name}, but careful choices keep the feast safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {f['reindeer'].label} the reindeer and {f['child'].label}, who work together in the folk-tale setting.",
        ),
        QAItem(
            question=f"What delicious thing did they find?",
            answer=f"They found a {f['treat'].adjective} {f['treat'].name}, and it was tempting enough to need a careful plan.",
        ),
        QAItem(
            question=f"What did the caution tell them to do?",
            answer=f"The caution told them to {f['caution'].safer_way}, because {f['caution'].reason}.",
        ),
        QAItem(
            question=f"What changed the story in the middle?",
            answer=f"The twist was that {f['twist'].reveal}",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the treat kept safe, less waste, and a lesson about care and patience.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reindeer?",
            answer="A reindeer is a deer that can live in cold places and has strong legs for walking through snow.",
        ),
        QAItem(
            question="What does delicious mean?",
            answer="Delicious means something tastes very good and makes people want another bite.",
        ),
        QAItem(
            question="What does minimize mean?",
            answer="Minimize means to make something as small as possible, like making a spill or a mistake less big.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise turn that changes what the characters expected.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means the story gives a warning or lesson so readers can be careful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label!r} meters={e.meters} memes={e.memes}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- fact(setting,S).
treat(T) :- fact(treat,T).
twist(Tw) :- fact(twist,Tw).
caution(C) :- fact(caution,C).

valid(S,T,Tw,C) :- setting(S), treat(T), twist(Tw), caution(C).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    for twid in TWISTS:
        lines.append(asp.fact("twist", twid))
    for cid in CAUTIONS:
        lines.append(asp.fact("caution", cid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP parity for valid combos ({len(py)}).")
        return 0
    print("Mismatch between Python and ASP combo sets.")
    print("Only in Python:", sorted(py - cl))
    print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        treat=args.treat or rng.choice(list(TREATS)),
        twist=args.twist or rng.choice(list(TWISTS)),
        caution=args.caution or rng.choice(list(CAUTIONS)),
        reindeer=rng.choice(REINDEER_NAMES),
        child=rng.choice(CHILD_NAMES),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a}" for a in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for s, t, tw, c in valid_combos():
            params = StoryParams(s, t, tw, c, random.choice(REINDEER_NAMES), random.choice(CHILD_NAMES), seed=base_seed)
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.reindeer} / {p.child} / {p.setting} / {p.treat} / {p.twist} / {p.caution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
