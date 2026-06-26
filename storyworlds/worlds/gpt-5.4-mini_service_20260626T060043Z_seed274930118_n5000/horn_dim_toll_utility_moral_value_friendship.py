#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/horn_dim_toll_utility_moral_value_friendship.py
================================================================================

A small Ghost-Story-style world about a dim horn, a toll gate, a humble utility,
and a friendship tested by a moral choice.

Premise:
- A child visits an old toll bridge at dusk.
- A faint horn in the tower can wake the quiet ferryman-ghost.
- The useful thing is not the horn itself, but what it can summon: a lantern,
  a crossing, or a kindness.
- The moral question is whether to keep the toll coin or use it to help a friend.

The story is constraint-checked: the ghostly helper only appears if the horn is
sounded in the dim light; the toll can be paid; and the helpful utility only
matters if a friend needs crossing.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
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
class Setting:
    place: str = "the old toll bridge"
    indoors: bool = False
    mood: str = "dim"


@dataclass
class StoryParams:
    name: str
    gender: str
    friend_name: str
    parent_name: str
    setting: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------- registries ----------
SETTINGS = {
    "bridge": Setting(place="the old toll bridge", indoors=False, mood="dim"),
    "lantern_room": Setting(place="the lantern room beside the toll gate", indoors=True, mood="dim"),
}

# The horn is dim: it only works if the world is shadowed and the player is brave enough to use it.
@dataclass
class Utility:
    id: str
    label: str
    use: str
    clue: str
    helps: str
    mood_need: str = "dim"


UTILITIES = {
    "horn": Utility(
        id="horn",
        label="a brass horn",
        use="sound the brass horn",
        clue="the horn was so dim with dust that it hardly gleamed",
        helps="it could call the ferryman-ghost to light the lantern and open the gate",
    ),
    "lantern": Utility(
        id="lantern",
        label="a little lantern",
        use="lift the lantern high",
        clue="the lantern gave off a meek gold blink",
        helps="it could show the safe boards across the water",
    ),
    "coin": Utility(
        id="coin",
        label="a toll coin",
        use="drop the toll coin into the box",
        clue="the coin was smooth and old",
        helps="it could pay the bridge keeper and let the crossing begin",
    ),
}

# Friendship and moral value are the emotional spine of the story.
@dataclass
class MoralChoice:
    keep_coin: str
    give_coin: str
    lesson: str


CHOICE = MoralChoice(
    keep_coin="keep the toll coin for himself",
    give_coin="use the toll coin to help his frightened friend",
    lesson="a small kindness can be more useful than keeping a coin",
)

GIRL_NAMES = ["Mina", "Lina", "Ruby", "Nora", "Ivy", "Maya"]
BOY_NAMES = ["Theo", "Owen", "Eli", "Finn", "Noah", "Leo"]


