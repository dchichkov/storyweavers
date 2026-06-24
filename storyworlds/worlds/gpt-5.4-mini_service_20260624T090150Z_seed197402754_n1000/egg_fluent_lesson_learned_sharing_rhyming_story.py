#!/usr/bin/env python3
"""
storyworlds/worlds/egg_fluent_lesson_learned_sharing_rhyming_story.py
======================================================================

A tiny rhyming story world about an egg, a fluent speaker, and a lesson
learned through sharing.

Initial seed tale:
---
A small child found a shiny egg that looked like a pearl.
A fluent little bird could speak in rhymes and words that swirled.

The child wanted to keep the egg all alone and would not share.
The bird sang a friendly rhyme and showed that sharing was fair.

They split the play, took turns, and tucked the egg into a nest.
The child learned that sharing makes a toy feel even best.
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the sunny meadow"


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    rhyme: str
    lesson: str
    share_action: str


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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["child"]
    guide = world.facts["guide"]
    if child.memes.get("stingy", 0.0) < THRESHOLD:
        return out
    if ("lesson", child.id) in world.fired:
        return out
    world.fired.add(("lesson", child.id))
    child.memes["sharing"] = child.memes.get("sharing", 0.0) + 1
    child.memes["lesson_learned"] = child.memes.get("lesson_learned", 0.0) + 1
    out.append(f"{guide.label} gave a grin and a rhyme so bright that {child.id} could see the light.")
    return out


CAUSAL_RULES = [
    _r_lesson,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_play(world: World, child: Entity, guide: Entity, prize: Entity, narrate: bool = True) -> None:
    child.meters["attention"] = child.meters.get("attention", 0.0) + 1
    if prize.owner == child.id:
        child.memes["possessive"] = child.memes.get("possessive", 0.0) + 1
    propagate(world, narrate=narrate)


def predict_share(world: World, child: Entity, guide: Entity, prize: Entity) -> dict:
    sim = world.copy()
    _do_play(sim, sim.get(child.id), sim.get(guide.id), sim.get(prize.id), narrate=False)
    return {
        "sharing": sim.get(child.id).memes.get("sharing", 0.0),
        "lesson_learned": sim.get(child.id).memes.get("lesson_learned", 0.0),
    }


def intro(world: World, child: Entity, guide: Entity, prize: Entity) -> None:
    world.say(
        f"In {world.setting.place}, a little {child.type} named {child.id} found {prize.phrase}."
    )
    world.say(
        f"A {guide.label} named {guide.id} was fluent with rhymes, and every line it sang felt smooth and true."
    )


def want_to_keep(world: World, child: Entity, prize: Entity) -> None:
    child.memes["stingy"] = child.memes.get("stingy", 0.0) + 1
    world.say(
        f"{child.id} held {prize.it()} tight and said, \"It's mine to keep, and mine to see.\""
    )


def ask_share(world: World, guide: Entity, child: Entity, prize: Entity) -> None:
    world.say(
        f"{guide.id} chirped a rhyme, all neat and light: \"A toy is bright when shared just right.\""
    )
    world.say(
        f"\"If we take turns with {prize.it()}, the fun will bloom for you and me.\""
    )


def turn_to_sharing(world: World, child: Entity, guide: Entity, prize: Entity) -> None:
    pred = predict_share(world, child, guide, prize)
    if pred["sharing"] < THRESHOLD:
        world.say(
            f"{child.id} paused, then smiled at the tune and knew the happy choice came soon."
        )
    child.memes["stingy"] = 0.0
    child.memes["sharing"] = child.memes.get("sharing", 0.0) + 1
    world.say(
        f"{child.id} gave {prize.it()} to {guide.id} for a turn, and then {guide.id} gave it back with a cheerful purr."
    )


def end_image(world: World, child: Entity, guide: Entity, prize: Entity) -> None:
    child.memes["lesson_learned"] = child.memes.get("lesson_learned", 0.0) + 1
    world.say(
        f"By the end, {child.id} and {guide.id} shared {prize.it()} in the meadow glow, and the lesson learned began to show."
    )
    world.say(
        f"The egg stayed safe, the rhyme stayed sweet, and sharing made the day complete."
    )


def tell(
    setting: Setting,
    prize_cfg: Prize,
    guide_cfg: Guide,
    child_name: str = "Milo",
    child_type: str = "boy",
) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    guide = world.add(Entity(id=guide_cfg.id, kind="character", type="bird", label=guide_cfg.label))
    prize = world.add(
        Entity(
            id="egg",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=child.id,
        )
    )

    world.facts.update(child=child, guide=guide, prize=prize, guide_cfg=guide_cfg, prize_cfg=prize_cfg)

    intro(world, child, guide, prize)
    world.para()
    want_to_keep(world, child, prize)
    ask_share(world, guide, child, prize)
    turn_to_sharing(world, child, guide, prize)
    world.para()
    end_image(world, child, guide, prize)
    return world


SETTINGS = {
    "meadow": Setting(place="the sunny meadow"),
    "garden": Setting(place="the little garden"),
    "brook": Setting(place="the brookside"),
}

PRIZES = {
    "egg": Prize(label="egg", phrase="a shiny little egg", type="egg"),
    "gold_egg": Prize(label="gold egg", phrase="a golden egg", type="egg"),
}

GUIDES = {
    "bird": Guide(
        id="Pip",
        label="Pip the bird",
        phrase="a fluent little bird",
        rhyme="A toy is bright when shared just right.",
        lesson="sharing makes joy grow",
        share_action="take turns",
    ),
    "duck": Guide(
        id="Dot",
        label="Dot the duck",
        phrase="a fluent little duck",
        rhyme="A toy is sweet when shared by each.",
        lesson="sharing keeps play kind",
        share_action="take turns",
    ),
}

NAMES_BOY = ["Milo", "Finn", "Theo", "Noah", "Eli"]
NAMES_GIRL = ["Luna", "Mia", "Zoe", "Ava", "Nora"]


@dataclass
class StoryParams:
    place: str
    prize: str
    guide: str
    name: str
    gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, prize, guide) for place in SETTINGS for prize in PRIZES for guide in GUIDES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about sharing a shiny egg.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.prize:
        combos = [c for c in combos if c[1] == args.prize]
    if args.guide:
        combos = [c for c in combos if c[2] == args.guide]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prize, guide = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    return StoryParams(place=place, prize=prize, guide=guide, name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short rhyming story for a child about an egg and sharing.',
        f"Tell a gentle story where {f['child'].id} finds {f['prize_cfg'].phrase} in {world.setting.place} and learns to share it.",
        f"Write a simple lesson-learned story with a fluent bird and a shiny egg.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, guide, prize = f["child"], f["guide"], f["prize"]
    return [
        QAItem(
            question=f"What did {child.id} find at {world.setting.place}?",
            answer=f"{child.id} found {prize.phrase}, and it became the little treasure in the story.",
        ),
        QAItem(
            question=f"Who was fluent with rhymes in the story?",
            answer=f"{guide.id}, {guide.label}, was the fluent helper who sang rhymes and encouraged sharing.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn?",
            answer=f"{child.id} learned that sharing can make play sweeter, kinder, and more fun for everyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an egg?",
            answer="An egg is a small oval thing that some animals lay, and some eggs can be fragile and smooth.",
        ),
        QAItem(
            question="What does fluent mean?",
            answer="Fluent means speaking or doing something smoothly and easily, without lots of stopping.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting another person use or enjoy something too, usually by taking turns.",
        ),
        QAItem(
            question="Why is taking turns fair?",
            answer="Taking turns is fair because each person gets time to play, and no one is left out.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
good_story(P, Egg, Guide) :- place(P), prize(Egg), fluent_guide(Guide).
shared_story(P, Egg, Guide) :- good_story(P, Egg, Guide).
lesson_learned(P, Egg, Guide) :- shared_story(P, Egg, Guide).
#show good_story/3.
#show shared_story/3.
#show lesson_learned/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for prize in PRIZES:
        lines.append(asp.fact("prize", prize))
    for guide in GUIDES:
        lines.append(asp.fact("fluent_guide", guide))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    atoms = set(asp.atoms(model, "good_story"))
    py = set(valid_combos())
    asp_set = set((p, e, g) for p, e, g in atoms)
    if asp_set == py:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        PRIZES[params.prize],
        GUIDES[params.guide],
        params.name,
        params.gender,
    )
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


CURATED = [
    StoryParams(place="meadow", prize="egg", guide="bird", name="Milo", gender="boy"),
    StoryParams(place="garden", prize="gold_egg", guide="duck", name="Luna", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show lesson_learned/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, egg, guide) combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.prize} in {p.place} with {p.guide}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
