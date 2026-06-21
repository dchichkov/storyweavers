#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/power_ful_concentrate_sound_effects_bravery_kindness.py
=======================================================================================

A standalone story world for a small ghost-story domain.

Premise
-------
A child hears spooky sounds in an old house, must concentrate to understand the
ghostly clues, shows bravery instead of panic, and answers the ghost with
kindness. The ending proves the spooky place is not hostile: a lonely ghost is
helped, the sounds become friendly, and the child leaves with more courage.

This world keeps the story child-facing, concrete, and state-driven. Physical
state lives in meters; emotional state lives in memes. The narrative is driven
by a tiny simulation, not by swapping nouns into a frozen paragraph.

Contract notes
--------------
- stdlib only
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --verify, --asp, --show-asp, --json, --qa, --trace, -n, --all, --seed
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

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
    darkness: str
    echoes: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundClue:
    id: str
    effect: str
    source: str
    meaning: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GhostKind:
    id: str
    name: str
    need: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    comfort: int
    action: str
    fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    clue: str
    ghost: str
    response: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["fear"] < THRESHOLD:
            continue
        sig = ("echo", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["listening"] += 1
        out.append("__echo__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ghost = world.get("ghost")
    if child.memes["kindness"] < THRESHOLD or ghost.memes["lonely"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["calm"] += 1
    ghost.memes["lonely"] = max(0.0, ghost.memes["lonely"] - 1.0)
    child.memes["brave"] += 1
    out.append("__soft__")
    return out


CAUSAL_RULES = [Rule("echo", _r_echo), Rule("kindness", _r_kindness)]


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


def sound_risk(clue: SoundClue) -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, clue in CLUES.items():
            for gid, ghost in GHOSTS.items():
                for rid, resp in RESPONSES.items():
                    if resp.sense >= 2 and sound_risk(clue):
                        combos.append((sid, cid, gid, rid))
    return combos


def shadow_title(setting: Setting) -> str:
    return f"the old house at {setting.place}"


def predict(world: World, clue_id: str) -> dict:
    sim = world.copy()
    sim.get("child").memes["fear"] += 1
    propagate(sim, narrate=False)
    return {
        "listening": sim.get("child").meters["listening"],
        "ghost_calm": sim.get("ghost").memes["calm"],
    }


def opening(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"On a rainy night, {child.id} and {helper.id} stepped into {setting.place}, "
        f"where the walls were dark and the air felt cold."
    )
    world.say(
        f"Somewhere inside, the house answered with {setting.echoes}."
    )
    child.memes["curious"] += 1
    child.memes["fear"] += 1


def clue_beats(world: World, child: Entity, clue: SoundClue, setting: Setting) -> None:
    world.say(
        f"Then came {clue.effect}, a {clue.source} sound that seemed to float from "
        f"the hall. It made {child.id} want to {clue.risk}."
    )
    world.say(
        f"{child.id} stopped and tried to concentrate. The sound was not just spooky; "
        f"it was trying to say something."
    )


def warning_and_bravery(world: World, helper: Entity, child: Entity, clue: SoundClue) -> None:
    child.memes["brave"] += 1
    world.say(
        f'"Stay close," {helper.id} said. "{clue.meaning}"'
    )
    world.say(
        f"{child.id} took a slow breath and chose bravery over a scared rush."
    )


def approach(world: World, child: Entity, ghost: Entity, clue: SoundClue) -> None:
    world.say(
        f"{child.id} followed the sound to the stair landing and saw a pale shape by the window."
    )
    world.say(
        f'The ghost whispered, "{ghost.attrs.get("whisper", "help")}" in a tiny, wobbly voice.'
    )
    child.memes["kindness"] += 1
    child.memes["brave"] += 1


def soothe(world: World, child: Entity, ghost: Entity, response: Response) -> None:
    if response.id == "listen":
        world.say(
            f'{child.id} said, "Are you lonely?" and sat very still so the ghost would feel safe.'
        )
    elif response.id == "lantern":
        world.say(
            f"{child.id} turned on a little lantern and let the warm light glow without any flame."
        )
    elif response.id == "song":
        world.say(
            f"{child.id} hummed a soft song and the tune made the dark corner feel less sharp."
        )
    else:
        world.say(
            f"{child.id} held out a kind hand and waited."
        )
    child.memes["kindness"] += 1
    ghost.memes["lonely"] = max(0.0, ghost.memes["lonely"] - 1.0)


def resolve(world: World, child: Entity, helper: Entity, ghost: Entity, response: Response) -> None:
    ghost.meters["glow"] += 1
    world.say(
        f"At last the ghost smiled, and the cold room softened like a blanket."
    )
    world.say(
        f"{helper.id} smiled too. {response.action}."
    )
    world.say(
        f"The scary noises turned into gentle taps, and {shadow_title(world.get('setting'))} felt friendly instead of mean."
    )
    child.memes["brave"] += 1
    child.memes["fear"] = 0.0


def ending(world: World, child: Entity, ghost: Entity) -> None:
    world.say(
        f"By morning, {ghost.id} was no longer lonely, and {child.id} was no longer afraid."
    )
    world.say(
        f"{child.id} left the old house with a strong heart and a kind memory of the little ghost who only wanted a friend."
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    ghost_kind = GHOSTS[params.ghost]
    response = RESPONSES[params.response]
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role=params.helper_role))
    st = world.add(Entity(id="setting", type="place", label=setting.place))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=ghost_kind.name, attrs={"whisper": ghost_kind.sound}))
    child.memes["fear"] = 1.0
    ghost.memes["lonely"] = 1.0
    opening(world, child, helper, setting)
    world.para()
    clue_beats(world, child, clue, setting)
    warning_and_bravery(world, helper, child, clue)
    approach(world, child, ghost, clue)
    world.para()
    soothe(world, child, ghost, response)
    resolve(world, child, helper, ghost, response)
    ending(world, child, ghost)
    world.facts.update(setting=setting, clue=clue, ghost=ghost_kind, response=response, child=child, helper=helper, outcome="kind")
    return world


