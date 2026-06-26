#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tar_endanger_thin_flower_field_repetition_animal.py
=============================================================================================================================

A tiny animal-story world set in a flower field, built around repetition,
tar, danger, and a thin rescue path.

Premise:
- A small animal loves the flower field.
- Sticky tar threatens the thin stems and the little creatures who hop there.
- The helper keeps repeating the same careful action to clean up and protect the field.

Story shape:
- Beginning: animals play in a flower field.
- Middle: tar appears and endangers thin flowers.
- Turn: repeated careful work removes the tar.
- Ending: the field is safe again, and the small animal can play in peace.

The world is deliberately small and constraint-checked:
- tar is a real hazard in the flower field
- thin stems are at risk
- repetition is the chosen problem-solving feature
- the resolution must actually protect the endangered flowers
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "mouse", "bird", "squirrel"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the flower field"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    fragile: bool = True


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    repeated_action: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "flower_field": Setting(place="the flower field", affords={"tar_walk"}),
}

ACTIVITIES = {
    "tar_walk": Activity(
        id="tar_walk",
        verb="cross the flower field",
        gerund="crossing the flower field",
        rush="dash toward the flowers",
        hazard="tar",
        soil="stuck with tar",
        keyword="tar",
        tags={"tar", "field", "thin", "repetition"},
    )
}

PRIZES = {
    "flowers": Prize(
        label="flowers",
        phrase="a patch of thin flowers",
        type="flowers",
        fragile=True,
    )
}

TOOLS = {
    "washing_rinse": Tool(
        id="washing_rinse",
        label="a little pail of water",
        prep="fetch a little pail of water",
        tail="kept rinsing the sticky spots away",
        repeated_action="again and again",
    ),
    "leaf_pat": Tool(
        id="leaf_pat",
        label="soft leaves",
        prep="gather soft leaves",
        tail="kept patting the tar so it would lift off",
        repeated_action="over and over",
    ),
}

ANIMALS = [
    ("Pip", "rabbit"),
    ("Nia", "mouse"),
    ("Toto", "squirrel"),
    ("Momo", "bird"),
    ("Lulu", "fox"),
]

