#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/girl_heart_lmnop_bravery_sharing_quest_slice.py
===========================================================================================================================

A small slice-of-life storyworld about a girl, a heart-shaped token, and a
quiet quest that is solved through bravery and sharing.

Seed image:
A girl finds a little heart token named "lmnop" before a neighborhood quest
day. She wants to keep it safe, but a friend needs it to complete a shared
quest. The story turns when she finds the courage to share and both children
finish the day happier than before.

World model:
- physical meters: possession, distance, preparation, tidiness
- emotional memes: joy, worry, bravery, trust, pride, generosity
- typed entities: girl, friend, heart token, quest board, keepsake box

The prose is state-driven: the token can be carried or shared, the quest has a
real completion condition, and the ending image proves what changed.
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
# Domain registries
# ---------------------------------------------------------------------------

GIRL_NAMES = ["Mia", "Lila", "Nora", "Ava", "Zoe", "Ivy", "Ruby", "Ella"]
FRIEND_NAMES = ["Ben", "Noah", "Owen", "Eli", "Finn", "Max", "Theo", "Sam"]
PLACES = {
    "street": "the little street",
    "yard": "the front yard",
    "porch": "the porch",
    "garden": "the community garden",
}
TOKENS = {
    "heart": {
        "label": "heart",
        "phrase": "a small red heart token",
        "shape": "heart-shaped",
    },
    "lmnop": {
        "label": "lmnop",
        "phrase": "a tiny charm with the word lmnop painted on it",
        "shape": "lettered",
    },
}
QUESTS = {
    "share_cards": {
        "label": "sharing quest",
        "goal": "share one special token so the quest can be finished together",
        "reward": "a bright paper star",
    },
    "deliver_note": {
        "label": "quest",
        "goal": "carry a note to the neighbor and say the right line together",
        "reward": "a thank-you sticker",
    },
    "find_map": {
        "label": "quest slice",
        "goal": "match a token to a clue board and point out the next step",
        "reward": "a little ribbon",
    },
}


# ---------------------------------------------------------------------------
# Shared result model
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    token: str
    quest: str
    girl_name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    shared_with: Optional[str] = None
    revealed: bool = False


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------

def braver(actor: Entity, amount: float = 1.0) -> None:
    actor.memes["bravery"] = actor.memes.get("bravery", 0.0) + amount


def worry(actor: Entity, amount: float = 1.0) -> None:
    actor.memes["worry"] = actor.memes.get("worry", 0.0) + amount


def trust(actor: Entity, amount: float = 1.0) -> None:
    actor.memes["trust"] = actor.memes.get("trust", 0.0) + amount


def joy(actor: Entity, amount: float = 1.0) -> None:
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + amount


def share_token(world: World, girl: Entity, friend: Entity, token: Entity) -> None:
    token.shared_with = friend.id
    token.carried_by = None
    token.revealed = True
    girl.meters["possession"] = 0.0
    friend.meters["possession"] = 1.0
    trust(girl, 1.0)
    trust(friend, 1.0)
    joy(girl, 1.0)
    joy(friend, 1.0)
    braver(girl, 1.0)
    world.facts["shared"] = True


def complete_quest(world: World, girl: Entity, friend: Entity, token: Entity, quest_id: str) -> bool:
    quest = QUESTS[quest_id]
    if quest_id == "share_cards":
        return token.shared_with == friend.id
    if quest_id == "deliver_note":
        return token.revealed and token.carried_by is None
    return token.revealed and girl.memes.get("trust", 0.0) >= 1.0


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def opening_line(girl: Entity, token: Entity, place: str) -> str:
    return (
        f"{girl.label} found {token.phrase} on {place} and held it close, "
        f"as if the little heart could keep a whole day warm."
    )


def quest_line(friend: Entity, quest_label: str, goal: str) -> str:
    return (
        f"At the same time, {friend.label} was waiting for a {quest_label}. "
        f"The plan was simple: {goal}."
    )


def conflict_line(girl: Entity, token: Entity) -> str:
    return (
        f"{girl.label} wanted to keep the {token.label} token all to herself. "
        f"It looked too special to give away."
    )


def turn_line(girl: Entity, friend: Entity, token: Entity) -> str:
    return (
        f"Then {girl.label} took a small breath, showed {friend.label} the "
        f"{token.label} token, and said she could share it for the quest."
    )


def ending_line(girl: Entity, friend: Entity, token: Entity, reward: str) -> str:
    return (
        f"By the end, the {token.label} token sat between them on the table, "
        f"the quest was done, and {girl.label} and {friend.label} were smiling "
        f"over {reward}."
    )


