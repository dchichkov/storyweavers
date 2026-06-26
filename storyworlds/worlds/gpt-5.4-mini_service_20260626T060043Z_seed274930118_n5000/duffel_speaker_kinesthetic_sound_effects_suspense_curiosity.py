#!/usr/bin/env python3
"""
A small space-adventure story world: a child aboard a ship, a curious mystery,
a duffel bag, and a speaker that helps reveal what is hidden through sound and
kinesthetic clues.

The story logic is state-driven:
- A duffel carries a clue or tool.
- A speaker emits sound effects that guide attention.
- A kinesthetic sensor reads bumps, pulls, and vibrations.
- Suspense builds when the child cannot yet see what is inside.
- Curiosity pushes the child to investigate.
- The ending proves what changed in the world model.

This module follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports results eagerly, asp lazily
- StoryParams, registries, parser, resolver, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    portable: bool = False
    openable: bool = False
    open: bool = False
    loud: bool = False
    sound: str = ""
    kinesthetic: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    investigate: str
    sound: str
    kinesthetic: str
    suspense: str
    curiosity: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectConfig:
    label: str
    phrase: str
    owner_kind: str = "child"
    is_duffel: bool = False
    is_speaker: bool = False
    is_clue: bool = False


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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_speaker(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    speaker = world.facts.get("speaker")
    if not child or not speaker:
        return out
    c = world.get(child.id)
    s = world.get(speaker.id)
    if s.meters.get("powered", 0.0) < THRESHOLD:
        return out
    if c.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("speaker", c.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    c.memes["focus"] = c.memes.get("focus", 0.0) + 1
    out.append(f"The speaker crackled with a soft whoosh and a tiny beep-beep.")
    return out


def _r_duffel_open(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    duffel = world.facts.get("duffel")
    if not child or not duffel:
        return out
    c = world.get(child.id)
    d = world.get(duffel.id)
    if not d.open:
        return out
    sig = ("open", d.id)
    if sig in world.fired:
        return out
    if c.memes.get("suspense", 0.0) < THRESHOLD and c.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    world.fired.add(sig)
    out.append(f"The duffel zipper whispered open, and the mystery inside finally waited in the light.")
    return out


CAUSAL_RULES = [Rule("speaker", _r_speaker), Rule("duffel_open", _r_duffel_open)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "cargo_bay": Setting(
        place="the cargo bay",
        detail="Metal crates floated in neat rows, and blue lights blinked along the floor.",
        affords={"search", "listen", "open"},
    ),
    "observation_deck": Setting(
        place="the observation deck",
        detail="Stars glittered beyond the glass, and the whole room hummed like a sleeping engine.",
        affords={"search", "listen", "open"},
    ),
    "airlock_hall": Setting(
        place="the airlock hall",
        detail="A round door stood at the far end, and the wall pads felt cool under small hands.",
        affords={"search", "listen", "open"},
    ),
}

ACTIVITIES = {
    "search": Activity(
        id="search",
        verb="search the ship",
        gerund="searching the ship",
        investigate="look inside the duffel",
        sound="a soft whirr",
        kinesthetic="a tiny thump in the floor",
        suspense="The answer felt close, but not close enough.",
        curiosity="Curiosity tugged harder and harder.",
        tags={"curiosity", "suspense"},
    ),
    "listen": Activity(
        id="listen",
        verb="listen for the source of the sound",
        gerund="listening for the sound",
        investigate="follow the beep-beep",
        sound="beep-beep",
        kinesthetic="a buzzing vibration through the soles",
        suspense="Something was making noise just out of sight.",
        curiosity="The child wanted to know what it was.",
        tags={"sound", "curiosity"},
    ),
    "open": Activity(
        id="open",
        verb="open the duffel",
        gerund="opening the duffel",
        investigate="peek into the duffel",
        sound="a zipper zzzzzip",
        kinesthetic="a wiggle of the zipper teeth",
        suspense="What was hidden inside?",
        curiosity="The mystery pulled like a magnet.",
        tags={"duffel", "suspense", "curiosity"},
    ),
}

OBJECTS = {
    "duffel": ObjectConfig(
        label="duffel",
        phrase="a navy duffel with a bright orange zipper",
        is_duffel=True,
    ),
    "speaker": ObjectConfig(
        label="speaker",
        phrase="a small ship speaker with a glowing ring",
        is_speaker=True,
    ),
    "beacon": ObjectConfig(
        label="beacon",
        phrase="a silver beacon shaped like a star",
        is_clue=True,
    ),
    "toolkit": ObjectConfig(
        label="toolkit",
        phrase="a tiny toolkit wrapped in foam",
        is_clue=True,
    ),
}

NAMES = ["Ari", "Mina", "Toby", "Nia", "Leo", "Zuri", "Eli", "Pia"]
TRAITS = ["brave", "curious", "alert", "careful", "quick", "bright"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    object: str
    name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for o in OBJECTS:
                combos.append((s, a, o))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with duffel, speaker, kinesthetic clues.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, obj = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        activity=activity,
        object=obj,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def _do_activity(world: World, child: Entity, activity: Activity, narrate: bool = True) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    child.memes["suspense"] = child.memes.get("suspense", 0.0) + 1
    if narrate:
        world.say(f"{child.id} wanted to {activity.verb}, and {activity.suspense}")
        world.say(f"{activity.curiosity}")
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, obj: ObjectConfig, name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child", label=name))
    speaker = world.add(Entity(
        id="speaker", type="speaker", label="speaker", phrase=obj.phrase, loud=True, kinesthetic=True
    ))
    duffel = world.add(Entity(
        id="duffel", type="duffel", label="duffel", phrase=obj.phrase, openable=True, open=False, portable=True
    ))
    clue = world.add(Entity(
        id=obj.label, type=obj.label, label=obj.label, phrase=obj.phrase, portable=True
    ))
    world.facts.update(child=child, speaker=speaker, duffel=duffel, clue=clue, activity=activity, setting=setting)

    world.say(f"{name} was a {trait} little child aboard a ship near {setting.place}.")
    world.say(setting.detail)
    world.say(f"{name} noticed {duffel.phrase} and a {speaker.phrase} tucked beside the wall.")

    world.para()
    child.memes["curiosity"] = 1
    child.memes["suspense"] = 1
    speaker.meters["powered"] = 1
    world.say(f"The speaker made a gentle {activity.sound}, and {name} felt a shiver of curiosity.")
    world.say(f"Something in the ship answered with {activity.kinesthetic}.")

    world.para()
    _do_activity(world, child, activity, narrate=True)

    if activity.id == "open":
        duffel.open = True
        clue.owner = name
        world.say(f"{name} gripped the zipper and opened the duffel.")
        if obj.is_clue:
            world.say(f"Inside was {obj.phrase}, safe and ready to use.")
        else:
            world.say(f"Inside was something useful and shiny, exactly what the ship needed.")
    else:
        duffel.open = True
        clue.owner = name
        world.say(f"{name} followed the sound to the duffel and opened it carefully.")
        world.say(f"Inside was {obj.phrase}, and the mystery finally made sense.")

    child.memes["suspense"] = 0
    child.memes["curiosity"] += 1
    world.say(f"{name} smiled, because the strange sound had turned into a helpful discovery.")

    world.facts.update(resolved=True)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], OBJECTS[params.object], params.name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    act = f["activity"]
    obj = f["clue"]
    return [
        f'Write a short space-adventure story for a young child about curiosity, suspense, and a "{obj.label}" clue.',
        f"Tell a story where {child.id} hears a {act.sound} from a speaker and decides to {act.verb}.",
        f'Write a gentle shipboard mystery featuring a duffel, a speaker, and a surprising discovery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    act = f["activity"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where does {child.id} find the duffel in the story?",
            answer=f"{child.id} finds the duffel aboard the ship near {setting.place}, where the lights glow and the mystery feels close.",
        ),
        QAItem(
            question=f"What sound helped {child.id} decide to keep looking?",
            answer=f"The speaker made {act.sound}, which made {child.id} feel curious and pay attention.",
        ),
        QAItem(
            question=f"What was inside the duffel at the end?",
            answer=f"Inside the duffel was {clue.phrase}, and that was the helpful thing the child had been hunting for.",
        ),
        QAItem(
            question=f"How did the story change by the end?",
            answer=f"At first the ship felt suspenseful and puzzling, but by the end {child.id} had solved the mystery and found a useful clue.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "duffel": [
        QAItem(
            question="What is a duffel bag?",
            answer="A duffel bag is a soft bag with room inside for carrying clothes, tools, or other things.",
        )
    ],
    "speaker": [
        QAItem(
            question="What does a speaker do?",
            answer="A speaker turns sound into something people can hear, like beeps, music, or voices.",
        )
    ],
    "sound": [
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special sounds that help tell a story, like zips, beeps, or whooshes.",
        )
    ],
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn more about something.",
        )
    ],
    "suspense": [
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next because the answer is not known yet.",
        )
    ],
    "kinesthetic": [
        QAItem(
            question="What does kinesthetic mean?",
            answer="Kinesthetic means about body movement or touch, like feeling a bump, vibration, or pull.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["duffel"])
    out.extend(WORLD_KNOWLEDGE["speaker"])
    out.extend(WORLD_KNOWLEDGE["sound"])
    out.extend(WORLD_KNOWLEDGE["curiosity"])
    out.extend(WORLD_KNOWLEDGE["suspense"])
    out.extend(WORLD_KNOWLEDGE["kinesthetic"])
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.openable:
            bits.append(f"open={e.open}")
        if e.loud:
            bits.append("loud")
        if e.kinesthetic:
            bits.append("kinesthetic")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when a child, a speaker, and a duffel exist in the same setting.
child_story(S) :- setting(S), child(C), speaker(P), duffel(D), located_in(C,S), located_in(P,S), located_in(D,S).

% Suspense and curiosity are part of the world if the activity uses sound, touch, or opening a mystery.
uses_suspense(A) :- activity(A), suspenseful(A).
uses_curiosity(A) :- activity(A), curious(A).
uses_kinesthetic(A) :- activity(A), kinesthetic(A).

% A clue is reasonable if the duffel can hold it and the speaker can signal it.
reasonable_story(S,A,O) :- child_story(S), activity(A), object(O), holds_duffel(O), uses_suspense(A), uses_curiosity(A).
#show reasonable_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if "suspense" in a.tags:
            lines.append(asp.fact("suspenseful", aid))
        if "curiosity" in a.tags:
            lines.append(asp.fact("curious", aid))
        if "sound" in a.tags or "duffel" in a.tags:
            lines.append(asp.fact("kinesthetic", aid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.is_duffel:
            lines.append(asp.fact("holds_duffel", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable_story/3."))
    return sorted(set(asp.atoms(model, "reasonable_story")))


def asp_verify() -> int:
    py = {(s, a, o) for s, a, o in valid_combos()}
    asp_set = set(asp_reasonable())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


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
    StoryParams(setting="cargo_bay", activity="listen", object="beacon", name="Ari", trait="curious"),
    StoryParams(setting="observation_deck", activity="search", object="toolkit", name="Mina", trait="alert"),
    StoryParams(setting="airlock_hall", activity="open", object="beacon", name="Toby", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        items = asp_reasonable()
        print(f"{len(items)} reasonable (setting, activity, object) combos:\n")
        for s, a, o in items:
            print(f"  {s:18} {a:10} {o}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
