#!/usr/bin/env python3
"""
A bedtime-story world about a child, a friend, and one vital little
something that helps them settle the night with kindness and dialogue.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    partner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the small bedroom"
    time: str = "bedtime"
    afford: set[str] = field(default_factory=lambda: {"talk", "share", "read", "breathe"})


@dataclass
class Bond:
    name: str
    label: str
    dialogue_prompt: str
    comfort_action: str
    ending_image: str
    vital_object: str
    vital_phrase: str


@dataclass
class StoryParams:
    bond: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


SETTING = Setting()

BONDS = {
    "lantern": Bond(
        name="lantern",
        label="little lantern",
        dialogue_prompt="share a soft word and a warm light",
        comfort_action="hold the lantern together",
        ending_image="the little lantern glowed like a tiny moon on the nightstand",
        vital_object="lantern",
        vital_phrase="vital little light",
    ),
    "blanket": Bond(
        name="blanket",
        label="cozy blanket",
        dialogue_prompt="trade sleepy promises",
        comfort_action="pull the blanket up around them",
        ending_image="the cozy blanket stayed tucked under their chins",
        vital_object="blanket",
        vital_phrase="vital cozy blanket",
    ),
    "song": Bond(
        name="song",
        label="soft song",
        dialogue_prompt="whisper a tiny bedtime song",
        comfort_action="hum the song together",
        ending_image="the soft song drifted through the room like a gentle cloud",
        vital_object="song",
        vital_phrase="vital soft song",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Leo", "Theo", "Sam"]


@dataclass
class StoryState:
    child: Entity
    friend: Entity
    bond: Bond
    setting: Setting
    calm: float = 0.0
    closeness: float = 0.0
    worry: float = 0.0


def _bounce_worry(world: World, state: StoryState) -> None:
    if state.worry >= 1.0 and ("worry", state.child.id) not in world.fired:
        world.fired.add(("worry", state.child.id))
        state.child.memes["worry"] = state.worry
        world.say(
            f"{state.child.id} felt a tiny wobble in {state.chest_name if hasattr(state, 'chest_name') else 'their chest'}."
        )


def tell_story(world: World, state: StoryState) -> None:
    child = state.child
    friend = state.friend
    bond = state.bond

    world.say(
        f"It was bedtime in {world.setting.place}, and {child.id} was not quite ready to sleep."
    )
    world.say(
        f"{friend.id} came in with {child.pronoun('possessive')} {bond.label}, and both of them smiled."
    )
    world.say(
        f'"Do you want to {bond.dialogue_prompt}?" {friend.id} asked.'
    )
    world.say(
        f'{child.id} nodded, but {child.pronoun("subject")} still held a little worry in {child.pronoun("possessive")} hands.'
    )
    state.worry += 1
    state.child.memes["worry"] = state.worry

    world.para()
    world.say(
        f'“I feel shaky,” {child.id} whispered. “Will you stay with me?”'
    )
    world.say(
        f'“Always,” {friend.id} said, and {friend.pronoun("subject")} sat close by.'
    )
    world.say(
        f'Together they chose to {bond.comfort_action}, which made the room feel softer.'
    )
    state.closeness += 1
    state.calm += 1
    state.child.memes["calm"] = state.calm
    state.friend.memes["closeness"] = state.closeness

    world.para()
    world.say(
        f'Then {child.id} took one slow breath, and {friend.id} took one slow breath too.'
    )
    world.say(
        f'“First we talk, then we rest,” {friend.id} said, and {child.id} repeated it in a tiny sleepy voice.'
    )
    world.say(
        f'By the time the shadows stretched across the wall, {child.id} felt brave enough to close {child.pronoun("possessive")} eyes.'
    )
    world.say(f'The {bond.ending_image}.')
    state.calm += 1
    state.child.memes["calm"] = state.calm
    world.facts.update(
        child=child,
        friend=friend,
        bond=bond,
        setting=world.setting,
        calm=state.calm,
        closeness=state.closeness,
        worry=state.worry,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    bond = f["bond"]
    return [
        f'Write a bedtime story for a young child about {child.id} and {friend.id} sharing something vital and talking softly before sleep.',
        f"Tell a gentle friendship story where {child.id} feels worried at bedtime, but {friend.id} helps with a {bond.vital_phrase}.",
        f'Write a cozy story that includes the word "vital" and ends with a child falling asleep after a kind dialogue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    bond = f["bond"]
    return [
        QAItem(
            question=f"Who was the bedtime story about?",
            answer=f"It was about {child.id} and {friend.id}, who stayed kind to each other at bedtime.",
        ),
        QAItem(
            question=f"What did {friend.id} share that was vital?",
            answer=f"{friend.id} shared the {bond.vital_object}, which was a vital little comfort for the bedtime moment.",
        ),
        QAItem(
            question=f"How did {child.id} feel before the two friends settled down?",
            answer=f"{child.id} felt a little worried at first, but calm came back after the two of them talked and stayed close.",
        ),
        QAItem(
            question=f"What did the friends do together to feel better?",
            answer=f"They shared a gentle dialogue, took slow breaths, and used the {bond.vital_object} together so the room felt safe and cozy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} sleepy and brave, and with {bond.ending_image}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does vital mean?",
            answer="Vital means something is very important or needed, like a helpful thing that makes a problem easier.",
        ),
        QAItem(
            question="Why can talking softly help at bedtime?",
            answer="Talking softly can help because calm words make the room feel safe and make it easier to relax.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share, listen, and help one another feel better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime friendship story world.")
    ap.add_argument("--bond", choices=BONDS.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


def _valid_params(params: StoryParams) -> None:
    if params.child_type == params.friend_type and params.child_name == params.friend_name:
        raise StoryError("The child and friend must be different people.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    bond = args.bond or rng.choice(sorted(BONDS))
    child_type = args.gender or rng.choice(["girl", "boy"])
    friend_type = args.friend_gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    friend_pool = GIRL_NAMES if friend_type == "girl" else BOY_NAMES
    friend_name = args.friend_name or rng.choice([n for n in friend_pool if n != child_name] or friend_pool)
    params = StoryParams(bond=bond, child_name=child_name, child_type=child_type,
                         friend_name=friend_name, friend_type=friend_type)
    _valid_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    bond = BONDS[params.bond]
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    state = StoryState(child=child, friend=friend, bond=bond, setting=world.setting)
    tell_story(world, state)
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


ASP_RULES = r"""
child(C) :- character(C), child_type(C,_).
friend(F) :- character(F), friend_type(F,_).
bond(B) :- bond_name(B).

friendship(C,F) :- child(C), friend(F), C != F.
vital(B) :- bond(B).
helpful(B) :- vital(B).
#show friendship/2.
#show vital/1.
#show helpful/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name, bond in BONDS.items():
        lines.append(asp.fact("bond_name", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show vital/1."))
    vitals = set(asp.atoms(model, "vital"))
    if vitals == {("lantern",), ("blanket",), ("song",)}:
        print("OK: ASP twin sees all vital bonds.")
        return 0
    print("Mismatch in ASP twin.")
    return 1


CURATED = [
    StoryParams(bond="lantern", child_name="Mia", child_type="girl", friend_name="Noah", friend_type="boy"),
    StoryParams(bond="blanket", child_name="Leo", child_type="boy", friend_name="Nora", friend_type="girl"),
    StoryParams(bond="song", child_name="Ava", child_type="girl", friend_name="Finn", friend_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show friendship/2.\n#show vital/1.\n#show helpful/1."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show friendship/2.\n#show vital/1.\n#show helpful/1."))
        print("friendship:", sorted(set(asp.atoms(model, "friendship"))))
        print("vital:", sorted(set(asp.atoms(model, "vital"))))
        print("helpful:", sorted(set(asp.atoms(model, "helpful"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
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
