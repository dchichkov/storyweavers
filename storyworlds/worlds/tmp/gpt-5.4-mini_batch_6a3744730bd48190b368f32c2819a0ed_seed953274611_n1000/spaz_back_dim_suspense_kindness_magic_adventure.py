#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spaz_back_dim_suspense_kindness_magic_adventure.py
===================================================================================

A standalone storyworld for a small adventure tale with suspense, kindness, and
a little magic. The seed words "spaz" and "back-dim" are kept in play as a
made-up creature name and a dim back passage.

This world simulates:
- a child explorer,
- a tense dim passage with a hidden object,
- a magical helper and a kind choice,
- a suspenseful turn,
- an ending image that proves the change.

The world is intentionally small and classical: the same core state drives the
story, Q&A, trace output, and the ASP twin.
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
MOOD_WARM = 1.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Token:
    id: str
    label: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    hidden_in: str
    requires: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
class StoryParams:
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    mentor: str
    mentor_gender: str
    setting: str
    token: str
    relic: str
    tool: str
    response: str
    seed: Optional[int] = None


class Rule:
    def __init__(self, name: str, apply: Callable[[World], list[str]]) -> None:
        self.name = name
        self.apply = apply


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("ritual_awake") and not world.facts.get("relic_found"):
        for e in world.entities.values():
            if e.role in {"hero", "friend"}:
                e.memes["worry"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def setup_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.token not in TOKENS or params.relic not in RELICS or params.tool not in TOOLS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters for this storyworld.")
    if params.response in LOW_SENSE_RESPONSES:
        raise StoryError(explain_response(params.response))

    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend"))
    mentor = world.add(Entity(id=params.mentor, kind="character", type=params.mentor_gender, role="mentor", label="the old guide"))
    world.add(Entity(id="place", type="place", label=SETTINGS[params.setting].label))
    world.add(Entity(id="token", type="token", label=TOKENS[params.token].label))
    world.add(Entity(id="relic", type="relic", label=RELICS[params.relic].label))
    world.add(Entity(id="tool", type="tool", label=TOOLS[params.tool].label))

    hero.memes["curiosity"] = 2.0
    friend.memes["kindness"] = 1.0
    mentor.memes["calm"] = 2.0
    world.facts["ritual_awake"] = True
    world.facts["relic_found"] = False
    return world


@dataclass
class Setting:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "back_dim": Setting(id="back_dim", label="the back-dim passage", tags={"back-dim", "dim"}),
    "harbor_cave": Setting(id="harbor_cave", label="the harbor cave", tags={"adventure", "dim"}),
    "moon_hall": Setting(id="moon_hall", label="the moonlit hall", tags={"magic", "dim"}),
}

TOKENS = {
    "spaz": Token(id="spaz", label="spaz", kind="creature", tags={"spaz", "creature"}),
    "lantern": Token(id="lantern", label="little lantern", kind="light", tags={"light"}),
    "map": Token(id="map", label="folded map", kind="map", tags={"map"}),
}

RELICS = {
    "bell": Relic(id="bell", label="silver bell", phrase="a silver bell", hidden_in="back-dim", requires="kindness", tags={"magic", "kindness"}),
    "seed": Relic(id="seed", label="glow seed", phrase="a glow seed", hidden_in="back-dim", requires="magic", tags={"magic"}),
    "key": Relic(id="key", label="small key", phrase="a small key", hidden_in="back-dim", requires="suspense", tags={"adventure"}),
}

TOOLS = {
    "charm": MagicTool(id="charm", label="shimmer charm", phrase="a shimmer charm", effect="glowed softly", tags={"magic"}),
    "song": MagicTool(id="song", label="humming song", phrase="a humming song", effect="warmed the air", tags={"kindness"}),
    "spark": MagicTool(id="spark", label="bright spark", phrase="a bright spark", effect="lit the path", tags={"magic"}),
}

RESPONSES = {
    "calm_hug": Response(id="calm_hug", sense=3, power=3,
                         text="held the frightened spaz close, then used the charm to light the way",
                         fail="held the frightened spaz close, but the dark stayed thick",
                         qa_text="held the frightened spaz close and used the charm to light the way",
                         tags={"kindness", "magic"}),
    "song_spell": Response(id="song_spell", sense=3, power=2,
                           text="sang a soft song and the shimmer charm answered with a warm glow",
                           fail="sang a soft song, but the shadows did not move",
                           qa_text="sang a soft song and let the shimmer charm answer with a warm glow",
                           tags={"kindness", "magic"}),
    "scatter": Response(id="scatter", sense=1, power=1,
                        text="ran in circles and made everything more confused",
                        fail="ran in circles and helped no one",
                        qa_text="ran in circles",
                        tags={"panic"}),
}

LOW_SENSE_RESPONSES = {"scatter"}

GIRL_NAMES = ["Lina", "Mira", "Nia", "Tess", "Ada", "Zara"]
BOY_NAMES = ["Rian", "Otto", "Jules", "Pax", "Nico", "Bram"]
TRAITS = ["brave", "gentle", "curious", "careful", "steady"]


