#!/usr/bin/env python3
"""
Bedtime storyworld: a little defensive horsie who hears tiny sound effects and
thinks in a soft inner monologue before learning that the dark is not a bully.

Source-tale sketch:
---
At bedtime, Pip the small horsie hears the house creak, the blanket whisper,
and the wind tap the window. Pip is brave during the day, but at night Pip gets
defensive and says, "I'm not scared." Inside, Pip's thoughts wobble. A sleepy
parent notices and offers a lantern, a stuffed star, and a gentle song. Pip
listens to the sounds again, names them one by one, and realizes they are only
the friendly noises of a safe house. Pip relaxes, curls up, and falls asleep
with the soft sound of breathing and the lamp's warm glow.

World model:
- A child-facing bedtime scene with a small horsie protagonist.
- Physical meters: light level, softness, closeness, noise, warmth.
- Emotional memes: defensiveness, worry, comfort, trust, sleepiness.
- Sound effects are narrated as concrete, short sensory beats.
- Inner monologue is used sparingly and stays child-friendly.
- The turn comes from reinterpreting scary noises as safe household sounds.
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

SOUND_KINDS = {
    "creak": "creak",
    "whisper": "whisper",
    "tap": "tap",
    "hum": "hum",
    "rustle": "rustle",
    "snore": "snore",
}


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        horse_types = {"horsie", "horse", "pony"}
        parent_types = {"mother", "father", "mom", "dad"}
        if self.type in horse_types:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in parent_types:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str = "the bedroom"
    bedtime: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ComfortItem:
    id: str
    label: str
    phrase: str
    warmth: float = 0.0
    glow: float = 0.0
    soft: float = 0.0
    kind: str = "thing"


@dataclass
class StoryParams:
    room: str = "bedroom"
    hero_name: str = "Pip"
    parent_name: str = "Mara"
    seed: Optional[int] = None


ROOMS = {
    "bedroom": Room(name="the bedroom", bedtime=True, affords={"creak", "whisper", "rustle", "snore", "hum", "tap"}),
    "nursery": Room(name="the nursery", bedtime=True, affords={"whisper", "rustle", "snore", "hum"}),
    "cabin": Room(name="the little cabin room", bedtime=True, affords={"creak", "tap", "hum", "whisper"}),
}

COMFORT_ITEMS = {
    "lantern": ComfortItem(id="lantern", label="lantern", phrase="a small lantern", warmth=1.0, glow=1.0, soft=0.0, kind="light"),
    "stuffed_star": ComfortItem(id="stuffed_star", label="stuffed star", phrase="a stuffed star", warmth=0.2, glow=0.0, soft=1.0, kind="toy"),
    "blanket": ComfortItem(id="blanket", label="blanket", phrase="a soft blanket", warmth=1.0, glow=0.0, soft=1.0, kind="blanket"),
}

SOUND_REGISTRY = {
    "creak": {
        "sound": "creeeak",
        "source": "the old floorboards",
        "meaning": "the house is settling down to sleep",
        "risk": 1.0,
    },
    "whisper": {
        "sound": "whish-whish",
        "source": "the curtains",
        "meaning": "the air is moving softly near the window",
        "risk": 0.7,
    },
    "tap": {
        "sound": "tap-tap",
        "source": "raindrops on the glass",
        "meaning": "the rain is tapping politely outside",
        "risk": 0.6,
    },
    "hum": {
        "sound": "hmmmm",
        "source": "the night lamp",
        "meaning": "the lamp is humming its tiny warm song",
        "risk": 0.3,
    },
    "rustle": {
        "sound": "ruff-ruff",
        "source": "the blanket",
        "meaning": "the blanket is shifting when someone wiggles underneath it",
        "risk": 0.5,
    },
    "snore": {
        "sound": "snoooore",
        "source": "the parent",
        "meaning": "the grown-up is sleeping close by",
        "risk": 0.4,
    },
}


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, ComfortItem] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.noises: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: ComfortItem) -> ComfortItem:
        self.items[item.id] = item
        return item

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
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.items = copy.deepcopy(self.items)
        w.fired = set(self.fired)
        w.noises = list(self.noises)
        return w


def _narrate_sound(kind: str) -> str:
    return SOUND_REGISTRY[kind]["sound"]


def _r_worry(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes.get("worry", 0.0) >= THRESHOLD and hero.memes.get("defensive", 0.0) >= THRESHOLD:
        sig = ("worry", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append(f"{hero.id} pulled the blanket closer and tried to look tough.")
    return out


def _r_comfort(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes.get("comfort", 0.0) < THRESHOLD:
        return out
    sig = ("comfort", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["defensive"] = max(0.0, hero.memes.get("defensive", 0.0) - 1.0)
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    hero.memes["sleepy"] = hero.memes.get("sleepy", 0.0) + 1.0
    out.append(f"The little horsie stopped bracing for trouble and listened instead.")
    return out


def _r_sleep(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes.get("sleepy", 0.0) < THRESHOLD or hero.memes.get("trust", 0.0) < THRESHOLD:
        return out
    sig = ("sleep", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"The room stayed quiet, and the horsie drifted into sleep.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_worry, _r_comfort, _r_sleep):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sound_effect_line(kind: str) -> str:
    reg = SOUND_REGISTRY[kind]
    return f"{_narrate_sound(kind)} went the {reg['source']}."


def bedtime_detail(room: Room) -> str:
    if room.name == "the nursery":
        return "The nursery was dim and warm, with one tiny lamp glowing like a sleepy firefly."
    if room.name == "the little cabin room":
        return "The little cabin room held a warm quilt, and the wooden walls made the night feel snug."
    return "The bedroom was quiet, and the shadows only looked like blankets folded in half."


def tell(room: Room, hero_name: str = "Pip", parent_name: str = "Mara") -> World:
    world = World(room)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type="horsie",
        label="the little horsie",
        traits=["little", "defensive", "sleepy"],
        memes={"defensive": 1.0, "worry": 0.0, "comfort": 0.0, "trust": 0.0, "sleepy": 0.0},
        meters={"softness": 0.0, "light": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type="mother",
        label=parent_name,
        memes={"gentle": 1.0, "calm": 1.0},
    ))
    lamp = world.add_item(COMFORT_ITEMS["lantern"])
    blanket = world.add_item(COMFORT_ITEMS["blanket"])
    star = world.add_item(COMFORT_ITEMS["stuffed_star"])

    world.say(f"{hero_name} was a little horsie who liked day-time gallops and bedtime songs.")
    world.say(f"But when the house got dark, {hero.pronoun('subject')} got defensive and said, \"I'm fine.\"")
    world.say(f"Inside, {hero.pronoun('subject')} thought, I am not scared... but maybe I am a tiny bit scared.")
    world.para()

    world.say(bedtime_detail(room))
    first_sound = "creak" if "creak" in room.affords else "whisper"
    second_sound = "tap" if "tap" in room.affords else "hum"
    world.noises.extend([first_sound, second_sound, "rustle"])
    world.say(sound_effect_line(first_sound))
    hero.memes["worry"] += 1.0
    hero.memes["defensive"] += 1.0
    world.say(f"{hero_name} held very still and listened harder.")
    world.say(f"Inside, {hero.pronoun('subject')} thought, That sound is too big. What if it is a night monster?")
    world.para()

    world.say(f"{parent.label} came in slowly, so the floor only said a soft hello.")
    world.say(sound_effect_line(second_sound))
    world.say(f"{parent.label} smiled and said, \"Let's name the sounds one by one.\"")
    world.say(f"{parent.label} lifted the lantern, and the room became a cozy golden puddle of light.")
    hero.memes["comfort"] += 1.0
    hero.meters["light"] = 1.0
    lamp.glow = 1.0
    lamp.warmth = 0.5
    world.say(f"Inside, {hero.pronoun('subject')} thought, A little light means I can see the whole room.")
    world.para()

    world.say(f"{parent.label} pointed to the window. \"Tap-tap,\" they said, \"that's only the rain.\"")
    world.say(f"\"Whish-whish,\" they said, \"that's only the curtain.\"")
    world.say(f"\"Hmmm,\" they said, \"that's the lamp singing.\"")
    world.say(f"{hero_name} listened again.")
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
    hero.memes["comfort"] += 1.0
    hero.memes["trust"] += 1.0
    world.say(f"Inside, {hero.pronoun('subject')} thought, Oh. These are just house sounds. They are not mean.")
    world.say(f"{hero_name} hugged the stuffed star and tucked the blanket under {hero.pronoun('possessive')} chin.")
    world.say(f"The blanket made one last rustle, {sound_effect_line('rustle').split(' went the ')[0]}.")
    world.say(f"Then {parent.label} sat nearby and breathed slowly: in... out... in... out...")
    world.say(sound_effect_line("snore"))
    hero.memes["sleepy"] += 1.0
    hero.meters["softness"] = 1.0
    blanket.soft = 1.0
    propagate(world, narrate=True)
    world.say(f"At last, {hero_name} yawned a little horsey yawn and stopped being defensive.")
    world.say(f"{hero_name} closed {hero.pronoun('possessive')} eyes, and the room felt safe and warm.")
    world.facts.update(hero=hero, parent=parent, room=room, lamp=lamp, blanket=blanket, star=star)
    return world


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    room = world.facts["room"]
    qa = [
        QAItem(
            question=f"What kind of little animal was {hero.id} in the bedtime story?",
            answer=f"{hero.id} was a little horsie, and {hero.pronoun('subject')} liked daytime play but got defensive at night.",
        ),
        QAItem(
            question=f"What did {parent.label} do when the night sounds worried {hero.id}?",
            answer=f"{parent.label} came in gently, turned on the lantern, and helped {hero.id} name the sounds one by one.",
        ),
        QAItem(
            question=f"Why did {hero.id} stop feeling so defensive before falling asleep?",
            answer=f"{hero.id} learned that the creaks, taps, whispers, and hum were only safe house sounds in {room.name}, so the worry could settle down.",
        ),
        QAItem(
            question=f"What helped the room feel cozy at the end?",
            answer=f"The lantern glow, the soft blanket, the stuffed star, and the calm breathing all made the room feel cozy and safe.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a creak sound like?",
            answer="A creak is a long, squeaky little house sound, like old wood moving slowly.",
        ),
        QAItem(
            question="Why can a lamp make bedtime feel better?",
            answer="A lamp can make a room less dark, and a little light often helps children feel safer and calmer.",
        ),
        QAItem(
            question="What does it mean to feel defensive?",
            answer="Feeling defensive means trying to protect yourself, even when someone else is not trying to hurt you.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a soft bedtime story about a defensive horsie who hears tiny sound effects in the dark and learns what they mean.',
        'Tell a child-friendly story where a little horsie has an inner monologue, feels defensive, and is comforted by a gentle parent.',
        'Write a bedtime tale in which creaks, taps, whispers, and a warm lamp help a horsie realize the house is safe.',
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)}")
    for i in world.items.values():
        lines.append(f"  {i.id:8} ({i.kind:7}) warmth={i.warmth} glow={i.glow} soft={i.soft}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for kind in SOUND_REGISTRY:
        lines.append(asp.fact("sound", kind))
    for item_id, item in COMFORT_ITEMS.items():
        lines.append(asp.fact("comfort_item", item_id))
        if item.warmth >= 1.0:
            lines.append(asp.fact("warms", item_id))
        if item.glow >= 1.0:
            lines.append(asp.fact("glows", item_id))
        if item.soft >= 1.0:
            lines.append(asp.fact("soft", item_id))
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        for s in sorted(room.affords):
            lines.append(asp.fact("offers_sound", room_id, s))
    return "\n".join(lines)


ASP_RULES = r"""
safe_sound(S) :- sound(S), offers_sound(R, S), room(R).
comfort_item(I) :- comfort_item(I).