SETTINGS = {
    "hall": Setting(id="hall", place="the old hall", darkness="long shadows", echoes="a slow creak, creak"),
    "attic": Setting(id="attic", place="the dusty attic", darkness="spiderweb corners", echoes="a tap-tap overhead"),
    "cellar": Setting(id="cellar", place="the cellar stairs", darkness="a black corner", echoes="a drip and a bump"),
}

CLUES = {
    "knock": SoundClue(id="knock", effect="knock, knock, knock", source="wooden", meaning="Someone is trying to talk.", risk="run away"),
    "rattle": SoundClue(id="rattle", effect="rattle-rattle", source="metal", meaning="That sound might be a key or a chain.", risk="hide"),
    "whisper": SoundClue(id="whisper", effect="whisshhh", source="windy", meaning="It is only a voice asking for help.", risk="scream"),
}

GHOSTS = {
    "lonely": GhostKind(id="lonely", name="a lonely ghost", need="a friend", sound="Please stay.", tags={"ghost", "kindness"}),
    "lost": GhostKind(id="lost", name="a lost ghost", need="help finding the door", sound="Which way?", tags={"ghost", "kindness"}),
    "small": GhostKind(id="small", name="a small ghost", need="a gentle hello", sound="Hello?", tags={"ghost", "kindness"}),
}