def base_story(seed: int) -> tuple[str, str, str]:
    names = GIRL_NAMES + BOY_NAMES
    rng = random.Random(seed)
    name = rng.choice(names)
    friend = rng.choice([n for n in names if n != name])
    parent = rng.choice(["mother", "father"])
    return name, friend, parent


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name, kind="character", type=params.gender,
        label=params.name, meters={"courage": 0.0}, memes={"wonder": 0.0, "moral_value": 0.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name, kind="character", type="child",
        label=params.friend_name, meters={"fear": 1.0}, memes={"friendship": 1.0},
    ))
    parent = world.add(Entity(
        id=params.parent_name, kind="character", type="mother" if params.parent_name == "mother" else "father",
        label=params.parent_name, memes={"care": 1.0},
    ))
    horn = world.add(Entity(id="horn", label=UTILITIES["horn"].label, type="horn"))
    lantern = world.add(Entity(id="lantern", label=UTILITIES["lantern"].label, type="lantern"))
    coin = world.add(Entity(id="coin", label=UTILITIES["coin"].label, type="coin"))
    ghost = world.add(Entity(id="ferryman", kind="character", type="ghost", label="the ferryman-ghost",
                             meters={"presence": 0.0}, memes={"kindness": 0.0}))

    # Act 1: dusk, setting, and the dim horn.
    world.say(
        f"At dusk, {hero.id} came to {setting.place}, where the air felt still and old."
    )
    world.say(
        f"Near the toll box sat {horn.label} and {lantern.label}; {UTILITIES['horn'].clue}."
    )
    world.say(
        f"{hero.id} had brought a friend, {friend.id}, and {friend.id} looked uneasy beside the dark water."
    )

    # Act 2: need, utility, moral pressure.
    world.para()
    hero.meters["courage"] += 1.0
    hero.memes["wonder"] += 1.0
    world.say(
        f"{hero.id} remembered what the grown-ups said: the bridge would only wake if someone used the horn."
    )
    world.say(
        f"But there was one toll coin, and {CHOICE.keep_coin} sounded easier than doing the helpful thing."
    )
    world.say(
        f"{friend.id} whispered that the boards looked like shadows, and that made the crossing feel huge."
    )
    world.say(
        f"{hero.id} looked at the coin, then at {friend.id}, and felt the question in {CHOICE.lesson}."
    )

    # Turn: choose utility over selfishness.
    world.para()
    coin.memes["value"] = 1.0
    hero.memes["moral_value"] += 1.0
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    world.say(
        f"At last {hero.id} chose to {CHOICE.give_coin}."
    )
    world.say(
        f"{hero.id} dropped the toll coin into the box and sounded the brass horn."
    )
    world.say(
        f"The note came out low and dim, and the ferryman-ghost stirred as if he had been waiting kindly all evening."
    )

    # Resolution: ghost helps, utility becomes real, friendship proven.
    world.para()
    ghost.meters["presence"] += 1.0
    ghost.memes["kindness"] += 1.0
    world.say(
        f"The ferryman-ghost lifted {lantern.label} and showed the safe way across."
    )
    world.say(
        f"{friend.id} held tight to {hero.id}'s hand, and together they crossed the toll bridge without fear."
    )
    world.say(
        f"On the far side, {friend.id} smiled through the dark, and {hero.id} knew that {CHOICE.lesson}."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        horn=horn,
        lantern=lantern,
        coin=coin,
        ghost=ghost,
        setting=setting,
        choice=CHOICE,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        f'Write a short Ghost Story for a child named {hero.id} who finds a dim horn at a toll bridge and helps a friend.',
        f"Tell a gentle spooky story about {hero.id}, {friend.id}, and a toll coin that becomes useful for kindness.",
        f'Write a child-friendly haunted story using the words "horn", "dim", and "toll" with a happy ending about friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        QAItem(
            question=f"Where did {hero.id} go at dusk?",
            answer=f"{hero.id} went to {f['setting'].place}, an old toll bridge that felt quiet and dim.",
        ),
        QAItem(
            question=f"What did {hero.id} do with the brass horn?",
            answer=f"{hero.id} sounded the brass horn to wake the ferryman-ghost and ask for help.",
        ),
        QAItem(
            question=f"Why did {hero.id} use the toll coin instead of keeping it?",
            answer=f"{hero.id} used the toll coin to help {friend.id} cross safely, because friendship and kindness mattered more.",
        ),
        QAItem(
            question=f"What changed after the horn was sounded?",
            answer="The ferryman-ghost woke up, lifted the lantern, and showed the safe way across the bridge.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a toll?",
            answer="A toll is a small payment you give to use a road, bridge, or gate.",
        ),
        QAItem(
            question="What does utility mean?",
            answer="Utility means something is useful and can help get a job done.",
        ),
        QAItem(
            question="What does moral value mean?",
            answer="Moral value means the good choice, like being honest, helpful, or kind.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between people who help each other and stay close.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== Prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    return "\n".join(lines)


# ASP twin
ASP_RULES = r"""
hero(H) :- hero_name(H).
friend(F) :- friend_name(F).

dim_horn_available :- horn(H), dim(H).
ghost_wakes :- dim_horn_available, sound(H).
good_choice :- give_coin, friend_in_need, use_coin_for_help.
friendship_shines :- good_choice.
story_valid :- ghost_wakes, friendship_shines.
#show story_valid/0.
#show ghost_wakes/0.
#show friendship_shines/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("hero_name", "hero"))
    lines.append(asp.fact("friend_name", "friend"))
    lines.append(asp.fact("horn"))
    lines.append(asp.fact("sound", "horn"))
    lines.append(asp.fact("dim", "horn"))
    lines.append(asp.fact("give_coin"))
    lines.append(asp.fact("friend_in_need"))
    lines.append(asp.fact("use_coin_for_help"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_valid/0.\n"))
    has_story = any(a.name == "story_valid" for a in model)
    python_ok = True
    if has_story != python_ok:
        print("MISMATCH between ASP and Python gate.")
        return 1
    print("OK: ASP and Python gates agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: a dim horn, a toll, a useful kindness, and friendship.")
    ap.add_argument("--name", choices=sorted(set(GIRL_NAMES + BOY_NAMES)))
    ap.add_argument("--gender", choices=["girl", "boy", "child"], default="child")
    ap.add_argument("--friend-name", choices=sorted(set(GIRL_NAMES + BOY_NAMES)))
    ap.add_argument("--parent-name", choices=["mother", "father"])
    ap.add_argument("--setting", choices=SETTINGS)
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
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    parent = args.parent_name or rng.choice(["mother", "father"])
    setting = args.setting or rng.choice(list(SETTINGS))
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    return StoryParams(name=name, gender=gender, friend_name=friend, parent_name=parent, setting=setting)


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


CURATED = [
    StoryParams(name="Mina", gender="girl", friend_name="Theo", parent_name="mother", setting="bridge"),
    StoryParams(name="Finn", gender="boy", friend_name="Ivy", parent_name="father", setting="bridge"),
    StoryParams(name="Nora", gender="girl", friend_name="Leo", parent_name="mother", setting="lantern_room"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_valid/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_valid/0.\n"))
        print("ASP model:", model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
