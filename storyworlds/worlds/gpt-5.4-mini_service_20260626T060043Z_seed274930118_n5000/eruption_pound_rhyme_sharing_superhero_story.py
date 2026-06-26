#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/eruption_pound_rhyme_sharing_superhero_story.py
===========================================================================================================================

A small superhero-style story world about a child hero, a shared resource,
and a noisy eruption. The story premise is built from a tiny source-tale feel:
a brave helper wants to save the day, but must choose how to share a useful
tool or treat while a volcano rumbles and pounds overhead.

World shape:
- The hero has physical meters: heat, dust, and carry-load.
- The hero and others have emotional memes: courage, worry, and kindness.
- An eruption raises heat and ash.
- A pounding sound can startle the hero and push a scene toward haste.
- Sharing can lower worry, increase kindness, and help the group survive.

The generated stories aim for a child-facing superhero tone:
clear beginning, a state-driven middle turn, and a resolution image proving
what changed.
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
    owner: Optional[str] = None
    held_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"heat": 0.0, "ash": 0.0, "load": 0.0}
        if not self.memes:
            self.memes = {"courage": 0.0, "worry": 0.0, "kindness": 0.0, "rush": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "heroine"}
        male = {"boy", "father", "dad", "man", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    name: str
    feature: str
    safe_zone: bool = False
    can_echo: bool = False


@dataclass
class Event:
    id: str
    kind: str
    verb: str
    gerund: str
    sound: str
    mess: str
    affects: set[str] = field(default_factory=set)


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.ash_level: float = 0.0
        self.heat_level: float = 0.0
        self.sound_level: float = 0.0
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


@dataclass
class StoryParams:
    place: str
    event: str
    shared_item: str
    name: str
    gender: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "city": Location(name="the city square", feature="tall towers", safe_zone=False, can_echo=True),
    "rooftop": Location(name="the rooftop garden", feature="windy railings", safe_zone=False, can_echo=True),
    "cave": Location(name="the lava cave", feature="glowing rocks", safe_zone=False, can_echo=False),
    "schoolyard": Location(name="the schoolyard", feature="bright windows", safe_zone=True, can_echo=True),
}

EVENTS = {
    "eruption": Event(
        id="eruption",
        kind="eruption",
        verb="stop the eruption",
        gerund="stopping the eruption",
        sound="rumbling",
        mess="ash",
        affects={"heat", "ash", "rush"},
    ),
    "pound": Event(
        id="pound",
        kind="pound",
        verb="follow the pounding beat",
        gerund="following the pounding beat",
        sound="pounding",
        mess="sound",
        affects={"rush"},
    ),
}

SHARED_ITEMS = {
    "blanket": {"label": "a warm blanket", "phrase": "a warm blanket", "plural": False},
    "snacks": {"label": "snacks", "phrase": "a bag of snacks", "plural": True},
    "helmet": {"label": "a shiny helmet", "phrase": "a shiny helmet", "plural": False},
    "water": {"label": "water bottles", "phrase": "two cool water bottles", "plural": True},
    "cape": {"label": "a bright cape", "phrase": "a bright cape", "plural": False},
}

GIRL_NAMES = ["Mia", "Luna", "Tess", "Nora", "Ava", "Zoe", "Iris", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Max", "Finn", "Theo", "Sam", "Noah", "Eli"]
TRAITS = ["brave", "quick", "kind", "bright", "bold", "steady"]


class ReasoningWorld(World):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: eruption, pounding, and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--shared-item", choices=SHARED_ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    place = args.place or rng.choice(list(SETTINGS))
    event = args.event or rng.choice(list(EVENTS))
    shared_item = args.shared_item or rng.choice(list(SHARED_ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick = args.sidekick or rng.choice(["robot", "sparrow", "neighbor", "cat"])
    trait = args.trait or rng.choice(TRAITS)

    if event == "eruption" and place == "schoolyard":
        # Schoolyard stories work, but only when the hero uses shared supplies
        # to protect the class and reach the safe zone.
        pass

    return StoryParams(
        place=place,
        event=event,
        shared_item=shared_item,
        name=name,
        gender=gender,
        sidekick=sidekick,
        trait=trait,
    )


def _hero_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def _sidekick_label(kind: str) -> str:
    return {
        "robot": "a little robot",
        "sparrow": "a sparrow friend",
        "neighbor": "a neighbor kid",
        "cat": "a cat sidekick",
    }.get(kind, kind)


def _make_world(params: StoryParams) -> World:
    location = SETTINGS[params.place]
    world = ReasoningWorld(location)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=_hero_type(params.gender),
        label=params.name,
        meters={"heat": 0.0, "ash": 0.0, "load": 0.0},
        memes={"courage": 0.0, "worry": 0.0, "kindness": 0.0, "rush": 0.0},
    ))
    sidekick = world.add(Entity(
        id="sidekick",
        kind="character",
        type="friend",
        label=_sidekick_label(params.sidekick),
        meters={"heat": 0.0, "ash": 0.0, "load": 0.0},
        memes={"courage": 0.0, "worry": 0.0, "kindness": 0.0, "rush": 0.0},
    ))
    item_def = SHARED_ITEMS[params.shared_item]
    shared = world.add(Entity(
        id="shared_item",
        kind="thing",
        type=params.shared_item,
        label=item_def["label"],
        phrase=item_def["phrase"],
        plural=item_def["plural"],
        owner=hero.id,
        shared_with={sidekick.id},
    ))
    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        shared=shared,
        params=params,
    )
    return world


