#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/polite_ironic_lesson_learned_suspense_cautionary_ghost.py
==========================================================================================

A small storyworld for a ghost-story style tale with the seed words
"polite" and "ironic", plus the features Lesson Learned, Suspense, and
Cautionary.

Premise:
A child hears a polite knock in an old house at night, follows a suspiciously
polite clue, and learns not to chase strange noises alone. The ghost is not
mean; the lesson is caution, not cruelty.

The world is intentionally compact: one child, one helper adult, one ghost,
one important object, and one dark place. State changes drive the prose:
cold spots deepen, fear rises, a lantern helps, and a truthful solution
clears the house.

The script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a reasonableness gate with an inline ASP twin
- three Q&A sets grounded in world state
- support for --verify, --asp, --show-asp, --qa, --json, --trace, --all, -n
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

GHOST_THRESHOLD = 1.0
SCARED_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
class Setting:
    id: str
    place: str
    dark_spot: str
    echo: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ghost:
    id: str
    name: str
    clue: str
    sound: str
    chill: str
    reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    helpful: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    ghost: str
    object: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
    seed: Optional[int] = None


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


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    if not ghost or ghost.meters["haunt"] < GHOST_THRESHOLD:
        return out
    sig = ("cold",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "child" in world.entities:
        world.get("child").memes["fear"] += 1
    if "helper" in world.entities:
        world.get("helper").memes["alert"] += 1
    world.get("setting").meters["chill"] += 1
    out.append("__cold__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_cold,):
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def available_settings() -> dict[str, Setting]:
    return SETTINGS


def available_ghosts() -> dict[str, Ghost]:
    return GHOSTS


def available_objects() -> dict[str, ObjectThing]:
    return OBJECTS


def reasonableness_ok(setting: Setting, ghost: Ghost, obj: ObjectThing) -> bool:
    return "ghost" in setting.tags and "lesson" in ghost.tags and "lantern" in obj.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for gid, g in GHOSTS.items():
            for oid, o in OBJECTS.items():
                if reasonableness_ok(s, g, o):
                    combos.append((sid, gid, oid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story world with polite, ironic suspense and a lesson learned."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--helper-role", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.setting and args.ghost and args.object:
        s, g, o = SETTINGS[args.setting], GHOSTS[args.ghost], OBJECTS[args.object]
        if not reasonableness_ok(s, g, o):
            raise StoryError("That combination does not make a sensible ghost story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.ghost is None or c[1] == args.ghost)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, ghost, obj = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_role = args.helper_role or rng.choice(["mother", "father", "grandmother", "grandfather"])
    helper_name = args.helper or rng.choice(HELPER_NAMES[helper_role])
    return StoryParams(
        setting=setting,
        ghost=ghost,
        object=obj,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender="woman" if helper_role in {"mother", "grandmother"} else "man",
        helper_role=helper_role,
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    ghost = GHOSTS[params.ghost]
    obj = OBJECTS[params.object]

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper", label=f"the {params.helper_role}"))
    place = world.add(Entity(id="setting", type="place", label=setting.place, tags=set(setting.tags)))
    specter = world.add(Entity(id="ghost", type="ghost", label=ghost.name, role="haunting", tags=set(ghost.tags)))
    thing = world.add(Entity(id="object", type="thing", label=obj.label, role="clue", tags=set(obj.tags)))

    child.memes["curiosity"] += 1
    child.memes["polite"] += 1
    child.meters["night"] += 1
    specter.meters["haunt"] += 1
    place.meters["chill"] += 1

    world.say(
        f"On a rainy night, {child.id} walked through {setting.place} with a small, "
        f"polite whisper in {child.pronoun('possessive')} throat."
    )
    world.say(
        f"Then came a knock from {setting.dark_spot}, soft and {ghost.clue.lower()}. "
        f"It was {ghost.reason}, which felt strange and ironic."
    )
    world.para()
    world.say(
        f"{child.id} leaned toward the dark. {setting.echo} seemed to answer every step."
    )
    child.memes["fear"] += 1
    child.memes["caution"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{ghost.sound} drifted out of the shadows, and the air turned {ghost.chill}."
    )
    world.say(
        f'"{child.id}," {helper.id} called gently, "do not follow strange noises alone.'
        f" Come here with me."
    )
    world.para()

    child.memes["obedience"] += 1
    world.say(
        f"{child.id} stopped. {child.id} looked at the door, then at {helper.id}, and "
        f"chose to stay where the lamp could reach."
    )
    world.say(
        f"Together they found the {thing.label} by the stairs. It matched the note "
        f"left by the ghost, and that was the ironic part: the spooky visitor only "
        f"wanted help."
    )
    world.say(
        f"{helper.id} picked up the {thing.label} and read the note aloud. "
        f"The ghost's voice went quiet, and the cold spot eased."
    )

    specter.meters["haunt"] = 0.0
    place.meters["chill"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.para()
    world.say(
        f"After that, the ghost gave one last polite tap, like a thank-you, and the "
        f"house felt warm again."
    )
    world.say(
        f"{child.id} went to bed with the lesson tucked safely in {child.pronoun('possessive')} mind: "
        f"when a night sound feels strange, call a grown-up and do not chase it alone."
    )

    world.facts.update(
        child=child,
        helper=helper,
        setting=setting,
        ghost=ghost,
        object=obj,
        night_sound=ghost.sound,
        lesson="call a grown-up and do not chase strange sounds alone",
        polite=True,
        ironic=True,
        suspense=True,
        cautionary=True,
        resolved=True,
        cold=place.meters["chill"] > 0,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a 3-to-5-year-old that includes the words "polite" and "ironic".',
        f"Tell a suspenseful cautionary story where {f['child'].id} hears a strange sound in {f['setting'].place} and learns to call a grown-up instead of following it.",
        f"Write a lesson-learned ghost story with a gentle ending, a polite ghost, and a spooky but safe mystery under the stairs.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    ghost = f["ghost"]
    obj = f["object"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, {helper.id}, and a ghost in {setting.place}. The story stays small and child-sized, so the suspense comes from the dark place and the strange sound.",
        ),
        QAItem(
            question="Why was the ghost story ironic?",
            answer=f"The ghost sounded spooky at first, but it was actually polite and needed help. That is ironic because the thing that seemed frightening turned out to be gentle.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer=f"{f['lesson'].capitalize()}. The child learned that a dark sound can feel important, but a grown-up can check it safely.",
        ),
        QAItem(
            question=f"What did {child.id} do when the sound got scary?",
            answer=f"{child.id} stopped and stayed near the lamp instead of following the noise. That choice kept {child.id} safe while {helper.id} handled the mystery.",
        ),
        QAItem(
            question=f"What did the helper find near the stairs?",
            answer=f"{helper.id} found the {obj.label} and the note that explained the ghost's polite request. That solved the mystery without anyone needing to be brave in a foolish way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["ghost"].tags) | set(world.facts["object"].tags) | set(world.facts["setting"].tags)
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            for q, a in KNOWLEDGE[key]:
                out.append(QAItem(question=q, answer=a))
    return out


KNOWLEDGE = {
    "polite": [("What does polite mean?",
                "Polite means kind and respectful. Polite words help people feel calm and safe.")],
    "ghost": [("What is a ghost in a story?",
               "A ghost in a story is a spooky character that can make a place feel mysterious.")],
    "lantern": [("What is a lantern for?",
                 "A lantern gives light in the dark. It helps people see without needing to feel scared of the shadows.")],
    "stairs": [("Why can stairs feel spooky at night?",
                 "Stairs can feel spooky because shadows gather there and sounds echo up and down them.")],
    "lesson": [("What is a lesson learned?",
                "A lesson learned is something a character understands better after something happens.")],
    "cautionary": [("What is a cautionary story?",
                     "A cautionary story warns about a choice that could be unsafe and shows a better choice.")],
    "suspense": [("What is suspense?",
                  "Suspense is the feeling of wondering what will happen next.")],
    "ironic": [("What does ironic mean?",
                "Ironic means something turns out in a surprising way, often different from what you first expect.")],
}
KNOWLEDGE_ORDER = ["polite", "ghost", "lantern", "stairs", "lesson", "cautionary", "suspense", "ironic"]


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.ghost not in GHOSTS:
        raise StoryError(f"Unknown ghost: {params.ghost}")
    if params.object not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object}")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


SETTINGS = {
    "old_house": Setting(
        id="old_house",
        place="the old house",
        dark_spot="the narrow stairs",
        echo="Every board gave a tiny creak",
        tags={"ghost", "stairs"},
    ),
    "attic": Setting(
        id="attic",
        place="the attic",
        dark_spot="the attic door",
        echo="The rafters answered with a hollow sigh",
        tags={"ghost", "stairs"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the long hallway",
        dark_spot="the cracked mirror at the end",
        echo="The hall stretched every footstep",
        tags={"ghost", "mirror"},
    ),
}

GHOSTS = {
    "bell": Ghost(
        id="bell",
        name="Bell Ghost",
        clue="polite",
        sound="A soft tap-tap-tap",
        chill="icy",
        reason="it wanted its little bell back",
        tags={"lesson", "polite", "ghost"},
    ),
    "note": Ghost(
        id="note",
        name="Note Ghost",
        clue="polite",
        sound="A tiny scratch of paper",
        chill="cold",
        reason="it had left a note under the stairs",
        tags={"lesson", "polite", "ghost"},
    ),
    "key": Ghost(
        id="key",
        name="Key Ghost",
        clue="polite",
        sound="A careful knock",
        chill="shivery",
        reason="it was looking for a brass key",
        tags={"lesson", "polite", "ghost"},
    ),
}

OBJECTS = {
    "lantern": ObjectThing(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        helpful=True,
        tags={"lantern"},
    ),
    "bell": ObjectThing(
        id="bell",
        label="little bell",
        phrase="a little bell",
        helpful=True,
        tags={"lesson"},
    ),
    "key": ObjectThing(
        id="key",
        label="brass key",
        phrase="a brass key",
        helpful=True,
        tags={"lesson"},
    ),
}

GIRL_NAMES = ["Maya", "Nora", "Lily", "Ivy", "Clara"]
BOY_NAMES = ["Theo", "Finn", "Noah", "Eli", "Sam"]
HELPER_NAMES = {
    "mother": ["Mom", "Anna", "Rose"],
    "father": ["Dad", "Ben", "Mark"],
    "grandmother": ["Gran", "Mabel", "June"],
    "grandfather": ["Grandpa", "Arthur", "Hank"],
}


def explain_rejection(setting: Setting, ghost: Ghost, obj: ObjectThing) -> str:
    return "(No story: this setup is not spooky-cautionary enough for the ghost-story world.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("setting_tag", sid, t))
    for gid, g in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        for t in sorted(g.tags):
            lines.append(asp.fact("ghost_tag", gid, t))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        for t in sorted(o.tags):
            lines.append(asp.fact("object_tag", oid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, G, O) :- setting(S), ghost(G), object(O),
                  setting_tag(S, ghost),
                  ghost_tag(G, lesson),
                  object_tag(O, lantern).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity:")
        if a - p:
            print("  only in ASP:", sorted(a - p))
        if p - a:
            print("  only in Python:", sorted(p - a))
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, ghost=None, object=None, name=None, helper=None,
            helper_role=None, gender=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def sensibly_valid() -> list[tuple[str, str, str]]:
    return valid_combos()


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
        for s, g, o in combos:
            print(f"  {s:10} {g:8} {o}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="old_house", ghost="bell", object="lantern", child_name="Maya", child_gender="girl", helper_name="Mom", helper_gender="woman", helper_role="mother"),
            StoryParams(setting="attic", ghost="note", object="lantern", child_name="Theo", child_gender="boy", helper_name="Gran", helper_gender="woman", helper_role="grandmother"),
            StoryParams(setting="hallway", ghost="key", object="lantern", child_name="Nora", child_gender="girl", helper_name="Dad", helper_gender="man", helper_role="father"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and the {p.ghost} ghost in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