TRAITS = ["small", "curious", "gentle", "brave", "cheerful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    animal: str
    trait: str
    seed: Optional[int] = None


def tar_is_threat(activity: Activity, prize: Prize) -> bool:
    return activity.hazard == "tar" and prize.fragile


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if tar_is_threat(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: tar, thin flowers, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=[a for _, a in ANIMALS])
    ap.add_argument("--trait", choices=TRAITS)
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
        if not tar_is_threat(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError("No story: tar does not honestly endanger that prize here.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, act, prize = rng.choice(sorted(combos))
    name, animal = rng.choice(ANIMALS) if args.name is None or args.animal is None else (args.name, args.animal)
    if args.name is not None:
        name = args.name
    if args.animal is not None:
        animal = args.animal
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=act, prize=prize, name=name, animal=animal, trait=trait)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["tar"] = actor.meters.get("tar", 0.0) + 1.0
    world.facts["tar_seen"] = True
    world.facts["tar_threat"] = True
    if narrate:
        world.say(f"{actor.id} got tar on its paws while {activity.gerund}.")


def _tar_spread(world: World, actor: Entity, prize: Entity) -> None:
    sig = ("tar_spread", actor.id, prize.id)
    if sig in world.fired:
        return
    if actor.meters.get("tar", 0.0) >= THRESHOLD:
        world.fired.add(sig)
        prize.meters["tar"] = prize.meters.get("tar", 0.0) + 1.0
        prize.meters["endangered"] = prize.meters.get("endangered", 0.0) + 1.0


def _repeat_clean(world: World, actor: Entity, prize: Entity, tool: Tool) -> None:
    sig = ("repeat_clean", actor.id, prize.id)
    if sig in world.fired:
        return
    if actor.memes.get("repetition", 0.0) >= 1.0:
        world.fired.add(sig)
        prize.meters["tar"] = max(0.0, prize.meters.get("tar", 0.0) - 1.0)
        if prize.meters["tar"] <= 0.0:
            prize.meters["endangered"] = 0.0
        world.say(f"{actor.id} used {tool.label} {tool.repeated_action}.")


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters.get("tar", 0.0) >= THRESHOLD:
                for prize in world.entities.values():
                    if prize.kind != "thing":
                        continue
                    before = prize.meters.get("tar", 0.0)
                    _tar_spread(world, actor, prize)
                    if prize.meters.get("tar", 0.0) != before:
                        changed = True
                        if narrate:
                            world.say("The sticky tar started to endanger the thin flowers.")
            if actor.memes.get("repetition", 0.0) >= 1.0:
                for prize in world.entities.values():
                    if prize.kind == "thing":
                        before = prize.meters.get("tar", 0.0)
                        _repeat_clean(world, actor, prize, TOOLS["washing_rinse"])
                        if prize.meters.get("tar", 0.0) != before:
                            changed = True


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, animal: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=animal))
    hero.memes["repetition"] = 0.0
    prize = world.add(Entity(id="flowers", kind="thing", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    prize.meters["endangered"] = 0.0

    world.say(f"{hero.id} was a {trait} {animal} who loved the flower field.")
    world.say(f"The field was full of thin flowers that swayed like little bows.")
    world.para()
    world.say(f"One day, {hero.id} saw a dark patch of {activity.keyword} near the flowers.")
    world.say(f"{hero.id} wanted to {activity.verb}, but the sticky tar could endanger the thin flowers.")
    _do_activity(world, hero, activity, narrate=False)
    propagate(world)
    world.para()
    world.say(f"{hero.id} did not want the tar to stay.")
    world.say(f"So {hero.id} chose a careful way: {TOOLS['washing_rinse'].prep}.")
    hero.memes["repetition"] = 1.0
    world.say(f"{hero.id} kept cleaning {TOOLS['washing_rinse'].repeated_action}.")
    propagate(world)
    world.para()
    if prize.meters.get("tar", 0.0) <= 0.0:
        world.say(f"At last, the thin flowers stood clean and safe again.")
        world.say(f"{hero.id} smiled in the flower field, and the wind moved the petals gently.")
        world.facts["resolved"] = True
    else:
        world.say(f"The tar was still there, and the flowers were not safe.")
        world.facts["resolved"] = False

    world.facts.update(hero=hero, prize=prize, activity=activity, setting=setting, tool=TOOLS["washing_rinse"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f"Write a short animal story in a flower field about {hero.id} and sticky tar.",
        f"Tell a gentle story where a {hero.type} meets tar and uses repetition to help thin flowers.",
        f"Write a simple story about a flower field, danger, and a careful animal who cleans tar away.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    act = f["activity"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"Who was the story about in the flower field?",
            answer=f"It was about {hero.id}, a small {hero.type} who cared about the flower field.",
        ),
        QAItem(
            question=f"What made the thin flowers unsafe?",
            answer=f"The sticky tar made the thin flowers endangered, because it could cling to them and hurt them.",
        ),
        QAItem(
            question=f"What did {hero.id} do to help?",
            answer=f"{hero.id} used {tool.label} and kept cleaning {tool.repeated_action} until the tar was gone.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question="How did the story end?",
            answer="The tar was cleaned away, and the thin flowers stood safe and bright in the flower field.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tar?",
            answer="Tar is a sticky, dark substance that can cling to things and make them dirty.",
        ),
        QAItem(
            question="What does thin mean?",
            answer="Thin means something is not wide or thick, so it can bend or break more easily.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing the same helpful action again and again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
threatened(P) :- tar_on(A), thin(P).
resolved(P) :- threatened(P), cleaned(P).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "flower_field")]
    lines.append(asp.fact("affords", "flower_field", "tar_walk"))
    lines.append(asp.fact("activity", "tar_walk"))
    lines.append(asp.fact("hazard", "tar_walk", "tar"))
    lines.append(asp.fact("thin", "flowers"))
    lines.append(asp.fact("prize", "flowers"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_triples() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show threatened/1."))
    return sorted(set(asp.atoms(model, "threatened")))


def asp_verify() -> int:
    if valid_story_triples():
        print(f"OK: python gate has {len(valid_story_triples())} combo(s).")
        return 0
    print("MISMATCH: no valid combos.")
    return 1


CURATED = [
    StoryParams(place="flower_field", activity="tar_walk", prize="flowers", name="Pip", animal="rabbit", trait="curious"),
    StoryParams(place="flower_field", activity="tar_walk", prize="flowers", name="Nia", animal="mouse", trait="gentle"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "flower_field":
        raise StoryError("No story: this world only lives in the flower field.")
    if args.activity and args.activity != "tar_walk":
        raise StoryError("No story: only tar-walk belongs here.")
    if args.prize and args.prize != "flowers":
        raise StoryError("No story: only the thin flowers are part of this world.")
    return StoryParams(
        place="flower_field",
        activity="tar_walk",
        prize="flowers",
        name=args.name or rng.choice([n for n, _ in ANIMALS]),
        animal=args.animal or rng.choice([a for _, a in ANIMALS]),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.animal, params.trait)
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show threatened/1."))
        return
    if args.asp:
        print("1 compatible story triple:")
        print("  flower_field tar_walk flowers")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
