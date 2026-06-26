#!/usr/bin/env python3
"""
A standalone storyworld for an orchard tale with caution, foreshadowing, and reconciliation
in a gentle rhyming-story style.

The simulated domain:
- a child visits an orchard
- wants to pick ripe fruit too fast
- a warning is foreshadowed by signs in the world
- a small mistake leads to trouble
- a helper and child reconcile and finish safely together

This script follows the Storyweavers world contract.
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


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
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


@dataclass
class Orchard:
    place: str = "the orchard"
    trees: int = 6
    ladders: int = 1
    affords: set[str] = field(default_factory=lambda: {"pick", "climb", "shake"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    risk: str
    zone: set[str]
    keyword: str
    caution: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class HelperGear:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, orchard: Orchard) -> None:
        self.orchard = orchard
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.seen_signs: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
ORCHARDS = {
    "orchard": Orchard(place="the orchard", trees=7, ladders=1),
}

ACTIVITIES = {
    "pick": Activity(
        id="pick",
        verb="pick the apples",
        gerund="picking apples",
        rush="dash to the tallest tree",
        mess="bumps",
        risk="a wobble on the ladder",
        zone={"hands", "feet"},
        keyword="orchard",
        caution="Look before you leap, or down you may creep.",
    ),
    "shake": Activity(
        id="shake",
        verb="shake the branches",
        gerund="shaking branches",
        rush="pull hard on the branch",
        mess="spills",
        risk="fruit raining down too fast",
        zone={"hands", "head"},
        keyword="orchard",
        caution="Shake too wild and the apples may slide.",
    ),
}

PRIZES = {
    "basket": Prize(
        label="basket",
        phrase="a bright woven basket",
        type="basket",
        region="hands",
    ),
    "hat": Prize(
        label="hat",
        phrase="a sun hat with a ribbon",
        type="hat",
        region="head",
    ),
}

HELPERS = {
    "crate": HelperGear(
        id="crate",
        label="a low wooden crate",
        prep="set up a low wooden crate",
        tail="stood together on the crate and reached the apples safely",
    ),
    "basket_step": HelperGear(
        id="basket_step",
        label="a steady basket step",
        prep="bring over a steady basket step",
        tail="used the step to pick fruit without any fright",
    ),
}

NAMES_GIRL = ["Mia", "Luna", "Nora", "Ivy", "Ruby", "Ella"]
NAMES_BOY = ["Leo", "Finn", "Theo", "Max", "Owen", "Eli"]
TRAITS = ["careful", "curious", "brave", "gentle", "bright", "spry"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonable world constraints
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_helper(activity: Activity, prize: Prize) -> Optional[HelperGear]:
    if activity.id == "pick" and prize.region == "hands":
        return HELPERS["crate"]
    if activity.id == "shake" and prize.region == "head":
        return HELPERS["basket_step"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, orchard in ORCHARDS.items():
        for act_id, act in ACTIVITIES.items():
            for prize_id, prize in PRIZES.items():
                if place == "orchard" and prize_at_risk(act, prize) and select_helper(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} would not put {prize.label} at risk, "
            f"so the caution would feel forced.)"
        )
    return (
        f"(No story: there is no helpful orchard fix for {prize.phrase} and "
        f"{activity.gerund}; the compromise would not fit the risk.)"
    )


# ---------------------------------------------------------------------------
# Rhyming narration helpers
# ---------------------------------------------------------------------------
def rhyme_opening(hero: Entity, trait: str) -> str:
    return f"{hero.id} was a {trait} child with a smile that shone bright, who loved the orchard by day and by light."


def rhyme_activity(activity: Activity) -> str:
    return {
        "pick": "The apples looked rosy, the apples looked sweet, and tiny red fruit lined the branches like treats.",
        "shake": "The leaves made a whisper, the leaves made a song, but shaking too hard can go awkward and wrong.",
    }[activity.id]


def rhyme_warning(activity: Activity, prize: Prize) -> str:
    return (
        f'"{activity.caution}" said the helper, "for that is the key; '
        f"if you rush with {prize.label}, a spill there may be."
    )


def rhyme_resolution(hero: Entity, helper_name: str, activity: Activity, prize: Prize) -> str:
    return (
        f"Then {hero.id} and the helper made up with a grin, and {helper_name} let {hero.id} begin. "
        f"They worked with a rhythm, both steady and neat, and {prize.label} stayed ready and safe to eat."
    )


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def warn_with_foreshadowing(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity) -> bool:
    world.seen_signs.append("windy_leaves")
    world.say(
        f"The leaves kept on rustling, the ladder leaned near, and the helper said softly, 'Be careful, dear.'"
    )
    world.say(rhyme_warning(activity, prize))
    return True


def misstep(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["impulse"] = hero.memes.get("impulse", 0) + 1
    hero.meters["wobble"] = hero.meters.get("wobble", 0) + 1
    world.say(f"But {hero.id} grew eager and gave a quick tug, then {activity.rush}, too speedy and smug.")


def reconcile(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["regret"] = hero.memes.get("regret", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    hero.memes["peace"] = 1
    helper.memes["peace"] = 1
    world.say(f"{hero.id} took a deep breath and gave a small sigh. '{helper.id}, I'm sorry,' came softly nearby.")
    world.say(f"{helper.id} smiled back and said, 'No harm was done; let's solve this together and have some fun.'")


def finish(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity, helper_gear: HelperGear) -> None:
    world.say(f"They {helper_gear.prep}, then went up with delight; {helper_gear.tail}.")
    world.say(
        f"So {hero.id} went on {activity.gerund}, with {prize.label} held steady and bright, "
        f"and the orchard felt joyful from morning to night."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    orchard = ORCHARDS[params.place]
    world = World(orchard)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Helper", kind="character", type="adult", label="the helper"))
    prize = world.add(Entity(id="Prize", type=params.prize, label=params.prize, phrase=PRIZES[params.prize].phrase))
    helper_gear = select_helper(ACTIVITIES[params.activity], PRIZES[params.prize])

    if helper_gear is None:
        raise StoryError("This storyworld only builds stories when the helper's fix truly matches the risk.")

    # Act 1
    world.say(rhyme_opening(hero, params.trait))
    world.say(rhyme_activity(ACTIVITIES[params.activity]))
    world.say(f"The orchard was ready, with branches that bent and a path through the green.")
    world.para()

    # Act 2
    world.say(f"One day at {orchard.place}, {hero.id} wanted to {ACTIVITIES[params.activity].verb}.")
    warn_with_foreshadowing(world, hero, helper, ACTIVITIES[params.activity], prize)
    misstep(world, hero, ACTIVITIES[params.activity])
    world.say(
        f"The helper held up a hand, not harsh but just right, for caution can save you from a tumble in sight."
    )
    world.para()

    # Act 3
    reconcile(world, hero, helper)
    finish(world, hero, helper, ACTIVITIES[params.activity], prize, helper_gear)

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        activity=ACTIVITIES[params.activity],
        helper_gear=helper_gear,
        place=orchard.place,
        trait=params.trait,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short rhyming story for a small child about an orchard, caution, and a happy ending that includes "{f["place"]}".',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but learns to slow down so {prize.label} stays safe.",
        f"Write a cautionary rhyming tale about an orchard where a child and helper reconcile after a small mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["helper_gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the orchard?",
            answer=f"{hero.id} wanted to {act.verb}."
        ),
        QAItem(
            question=f"Why did the helper warn {hero.id} to slow down?",
            answer=f"The helper warned {hero.id} because {act.caution.lower()} The orchard had a ladder and branches that could make a quick move risky."
        ),
        QAItem(
            question=f"How did {hero.id} and the helper make things right?",
            answer=f"They apologized, forgave each other, and used {gear.label} so they could keep going safely."
        ),
        QAItem(
            question=f"What stayed safe by the end of the story?",
            answer=f"{prize.label.capitalize()} stayed safe and ready while {hero.id} and {helper.label} finished together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orchard?",
            answer="An orchard is a place where fruit trees grow together, so people can pick apples, pears, or other fruit."
        ),
        QAItem(
            question="Why should a child be careful on a ladder?",
            answer="A ladder can be helpful, but a child should be careful because moving too fast can make it wobble."
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who had a small problem say sorry, forgive each other, and feel friendly again."
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is when a story gives little clues that something important may happen soon."
        ),
        QAItem(
            question="Why is caution useful?",
            answer="Caution helps people notice danger early and choose a safer way to do something."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
risk(A, P) :- activity(A), prize(P), zone(A, R), region(P, R).
fix(A, P) :- risk(A, P), helper(H), helps(H, A, P).
valid_story(Place, A, P) :- orchard(Place), affords(Place, A), risk(A, P), fix(A, P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for oid in ORCHARDS:
        lines.append(asp.fact("orchard", oid))
        for act in sorted(ORCHARDS[oid].affords):
            lines.append(asp.fact("affords", oid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(act.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, prize.region))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        if hid == "crate":
            lines.append(asp.fact("helps", hid, "pick", "basket"))
        if hid == "basket_step":
            lines.append(asp.fact("helps", hid, "shake", "hat"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return asp_valid_stories()


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: ASP and Python agree on {len(py)} valid stories.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only python:", sorted(py - clingo))
    print("only asp:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Orchard rhyming storyworld with caution and reconciliation.")
    ap.add_argument("--place", choices=ORCHARDS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not prize_at_risk(act, pr) or select_helper(act, pr) is None:
            raise StoryError(explain_rejection(act, pr))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or ("crate" if activity == "pick" else "basket_step")
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  seen signs: {world.seen_signs}")
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


CURATED = [
    StoryParams(place="orchard", activity="pick", prize="basket", name="Mia", gender="girl", helper="crate", trait="careful"),
    StoryParams(place="orchard", activity="shake", prize="hat", name="Leo", gender="boy", helper="basket_step", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for s in stories:
            print("  ", s)
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
