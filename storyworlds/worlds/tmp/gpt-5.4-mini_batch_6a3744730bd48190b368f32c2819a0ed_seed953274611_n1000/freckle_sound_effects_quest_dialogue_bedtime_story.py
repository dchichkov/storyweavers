#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/freckle_sound_effects_quest_dialogue_bedtime_story.py
======================================================================================

A small bedtime-story world: a child goes on a tiny quest to help a bedtime friend
feel brave enough to sleep, and the story uses dialogue, sound effects, and the
word "freckle" as a soft, child-facing detail.

The world is intentionally simple but state-driven:
- a child and a bedtime friend each carry emotions in "memes"
- a little quest object must be found and used
- sound effects are narrated only when the simulated actions happen
- dialogue changes the emotional state and moves the story toward rest

This script follows the Storyweavers contract:
- stdlib-only script
- imports results eagerly
- imports asp lazily only in ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Place:
    id: str
    label: str
    dark: bool = False
    cozy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    kind: str
    required_place: str
    use_line: str
    find_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cue:
    id: str
    label: str
    sound: str
    action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    comfort: int
    text: str
    tags: set[str] = field(default_factory=set)


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_breathe(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["rest"] >= THRESHOLD and ("settled", e.id) not in world.fired:
            world.fired.add(("settled", e.id))
            e.memes["calm"] += 1
            out.append("__settled__")
    return out


CAUSAL_RULES = [Rule("breathe", "social", _r_breathe)]


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


def reasonableness_gate(item: Item, place: Place) -> bool:
    return item.required_place == place.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            if not reasonableness_gate(item, place):
                continue
            for cue_id in CUES:
                combos.append((place_id, item_id, cue_id))
    return combos


def choose_name(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool), gender


def predict(world: World, item: Item) -> dict:
    sim = world.copy()
    child = sim.get("child")
    friend = sim.get("friend")
    _start_quest(sim, child, friend, item, narrate=False)
    return {"calm": friend.memes["calm"], "rest": friend.meters["rest"]}


def _start_quest(world: World, child: Entity, friend: Entity, item: Item, narrate: bool = True) -> None:
    child.meters["quest"] += 1
    friend.memes["worry"] += 1
    if narrate:
        world.say(f"{child.id} began a tiny quest to find {item.label}.")
    world.say(f"Tip-tap, tip-tap, went the little footsteps.")
    child.meters["found"] += 1
    world.facts["found_item"] = item.id


def _use_item(world: World, child: Entity, friend: Entity, item: Item, cue: Cue) -> None:
    world.say(cue.sound + " " + item.use_line)
    friend.memes["worry"] = 0.0
    friend.meters["rest"] += 1
    child.memes["pride"] += 1
    child.meters["quest"] += 1
    propagate(world, narrate=False)


def _dialogue(world: World, child: Entity, friend: Entity, response: Response) -> None:
    world.say(f'"{friend.label}," said {child.id}, "I found something to help you."')
    world.say(f'"{response.text}" whispered {friend.id}.')
    friend.memes["worry"] = max(0.0, friend.memes["worry"] - response.comfort)
    child.memes["love"] += 1


def tell(place: Place, item: Item, cue: Cue, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         friend_name: str = "Toby", friend_gender: str = "boy",
         parent_name: str = "Mom") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother", role="parent"))
    room = world.add(Entity(id="room", type="room", label=place.label, attrs={"dark": place.dark}))
    child.memes["hope"] = 1.0
    friend.memes["worry"] = 2.0 if place.dark else 1.0

    world.say(f"It was bedtime in {place.label}, where the air was soft and still.")
    world.say(f"{child.id} noticed {friend.id} looking down at a little {item.kind} on the shelf.")
    world.say(f'There was one tiny freckle on {child.id}\'s cheek, and it caught the moonlight like a dot of gold.')

    world.para()
    world.say(f'"Can you sleep?" asked {child.id}.')
    world.say(f'"Not yet," said {friend.id}. "The dark feels too big."')
    world.say(f"{child.id} thought for a moment, then set out on a quiet quest.")

    _start_quest(world, child, friend, item)

    world.para()
    world.say(f"In the hush of the room, the quest turned toward the right hiding place.")
    world.say(f'"Look," said {child.id}, "I know where {item.label} is."')
    world.say(f"{cue.action}")
    _dialogue(world, child, friend, response)
    _use_item(world, child, friend, item, cue)

    world.para()
    world.say(f"{parent.label_word.capitalize()} peeked in with a sleepy smile.")
    world.say(f'"Did the quest help?" asked {parent.id}.')
    world.say(f'"Yes," said {friend.id}, now quiet and cozy. "The room feels small enough for sleep."')
    world.say(f"{child.id} climbed into bed with a happy heart, and the freckle on {child.id}'s cheek blinked in the lamp light like a tiny star.")

    world.facts.update(
        child=child, friend=friend, parent=parent, place=place, item=item,
        cue=cue, response=response, room=room, outcome="rested",
    )
    return world


PLACES = {
    "nursery": Place(id="nursery", label="the nursery", dark=True, cozy=True, tags={"bedtime"}),
    "attic_room": Place(id="attic_room", label="the attic room", dark=True, cozy=True, tags={"bedtime"}),
    "moon_room": Place(id="moon_room", label="the moon room", dark=True, cozy=True, tags={"bedtime"}),
}

ITEMS = {
    "lantern": Item(id="lantern", label="a paper lantern", kind="lantern", required_place="nursery",
                    use_line="the lantern glowed like a tiny moon.",
                    find_line="it waited beside the pillow."),
    "shell": Item(id="shell", label="a singing shell", kind="shell", required_place="attic_room",
                 use_line="the shell hummed soft and low.",
                 find_line="it was tucked in a blanket nest."),
    "starbell": Item(id="starbell", label="a star bell", kind="bell", required_place="moon_room",
                     use_line="the bell rang one soft ding.",
                     find_line="it hid under a cushion."),
}

CUES = {
    "lantern": Cue(id="lantern", label="lantern", sound="Whirr-", action="The lantern blinked awake."),
    "shell": Cue(id="shell", label="shell", sound="Shhh-", action="The shell gave a sleepy hum."),
    "starbell": Cue(id="starbell", label="bell", sound="Ding-ding.", action="The bell sang once."),
}

RESPONSES = {
    "gentle": Response(id="gentle", sense=3, comfort=2, text="It's all right. The dark can be soft too.", tags={"bedtime", "dialogue"}),
    "brave": Response(id="brave", sense=4, comfort=3, text="We can be brave together. I'll stay till you feel sleepy.", tags={"bedtime", "dialogue"}),
    "hush": Response(id="hush", sense=3, comfort=2, text="Let's listen to the quiet and let it tuck us in.", tags={"bedtime", "dialogue"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Toby", "Finn", "Leo", "Noah", "Theo", "Max"]

CURATED = [
    StoryParams = None
]

# Build curated after StoryParams definition

@dataclass
class StoryParams:
    place: str
    item: str
    cue: str
    response: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    parent_name: str = "Mom"
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="nursery", item="lantern", cue="lantern", response="gentle",
                child_name="Mina", child_gender="girl", friend_name="Toby", friend_gender="boy",
                parent_name="Mom"),
    StoryParams(place="attic_room", item="shell", cue="shell", response="brave",
                child_name="Lily", child_gender="girl", friend_name="Finn", friend_gender="boy",
                parent_name="Dad"),
    StoryParams(place="moon_room", item="starbell", cue="starbell", response="hush",
                child_name="Noah", child_gender="boy", friend_name="Nora", friend_gender="girl",
                parent_name="Mom"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime quest with dialogue and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cue", choices=CUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
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
    if args.item and args.place and not reasonableness_gate(ITEMS[args.item], PLACES[args.place]):
        raise StoryError("That item does not belong in that place for this bedtime quest.")
    choices = [c for c in valid_combos()
               if (args.place is None or c[0] == args.place)
               and (args.item is None or c[1] == args.item)
               and (args.cue is None or c[2] == args.cue)]
    if not choices:
        raise StoryError("(No valid bedtime quest matches the given options.)")
    place, item, cue = rng.choice(sorted(choices))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_name = args.child_name or choose_name(rng)[0]
    child_gender = args.child_gender or ("girl" if child_name in GIRL_NAMES else "boy")
    friend_name = args.friend_name or choose_name(rng)[0]
    friend_gender = args.friend_gender or ("girl" if friend_name in GIRL_NAMES else "boy")
    parent_name = args.parent_name or "Mom"
    return StoryParams(place=place, item=item, cue=cue, response=response,
                       child_name=child_name, child_gender=child_gender,
                       friend_name=friend_name, friend_gender=friend_gender,
                       parent_name=parent_name)


def generate(params: StoryParams) -> StorySample:
    place = PLACES.get(params.place)
    item = ITEMS.get(params.item)
    cue = CUES.get(params.cue)
    response = RESPONSES.get(params.response)
    if not all([place, item, cue, response]):
        raise StoryError("Invalid params for this bedtime story world.")
    world = tell(place, item, cue, response, params.child_name, params.child_gender,
                 params.friend_name, params.friend_gender, params.parent_name)
    prompts = [
        f'Write a bedtime story with dialogue and sound effects about a child and a small quest. Include the word "freckle".',
        f"Tell a cozy story where {params.child_name} helps {params.friend_name} feel sleepy by finding {item.label}.",
        f"Write a gentle bedtime quest using the sound effect {cue.sound} and a calm ending.",
    ]
    story_qa = [
        QAItem(question="What was the quest?", answer=f"The quest was to find {item.label} and use it to help {params.friend_name} feel safe enough to sleep. It turned the quiet room into a tiny adventure with a calm ending."),
        QAItem(question="Why did the friend need help?", answer=f"{params.friend_name} felt like the dark was too big at first. The child answered with kind words and a gentle sound, which helped the worry fade."),
        QAItem(question="What changed by the end?", answer=f"By the end, {params.friend_name} was cozy and ready for sleep, and {params.child_name} felt proud and happy. The room stayed soft and peaceful, like a bedtime hug."),
    ]
    world_qa = [
        QAItem(question="What is a freckle?", answer="A freckle is a small spot on skin. It can look like a tiny dot of sunshine."),
        QAItem(question="What is a quest?", answer="A quest is a small mission to find something or help someone. In stories, quests make a character keep going with purpose."),
        QAItem(question="What does a sound effect do in a story?", answer="A sound effect helps you hear the action in your mind. It can make a little moment feel playful or magical."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts,
                       story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
valid(P,I,C) :- place(P), item(I), cue(C), required_place(I,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("required_place", iid, item.required_place))
    for cid in CUES:
        lines.append(asp.fact("cue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos() differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, item=None, cue=None, response=None, child_name=None,
            child_gender=None, friend_name=None, friend_gender=None,
            parent_name=None
        ), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid bedtime quest combos:")
        for p, i, c in asp_valid_combos():
            print(f"  {p:10} {i:10} {c}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
