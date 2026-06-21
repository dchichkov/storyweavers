#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/flitter_sharing_misunderstanding_conflict_ghost_story.py
========================================================================================

A small storyworld about a ghostly flitter, a sharing mishap, and a conflict that
gets solved by kindness.

Seed-inspired premise
---------------------
A child hears a tiny ghostly flitter in an old house, assumes it wants to take a
shiny thing, and conflict starts. The misunderstanding resolves when the flitter
turns out to be sharing a lost treasure instead of stealing it.

This script follows the Storyweavers storyworld contract:
- typed entities with physical meters and emotional memes
- a forward causal model that drives the prose
- explicit validity gates
- a Python reasonableness checker plus inline ASP twin
- three QA sets grounded in the simulated world state
- standard CLI flags for story generation, tracing, QA, JSON, ASP, and verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    hiding_spot: str
    shared_item: str
    ghost_sound: str


@dataclass
class GhostThing:
    id: str
    label: str
    shared_phrase: str
    note: str
    wears: str
    friendly: bool = True
    spooky: bool = True


@dataclass
class ConflictMove:
    id: str
    sense: int
    calm: int
    text: str
    fail: str
    qa_text: str


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["ghostly"] < THRESHOLD:
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for name in ("child", "friend"):
            if name in world.entities:
                world.get(name).memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    if "child" not in world.entities or "friend" not in world.entities:
        return out
    child = world.get("child")
    friend = world.get("friend")
    if child.memes["share"] < THRESHOLD or friend.memes["share"] < THRESHOLD:
        return out
    sig = ("soften",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    friend.memes["calm"] += 1
    out.append("Their voices softened.")
    return out


CAUSAL_RULES = [_r_fear, _r_soften]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(item: GhostThing, move: ConflictMove, setting: Setting) -> bool:
    return item.friendly and item.spooky and move.sense >= 2 and setting.place


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for gid, item in GHOST_THINGS.items():
            for mid, mv in MOVES.items():
                if reasonableness_gate(item, mv, SETTINGS[sid]):
                    combos.append((sid, gid, mid))
    return combos


def predict(world: World, item_id: str) -> dict:
    sim = world.copy()
    _haunt(sim, sim.get(item_id), narrate=False)
    return {"ghostly": sim.get("child").meters["ghostly"], "fear": sim.get("child").memes["fear"]}


def _haunt(world: World, item: Entity, narrate: bool = True) -> None:
    item.meters["ghostly"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, item: GhostThing, move: ConflictMove,
         child_name: str = "Mina", child_type: str = "girl",
         friend_name: str = "Pip", friend_type: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="sharer"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, role="listener"))
    ghost = world.add(Entity(id="flitter", kind="thing", type="ghost", label=item.label,
                             traits=["tiny", "floating"], attrs={"shared_phrase": item.shared_phrase}))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))

    child.memes["curiosity"] = 1
    friend.memes["curiosity"] = 1

    world.say(
        f"On a quiet night, {child.label} and {friend.label} crept into {setting.place}. "
        f"The air felt {setting.mood}, and something soft seemed to {setting.ghost_sound} near {setting.hiding_spot}."
    )
    world.say(
        f'"Did you hear that?" {friend.label} whispered. "{item.label_word.capitalize()}!" '
        f'{child.label} clutched a little flashlight, but the old house still seemed to breathe.'
    )

    world.para()
    child.memes["share"] += 1
    friend.memes["share"] += 1
    world.say(
        f"{child.label} found {item.shared_phrase} tucked beside {setting.shared_item}. "
        f"{child.label} thought the flitter wanted to take it, and worry flickered into conflict."
    )
    world.say(
        f'"No, it is mine," {child.label} said, pulling back. {friend.label} frowned, because {item.note} made the room feel stranger.'
    )

    world.para()
    fear = predict(world, "flitter")
    world.facts["predicted_fear"] = fear["fear"]
    world.say(
        f"Then the tiny flitter drifted close and flittered in a silver loop. "
        f"It did not snatch anything. It pointed at {setting.shared_item} and waited."
    )
    world.say(
        f'{friend.label} noticed the flitter was not grabbing, just sharing a sign. '
        f'On the floor lay a note that said, "{item.wears}."'
    )

    world.para()
    if move.sense >= 2:
        world.say(
            f'{child.label} looked at {friend.label}, took a slow breath, and used a kinder answer. '
            f"{move.text.format(item=item.label)}."
        )
        child.memes["share"] += 1
        friend.memes["share"] += 1
        child.memes["calm"] += 1
        friend.memes["calm"] += 1
        _haunt(world, ghost)
        world.say(
            f"The flitter glow grew warm instead of cold. It had been sharing all along: "
            f"it wanted the children to split {setting.shared_item} and find the hidden toy together."
        )
        world.para()
        world.say(
            f"So {child.label} and {friend.label} divided the treasure into two parts and left one for the flitter. "
            f"The old house felt less lonely, and the silver shape drifted happily through the hall."
        )
        outcome = "shared"
    else:
        world.say(
            f'{child.label} tried a sharp answer instead. {move.fail.format(item=item.label)}'
        )
        child.memes["conflict"] += 1
        friend.memes["conflict"] += 1
        outcome = "conflict"

    world.facts.update(
        child=child,
        friend=friend,
        ghost=ghost,
        room=room,
        setting=setting,
        item=item,
        move=move,
        outcome=outcome,
    )
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic",
        mood="moon-bright and dusty",
        hiding_spot="a blue trunk",
        shared_item="a candy tin",
        ghost_sound="flitter",
    ),
    "hall": Setting(
        id="hall",
        place="the old hall",
        mood="cool and hushy",
        hiding_spot="the coat rack",
        shared_item="a cookie plate",
        ghost_sound="whisper",
    ),
    "basement": Setting(
        id="basement",
        place="the basement",
        mood="damp and echoey",
        hiding_spot="the stair corner",
        shared_item="a toy box",
        ghost_sound="flicker",
    ),
}