def _apply_eruption(world: World, hero: Entity, sidekick: Entity, shared: Entity) -> None:
    world.heat_level += 1.0
    world.ash_level += 1.0
    hero.meters["heat"] += 1.0
    hero.meters["ash"] += 1.0
    sidekick.meters["ash"] += 1.0
    hero.memes["worry"] += 1.0
    world.fired.add(("eruption", hero.id))
    shared.meters["ash"] += 1.0
    if world.location.can_echo:
        world.sound_level += 1.0


def _apply_pound(world: World, hero: Entity, sidekick: Entity) -> None:
    world.sound_level += 1.0
    hero.memes["rush"] += 1.0
    sidekick.memes["rush"] += 1.0
    world.fired.add(("pound", hero.id))


def _share(world: World, hero: Entity, sidekick: Entity, shared: Entity) -> None:
    hero.memes["kindness"] += 1.0
    sidekick.memes["kindness"] += 1.0
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    sidekick.memes["worry"] = max(0.0, sidekick.memes["worry"] - 1.0)
    shared.shared_with.add(hero.id)
    shared.shared_with.add(sidekick.id)
    hero.meters["load"] = max(0.0, hero.meters["load"] - 1.0)
    sidekick.meters["load"] += 0.5


def tell_world(params: StoryParams) -> World:
    world = _make_world(params)
    hero = world.get(params.name)
    sidekick = world.get("sidekick")
    shared = world.get("shared_item")
    event = EVENTS[params.event]

    world.say(f"{hero.id} was a {params.trait} young superhero with a {event.kind} problem to solve.")
    world.say(f"{hero.pronoun().capitalize()} and {sidekick.label} kept {shared.label} close, because shared tools helped on hard days.")
    world.say(f"At {world.location.name}, the air had {world.location.feature}, and the day felt ready for adventure.")

    world.para()
    if params.event == "eruption":
        world.say(f"Then the mountain gave a loud {event.sound}, and ash began to drift down like gray snow.")
        _apply_eruption(world, hero, sidekick, shared)
        world.say(f"{hero.id} lifted {hero.pronoun('possessive')} chin and said, 'I can help!'")
        world.say(f"But the ash made {hero.pronoun('possessive')} eyes sting, and {sidekick.label} needed the {shared.label} too.")
    else:
        world.say(f"Then the hallway started {event.sound}, like a drum calling everyone to move fast.")
        _apply_pound(world, hero, sidekick)
        world.say(f"{hero.id} listened for the beat, but {hero.pronoun('possessive')} heart kept pounding louder.")
        world.say(f"{sidekick.label} pointed at the {shared.label} and said it should be shared before anyone ran off.")

    world.para()
    if shared.plural:
        share_line = f"Together they shared the {shared.label} so both could use them."
    else:
        share_line = f"Together they shared {shared.label} so both could use it."
    world.say(f"{hero.id} remembered that real heroes do not grab; they share.")
    _share(world, hero, sidekick, shared)
    world.say(share_line)

    if params.event == "eruption":
        world.say(f"{hero.id} used the {shared.label} to protect {hero.pronoun('possessive')} nose and led {sidekick.label} toward the safe path.")
        hero.meters["ash"] = max(0.0, hero.meters["ash"] - 0.5)
        hero.meters["heat"] = max(0.0, hero.meters["heat"] - 0.5)
    else:
        world.say(f"{hero.id} and {sidekick.label} followed the pounding beat all the way to the quiet safe zone.")
        hero.memes["rush"] = max(0.0, hero.memes["rush"] - 1.0)

    world.say(f"In the end, the ash or noise no longer felt huge, because {hero.id} had helped with a calm, shared plan.")
    world.facts.update(event=event, world=world)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    params = f["params"]
    return [
        f'Write a superhero story for a small child that includes the words "{params.event}" and "{params.shared_item}".',
        f"Tell a brave but gentle story about {hero.id}, {params.gender}, who must share a useful item during a {params.event}.",
        f"Write a short story with rhyme-like sound words and a happy sharing ending in {world.location.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    shared: Entity = f["shared"]
    event: Event = f["event"]
    params: StoryParams = f["params"]

    return [
        QAItem(
            question=f"Who is the superhero story about?",
            answer=f"It is about {hero.id}, a {params.trait} young superhero who helps with {event.kind} trouble at {world.location.name}.",
        ),
        QAItem(
            question=f"What did {hero.id} and {sidekick.label} do with the {shared.label}?",
            answer=f"They shared {shared.label} so both of them could use it during the emergency.",
        ),
        QAItem(
            question=f"Why did {hero.id} stay calm when the {event.kind} started?",
            answer=f"{hero.id} stayed calm because sharing the {shared.label} gave {hero.id} and {sidekick.label} a plan, and that made the worry smaller.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} had less worry and more kindness, and the group reached a safer place together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an eruption?",
            answer="An eruption is when a volcano sends out hot rock, ash, or steam very suddenly.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let other people use something too instead of keeping it all for yourself.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a helper character who uses bravery and special tools or powers to protect others.",
        ),
        QAItem(
            question="Why can ash be tricky?",
            answer="Ash can be tricky because it is dusty and can get into eyes, noses, and clothes.",
        ),
        QAItem(
            question="What does a calm plan do in a problem?",
            answer="A calm plan helps everyone know what to do next, which can make a scary moment feel smaller.",
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
    lines.append(f"location={world.location.name} feature={world.location.feature}")
    lines.append(f"ash_level={world.ash_level} heat_level={world.heat_level} sound_level={world.sound_level}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
shared(S) :- shared_item(S).
event(E) :- event_kind(E).
at_risk(H) :- hero(H), eruption_event.
needs_share(H) :- at_risk(H).
calm_plan(H) :- needs_share(H), shared(_).
resolved(H) :- calm_plan(H).
#show resolved/1.
#show at_risk/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for eid in EVENTS:
        lines.append(asp.fact("event_kind", eid))
    for sid in SHARED_ITEMS:
        lines.append(asp.fact("shared_item", sid))
    lines.append(asp.fact("eruption_event"))
    lines.append(asp.fact("hero_name", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1.\n#show at_risk/1."))
    atoms = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = {("at_risk", ("hero",)), ("resolved", ("hero",))}
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python reasoning:")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/1.\n#show at_risk/1."))
    return sorted(set(asp.atoms(model, "resolved")))


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="city", event="eruption", shared_item="helmet", name="Mia", gender="girl", sidekick="robot", trait="brave"),
        StoryParams(place="rooftop", event="pound", shared_item="snacks", name="Leo", gender="boy", sidekick="sparrow", trait="kind"),
        StoryParams(place="schoolyard", event="eruption", shared_item="water", name="Ava", gender="girl", sidekick="neighbor", trait="steady"),
    ]


CURATED = build_curated()


def explain_rejection(place: str, event: str, shared_item: str) -> str:
    if event == "eruption" and place == "schoolyard":
        return "(No story: this combination is too weak unless the schoolyard version includes a shared protective item.)"
    return "(No story: the requested setup does not make a clear superhero problem and sharing turn.)"


def resolve_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    p = StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        event=args.event or rng.choice(list(EVENTS)),
        shared_item=args.shared_item or rng.choice(list(SHARED_ITEMS)),
        name=args.name or rng.choice(GIRL_NAMES if (args.gender or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES),
        gender=args.gender or rng.choice(["girl", "boy"]),
        sidekick=args.sidekick or rng.choice(["robot", "sparrow", "neighbor", "cat"]),
        trait=args.trait or rng.choice(TRAITS),
    )
    return p


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
        print(asp_program("#show resolved/1.\n#show at_risk/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/1.\n#show at_risk/1."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            rng = random.Random(seed)
            params = resolve_from_args(args, rng)
            params.seed = seed
            if args.event == "eruption" and args.place == "schoolyard" and args.shared_item is None:
                raise StoryError(explain_rejection(params.place, params.event, params.shared_item))
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
            header = f"### {p.name}: {p.event} at {p.place} with {p.shared_item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
