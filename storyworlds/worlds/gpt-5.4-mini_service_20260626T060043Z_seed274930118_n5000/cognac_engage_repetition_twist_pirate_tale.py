#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld about a sailor, a guarded bottle of cognac,
a risky engagement with mischief, and a twist that turns trouble into a win.

Seed premise:
- A young pirate wants to sip cognac.
- The first mate worries because the bottle is precious and the deck is rough.
- The child keeps trying again and again.
- A twist reveals the right way to engage with the bottle: not drink it, but use it for a toast after the ship is safely mended.
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

# Physical / emotional thresholds.
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the deck"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.state: dict[str, float] = {"repetition": 0.0, "twist": 0.0}

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _maybe(v: float) -> bool:
    return v >= THRESHOLD


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["eagerness"] = actor.memes.get("eagerness", 0.0) + 1.0
    world.state["repetition"] += 1.0
    if narrate:
        world.say(f"{actor.id} wanted to {activity.verb} again.")
        world.say(f"{actor.id} tried again, because the thought of {activity.keyword} would not let go.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters.get("dirty", 0.0) >= THRESHOLD or sim.state["repetition"] > 0


def valid_combo(activity: Activity, prize: Prize) -> bool:
    return prize.label == "cognac" and activity.id in {"engage", "twist"}


def asp_facts() -> str:
    import asp
    lines = []
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
    for gid, g in GEARS.items():
        lines.append(asp.fact("gear", gid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(A,P) :- activity(A), prize(P), keyword(A,"engage"), P = cognac.
valid(A,P) :- activity(A), prize(P), keyword(A,"twist"), P = cognac.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {("engage", "cognac"), ("twist", "cognac")}
    cl = set(asp_valid_combos())
    if cl == py:
        print("OK: ASP matches Python gate (2 combos).")
        return 0
    print("MISMATCH:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


def setting_detail(setting: Setting) -> str:
    return "The deck creaked under the lantern glow, and salt wind tugged at every rope."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little pirate with a quick grin and a stubborn heart.")


def love_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} loved to {activity.verb}, and loved to try again after that, again and again.")


def prize_line(world: World, hero: Entity, prize: Entity) -> None:
    world.say(f"Their most prized treasure was {prize.phrase}, kept safe by the ship's first mate.")


def arrive(world: World, hero: Entity, mate: Entity) -> None:
    world.say(f"One night, {hero.id} and {hero.pronoun('possessive')} {mate.label} stood on {world.setting.place}.")
    world.say(setting_detail(world.setting))


def wants(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    world.say(f"{hero.id} wanted to {activity.verb} with the {prize.label}, but that was not a wise thing to do.")


def warn(world: World, mate: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not predict_mess(world, hero, activity, prize.id):
        return False
    world.say(f'"If ye {activity.verb}, ye may spoil the {prize.label}," {mate.id} warned.')
    return True


def repeat_try(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubbornness"] = hero.memes.get("stubbornness", 0.0) + 1.0
    _do_activity(world, hero, activity, narrate=True)
    _do_activity(world, hero, activity, narrate=True)


def twist_offer(world: World, mate: Entity, hero: Entity, prize: Entity) -> None:
    world.state["twist"] += 1.0
    world.say(
        f"Then the first mate had a twist of an idea: 'We do not need to spill a drop. "
        f"We can engage with the {prize.label} by raising a toast after the deck is mended.'"
    )
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0


def accept(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    world.say(
        f"{hero.id} beamed, and together they fixed the last loose plank. "
        f"Then they lifted the {prize.label} high, and the ship shone like a tiny king's hall."
    )


SETTINGS = {
    "deck": Setting(place="the deck", affords={"engage", "twist"}),
}

ACTIVITIES = {
    "engage": Activity(
        id="engage",
        verb="engage the rigging",
        gerund="engaging the rigging",
        rush="rush at the ropes",
        mess="dirty",
        soil="dirty",
        keyword="engage",
        tags={"rope", "ship", "courage"},
    ),
    "twist": Activity(
        id="twist",
        verb="twist the rope",
        gerund="twisting the rope",
        rush="twirl the line",
        mess="dirty",
        soil="dirty",
        keyword="twist",
        tags={"rope", "ship", "courage"},
    ),
}

PRIZES = {
    "cognac": Prize(
        label="cognac",
        phrase="a tiny bottle of cognac",
        type="bottle",
    )
}

GEARS = {
    "gloves": Gear(
        id="gloves",
        label="work gloves",
        prep="pull on the work gloves",
        tail="put on the work gloves",
    )
}

NAMES = ["Nell", "Pip", "Wren", "Kit", "Mira", "Jory", "Ari", "Finn"]
TITLES = {"mother": "mother", "father": "father", "mate": "first mate"}


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    mate = world.add(Entity(id="Mate", kind="character", type="pirate", label=TITLES[params.parent]))
    prize = world.add(Entity(
        id=params.prize,
        kind="thing",
        type="bottle",
        label="cognac",
        phrase=PRIZES[params.prize].phrase,
        caretaker=mate.id,
        owner=hero.id,
    ))
    activity = ACTIVITIES[params.activity]

    introduce(world, hero)
    love_activity(world, hero, activity)
    prize_line(world, hero, prize)
    world.para()
    arrive(world, hero, mate)
    wants(world, hero, activity, prize)
    warn(world, mate, hero, activity, prize)
    repeat_try(world, hero, activity)
    world.para()
    twist_offer(world, mate, hero, prize)
    accept(world, hero, prize)

    world.facts.update(hero=hero, mate=mate, prize=prize, activity=activity, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for a young child about a sailor, a cognac bottle, and a clever twist.',
        f"Tell a story where {f['hero'].id} wants to {f['activity'].verb} but the {f['mate'].label} warns about the cognac.",
        "Write a gentle pirate story that repeats the problem a couple of times and then turns on a surprising idea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    prize: Entity = f["prize"]
    activity: Activity = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label}?",
            answer=f"{hero.id} wanted to {activity.verb}, but that was not the right way to handle the cognac.",
        ),
        QAItem(
            question=f"Who warned {hero.id} about the {prize.label}?",
            answer=f"The {mate.label} warned {hero.id} that the {prize.label} might be spoiled.",
        ),
        QAItem(
            question=f"What happened after {hero.id} tried again and again?",
            answer=f"A twist of an idea came: they used the moment to fix the ship and then share a safe toast.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the ship mended, the cognac kept safe, and everyone smiling on the deck.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cognac?",
            answer="Cognac is a kind of aged brandy, which is a strong drink made from wine.",
        ),
        QAItem(
            question="What does it mean to engage something?",
            answer="To engage something can mean to take hold of it, start using it, or get involved with it.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a turning motion, or a surprising change in a story or plan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"state={world.state}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: this pirate tale only fits cognac with engage or twist.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or "cognac"
    if not valid_combo(ACTIVITIES[activity], PRIZES[prize]):
        raise StoryError(explain_rejection(ACTIVITIES[activity], PRIZES[prize]))
    return StoryParams(
        place=args.place or "deck",
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        gender=args.gender or rng.choice(["girl", "boy"]),
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=args.trait or rng.choice(["brave", "curious", "stubborn"]),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about cognac, repetition, and twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait")
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


def asp_facts_program() -> str:
    return asp_facts()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(place="deck", activity="engage", prize="cognac", name="Nell", gender="girl", parent="mother", trait="brave"),
            StoryParams(place="deck", activity="twist", prize="cognac", name="Pip", gender="boy", parent="father", trait="curious"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
