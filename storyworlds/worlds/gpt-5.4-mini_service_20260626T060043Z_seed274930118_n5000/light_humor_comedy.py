#!/usr/bin/env python3
"""
storyworlds/worlds/light_humor_comedy.py
========================================

A small storyworld about light, funny shadows, and a careful bedtime compromise.

Seed tale:
---
A child loves making silly shadow puppets with a flashlight after dark. But the
bright beam wakes a sleepy sibling and makes bedtime wobble into giggles. A
parent warns that the room is getting too lively for sleep, then offers a softer
light and a new place for the game. The child agrees, and the shadows become
quiet, funny, and just right.

World idea:
---
- Physical meters: brightness, noise, tiredness, mess
- Emotional memes: delight, worry, silliness, conflict, relief
- Light can be too bright, too noisy, or just right depending on the room
- A good compromise turns down the glare without taking away the fun
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

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
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    brightness: float
    noise: float
    weather: str
    keyword: str
    humor: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    reduces_brightness: float = 0.0
    reduces_noise: float = 0.0


@dataclass
class StoryParams:
    activity: str
    gear: str
    name: str
    gender: str
    parent: str
    sibling: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = []
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _mood(entity: Entity, key: str, delta: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + delta


def _stat(entity: Entity, key: str, delta: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + delta


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"(No story: {world.setting.place} cannot support {activity.id}.)")
    _stat(actor, "brightness", activity.brightness)
    _stat(actor, "noise", activity.noise)
    _mood(actor, "silliness", 1.0)
    if narrate:
        world.say(f"{actor.id} wanted to {activity.verb}, and the room got a little brighter.")
        world.say(f"{activity.humor}")


def predict(world: World, actor: Entity, activity: Activity, sibling: Entity) -> dict[str, float | bool]:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    lamp = sim.get("Light")
    return {
        "too_bright": lamp.meters.get("brightness", 0.0) >= 2.0,
        "too_noisy": actor.meters.get("noise", 0.0) >= 1.0,
        "sleep_wobble": sibling.memes.get("sleepy", 0.0) > 0.0
        and lamp.meters.get("brightness", 0.0) >= 2.0,
    }


def setting_detail(activity: Activity) -> str:
    if activity.id == "shadows":
        return "The bedroom wall looked like a stage for squeaky, wiggly shadows."
    if activity.id == "lantern":
        return "The hall was dim, and the corners were waiting for a joke."
    return "The room was quiet enough for a small light to tell a funny story."


def build_world(params: StoryParams) -> World:
    setting = SETTINGS["bedroom"]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    sibling = world.add(Entity(id="Sibling", kind="character", type="baby", label="the baby sibling"))
    lamp = world.add(Entity(id="Light", kind="thing", type="lamp", label="flashlight", phrase="a bright flashlight", owner=hero.id))
    gear = world.add(Entity(id=params.gear, kind="thing", type=params.gear, label=GEAR[params.gear].label, phrase=GEAR[params.gear].phrase, owner=hero.id))

    sibling.memes["sleepy"] = 1.0
    lamp.worn_by = None
    gear.worn_by = hero.id

    activity = ACTIVITIES[params.activity]
    world.facts.update(hero=hero, parent=parent, sibling=sibling, lamp=lamp, gear=gear, activity=activity)

    # Act 1
    world.say(f"{hero.id} was a {params.trait} {params.gender} who loved {activity.gerund}.")
    world.say(f"{activity.humor}")
    world.say(f"{hero.id} especially liked {lamp.phrase} because {activity.keyword} made the walls look funny.")
    world.say(f"At bedtime, {hero.id} and {hero.pronoun('possessive')} {params.parent} were in {world.setting.place}.")
    world.say(setting_detail(activity))

    # Act 2
    _do_activity(world, hero, activity)
    sibling.meters["wakefulness"] = sibling.meters.get("wakefulness", 0.0) + activity.noise
    sibling.memes["wobbly"] = sibling.memes.get("wobbly", 0.0) + (1.0 if activity.brightness > 1.0 else 0.0)

    if predict(world, hero, activity, sibling)["too_bright"]:
        hero.memes["worry"] = hero.memes.get("worry", 0.0)
        _mood(parent, "worry", 1.0)
        world.say(
            f'"That light is turning the room into a joke show," {parent.id} said. '
            f'"It might wake the baby sibling."'
        )
        world.say(f"{hero.id} tried to keep going, but the beam kept bouncing off the wall.")
        _mood(hero, "defiance", 1.0)
        _mood(hero, "conflict", 1.0)
        world.say(f"{hero.id} frowned and tried to {activity.rush}.")
        _mood(parent, "protective", 1.0)
        world.say(f"{parent.id} gently held up a hand and stopped the silliness for a moment.")

    # Act 3
    gear_def = GEAR[params.gear]
    _stat(lamp, "brightness", -gear_def.reduces_brightness)
    _stat(hero, "noise", -gear_def.reduces_noise)
    if gear_def.id == "shade":
        world.say(f'{parent.id} smiled. "How about we use the {gear_def.label} and make the shadows soft?"')
    else:
        world.say(f'{parent.id} smiled. "How about we use the {gear_def.label} and keep the joke gentle?"')
    world.say(f"{hero.id} nodded and {gear_def.prep}.")
    _mood(hero, "relief", 1.0)
    _mood(hero, "joy", 1.0)
    _mood(parent, "relief", 1.0)
    _mood(parent, "delight", 1.0)
    _mood(sibling, "calm", 1.0)
    _mood(hero, "conflict", -1.0)
    world.say(f"Then {hero.id} kept {activity.gerund}, and the light became just right.")
    world.say(f"{hero.id} {gear_def.tail}.")
    world.say(f"The baby sibling stayed sleepy, and the wall still had room for one last silly shadow.")
    world.say(f"Everyone laughed softly, because the room had learned the punchline.")

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"shadows", "lantern", "nightlight"}),
}

ACTIVITIES = {
    "shadows": Activity(
        id="shadows",
        verb="make shadow puppets",
        gerund="making shadow puppets",
        rush="wave the flashlight higher",
        brightness=2.0,
        noise=1.0,
        weather="night",
        keyword="light",
        humor="The shadows looked like a goose wearing a hat, which was somehow funnier than it should have been.",
        tags={"light", "shadow", "night"},
    ),
    "lantern": Activity(
        id="lantern",
        verb="carry a lantern like a tiny explorer",
        gerund="carrying a lantern like a tiny explorer",
        rush="dash down the hall with it",
        brightness=1.5,
        noise=0.5,
        weather="night",
        keyword="light",
        humor="The lantern bobbed like a serious bug trying very hard to be a lamp.",
        tags={"light", "lantern", "night"},
    ),
    "nightlight": Activity(
        id="nightlight",
        verb="watch the nightlight glow",
        gerund="watching the nightlight glow",
        rush="turn the light up too high",
        brightness=1.0,
        noise=0.0,
        weather="night",
        keyword="light",
        humor="The nightlight was so small that it seemed to be whispering, 'I am the boss of bedtime.'",
        tags={"light", "night"},
    ),
}

GEAR = {
    "shade": Gear(
        id="shade",
        label="lamp shade",
        phrase="a lamp shade",
        prep="put the lamp shade back on",
        tail="let the flashlight glow through the shade like a sleepy moon",
        reduces_brightness=1.0,
        reduces_noise=0.0,
    ),
    "blanket": Gear(
        id="blanket",
        label="blanket tent",
        phrase="a blanket tent",
        prep="tucked the flashlight under the blanket tent",
        tail="made a cozy shadow stage under the blanket tent",
        reduces_brightness=0.5,
        reduces_noise=0.5,
    ),
    "dim": Gear(
        id="dim",
        label="dimmer switch",
        phrase="the dimmer switch",
        prep="turned the dimmer switch down a little",
        tail="let the room glow softly instead of blaring like a trumpet",
        reduces_brightness=1.0,
        reduces_noise=0.0,
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Finn"]
TRAITS = ["curious", "playful", "silly", "cheerful", "wiggly"]


def prize_at_risk(activity: Activity) -> bool:
    return activity.brightness >= 1.5 or activity.noise >= 0.5


def select_gear(activity: Activity) -> Optional[Gear]:
    if activity.id == "shadows":
        return GEAR["shade"]
    if activity.id == "lantern":
        return GEAR["dim"]
    if activity.id == "nightlight":
        return GEAR["blanket"]
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            if select_gear(ACTIVITIES[act]):
                out.append((place, act))
    return out


KNOWLEDGE = {
    "light": [("What is light?", "Light is what helps us see things. It can come from the sun, a lamp, a candle, or a flashlight.")],
    "shadow": [("What is a shadow?", "A shadow is a dark shape made when something blocks light.")],
    "night": [("Why do we use lights at night?", "We use lights at night so we can see where we are going and feel safer.")],
    "lantern": [("What is a lantern?", "A lantern is a light that can be carried and used to shine in dark places.")],
    "shade": [("What does a lamp shade do?", "A lamp shade helps soften the light so it feels gentler on your eyes.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    return [
        'Write a short comedy story for a young child about light, shadows, and a bedtime compromise.',
        f"Tell a funny story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about bedtime.",
        "Write a gentle, silly story that ends with the room becoming soft and calm instead of too bright.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, sibling, act, gear = f["hero"], f["parent"], f["sibling"], f["activity"], f["gear"]
    ans1 = f"{hero.id} is a {hero.type} who loves {act.gerund}, and {parent.label} helps keep the baby sibling sleepy."
    ans2 = f"{parent.id} worried because the light was bright enough to wake {sibling.label}."
    ans3 = f"They used the {gear.label} so the light stayed soft and funny instead of too bright."
    return [
        QAItem(question=f"Who is the story about and what does {hero.id} like to do?", answer=ans1),
        QAItem(question=f"Why did {parent.label} worry about the light?", answer=ans2),
        QAItem(question=f"What helped the family keep the fun but calm the room down?", answer=ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for key in ["light", "shadow", "night", "lantern", "shade"]:
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(activity="shadows", gear="shade", name="Mia", gender="girl", parent="mother", sibling="baby sibling", trait="silly"),
    StoryParams(activity="lantern", gear="dim", name="Leo", gender="boy", parent="father", sibling="baby sibling", trait="curious"),
    StoryParams(activity="nightlight", gear="blanket", name="Nora", gender="girl", parent="mother", sibling="baby sibling", trait="playful"),
]


def explain_rejection(activity: Activity) -> str:
    return f"(No story: the {activity.id} idea does not have a believable gentle compromise.)"


ASP_RULES = r"""
activity(A) :- act(A).
gear(G) :- fix(G).

