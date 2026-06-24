#!/usr/bin/env python3
"""
A small fable-style story world about a loud bully, a funny trick, and a team
that stands together.

The source tale that inspired this world:
- A boastful wolf tries to intimidate smaller forest friends.
- The smaller friends laugh together, make a clever plan, and work as a team.
- The wolf loses its power to scare them once the friends help each other.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    teammates: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "fox"}
        masculine = {"boy", "man", "father", "wolf", "crow"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the meadow"
    feature: str = "a wide oak tree"


@dataclass
class Role:
    id: str
    kind: str
    type: str
    label: str
    phrase: str
    traits: list[str] = field(default_factory=list)


@dataclass
class Tale:
    bully_line: str
    laugh_line: str
    teamwork_line: str
    ending_line: str
    danger: str
    humor: str
    team_task: str
    result: str


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", feature="a wide oak tree"),
    "riverbank": Setting(place="the riverbank", feature="a fallen log"),
    "orchard": Setting(place="the orchard", feature="a round stone wall"),
}

BULLIES = {
    "wolf": Role(
        id="wolf",
        kind="character",
        type="wolf",
        label="wolf",
        phrase="a tall wolf with a loud voice",
        traits=["boastful", "pushy"],
    ),
    "fox": Role(
        id="fox",
        kind="character",
        type="fox",
        label="fox",
        phrase="a sharp-eyed fox with a sly grin",
        traits=["smug", "loud"],
    ),
}

FRIENDS = {
    "rabbit": Role(
        id="rabbit",
        kind="character",
        type="rabbit",
        label="rabbit",
        phrase="a quick rabbit",
        traits=["kind", "nimble"],
    ),
    "hedgehog": Role(
        id="hedgehog",
        kind="character",
        type="hedgehog",
        label="hedgehog",
        phrase="a small hedgehog",
        traits=["steady", "patient"],
    ),
    "mouse": Role(
        id="mouse",
        kind="character",
        type="mouse",
        label="mouse",
        phrase="a tiny mouse",
        traits=["clever", "gentle"],
    ),
    "crow": Role(
        id="crow",
        kind="character",
        type="crow",
        label="crow",
        phrase="a clever crow",
        traits=["funny", "bright"],
    ),
}

TALES = {
    ("wolf", "rabbit", "meadow"): Tale(
        bully_line="The wolf tried to intimidate the rabbit with a thunderous howl.",
        laugh_line="But the rabbit made a silly hop and a crooked bow, and the others laughed.",
        teamwork_line="Then the friends worked together to line up a trail of shiny pebbles.",
        ending_line="The wolf blinked, lost its brave act, and wandered off while the team shared a grin.",
        danger="being frightened by loud threats",
        humor="a funny hop and crooked bow",
        team_task="line up a trail of shiny pebbles",
        result="the wolf could not keep scaring them",
    ),
    ("fox", "mouse", "orchard"): Tale(
        bully_line="The fox tried to intimidate the mouse by puffing up its chest.",
        laugh_line="The mouse squeaked a joke about the fox's puffed cheeks, and the friends snickered kindly.",
        teamwork_line="Together they stacked apples into a little bridge across the roots.",
        ending_line="The fox saw the playful bridge, forgot its growl, and slunk away from the laughing team.",
        danger="a bully puffing itself up",
        humor="a joke about puffed cheeks",
        team_task="stack apples into a little bridge",
        result="the fox lost its scary power",
    ),
    ("wolf", "crow", "riverbank"): Tale(
        bully_line="The wolf tried to intimidate the crow with a deep growl beside the water.",
        laugh_line="The crow answered with a squeaky parade voice, and that made everyone laugh.",
        teamwork_line="The friends joined wings and paws to pass reeds from bank to bank.",
        ending_line="The wolf could not stay fierce in the middle of all that laughter and teamwork, so it trotted away.",
        danger="a growling bully by the water",
        humor="a squeaky parade voice",
        team_task="pass reeds from bank to bank",
        result="the scary mood melted",
    ),
}

NAMES = {
    "wolf": ["Waldo", "Bruno", "Tarn"],
    "fox": ["Fenn", "Tessa", "Milo"],
    "rabbit": ["Pip", "Ruby", "Nora"],
    "hedgehog": ["Hugo", "Mimi", "Bram"],
    "mouse": ["Mina", "Nim", "Tilo"],
    "crow": ["Cora", "Jett", "Lark"],
}

TRAITS = ["brave", "kind", "quick", "gentle", "bright", "steady"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    bully: str
    friend: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid story needs a setting, a bully, and a friend.
valid_story(S, B, F) :- setting(S), bully(B), friend(F), not same(B, F),
                        intimidates(B, F, S),
                        has_humor(F, S),
                        has_teamwork(F, S).

% The bully must be the one doing the intimidating.
intimidation(B, F, S) :- intimidates(B, F, S).

% Humor and teamwork are the positive counters in the fable.
resolves(F, S) :- has_humor(F, S), has_teamwork(F, S).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BULLIES:
        lines.append(asp.fact("bully", bid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend", fid))
    for (bid, fid, sid) in TALES:
        lines.append(asp.fact("intimidates", bid, fid, sid))
        lines.append(asp.fact("has_humor", fid, sid))
        lines.append(asp.fact("has_teamwork", fid, sid))
    for bid in BULLIES:
        for fid in FRIENDS:
            if bid == fid:
                lines.append(asp.fact("same", bid, fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return sorted(TALES.keys())


def explain_rejection(setting: str, bully: str, friend: str) -> str:
    return (
        f"(No story: there is no fable where {bully} can intimidate {friend} at {setting} "
        f"and still meet the humor-and-teamwork turn.)"
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def _introduce(world: World, bully: Entity, friend: Entity, setting: Setting, tale: Tale) -> None:
    world.say(
        f"At {setting.place}, under {setting.feature}, there lived {bully.phrase} and {friend.phrase}."
    )
    world.say(
        f"The {bully.label} was {bully.traits[0]}, and the {friend.label} was {friend.traits[0]}."
    )
    world.say(
        f"One day, trouble came in the form of {tale.danger}."
    )


def _conflict(world: World, bully: Entity, friend: Entity, tale: Tale) -> None:
    bully.meters["threat"] = bully.meters.get("threat", 0.0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0.0) + 1
    world.say(tale.bully_line)


def _humor(world: World, friend: Entity, tale: Tale) -> None:
    friend.memes["humor"] = friend.memes.get("humor", 0.0) + 1
    world.say(tale.laugh_line)


def _teamwork(world: World, friend: Entity, tale: Tale) -> None:
    for mate in world.characters():
        if mate.id != friend.id:
            mate.memes["helpful"] = mate.memes.get("helpful", 0.0) + 1
    friend.memes["teamwork"] = friend.memes.get("teamwork", 0.0) + 1
    world.say(tale.teamwork_line)


def _resolution(world: World, bully: Entity, friend: Entity, tale: Tale) -> None:
    bully.meters["threat"] = 0.0
    bully.memes["embarrassed"] = bully.memes.get("embarrassed", 0.0) + 1
    friend.memes["worry"] = 0.0
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    world.say(tale.ending_line)


def tell(setting_key: str, bully_key: str, friend_key: str, bully_name: str, friend_name: str) -> World:
    setting = SETTINGS[setting_key]
    tale = TALES[(bully_key, friend_key, setting_key)]
    world = World(setting)
    bully = world.add(Entity(
        id=bully_name,
        kind="character",
        type=bully_key,
        label=bully_key,
        phrase=BULLIES[bully_key].phrase.replace("a ", "").replace("an ", ""),
        traits=list(BULLIES[bully_key].traits),
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_key,
        label=friend_key,
        phrase=FRIENDS[friend_key].phrase.replace("a ", "").replace("an ", ""),
        traits=list(FRIENDS[friend_key].traits),
    ))

    _introduce(world, bully, friend, setting, tale)
    world.para()
    _conflict(world, bully, friend, tale)
    _humor(world, friend, tale)
    _teamwork(world, friend, tale)
    _resolution(world, bully, friend, tale)

    world.facts.update(
        setting=setting_key,
        bully=bully_key,
        friend=friend_key,
        tale=tale,
        bully_name=bully_name,
        friend_name=friend_name,
        bully_entity=bully,
        friend_entity=friend,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for young children about how {f["bully_name"]} the {f["bully"]} tried to intimidate {f["friend_name"]} at {SETTINGS[f["setting"]].place}.',
        f"Tell a gentle animal story where humor and teamwork help {f['friend_name']} stand up to a bully.",
        f'Write a fable with a funny moment, a brave group, and the word "intimidate" somewhere in the story.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bully_ent: Entity = f["bully_entity"]
    friend_ent: Entity = f["friend_entity"]
    setting = SETTINGS[f["setting"]]
    tale: Tale = f["tale"]

    return [
        QAItem(
            question=f"Who tried to intimidate {f['friend_name']} at {setting.place}?",
            answer=f"It was {f['bully_name']}, the {f['bully']}. {bully_ent.pronoun('subject').capitalize()} was the one making the loud threat.",
        ),
        QAItem(
            question=f"What helped {f['friend_name']} stop feeling scared?",
            answer=f"Humor and teamwork helped. {f['friend_name']} made a funny move, then the friends worked together, and the bully lost its power.",
        ),
        QAItem(
            question=f"What did the friends do together in the middle of the story?",
            answer=f"They worked as a team to {tale.team_task}, which turned the scary moment into a playful one.",
        ),
        QAItem(
            question=f"How did the story end after the bully was intimidated by the group?",
            answer=f"The ending showed that {tale.result}. The bully stopped acting so fierce and the friends stayed united.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is intimidation?",
            answer="Intimidation is when someone uses loud or scary behavior to try to make another person feel afraid.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do something well.",
        ),
        QAItem(
            question="Why can humor help in a hard moment?",
            answer="Humor can help because a funny moment can make fear feel smaller and help people stay calm.",
        ),
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
        lines.append(
            f"  {e.id:10} ({e.type:8}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about intimidation, humor, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bully", choices=BULLIES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    combos = valid_combos()
    if args.setting and args.bully and args.friend:
        if (args.bully, args.friend, args.setting) not in combos:
            raise StoryError(explain_rejection(args.setting, args.bully, args.friend))

    filtered = [
        c for c in combos
        if (args.setting is None or c[2] == args.setting)
        and (args.bully is None or c[0] == args.bully)
        and (args.friend is None or c[1] == args.friend)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    bully, friend, setting = rng.choice(sorted(filtered))
    return StoryParams(
        setting=setting,
        bully=bully,
        friend=friend,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    bully_name = params.seed is not None and NAMES[params.bully][params.seed % len(NAMES[params.bully])] or random.choice(NAMES[params.bully])
    friend_name = params.seed is not None and NAMES[params.friend][(params.seed + 1) % len(NAMES[params.friend])] or random.choice(NAMES[params.friend])
    world = tell(params.setting, params.bully, params.friend, bully_name, friend_name)
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
    StoryParams(setting="meadow", bully="wolf", friend="rabbit"),
    StoryParams(setting="orchard", bully="fox", friend="mouse"),
    StoryParams(setting="riverbank", bully="wolf", friend="crow"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story triples:")
        for s, b, f in stories:
            print(f"  {s:10} {b:8} {f:8}")
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
