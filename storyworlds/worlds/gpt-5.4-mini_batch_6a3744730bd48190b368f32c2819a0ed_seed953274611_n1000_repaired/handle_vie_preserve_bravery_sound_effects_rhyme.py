#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/handle_vie_preserve_bravery_sound_effects_rhyme.py
===================================================================================

A tiny rhyming storyworld about two children, a noisy handle, a little contest to
be brave, and a choice to preserve something precious.

The seed words are woven into the world model:
- handle: a physical thing that can squeak or turn
- vie: the children compete to be the first brave one
- preserve: the parent or child tries to keep something safe, intact, or neat

The story style is child-facing and rhymed in short beats, with sound effects
driven by simulated state. The world tracks bravery, noise, and preservation as
meters and emotions as memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Handle:
    id: str
    label: str
    sound: str
    action: str
    can_squeak: bool = False
    can_spin: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    protect_word: str
    fragile: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Situation:
    id: str
    place: str
    rhyme_beat: str
    mood_word: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    situation: str
    handle: str
    treasure: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SITUATIONS = {
    "attic": Situation("attic", "the attic", "soft and bright", "brave"),
    "garden_gate": Situation("garden_gate", "the garden gate", "old and gray", "bold"),
    "toy_box": Situation("toy_box", "the toy box", "tiny and neat", "kind"),
}

HANDLES = {
    "rusty_gate": Handle("rusty_gate", "the handle", "creeeak", "turn", can_squeak=True),
    "music_box": Handle("music_box", "the little handle", "twirl", "wind", can_spin=True),
    "drawer": Handle("drawer", "the drawer handle", "click", "pull", can_squeak=False),
}

TREASURES = {
    "cookie_jar": Treasure("cookie_jar", "the cookie jar", "a cookie jar", "preserve the cookies"),
    "ribbon_box": Treasure("ribbon_box", "the ribbon box", "a ribbon box", "preserve the ribbons"),
    "bird_nest": Treasure("bird_nest", "the bird nest", "a bird nest", "preserve the nest"),
}

