#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/enroll_controversy_magic_sound_effects_moral_value.py
======================================================================================

A standalone story world for a tiny superhero tale about a child trying to enroll
in a hero club while a controversy erupts around flashy magic and loud sound
effects. The moral-value turn is that the hero learns to use powers to help others,
not to show off.

The world is intentionally small and classical:
- a hero candidate, a cautious friend, and an adult leader
- a club enrollment decision
- a magical trick that can be used responsibly or selfishly
- sound effects that make the moment feel big
- a controversy beat that is resolved by a moral choice

The prose is state-driven: the physical meters and emotional memes change as the
story progresses, and the ending image proves what changed.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Club:
    id: str
    name: str
    motto: str
    place: str
    sparkle_need: str
    sound_need: str
    moral_need: str


@dataclass
class Power:
    id: str
    name: str
    label: str
    effect: str
    safe: bool = True
    showy: bool = False


@dataclass
class Controversy:
    id: str
    label: str
    cause: str
    wrong_reason: str
    right_reason: str


@dataclass
class Resolution:
    id: str
    title: str
    success: str
    lesson: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_attention(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["showing_off"] >= THRESHOLD and ("attention", "hero") not in world.fired:
        world.fired.add(("attention", "hero"))
        hero.memes["thrill"] += 1
        out.append("__attention__")
    return out


def _r_controversy(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.meters["showing_off"] >= THRESHOLD and friend.memes["worry"] >= THRESHOLD:
        sig = ("controversy", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["embarrassment"] += 1
            friend.memes["concern"] += 1
            world.get("crowd").meters["buzz"] += 1
            out.append("__controversy__")
    return out


def _r_moral_shift(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["realization"] >= THRESHOLD and ("moral", hero.id) not in world.fired:
        world.fired.add(("moral", hero.id))
        hero.memes["pride"] += 1
        hero.meters["showing_off"] = 0.0
        return ["__moral__"]
    return []


CAUSAL_RULES = [Rule("attention", "social", _r_attention),
                Rule("controversy", "social", _r_controversy),
                Rule("moral", "social", _r_moral_shift)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reason_gate(club: Club, power: Power, controversy: Controversy) -> bool:
    return power.safe and club.moral_need and controversy.cause


def would_enroll(hero: Entity, mentor: Entity, power: Power) -> bool:
    return hero.memes["resolve"] + (1 if power.safe else 0) >= mentor.memes["trust"]


def predict_story(world: World, power: Power) -> dict:
    sim = world.copy()
    _use_power(sim, power, narrate=False)
    return {
        "controversy": sim.get("crowd").meters["buzz"] >= THRESHOLD,
        "moral_shift": sim.get("hero").memes["realization"] >= THRESHOLD,
    }


def _use_power(world: World, power: Power, narrate: bool = True) -> None:
    hero = world.get("hero")
    if power.showy:
        hero.meters["showing_off"] += 1
        hero.meters["sparkle"] += 1
    else:
        hero.meters["sparkle"] += 1
    hero.memes["hope"] += 1
    if narrate:
        world.say(f"{hero.id} used {power.label}, and the air felt brighter.")


def opening(world: World, hero: Entity, friend: Entity, club: Club) -> None:
    hero.memes["hope"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {friend.id} hurried to {club.place}. "
        f"{hero.id} wanted to enroll in the {club.name}."
    )
    world.say(
        f"The club's motto was simple: {club.motto}. The room already smelled like excitement."
    )


def temptation(world: World, hero: Entity, power: Power, club: Club) -> None:
    hero.meters["showing_off"] += 1
    hero.memes["thrill"] += 1
    world.say(
        f'{hero.id} lifted {power.label} and grinned. "This will look amazing," {hero.pronoun()} said.'
    )
    world.say(
        f"Then {hero.id} made a loud {power.effect} sound effect, and every head turned."
    )


def warn(world: World, friend: Entity, hero: Entity, controversy: Controversy) -> None:
    friend.memes["worry"] += 1
    friend.memes["concern"] += 1
    world.say(
        f'{friend.id} bit {friend.pronoun("possessive")} lip. "{hero.id}, the club is already'
        f" having a controversy about {controversy.label}. People will think you're showing off."'
    )


def public_reaction(world: World) -> None:
    propagate(world, narrate=False)
    if world.get("crowd").meters["buzz"] >= THRESHOLD:
        world.say(
            "The crowd started whispering. Some kids clapped, but others frowned and stepped back."
        )
        world.say("For a moment, the whole room felt split in two.")
    else:
        world.say("The crowd stayed quiet, waiting to see what kind of hero would speak next.")


def mentor_turn(world: World, mentor: Entity, hero: Entity, controversy: Controversy) -> None:
    mentor.memes["trust"] += 1
    world.say(
        f'{mentor.label_word.capitalize()} raised a hand and said, "A real hero cares about why a power is used."'
    )
    world.say(
        f'"{controversy.right_reason}," {mentor.id} said, "and that is the kind of choice this club wants."'
    )


def moral_choice(world: World, hero: Entity, resolution: Resolution, power: Power) -> None:
    hero.memes["realization"] += 1
    hero.meters["showing_off"] = 0.0
    world.say(
        f"{hero.id}'s face softened. {hero.pronoun().capitalize()} lowered {hero.pronoun('possessive')} hands and nodded."
    )
    world.say(
        f'"You were right," {hero.id} said. "{resolution.lesson}"'
    )
    world.say(
        f"{hero.id} used {power.label} again, but this time it helped the other kids line up safely."
    )
    world.say(
        f"The magic sparkled like a tiny star, and the loud sound effects became cheerful instead of boastful."
    )


def ending(world: World, hero: Entity, friend: Entity, club: Club, resolution: Resolution) -> None:
    hero.memes["pride"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"In the end, {hero.id} was enrolled in the {club.name}. {resolution.success}."
    )
    world.say(
        f"{hero.id} and {friend.id} walked out smiling, with the crowd buzzing about kindness instead of controversy."
    )


def tell(club: Club, power: Power, controversy: Controversy, resolution: Resolution,
         hero_name: str = "Maya", hero_gender: str = "girl",
         friend_name: str = "Finn", friend_gender: str = "boy",
         mentor_gender: str = "woman") -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type=hero_gender, role="candidate"))
    hero.id = hero_name
    friend = world.add(Entity("friend", kind="character", type=friend_gender, role="friend"))
    friend.id = friend_name
    mentor = world.add(Entity("mentor", kind="character", type=mentor_gender, role="leader", label="the mentor"))
    crowd = world.add(Entity("crowd", kind="thing", type="crowd", label="the crowd"))

    hero.memes["resolve"] = 1.0
    mentor.memes["trust"] = 1.0
    mentor.memes["wisdom"] = 1.0

    opening(world, hero, friend, club)
    world.para()
    temptation(world, hero, power, club)
    warn(world, friend, hero, controversy)
    public_reaction(world)
    world.para()
    mentor_turn(world, mentor, hero, controversy)
    moral_choice(world, hero, resolution, power)
    ending(world, hero, friend, club, resolution)

    world.facts.update(
        hero=hero, friend=friend, mentor=mentor, crowd=crowd,
        club=club, power=power, controversy=controversy, resolution=resolution,
        enrolled=True, controversial=hero.meters["showing_off"] >= THRESHOLD,
    )
    return world


CLUBS = {
    "starlight": Club("starlight", "Starlight Club", "Use your powers to protect, not to brag.",
                      "the old community hall", "sparkle", "sound", "moral"),
    "skyguard": Club("skyguard", "Skyguard Squad", "Help first, shine second.",
                     "the rooftop room", "glow", "boom", "moral"),
}

POWERS = {
    "magic_beam": Power("magic_beam", "magic beam", "magic beam", "a bright magic beam", safe=True, showy=True),
    "glow_shield": Power("glow_shield", "glow shield", "glow shield", "a round glow shield", safe=True, showy=False),
    "wind_whisper": Power("wind_whisper", "wind whisper", "wind whisper", "a soft whoosh of wind", safe=True, showy=False),
    "star_spark": Power("star_spark", "star spark", "star spark", "a shower of star sparks", safe=True, showy=True),
}

CONTROVERSIES = {
    "showoff": Controversy("showoff", "showing off magic", "the power looked too flashy",
                           "people thought the magic was only for applause",
                           "heroes should use power to help first"),
    "noise": Controversy("noise", "too much sound effects", "the boom was louder than the work",
                         "the sound effects made the room nervous",
                         "sound effects should never hide the kindness"),
}

RESOLUTIONS = {
    "help": Resolution("help", "The club approved the enrollment", "The mentor handed over a shiny badge",
                       "a hero should use power to help, not to impress"),
    "repair": Resolution("repair", "The room felt calm again", "The kids nodded and the line moved forward",
                         "the best magic is the kind that serves others"),
}

GIRL_NAMES = ["Maya", "Lena", "Zoe", "Ava", "Nora", "Ruby"]
BOY_NAMES = ["Finn", "Noah", "Eli", "Theo", "Owen", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for c in CLUBS:
        for p in POWERS:
            for x in CONTROVERSIES:
                if reason_gate(CLUBS[c], POWERS[p], CONTROVERSIES[x]):
                    combos.append((c, p, x))
    return combos


@dataclass
class StoryParams:
    club: str
    power: str
    controversy: str
    resolution: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    mentor_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero-style story world about enrollment, controversy, magic, sound effects, and moral value.")
    ap.add_argument("--club", choices=CLUBS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--controversy", choices=CONTROVERSIES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--mentor-gender", choices=["woman", "man"])
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


def explain_rejection(club: Club, power: Power, controversy: Controversy) -> str:
    return f"(No story: {power.name} is not a reasonable fit for this controversy, or the club's moral lesson would not be credible.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.club and args.power and args.controversy:
        if not reason_gate(CLUBS[args.club], POWERS[args.power], CONTROVERSIES[args.controversy]):
            raise StoryError(explain_rejection(CLUBS[args.club], POWERS[args.power], CONTROVERSIES[args.controversy]))
    combos = [c for c in valid_combos()
              if (args.club is None or c[0] == args.club)
              and (args.power is None or c[1] == args.power)
              and (args.controversy is None or c[2] == args.controversy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    club, power, controversy = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(RESOLUTIONS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in (BOY_NAMES if friend_gender == "boy" else GIRL_NAMES) if n != hero_name])
    mentor_gender = args.mentor_gender or rng.choice(["woman", "man"])
    return StoryParams(club, power, controversy, resolution, hero_name, hero_gender, friend_name, friend_gender, mentor_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    club = f["club"]
    return [
        f'Write a superhero story for a young child that includes the words "enroll" and "controversy".',
        f"Tell a story where {hero.id} wants to enroll in the {club.name} but a controversy starts over flashy magic and loud sound effects.",
        f"Write a gentle superhero tale with magic, sound effects, and a moral value lesson about choosing help over showing off.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    club = f["club"]
    controversy = f["controversy"]
    resolution = f["resolution"]
    return [
        QAItem("What did the hero want to do?", f"{hero.id} wanted to enroll in the {club.name}."),
        QAItem("What was the controversy about?", f"The controversy was about {controversy.label}, because people worried the magic was too flashy and noisy."),
        QAItem("How did the story end?", f"{hero.id} learned the moral lesson, used the power to help, and got enrolled in the {club.name}."),
        QAItem(f"Why did {friend.id} worry?", f"{friend.id} worried because {controversy.right_reason}. That made {friend.id} speak up before the crowd got even noisier."),
        QAItem("What moral value was taught?", f"The story taught that a hero should use power to help others instead of showing off, and that kindness matters more than applause."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem("What is enrollment?", "Enrollment is when someone officially joins a group, class, or club."),
        QAItem("What is a controversy?", "A controversy is a disagreement that makes people argue or feel unsure about what is right."),
        QAItem("What are sound effects?", "Sound effects are extra sounds, like booms or whooshes, that make a story feel dramatic."),
        QAItem("What is moral value?", "Moral value means choosing what is kind, fair, and right, even when another choice looks cooler."),
    ]
    if f["power"].showy:
        out.append(QAItem("Can magic be flashy?", "Yes. Magic can look flashy, but a good hero still has to use it wisely."))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(C, P, X) :- club(C), power(P), controversy(X), safe(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CLUBS:
        lines.append(asp.fact("club", cid))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        if p.safe:
            lines.append(asp.fact("safe", pid))
    for xid in CONTROVERSIES:
        lines.append(asp.fact("controversy", xid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            club=None, power=None, controversy=None, resolution=None,
            hero_name=None, hero_gender=None, friend_name=None, friend_gender=None,
            mentor_gender=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(CLUBS[params.club], POWERS[params.power], CONTROVERSIES[params.controversy], RESOLUTIONS[params.resolution],
                 params.hero_name, params.hero_gender, params.friend_name, params.friend_gender, params.mentor_gender)
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
    StoryParams("starlight", "magic_beam", "showoff", "help", "Maya", "girl", "Finn", "boy", "woman"),
    StoryParams("skyguard", "glow_shield", "noise", "repair", "Lena", "girl", "Noah", "boy", "man"),
    StoryParams("starlight", "star_spark", "showoff", "help", "Eli", "boy", "Zoe", "girl", "woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