def story_qa(world: World) -> list[QAItem]:
    g = world.get("girl")
    f = world.get("friend")
    t = world.get("token")
    q = QUESTS[world.facts["quest"]]
    return [
        QAItem(
            question=f"What did {g.label} find at the start of the story?",
            answer=f"{g.label} found {t.phrase} and held it close."
        ),
        QAItem(
            question=f"What did {g.label} have to do to finish the {q['label']}?",
            answer=f"{g.label} had to share the {t.label} token with {f.label} so they could finish the quest together."
        ),
        QAItem(
            question=f"How did the story end for {g.label} and {f.label}?",
            answer=f"They finished the quest together, and both were smiling by the end."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery in this storyworld?",
            answer="Bravery is when a child does something a little scary or hard, like sharing something special or saying yes to a helpful plan."
        ),
        QAItem(
            question="What does sharing mean here?",
            answer="Sharing means letting someone else use or hold something special so two people can enjoy it together."
        ),
        QAItem(
            question="What is a quest in this storyworld?",
            answer="A quest is a small goal for the children to finish, like delivering a note or matching a token to a clue."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        f"Write a slice-of-life story about a girl named {p['girl']} who finds the word {p['token']} and learns bravery through sharing.",
        f"Tell a gentle story where {p['girl']} and {p['friend']} complete a small {QUESTS[p['quest']]['label']} together.",
        f"Make a child-friendly story about a heart-shaped keepsake, a little worry, and a brave choice to share.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.shared_with:
            bits.append(f"shared_with={e.shared_with}")
        if e.revealed:
            bits.append("revealed=True")
        lines.append(f"  {e.id:6} ({e.kind:6}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
shared(Girl,Friend,Token) :- girl(Girl), friend(Friend), token(Token), carried(Token,Girl), needs_share(Token), brave(Girl).
quest_complete(Quest) :- quest(Quest), requires_share(Quest), shared(_,_,_).
quest_complete(Quest) :- quest(Quest), requires_show(Quest), revealed(token).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in GIRL_NAMES:
        lines.append(asp.fact("girl_name", name))
    for name in FRIEND_NAMES:
        lines.append(asp.fact("friend_name", name))
    for pid, pl in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_label", pid, pl))
    for tid, tok in TOKENS.items():
        lines.append(asp.fact("token", tid))
        lines.append(asp.fact("token_label", tid, tok["label"]))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if "share" in qid:
            lines.append(asp.fact("requires_share", qid))
        if "map" in qid:
            lines.append(asp.fact("requires_show", qid))
    lines.append(asp.fact("brave", "girl"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest_complete/1."))
    asp_answers = set(asp.atoms(model, "quest_complete"))
    py_answers = {("share_cards",), ("find_map",)}  # reasonable cases by design
    if asp_answers == py_answers:
        print(f"OK: ASP gate matches reasonableness set ({len(py_answers)} cases).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("  asp:", sorted(asp_answers))
    print("  py :", sorted(py_answers))
    return 1


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def build_story(params: StoryParams) -> StorySample:
    world = World(place=PLACES[params.place])

    girl = world.add(Entity(id="girl", kind="character", label=params.girl_name))
    friend = world.add(Entity(id="friend", kind="character", label=params.friend_name))
    token_info = TOKENS[params.token]
    token = world.add(Entity(
        id="token",
        kind="thing",
        label=token_info["label"],
        phrase=token_info["phrase"],
        owner=girl.id,
        carried_by=girl.id,
        meters={"possession": 1.0},
    ))
    quest = QUESTS[params.quest]
    board = world.add(Entity(id="board", kind="thing", label="quest board"))
    box = world.add(Entity(id="box", kind="thing", label="keepsake box"))

    world.facts.update(
        girl=girl.label,
        friend=friend.label,
        token=token.label,
        quest=params.quest,
        place=params.place,
    )

    joy(girl, 1.0)
    worry(girl, 0.5)
    trust(friend, 0.5)

    world.say(
        f"{girl.label} was walking near {world.place} when she found {token.phrase}."
    )
    world.say(opening_line(girl, token, world.place))
    world.para()
    world.say(quest_line(friend, quest["label"], quest["goal"]))
    world.say(
        f"{friend.label} pointed to the {board.label} and said the quest would work only if they used the token together."
    )
    world.say(conflict_line(girl, token))
    world.para()
    world.say(
        f"{girl.label} looked at the {box.label}, then at {friend.label}, and felt her worry slowly turn into bravery."
    )
    share_token(world, girl, friend, token)
    if complete_quest(world, girl, friend, token, params.quest):
        world.facts["completed"] = True
        world.say(turn_line(girl, friend, token))
        world.say(
            f"They placed the {token.label} token on the {board.label}, finished the {quest['label']}, and got {quest['reward']}."
        )
        world.para()
        world.say(
            ending_line(girl, friend, token, quest["reward"])
        )
    else:
        raise StoryError("The story setup did not reach a valid shared-quest ending.")

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small slice-of-life storyworld about bravery, sharing, and a tiny quest."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--token", choices=sorted(TOKENS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--girl-name", choices=GIRL_NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
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
    place = args.place or rng.choice(sorted(PLACES))
    token = args.token or rng.choice(sorted(TOKENS))
    quest = args.quest or rng.choice(sorted(QUESTS))
    girl_name = args.girl_name or rng.choice(GIRL_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    if girl_name == friend_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != girl_name])
    if quest == "share_cards" and token != "heart":
        # sharing is the most natural fit for the heart token in this world
        if args.quest and args.token:
            raise StoryError("The sharing quest wants the heart token in this storyworld.")
        token = "heart"
    return StoryParams(place=place, token=token, quest=quest, girl_name=girl_name, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_complete/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quest_complete/1."))
        print(sorted(asp.atoms(model, "quest_complete")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="street", token="heart", quest="share_cards", girl_name="Mia", friend_name="Ben"),
            StoryParams(place="yard", token="lmnop", quest="deliver_note", girl_name="Lila", friend_name="Owen"),
            StoryParams(place="garden", token="heart", quest="find_map", girl_name="Nora", friend_name="Finn"),
        ]
        samples = [generate(p) for p in curated]
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
