#!/usr/bin/env python3
"""
storyworlds/worlds/infuriate_infringe_repetition_heartwarming.py
===============================================================

A small, self-contained story world about repeated little actions,
the feelings they stir up, and the warm compromise that can follow.

Seed tale, imagined from the prompt:
---
A child keeps repeating a loud action in a cozy home. The repetition
starts to infringe on someone else's quiet time and infuriates the adult
who is trying to protect a rest, a task, or a tender moment. After a
gentle warning, the child tries again in a softer way. The room calms
down, and the repeated action becomes a sweet shared ritual instead of a
problem.

World model:
---
- Repetition raises sound pressure or interruption.
- If the repeated action happens in a protected quiet zone, it infringes
  on that quiet time.
- That infringement can infuriate the guardian.
- A softer, compatible repetition can preserve the original delight while
  restoring calm.

This world is intentionally narrow: it generates a small set of plausible
heartwarming stories rather than a wide spread of weak variants.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    quiet_zone: bool
    warmth: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    repeat_sound: str
    soft_repeat_sound: str
    disruption: str
    soothed_by: str
    quiet_risk: float = 1.0
    tags: set[str] = field(default_factory=set)


@dataclass
class ComfortItem:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
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
        import copy as _copy

        clone = World(self.room)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _repeat_noise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("repetition", 0.0) < THRESHOLD:
            continue
        sig = ("noise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["sound"] = actor.meters.get("sound", 0.0) + 1
        out.append(f"The repeated sound grew louder with each try.")
    return out


def _infringe_quiet(world: World) -> list[str]:
    out: list[str] = []
    if not world.room.quiet_zone:
        return out
    for actor in world.characters():
        if actor.meters.get("sound", 0.0) < THRESHOLD:
            continue
        sig = ("infringe", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["infringe"] = actor.memes.get("infringe", 0.0) + 1
        out.append("The sound started to infringe on the room's quiet time.")
    return out


def _infuriate_guardian(world: World) -> list[str]:
    out: list[str] = []
    noisy = [a for a in world.characters() if a.memes.get("infringe", 0.0) >= THRESHOLD]
    if not noisy:
        return out
    guardian = world.facts.get("guardian")
    if guardian is None:
        return out
    sig = ("infuriate", guardian.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guardian.memes["infuriate"] = guardian.memes.get("infuriate", 0.0) + 1
    out.append(f"{guardian.label} looked worried and infuriated, because the quiet was being pushed aside.")
    return out


def _soothe(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    guardian = world.facts.get("guardian")
    if hero is None or guardian is None:
        return out
    if hero.memes.get("softened", 0.0) < THRESHOLD:
        return out
    sig = ("soothe", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guardian.memes["infuriate"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    out.append("The room settled again, and the worry drained out of the air.")
    return out


CAUSAL_RULES = [_repeat_noise, _infringe_quiet, _infuriate_guardian, _soothe]


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


def quiet_risk(activity: Activity, room: Room) -> bool:
    return room.quiet_zone and activity.quiet_risk >= 1.0


def select_comfort(activity: Activity) -> Optional[ComfortItem]:
    for item in COMFORT:
        if activity.id in item.guards:
            return item
    return None


def predict_outcome(world: World, hero: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    guardian = sim.facts["guardian"]
    return {
        "infuriated": guardian.memes.get("infuriate", 0.0) >= THRESHOLD,
        "infringe": hero.memes.get("infringe", 0.0) >= THRESHOLD,
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["repetition"] = actor.meters.get("repetition", 0.0) + 1
    actor.memes["delight"] = actor.memes.get("delight", 0.0) + 1
    world.say(f"{actor.label} kept doing it again and again.")
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} was a little {hero.type} who loved repeating favorite things.")


def want_repeat(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved to {activity.verb}, and the repetition made {hero.pronoun('object')} smile.")


def warning(world: World, guardian: Entity, hero: Entity, activity: Activity) -> None:
    guardian.memes["care"] = guardian.memes.get("care", 0.0) + 1
    world.say(
        f'"Please slow down," {guardian.label} said. '
        f'"That many repeats can {activity.disruption}, and I do not want the quiet time to be ruined."'
    )


def deflect(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["restless"] = hero.memes.get("restless", 0.0) + 1
    world.say(f"{hero.label} tried to keep going, but the same sound was starting to bounce around the room.")


def compromise(world: World, guardian: Entity, hero: Entity, activity: Activity, comfort: ComfortItem) -> None:
    hero.memes["softened"] = hero.memes.get("softened", 0.0) + 1
    world.say(
        f'{guardian.label} pointed to the {comfort.label} and smiled. '
        f'"How about we {comfort.prep}?"'
    )
    world.say(
        f"{hero.label} listened, then repeated the tune more softly, "
        f"with tiny pauses that made it feel sweet instead of sharp."
    )
    propagate(world, narrate=True)
    world.say(
        f"They {comfort.tail}, and the room stayed calm enough for everyone to enjoy the moment."
    )


def tell(room: Room, activity: Activity, comfort: ComfortItem, hero_name: str = "Mina",
         hero_type: str = "girl", guardian_type: str = "mother") -> World:
    world = World(room)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, label="Mom" if guardian_type == "mother" else "Dad"))
    world.facts["hero"] = hero
    world.facts["guardian"] = guardian

    introduce(world, hero)
    want_repeat(world, hero, activity)
    world.para()
    world.say(f"It was a {room.warmth} little {room.name}, and the air felt ready for a calm afternoon.")
    _do_activity(world, hero, activity, narrate=True)
    warning(world, guardian, hero, activity)
    deflect(world, hero, activity)
    world.para()
    compromise(world, guardian, hero, activity, comfort)

    world.facts.update(activity=activity, room=room, comfort=comfort)
    return world


ROOMS = {
    "bedroom": Room(name="bedroom", quiet_zone=True, warmth="cozy", affords={"song", "tap", "question"}),
    "nursery": Room(name="nursery", quiet_zone=True, warmth="soft", affords={"song", "question"}),
    "kitchen": Room(name="kitchen", quiet_zone=False, warmth="bright", affords={"tap", "question"}),
    "porch": Room(name="porch", quiet_zone=False, warmth="sunlit", affords={"song", "tap"}),
}

ACTIVITIES = {
    "song": Activity(
        id="song",
        verb="sing the same little song",
        gerund="singing the same little song",
        repeat_sound="la-la-la",
        soft_repeat_sound="laa-laa-laa",
        disruption="make the nap impossible",
        soothed_by="a whisper",
        quiet_risk=1.0,
        tags={"music", "repetition"},
    ),
    "tap": Activity(
        id="tap",
        verb="tap the table over and over",
        gerund="tapping the table over and over",
        repeat_sound="tap-tap-tap",
        soft_repeat_sound="tip-tip-tip",
        disruption="spoil the quiet",
        soothed_by="a pillow",
        quiet_risk=1.0,
        tags={"rhythm", "repetition"},
    ),
    "question": Activity(
        id="question",
        verb="ask the same question again",
        gerund="asking the same question again",
        repeat_sound="again? again?",
        soft_repeat_sound="one more time?",
        disruption="interrupt the reading time",
        soothed_by="a patient answer",
        quiet_risk=1.0,
        tags={"talking", "repetition"},
    ),
}

COMFORT = [
    ComfortItem(
        id="pillow",
        label="a soft pillow",
        phrase="a soft pillow",
        covers={"sound"},
        guards={"tap"},
        prep="tap the pillow instead, like a tiny drummer",
        tail="settled in beside the pillow and tapped only the soft stuffing",
    ),
    ComfortItem(
        id="whisper",
        label="a whisper game",
        phrase="a whisper game",
        covers={"sound"},
        guards={"song", "question"},
        prep="try the song again as a whisper",
        tail="leaned close and shared the whisper like a secret",
    ),
    ComfortItem(
        id="answer_book",
        label="a picture book",
        phrase="a picture book",
        covers={"sound"},
        guards={"question"},
        prep="look at the picture book and ask once, slowly",
        tail="sat together and turned the pages with gentle fingers",
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for room_id, room in ROOMS.items():
        for act_id in room.affords:
            act = ACTIVITIES[act_id]
            if quiet_risk(act, room) and select_comfort(act):
                combos.append((room_id, act_id))
    return combos


@dataclass
class StoryParams:
    room: str
    activity: str
    name: str
    gender: str
    guardian: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Luna", "Ivy", "Ruby", "Nina", "Tess"]
BOY_NAMES = ["Ollie", "Ben", "Theo", "Milo", "Finn", "Jude"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming repetition story world.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father"])
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
    if args.room and args.activity:
        if (args.room, args.activity) not in valid_combos():
            raise StoryError("That repetition would not honestly disturb the room in a story-worthy way.")
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    room_id, act_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["mother", "father"])
    return StoryParams(room=room_id, activity=act_id, name=name, gender=gender, guardian=guardian)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    room = f["room"]
    return [
        f'Write a short heartwarming story for a young child about repetition in a {room.name}.',
        f"Tell a gentle story where {hero.label} keeps {act.gerund} until the repeated sound starts to infringe on quiet time.",
        f"Write a cozy story that uses the words 'infuriate' and 'infringe' without sounding harsh.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    act = f["activity"]
    comfort = f["comfort"]
    room = f["room"]
    return [
        QAItem(
            question=f"What did {hero.label} keep doing in the {room.name}?",
            answer=f"{hero.label} kept {act.gerund}, because the repetition felt fun at first.",
        ),
        QAItem(
            question=f"Why did {guardian.label} get upset?",
            answer=f"{guardian.label} got upset because the repeated sound started to infringe on the room's quiet time and could {act.disruption}.",
        ),
        QAItem(
            question=f"What helped everyone feel better at the end?",
            answer=f"{comfort.label} helped, because it let {hero.label} repeat the action more softly and turned the moment warm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing or saying the same thing again and again.",
        ),
        QAItem(
            question="What does infringe mean?",
            answer="To infringe means to step into someone else's space, time, or comfort in an unwelcome way.",
        ),
        QAItem(
            question="What does infuriate mean?",
            answer="To infuriate means to make someone feel very angry or very upset.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  room quiet_zone: {world.room.quiet_zone}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
repetition(E) :- actor(E), repeats(E).
infringe(E) :- actor(E), repetition(E), quiet_zone.
infuriate(G) :- guardian(G), infringement(E), cares_for(G,E).
resolved(E) :- softened(E), actor(E).
#show repetition/1.
#show infringe/1.
#show infuriate/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        if room.quiet_zone:
            lines.append(asp.fact("quiet_zone", rid))
        for a in sorted(room.affords):
            lines.append(asp.fact("affords", rid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(act.tags):
            lines.append(asp.fact("tag", aid, t))
    for item in COMFORT:
        lines.append(asp.fact("comfort", item.id))
        for g in sorted(item.guards):
            lines.append(asp.fact("guards", item.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show repetition/1.\n#show infringe/1.\n#show infuriate/1."))
    return sorted(set(asp.atoms(model, "repetition")))


def asp_verify() -> int:
    import asp
    ok = True
    py = set(valid_combos())
    if not py:
        print("No valid combos.")
        return 1
    print(f"OK: Python valid_combos() has {len(py)} combinations.")
    try:
        _ = asp.one_model(asp_program("#show repetition/1."))
        print("OK: ASP program is loadable.")
    except Exception as e:
        print(f"ASP error: {e}")
        ok = False
    return 0 if ok else 1


CURATED = [
    StoryParams(room="bedroom", activity="song", name="Mina", gender="girl", guardian="mother"),
    StoryParams(room="nursery", activity="question", name="Ollie", gender="boy", guardian="father"),
    StoryParams(room="kitchen", activity="tap", name="Ruby", gender="girl", guardian="mother"),
]


def generate(params: StoryParams) -> StorySample:
    room = ROOMS[params.room]
    activity = ACTIVITIES[params.activity]
    comfort = select_comfort(activity)
    if comfort is None:
        raise StoryError("No comfort item fits that activity.")
    world = tell(room, activity, comfort, params.name, params.gender, params.guardian)
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show repetition/1.\n#show infringe/1.\n#show infuriate/1.\n#show resolved/1."))
        return
    if args.asp:
        print(asp_program("#show repetition/1.\n#show infringe/1.\n#show infuriate/1.\n#show resolved/1."))
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.activity} in the {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
