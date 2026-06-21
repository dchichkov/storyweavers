#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/love_reconciliation_nursery_rhyme.py
=====================================================================

A small nursery-rhyme storyworld about a tiny quarrel, a gentle reconciliation,
and the warm feeling of love that returns when two little friends make peace.

The world is built around a few concrete entities:
- two children,
- a shared toy or song,
- a small misunderstanding,
- a helping object or gesture,
- a reconciliation ending image.

The story is state-driven: emotional memes and physical meters change through
the simulation, and the prose is rendered from that evolving world state.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
        return self.label or self.id


@dataclass
class Sound:
    id: str
    label: str
    phrase: str
    sparkle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PeaceGesture:
    id: str
    label: str
    phrase: str
    effect: str
    warmth: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    id: str
    label: str
    cause: str
    beat: str
    tension: int
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["hurt"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for eid in ("child_a", "child_b"):
            if eid in world.entities:
                world.get(eid).memes["sadness"] += 1
        out.append("__sad__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quarrel_reason(conflict: Conflict) -> str:
    return conflict.cause


def choose_child_names(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    girls = ["Mimi", "Lily", "Nina", "Tilly", "Daisy", "Ruby"]
    boys = ["Tommy", "Benny", "Ned", "Rufus", "Pip", "Cory"]
    a = rng.choice(girls + boys)
    b = rng.choice([n for n in girls + boys if n != a])
    def gender(name: str) -> str:
        return "girl" if name in girls else "boy"
    return (a, gender(a)), (b, gender(b))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for song in SONGS:
        for conflict in CONFLICTS:
            for gesture in GESTURES:
                if conflict.label == "broken turn" and gesture.warmth >= conflict.tension:
                    combos.append((song, conflict.id, gesture.id))
    return combos


@dataclass
class StoryParams:
    song: str
    conflict: str
    gesture: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    seed: Optional[int] = None


SONGS = {
    "rounds": Sound(id="rounds", label="round song", phrase="a round little song", sparkle="tra-la-la", tags={"song", "love"}),
    "bells": Sound(id="bells", label="bell tune", phrase="a tiny bell tune", sparkle="ding-dong", tags={"song"}),
    "lullaby": Sound(id="lullaby", label="lullaby", phrase="a soft nursery lullaby", sparkle="hush-a-bye", tags={"song", "love"}),
}

CONFLICTS = {
    "broken_toy": Conflict(id="broken_toy", label="broken toy", cause="one child tugged too hard on the toy lamb", beat="the lamb fell apart", tension=3, tags={"toy"}),
    "spilled_tea": Conflict(id="spilled_tea", label="spilled tea", cause="one child bumped the little tea cup", beat="the tea splashed and made a mess", tension=2, tags={"tea"}),
    "lost_turn": Conflict(id="lost_turn", label="lost turn", cause="one child forgot to share the next turn", beat="the other child felt left out", tension=2, tags={"sharing"}),
}

GESTURES = {
    "hug": PeaceGesture(id="hug", label="gentle hug", phrase="a gentle hug", effect="wrapped their arms around each other", warmth=3, tags={"love", "peace"}),
    "song": PeaceGesture(id="song", label="shared song", phrase="a shared song", effect="sang the tune together", warmth=2, tags={"song", "love"}),
    "gift": PeaceGesture(id="gift", label="small gift", phrase="a small ribbon bow", effect="tied a ribbon bow on the toy", warmth=3, tags={"gift", "love"}),
}

RECIPES = {
    "jam": "a little jam tart",
    "cake": "a tiny honey cake",
    "milk": "a warm cup of milk",
}

CURATED = [
    StoryParams(song="rounds", conflict="broken_toy", gesture="hug",
                child_a="Mimi", child_a_gender="girl", child_b="Tommy", child_b_gender="boy"),
    StoryParams(song="lullaby", conflict="spilled_tea", gesture="song",
                child_a="Lily", child_a_gender="girl", child_b="Ned", child_b_gender="boy"),
    StoryParams(song="bells", conflict="lost_turn", gesture="gift",
                child_a="Pip", child_a_gender="boy", child_b="Daisy", child_b_gender="girl"),
]


def reasonableness_gate(conflict: Conflict, gesture: PeaceGesture) -> bool:
    return gesture.warmth >= conflict.tension


def choose_ending_food(rng: random.Random) -> str:
    return rng.choice(list(RECIPES.values()))


def tell(song: Sound, conflict: Conflict, gesture: PeaceGesture,
         a_name: str, a_gender: str, b_name: str, b_gender: str,
         snack: str = "a little jam tart") -> World:
    world = World()
    a = world.add(Entity(id="child_a", kind="character", type=a_gender, label=a_name, role="child"))
    b = world.add(Entity(id="child_b", kind="character", type=b_gender, label=b_name, role="child"))

    a.memes["love"] = 2
    b.memes["love"] = 2
    a.memes["joy"] = 1
    b.memes["joy"] = 1

    world.say(f"{a.label} and {b.label} were two little friends in a nursery rhyme lane.")
    world.say(f"They sang a {song.phrase}, tra-la-la, with bright eyes and a merry refrain.")

    world.para()
    world.say(f"Then came a trouble, small as can be: {quarrel_reason(conflict)}.")
    world.say(f"{conflict.beat}, and the sweet little tune went quiet for a spell.")
    a.memes["hurt"] += 1
    b.memes["hurt"] += 1
    a.memes["sadness"] += 1
    b.memes["sadness"] += 1

    world.para()
    if not reasonableness_gate(conflict, gesture):
        raise StoryError("This peace gesture is too small for the quarrel.")
    world.say(f"But {a.label} looked at {b.label}, and {b.label} looked at {a.label}.")
    world.say(f"Then {gesture.effect}, and the hurt began to soften and fall.")

    a.memes["hurt"] = 0
    b.memes["hurt"] = 0
    a.memes["sadness"] = max(0.0, a.memes["sadness"] - 1)
    b.memes["sadness"] = max(0.0, b.memes["sadness"] - 1)
    a.memes["love"] += 2
    b.memes["love"] += 2
    a.memes["peace"] += 2
    b.memes["peace"] += 2
    world.say(f"They said, \"I'm sorry,\" and \"I forgive you,\" as soft as falling rain.")
    world.say(f"Their love came back warm and round, like the sun after rain.")

    world.para()
    world.say(f"To mend the moment, they shared {snack}, and the little room grew bright again.")
    if gesture.id == "gift":
        world.say("The ribbon bow shone like a moonbeam on the toy lamb.")
    elif gesture.id == "song":
        world.say("And the tune they sang together made the teacups seem to dance.")
    else:
        world.say("They hugged so close that even the mouse in the wall felt glad.")
    world.say("So the friends were friends once more, and the night sang softly on.")
    world.facts.update(song=song, conflict=conflict, gesture=gesture, a=a, b=b, snack=snack)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    song: Sound = f["song"]
    conflict: Conflict = f["conflict"]
    gesture: PeaceGesture = f["gesture"]
    a: Entity = f["a"]
    b: Entity = f["b"]
    return [
        f"Write a nursery-rhyme style story about {a.label} and {b.label}, including the word love.",
        f"Tell a little story where a small quarrel happens during {song.phrase}, then {gesture.phrase} helps the friends make peace.",
        f"Write a gentle rhyme about {conflict.label} turning into reconciliation and love again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a: Entity = f["a"]
    b: Entity = f["b"]
    conflict: Conflict = f["conflict"]
    gesture: PeaceGesture = f["gesture"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a.label} and {b.label}, two little friends who had a small quarrel and then made peace again. The story follows how their feelings changed from hurt to love.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"The trouble came from {conflict.cause}. That small mistake made both children feel hurt for a moment.",
        ),
        QAItem(
            question="How did they reconcile?",
            answer=f"They reconciled when they used {gesture.phrase}. That gentle act helped them say sorry, forgive each other, and bring back their love.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset with each other and make peace again. It is when they forgive, mend the trouble, and feel friendly once more.",
        ),
        QAItem(
            question="Why are nursery rhymes often bouncy and short?",
            answer="Nursery rhymes are often bouncy and short because they are easy to remember and pleasant to say aloud. Their rhythm helps little listeners follow the story and the music of the words.",
        ),
        QAItem(
            question="What is love in a gentle story?",
            answer="Love is a warm feeling of caring, kindness, and closeness. In a gentle story, love can show up as helping, forgiving, hugging, and wanting to be kind again.",
        ),
    ]


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
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
peace(G) :- gesture(G), warmth(G, W), tension(C, T), W >= T.
valid(S, C, G) :- song(S), conflict(C), gesture(G), peace(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SONGS:
        lines.append(asp.fact("song", sid))
    for cid, c in CONFLICTS.items():
        lines.append(asp.fact("conflict", cid))
        lines.append(asp.fact("tension", cid, c.tension))
    for gid, g in GESTURES.items():
        lines.append(asp.fact("gesture", gid))
        lines.append(asp.fact("warmth", gid, g.warmth))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"FAIL: generation smoke test crashed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld of love and reconciliation.")
    ap.add_argument("--song", choices=SONGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--gesture", choices=GESTURES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.song is None or c[0] == args.song)
              and (args.conflict is None or c[1] == args.conflict)
              and (args.gesture is None or c[2] == args.gesture)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    song, conflict, gesture = rng.choice(sorted(combos))
    (a, ag), (b, bg) = choose_child_names(rng)
    return StoryParams(song=song, conflict=conflict, gesture=gesture,
                       child_a=a, child_a_gender=ag, child_b=b, child_b_gender=bg)


def generate(params: StoryParams) -> StorySample:
    if params.song not in SONGS or params.conflict not in CONFLICTS or params.gesture not in GESTURES:
        raise StoryError("Invalid story parameters.")
    song = SONGS[params.song]
    conflict = CONFLICTS[params.conflict]
    gesture = GESTURES[params.gesture]
    if not reasonableness_gate(conflict, gesture):
        raise StoryError("This gesture is too small for the quarrel.")
    world = tell(song, conflict, gesture, params.child_a, params.child_a_gender,
                 params.child_b, params.child_b_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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
        print(f"{len(combos)} compatible combos:\n")
        for song, conflict, gesture in combos:
            print(f"  {song:9} {conflict:12} {gesture}")
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
