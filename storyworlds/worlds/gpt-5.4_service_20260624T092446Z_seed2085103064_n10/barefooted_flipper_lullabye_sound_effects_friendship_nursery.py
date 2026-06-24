#!/usr/bin/env python3
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    bedtime: bool = True


@dataclass
class SoundEffect:
    id: str
    verb: str
    loud_line: str
    soft_line: str
    kind: str
    with_prop: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    guards: set[str]
    offer: str
    action: str
    tail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendGift:
    id: str
    label: str
    phrase: str
    type: str
    detail: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_startle(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    room = world.get("room")
    if friend.meters["sleepy"] < THRESHOLD or room.meters["noise"] < THRESHOLD:
        return []
    sig = ("startle", int(room.meters["noise"]), int(friend.meters["sleepy"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["startle"] += 1
    friend.meters["rest"] -= 1
    hero.memes["concern"] += 1
    return [f"{friend.id} blinked and tucked the blanket close, because the room had grown too noisy for bedtime."]


def _r_lullabye(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["care"] < THRESHOLD or world.facts.get("sang_lullabye") is not True:
        return []
    sig = ("lullabye",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["calm"] += 1
    friend.meters["rest"] += 2
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    return [f"The soft lullabye settled over them, and the room felt friendly and still."]


RULES = [
    Rule("startle", _r_startle),
    Rule("lullabye", _r_lullabye),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def comfort_matches(sound: SoundEffect, comfort: Comfort) -> bool:
    return sound.kind in comfort.guards


def predict_too_noisy(world: World, sound: SoundEffect) -> bool:
    sim = world.copy()
    room = sim.get("room")
    friend = sim.get("friend")
    room.meters["noise"] += 1
    friend.meters["sleepy"] += 1
    propagate(sim, narrate=False)
    return friend.memes["startle"] >= THRESHOLD


def opening_line(hero: Entity, place: str, trait: str) -> str:
    return f"In {place}, {hero.id} was a little {trait} {hero.type} who liked to make small evenings sparkle."


def introduce(world: World, hero: Entity, friend: Entity, gift: FriendGift) -> None:
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    world.say(opening_line(hero, world.setting.place, trait))
    world.say(
        f"{hero.pronoun('subject').capitalize()} padded about barefooted on the rug, "
        f"and {friend.id}, {hero.pronoun('possessive')} friend, sat waiting with {gift.phrase}."
    )
    world.say(f"The toy had {gift.detail}, and that made both children smile.")


def friendship_beat(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{hero.id} and {friend.id} liked being together at bedtime, because each one made the other feel brave and cozy."
    )


def bedtime(world: World, friend: Entity) -> None:
    friend.meters["sleepy"] += 1
    room = world.get("room")
    room.meters["dim"] += 1
    world.say(
        f"The lamp grew low, the blanket grew warm, and sleepy time tiptoed into the room."
    )


def wants_show(world: World, hero: Entity, sound: SoundEffect, gift: FriendGift) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"But {hero.id} still wanted to {sound.verb} and make a tiny sea-show with {gift.label}."
    )
    world.say(f'"{sound.loud_line}!" {hero.pronoun("subject")} whispered first, just to hear the sound effects bounce.')


def loud_show(world: World, hero: Entity, friend: Entity, sound: SoundEffect, gift: FriendGift) -> None:
    room = world.get("room")
    room.meters["noise"] += 1
    hero.memes["joy"] += 1
    world.facts["loud_sound"] = sound.loud_line
    world.say(
        f"Then {hero.pronoun('subject')} tried it bigger, {sound.with_prop}, and the room answered, "
        f'"{sound.loud_line}!"'
    )
    propagate(world, narrate=True)


def friend_reacts(world: World, friend: Entity, sound: SoundEffect) -> None:
    if friend.memes["startle"] >= THRESHOLD:
        world.say(
            f'{friend.id} rubbed {friend.pronoun("possessive")} eyes and said, '
            f'"I like your sea-show, but that sound is too jumpy for my sleepy ears."'
        )


def offer_soft_plan(world: World, hero: Entity, friend: Entity, sound: SoundEffect, comfort: Comfort) -> None:
    hero.memes["care"] += 1
    world.say(
        f"{hero.id} looked at {friend.id}, then at the toy, and remembered friendship before fuss."
    )
    world.say(
        f'"Then let us {comfort.offer}," said {hero.id}. "We can keep the story and make it soft."'
    )


def soft_show(world: World, hero: Entity, friend: Entity, sound: SoundEffect, comfort: Comfort, gift: FriendGift) -> None:
    room = world.get("room")
    room.meters["noise"] = 0
    world.facts["sang_lullabye"] = True
    world.facts["soft_sound"] = sound.soft_line
    world.say(
        f"They {comfort.action}, and soon {gift.label} moved in a gentler way: "
        f'"{sound.soft_line}," sang {hero.id}.'
    )
    world.say(
        f"{comfort.tail} The sound effects turned into a lullabye, soft as a moonbeam on milk."
    )
    propagate(world, narrate=True)


def closing(world: World, hero: Entity, friend: Entity, gift: FriendGift) -> None:
    world.say(
        f"In the end, {friend.id} leaned close to {gift.label}, and {hero.id} stayed nearby, smiling with quiet pride."
    )
    world.say(
        f"Two friends listened to the last tiny hush, and bedtime tucked them in."
    )


def tell(setting: Setting, sound: SoundEffect, comfort: Comfort, gift_cfg: FriendGift,
         hero_name: str, hero_type: str, friend_name: str, friend_type: str,
         hero_trait: str, friend_trait: str) -> World:
    if sound.id not in setting.affords:
        raise StoryError(f"{setting.place} does not fit the sound game '{sound.id}'.")
    if not comfort_matches(sound, comfort):
        raise StoryError(
            f"{comfort.label} cannot honestly soften the '{sound.id}' sound; the bedtime fix would not work."
        )

    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name,
                            traits=["little", hero_trait]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name,
                              traits=["little", friend_trait]))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    gift = world.add(Entity(id="gift", kind="thing", type=gift_cfg.type, label=gift_cfg.label,
                            phrase=gift_cfg.phrase, owner="hero"))

    world.facts["hero_name"] = hero_name
    world.facts["friend_name"] = friend_name
    world.facts["hero_trait"] = hero_trait
    world.facts["friend_trait"] = friend_trait

    introduce(world, hero, friend, gift_cfg)
    friendship_beat(world, hero, friend)

    world.para()
    bedtime(world, friend)
    wants_show(world, hero, sound, gift_cfg)
    loud_show(world, hero, friend, sound, gift_cfg)
    friend_reacts(world, friend, sound)

    world.para()
    offer_soft_plan(world, hero, friend, sound, comfort)
    soft_show(world, hero, friend, sound, comfort, gift_cfg)
    closing(world, hero, friend, gift_cfg)

    world.facts.update(
        hero=hero,
        friend=friend,
        sound=sound,
        comfort=comfort,
        gift=gift_cfg,
        setting=setting,
        predicted_too_noisy=predict_too_noisy(world, sound),
        resolved=True,
    )
    return world


SETTINGS = {
    "nursery": Setting(place="the nursery", affords={"flipper_pat", "wave_stomp", "shell_rattle", "whisper_whoosh"}),
    "bedroom": Setting(place="the bedroom", affords={"flipper_pat", "wave_stomp", "whisper_whoosh"}),
    "moon_nook": Setting(place="the moonlit reading nook", affords={"flipper_pat", "shell_rattle", "whisper_whoosh"}),
}

SOUNDS = {
    "flipper_pat": SoundEffect(
        id="flipper_pat",
        verb="pat the quilt like a seal on a shore",
        loud_line="pat-pat-plap",
        soft_line="pat... pat... hush",
        kind="impact",
        with_prop="tapping the quilt with the toy's flipper",
        keyword="flipper",
        tags={"sound", "flipper"},
    ),
    "wave_stomp": SoundEffect(
        id="wave_stomp",
        verb="make wave sounds with barefooted feet",
        loud_line="splash-stomp, splash-stomp",
        soft_line="swish... swish...",
        kind="impact",
        with_prop="padding and stomping with barefooted feet beside the bed",
        keyword="barefooted",
        tags={"sound", "barefooted"},
    ),
    "shell_rattle": SoundEffect(
        id="shell_rattle",
        verb="shake a shell cup like little sea bells",
        loud_line="chik-chik-chik",
        soft_line="chik... hush... chik",
        kind="rattle",
        with_prop="shaking a tiny shell cup over the blanket",
        keyword="shell",
        tags={"sound"},
    ),
    "whisper_whoosh": SoundEffect(
        id="whisper_whoosh",
        verb="whoosh a scarf like a moonlit tide",
        loud_line="whooosh-swish",
        soft_line="whoo... shh...",
        kind="air",
        with_prop="floating a blue scarf through the air",
        keyword="lullabye",
        tags={"sound", "lullabye"},
    ),
}

COMFORTS = {
    "pillow_stage": Comfort(
        id="pillow_stage",
        label="a pillow stage",
        guards={"impact"},
        offer="put the puppet on a pillow stage",
        action="laid the toy on a pillow and used only soft taps",
        tail="The pillow drank the bumping sound before it could run around the room.",
        tags={"bedtime"},
    ),
    "humming_lap": Comfort(
        id="humming_lap",
        label="a humming lap",
        guards={"rattle", "air"},
        offer="sit close and hum together",
        action="sat knee to knee and wrapped the sound inside a shared hum",
        tail="Their humming lap kept the sound close and gentle.",
        tags={"lullabye"},
    ),
    "blanket_boat": Comfort(
        id="blanket_boat",
        label="a blanket boat",
        guards={"impact", "air"},
        offer="make a blanket boat for the toy",
        action="folded the blanket into a little boat and let the toy rock there",
        tail="The blanket boat turned every bump into a soft bobbing sway.",
        tags={"friendship", "lullabye"},
    ),
}

GIFTS = {
    "seal": FriendGift(
        id="seal",
        label="the seal puppet",
        phrase="a soft seal puppet with a shiny flipper",
        type="puppet",
        detail="one silver flipper that flashed when it waved",
        tags={"flipper"},
    ),
    "penguin": FriendGift(
        id="penguin",
        label="the penguin puppet",
        phrase="a round penguin puppet with a velvet flipper",
        type="puppet",
        detail="a velvet flipper stitched in midnight blue",
        tags={"flipper"},
    ),
    "duck": FriendGift(
        id="duck",
        label="the duck toy",
        phrase="a sleepy duck toy with a little flipper-shaped wing",
        type="toy",
        detail="a funny flipper-like wing that wobbled when it turned",
        tags={"flipper"},
    ),
}

GIRL_NAMES = ["Molly", "Nina", "Tess", "Lila", "Daisy", "Poppy", "May"]
BOY_NAMES = ["Ollie", "Finn", "Jude", "Toby", "Milo", "Ned", "Ben"]
TRAITS = ["gentle", "merry", "curious", "bright", "kind", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for sound_id in setting.affords:
            sound = SOUNDS[sound_id]
            for comfort_id, comfort in COMFORTS.items():
                if comfort_matches(sound, comfort):
                    out.append((place, sound_id, comfort_id))
    return sorted(out)


@dataclass
class StoryParams:
    place: str
    sound: str
    comfort: str
    gift: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    hero_trait: str
    friend_trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Nursery Rhyme style story for a very young child that includes the words "barefooted", "flipper", and "lullabye".',
        f"Tell a gentle bedtime story set in {f['setting'].place} where friendship turns lively sound effects into a soft song.",
        f"Write a tiny story about two friends, a sea puppet with a flipper, and a bedtime problem solved by making the sounds softer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    sound = f["sound"]
    comfort = f["comfort"]
    gift = f["gift"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who are the friends in the story in {setting.place}?",
            answer=(
                f"The friends are {hero.label} and {friend.label}. They spend bedtime together in "
                f"{setting.place} with {gift.phrase}."
            ),
        ),
        QAItem(
            question=f"Why did the first sound effects become a problem?",
            answer=(
                f"The first sound effects were too lively for bedtime. {friend.label} was already sleepy, "
                f"so the louder room made {friend.pronoun('object')} blink and hold the blanket close."
            ),
        ),
        QAItem(
            question=f"What was {hero.label} doing when the room got too noisy?",
            answer=(
                f"{hero.label} wanted to {sound.verb}. While making the sea-show, {hero.pronoun('subject')} "
                f"used {gift.label} and the sound came out as '{f['loud_sound']}'."
            ),
        ),
        QAItem(
            question=f"How did friendship help the children fix the bedtime problem?",
            answer=(
                f"Friendship helped because {hero.label} noticed that {friend.label} needed a gentler kind of play. "
                f"They chose {comfort.label}, kept the story, and turned the noise into a lullabye instead."
            ),
        ),
        QAItem(
            question=f"How did the story end after they used {comfort.label}?",
            answer=(
                f"After they used {comfort.label}, the sound changed to '{f['soft_sound']}' and the room grew calm. "
                f"{friend.label} felt cozy, and the two friends ended the night together in peace."
            ),
        ),
    ]


KNOWLEDGE = {
    "flipper": [
        (
            "What is a flipper?",
            "A flipper is a flat, wide limb that helps some animals, like seals and penguins, move through water."
        )
    ],
    "barefooted": [
        (
            "What does barefooted mean?",
            "Barefooted means your feet are bare, with no shoes or socks on them."
        )
    ],
    "lullabye": [
        (
            "What is a lullabye?",
            "A lullabye is a soft, gentle song that helps someone feel calm and sleepy."
        )
    ],
    "sound": [
        (
            "What are sound effects?",
            "Sound effects are noises people make to help a story feel real, like a whoosh for wind or a splash for waves."
        )
    ],
    "friendship": [
        (
            "How can friendship help at bedtime?",
            "Friendship can help at bedtime when friends notice each other's feelings and choose a kinder, calmer way to play."
        )
    ],
    "bedtime": [
        (
            "Why do people use quiet voices at bedtime?",
            "People use quiet voices at bedtime because soft sounds help resting bodies and sleepy minds stay calm."
        )
    ],
}
KNOWLEDGE_ORDER = ["flipper", "barefooted", "lullabye", "sound", "friendship", "bedtime"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"sound", "friendship", "bedtime"}
    sound = world.facts["sound"]
    gift = world.facts["gift"]
    if sound.id == "wave_stomp":
        tags.add("barefooted")
    if sound.id == "whisper_whoosh" or "lullabye" in sound.tags:
        tags.add("lullabye")
    if "flipper" in gift.tags or "flipper" in sound.tags:
        tags.add("flipper")
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            for q, a in KNOWLEDGE[key]:
                out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="nursery",
        sound="flipper_pat",
        comfort="pillow_stage",
        gift="seal",
        hero_name="Molly",
        hero_gender="girl",
        friend_name="Toby",
        friend_gender="boy",
        hero_trait="merry",
        friend_trait="gentle",
    ),
    StoryParams(
        place="bedroom",
        sound="wave_stomp",
        comfort="blanket_boat",
        gift="penguin",
        hero_name="Finn",
        hero_gender="boy",
        friend_name="Lila",
        friend_gender="girl",
        hero_trait="bright",
        friend_trait="kind",
    ),
    StoryParams(
        place="moon_nook",
        sound="shell_rattle",
        comfort="humming_lap",
        gift="duck",
        hero_name="Poppy",
        hero_gender="girl",
        friend_name="Ned",
        friend_gender="boy",
        hero_trait="curious",
        friend_trait="merry",
    ),
    StoryParams(
        place="nursery",
        sound="whisper_whoosh",
        comfort="blanket_boat",
        gift="seal",
        hero_name="Ollie",
        hero_gender="boy",
        friend_name="May",
        friend_gender="girl",
        hero_trait="kind",
        friend_trait="bright",
    ),
]


def explain_rejection(sound: SoundEffect, comfort: Comfort) -> str:
    return (
        f"(No story: {comfort.label} does not truly soften the '{sound.id}' sound. "
        f"A bedtime fix must make the sound effects gentle enough for a lullabye mood.)"
    )


ASP_RULES = r"""
compatible(S, C) :- sound_kind(S, K), comfort_guards(C, K).
valid(P, S, C) :- affords(P, S), compatible(S, C).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for sid in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, sid))
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("sound_kind", sid, sound.kind))
    for cid, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for k in sorted(comfort.guards):
            lines.append(asp.fact("comfort_guards", cid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        checked = 0
        for place, sound, comfort in sorted(py)[: min(10, len(py))]:
            params = StoryParams(
                place=place,
                sound=sound,
                comfort=comfort,
                gift="seal",
                hero_name="Molly",
                hero_gender="girl",
                friend_name="Toby",
                friend_gender="boy",
                hero_trait="kind",
                friend_trait="gentle",
            )
            generate(params)
            checked += 1
        print(f"Exercised {checked} generated stories.")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    if py - cl:
        print(" only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme bedtime stories about sound effects, friendship, and a soft lullabye."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="emit curated set")
    ap.add_argument("--trace", action="store_true", help="show world model")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list ASP valid combos")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sound and args.comfort:
        sound = SOUNDS[args.sound]
        comfort = COMFORTS[args.comfort]
        if not comfort_matches(sound, comfort):
            raise StoryError(explain_rejection(sound, comfort))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.sound is None or c[1] == args.sound)
        and (args.comfort is None or c[2] == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid bedtime combination matches the given options.)")

    place, sound_id, comfort_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    gift = args.gift or rng.choice(sorted(GIFTS))
    return StoryParams(
        place=place,
        sound=sound_id,
        comfort=comfort_id,
        gift=gift,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        hero_trait=rng.choice(TRAITS),
        friend_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        SOUNDS[params.sound],
        COMFORTS[params.comfort],
        GIFTS[params.gift],
        params.hero_name,
        params.hero_gender,
        params.friend_name,
        params.friend_gender,
        params.hero_trait,
        params.friend_trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sound, comfort) combos:\n")
        for place, sound, comfort in combos:
            print(f"  {place:10} {sound:14} {comfort}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.friend_name}: {p.sound} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
