#!/usr/bin/env python3
"""
A small nursery-rhyme story world about a pompon, a rabid rumor, and a dungeon,
with friendship and inner monologue driving the turn.
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
    friend: Optional[str] = None
    location: str = ""
    carrying: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    aura: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    risk: str
    region: str


@dataclass
class EventCfg:
    id: str
    verb: str
    gerund: str
    worry: str
    danger: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.inner_voice: list[str] = []

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.inner_voice = list(self.inner_voice)
        return clone


def simple_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def is_risky(event: EventCfg, obj: ObjectCfg) -> bool:
    return obj.region in event.zone


def select_safe_help(event: EventCfg, obj: ObjectCfg) -> Optional[str]:
    for aid, gear in HELPS.items():
        if event.id in gear.fixes and obj.region in gear.covers:
            return aid
    return None


def predict(world: World, hero: Entity, event: EventCfg, obj_id: str) -> dict:
    sim = world.copy()
    _do_event(sim, sim.get(hero.id), event, narrate=False)
    obj = sim.get(obj_id)
    return {"fright": obj.meters.get("fright", 0.0), "mended": obj.meters.get("safe", 0.0)}


def _do_event(world: World, hero: Entity, event: EventCfg, narrate: bool = True) -> None:
    if event.id not in world.setting.affords:
        return
    hero.meters[event.id] = hero.meters.get(event.id, 0.0) + 1.0
    hero.memes["spark"] = hero.memes.get("spark", 0.0) + 1.0
    if narrate:
        world.say(f"{hero.name_or_label()} did the {event.gerund} in the {world.setting.place}.")
    if event.id == "dungeon":
        hero.memes["shiver"] = hero.memes.get("shiver", 0.0) + 1.0
    if event.id == "rabid":
        hero.memes["alarm"] = hero.memes.get("alarm", 0.0) + 1.0


def whisper_inner_monologue(world: World, hero: Entity, event: EventCfg, obj: Entity) -> None:
    line = (
        f'"If I go to the {world.setting.place}, will my {obj.label} be safe?" '
        f'{hero.name_or_label()} wondered.'
    )
    world.inner_voice.append(line)
    world.say(line)


def introduce(world: World, hero: Entity, friend: Entity, obj: Entity) -> None:
    world.say(
        f"Little {hero.name_or_label()} had a soft pompon and a dear friend named {friend.name_or_label()}."
    )
    world.say(
        f"The pompon was bright and round, and {hero.name_or_label()} loved it like a tiny moon."
    )
    world.say(
        f"{friend.name_or_label()} loved it too, for good friends share the things they treasure."
    )


def rhyme_setup(world: World, hero: Entity, friend: Entity, event: EventCfg, obj: Entity) -> None:
    world.para()
    world.say(
        f"One day, by the old {world.setting.place}, the air felt strange and the stones felt gray."
    )
    world.say(
        f"{hero.name_or_label()} wanted to {event.verb}, but {hero.pronoun('possessive')} heart beat fast."
    )
    whisper_inner_monologue(world, hero, event, obj)


def warn(world: World, friend: Entity, hero: Entity, event: EventCfg, obj: Entity) -> bool:
    pred = predict(world, hero, event, obj.id)
    if not is_risky(event, obj):
        return False
    world.facts["predicted"] = pred
    if event.id == "rabid":
        world.say(
            f'"The rabid tale is wild," said {friend.name_or_label()}, "and it may make your {obj.label} feel sad."'
        )
    else:
        world.say(
            f'"Mind the dungeon gloom," said {friend.name_or_label()}, "for the dark may trouble your {obj.label}."'
        )
    return True


def inner_thought(world: World, hero: Entity, event: EventCfg, obj: Entity) -> None:
    if event.id == "dungeon":
        text = (
            f'"Brave or not brave, I can still walk slow," {hero.name_or_label()} thought, '
            f'"and keep my {obj.label} close."'
        )
    else:
        text = (
            f'"If the wild thing rushes near, I must not drop my {obj.label}," '
            f'{hero.name_or_label()} thought.'
        )
    world.say(text)


def turn_friendship(world: World, friend: Entity, hero: Entity, event: EventCfg, obj: Entity) -> Optional[str]:
    help_id = select_safe_help(event, obj)
    if help_id is None:
        return None
    help_cfg = HELPS[help_id]
    helper = world.add(Entity(id=help_id, type="thing", label=help_cfg.label, phrase=help_cfg.phrase))
    helper.owner = hero.id
    helper.carrying = True
    if predict(world, hero, event, obj.id)["fright"] > THRESHOLD:
        helper.carrying = False
        del world.entities[help_id]
        return None
    world.say(
        f"{friend.name_or_label()} sang, 'Come now, chum, let's use the {helper.label} and keep the pompon calm.'"
    )
    return help_id


def resolve(world: World, hero: Entity, friend: Entity, event: EventCfg, obj: Entity, help_id: str) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["brave"] = hero.memes.get("brave", 0.0) + 1.0
    hero.memes["fear"] = 0.0
    world.say(
        f"So {hero.name_or_label()} held the {obj.label} with care, and {friend.name_or_label()} stayed near."
    )
    world.say(
        f"With friendship as a lantern bright, they went through the {world.setting.place} in the hush of night."
    )
    world.say(
        f"In the end, the pompon stayed soft and safe, and {hero.name_or_label()} smiled like a star."
    )


def tell(setting: Setting, event: EventCfg, obj_cfg: ObjectCfg, hero_name: str, hero_type: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type="friend", label=friend_name))
    obj = world.add(Entity(id="pompon", type="thing", label=obj_cfg.label, phrase=obj_cfg.phrase, owner=hero.id, location="arms"))

    introduce(world, hero, friend, obj)
    rhyme_setup(world, hero, friend, event, obj)
    warn(world, friend, hero, event, obj)
    inner_thought(world, hero, event, obj)
    help_id = turn_friendship(world, friend, hero, event, obj)
    world.para()
    if help_id:
        resolve(world, hero, friend, event, obj, help_id)
    world.facts.update(hero=hero, friend=friend, obj=obj, event=event, help_id=help_id, setting=setting)
    return world


SETTINGS = {
    "moonpath": Setting(place="moonpath", aura="soft", affords={"dungeon", "rabid"}),
    "old_gate": Setting(place="old gate", aura="gray", affords={"dungeon"}),
    "hillroad": Setting(place="hillroad", aura="windy", affords={"rabid", "dungeon"}),
}

EVENTS = {
    "rabid": EventCfg(
        id="rabid",
        verb="follow the rabid rumor",
        gerund="following a rabid rumor",
        worry="wild and sharp",
        danger="tremble",
        zone={"heart", "hands"},
        tags={"rabid"},
    ),
    "dungeon": EventCfg(
        id="dungeon",
        verb="step into the dungeon",
        gerund="stepping into the dungeon",
        worry="dark and echoing",
        danger="shiver",
        zone={"heart", "hands"},
        tags={"dungeon"},
    ),
}

OBJECTS = {
    "pompon": ObjectCfg(label="pompon", phrase="a soft round pompon", risk="fright", region="heart"),
}

HELPS = {
    "lantern": {"label": "lantern", "phrase": "a little lantern", "covers": {"heart", "hands"}, "fixes": {"dungeon"}},
    "ribbon": {"label": "ribbon", "phrase": "a bright ribbon", "covers": {"heart"}, "fixes": {"rabid"}},
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Poppy", "Tess", "Willa", "Miri", "Clara"]
BOY_NAMES = ["Theo", "Bram", "Jules", "Rowan", "Finn", "Ned", "Owen", "Toby"]


@dataclass
class StoryParams:
    place: str
    event: str
    obj: str
    name: str
    gender: str
    friend: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    event = f["event"]
    return [
        f'Write a nursery-rhyme-style story about "{hero.name_or_label()}", a {event.id} worry, and a pompon.',
        f"Tell a gentle story in which {hero.name_or_label()} and {f['friend'].name_or_label()} use friendship to face the {f['setting'].place}.",
        f"Write a short story with inner monologue and a happy turn, using the word 'pompon'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, event, obj = f["hero"], f["friend"], f["event"], f["obj"]
    help_id = f.get("help_id")
    qa = [
        QAItem(
            question=f"Who carried the pompon in the story?",
            answer=f"{hero.name_or_label()} carried the pompon carefully, and {friend.name_or_label()} stayed close by.",
        ),
        QAItem(
            question=f"What did {hero.name_or_label()} worry about in the {f['setting'].place}?",
            answer=f"{hero.name_or_label()} worried that the {event.id} trouble and the dark place might upset the pompon.",
        ),
        QAItem(
            question=f"What did the inner monologue sound like for {hero.name_or_label()}?",
            answer=f"The inner monologue was a quiet thought about keeping the pompon safe and walking slowly with a brave heart.",
        ),
    ]
    if help_id:
        qa.append(
            QAItem(
                question=f"How did friendship help {hero.name_or_label()}?",
                answer=f"Friendship helped because {friend.name_or_label()} brought the {help_id} and stayed near, so the pompon could remain safe.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pompon?",
            answer="A pompon is a soft, round tuft, often seen on hats or toys, and it can feel fluffy in a child's hand.",
        ),
        QAItem(
            question="What does friendship do in a hard moment?",
            answer="Friendship helps by making a child feel less alone, calmer, and braver when something seems scary.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice inside a person's mind where they think their own thoughts.",
        ),
        QAItem(
            question="What is a dungeon?",
            answer="A dungeon is a dark underground room or place with stone walls, often used in old stories and castles.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(E,O) :- event(E), object(O), zone(E,R), region(O,R).
safe_help(H,E,O) :- help(H), fixes(H,E), covers(H,R), region(O,R), event(E), object(O).
valid_story(P,E,O,G) :- place(P), event(E), object(O), gender(G), risk(E,O), safe_help(_,E,O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        for e in sorted(s.affords):
            lines.append(asp.fact("affords", sid, e))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        for z in sorted(e.zone):
            lines.append(asp.fact("zone", eid, z))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("region", oid, o.region))
    for hid, h in HELPS.items():
        lines.append(asp.fact("help", hid))
        for c in sorted(h["covers"]):
            lines.append(asp.fact("covers", hid, c))
        for f in sorted(h["fixes"]):
            lines.append(asp.fact("fixes", hid, f))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, s in SETTINGS.items():
        for event_id in s.affords:
            event = EVENTS[event_id]
            for obj_id, obj in OBJECTS.items():
                if is_risky(event, obj) and select_safe_help(event, obj):
                    combos.append((place, event_id, obj_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set((a, b, c) for (a, b, c, _g) in asp_valid_stories())
    if py == asps:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - asps))
    print("only asp:", sorted(asps - py))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about pompon, rabid rumor, dungeon, friendship, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--obj", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.event and args.obj:
        ev, obj = EVENTS[args.event], OBJECTS[args.obj]
        if not (is_risky(ev, obj) and select_safe_help(ev, obj)):
            raise StoryError("No story: this event does not create a reasonable risk-and-fix shape.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.event is None or c[1] == args.event)
              and (args.obj is None or c[2] == args.obj)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, event, obj = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or simple_name(gender, rng)
    friend = args.friend or rng.choice(["Pip", "Moss", "June", "Sunny", "Bells", "Penny"])
    return StoryParams(place=place, event=event, obj=obj, name=name, gender=gender, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], EVENTS[params.event], OBJECTS[params.obj], params.name, "girl" if params.gender == "girl" else "boy", params.friend)
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
    StoryParams(place="moonpath", event="dungeon", obj="pompon", name="Mina", gender="girl", friend="Pip"),
    StoryParams(place="hillroad", event="rabid", obj="pompon", name="Theo", gender="boy", friend="June"),
    StoryParams(place="old_gate", event="dungeon", obj="pompon", name="Lila", gender="girl", friend="Moss"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