GIRL_NAMES = ["Mia", "Luna", "Zoe", "Nia", "Ruby", "Tess"]
BOY_NAMES = ["Finn", "Owen", "Milo", "Theo", "Jack", "Eli"]
PARENTS = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, sit in SITUATIONS.items():
        for hid, h in HANDLES.items():
            for tid, t in TREASURES.items():
                if sid == "toy_box" and tid == "bird_nest":
                    continue
                if h.can_squeak or h.can_spin:
                    combos.append((sid, hid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming handle storyworld with bravery and preservation.")
    ap.add_argument("--situation", choices=SITUATIONS)
    ap.add_argument("--handle", choices=HANDLES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.situation is None or c[0] == args.situation)
              and (args.handle is None or c[1] == args.handle)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    situation, handle, treasure = rng.choice(sorted(combos))
    c1g = args.child1_gender or rng.choice(["girl", "boy"])
    c2g = args.child2_gender or ("boy" if c1g == "girl" else "girl")
    child1 = args.child1 or _pick_name(rng, c1g)
    child2 = args.child2 or _pick_name(rng, c2g)
    if child2 == child1:
        child2 = _pick_name(rng, c2g)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(
        situation=situation,
        handle=handle,
        treasure=treasure,
        child1=child1,
        child1_gender=c1g,
        child2=child2,
        child2_gender=c2g,
        parent=parent,
    )


def tell(params: StoryParams) -> World:
    world = World()
    sit = SITUATIONS[params.situation]
    h = HANDLES[params.handle]
    t = TREASURES[params.treasure]
    a = world.add(Entity(id=params.child1, kind="character", type=params.child1_gender, role="vie"))
    b = world.add(Entity(id=params.child2, kind="character", type=params.child2_gender, role="helper"))
    p = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    door = world.add(Entity(id="handle", label=h.label, kind="thing"))
    treasure = world.add(Entity(id="treasure", label=t.label, kind="thing"))
    a.memes["bravery"] = 2.0
    b.memes["bravery"] = 3.0
    world.facts["situation"] = sit
    world.facts["handle"] = h
    world.facts["treasure"] = t

    world.say(
        f"In {sit.place}, where the day felt {sit.mood_word} and light, "
        f"{a.id} and {b.id} began to vie."
    )
    world.say(
        f'"Who will try {h.action} the {h.label}?" said {a.id}. '
        f'"I will!" said {b.id}, with a grin so spry.'
    )
    world.say(
        f"Their voices went jolly: \"We can be brave, we can be bright, "
        f"we can try through the day and the late-golden light.\""
    )

    world.para()
    if h.can_squeak:
        a.memes["bravery"] += 1
        b.memes["bravery"] += 1
        world.say(f"{a.id} reached first and gave the handle a pull.")
        world.say(f"{h.sound}! It sang out loud, not quiet but full.")
    else:
        world.say(f"{b.id} gave the handle a twist with a steady small grin.")
        world.say(f"{h.sound}! It answered with a tidy little spin.")

    preserve_turn = False
    if t.fragile:
        preserve_turn = True
        p.memes["care"] = 1.0
        world.say(
            f"Then {p.label_word} said softly, \"Let's preserve {t.phrase}; "
            f"we'll handle it gently and keep it in place.\""
        )
        world.say(
            f"So they swapped to a careful plan, step by step, with grace."
        )

    world.para()
    a.memes["joy"] = a.memes.get("joy", 0) + 1
    b.memes["joy"] = b.memes.get("joy", 0) + 1
    if preserve_turn:
        world.say(
            f"{a.id} and {b.id} stayed brave, but kind, and did not make a mess."
        )
        world.say(
            f"They tucked {t.label} safe and sound; that was the final success."
        )
    else:
        world.say(
            f"They laughed, and they cheered, and they spun through the air."
        )
        world.say(
            f"The handle went clickety-clack, and the room felt fair and square."
        )

    world.facts["preserve"] = preserve_turn
    world.facts["bravery"] = max(a.memes.get("bravery", 0), b.memes.get("bravery", 0))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the words "handle", '
        f'"vie", and "preserve".',
        f"Tell a brave little rhyme where {f['handle'].label} makes a sound, two kids vie, "
        f"and somebody tries to preserve something precious.",
        f'Write a child-friendly rhyming story with sound effects like "{f["handle"].sound}!" '
        f"and a calm ending about bravery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sit = f["situation"]
    h = f["handle"]
    t = f["treasure"]
    a = world.get(f["situation"].id if False else list(world.entities.keys())[0])
    answers = [
        QAItem(
            question="What did the children want to do?",
            answer=f"They wanted to vie for the first brave turn with {h.label}. "
                   f"They were excited, and the sound of the handle made the game feel daring.",
        ),
        QAItem(
            question="Why did they try to preserve the treasure?",
            answer=f"They wanted to keep {t.phrase} safe and neat. "
                   f"That way the fun could stay gentle, and nothing precious would be ruined.",
        ),
    ]
    if f.get("preserve"):
        answers.append(QAItem(
            question="How did the story turn out?",
            answer=f"It ended well. The children stayed brave, used careful hands, and "
                   f"preserved {t.phrase} while enjoying the noisy handle.",
        ))
    else:
        answers.append(QAItem(
            question="How did the story turn out?",
            answer="It ended with laughter and a bright, brave feeling. "
                   "The children took turns and kept the day playful.",
        ))
    return answers


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    h = f["handle"]
    t = f["treasure"]
    return [
        QAItem(
            question="What is a handle?",
            answer="A handle is a part you hold to open, turn, pull, or push something. "
                   "It helps people move doors, drawers, lids, and little machines.",
        ),
        QAItem(
            question="What does brave mean?",
            answer="Brave means you try something hard or a little scary while staying calm. "
                   "A brave child can still be gentle and careful.",
        ),
        QAItem(
            question=f"What does {h.sound}! sound like?",
            answer=f"It sounds like a quick, lively noise the handle makes when it moves. "
                   f"The story uses sound effects to make the moment feel real.",
        ),
        QAItem(
            question="What does preserve mean?",
            answer="Preserve means keep something safe, whole, or unchanged. "
                   "You preserve a thing when you protect it from damage or mess.",
        ),
        QAItem(
            question="Why do rhyming stories feel fun?",
            answer="Rhymes make words echo each other, so the story feels musical and easy to remember. "
                   "That playful sound helps the tale feel bright and bouncy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:8}) meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        situation="attic",
        handle="rusty_gate",
        treasure="cookie_jar",
        child1="Mia",
        child1_gender="girl",
        child2="Finn",
        child2_gender="boy",
        parent="mother",
    ),
    StoryParams(
        situation="garden_gate",
        handle="music_box",
        treasure="ribbon_box",
        child1="Theo",
        child1_gender="boy",
        child2="Luna",
        child2_gender="girl",
        parent="father",
    ),
    StoryParams(
        situation="toy_box",
        handle="drawer",
        treasure="bird_nest",
        child1="Ruby",
        child1_gender="girl",
        child2="Owen",
        child2_gender="boy",
        parent="mother",
    ),
]


ASP_RULES = r"""
valid(S, H, T) :- situation(S), handle(H), treasure(T), not invalid_combo(S, H, T).
invalid_combo("toy_box", _, "bird_nest").
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SITUATIONS:
        lines.append(asp.fact("situation", sid))
    for hid in HANDLES:
        lines.append(asp.fact("handle", hid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    ok = 0
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        ok = 1
        print("MISMATCH in valid combos:")
        print("  only in python:", sorted(python_set - clingo_set))
        print("  only in clingo:", sorted(clingo_set - python_set))
    try:
        sample = generate(resolve_params(argparse.Namespace(
            situation=None, handle=None, treasure=None,
            child1=None, child1_gender=None, child2=None, child2_gender=None,
            parent=None, seed=None, all=False, trace=False, qa=False, json=False,
            asp=False, verify=False, show_asp=False, n=1
        ), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return ok


def generate(params: StoryParams) -> StorySample:
    if params.situation not in SITUATIONS:
        raise StoryError(f"Unknown situation: {params.situation}")
    if params.handle not in HANDLES:
        raise StoryError(f"Unknown handle: {params.handle}")
    if params.treasure not in TREASURES:
        raise StoryError(f"Unknown treasure: {params.treasure}")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.situation is None or c[0] == args.situation)
              and (args.handle is None or c[1] == args.handle)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    situation, handle, treasure = rng.choice(sorted(combos))
    c1g = args.child1_gender or rng.choice(["girl", "boy"])
    c2g = args.child2_gender or ("boy" if c1g == "girl" else "girl")
    return StoryParams(
        situation=situation,
        handle=handle,
        treasure=treasure,
        child1=args.child1 or _pick_name(rng, c1g),
        child1_gender=c1g,
        child2=args.child2 or _pick_name(rng, c2g),
        child2_gender=c2g,
        parent=args.parent or rng.choice(PARENTS),
    )


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_story_params_default(rng: random.Random) -> StoryParams:
    return resolve_params(argparse.Namespace(
        situation=None, handle=None, treasure=None,
        child1=None, child1_gender=None, child2=None, child2_gender=None,
        parent=None
    ), rng)


def build_parser_and_defaults() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for s, h, t in combos:
            print(f"{s} {h} {t}")
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