def explain_response(rid: str) -> str:
    return f"(Refusing response '{rid}': it is too frantic for a story built on kindness and magic.)"


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for t in TOKENS:
            for r in RELICS:
                for tool in TOOLS:
                    out.append((s, t, r, tool))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure world of suspense, kindness, and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--mentor")
    ap.add_argument("--mentor-gender", choices=["woman", "man"])
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
    if args.response and args.response in LOW_SENSE_RESPONSES:
        raise StoryError(explain_response(args.response))
    setting = args.setting or rng.choice(list(SETTINGS))
    token = args.token or rng.choice(list(TOKENS))
    relic = args.relic or rng.choice(list(RELICS))
    tool = args.tool or rng.choice(list(TOOLS))
    response = args.response or rng.choice([k for k in RESPONSES if k not in LOW_SENSE_RESPONSES])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    mentor_gender = args.mentor_gender or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    mentor = args.mentor or rng.choice(["Mara", "Tobin", "Iris", "Hale"])
    return StoryParams(hero=hero, hero_gender=hero_gender, friend=friend, friend_gender=friend_gender,
                       mentor=mentor, mentor_gender=mentor_gender, setting=setting, token=token,
                       relic=relic, tool=tool, response=response)


def _line(world: World, text: str) -> None:
    world.say(text)


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.get(params.hero)
    friend = world.get(params.friend)
    mentor = world.get(params.mentor)
    setting = SETTINGS[params.setting]
    token = TOKENS[params.token]
    relic = RELICS[params.relic]
    tool = TOOLS[params.tool]
    response = RESPONSES[params.response]

    _line(world, f"{hero.id} and {friend.id} went into {setting.label} with {token.label} and a brave heart.")
    _line(world, f"They were chasing a mystery in the back-dim passage, where even small steps sounded loud.")
    _line(world, f"Then {hero.id} spotted {relic.phrase} tucked away where the dark made it hard to see.")

    world.para()
    hero.memes["fear"] += 1
    friend.memes["kindness"] += 1
    _line(world, f'A hush fell over them. "{token.label.capitalize()}," whispered {friend.id}, and the air felt full of suspense.')
    _line(world, f'{hero.id} wanted to reach in at once, but {mentor.label_word if mentor.label else "the guide"} lifted a hand and smiled.')
    _line(world, f'"We can be careful," said {mentor.id}, "and kind, too."')

    world.para()
    if params.response == "calm_hug":
        _line(world, f'{response.text[0].upper()}{response.text[1:]}.')
    else:
        _line(world, f'{response.text[0].upper()}{response.text[1:]}.')
    world.facts["relic_found"] = True
    world.facts["ritual_awake"] = False
    hero.memes["relief"] += 1
    friend.memes["joy"] += 1
    mentor.memes["warmth"] += 1

    world.para()
    _line(world, f"The {tool.label} {tool.effect}, and the {relic.label} came free at last.")
    _line(world, f"It shone in {hero.id}'s hands while {friend.id} grinned, and the back-dim passage did not feel scary anymore.")
    _line(world, f"Together they walked home by the glow, glad they had chosen kindness over panic.")
    world.facts.update(hero=hero, friend=friend, mentor=mentor, setting=setting, token=token, relic=relic, tool=tool, response=response)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a child that uses the words "spaz" and "back-dim" and includes a suspenseful mystery, kindness, and a little magic.',
        f"Tell a gentle adventure where {f['hero'].id} and {f['friend'].id} explore the back-dim passage, meet a spaz, and solve the problem kindly with magic.",
        f'Write a short story with suspense and a happy ending where the back-dim place feels scary at first, but kindness and magic help the children succeed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mentor = f["mentor"]
    relic = f["relic"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What were {hero.id} and {friend.id} looking for?",
            answer=f"They were looking for {relic.phrase}. It was hidden in the back-dim passage, so they had to be careful and brave."
        ),
        QAItem(
            question=f"Why did the scene feel suspenseful?",
            answer=f"The passage was dim and quiet, so every sound seemed bigger than usual. The children did not know what was waiting there until the magical glow appeared."
        ),
        QAItem(
            question=f"How did {mentor.id} help?",
            answer=f"{mentor.id} stayed calm and reminded them to be kind and careful. That steady help gave them a safe way to use the magic and reach the relic."
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The relic was found, the scary darkness was softened by {tool.phrase}, and the children went home happy. The ending shows that kindness and magic turned the tense moment into a safe adventure."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next. It makes a story feel tense until the answer arrives."
        ),
        QAItem(
            question="What does kindness do in a story?",
            answer="Kindness helps characters care for each other and make good choices. It can calm fear and help a problem get solved."
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special that can do impossible-looking things. In adventure stories, it often helps the heroes find a way forward."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(back_dim).
setting(harbor_cave).
setting(moon_hall).

token(spaz).
token(lantern).
token(map).

relic(bell).
relic(seed).
relic(key).

tool(charm).
tool(song).
tool(spark).

response(calm_hug).
response(song_spell).

valid(S,T,R,U) :- setting(S), token(T), relic(R), tool(U).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TOKENS:
        lines.append(asp.fact("token", t))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    for u in TOOLS:
        lines.append(asp.fact("tool", u))
    for resp in RESPONSES:
        lines.append(asp.fact("response", resp))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python combo sets differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.token not in TOKENS or params.relic not in RELICS or params.tool not in TOOLS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(params)
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
    StoryParams(hero="Lina", hero_gender="girl", friend="Pax", friend_gender="boy", mentor="Mara", mentor_gender="woman",
                setting="back_dim", token="spaz", relic="bell", tool="charm", response="calm_hug"),
    StoryParams(hero="Rian", hero_gender="boy", friend="Nia", friend_gender="girl", mentor="Tobin", mentor_gender="man",
                setting="moon_hall", token="map", relic="seed", tool="song", response="song_spell"),
]


def resolve_combos(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_combos(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
