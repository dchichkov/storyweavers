#!/usr/bin/env python3
"""
A small story world about a ballerina in a vegetable garden, where a playful
rhyme helps turn a mistake into reconciliation.

The premise is simple: a ballerina loves to dance near a vegetable garden. A
careful gardener worries the dancing might bend seedlings or scatter mulch. The
turn comes when the ballerina slows down, listens, and changes the dance into a
gentle rhyme the gardener can join. The ending should feel warm, concrete, and
earned: the garden stays safe, the hurt feeling eases, and both characters share
a small happy rhythm together.
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
        female = {"girl", "woman", "mother", "mom", "ballerina"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the vegetable garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str = "rhyme"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _touch_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.meters.get("careful", 0) >= THRESHOLD:
            continue
        if actor.meters.get("twirl", 0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.caretaker != actor.id:
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            if item.type in {"seedling", "row", "soil"}:
                world.fired.add(sig)
                item.meters["scuffed"] = item.meters.get("scuffed", 0) + 1
                out.append("A few tiny leaves bent as the dance stepped too close.")
    return out


def _reconcile(world: World) -> list[str]:
    out: list[str] = []
    ballerina = world.get("Ballerina")
    gardener = world.get("Gardener")
    if ballerina.memes.get("sorry", 0) >= THRESHOLD and gardener.memes.get("hurt", 0) >= THRESHOLD:
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            ballerina.memes["reconciliation"] = ballerina.memes.get("reconciliation", 0) + 1
            gardener.memes["reconciliation"] = gardener.memes.get("reconciliation", 0) + 1
            gardener.memes["hurt"] = 0
            out.append("The hurt feeling softened into a shared smile.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_touch_mess, _reconcile):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_mess(world: World) -> bool:
    sim = world.copy()
    ballerina = sim.get("Ballerina")
    ballerina.meters["twirl"] = ballerina.meters.get("twirl", 0) + 1
    propagate(sim, narrate=False)
    return any(e.meters.get("scuffed", 0) >= THRESHOLD for e in sim.entities.values())


def introduce(world: World, ballerina: Entity) -> None:
    world.say("There once was a cheerful ballerina who loved soft shoes and bright mornings.")
    world.say("She liked to hear little sounds that seemed ready to become a song.")
    world.say(f"{ballerina.id} watched the {world.setting.place} and thought it looked perfect for a dance.")


def enter_garden(world: World, ballerina: Entity, gardener: Entity) -> None:
    world.say(f"One day, {ballerina.id} went to {world.setting.place} with {gardener.label}.")
    world.say("The tomato vines leaned under green leaves, and the carrots hid below the soil.")


def wants_to_dance(world: World, ballerina: Entity) -> None:
    ballerina.meters["twirl"] = ballerina.meters.get("twirl", 0) + 1
    world.say(f"{ballerina.id} wanted to twirl, leap, and make the garden day feel like a rhyme.")
    world.say("Her feet tapped, tip-tap, as if each step were searching for a line to sing.")


def warn(world: World, gardener: Entity, ballerina: Entity, prize: Entity) -> None:
    if not predict_mess(world):
        return
    gardener.memes["hurt"] = gardener.memes.get("hurt", 0) + 1
    world.say(f'"Please be careful," {gardener.id} said. "Those little {prize.label} could get bent."')
    world.say(f"{gardener.pronoun('possessive').capitalize()} voice was gentle, but it carried worry.")


def apologize(world: World, ballerina: Entity) -> None:
    ballerina.memes["sorry"] = ballerina.memes.get("sorry", 0) + 1
    world.say(f"{ballerina.id} looked down at her slippers and whispered, 'I did not mean to be clumsy.'")
    world.say("She stood still long enough to listen to the breeze move through the bean leaves.")


def offer_rhyme(world: World, ballerina: Entity, gardener: Entity, gear: Gear) -> None:
    world.say(f"Then {ballerina.id} smiled softly and said, 'How about I use a gentler rhyme?'")
    world.say(f'"We can step like this," she said, and {gardener.id} nodded at the slow, careful beat.')
    world.say(f"They used {gear.label}, and the new rhythm felt kind instead of busy.")


def reconcile(world: World, ballerina: Entity, gardener: Entity, gear: Gear) -> None:
    ballerina.meters["careful"] = ballerina.meters.get("careful", 0) + 1
    propagate(world, narrate=True)
    world.say(f"{ballerina.id} lifted her arms, and {gardener.id} began to hum along.")
    world.say(f"Together they made a tiny rhyme: step, stop, smile, and step again.")
    world.say(f"The {gear.label} kept the path neat, and the little plants stayed safe.")
    world.say(f"By the end, {ballerina.id} was dancing in the {world.setting.place}, and {gardener.id} was laughing beside her.")


SETTINGS = {
    "garden": Setting(place="the vegetable garden", affords={"rhyme"}),
}

ACTIVITIES = {
    "rhyme": Activity(
        id="rhyme",
        verb="make a rhyme",
        gerund="making a rhyme",
        rush="rush through the rows",
        risk="might bend the seedlings",
        mess="scuffed",
        zone={"row"},
        keyword="rhyme",
        tags={"rhyme", "heartwarming"},
    )
}

PRIZES = {
    "seedlings": Prize(
        label="seedlings",
        phrase="a row of tiny seedlings",
        type="seedlings",
        region="row",
        plural=True,
    )
}

GEAR = {
    "garden-path": Gear(
        id="garden-path",
        label="a narrow stepping path",
        prep="set down a narrow stepping path first",
        tail="they followed the little path and kept the plants safe",
    )
}

GIRL_NAMES = ["Mina", "Luna", "Tara", "Nina", "Pia", "Sara"]
TRAITS = ["gentle", "bright", "kind", "careful", "brave"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("garden", "rhyme", "seedlings")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming ballerina story in a vegetable garden.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
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
    if args.place and args.place != "garden":
        raise StoryError("This world only knows the vegetable garden.")
    if args.activity and args.activity != "rhyme":
        raise StoryError("This world only supports the rhyme activity.")
    if args.prize and args.prize != "seedlings":
        raise StoryError("This world only supports the seedlings prize.")
    name = args.name or rng.choice(GIRL_NAMES)
    return StoryParams(place="garden", activity="rhyme", prize="seedlings", name=name)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    ballerina = world.add(Entity(id="Ballerina", kind="character", type="ballerina", label=params.name))
    gardener = world.add(Entity(id="Gardener", kind="character", type="woman", label="the gardener"))
    prize = world.add(Entity(id="Seedlings", type="seedlings", label="seedlings", plural=True, caretaker="Gardener"))
    gear = world.add(Entity(id="Path", type="gear", label="a narrow stepping path"))

    world.facts.update(ballerina=ballerina, gardener=gardener, prize=prize, gear=gear, activity=ACTIVITIES[params.activity], setting=world.setting)

    introduce(world, ballerina)
    enter_garden(world, ballerina, gardener)
    world.para()
    wants_to_dance(world, ballerina)
    warn(world, gardener, ballerina, prize)
    apologize(world, ballerina)
    world.para()
    offer_rhyme(world, ballerina, gardener, GEAR["garden-path"])
    reconcile(world, ballerina, gardener, GEAR["garden-path"])
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming story about a ballerina in a vegetable garden who turns a near-mistake into a kind rhyme.",
        "Tell a gentle story where a ballerina wants to dance among seedlings, but the gardener worries, and they reconcile.",
        "Write a short children's story set in a vegetable garden that includes a rhyme and a happy reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    ballerina = world.facts["ballerina"]
    gardener = world.facts["gardener"]
    return [
        QAItem(
            question=f"Where did {ballerina.label} want to dance?",
            answer=f"{ballerina.label} wanted to dance in the vegetable garden, where the rows of plants were growing carefully.",
        ),
        QAItem(
            question="Why did the gardener worry?",
            answer="The gardener worried that quick dancing might bend the tiny seedlings and disturb the neat garden rows.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer="The ballerina slowed down, apologized, and changed the dance into a gentle rhyme they could share together.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="By the end, the garden stayed safe, the worried feeling faded, and the two of them were smiling together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vegetable garden?",
            answer="A vegetable garden is a place where people grow vegetables like tomatoes, carrots, beans, and lettuce.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern of words that sound alike, which can make a song or a poem feel playful.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset, talk kindly, and make peace again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
needs_fix(A,P) :- prize_at_risk(A,P), has_gear(A,P).
valid_story(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_gear(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    lines.append(asp.fact("has_gear", "rhyme", "seedlings"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(py_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories:")
        for p, a, pr in asp_valid_combos():
            print(f"  {p} {a} {pr}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams("garden", "rhyme", "seedlings", "Mina", seed=base_seed))]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
