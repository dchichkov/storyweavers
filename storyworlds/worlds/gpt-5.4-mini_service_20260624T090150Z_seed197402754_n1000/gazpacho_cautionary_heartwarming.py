#!/usr/bin/env python3
"""
A small storyworld for a cautionary, heartwarming gazpacho tale.

Premise:
- A child loves making gazpacho on a hot day.
- The child wants to carry it outside right away.
- The parent knows gazpacho should stay cold, so they warn the child.
- They choose a cooler and an ice pack, and the soup ends up shared happily.

The world model tracks physical meters like coldness, warmth, and spill risk,
plus emotional memes like excitement, caution, relief, and warmth.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def short(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    outdoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    keeps_cold: bool
    holds: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""

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
        clone.paragraphs = [[]]
        clone.weather = self.weather
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_warm(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "thing":
            continue
        if ent.meter("cold") < THRESHOLD:
            continue
        if world.setting.outdoors and ent.carried_by:
            carrier = world.get(ent.carried_by)
            if carrier.meme("careful") >= THRESHOLD:
                continue
            sig = ("warm", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["warm"] = ent.meter("warm") + 1
            ent.meters["cold"] = max(0.0, ent.meter("cold") - 1)
            out.append(f"The {ent.short} started to lose its cool in the heat.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.kind != "thing" or ent.meter("sloshing") < THRESHOLD:
            continue
        if not ent.carried_by:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The soup nearly tipped, but someone caught it just in time.")
    return out


CAUSAL_RULES = [Rule("warm", _r_warm), Rule("spill", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("That setting does not support this gazpacho story.")
    actor.memes["excitement"] = actor.meme("excitement") + 1
    world.facts["activity_used"] = activity.id
    world.facts["activity_keyword"] = activity.keyword
    propagate(world, narrate=narrate)


def predict(world: World, actor: Entity, activity: Activity, soup_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    soup = sim.get(soup_id)
    return {"warm": soup.meter("warm") >= THRESHOLD, "cold": soup.meter("cold")}


def build_setting() -> Setting:
    return Setting(place="the kitchen", outdoors=False, affords={"make_gazpacho", "carry_outside"})


SETTINGS = {
    "kitchen": Setting(place="the kitchen", outdoors=False, affords={"make_gazpacho"}),
    "porch": Setting(place="the porch", outdoors=True, affords={"carry_outside"}),
    "garden": Setting(place="the garden table", outdoors=True, affords={"carry_outside"}),
}

ACTIVITIES = {
    "make_gazpacho": Activity(
        id="make_gazpacho",
        verb="make gazpacho",
        gerund="making gazpacho",
        rush="dash the bowl outside",
        risk="get warm in the sun",
        weather="hot",
        keyword="gazpacho",
        tags={"gazpacho", "cold", "kitchen"},
    ),
    "carry_outside": Activity(
        id="carry_outside",
        verb="bring it outside",
        gerund="carrying the soup outside",
        rush="run to the table",
        risk="warm up on the porch",
        weather="hot",
        keyword="gazpacho",
        tags={"gazpacho", "sun", "cold"},
    ),
}

CONTAINERS = {
    "bowl": Container(
        id="bowl",
        label="big bowl",
        phrase="a big bowl",
        keeps_cold=False,
        holds={"soup"},
        prep="stir the gazpacho in a big bowl",
        tail="kept the soup in the big bowl",
    ),
    "cooler": Container(
        id="cooler",
        label="small cooler",
        phrase="a small cooler with an ice pack",
        keeps_cold=True,
        holds={"soup"},
        prep="put the gazpacho into a small cooler with an ice pack",
        tail="carried the cooler carefully to the table",
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Max", "Ben"]
TRAITS = ["cheerful", "curious", "gentle", "brave", "patient", "bright"]


@dataclass
class StoryParams:
    place: str
    activity: str
    container: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def story_setup(world: World, hero: Entity, parent: Entity, soup: Entity, container: Entity, activity: Activity) -> None:
    hero.memes["love"] = hero.meme("love") + 1
    world.say(
        f"{hero.id} was a little {hero.traits[0]} {hero.type} who loved cool, bright gazpacho."
    )
    world.say(
        f"One hot day, {hero.id}'s {parent.short} brought home tomatoes, cucumbers, and bread, "
        f"and together they made a bowl of gazpacho."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, because {hero.pronoun('subject')} thought the soup would be perfect for sharing."
    )
    soup.meters["cold"] = 2.0
    soup.carried_by = hero.id
    container.carried_by = hero.id
    world.say(
        f"The soup waited in {container.phrase}, and {hero.id} was proud to carry it."
    )


def warn(world: World, parent: Entity, hero: Entity, soup: Entity, activity: Activity) -> bool:
    pred = predict(world, hero, activity, soup.id)
    if pred["warm"]:
        parent.memes["careful"] = parent.meme("careful") + 1
        world.facts["warning"] = True
        world.say(
            f'"If you take the gazpacho straight into the sun, it will {activity.risk}," '
            f"{hero.pronoun('possessive')} {parent.short} said."
        )
        return True
    return False


def hesitate(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] = hero.meme("worry") + 1
    world.say(
        f"{hero.id} paused. {hero.pronoun().capitalize()} did not want the soup to stop being cool."
    )
    world.say(
        f"Still, {hero.id} really wanted to {activity.verb}, so {hero.pronoun('subject')} held the bowl tightly."
    )


def offer_cooler(world: World, parent: Entity, hero: Entity, soup: Entity, container: Container, activity: Activity) -> None:
    world.say(
        f"{parent.short} smiled and said, 'Let's use {container.phrase} instead.'"
    )
    world.say(
        f"That way, the gazpacho could stay cold while you {activity.verb}."
    )
    hero.memes["relief"] = hero.meme("relief") + 1
    parent.memes["warmth"] = parent.meme("warmth") + 1
    soup.meters["cold"] = soup.meter("cold") + 1
    soup.meters["warm"] = 0.0
    soup.carried_by = hero.id
    world.facts["resolved"] = True
    world.facts["container"] = container.id


def finish(world: World, hero: Entity, parent: Entity, soup: Entity, container: Container, activity: Activity) -> None:
    world.say(
        f"{hero.id} nodded and changed the plan."
    )
    world.say(
        f"They {container.tail}. Soon the gazpacho stayed cool, and everyone ate it with little smiles."
    )
    world.say(
        f"{hero.id} felt proud, because being careful helped the soup taste fresh."
    )


def tell(setting: Setting, activity: Activity, container: Container, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=[trait, "kind"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"{parent_type}"))
    soup = world.add(Entity(id="gazpacho", kind="thing", type="soup", label="gazpacho", phrase="a bowl of gazpacho", owner=hero.id, caretaker=parent.id))
    pack = world.add(Entity(id=container.id, kind="thing", type="container", label=container.label, phrase=container.phrase, owner=hero.id, caretaker=parent.id, plural=container.plural))
    pack.carried_by = hero.id

    story_setup(world, hero, parent, soup, pack, activity)
    world.para()
    if warn(world, parent, hero, soup, activity):
        hesitate(world, hero, activity)
        world.para()
        offer_cooler(world, parent, hero, soup, container, activity)
        finish(world, hero, parent, soup, container, activity)

    world.facts.update(hero=hero, parent=parent, soup=soup, container=container, activity=activity, setting=setting)
    return world


SETTINGS_REGISTRY = SETTINGS
ACTIVITIES_REGISTRY = ACTIVITIES
CONTAINERS_REGISTRY = CONTAINERS


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            if act_id != "carry_outside":
                for container_id in CONTAINERS:
                    if container_id == "cooler":
                        combos.append((place, act_id, container_id))
            else:
                combos.append((place, act_id, "cooler"))
    return combos


def explain_rejection(activity: Activity, container: Container) -> str:
    if activity.id == "make_gazpacho" and container.id == "bowl":
        return "(No story: a plain bowl would not keep gazpacho cold enough for the cautionary turn.)"
    return "(No story: that container does not make a believable, safe gazpacho compromise here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary, heartwarming gazpacho storyworld.")
    ap.add_argument("--place", choices=SETTINGS_REGISTRY)
    ap.add_argument("--activity", choices=ACTIVITIES_REGISTRY)
    ap.add_argument("--container", choices=CONTAINERS_REGISTRY)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.container is None or c[2] == args.container)]
    if not combos:
        raise StoryError("(No valid gazpacho story matches the given options.)")
    place, activity, container = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, container=container, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        "Write a short heartwarming story about a child making gazpacho on a hot day.",
        f"Tell a gentle cautionary story where {hero.id} wants to {act.verb} but learns to keep the soup cold.",
        "Write a simple story that ends with gazpacho being shared safely and happily.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    soup = f["soup"]
    activity = f["activity"]
    container = f["container"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the gazpacho?",
            answer=f"{hero.id} wanted to {activity.verb} because {hero.pronoun('subject')} was excited to share the soup.",
        ),
        QAItem(
            question=f"Why did {parent.short} warn {hero.id} about the gazpacho?",
            answer=f"{parent.short} warned {hero.id} because the soup could {activity.risk} if it went into the hot air too soon.",
        ),
        QAItem(
            question=f"What did they use to keep the gazpacho cold?",
            answer=f"They used {container.phrase} so the gazpacho could stay cool and safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} feeling proud and everyone sharing the gazpacho while it stayed cold.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gazpacho?",
            answer="Gazpacho is a cold soup, often made with tomatoes and other fresh vegetables.",
        ),
        QAItem(
            question="Why do people keep gazpacho cold?",
            answer="People keep gazpacho cold so it stays refreshing and tastes like a cool soup on a hot day.",
        ),
        QAItem(
            question="What does a cooler help with?",
            answer="A cooler helps keep food and drinks cold for a little while.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS_REGISTRY[params.place], ACTIVITIES_REGISTRY[params.activity], CONTAINERS_REGISTRY[params.container], params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
activity(make_gazpacho).
activity(carry_outside).
place(kitchen).
place(porch).
place(garden).

affords(kitchen, make_gazpacho).
affords(porch, carry_outside).
affords(garden, carry_outside).

cold_risk(make_gazpacho).
cold_risk(carry_outside).

compatible(kitchen, make_gazpacho, cooler).
compatible(porch, carry_outside, cooler).
compatible(garden, carry_outside, cooler).

valid(P, A, C) :- affords(P, A), compatible(P, A, C).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        if s.outdoors:
            lines.append(asp.fact("outdoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES_REGISTRY.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for cid, c in CONTAINERS_REGISTRY.items():
        lines.append(asp.fact("container", cid))
        if c.keeps_cold:
            lines.append(asp.fact("keeps_cold", cid))
        for h in sorted(c.holds):
            lines.append(asp.fact("holds", cid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    return 1


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
    StoryParams(place="kitchen", activity="make_gazpacho", container="cooler", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="kitchen", activity="make_gazpacho", container="cooler", name="Leo", gender="boy", parent="father", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (container: {p.container})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