calming(I, S) :- comfort_item(I), soft(I), sound(S), S = whisper.
calming(I, S) :- comfort_item(I), glows(I), sound(S), S = hum.
calming(I, S) :- comfort_item(I), warms(I), sound(S), S = rustle.

bedtime_ok(R) :- room(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_sound/1. #show calming/2."))
    facts = set()
    for sym in model:
        if sym.name == "safe_sound":
            facts.add(("safe_sound", sym.arguments[0].name))
        elif sym.name == "calming":
            facts.add(("calming", sym.arguments[0].name, sym.arguments[1].name))
    expected = {
        ("safe_sound", "creak"), ("safe_sound", "whisper"), ("safe_sound", "tap"),
        ("safe_sound", "hum"), ("safe_sound", "rustle"), ("safe_sound", "snore"),
        ("calming", "lantern", "hum"),
        ("calming", "stuffed_star", "whisper"),
        ("calming", "blanket", "rustle"),
    }
    if facts == expected:
        print("OK: clingo gate matches Python reasonableness and comfort facts.")
        return 0
    print("MISMATCH between clingo and expected facts:")
    print("  only in clingo:", sorted(facts - expected))
    print("  only in expected:", sorted(expected - facts))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: a defensive horsie and the safe house sounds.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--name", default="Pip")
    ap.add_argument("--parent", default="Mara")
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
    room = args.room or rng.choice(list(ROOMS))
    return StoryParams(room=room, hero_name=args.name, parent_name=args.parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room], params.hero_name, params.parent_name)
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
        print(asp_program("#show safe_sound/1. #show calming/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for room in ROOMS:
            p = StoryParams(room=room, hero_name=args.name, parent_name=args.parent)
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {sample.params.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
