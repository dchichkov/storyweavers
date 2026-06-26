#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/spine_route_repertoire_sharing_comedy.py
==============================================================================================================

A small story world about a child comic, a bumpy route, a treasured repertoire,
and the silly problem of a book spine that should not be squashed.

Seed tale:
---
Milo loved comedy more than broccoli loved pretending to be soup. He had a little
book of jokes, songs, and funny faces — his repertoire — and he wanted to share it
at the neighborhood show on the other side of town.

On the way, his mom noticed the book's spine was already creaky. "If we stuff it in
your backpack and bounce down the route, the spine may crack," she warned. Milo
wanted to rush ahead anyway, because jokes were funniest when they arrived first.

Then his friend Tia had an idea. "Let's share the repertoire without hauling the
whole book. We can copy the best jokes onto cards and tuck them into a tiny folder."
Milo agreed, and by the time they reached the show, everyone was laughing — even the
book, which got to rest with its spine safe and smug.

World model:
---
Physical state:
    book.spine_health      -- whether the joke book's spine stays sturdy
    cards.orderliness      -- whether the shared repertoire cards stay usable
    bag.bumpiness          -- route bumps can stress the book
Emotional state:
    hero.excitement        -- desire to perform and share
    parent.worry           -- concern about the spine on the route
    hero.defiance          -- if the child insists on carrying the big book
    shared.joy             -- rises when the repertoire is shared kindly
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"              # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    place: str = "the neighborhood"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    supports: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.route: str = ""
        self.facts: dict = {}

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.route = self.route
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_bump_spine(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["bump"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.carried_by != actor.id:
                continue
            if "spine" not in item.meters:
                continue
            sig = ("spine", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["spine"] -= 1
            if item.meters["spine"] < 0:
                item.meters["spine"] = 0
            out.append(f"The route's bumps made {actor.pronoun('possessive')} {item.label} creak.")
    return out


def _r_share_joy(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("Hero")
    friend = world.entities.get("Friend")
    cards = world.entities.get("Cards")
    if not hero or not friend or not cards:
        return out
    if hero.memes["sharing"] < THRESHOLD or cards.meters["ready"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    cards.meters["order"] += 1
    out.append("The repertoire got shared the smart way, and everyone grinned.")
    return out


CAUSAL_RULES = [
    Rule("bump_spine", _r_bump_spine),
    Rule("share_joy", _r_share_joy),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def route_is_risky(activity: Activity, prize: Prize) -> bool:
    return "spine" in activity.tags and prize.label == "joke book"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.keyword in gear.supports and "spine" in gear.guards:
            return gear
    return None


def predict_damage(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "spine": prize.meters["spine"] <= 0,
        "joy": hero.memes["joy"] + sim.entities["Friend"].memes["joy"],
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    actor.meters["bump"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "funny")
    world.say(f"{hero.id} was a little {trait} {hero.type} with a grin that could trip over itself.")


def loves_comedy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_comedy"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved comedy, especially {activity.gerund}, because laughter felt like popcorn for the brain.")


def buys_book(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One bright afternoon, {hero.pronoun('possessive')} {parent.pronoun('subject')} bought {hero.pronoun('object')} {prize.phrase}.")


def loves_book(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.carried_by = hero.id
    prize.meters["spine"] = 2.0
    world.say(f"{hero.id} loved the {prize.label} and carried {prize.it()} everywhere like a tiny treasure chest of giggles.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.route = "the bumpy route to the little show"
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.pronoun('subject')} took {world.route}.")
    world.say(f"The path had little dips, and every dip looked like it wanted to tell a joke of its own.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} {parent.pronoun('subject')} frowned at the wobbling bag.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_damage(world, hero, activity, prize.id)
    if not pred["spine"]:
        return False
    world.facts["predicted_break"] = True
    world.say(f'"If we keep bouncing the {prize.label} down this route, its spine may crack," {parent.pronoun("subject")} said.')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} still wanted to rush ahead, because waiting felt slower than a turtle wearing slippers.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_and_rethink(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["held_back"] += 1
    world.say(f"but {hero.pronoun('possessive')} {parent.pronoun('subject')} gave the bag a gentle stop and said, 'Easy now, little superstar.'")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        plural=gear_def.plural,
    ))
    gear.meters["ready"] = 1.0
    world.say(f"Then a friend named Tia waved a hand and said, 'Let's share the repertoire instead of hauling the whole book.'")
    world.say(f"They decided to {gear_def.prep}.")
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["sharing"] += 1
    hero.memes["defiance"] = 0.0
    prize.meters["spine"] = 2.0
    world.add(Entity(id="Cards", type="thing", label="tiny cue cards", plural=True))
    cards = world.get("Cards")
    cards.meters["ready"] = 1.0
    cards.meters["order"] = 1.0
    world.say(f"{hero.id} laughed, helped copy the best jokes onto tiny cue cards, and tucked them into a small folder.")
    world.say(f"By the time they reached the show, {hero.id} was {activity.gerund}, {prize.label} safe and smug, and the whole repertoire was being shared out loud.")
    world.say(f"Even the {prize.label} seemed pleased to keep its spine straight for once.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Milo", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)

    hero = world.add(Entity(id="Hero", kind="character", type=hero_type, label=hero_name,
                            traits=["little"] + (hero_traits or ["funny", "curious"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    friend = world.add(Entity(id="Friend", kind="character", type="girl", label="Tia", traits=["helpful"]))
    prize = world.add(Entity(id="Book", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id))

    introduce(world, hero)
    loves_comedy(world, hero, activity)
    buys_book(world, parent, hero, prize)
    loves_book(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_and_rethink(world, parent, hero, activity)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, friend=friend, prize=prize, activity=activity,
                       setting=setting, gear=gear_def, resolved=gear_def is not None)
    return world


SETTINGS = {
    "neighborhood": Setting(place="the neighborhood", affords={"route"}),
    "school": Setting(place="the school hall", affords={"route"}),
    "fair": Setting(place="the little street fair", affords={"route"}),
}

ACTIVITIES = {
    "route": Activity(
        id="route",
        verb="take the comedy route to the show",
        gerund="traveling the comedy route",
        rush="dash down the route with the book bouncing",
        risk="spine",
        zone={"spine"},
        keyword="route",
        tags={"route", "spine"},
    ),
}

PRIZES = {
    "joke_book": Prize(
        label="joke book",
        phrase="a joke book full of riddles, skits, and silly faces",
        type="book",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="folder",
        label="a tiny folder",
        prep="copy the best jokes onto cards and use a tiny folder",
        tail="used the tiny folder for the repertoire cards",
        guards={"spine"},
        supports={"route"},
    ),
    Gear(
        id="book_sleeve",
        label="a padded book sleeve",
        prep="slip the joke book into a padded sleeve",
        tail="slipped the joke book into the padded sleeve",
        guards={"spine"},
        supports={"route"},
    ),
]

GIRL_NAMES = ["Tia", "Nora", "Mina", "Bea", "Lena"]
BOY_NAMES = ["Milo", "Otis", "Finn", "Ari", "Pip"]
TRAITS = ["silly", "cheerful", "curious", "playful", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if route_is_risky(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


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


KNOWLEDGE = {
    "spine": [("What is the spine of a book?", "The spine is the stiff part in the middle of a book that helps hold the pages together.")],
    "route": [("What is a route?", "A route is a path or way from one place to another.")],
    "repertoire": [("What is a repertoire?", "A repertoire is a set of songs, jokes, dances, or other things someone knows how to do or perform.")],
    "sharing": [("What does sharing mean?", "Sharing means letting other people use, enjoy, or hear something too.")],
    "comedy": [("What is comedy?", "Comedy is a kind of funny performance or story that tries to make people laugh.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a child-friendly funny story about {hero.label} going along a {act.id} to share a repertoire.',
        f"Tell a comedy story where {hero.label} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about the {prize.label}'s spine.",
        f"Write a short story that includes the words spine, route, repertoire, and sharing, and ends with a happy laugh.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa: list[QAItem] = [
        QAItem(
            question=f"Who wanted to take the comedy route and share the repertoire?",
            answer=f"{hero.label} wanted to take the comedy route and share the repertoire.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried because the bumpy route could crack the {prize.label}'s spine.",
        ),
        QAItem(
            question=f"What did they do instead of carrying the whole book?",
            answer=f"They copied the best jokes onto tiny cue cards and used a tiny folder, so the repertoire could be shared safely.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question="How did the tiny folder help?",
            answer="The tiny folder kept the shared repertoire neat, so the jokes could travel without hurting the book's spine.",
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did {hero.label} feel at the end?",
            answer=f"{hero.label} felt happy and laughed, because the jokes were shared and the book stayed safe.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["activity"].tags) | {"sharing", "comedy", "repertoire", "spine", "route"}
    for key in ["spine", "route", "repertoire", "sharing", "comedy"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="neighborhood", activity="route", prize="joke_book", name="Milo", gender="boy", parent="mother", trait="silly"),
    StoryParams(place="school", activity="route", prize="joke_book", name="Tia", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="fair", activity="route", prize="joke_book", name="Pip", gender="boy", parent="father", trait="bouncy"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return "(No story: this combination does not create a real spine-vs-route problem to solve.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A funny little story world about a route, a spine, a repertoire, and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (route_is_risky(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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


ASP_RULES = r"""
prize_at_risk(A,P) :- route(A), prize(P).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), supports(G,A), guards(G,spine).
valid(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("route", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for a in sorted(g.supports):
            lines.append(asp.fact("supports", g.id, a))
        for k in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
