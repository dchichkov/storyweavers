#!/usr/bin/env python3
"""
storyworlds/worlds/jag_playroom_sharing_pirate_tale.py
======================================================

A small storyworld for a pirate-tale sharing scene set in a playroom.

Seed tale:
---
A little child loved pirate play in the playroom. One day, the child found a
jagged toy chest key and wanted to keep it forever. A friend reached for the key
too, because they both wanted the same pirate treasure game. The child grew
grumpy until a parent suggested sharing the key and taking turns opening the
toy chest. In the end, the friends shared the key, opened the chest together,
and the playroom felt friendly again.

The world models:
- a playroom with pirate props
- one special jagged prize that wants to be kept safe
- sharing / taking turns as the main social turn
- a small amount of physical state (meters) and emotional state (memes)
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Lazy ASP import inside helpers only.


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the playroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    zone: set[str]
    plural: bool = False


@dataclass
class SharePrompt:
    id: str
    label: str
    phrase: str
    takes: str
    turns: str
    helper: str


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    parent_type: str
    artifact: str
    seed: Optional[int] = None


SETTINGS = {
    "playroom": Setting(place="the playroom", affords={"share"}),
}

ARTIFACTS = {
    "key": Artifact(
        id="key",
        label="jagged key",
        phrase="a little jagged key",
        type="key",
        risk="lost",
        zone={"hand"},
        plural=False,
    ),
    "map": Artifact(
        id="map",
        label="pirate map",
        phrase="a folded pirate map",
        type="map",
        risk="torn",
        zone={"hand"},
        plural=False,
    ),
    "coin": Artifact(
        id="coin",
        label="gold coin",
        phrase="a shiny gold coin",
        type="coin",
        risk="lost",
        zone={"hand"},
        plural=False,
    ),
}

SHARE_PROMPTS = {
    "key": SharePrompt(
        id="share_key",
        label="take turns",
        phrase="share the jagged key",
        takes="takes a turn with the key",
        turns="take turns opening the toy chest",
        helper="the key",
    ),
    "map": SharePrompt(
        id="share_map",
        label="share the map",
        phrase="share the pirate map",
        takes="takes a turn with the map",
        turns="take turns tracing the treasure path",
        helper="the map",
    ),
    "coin": SharePrompt(
        id="share_coin",
        label="share the coin",
        phrase="share the gold coin",
        takes="takes a turn with the coin",
        turns="take turns hiding the coin",
        helper="the coin",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Ben", "Sam"]
PARENT_TYPES = ["mother", "father"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_grumpy(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.memes.get("want_keep", 0) < THRESHOLD:
            continue
        if hero.memes.get("sharing", 0) >= THRESHOLD:
            continue
        sig = ("grumpy", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["grumpy"] = hero.memes.get("grumpy", 0) + 1
        out.append(f"{hero.id} got grumpy and hugged the treasure close.")
    return out


def _r_shared(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.memes.get("sharing", 0) < THRESHOLD:
            continue
        sig = ("shared", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        hero.memes["grumpy"] = 0
        out.append(f"{hero.id} felt cheerful again.")
    return out


CAUSAL_RULES = [Rule("grumpy", _r_grumpy), Rule("shared", _r_shared)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for line in out:
            world.say(line)
    return out


def predict_grumpy(world: World, hero: Entity, artifact: Artifact) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["want_keep"] = 1
    propagate(sim, narrate=False)
    return sim.get(hero.id).memes.get("grumpy", 0) >= THRESHOLD


def choose_share_prompt(artifact: Artifact) -> SharePrompt:
    if artifact.id not in SHARE_PROMPTS:
        raise StoryError(f"No sharing prompt for artifact '{artifact.id}'.")
    return SHARE_PROMPTS[artifact.id]


def build_story(world: World, hero: Entity, friend: Entity, parent: Entity, artifact: Entity, prompt: SharePrompt) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved pirate games in the playroom."
    )
    world.say(
        f"{hero.id} found {artifact.phrase} and wanted to keep {artifact.it()} forever."
    )
    world.say(
        f"{friend.id} wanted to play too, because {friend.pronoun('subject')} liked pirate treasure games as well."
    )
    world.para()
    world.say(
        f"One day, {hero.id} and {friend.id} knelt by the toy chest in {world.setting.place}."
    )
    world.say(
        f"They both reached for {artifact.it()}, and {hero.id} tried to keep it close."
    )
    hero.memes["want_keep"] = 1
    friend.memes["want_play"] = 1
    if predict_grumpy(world, hero, artifact):
        world.say(
            f"{hero.id} started to feel grumpy because {hero.pronoun('possessive')} pirate treasure did not feel shared."
        )
    propagate(world, narrate=True)
    world.say(
        f'Then {parent.id} smiled and said, "How about you {prompt.label} and {prompt.turns}?"'
    )
    hero.memes["sharing"] = 1
    friend.memes["sharing"] = 1
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"{hero.id} and {friend.id} took turns carefully, and {artifact.label} stayed safe in their hands."
    )
    world.say(
        f"At last, they opened the toy chest together, and the playroom felt warm and friendly again."
    )


def tell(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError("That place is not available in this world.")
    if params.artifact not in ARTIFACTS:
        raise StoryError("That pirate treasure is not available.")
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="the parent"))
    art_cfg = ARTIFACTS[params.artifact]
    artifact = world.add(Entity(
        id=art_cfg.id,
        kind="thing",
        type=art_cfg.type,
        label=art_cfg.label,
        phrase=art_cfg.phrase,
        plural=art_cfg.plural,
    ))
    prompt = choose_share_prompt(art_cfg)
    world.facts.update(hero=hero, friend=friend, parent=parent, artifact=artifact, prompt=prompt, setting=world.setting)
    build_story(world, hero, friend, parent, artifact, prompt)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    artifact = f["artifact"]
    prompt = f["prompt"]
    return [
        f'Write a short pirate-tale story for a young child set in {world.setting.place} about {hero.id} and {friend.id} learning to {prompt.label}.',
        f'Create a gentle story where {hero.id} wants to keep {artifact.phrase}, but {friend.id} needs a turn too.',
        f'Write a playroom pirate story with a jagged treasure and a happy sharing ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    artifact = f["artifact"]
    prompt = f["prompt"]
    return [
        QAItem(
            question=f"Who wanted to keep {artifact.phrase} at first?",
            answer=f"{hero.id} wanted to keep {artifact.phrase} all to {hero.pronoun('object')} self at first.",
        ),
        QAItem(
            question=f"Why did {friend.id} want the pirate treasure too?",
            answer=f"{friend.id} wanted a turn because {friend.pronoun('subject')} liked pirate treasure games and wanted to play with {hero.id}.",
        ),
        QAItem(
            question=f"What did the parent suggest?",
            answer=f"The parent suggested that they {prompt.label} and {prompt.turns}.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{hero.id} and {friend.id} shared {artifact.label}, took turns, and the playroom felt friendly again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too, often by taking turns.",
        ),
        QAItem(
            question="What is a pirate treasure chest?",
            answer="A pirate treasure chest is a box in pirate stories that holds coins, keys, maps, or other hidden treasure.",
        ),
        QAItem(
            question="What is a playroom?",
            answer="A playroom is a room where children can play with toys and games.",
        ),
        QAItem(
            question="What does a jagged thing look like?",
            answer="A jagged thing has rough or sharp edges that do not look smooth.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the artifact is from this world and sharing is needed.
needs_sharing(A) :- artifact(A), shareable(A).
valid_story(playroom, A) :- artifact(A), needs_sharing(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, art in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("shareable", aid))
        lines.append(asp.fact("risk", aid, art.risk))
        for z in sorted(art.zone):
            lines.append(asp.fact("zone", aid, z))
    for pid, prompt in SHARE_PROMPTS.items():
        lines.append(asp.fact("share_prompt", pid))
        lines.append(asp.fact("prompt_for", pid, prompt.helper))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {("playroom", aid) for aid in ARTIFACTS}
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python story set ({len(clingo_set)} artifacts).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale sharing story world in a playroom.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--artifact", choices=list(ARTIFACTS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=PARENT_TYPES)
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
    artifact = args.artifact or rng.choice(list(ARTIFACTS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend_pool = GIRL_NAMES if friend_type == "girl" else BOY_NAMES
    friend_name = args.friend_name or rng.choice([n for n in friend_pool if n != hero_name] or friend_pool)
    parent_type = args.parent_type or rng.choice(PARENT_TYPES)
    return StoryParams(
        place=args.place or "playroom",
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        parent_type=parent_type,
        artifact=artifact,
    )


def generate(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for aid in ARTIFACTS:
            p = StoryParams(
                place="playroom",
                hero_name="Mia",
                hero_type="girl",
                friend_name="Leo",
                friend_type="boy",
                parent_type="mother",
                artifact=aid,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