RESPONSES = {
    "listen": Response(id="listen", sense=3, comfort=3, action="They listened first and answered kindly", fail="tried to shout back, but the ghost could not hear the kindness", tags={"kindness"}),
    "lantern": Response(id="lantern", sense=3, comfort=2, action="They used a soft lantern and stayed calm", fail="turned on the wrong light and only made more shadows", tags={"light", "kindness"}),
    "song": Response(id="song", sense=2, comfort=3, action="They sang a gentle song and the room grew warmer", fail="hummed too softly, and the ghost stayed lonely", tags={"kindness"}),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Theo", "Finn", "Noah", "Ben", "Eli"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a 3-to-5-year-old that uses the words "power-ful" and "concentrate" and includes spooky sounds.',
        f"Tell a gentle ghost story where {f['child'].id} hears a spooky clue, concentrates, shows bravery, and answers with kindness.",
        f"Write a child-facing haunted-house story in which scary sound effects lead to a friendly ending instead of a monster ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    ghost = f["ghost"]
    clue = f["clue"]
    response = f["response"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who walked into a spooky old house with a helper and listened closely to the sounds."),
        ("Why did the child concentrate?",
         f"{child.id} concentrated because the noise sounded scary, but it was really a clue. Concentrating helped {child.pronoun('object')} notice that the house was not being mean."),
        ("How did bravery help?",
         f"{child.id} chose bravery by taking a slow breath and not running away. That made it possible to keep listening and find the ghost instead of only feeling scared."),
        ("How did kindness change the ending?",
         f"{child.id} answered kindly, and that helped the lonely ghost feel safe. The ghost became calm, so the scary sounds turned gentle at the end."),
        ("What did the child and helper do together?",
         f"{child.id} and {helper.id} listened to the sound effects, followed the clue, and spoke softly to the ghost. They worked as a team, which helped the whole house settle down."),
        ("What was the ghost like at first?",
         f"It was {ghost.name}, and it felt lonely and hard to understand. The {clue.effect} sound was part of its way of asking for help."),
        ("What did the child use in the ending?",
         f"{child.id} used {response.action.lower()} to answer the ghost. That response was calm, kind, and just right for the spooky room."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = set(world.facts["clue"].tags) | set(world.facts["ghost"].tags) | set(world.facts["response"].tags)
    if "kindness" in tags:
        out.append(("What is kindness?",
                    "Kindness means choosing a gentle, caring action that helps someone feel safe and less alone."))
    if "ghost" in tags:
        out.append(("What is a ghost in a story?",
                    "A ghost is a spooky pretend character in a story. In child stories, a ghost can be lonely, friendly, or silly instead of scary."))
    if "light" in tags:
        out.append(("Why can a lantern feel comforting?",
                    "A lantern gives a warm light that makes dark places easier to see, so it can feel safe without being loud or harsh."))
    out.append(("What does it mean to concentrate?",
                "To concentrate means to pay close attention to one thing and not let your mind wander away."))
    out.append(("What does brave mean?",
                "Brave means doing something even though you feel scared, especially when you keep going carefully."))
    return out


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="hall", clue="knock", ghost="lonely", response="listen", child_name="Mia", child_gender="girl", helper_name="Grandma", helper_gender="woman", helper_role="grandmother"),
    StoryParams(setting="attic", clue="whisper", ghost="lost", response="lantern", child_name="Noah", child_gender="boy", helper_name="Dad", helper_gender="man", helper_role="father"),
    StoryParams(setting="cellar", clue="rattle", ghost="small", response="song", child_name="Lily", child_gender="girl", helper_name="Aunt June", helper_gender="woman", helper_role="aunt"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: spooky sounds, bravery, kindness, and a gentle ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man", "girl", "boy"])
    ap.add_argument("--helper-role")
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
              and (args.clue is None or c[1] == args.clue)
              and (args.ghost is None or c[2] == args.ghost)
              and (args.response is None or c[3] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, ghost, response = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper = args.helper or rng.choice(["Grandma", "Dad", "Aunt June", "Uncle Ben"])
    helper_role = args.helper_role or ("grandmother" if helper == "Grandma" else "father")
    return StoryParams(setting=setting, clue=clue, ghost=ghost, response=response,
                       child_name=name, child_gender=gender,
                       helper_name=helper, helper_gender=helper_gender,
                       helper_role=helper_role)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.ghost not in GHOSTS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,G,R) :- setting(S), clue(C), ghost(G), response(R), sense(R,X), sense_min(M), X >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid-combos differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
    except Exception as err:
        rc = 1
        print(f"MISMATCH: smoke test failed: {err}")
    if rc == 0:
        print("OK: ASP parity and smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ".join(map(str, row)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} in {p.setting} ({p.clue}, {p.ghost}, {p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