GHOST_THINGS = {
    "flitter": GhostThing(
        id="flitter",
        label="flitter",
        shared_phrase="a little star-shaped charm",
        note="the tiny shape was not cold, only shy",
        wears="Share the charm, and the room will open",
    ),
}

MOVES = {
    "gentle": ConflictMove(
        id="gentle",
        sense=3,
        calm=3,
        text="they nodded and asked if the flitter wanted to share the charm",
        fail="But the flitter only drifted back, and the misunderstanding stayed rough.",
        qa_text="asked the flitter to share the charm kindly",
    ),
    "open_hand": ConflictMove(
        id="open_hand",
        sense=3,
        calm=4,
        text="they opened their hand and offered half of it first",
        fail="But the open hand came too late, and the child only felt more upset.",
        qa_text="offered half of it first",
    ),
    "shout": ConflictMove(
        id="shout",
        sense=1,
        calm=1,
        text="they shouted at the flitter",
        fail="The shout only made the room feel colder and louder.",
        qa_text="shouted at the flitter",
    ),
}

NAMES_GIRL = ["Mina", "Lily", "Nora", "Pia", "Maya"]
NAMES_BOY = ["Pip", "Leo", "Finn", "Toby", "Noah"]


@dataclass
class StoryParams:
    setting: str
    ghost: str
    move: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghostly storyworld about sharing, misunderstanding, and conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ghost", choices=GHOST_THINGS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.move and MOVES[args.move].sense < 2:
        raise StoryError("That move is too sharp for a child-friendly ghost story.")
    combos = [c for c in valid_combos()
              if args.setting in (None, c[0])
              and args.ghost in (None, c[1])
              and args.move in (None, c[2])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, ghost, move = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    friend_name = args.friend_name or rng.choice(NAMES_BOY if friend_gender == "boy" else NAMES_GIRL)
    if child_name == friend_name:
        friend_name = "Pip" if child_name != "Pip" else "Mina"
    return StoryParams(
        setting=setting,
        ghost=ghost,
        move=move,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.ghost not in GHOST_THINGS or params.move not in MOVES:
        raise StoryError("Invalid story parameters.")
    world = tell(
        SETTINGS[params.setting],
        GHOST_THINGS[params.ghost],
        MOVES[params.move],
        child_name=params.child_name,
        child_type=params.child_gender,
        friend_name=params.friend_name,
        friend_type=params.friend_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    item = f["item"]
    return [
        f'Write a tiny ghost story for a 3-to-5-year-old that includes the word "{item.id}" and a misunderstanding.',
        f"Tell a child-friendly ghost story in {setting.place} where two friends think a flitter wants to steal something, but it is really sharing.",
        f"Write a story about sharing and conflict in a spooky old place, and make the flitter turn out friendly in the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    setting: Setting = f["setting"]
    item: GhostThing = f["item"]
    move: ConflictMove = f["move"]
    out = [
        ("Who is the story about?", f"It is about {child.label} and {friend.label}, who went looking for a small ghostly flitter in {setting.place}."),
        ("What caused the misunderstanding?", f"{child.label} thought the flitter wanted to take {item.shared_phrase}, so worry turned into conflict. The tiny shape was actually trying to share a clue."),
        ("How did they solve the problem?", f"They answered with {move.qa_text}, which let them understand the flitter was friendly. That changed the mood from tense to warm."),
    ]
    if f["outcome"] == "shared":
        out.append(("How did the story end?", f"They shared the treasure and the flitter drifted away happily. The old place felt less lonely because everyone kept part of the prize.")) 
    else:
        out.append(("How did the story end?", "The conflict stayed noisy, and the room never settled down. The misunderstanding was never fixed."))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a flitter in this story?", "A flitter is a tiny ghostly shape that floats and moves with quick, light motions. It seems spooky at first, but it can be friendly."),
        ("Why can misunderstandings cause conflict?", "When someone guesses the wrong reason for a strange action, feelings can get hurt fast. Talking kindly helps find the real meaning."),
        ("What does sharing mean?", "Sharing means letting someone else have part of something or taking turns with it. It can turn a fight into cooperation."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="attic", ghost="flitter", move="gentle", child_name="Mina", child_gender="girl", friend_name="Pip", friend_gender="boy"),
    StoryParams(setting="hall", ghost="flitter", move="open_hand", child_name="Nora", child_gender="girl", friend_name="Leo", friend_gender="boy"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid in GHOST_THINGS:
        lines.append(asp.fact("ghost", gid))
    for mid, mv in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("sense", mid, mv.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, G, M) :- setting(S), ghost(G), move(M), sense(M, N), sense_min(X), N >= X.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, ghost=None, move=None, child_name=None, friend_name=None, child_gender=None, friend_gender=None), random.Random(1)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for x in combos:
            print(" ", x)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            i += 1
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