needs_fix(A) :- act(A), bright(A,B), B >= 1.5.
needs_fix(A) :- act(A), noisy(A,N), N >= 0.5.

compatible(A,G) :- act(A), fix(G), reduces_brightness(G,RB), bright(A,B), B > RB.
compatible(A,G) :- act(A), fix(G), reduces_noise(G,RN), noisy(A,N), N > RN.

valid(A,G) :- act(A), needs_fix(A), compatible(A,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for a in ACTIVITIES.values():
        lines.append(asp.fact("act", a.id))
        lines.append(asp.fact("bright", a.id, int(a.brightness * 10)))
        lines.append(asp.fact("noisy", a.id, int(a.noise * 10)))
    for g in GEAR.values():
        lines.append(asp.fact("fix", g.id))
        lines.append(asp.fact("reduces_brightness", g.id, int(g.reduces_brightness * 10)))
        lines.append(asp.fact("reduces_noise", g.id, int(g.reduces_noise * 10)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((a, select_gear(ACTIVITIES[a]).id) for _, a in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: light, humor, and a comedy bedtime compromise.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--sibling", default="baby sibling")
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
    if args.activity and args.gear:
        if select_gear(ACTIVITIES[args.activity]).id != args.gear:
            raise StoryError(explain_rejection(ACTIVITIES[args.activity]))
    acts = [a for a in ACTIVITIES if args.activity is None or a == args.activity]
    if not acts:
        raise StoryError("(No valid combination matches the given options.)")
    act = rng.choice(sorted(acts))
    gear = args.gear or select_gear(ACTIVITIES[act]).id
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(activity=act, gear=gear, name=name, gender=gender, parent=parent, sibling=args.sibling, trait=trait)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
