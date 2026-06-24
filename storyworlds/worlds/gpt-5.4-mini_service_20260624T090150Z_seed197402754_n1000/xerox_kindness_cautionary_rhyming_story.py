#!/usr/bin/env python3
"""
xerox_kindness_cautionary_rhyming_story.py
==========================================

A tiny story world about a child's kindness, a cautionary copier mistake, and a
rhyming fix.

Premise:
- A child finds a Xerox machine in a small copy room.
- They want to make a kind copy for someone else.
- They must be careful, because the machine can jam, smear, or waste paper.

The world is deliberately small and constraint-checked:
- physical meters: paper, ink, jam, copies, mess
- emotional memes: kindness, caution, worry, pride, relief

The story always resolves by showing a safer, kinder choice.
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
    worn_by: Optional[str] = None
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
class Place:
    id: str
    label: str
    quiet: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
    weather: str = ""
    keyword: str = "xerox"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    kind: str
    can_be_copied: bool = True
    fragile: bool = False


@dataclass
class Gear:
    id: str
    label: str
    verb: str
    safety: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = meter(ent, key) + amount


def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def risky_copy(world: World, actor: Entity, prize: Entity, action: Action, use_gear: bool) -> dict:
    sim = world.copy()
    sim_actor = sim.get(actor.id)
    sim_prize = sim.get(prize.id)
    if use_gear:
        add_meme(sim_actor, "caution", 1.0)
        add_meter(sim_actor, "paper", -1.0)
    add_meter(sim_actor, action.mess, 1.0)
    add_meme(sim_actor, "worry", 1.0)
    jammed = action.id == "copy_fast" and not use_gear
    if jammed:
        add_meter(sim_actor, "jam", 1.0)
    if prize.fragile and not use_gear:
        add_meter(sim_prize, "smudge", 1.0)
    return {
        "jammed": jammed,
        "smudged": meter(sim_prize, "smudge") >= THRESHOLD,
        "waste": meter(sim_actor, "paper") < 0,
    }


def choose_safe_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if action.id in gear.tags and prize.can_be_copied:
            return gear
    return None


def rhyme_line(left: str, right: str) -> str:
    return f"{left}, {right}."


def intro(world: World, child: Entity, adult: Entity, prize: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} with a kind heart and a bright idea. "
        f"{child.pronoun().capitalize()} wanted to make a Xerox copy, nice and neat, "
        f"so {child.pronoun('possessive')} {adult.label} could share a special treat."
    )
    world.say(
        f"{child.id} found {prize.phrase} on the table by the wall, "
        f"and {child.id} thought, “A copy would be kind for one and all.”"
    )


def setup(world: World, child: Entity, place: Place, action: Action) -> None:
    world.say(
        f"In {place.label}, the Xerox machine sat with a soft green gleam; "
        f"{child.id} leaned in close and loved its whir and beam."
    )
    world.say(
        f"{child.id} wanted to {action.verb}, quick as a hop, "
        f"but a machine like that can smear, jam, or stop."
    )


def warn(world: World, child: Entity, adult: Entity, prize: Entity, action: Action) -> bool:
    pred = risky_copy(world, child, prize, action, use_gear=False)
    if not pred["jammed"] and not pred["smudged"]:
        return False
    add_meme(adult, "caution", 1.0)
    world.facts["pred"] = pred
    if pred["jammed"] and pred["smudged"]:
        world.say(
            f'"Careful," said {adult.id}, "or the Xerox may jam and make a mess; '
            f"your {prize.label} could lose its clean success.""
        )
    elif pred["jammed"]:
        world.say(
            f'"Careful," said {adult.id}, "or the Xerox may jam and grumble and groan; '
            f"then we will need to fix it, and that is no fun at home.""
        )
    else:
        world.say(
            f'"Careful," said {adult.id}, "or the Xerox may leave a smudge behind; '
            f"then the copy will not look gentle, tidy, and kind.""
        )
    return True


def hesitate(world: World, child: Entity, action: Action) -> None:
    add_meme(child, "worry", 1.0)
    world.say(
        f"{child.id} paused a bit, then took a tiny breath; "
        f"{child.pronoun().capitalize()} did not want a copier mishap."
    )
    world.say(
        f"{child.id} had rushed before, but now would choose with care; "
        f"kindness is sweetest when it is thoughtful and fair."
    )


def offer_gear(world: World, child: Entity, adult: Entity, prize: Entity, action: Action) -> Optional[Gear]:
    gear = choose_safe_gear(action, prize)
    if gear is None:
        raise StoryError("No safe gear fits this Xerox story.")
    add_meme(child, "caution", 1.0)
    world.say(
        f"{adult.id} smiled and said, “Let’s use {gear.label} first, and go slow; "
        f"that way the Xerox can work, and the good copy will show.”"
    )
    return gear


def resolve(world: World, child: Entity, adult: Entity, prize: Entity, action: Action, gear: Gear) -> None:
    add_meme(child, "kindness", 2.0)
    add_meme(child, "relief", 1.0)
    add_meme(adult, "relief", 1.0)
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1.0)
    world.say(
        f"{child.id} used {gear.label}, then pressed the button with care; "
        f"the Xerox hummed gently in the bright little air."
    )
    world.say(
        f"The page slid out clean, with no jam in sight; "
        f"{child.id} made a kind copy, neat and bright."
    )
    world.say(
        f"So {child.id} shared the copy with a grin so wide, "
        f"and the {prize.label} stayed safe, like a treasure inside."
    )


def tell(place: Place, action: Action, prize_cfg: Prize, hero_name: str, hero_type: str,
         adult_type: str = "mother") -> World:
    world = World(place)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, label="grown-up"))
    prize = world.add(Entity(id="prize", type=prize_cfg.kind, label=prize_cfg.id, phrase=prize_cfg.phrase))

    add_meme(child, "kindness", 1.0)
    intro(world, child, adult, prize)
    world.para()
    setup(world, child, place, action)
    warn(world, child, adult, prize, action)
    hesitate(world, child, action)
    gear = offer_gear(world, child, adult, prize, action)
    world.para()
    resolve(world, child, adult, prize, action, gear)

    world.facts.update(
        child=child,
        adult=adult,
        prize=prize,
        action=action,
        gear=gear,
        place=place,
        resolved=True,
    )
    return world


PLACES = {
    "copy_room": Place(id="copy_room", label="the copy room", quiet=True, affords={"copy_fast", "copy_slow"}),
    "library_corner": Place(id="library_corner", label="the library corner", quiet=True, affords={"copy_slow"}),
    "office": Place(id="office", label="the office", quiet=True, affords={"copy_fast", "copy_slow"}),
}

ACTIONS = {
    "copy_fast": Action(
        id="copy_fast",
        verb="copy the page fast",
        gerund="copying pages fast",
        rush="dash to the Xerox",
        risk="it may jam",
        mess="jam",
        weather="",
        keyword="xerox",
        tags={"xerox", "jam"},
    ),
    "copy_slow": Action(
        id="copy_slow",
        verb="copy the page slowly",
        gerund="copying pages slowly",
        rush="walk to the Xerox",
        risk="it may smudge",
        mess="smudge",
        weather="",
        keyword="xerox",
        tags={"xerox", "smudge"},
    ),
}

PRIZES = {
    "flyer": Prize(id="flyer", label="flyer", phrase="a colorful flyer", kind="paper", can_be_copied=True, fragile=False),
    "drawing": Prize(id="drawing", label="drawing", phrase="a crayon drawing", kind="paper", can_be_copied=True, fragile=True),
    "note": Prize(id="note", label="note", phrase="a thank-you note", kind="paper", can_be_copied=True, fragile=True),
}

GEAR = [
    Gear(id="guides", label="paper guides", verb="guide the paper", safety="less jamming", tags={"copy_fast", "copy_slow"}),
    Gear(id="cover", label="the copier cover", verb="keep the glass clean", safety="less smudging", tags={"copy_slow"}),
]

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Zoe", "Sam"]
TRAITS = ["kind", "careful", "brave", "gentle", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, place in PLACES.items():
        for aid in place.affords:
            for pr in PRIZES:
                if aid == "copy_fast" and pr == "drawing":
                    combos.append((pid, aid, pr))
                elif aid == "copy_slow":
                    combos.append((pid, aid, pr))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    action = f["action"]
    prize = f["prize"]
    return [
        f'Write a short rhyming story about a child named {child.id} and a Xerox machine.',
        f"Tell a cautionary, kind story where {child.id} wants to {action.verb} for someone else.",
        f"Write a gentle rhyming tale that includes the word 'xerox' and ends with a safe choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    prize = f["prize"]
    action = f["action"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Why did {child.id} want to use the Xerox machine?",
            answer=f"{child.id} wanted to make a kind copy so the other person could have one too.",
        ),
        QAItem(
            question=f"What warning did {adult.id} give about the Xerox machine?",
            answer=f"{adult.id} warned that the Xerox could jam or make a mess if they were not careful.",
        ),
        QAItem(
            question=f"What safe thing helped {child.id} make the copy?",
            answer=f"They used {gear.label} and went slowly, so the copy came out clean and neat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a Xerox machine?",
            answer="A Xerox machine is a copier that makes paper copies of pages and pictures.",
        ),
        QAItem(
            question="Why should a copier be used carefully?",
            answer="A copier should be used carefully so the paper does not jam and the pages do not get smudged.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping someone in a caring way and trying to make things better for them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story q&a =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.quiet:
            lines.append(asp.fact("quiet", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("risk", aid, a.mess))
    for prid, pr in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("copyable", prid))
        if pr.fragile:
            lines.append(asp.fact("fragile", prid))
    for gid, g in GEAR:
        lines.append(asp.fact("gear", gid))
    return "\n".join(lines)


ASP_RULES = r"""
safe(Place, Action, Prize) :- affords(Place, Action), copyable(Prize), place(Place), action(Action), prize(Prize).
risky(Action, Prize) :- fragile(Prize), risk(Action, smudge).
risky(Action, Prize) :- risk(Action, jam), prize(Prize).
has_fix(Action) :- gear(_), action(Action).
valid_story(Place, Action, Prize) :- safe(Place, Action, Prize), has_fix(Action).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def explain_rejection() -> str:
    return "(No story: that Xerox setup would not be safe or kind enough to make a clean copy.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming story world about Xerox kindness and caution.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.action is None or c[1] == args.action)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not filtered:
        raise StoryError(explain_rejection())
    place, action, prize = rng.choice(filtered)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIONS[params.action], PRIZES[params.prize], params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [
            StoryParams("copy_room", "copy_fast", "flyer", "Mia", "girl", "mother", "kind"),
            StoryParams("copy_room", "copy_slow", "drawing", "Leo", "boy", "father", "careful"),
            StoryParams("office", "copy_slow", "note", "Nora", "girl", "mother", "gentle"),
        ]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
